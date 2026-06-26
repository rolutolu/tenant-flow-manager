"""Virix — Main Entry Point

A property management application built with NiceGUI + Supabase.
Run with:  python main.py
"""

from app.auth import ensure_admin_exists

# Ensure default admin user exists in Supabase
ensure_admin_exists()

# Import all page modules so their @ui.page decorators register routes
from app.pages.login import login_page
from app.pages.dashboard import dashboard_page
from app.pages.intake import intake_page
from app.pages.lease import lease_page
from app.pages.marketing import marketing_page
from app.pages.properties import properties_page
from app.pages.import_data import import_page
from app.pages.finance import finance_page
from app.pages.maintenance import maintenance_page
from app.pages.actions import actions_page
from app.pages.admin import admin_page
from app.pages.settings import settings_page
from app.pages.audit_log import audit_log_page

from nicegui import ui, app as nicegui_app  # noqa: E402
from app.config import APP_TITLE, APP_HOST, APP_PORT, STORAGE_SECRET  # noqa: E402
from fastapi import Request  # noqa: E402

nicegui_app.add_static_files("/static", "static")

# ── Dark mode persistence endpoint ──────────────────────────────────────────
@nicegui_app.post("/api/dark-mode")
async def set_dark_mode(request: Request, enabled: str = "true"):
    """Persist dark mode preference to user storage."""
    from nicegui import app as _app
    _app.storage.user["dark_mode"] = (enabled.lower() == "true")
    return {"ok": True}

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title=APP_TITLE,
        host=APP_HOST,
        port=APP_PORT,
        dark=None,
        storage_secret=STORAGE_SECRET,
        reload=True,
        show_welcome_message=False,
    )
