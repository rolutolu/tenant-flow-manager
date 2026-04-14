"""Authentication middleware — single shared password gatekeeper."""

from functools import wraps
from nicegui import app, ui
from app.config import APP_PASSWORD


def is_authenticated() -> bool:
    """Check if the current user is authenticated."""
    return app.storage.user.get("authenticated", False)


def require_auth(func):
    """Decorator that redirects unauthenticated users to the login page."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            ui.navigate.to("/login")
            return
        return func(*args, **kwargs)
    return wrapper


def attempt_login(password: str) -> bool:
    """Validate the password and set the auth state."""
    if password == APP_PASSWORD:
        app.storage.user.update({"authenticated": True})
        return True
    return False
