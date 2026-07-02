"""Service for managing properties and units."""
from app.models.database import get_client
from app.services.audit_service import log_action

def get_properties(user_id: str) -> list[dict]:
    """Retrieve all properties for a user."""
    client = get_client()
    response = client.table("properties").select("*").eq("user_id", user_id).order("name").execute()
    return response.data or []

def add_property(user_id: str, name: str, address: str) -> str | None:
    """Add a new property."""
    client = get_client()
    data = {"user_id": user_id, "name": name, "address": address}
    try:
        response = client.table("properties").insert(data).execute()
        property_id = response.data[0]["id"]
        log_action(user_id, "PROPERTY_ADDED", "property", property_id, new_value={"name": name, "address": address})
        return property_id
    except Exception as e:
        print(f"Error adding property: {e}")
        return None

def get_units_by_property(property_id: str) -> list[dict]:
    """Retrieve all units for a specific property."""
    client = get_client()
    response = client.table("units").select("*").eq("property_id", property_id).order("unit_number").execute()
    return response.data or []

def get_all_units(user_id: str) -> list[dict]:
    """Retrieve all units across all properties for a user."""
    client = get_client()
    # Need to join with properties to filter by user_id
    response = client.table("units").select("*, properties!inner(user_id, name)").eq("properties.user_id", user_id).execute()
    return response.data or []

def add_unit(user_id: str, property_id: str, unit_number: str, default_rent: float = 0, status: str = "Vacant") -> str | None:
    """Add a new unit to a property."""
    client = get_client()
    data = {
        "property_id": property_id,
        "unit_number": unit_number,
        "default_rent": default_rent,
        "status": status
    }
    try:
        response = client.table("units").insert(data).execute()
        unit_id = response.data[0]["id"]
        log_action(user_id, "UNIT_ADDED", "unit", unit_id, new_value={"unit_number": unit_number, "property_id": property_id})
        return unit_id
    except Exception as e:
        print(f"Error adding unit: {e}")
        return None

def update_unit_status(user_id: str, unit_id: str, new_status: str) -> bool:
    """Update the status of a unit."""
    client = get_client()
    try:
        client.table("units").update({"status": new_status}).eq("id", unit_id).execute()
        log_action(user_id, "UNIT_STATUS_CHANGED", "unit", unit_id, new_value={"status": new_status})
        return True
    except Exception as e:
        print(f"Error updating unit status: {e}")
        return False


def update_unit(user_id: str, unit_id: str, unit_number: str, default_rent: float) -> bool:
    """Update a unit's number and default rent."""
    client = get_client()
    try:
        client.table("units").update({"unit_number": unit_number, "default_rent": default_rent}).eq("id", unit_id).execute()
        log_action(user_id, "UNIT_UPDATED", "unit", unit_id, new_value={"unit_number": unit_number, "default_rent": default_rent})
        return True
    except Exception as e:
        print(f"Error updating unit: {e}")
        return False


def delete_unit(user_id: str, unit_id: str) -> bool:
    """Delete a unit by ID."""
    client = get_client()
    try:
        client.table("units").delete().eq("id", unit_id).execute()
        log_action(user_id, "UNIT_DELETED", "unit", unit_id)
        return True
    except Exception as e:
        print(f"Error deleting unit: {e}")
        return False


def delete_property(user_id: str, property_id: str) -> bool:
    """Delete a property and all its units by property ID."""
    client = get_client()
    try:
        # Units are cascade-deleted by Supabase foreign key; log the property deletion
        client.table("properties").delete().eq("id", property_id).execute()
        log_action(user_id, "PROPERTY_DELETED", "property", property_id)
        return True
    except Exception as e:
        print(f"Error deleting property: {e}")
        return False

