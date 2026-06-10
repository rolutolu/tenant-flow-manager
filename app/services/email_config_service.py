"""Per-account email branding and sender configuration."""

from app.config import SES_FROM_EMAIL
from app.models.database import get_client
from app.services.ses_service import check_ses_verification, request_ses_verification


def get_email_config(user_id: str) -> dict:
    """Load email settings for a landlord account."""
    client = get_client()
    try:
        resp = client.table("email_configs").select("*").eq("user_id", user_id).execute()
        if resp.data:
            return resp.data[0]
    except Exception as e:
        print(f"Error loading email config: {e}")
    return {
        "user_id": user_id,
        "from_email": "",
        "from_name": "",
        "reply_to": "",
        "footer_text": "",
        "ses_verified": False,
    }


def save_email_config(
    user_id: str,
    from_email: str,
    from_name: str = "",
    reply_to: str = "",
    footer_text: str = "",
) -> tuple[bool, str]:
    """Save per-account email settings."""
    if not from_email or "@" not in from_email:
        return False, "A valid sender email address is required."

    client = get_client()
    data = {
        "user_id": user_id,
        "from_email": from_email.strip(),
        "from_name": (from_name or "").strip(),
        "reply_to": (reply_to or "").strip(),
        "footer_text": (footer_text or "").strip(),
    }
    try:
        client.table("email_configs").upsert(data).execute()
        return True, "Email settings saved."
    except Exception as e:
        return False, f"Failed to save email settings: {str(e)}"


def resolve_sender(user_id: str) -> dict:
    """Resolve the From address and footer for outbound mail."""
    config = get_email_config(user_id)
    from_email = (config.get("from_email") or "").strip() or SES_FROM_EMAIL
    from_name = (config.get("from_name") or "").strip()
    reply_to = (config.get("reply_to") or "").strip()
    footer = (config.get("footer_text") or "").strip()

    if from_name:
        source = f"{from_name} <{from_email}>"
    else:
        source = from_email

    return {
        "from_email": from_email,
        "from_name": from_name,
        "source": source,
        "reply_to": reply_to,
        "footer_text": footer,
        "is_custom": bool(config.get("from_email")),
    }


def append_footer(body: str, footer: str) -> str:
    """Append the landlord's custom footer to an email body."""
    if not footer:
        return body
    return f"{body.rstrip()}\n\n--\n{footer}"


def update_verification_status(user_id: str) -> tuple[bool, str]:
    """Refresh stored verification flag from SES."""
    config = get_email_config(user_id)
    email = config.get("from_email", "")
    if not email:
        return False, "No sender email configured."

    verified, status = check_ses_verification(email)
    client = get_client()
    try:
        client.table("email_configs").update({"ses_verified": verified}).eq("user_id", user_id).execute()
    except Exception as e:
        print(f"Error updating verification status: {e}")

    if verified:
        return True, "Verified — you can send from this address."
    if status == "Pending":
        return False, "Pending — check your inbox for AWS verification email and click the link."
    return False, f"Not verified (status: {status}). Request verification and confirm via email."


# Re-export for settings page convenience
__all__ = [
    "get_email_config",
    "save_email_config",
    "resolve_sender",
    "append_footer",
    "update_verification_status",
    "request_ses_verification",
    "check_ses_verification",
]
