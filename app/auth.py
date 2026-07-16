"""Authentication — username/password login with bcrypt + role-based access."""

from typing import Callable, Any
from functools import wraps
import time
import bcrypt
from nicegui import app, ui
from app.models.database import get_client


# ── Session Helpers ────────────────────────────────────────────────────────────

# Bug fix #2: Must be defined BEFORE is_authenticated() uses it
SESSION_TIMEOUT_SECONDS = 900  # 15 minutes


def is_authenticated() -> bool:
    """Check if the user is currently logged in and session is active."""
    user_id = app.storage.user.get("user_id")
    last_activity = app.storage.user.get("last_activity", 0)

    # Check timeout
    if time.time() - last_activity > SESSION_TIMEOUT_SECONDS:
        # Clear the keys from the dict instead of unlinking the file
        for k in list(app.storage.user.keys()):
            del app.storage.user[k]
        return False

    # Update activity timestamp on every valid request
    app.storage.user["last_activity"] = time.time()
    return bool(user_id)


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


def is_superadmin() -> bool:
    """Return True if the current user has the superadmin role."""
    return get_user_role() == "superadmin"


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
    """Decorator factory that restricts access to specific roles.
    superadmin always passes through regardless of the role list.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not is_authenticated():
                ui.navigate.to("/login")
                return
            user_role = get_user_role()
            # superadmin is a superset of all roles
            if user_role == "superadmin" or user_role in roles:
                return func(*args, **kwargs)
            ui.notify("You don't have permission to access this page", type="negative")
            ui.navigate.to("/")
            return
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
            login(user["id"], user["username"], user["role"])
            return True, "Login successful."
    except ValueError:
        # Invalid hash in database — cannot verify
        return False, "Account error. Please contact your admin to reset your password."

    return False, "Invalid username or password."


def login(user_id: str, username: str, role: str):
    """Set the user session variables upon successful login."""
    app.storage.user.update(
        {
            "user_id": user_id,
            "username": username,
            "role": role,
            "last_activity": time.time(),
        }
    )


def logout():
    """Clear auth state and redirect to login."""
    # Clear the keys from the dict instead of unlinking the file
    for k in list(app.storage.user.keys()):
        del app.storage.user[k]
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
    # Note: superadmin can only be set via SQL — not creatable through the app

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
    
    caller_id = app.storage.user.get("user_id")
    if not caller_id:
        return False, "Unauthorized."
    
    client = get_client()
    try:
        # Re-check the caller's role directly from the DB
        caller_resp = client.table("users").select("role").eq("id", caller_id).execute()
        if not caller_resp.data or caller_resp.data[0]["role"] not in ("admin", "superadmin"):
            return False, "Unauthorized to perform password reset."

        hashed = hash_password(new_password)
        client.table("users").update({"password": hashed}).eq("id", user_id).execute()
        return True, "Password reset successfully."
    except Exception as e:
        return False, f"Failed to reset password: {str(e)}"


def delete_user(user_id: str) -> tuple[bool, str]:
    """Delete a user by ID."""
    caller_id = app.storage.user.get("user_id")
    if not caller_id:
        return False, "Unauthorized."

    client = get_client()
    try:
        # Re-check the caller's role directly from the DB
        caller_resp = client.table("users").select("role").eq("id", caller_id).execute()
        if not caller_resp.data or caller_resp.data[0]["role"] not in ("admin", "superadmin"):
            return False, "Unauthorized to delete users."

        client.table("users").delete().eq("id", user_id).execute()
        return True, "User deleted successfully."
    except Exception as e:
        return False, f"Failed to delete user: {str(e)}"



