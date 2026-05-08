"""Marketing service — Meta Marketing API integration for Facebook & Instagram ads.

Uses the Meta Graph API directly via requests (no SDK dependency required).
Fetches campaigns, ad sets, ads, and their insights from the connected ad account.
"""

import requests
from app.config import META_ACCESS_TOKEN, META_AD_ACCOUNT_ID

GRAPH_API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def is_meta_configured() -> bool:
    """Check whether Meta API credentials are provided."""
    return bool(META_ACCESS_TOKEN and META_AD_ACCOUNT_ID)


def _meta_get(endpoint: str, params: dict | None = None) -> dict:
    """Make an authenticated GET request to the Meta Graph API."""
    params = params or {}
    params["access_token"] = META_ACCESS_TOKEN
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

def get_ads(campaign_id: str = None) -> tuple[bool, list[dict], str]:
    """Fetch all ads, optionally filtered by campaign_id."""
    if not is_meta_configured():
        return False, [], "Meta API credentials not configured."

    endpoint = f"{campaign_id}/ads" if campaign_id else f"{META_AD_ACCOUNT_ID}/ads"
    data = _meta_get(
        endpoint,
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

def get_account_insights(date_preset: str = "last_30d") -> tuple[bool, dict, str]:
    """Fetch account-level insights (impressions, clicks, spend, etc.)."""
    if not is_meta_configured():
        return False, {}, "Meta API credentials not configured."

    data = _meta_get(
        f"{META_AD_ACCOUNT_ID}/insights",
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
