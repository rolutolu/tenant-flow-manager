"""Shared UI theme — premium design with header, sidebar, and page wrapper."""

from contextlib import contextmanager
from nicegui import ui, app


# ── Brand Colors (refined palette) ─────────────────────────────────────────────
PRIMARY = "#0F172A"       # Rich dark navy
PRIMARY_LIGHT = "#1E293B" # Slightly lighter navy
ACCENT = "#6366F1"        # Indigo / violet accent
ACCENT_LIGHT = "#818CF8"  # Lighter accent for hovers
SURFACE = "#F1F5F9"       # Cool gray background
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#0F172A"
TEXT_SECONDARY = "#64748B"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
BORDER = "#E2E8F0"

# ── Global Styles ──────────────────────────────────────────────────────────────
GLOBAL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    cursor: default;
}
input, button, select, textarea, label,
.q-btn, .q-field, .q-card, .q-tab, .q-table,
.q-toolbar, .q-drawer, .q-page {
    font-family: inherit !important;
}

/* Preserve Material Icons font */
.material-icons, .q-icon, [class*="material-icons"],
.notranslate { font-family: 'Material Icons' !important; }

/* Remove NiceGUI watermark logo */
.nicegui-logo { display: none !important; }
a[href="https://nicegui.io"] { display: none !important; }
div[style*="nicegui"] { display: none !important; }

/* Fix "white bar" / header borders */
.q-header { border: none !important; box-shadow: 0 4px 20px rgba(0,0,0,0.15) !important; }
.q-layout__section--marginal { background-color: transparent !important; }

/* Blur overlay for locked sections */
.blur-content { filter: blur(8px); pointer-events: none; user-select: none; transition: all 0.5s ease; }
.lock-overlay {
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    z-index: 100; display: flex; align-items: center; justify-content: center;
    background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(4px);
}

/* Prevent text cursor on non-interactive areas */
.q-page, .q-layout, .q-drawer, .q-header { cursor: default; user-select: none; }
input, textarea, .q-field__native { cursor: text; user-select: auto; }

/* Smooth scrolling */
html { scroll-behavior: smooth; }

/* Card hover lift effect */
.card-hover { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.card-hover:hover { transform: translateY(-2px); box-shadow: 0 12px 40px rgba(0,0,0,0.08) !important; }

/* Glass effect */
.glass {
    background: rgba(255, 255, 255, 0.7) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
}

/* Sidebar nav item hover */
.nav-item {
    transition: all 0.2s ease;
    border-radius: 10px;
}
.nav-item:hover {
    background: rgba(99, 102, 241, 0.08) !important;
    transform: translateX(4px);
}

/* Gradient text helper */
.gradient-text {
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Pulse animation for badges */
@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
.pulse-badge { animation: pulse-dot 2s ease-in-out infinite; }

/* Fade in animation */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fadeIn 0.4s ease-out; }

/* Button press effect */
.q-btn { transition: all 0.15s ease !important; }
.q-btn:active { transform: scale(0.97) !important; }

/* Better scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }
"""


def _get_nav_items() -> list[dict]:
    """Return nav items filtered by the current user's role."""
    role = app.storage.user.get("role", "viewer")
    items = [
        {"label": "Dashboard",  "icon": "dashboard",            "path": "/",          "roles": ["admin", "manager", "viewer"]},
        {"label": "Intake",     "icon": "person_add",           "path": "/intake",    "roles": ["admin", "manager"]},
        {"label": "Leases",     "icon": "description",          "path": "/lease",     "roles": ["admin", "manager"]},
        {"label": "Finance",    "icon": "account_balance",      "path": "/finance",   "roles": ["admin"]},
        {"label": "Actions",    "icon": "notifications_active", "path": "/actions",   "roles": ["admin", "manager", "viewer"]},
        {"label": "Marketing",  "icon": "campaign",             "path": "/marketing", "roles": ["admin", "manager", "viewer"]},
        {"label": "Admin",      "icon": "admin_panel_settings",  "path": "/admin",     "roles": ["admin"]},
    ]
    return [item for item in items if role in item["roles"]]


@contextmanager
def page_layout(title: str = ""):
    """Context manager that wraps page content with header + sidebar navigation."""
    # Inject global styles
    ui.add_head_html(f"<style>{GLOBAL_CSS}</style>")

    ui.colors(primary=PRIMARY, secondary=ACCENT, accent=ACCENT, positive=SUCCESS,
              negative=DANGER, warning=WARNING)

    username = app.storage.user.get("username", "User")
    role = app.storage.user.get("role", "viewer")

    # ── Header ─────────────────────────────────────────────────────────────
    with ui.header().classes("items-center justify-between px-6 shadow-lg").style(
        f"background: linear-gradient(135deg, {PRIMARY} 0%, #1E293B 50%, #334155 100%);"
        "border-bottom: 1px solid rgba(255,255,255,0.08);"
    ):
        with ui.row().classes("items-center gap-3"):
            with ui.element("div").classes("rounded-xl p-2").style(
                f"background: linear-gradient(135deg, {ACCENT}, #8B5CF6);"
            ):
                ui.icon("apartment", size="22px").classes("text-white")
            with ui.column().classes("gap-0"):
                ui.label("Tenant Flow").classes(
                    "text-white text-lg font-bold tracking-wide leading-tight"
                )
                ui.label("Manager").classes(
                    "text-slate-400 text-xs font-medium tracking-widest uppercase leading-tight"
                )

        with ui.row().classes("items-center gap-3"):
            if title and title.strip():
                ui.badge(title).props("outline color=white").classes("text-[10px] px-2 opacity-70 border-white/30")
            # User pill
            with ui.row().classes("items-center gap-2 rounded-full px-3 py-1").style(
                "background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12);"
            ):
                ui.icon("person", size="16px").classes("text-slate-300")
                ui.label(username).classes("text-slate-200 text-xs font-medium")
                ui.badge(role.capitalize(), color="#6366F1").classes("text-xs")
            ui.button(icon="logout", on_click=_logout).props(
                "flat round color=white size=sm"
            ).tooltip("Sign Out")

    # ── Sidebar ────────────────────────────────────────────────────────────
    with ui.left_drawer(value=True, bordered=True).classes("p-4").style(
        f"background: {CARD_BG}; border-right: 1px solid {BORDER};"
    ):
        ui.label("NAVIGATION").classes(
            "text-xs font-bold tracking-widest mb-4 px-3"
        ).style(f"color: {TEXT_SECONDARY}")

        for item in _get_nav_items():
            with ui.row().classes(
                "items-center gap-3 px-3 py-2.5 cursor-pointer nav-item w-full"
            ).on("click", lambda _, p=item["path"]: ui.navigate.to(p)):
                with ui.element("div").classes("rounded-lg p-1.5").style(
                    f"background: {ACCENT}12;"
                ):
                    ui.icon(item["icon"], size="18px").style(f"color: {ACCENT}")
                ui.label(item["label"]).classes("text-sm font-medium").style(
                    f"color: {TEXT_PRIMARY}"
                )

        # Footer
        ui.space()
        ui.separator().classes("my-3")
        with ui.row().classes("items-center gap-2 px-3"):
            ui.icon("cloud_done", size="14px").style(f"color: {SUCCESS}")
            ui.label("Cloud Connected").classes("text-xs font-medium").style(
                f"color: {SUCCESS}"
            )

    # ── Main Content ───────────────────────────────────────────────────────
    with ui.column().classes("w-full p-8 gap-6 fade-in").style(
        f"background: {SURFACE}; min-height: 100vh"
    ):
        yield


def _logout():
    """Clear auth state and redirect to login."""
    from app.auth import logout
    logout()


# ── Reusable UI Components ─────────────────────────────────────────────────────

def metric_card(label: str, value, icon: str = "info", color: str = ACCENT):
    """A styled metric card for dashboards."""
    with ui.card().classes("p-5 rounded-2xl shadow-sm card-hover").style(
        f"background: {CARD_BG}; border: 1px solid {BORDER}; min-width: 200px"
    ):
        with ui.row().classes("items-center gap-3"):
            with ui.element("div").classes("rounded-xl p-2.5").style(
                f"background: linear-gradient(135deg, {color}18, {color}08);"
            ):
                ui.icon(icon, size="24px").style(f"color: {color}")
            with ui.column().classes("gap-0"):
                ui.label(str(value)).classes("text-2xl font-bold").style(
                    f"color: {TEXT_PRIMARY}"
                )
                ui.label(label).classes("text-xs font-medium").style(f"color: {TEXT_SECONDARY}")


def section_header(title: str, subtitle: str = ""):
    """A styled section header."""
    with ui.column().classes("gap-1 mb-2"):
        ui.label(title).classes("text-2xl font-bold").style(f"color: {TEXT_PRIMARY}")
        if subtitle:
            ui.label(subtitle).classes("text-sm").style(f"color: {TEXT_SECONDARY}")
