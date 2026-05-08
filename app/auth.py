"""Authentication — username/password login with bcrypt + role-based access."""

from functools import wraps
import bcrypt
from nicegui import app, ui
from app.models.database import get_client


# ── Session Helpers ────────────────────────────────────────────────────────────

def is_authenticated() -> bool:
    """Check if the current user is authenticated."""
    return app.storage.user.get("authenticated", False)


def get_current_user() -> dict:
    """Return the current user's session data."""
    return {
        "user_id": app.storage.user.get("user_id"),
        "username": app.storage.user.get("username"),
        "role": app.storage.user.get("role"),
    }


def get_user_id() -> str | None:
    """Return the current user's ID."""
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
            app.storage.user.update({
                "authenticated": True,
                "user_id": user["id"],
                "username": user["username"],
                "role": user["role"],
            })
            return True, "Login successful."
    except (ValueError, Exception):
        # Invalid hash in database — cannot verify
        return False, "Account error. Please contact your admin to reset your password."

    return False, "Invalid username or password."


def logout():
    """Clear auth state and redirect to login."""
    app.storage.user.update({
        "authenticated": False,
        "user_id": None,
        "username": None,
        "role": None,
    })
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
