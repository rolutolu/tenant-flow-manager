"""Seed the Supabase database with sample data for testing.

Creates:
  - 3 user accounts: superadmin, admin, manager
  - 3 properties with 8 units
  - 5 tenants assigned to occupied units
  - Sample transactions (rent payments)
  - Sample maintenance requests

Usage:  python create_dummy_data.py
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from app.models.database import get_client
from app.auth import hash_password


def create_dummy_data():
    """Seed Supabase with sample users, properties, units, tenants, and transactions."""
    client = get_client()

    # ── Check for existing data ────────────────────────────────────────────
    existing = client.table("users").select("id").limit(1).execute()
    if existing.data:
        print("Database already has user data. Skipping seed.")
        print("To re-seed, manually clear the tables first via Supabase SQL Editor.")
        return

    today = datetime.now()

    # ── 1. Users ──────────────────────────────────────────────────────────
    users = [
        {"username": "superadmin", "password": hash_password("Super@2025!"), "role": "superadmin"},
        {"username": "admin",      "password": hash_password("Admin@2025!"),  "role": "admin"},
        {"username": "manager1",   "password": hash_password("Manager@2025!"), "role": "manager"},
    ]
    resp = client.table("users").insert(users).execute()
    user_map = {u["username"]: u["id"] for u in resp.data}
    admin_id = user_map["admin"]
    print(f"  ✓ Created {len(users)} users: superadmin / admin / manager1")
    print(f"    Passwords: Super@2025!  /  Admin@2025!  /  Manager@2025!")

    # ── 2. Properties ─────────────────────────────────────────────────────
    properties = [
        {"user_id": admin_id, "name": "Maple Heights", "address": "120 Maple Ave, Toronto, ON"},
        {"user_id": admin_id, "name": "Lakeview Towers", "address": "88 Lakeshore Blvd, Toronto, ON"},
        {"user_id": admin_id, "name": "Riverside Commons", "address": "55 River Rd, Mississauga, ON"},
    ]
    resp = client.table("properties").insert(properties).execute()
    prop_map = {p["name"]: p["id"] for p in resp.data}
    print(f"  ✓ Created {len(properties)} properties")

    # ── 3. Units ──────────────────────────────────────────────────────────
    units_data = [
        # Maple Heights
        {"property_id": prop_map["Maple Heights"], "unit_number": "101", "default_rent": 1500, "status": "Occupied"},
        {"property_id": prop_map["Maple Heights"], "unit_number": "102", "default_rent": 1600, "status": "Occupied"},
        {"property_id": prop_map["Maple Heights"], "unit_number": "201", "default_rent": 1550, "status": "Vacant"},
        # Lakeview Towers
        {"property_id": prop_map["Lakeview Towers"], "unit_number": "301", "default_rent": 1800, "status": "Occupied"},
        {"property_id": prop_map["Lakeview Towers"], "unit_number": "302", "default_rent": 1700, "status": "Occupied"},
        {"property_id": prop_map["Lakeview Towers"], "unit_number": "401", "default_rent": 1900, "status": "Vacant"},
        # Riverside Commons
        {"property_id": prop_map["Riverside Commons"], "unit_number": "A1", "default_rent": 1450, "status": "Occupied"},
        {"property_id": prop_map["Riverside Commons"], "unit_number": "A2", "default_rent": 1450, "status": "Notice"},
    ]
    resp = client.table("units").insert(units_data).execute()
    unit_map = {f"{u['property_id']}_{u['unit_number']}": u["id"] for u in resp.data}
    print(f"  ✓ Created {len(units_data)} units (5 occupied, 2 vacant, 1 notice)")

    # Helper to get unit ID by property name + unit number
    def uid(prop_name, unit_num):
        return unit_map[f"{prop_map[prop_name]}_{unit_num}"]

    # ── 4. Tenants ────────────────────────────────────────────────────────
    tenants = [
        {
            "user_id": admin_id, "name": "John Smith", "unit": "101",
            "unit_id": uid("Maple Heights", "101"), "rent_amount": 1500,
            "email": "john.smith@email.com",
            "lease_start": (today - timedelta(days=200)).strftime("%Y-%m-%d"),
            "lease_end": (today + timedelta(days=165)).strftime("%Y-%m-%d"),
            "banking_set_up": "Yes", "move_in_status": "Completed", "lease_signed": "Yes",
        },
        {
            "user_id": admin_id, "name": "Jane Doe", "unit": "102",
            "unit_id": uid("Maple Heights", "102"), "rent_amount": 1600,
            "email": "jane.doe@email.com",
            "lease_start": (today - timedelta(days=100)).strftime("%Y-%m-%d"),
            "lease_end": (today + timedelta(days=265)).strftime("%Y-%m-%d"),
            "banking_set_up": "Yes", "move_in_status": "Completed", "lease_signed": "Yes",
        },
        {
            "user_id": admin_id, "name": "Carlos Rivera", "unit": "301",
            "unit_id": uid("Lakeview Towers", "301"), "rent_amount": 1800,
            "email": "carlos.r@email.com",
            "lease_start": (today - timedelta(days=50)).strftime("%Y-%m-%d"),
            "lease_end": (today + timedelta(days=315)).strftime("%Y-%m-%d"),
            "banking_set_up": "Yes", "move_in_status": "Completed", "lease_signed": "No",
        },
        {
            "user_id": admin_id, "name": "Diana Chen", "unit": "302",
            "unit_id": uid("Lakeview Towers", "302"), "rent_amount": 1700,
            "email": "diana.chen@email.com",
            "lease_start": (today - timedelta(days=300)).strftime("%Y-%m-%d"),
            "lease_end": (today + timedelta(days=65)).strftime("%Y-%m-%d"),
            "banking_set_up": "Yes", "move_in_status": "Completed", "lease_signed": "Yes",
        },
        {
            "user_id": admin_id, "name": "Alice Tremblay", "unit": "A1",
            "unit_id": uid("Riverside Commons", "A1"), "rent_amount": 1450,
            "email": "alice.t@email.com",
            "lease_start": (today - timedelta(days=350)).strftime("%Y-%m-%d"),
            "lease_end": (today + timedelta(days=15)).strftime("%Y-%m-%d"),
            "banking_set_up": "No", "move_in_status": "Completed", "lease_signed": "Yes",
        },
    ]
    resp = client.table("tenants").insert(tenants).execute()
    tenant_map = {t["name"]: t["id"] for t in resp.data}
    print(f"  ✓ Created {len(tenants)} tenants")

    # ── 5. Transactions (rent payments) ───────────────────────────────────
    transactions = [
        {"user_id": admin_id, "tenant_id": tenant_map["John Smith"],
         "unit_id": uid("Maple Heights", "101"),
         "type": "Payment", "category": "Rent", "amount": 1500, "status": "Cleared",
         "date": (today - timedelta(days=30)).strftime("%Y-%m-%d"), "notes": "PAD"},
        {"user_id": admin_id, "tenant_id": tenant_map["John Smith"],
         "unit_id": uid("Maple Heights", "101"),
         "type": "Payment", "category": "Rent", "amount": 1500, "status": "Cleared",
         "date": today.strftime("%Y-%m-%d"), "notes": "PAD"},
        {"user_id": admin_id, "tenant_id": tenant_map["Jane Doe"],
         "unit_id": uid("Maple Heights", "102"),
         "type": "Payment", "category": "Rent", "amount": 1600, "status": "Cleared",
         "date": (today - timedelta(days=30)).strftime("%Y-%m-%d"), "notes": "PAD"},
        {"user_id": admin_id, "tenant_id": tenant_map["Jane Doe"],
         "unit_id": uid("Maple Heights", "102"),
         "type": "Payment", "category": "Rent", "amount": 1600, "status": "Failed",
         "date": today.strftime("%Y-%m-%d"), "notes": "NSF — Insufficient funds"},
        {"user_id": admin_id, "tenant_id": tenant_map["Carlos Rivera"],
         "unit_id": uid("Lakeview Towers", "301"),
         "type": "Payment", "category": "Rent", "amount": 1800, "status": "Cleared",
         "date": today.strftime("%Y-%m-%d"), "notes": "E-Transfer"},
        {"user_id": admin_id, "tenant_id": tenant_map["Diana Chen"],
         "unit_id": uid("Lakeview Towers", "302"),
         "type": "Payment", "category": "Rent", "amount": 1700, "status": "Cleared",
         "date": today.strftime("%Y-%m-%d"), "notes": "PAD"},
        {"user_id": admin_id, "tenant_id": tenant_map["Alice Tremblay"],
         "unit_id": uid("Riverside Commons", "A1"),
         "type": "Charge", "category": "Rent", "amount": 1450, "status": "Pending",
         "date": today.strftime("%Y-%m-%d"), "notes": "Monthly rent — pending"},
    ]
    client.table("transactions").insert(transactions).execute()
    print(f"  ✓ Created {len(transactions)} transactions")

    # ── 6. Maintenance requests ───────────────────────────────────────────
    maintenance = [
        {
            "user_id": admin_id, "property_id": prop_map["Maple Heights"],
            "unit_id": uid("Maple Heights", "101"),
            "title": "Leaking kitchen faucet", "description": "Slow drip from main tap",
            "priority": "Medium", "status": "Open",
            "reported_at": (today - timedelta(days=3)).isoformat(),
        },
        {
            "user_id": admin_id, "property_id": prop_map["Lakeview Towers"],
            "unit_id": uid("Lakeview Towers", "302"),
            "title": "Broken thermostat", "description": "Unit heater not responding to thermostat",
            "priority": "High", "status": "In Progress",
            "reported_at": (today - timedelta(days=7)).isoformat(),
        },
    ]
    client.table("maintenance_requests").insert(maintenance).execute()
    print(f"  ✓ Created {len(maintenance)} maintenance requests")

    print("\n✅ Database seeded successfully!")
    print("   Log in with:  superadmin / Super@2025!")
    print("                 admin      / Admin@2025!")
    print("                 manager1   / Manager@2025!")


if __name__ == "__main__":
    create_dummy_data()
