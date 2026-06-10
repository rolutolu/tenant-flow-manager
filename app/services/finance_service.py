"""Service for managing ledgers and transactions."""
import datetime
from app.models.database import get_client

def get_transactions(user_id: str, limit: int = 100) -> list[dict]:
    """Retrieve all transactions for a user."""
    client = get_client()
    response = client.table("transactions").select("*, tenants(name), units(unit_number)").eq("user_id", user_id).order("date", desc=True).limit(limit).execute()
    return response.data or []

def add_transaction(user_id: str, type: str, category: str, amount: float, tenant_id: int = None,
                    unit_id: str = None, date: str = None, notes: str = None,
                    status: str = None) -> str | None:
    """Add a new charge or payment to the ledger."""
    client = get_client()
    data = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "unit_id": unit_id,
        "type": type,
        "category": category,
        "amount": amount,
        "date": date or datetime.date.today().isoformat(),
        "notes": notes,
    }
    if status:
        data["status"] = status
    try:
        response = client.table("transactions").insert(data).execute()
        return response.data[0]["id"]
    except Exception as e:
        print(f"Error adding transaction: {e}")
        return None

def get_financial_summary(user_id: str) -> dict:
    """Calculate total income, outstanding charges, etc."""
    transactions = get_transactions(user_id, limit=1000)
    income = sum(t["amount"] for t in transactions if t["type"] == "Payment" and t["status"] == "Cleared")
    # Bug fix #4: Only count Pending charges as outstanding, not all charges
    outstanding = sum(t["amount"] for t in transactions if t["type"] == "Charge" and t["status"] == "Pending")
    return {"total_income": income, "outstanding_charges": outstanding}


# Bug fix #1: Dashboard imports this name — must match exactly
def get_revenue_summary(user_id: str) -> dict:
    """Alias for dashboard compatibility. Returns income, outstanding, and chart-ready data."""
    base = get_financial_summary(user_id)
    transactions = get_transactions(user_id, limit=1000)
    # For the revenue chart on the dashboard
    pad_total = sum(t["amount"] for t in transactions if t["type"] == "Payment" and t.get("notes", "") == "PAD")
    etransfer_total = sum(t["amount"] for t in transactions if t["type"] == "Payment" and t.get("notes", "") == "E-Transfer")
    return {
        "total": base["total_income"],
        "outstanding": base["outstanding_charges"],
        "PAD": pad_total,
        "E-Transfer": etransfer_total,
        "pad_count": sum(1 for t in transactions if t["type"] == "Payment" and t.get("notes", "") == "PAD"),
        "etransfer_count": sum(1 for t in transactions if t["type"] == "Payment" and t.get("notes", "") == "E-Transfer"),
    }

def update_transaction_status(txn_id: str, status: str) -> bool:
    """Update the status of a transaction (Pending, Cleared, Failed)."""
    client = get_client()
    try:
        client.table("transactions").update({"status": status}).eq("id", txn_id).execute()
        return True
    except Exception as e:
        print(f"Error updating transaction status: {e}")
        return False
