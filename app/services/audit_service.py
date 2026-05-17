"""Service for logging critical system actions to the audit_logs table."""
import json
from app.models.database import get_client

def log_action(user_id: str, action: str, entity_type: str, entity_id: str, old_value: dict = None, new_value: dict = None) -> bool:
    """Log an event to the audit trail."""
    client = get_client()
    data = {
        "user_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        # Bug fix #10: Store None/null rather than {} for missing values
        "old_value": old_value,
        "new_value": new_value
    }
    try:
        client.table("audit_logs").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error logging audit action: {e}")
        return False

def get_audit_logs(user_id: str, limit: int = 100) -> list[dict]:
    """Retrieve audit logs for a specific user."""
    client = get_client()
    try:
        response = client.table("audit_logs").select("*").eq("user_id", user_id).order("timestamp", desc=True).limit(limit).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching audit logs: {e}")
        return []
