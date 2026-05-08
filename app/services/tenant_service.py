"""CRUD operations for tenants using Supabase."""

from app.models.database import get_client, encrypt_value, decrypt_value


def add_tenant(user_id: str, name: str, unit: str, rent_amount: float,
               lease_start: str = "", lease_end: str = "",
               bank_info: str = "", banking_set_up: str = "No",
               move_in_status: str = "Pending", lease_signed: str = "No") -> int:
    """Insert a new tenant and return their ID."""
    client = get_client()
    data = {
        "user_id": user_id,
        "name": name,
        "unit": unit,
        "rent_amount": rent_amount,
        "lease_start": lease_start,
        "lease_end": lease_end,
        "bank_info": encrypt_value(bank_info),
        "banking_set_up": banking_set_up,
        "move_in_status": move_in_status,
        "lease_signed": lease_signed,
    }
    response = client.table("tenants").insert(data).execute()
    return response.data[0]["id"]


def get_all_tenants(user_id: str) -> list[dict]:
    """Return all tenants for a user (bank_info decrypted)."""
    client = get_client()
    response = (
        client.table("tenants")
        .select("*")
        .eq("user_id", user_id)
        .order("id")
        .execute()
    )
    result = []
    for row in (response.data or []):
        row["bank_info"] = decrypt_value(row.get("bank_info", ""))
        result.append(row)
    return result


def get_tenant(tenant_id: int) -> dict | None:
    """Return a single tenant by ID."""
    client = get_client()
    response = client.table("tenants").select("*").eq("id", tenant_id).execute()
    if response.data:
        d = response.data[0]
        d["bank_info"] = decrypt_value(d.get("bank_info", ""))
        return d
    return None


def get_tenant_by_unit(user_id: str, unit: str) -> dict | None:
    """Return a single tenant by unit identifier (scoped to user)."""
    client = get_client()
    response = (
        client.table("tenants")
        .select("*")
        .eq("user_id", user_id)
        .eq("unit", unit)
        .execute()
    )
    if response.data:
        d = response.data[0]
        d["bank_info"] = decrypt_value(d.get("bank_info", ""))
        return d
    return None


def update_tenant(tenant_id: int, **kwargs) -> bool:
    """Update specific fields for a tenant. Encrypts bank_info automatically."""
    if not kwargs:
        return False
    if "bank_info" in kwargs:
        kwargs["bank_info"] = encrypt_value(kwargs["bank_info"])
    client = get_client()
    try:
        client.table("tenants").update(kwargs).eq("id", tenant_id).execute()
        return True
    except Exception:
        return False


def delete_tenant(tenant_id: int) -> bool:
    """Delete a tenant by ID."""
    client = get_client()
    try:
        client.table("tenants").delete().eq("id", tenant_id).execute()
        return True
    except Exception:
        return False


def get_tenant_count(user_id: str) -> int:
    """Return total number of tenants for a user."""
    client = get_client()
    response = (
        client.table("tenants")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .execute()
    )
    return response.count or 0


def get_pending_signatures_count(user_id: str) -> int:
    """Return count of tenants who haven't signed their lease yet."""
    client = get_client()
    response = (
        client.table("tenants")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .neq("lease_signed", "Yes")
        .execute()
    )
    return response.count or 0
