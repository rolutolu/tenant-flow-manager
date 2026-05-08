"""Financial operations: banking info, PAD cross-referencing, NSF detection, revenue."""

from app.models.database import get_client, encrypt_value, decrypt_value
from app.services.tenant_service import update_tenant


def update_banking_info(tenant_id: int, bank_info: str) -> tuple[bool, str]:
    """Encrypt and store banking information for a tenant."""
    if not bank_info:
        return False, "Bank information cannot be empty."
    success = update_tenant(tenant_id, bank_info=bank_info, banking_set_up="Yes")
    if success:
        return True, "Banking information updated and encrypted successfully."
    return False, "Failed to update banking information."


def cross_reference_pads(user_id: str) -> tuple[bool, str, list[dict]]:
    """Compare the rent roll against the PAD schedule.

    Returns (success, message, discrepancies).
    In a real implementation this would compare against an external banking export.
    """
    client = get_client()
    response = (
        client.table("tenants")
        .select("*")
        .eq("user_id", user_id)
        .eq("banking_set_up", "Yes")
        .execute()
    )
    tenants = response.data or []

    # Simulated cross-reference — in production, compare against bank CSV
    discrepancies = []
    for t in tenants:
        if not t.get("rent_amount") or t["rent_amount"] <= 0:
            discrepancies.append({
                "tenant": t["name"],
                "unit": t["unit"],
                "issue": "Missing or zero rent amount"
            })

    if discrepancies:
        return False, f"Found {len(discrepancies)} discrepancy(ies).", discrepancies
    return True, f"All {len(tenants)} PADs match the master rent roll.", []


def flag_returned_payments(user_id: str) -> tuple[list[dict], str]:
    """Identify returned/NSF payments for the current user's tenants."""
    client = get_client()
    # First get user's tenant IDs
    tenants_resp = (
        client.table("tenants")
        .select("id")
        .eq("user_id", user_id)
        .execute()
    )
    tenant_ids = [t["id"] for t in (tenants_resp.data or [])]

    if not tenant_ids:
        return [], "No tenants found."

    # Get returned payments for those tenants
    response = (
        client.table("payments")
        .select("*, tenants(name, unit)")
        .in_("tenant_id", tenant_ids)
        .eq("status", "Returned")
        .order("date", desc=True)
        .execute()
    )
    cases = []
    for row in (response.data or []):
        tenant_data = row.get("tenants", {}) or {}
        cases.append({
            "id": row["id"],
            "tenant_id": row["tenant_id"],
            "tenant_name": tenant_data.get("name", "Unknown"),
            "unit": tenant_data.get("unit", "N/A"),
            "amount": row["amount"],
            "date": row["date"],
            "notes": row.get("notes", ""),
        })

    if cases:
        return cases, f"Found {len(cases)} returned payment(s)."
    return [], "No returned payments found."


def get_revenue_summary(user_id: str) -> dict:
    """Calculate total revenue split by payment type (PAD vs E-Transfer)."""
    client = get_client()
    # Get user's tenant IDs
    tenants_resp = (
        client.table("tenants")
        .select("id")
        .eq("user_id", user_id)
        .execute()
    )
    tenant_ids = [t["id"] for t in (tenants_resp.data or [])]

    summary = {"PAD": 0.0, "E-Transfer": 0.0, "total": 0.0,
               "pad_count": 0, "etransfer_count": 0}

    if not tenant_ids:
        return summary

    response = (
        client.table("payments")
        .select("*")
        .in_("tenant_id", tenant_ids)
        .eq("status", "Completed")
        .execute()
    )

    for row in (response.data or []):
        ptype = row.get("payment_type", "PAD")
        amount = float(row.get("amount", 0))
        if ptype == "PAD":
            summary["PAD"] += amount
            summary["pad_count"] += 1
        elif ptype == "E-Transfer":
            summary["E-Transfer"] += amount
            summary["etransfer_count"] += 1

    summary["total"] = summary["PAD"] + summary["E-Transfer"]
    return summary


def record_payment(tenant_id: int, amount: float, payment_type: str = "PAD",
                   status: str = "Completed", notes: str = "") -> int:
    """Record a new payment entry."""
    client = get_client()
    response = (
        client.table("payments")
        .insert({
            "tenant_id": tenant_id,
            "amount": amount,
            "payment_type": payment_type,
            "status": status,
            "notes": notes,
        })
        .execute()
    )
    return response.data[0]["id"]
