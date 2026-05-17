"""One-time setup script — creates tables in Supabase and seeds the admin user.

Run: python setup_db.py

PREREQUISITE: You must first run the SQL in setup_supabase.sql in the
Supabase SQL Editor before running this script.
"""

import bcrypt
from dotenv import load_dotenv
load_dotenv(override=True)

from app.config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client


def main():
    print("=" * 60)
    print("Virix -- Database Setup")
    print("=" * 60)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\n[ERROR] SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return

    print(f"\n[*] Connecting to: {SUPABASE_URL}")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Test connection by checking if users table exists
    try:
        response = client.table("users").select("id").limit(1).execute()
        print("[OK] 'users' table found!")
    except Exception as e:
        print(f"\n[ERROR] 'users' table not found. Error: {e}")
        print("\n[!] You need to run the SQL schema first!")
        print("   1. Open: https://supabase.com/dashboard/project/hvyhnlqxlrzqifcbvhkp/sql/new")
        print("   2. Copy-paste the contents of setup_supabase.sql")
        print("   3. Click 'Run'")
        print("   4. Then run this script again")
        return

    # Check if admin user already exists
    existing = client.table("users").select("id, username").eq("username", "admin").execute()
    if existing.data:
        print(f"[INFO] Admin user already exists (ID: {existing.data[0]['id'][:8]}...)")
        # Update the password in case it was a bad hash
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        client.table("users").update({"password": hashed}).eq("username", "admin").execute()
        print("[OK] Admin password reset to 'admin123'")
    else:
        # Create default admin user
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        client.table("users").insert({
            "username": "admin",
            "password": hashed,
            "role": "admin",
        }).execute()
        print("[OK] Default admin user created:")
        print("   Username: admin")
        print("   Password: admin123")

    # Create test manager user
    existing_mgr = client.table("users").select("id").eq("username", "manager1").execute()
    if not existing_mgr.data:
        hashed = bcrypt.hashpw("manager123".encode(), bcrypt.gensalt()).decode()
        client.table("users").insert({
            "username": "manager1",
            "password": hashed,
            "role": "manager",
        }).execute()
        print("[OK] Test manager user created (manager1 / manager123)")

    # Create test viewer user
    existing_viewer = client.table("users").select("id").eq("username", "viewer1").execute()
    if not existing_viewer.data:
        hashed = bcrypt.hashpw("viewer123".encode(), bcrypt.gensalt()).decode()
        client.table("users").insert({
            "username": "viewer1",
            "password": hashed,
            "role": "viewer",
        }).execute()
        print("[OK] Test viewer user created (viewer1 / viewer123)")

    # Verify all tables
    tables = ["users", "tenants", "payments", "documents"]
    print("\n[*] Table verification:")
    for table in tables:
        try:
            resp = client.table(table).select("*", count="exact").limit(0).execute()
            print(f"   [OK] {table}: {resp.count} row(s)")
        except Exception as e:
            print(f"   [ERROR] {table}: {e}")

    print("\n" + "=" * 60)
    print("Setup complete! Run the app with: python main.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
