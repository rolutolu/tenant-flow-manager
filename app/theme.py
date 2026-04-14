"""Shared UI theme — header, sidebar navigation, and consistent page wrapper."""

from contextlib import contextmanager
from nicegui import ui, app


# ── Brand Colors ───────────────────────────────────────────────────────────────
PRIMARY = "#1B2A4A"       # Deep navy
ACCENT = "#3B82F6"        # Bright blue
SURFACE = "#F8FAFC"       # Light gray background
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#1E293B"
TEXT_SECONDARY = "#64748B"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"

NAV_ITEMS = [
    {"label": "Dashboard",  "icon": "dashboard",        "path": "/"},
    {"label": "Intake",     "icon": "person_add",       "path": "/intake"},
    {"label": "Leases",     "icon": "description",      "path": "/lease"},
    {"label": "Finance",    "icon": "account_balance",   "path": "/finance"},
    {"label": "Actions",    "icon": "notifications_active", "path": "/actions"},
    {"label": "Marketing",  "icon": "campaign",         "path": "/marketing"},
]


@contextmanager
def page_layout(title: str = ""):
    """Context manager that wraps page content with header + sidebar navigation."""
    ui.colors(primary=PRIMARY, secondary=ACCENT, accent=ACCENT, positive=SUCCESS,
              negative=DANGER, warning=WARNING)

    # ── Header ─────────────────────────────────────────────────────────────
    with ui.header().classes("items-center justify-between px-6 shadow-md").style(
        f"background: linear-gradient(135deg, {PRIMARY} 0%, #2D3A5C 100%)"
    ):
        with ui.row().classes("items-center gap-3"):
            ui.icon("apartment", size="28px").classes("text-white")
            ui.label("Tenant Flow Manager").classes(
                "text-white text-lg font-bold tracking-wide"
            )
        with ui.row().classes("items-center gap-2"):
            if title:
                ui.label(title).classes("text-blue-200 text-sm")
            ui.button(icon="logout", on_click=_logout).props(
                "flat round color=white size=sm"
            ).tooltip("Sign Out")

    # ── Sidebar ────────────────────────────────────────────────────────────
    with ui.left_drawer(value=True, bordered=True).classes("p-4").style(
        f"background: {CARD_BG}; border-right: 1px solid #E2E8F0"
    ):
        ui.label("NAVIGATION").classes(
            "text-xs font-bold tracking-widest mb-4"
        ).style(f"color: {TEXT_SECONDARY}")

        for item in NAV_ITEMS:
            with ui.row().classes(
                "items-center gap-3 px-3 py-2 rounded-lg cursor-pointer "
                "hover:bg-blue-50 transition-all w-full"
            ).on("click", lambda _, p=item["path"]: ui.navigate.to(p)):
                ui.icon(item["icon"], size="20px").style(f"color: {ACCENT}")
                ui.label(item["label"]).classes("text-sm font-medium").style(
                    f"color: {TEXT_PRIMARY}"
                )

        # Footer
        ui.space()
        ui.separator().classes("my-3")
        ui.label("v2.0 — NiceGUI Edition").classes("text-xs").style(
            f"color: {TEXT_SECONDARY}"
        )

    # ── Main Content ───────────────────────────────────────────────────────
    with ui.column().classes("w-full p-6 gap-6").style(f"background: {SURFACE}; min-height: 100vh"):
        yield


def _logout():
    """Clear auth state and redirect to login."""
    app.storage.user.update({"authenticated": False})
    ui.navigate.to("/login")


# ── Reusable UI Components ─────────────────────────────────────────────────────

def metric_card(label: str, value, icon: str = "info", color: str = ACCENT):
    """A styled metric card for dashboards."""
    with ui.card().classes("p-5 rounded-xl shadow-sm hover:shadow-md transition-shadow").style(
        f"background: {CARD_BG}; border: 1px solid #E2E8F0; min-width: 200px"
    ):
        with ui.row().classes("items-center gap-3"):
            with ui.element("div").classes("rounded-lg p-2").style(
                f"background: {color}15"
            ):
                ui.icon(icon, size="24px").style(f"color: {color}")
            with ui.column().classes("gap-0"):
                ui.label(str(value)).classes("text-2xl font-bold").style(
                    f"color: {TEXT_PRIMARY}"
                )
                ui.label(label).classes("text-xs").style(f"color: {TEXT_SECONDARY}")


def section_header(title: str, subtitle: str = ""):
    """A styled section header."""
    with ui.column().classes("gap-0 mb-2"):
        ui.label(title).classes("text-xl font-bold").style(f"color: {TEXT_PRIMARY}")
        if subtitle:
            ui.label(subtitle).classes("text-sm").style(f"color: {TEXT_SECONDARY}")
