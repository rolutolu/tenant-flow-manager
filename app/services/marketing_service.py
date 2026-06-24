"""Marketing service — Meta Marketing API integration for Facebook & Instagram ads.

Uses the Meta Graph API directly via requests (no SDK dependency required).
Fetches campaigns, ad sets, ads, and their insights from the connected ad account.
"""

import requests
from app.config import META_ACCESS_TOKEN, META_AD_ACCOUNT_ID
from app.models.database import get_client, encrypt_value, decrypt_value

GRAPH_API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def get_marketing_config(user_id: str) -> dict:
    """Fetch encrypted Meta credentials for a specific user."""
    client = get_client()
    try:
        resp = client.table("marketing_configs").select("*").eq("user_id", user_id).execute()
        if resp.data:
            config = resp.data[0]
            return {
                "access_token": decrypt_value(config["access_token"]),
                "ad_account_id": decrypt_value(config["ad_account_id"]),
            }
    except Exception as e:
        print(f"[ERROR] Could not load marketing config: {e}")
    # Fallback to .env for single-user/legacy mode
    return {
        "access_token": META_ACCESS_TOKEN,
        "ad_account_id": META_AD_ACCOUNT_ID,
    }


def save_marketing_config(user_id: str, access_token: str, ad_account_id: str) -> bool:
    """Save encrypted Meta credentials for a specific user."""
    client = get_client()
    data = {
        "user_id": user_id,
        "access_token": encrypt_value(access_token),
        "ad_account_id": encrypt_value(ad_account_id),
    }
    try:
        client.table("marketing_configs").upsert(data).execute()
        return True
    except Exception as e:
        print(f"[ERROR] Could not save marketing config: {e}")
        return False


def is_meta_configured(user_id: str = None) -> bool:
    """Check whether Meta API credentials are provided (either in DB or .env)."""
    if user_id:
        config = get_marketing_config(user_id)
        return bool(config["access_token"] and config["ad_account_id"])
    return bool(META_ACCESS_TOKEN and META_AD_ACCOUNT_ID)


def _meta_get(endpoint: str, config: dict, params: dict | None = None) -> dict:
    """Make an authenticated GET request using provided config."""
    params = params or {}
    params["access_token"] = config["access_token"]
    url = f"{BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        error_data = {}
        try:
            error_data = e.response.json()
        except Exception:
            pass
        return {"error": error_data.get("error", {"message": str(e)})}
    except requests.exceptions.RequestException as e:
        return {"error": {"message": f"Connection error: {str(e)}"}}


# ── Campaigns ──────────────────────────────────────────────────────────────────

def get_campaigns() -> tuple[bool, list[dict], str]:
    """Fetch all campaigns from the ad account.

    Returns (success, campaigns_list, error_message).
    """
    if not is_meta_configured():
        return False, [], "Meta API credentials not configured."

    data = _meta_get(
        f"{META_AD_ACCOUNT_ID}/campaigns",
        params={
            "fields": "id,name,status,objective,daily_budget,lifetime_budget,"
                      "start_time,stop_time,buying_type,created_time",
            "limit": 50,
        },
    )
    if "error" in data:
        return False, [], data["error"].get("message", "Unknown API error")

    campaigns = data.get("data", [])
    return True, campaigns, ""


# ── Ad Sets ────────────────────────────────────────────────────────────────────

def get_ad_sets(campaign_id: str = None) -> tuple[bool, list[dict], str]:
    """Fetch ad sets, optionally filtered by campaign_id."""
    if not is_meta_configured():
        return False, [], "Meta API credentials not configured."

    endpoint = f"{campaign_id}/adsets" if campaign_id else f"{META_AD_ACCOUNT_ID}/adsets"
    data = _meta_get(
        endpoint,
        params={
            "fields": "id,name,status,daily_budget,targeting,optimization_goal,"
                      "billing_event,start_time,end_time",
            "limit": 50,
        },
    )
    if "error" in data:
        return False, [], data["error"].get("message", "Unknown API error")

    return True, data.get("data", []), ""


# ── Ads ────────────────────────────────────────────────────────────────────────

def get_ads(user_id: str, campaign_id: str = None) -> tuple[bool, list[dict], str]:
    """Fetch all ads, optionally filtered by campaign_id."""
    config = get_marketing_config(user_id)
    if not config["access_token"]:
        return False, [], "Meta API credentials not configured."

    endpoint = f"{campaign_id}/ads" if campaign_id else f"{config['ad_account_id']}/ads"
    data = _meta_get(
        endpoint,
        config=config,
        params={
            "fields": "id,name,status,creative{id,name,title,body,"
                      "image_url,thumbnail_url,object_story_spec},"
                      "effective_status,created_time",
            "limit": 50,
        },
    )
    if "error" in data:
        return False, [], data["error"].get("message", "Unknown API error")

    return True, data.get("data", []), ""


# ── Insights / Analytics ───────────────────────────────────────────────────────

def get_account_insights(user_id: str, date_preset: str = "last_30d") -> tuple[bool, dict, str]:
    """Fetch account-level insights (impressions, clicks, spend, etc.)."""
    config = get_marketing_config(user_id)
    if not config["access_token"]:
        return False, {}, "Meta API credentials not configured."

    data = _meta_get(
        f"{config['ad_account_id']}/insights",
        config=config,
        params={
            "fields": "impressions,clicks,ctr,spend,reach,cpc,cpm,"
                      "actions,cost_per_action_type",
            "date_preset": date_preset,
        },
    )
    if "error" in data:
        return False, {}, data["error"].get("message", "Unknown API error")

    insights = data.get("data", [{}])
    return True, insights[0] if insights else {}, ""


def get_campaign_insights(date_preset: str = "last_30d") -> tuple[bool, list[dict], str]:
    """Fetch per-campaign insights for the account."""
    if not is_meta_configured():
        return False, [], "Meta API credentials not configured."

    data = _meta_get(
        f"{META_AD_ACCOUNT_ID}/insights",
        params={
            "fields": "campaign_id,campaign_name,impressions,clicks,ctr,"
                      "spend,reach,actions",
            "date_preset": date_preset,
            "level": "campaign",
            "limit": 50,
        },
    )
    if "error" in data:
        return False, [], data["error"].get("message", "Unknown API error")

    return True, data.get("data", []), ""
