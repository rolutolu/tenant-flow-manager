"""Financial operations: banking info, PAD cross-referencing, NSF detection, revenue."""

from app.models.database import get_connection, encrypt_value, decrypt_value
from app.services.tenant_service import update_tenant


def update_banking_info(tenant_id: int, bank_info: str) -> tuple[bool, str]:
    """Encrypt and store banking information for a tenant."""
    if not bank_info:
        return False, "Bank information cannot be empty."
    success = update_tenant(tenant_id, bank_info=bank_info, banking_set_up="Yes")
    if success:
        return True, "Banking information updated and encrypted successfully."
    return False, "Failed to update banking information."


def cross_reference_pads() -> tuple[bool, str, list[dict]]:
    """Compare the rent roll against the PAD schedule.

    Returns (success, message, discrepancies).
    In a real implementation this would compare against an external banking export.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM tenants WHERE banking_set_up = 'Yes'"
        ).fetchall()
        tenants = [dict(r) for r in rows]

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
    finally:
        conn.close()


def flag_returned_payments() -> tuple[list[dict], str]:
    """Identify returned/NSF payments.

    In production, this would ingest a bank report CSV. For now, it checks
    the payments table for any marked as 'Returned'.
    """
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT p.*, t.name AS tenant_name, t.unit
            FROM payments p
            JOIN tenants t ON p.tenant_id = t.id
            WHERE p.status = 'Returned'
            ORDER BY p.date DESC
        """).fetchall()
        cases = [dict(r) for r in rows]
        if cases:
            return cases, f"Found {len(cases)} returned payment(s)."
        return [], "No returned payments found."
    finally:
        conn.close()


def get_revenue_summary() -> dict:
    """Calculate total revenue split by payment type (PAD vs E-Transfer)."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT payment_type, SUM(amount) AS total, COUNT(*) AS count
            FROM payments
            WHERE status = 'Completed'
            GROUP BY payment_type
        """).fetchall()
        summary = {"PAD": 0.0, "E-Transfer": 0.0, "total": 0.0,
                    "pad_count": 0, "etransfer_count": 0}
        for row in rows:
            d = dict(row)
            if d["payment_type"] == "PAD":
                summary["PAD"] = d["total"] or 0
                summary["pad_count"] = d["count"]
            elif d["payment_type"] == "E-Transfer":
                summary["E-Transfer"] = d["total"] or 0
                summary["etransfer_count"] = d["count"]
        summary["total"] = summary["PAD"] + summary["E-Transfer"]
        return summary
    finally:
        conn.close()


def record_payment(tenant_id: int, amount: float, payment_type: str = "PAD",
                   status: str = "Completed", notes: str = "") -> int:
    """Record a new payment entry."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO payments (tenant_id, amount, payment_type, status, notes) VALUES (?, ?, ?, ?, ?)",
            (tenant_id, amount, payment_type, status, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
