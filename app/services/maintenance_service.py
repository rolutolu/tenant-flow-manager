"""Service for managing maintenance requests."""
import datetime
from app.models.database import get_client

def get_maintenance_requests(user_id: str) -> list[dict]:
    """Retrieve all maintenance tickets for a user."""
    client = get_client()
    response = client.table("maintenance_requests").select("*, tenants(name), units(unit_number)").eq("user_id", user_id).order("created_at", desc=True).execute()
    return response.data or []

def add_maintenance_request(user_id: str, issue: str, urgency: str = "Low", tenant_id: int = None, unit_id: str = None) -> str | None:
    """Create a new maintenance ticket."""
    client = get_client()
    data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "unit_id": unit_id,
        "issue": issue,
        "urgency": urgency
    }
    try:
        response = client.table("maintenance_requests").insert(data).execute()
        return response.data[0]["id"]
    except Exception as e:
        print(f"Error adding maintenance request: {e}")
        return None

def update_maintenance_status(request_id: str, status: str) -> bool:
    """Update the status of a ticket."""
    client = get_client()
    data = {"status": status}
    if status == "Resolved":
        data["resolved_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        client.table("maintenance_requests").update(data).eq("id", request_id).execute()
        return True
    except Exception as e:
        print(f"Error updating maintenance request: {e}")
        return False


def update_maintenance_request(request_id: str, **kwargs) -> bool:
    """Update arbitrary fields on a maintenance ticket."""
    if not kwargs:
        return False
    client = get_client()
    try:
        client.table("maintenance_requests").update(kwargs).eq("id", request_id).execute()
        return True
    except Exception as e:
        print(f"Error updating maintenance request: {e}")
        return False
