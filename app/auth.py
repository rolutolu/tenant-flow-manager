"""Authentication — username/password login with bcrypt + role-based access."""

from typing import Callable, Any
from functools import wraps
import time
import secrets
import bcrypt
from nicegui import app, ui
from app.models.database import get_client


# ── Session Helpers ────────────────────────────────────────────────────────────

# Bug fix #2: Must be defined BEFORE is_authenticated() uses it
SESSION_TIMEOUT_SECONDS = 900  # 15 minutes


def is_authenticated() -> bool:
    """Check if the user is currently logged in, session is active, and MFA is complete."""
    user_id = app.storage.user.get("user_id")
    last_activity = app.storage.user.get("last_activity", 0)

    # Check timeout
    if time.time() - last_activity > SESSION_TIMEOUT_SECONDS:
        app.storage.user.clear()  # Force logout
        return False

    if not user_id:
        return False

    # Block admins who haven't completed MFA
    role = app.storage.user.get("role")
    if role == "admin" and not app.storage.user.get("mfa_verified", False):
        return False

    # Update activity timestamp on every valid request
    app.storage.user["last_activity"] = time.time()
    return True


def get_current_user() -> dict:
    """Return the current user's session data."""
    return {
        "user_id": app.storage.user.get("user_id"),
        "username": app.storage.user.get("username"),
        "role": app.storage.user.get("role"),
    }


# (Moved SESSION_TIMEOUT_SECONDS to the top of the block above)


def get_user_id() -> str | None:
    """Get the current user's UUID from app.storage.user."""
    return app.storage.user.get("user_id")


def get_user_role() -> str | None:
    """Return the current user's role."""
    return app.storage.user.get("role")


# ── Decorators ─────────────────────────────────────────────────────────────────

def require_auth(func):
    """Decorator that redirects unauthenticated users to the login page."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            ui.navigate.to("/login")
            return
        return func(*args, **kwargs)
    return wrapper


def require_role(*roles):
    """Decorator factory that restricts access to specific roles."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not is_authenticated():
                ui.navigate.to("/login")
                return
            user_role = get_user_role()
            if user_role not in roles:
                ui.notify("You don't have permission to access this page", type="negative")
                ui.navigate.to("/")
                return
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ── Login / Logout ─────────────────────────────────────────────────────────────

def attempt_login(username: str, password: str) -> tuple[bool, str]:
    """Validate credentials and set the auth state."""
    if not username or not password:
        return False, "Username and password are required."

    client = get_client()
    response = client.table("users").select("*").eq("username", username).execute()

    if not response.data:
        return False, "Invalid username or password."

    user = response.data[0]
    stored_hash = user["password"].encode()

    try:
        if bcrypt.checkpw(password.encode(), stored_hash):
            phone = user.get("phone_number", "") or ""
            login(user["id"], user["username"], user["role"], phone_number=phone)
            return True, "Login successful."
    except (ValueError, Exception):
        # Invalid hash in database — cannot verify
        return False, "Account error. Please contact your admin to reset your password."

    return False, "Invalid username or password."


def login(user_id: str, username: str, role: str, phone_number: str = ""):
    """Set the user session variables upon successful login.

    For admin users, generates a one-time passcode, sends it via SMS,
    and stores pending MFA state. The /mfa page verifies the code.
    """
    app.storage.user.update(
        {
            "user_id": user_id,
            "username": username,
            "role": role,
            "last_activity": time.time(),
            "mfa_verified": False,
            "mfa_phone": phone_number,
        }
    )

    if role == "admin":
        # Generate a secure 6-digit OTP and store it with a 10-minute expiry
        otp = str(secrets.randbelow(900000) + 100000)  # always 6 digits
        app.storage.user["mfa_otp"] = otp
        app.storage.user["mfa_otp_expiry"] = time.time() + 600  # 10 min

        show_code_on_page = False
        if phone_number:
            from app.services.notification_service import send_mfa_sms
            ok, msg = send_mfa_sms(phone_number, otp)
            # Simulated SMS or failed send — show code on MFA page (reload hides terminal prints)
            show_code_on_page = (not ok) or ("Simulated" in msg)
            if not ok:
                print(f"[MFA WARNING] Could not send SMS to {phone_number}: {msg}", flush=True)
            else:
                print(f"[MFA] OTP sent to {phone_number} for admin '{username}'", flush=True)
        else:
            show_code_on_page = True
            print(
                f"[MFA DEV] OTP for admin '{username}': {otp} "
                f"(add phone_number to your profile to receive via SMS)",
                flush=True,
            )
        app.storage.user["mfa_show_code"] = show_code_on_page


def logout():
    """Clear auth state and redirect to login."""
    # Bug fix #3: Use clear() to remove ALL session keys cleanly
    app.storage.user.clear()
    ui.navigate.to("/login")


# ── Password Hashing ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# ── User Management ───────────────────────────────────────────────────────────

def create_user(username: str, password: str, role: str,
                created_by: str | None = None) -> tuple[bool, str]:
    """Create a new user account."""
    if not username or not password:
        return False, "Username and password are required."

    if role not in ("admin", "manager", "viewer"):
        return False, "Invalid role. Must be admin, manager, or viewer."

    client = get_client()

    # Check if username already exists
    existing = client.table("users").select("id").eq("username", username).execute()
    if existing.data:
        return False, f"Username '{username}' already exists."

    hashed = hash_password(password)
    data = {
        "username": username,
        "password": hashed,
        "role": role,
    }
    if created_by:
        data["created_by"] = created_by

    try:
        client.table("users").insert(data).execute()
        return True, f"User '{username}' created with role '{role}'."
    except Exception as e:
        return False, f"Failed to create user: {str(e)}"


def get_all_users() -> list[dict]:
    """Return all users (without password hashes)."""
    client = get_client()
    response = (
        client.table("users")
        .select("id, username, role, created_at, created_by")
        .order("created_at")
        .execute()
    )
    return response.data or []


def reset_user_password(user_id: str, new_password: str) -> tuple[bool, str]:
    """Reset a user's password (admin-only operation)."""
    if not new_password:
        return False, "New password is required."
    client = get_client()
    try:
        hashed = hash_password(new_password)
        client.table("users").update({"password": hashed}).eq("id", user_id).execute()
        return True, "Password reset successfully."
    except Exception as e:
        return False, f"Failed to reset password: {str(e)}"


def delete_user(user_id: str) -> tuple[bool, str]:
    """Delete a user by ID."""
    client = get_client()
    try:
        client.table("users").delete().eq("id", user_id).execute()
        return True, "User deleted successfully."
    except Exception as e:
        return False, f"Failed to delete user: {str(e)}"


def ensure_admin_exists():
    """Create or fix the default admin user in the database."""
    client = get_client()

    # Check if admin user exists
    response = client.table("users").select("id, password").eq("username", "admin").execute()

    if response.data:
        # Admin exists — verify the hash is valid bcrypt
        stored = response.data[0]["password"]
        try:
            bcrypt.checkpw(b"test", stored.encode())
        except (ValueError, Exception):
            # Bad hash — reset it
            hashed = hash_password("admin123")
            client.table("users").update({"password": hashed}).eq("username", "admin").execute()
            print("[INFO] Admin password was invalid and has been reset to 'admin123'")
    else:
        # No admin — check if any users exist at all
        any_users = client.table("users").select("id").limit(1).execute()
        if not any_users.data:
            hashed = hash_password("admin123")
            client.table("users").insert({
                "username": "admin",
                "password": hashed,
                "role": "admin",
            }).execute()
            print("[INFO] Default admin user created (username: admin, password: admin123)")
