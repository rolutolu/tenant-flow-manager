"""Virix — Main Entry Point

A property management application built with NiceGUI + Supabase.
Run with:  python main.py
"""

from app.auth import ensure_admin_exists

# Ensure default admin user exists in Supabase (will run on startup event)

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
from app.pages.register import register_page


from nicegui import ui, app as nicegui_app  # noqa: E402
from app.config import APP_TITLE, APP_HOST, APP_PORT, STORAGE_SECRET  # noqa: E402


nicegui_app.add_static_files("/static", "static")
nicegui_app.on_startup(ensure_admin_exists)


if __name__ in {"__main__", "__mp_main__"}:
    import os
    is_dev = os.getenv("PORT") is None or os.getenv("DEBUG", "false").lower() == "true"
    ui.run(
        title=APP_TITLE,
        host=APP_HOST,
        port=APP_PORT,
        dark=None,
        storage_secret=STORAGE_SECRET,
        reload=is_dev,
        show_welcome_message=False,
    )
