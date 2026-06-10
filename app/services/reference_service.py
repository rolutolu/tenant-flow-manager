"""Service for tracking tenant reference check outreach."""

from app.models.database import get_client


def log_reference_check(user_id: str, tenant_id: int, ref_name: str,
                        ref_phone: str = "", ref_email: str = "",
                        ref_type: str = "Landlord", channel: str = "SMS",
                        notes: str = "") -> int | None:
    """Record a reference check that was sent."""
    client = get_client()
    data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "ref_name": ref_name,
        "ref_phone": ref_phone,
        "ref_email": ref_email,
        "ref_type": ref_type,
        "channel": channel,
        "status": "Sent",
        "notes": notes,
    }
    try:
        response = client.table("reference_checks").insert(data).execute()
        return response.data[0]["id"]
    except Exception as e:
        print(f"Error logging reference check: {e}")
        return None


def update_reference_status(check_id: int, status: str, notes: str = None) -> bool:
    """Update the status of a reference check."""
    client = get_client()
    data = {"status": status}
    if notes is not None:
        data["notes"] = notes
    try:
        client.table("reference_checks").update(data).eq("id", check_id).execute()
        return True
    except Exception as e:
        print(f"Error updating reference check: {e}")
        return False


def get_checks_for_tenant(tenant_id: int) -> list[dict]:
    """Fetch all reference checks for a tenant."""
    client = get_client()
    try:
        response = (
            client.table("reference_checks")
            .select("*")
            .eq("tenant_id", tenant_id)
            .order("sent_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"Error fetching reference checks: {e}")
        return []


def get_checks_for_user(user_id: str, limit: int = 50) -> list[dict]:
    """Fetch recent reference checks for a user."""
    client = get_client()
    try:
        response = (
            client.table("reference_checks")
            .select("*, tenants(name, unit)")
            .eq("user_id", user_id)
            .order("sent_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"Error fetching reference checks: {e}")
        return []
