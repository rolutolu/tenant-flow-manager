"""Tenant Flow Manager — Main Entry Point

A property management application built with NiceGUI.
Run with:  python main.py
"""

from app.models.database import init_db

# Initialize the database before importing pages
init_db()

# Import all page modules so their @ui.page decorators register routes
from app.pages import login, dashboard, intake, lease, finance, actions, marketing  # noqa: E402, F401

from nicegui import ui  # noqa: E402
from app.config import APP_TITLE, APP_HOST, APP_PORT  # noqa: E402

ui.run(
    title=APP_TITLE,
    host=APP_HOST,
    port=APP_PORT,
    dark=False,
    storage_secret="tenant-flow-manager-secret-key-change-me",
    reload=True,
)
