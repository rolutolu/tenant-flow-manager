"""Generate dummy data in the SQLite database for testing."""

import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from app.config import DATA_DIR
from app.models.database import init_db, get_connection


def create_dummy_data():
    """Seed the database with sample tenants and payments."""
    DATA_DIR.mkdir(exist_ok=True)
    init_db()

    conn = get_connection()
    try:
        # Check if data already exists
        count = conn.execute("SELECT COUNT(*) AS cnt FROM tenants").fetchone()["cnt"]
        if count > 0:
            print(f"Database already has {count} tenant(s). Skipping seed.")
            return

        today = datetime.now()

        # ── Tenants ────────────────────────────────────────────────────────
        tenants = [
            ("John Smith", "Unit_101", 1500,
             (today - timedelta(days=200)).strftime("%Y-%m-%d"),
             (today + timedelta(days=165)).strftime("%Y-%m-%d"),
             "", "Yes", "Completed", "Yes"),
            ("Jane Doe", "Unit_102", 1600,
             (today - timedelta(days=100)).strftime("%Y-%m-%d"),
             (today + timedelta(days=265)).strftime("%Y-%m-%d"),
             "", "Yes", "Completed", "Yes"),
            ("Alice Bob", "Unit_201", 1550,
             (today - timedelta(days=350)).strftime("%Y-%m-%d"),
             (today + timedelta(days=15)).strftime("%Y-%m-%d"),
             "", "No", "Completed", "Yes"),
            ("Carlos Rivera", "Unit_202", 1700,
             (today - timedelta(days=50)).strftime("%Y-%m-%d"),
             (today + timedelta(days=315)).strftime("%Y-%m-%d"),
             "", "Yes", "Completed", "No"),
            ("Diana Chen", "Unit_301", 1450,
             (today - timedelta(days=300)).strftime("%Y-%m-%d"),
             (today + timedelta(days=65)).strftime("%Y-%m-%d"),
             "", "Yes", "Completed", "Yes"),
        ]

        conn.executemany(
            """INSERT INTO tenants
               (name, unit, rent_amount, lease_start, lease_end,
                bank_info, banking_set_up, move_in_status, lease_signed)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            tenants
        )

        # ── Sample Payments ────────────────────────────────────────────────
        payments = [
            (1, 1500, "PAD", "Completed", (today - timedelta(days=30)).strftime("%Y-%m-%d"), ""),
            (1, 1500, "PAD", "Completed", today.strftime("%Y-%m-%d"), ""),
            (2, 1600, "PAD", "Completed", (today - timedelta(days=30)).strftime("%Y-%m-%d"), ""),
            (2, 1600, "PAD", "Returned", today.strftime("%Y-%m-%d"), "NSF — Insufficient funds"),
            (3, 1550, "E-Transfer", "Completed", today.strftime("%Y-%m-%d"), "Manual e-transfer"),
            (4, 1700, "PAD", "Completed", today.strftime("%Y-%m-%d"), ""),
            (5, 1450, "PAD", "Completed", (today - timedelta(days=30)).strftime("%Y-%m-%d"), ""),
            (5, 1450, "PAD", "Completed", today.strftime("%Y-%m-%d"), ""),
        ]

        conn.executemany(
            """INSERT INTO payments
               (tenant_id, amount, payment_type, status, date, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            payments
        )

        conn.commit()
        print(f"Created {len(tenants)} tenants and {len(payments)} payment records.")
        print(f"Database: {DATA_DIR / 'tenants.db'}")

    finally:
        conn.close()


if __name__ == "__main__":
    create_dummy_data()
