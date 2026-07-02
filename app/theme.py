"""Shared UI theme — premium design with header, sidebar, and page wrapper."""

from contextlib import contextmanager
from nicegui import ui, app

# ── Brand Colors (refined palette matching the mockup) ───────────────────────
PRIMARY = "#120E0C"       # Rich warm charcoal/black
PRIMARY_LIGHT = "#1E1B18"
ACCENT = "#120E0C"        # Black (was burgundy)
ACCENT_LIGHT = "#2A2A2A"
SURFACE = "#F6F5F3"       # Soft cream background
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#1C1915"
TEXT_SECONDARY = "#827B77"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
BORDER = "#E6E4DF"

# ── Global Styles ──────────────────────────────────────────────────────────────
GLOBAL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,400;1,500;1,600;1,700&family=Inter:wght@400;500;600;700&display=swap');

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    cursor: default;
    background-color: #F6F5F3 !important;
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

/* Fix header styling */
.q-header {
    background-color: #120E0C !important;
    box-shadow: none !important;
    border-bottom: 1px solid rgba(255,255,255,0.06) !important;
}
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
.card-hover:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(26,22,21,0.06) !important; }

/* Glass effect */
.glass {
    background: rgba(255, 255, 255, 0.7) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
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

/* Premium Editorial Styles */
.editorial-title {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-style: italic !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em;
}

.editorial-metric {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-style: italic !important;
    font-weight: 400 !important;
}

.metric-label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.65rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    font-weight: 600 !important;
    color: #827B77 !important;
}

.metric-card-line {
    height: 3px;
    width: 32px;
    background-color: #E6E4DF;
    border-radius: 1.5px;
    margin-top: 6px;
}

.q-menu {
    border: 1px solid #E6E4DF !important;
    box-shadow: 0 10px 30px rgba(26,22,21,0.08) !important;
    border-radius: 12px !important;
}

.q-item {
    font-family: 'Inter', sans-serif !important;
}

.q-card {
    border-radius: 16px !important;
    box-shadow: 0 4px 20px rgba(26,22,21,0.03) !important;
    border: 1px solid #E6E4DF !important;
    background-color: #FFFFFF !important;
}

.q-table__container {
    border-radius: 16px !important;
    box-shadow: 0 4px 20px rgba(26,22,21,0.03) !important;
    border: 1px solid #E6E4DF !important;
    background-color: #FFFFFF !important;
}
.q-table th {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    color: #827B77 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-size: 0.7rem !important;
}
.q-table td {
    font-family: 'Inter', sans-serif !important;
    color: #1A1615 !important;
}

.title-separator {
    height: 1px;
    background-color: #E6E4DF;
    width: 100%;
    margin-top: 4px;
    margin-bottom: 16px;
}
"""

@contextmanager
def page_layout(title: str = ""):
    """Context manager that wraps page content with a premium top-nav layout matching the mockup."""
    # Inject global styles
    ui.add_head_html(f"<style>{GLOBAL_CSS}</style>")

    ui.colors(primary=PRIMARY, secondary=ACCENT, accent=ACCENT, positive=SUCCESS,
              negative=DANGER, warning=WARNING)

    role = app.storage.user.get("role", "viewer")

    # ── Top Header ─────────────────────────────────────────────────────────
    with ui.header().classes("items-center justify-between px-8 py-4 shadow-sm"):
        # Logo block
        with ui.row().classes("items-center gap-3 cursor-pointer").on("click", lambda: ui.navigate.to("/")):
            ui.image("/static/virix_logo.png").style(
                "width: 36px; height: 36px; border-radius: 8px; object-fit: cover;"
            )
            # Text block
            with ui.column().classes("gap-0"):
                ui.html('<div style="font-family: \'Playfair Display\', serif; font-style: italic; font-weight: 600; font-size: 1.4rem; color: #FFFFFF; line-height: 1; margin-top: -2px;">Virix.</div>')
                ui.label("PROPERTY SUITE").classes("text-[9px] font-bold tracking-widest uppercase").style("color: #827B77; line-height: 1; margin-top: 1px;")

        # Navigation menu centered/right
        allowed_paths = []
        if role in ("superadmin", "admin", "manager"):
            allowed_paths.append("/properties")
            allowed_paths.append("/lease")
            allowed_paths.append("/finance")
        allowed_paths.append("/actions")

        nav_items = [
            {"label": "Portfolio", "path": "/properties"},
            {"label": "Leases", "path": "/lease"},
            {"label": "Tenants", "path": "/actions"},
            {"label": "Accounting", "path": "/finance"},
        ]

        with ui.row().classes("items-center gap-8 hidden md:flex").style("margin-left: auto; margin-right: 2.5rem;"):
            for item in nav_items:
                if item["path"] in allowed_paths:
                    ui.label(item["label"].upper()).classes("text-[11px] font-semibold tracking-widest cursor-pointer hover:text-white transition-colors").style(
                        "color: #D6D3D1; font-family: 'Inter', sans-serif;"
                    ).on("click", lambda _, p=item["path"]: ui.navigate.to(p))

        # Hamburger menu button on the right
        with ui.element("div").style(
            "background-color: #2A2A2A; border: 1px solid rgba(255,255,255,0.1); "
            "width: 34px; height: 34px; border-radius: 50%; cursor: pointer; "
            "display: flex; align-items: center; justify-content: center; "
            "flex-shrink: 0;"
        ):
            ui.icon("menu", size="20px").style("color: white; display: block;")
            with ui.menu().classes("w-48"):
                ui.menu_item("Dashboard", on_click=lambda: ui.navigate.to("/")).classes("text-sm")
                if role in ("superadmin", "admin"):
                    ui.menu_item("Admin Panel", on_click=lambda: ui.navigate.to("/admin")).classes("text-sm")
                if role in ("superadmin", "admin", "manager"):
                    ui.menu_item("Maintenance Hub", on_click=lambda: ui.navigate.to("/maintenance")).classes("text-sm")
                    ui.menu_item("Marketing", on_click=lambda: ui.navigate.to("/marketing")).classes("text-sm")
                    ui.menu_item("Import Data", on_click=lambda: ui.navigate.to("/import")).classes("text-sm")
                    ui.menu_item("Settings", on_click=lambda: ui.navigate.to("/settings")).classes("text-sm")
                ui.separator()
                ui.menu_item("Sign Out", on_click=_logout).classes("text-sm text-red-600")

    # ── Main Content Container ─────────────────────────────────────────────
    with ui.column().classes("w-full px-12 py-10 gap-6 fade-in").style(
        f"background-color: {SURFACE}; min-height: 100vh"
    ):
        yield

def _logout():
    """Clear auth state and redirect to login."""
    from app.auth import logout
    logout()

def metric_card(label: str, value, icon: str = "info", color: str = ACCENT):
    """A styled metric card matching the premium editorial mockup design."""
    with ui.card().classes("p-6 flex-1 min-w-[220px]").style(
        "box-shadow: 0 4px 20px rgba(26,22,21,0.03); border: 1px solid #E6E4DF; border-radius: 16px;"
    ):
        with ui.column().classes("gap-1 w-full"):
            ui.label(label).classes("metric-label")
            ui.label(str(value)).classes("editorial-metric text-4xl mt-1").style("color: #1C1915; line-height: 1;")
            ui.element("div").classes("metric-card-line")

def section_header(title: str, subtitle: str = ""):
    """A styled section header with serif styling and horizontal underline rule."""
    with ui.column().classes("gap-0 mb-4 w-full"):
        ui.label(title).classes("editorial-title text-4xl text-stone-900")
        if subtitle:
            ui.label(subtitle).classes("text-sm mt-1").style("color: #827B77; font-family: 'Inter', sans-serif;")
        ui.element("div").classes("title-separator")
