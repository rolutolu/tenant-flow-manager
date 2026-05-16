"""Service for managing ledgers, transactions, and Stripe integration."""
import datetime
from app.models.database import get_client

def get_transactions(user_id: str, limit: int = 100) -> list[dict]:
    """Retrieve all transactions for a user."""
    client = get_client()
    response = client.table("transactions").select("*, tenants(name), units(unit_number)").eq("user_id", user_id).order("date", desc=True).limit(limit).execute()
    return response.data or []

def add_transaction(user_id: str, type: str, category: str, amount: float, tenant_id: int = None, unit_id: str = None, date: str = None, notes: str = None) -> str | None:
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
        "notes": notes
    }
    try:
        response = client.table("transactions").insert(data).execute()
        return response.data[0]["id"]
    except Exception as e:
        print(f"Error adding transaction: {e}")
        return None

def get_financial_summary(user_id: str) -> dict:
    """Calculate total income, pending charges, etc."""
    transactions = get_transactions(user_id, limit=1000)
    income = sum(t["amount"] for t in transactions if t["type"] == "Payment" and t["status"] == "Cleared")
    outstanding = sum(t["amount"] for t in transactions if t["type"] == "Charge" and t["status"] == "Cleared")
    return {"total_income": income, "outstanding_charges": outstanding}

# Stripe Integration Stubs
def create_checkout_session(amount: float, description: str, success_url: str, cancel_url: str) -> str:
    """Create a Stripe checkout session for a payment."""
    # This requires the `stripe` python package and a Stripe Secret Key
    # For now, we simulate returning a checkout URL
    return f"https://checkout.stripe.com/pay/cs_test_mock?amount={amount}&desc={description}"
