"""Shared UI theme — premium dark mode design with header, sidebar, and page wrapper."""

from contextlib import contextmanager
from nicegui import ui, app

# ── Brand Colors (Light Mode) ─────────────────────────────────────────────────
PRIMARY = "#120E0C"       # Rich warm charcoal/black
PRIMARY_LIGHT = "#1E1B18"
ACCENT = "#120E0C"        # Black
ACCENT_LIGHT = "#2A2A2A"
SURFACE = "#F6F5F3"       # Soft cream background
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#1C1915"
TEXT_SECONDARY = "#827B77"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
BORDER = "#E6E4DF"

# ── Dark Mode Colors ──────────────────────────────────────────────────────────
DARK_SURFACE = "#0F0D0C"
DARK_CARD = "#1A1714"
DARK_CARD_BORDER = "#2C2825"
DARK_TEXT_PRIMARY = "#F2EDE8"
DARK_TEXT_SECONDARY = "#8A8480"
DARK_HEADER = "#0A0908"
DARK_ACCENT = "#C9A96E"      # Warm gold accent for dark mode

# ── Global Styles ──────────────────────────────────────────────────────────────
GLOBAL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,400;1,500;1,600;1,700&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --surface: #F6F5F3;
    --card-bg: #FFFFFF;
    --text-primary: #1C1915;
    --text-secondary: #827B77;
    --border: #E6E4DF;
    --header-bg: #FFFFFF;
    --header-border: #E6E4DF;
    --header-text: #1C1915;
    --header-nav-text: #827B77;
    --header-nav-hover: #120E0C;
    --header-menu-btn-bg: #EAE8E3;
    --header-menu-btn-border: #E6E4DF;
    --header-menu-btn-icon: #1C1915;
    --metric-line: #E6E4DF;
    --scrollbar-thumb: #CBD5E1;
    --scrollbar-thumb-hover: #94A3B8;
    --action-bar-bg: #FFFFFF;
    --action-bar-border: #E6E4DF;
    --action-bar-btn-bg: rgba(18, 14, 12, 0.04);
    --action-bar-btn-border: rgba(18, 14, 12, 0.08);
    --action-bar-btn-color: #1C1915;
    --action-bar-btn-hover-bg: rgba(18, 14, 12, 0.08);
    --action-bar-btn-hover-border: rgba(18, 14, 12, 0.15);
    --action-bar-btn-hover-color: #120E0C;
    --action-bar-text-label: #827B77;
    --action-bar-separator: rgba(18, 14, 12, 0.08);
    --card-shadow: rgba(26,22,21,0.03);
    --card-shadow-hover: rgba(26,22,21,0.06);
    --icon-bg: linear-gradient(135deg, #120E0C18, #120E0C08);
    --icon-color: #120E0C;
    --label-color: #827B77;
}

.dark-mode {
    --surface: #0F0D0C;
    --card-bg: #1A1714;
    --text-primary: #F2EDE8;
    --text-secondary: #8A8480;
    --border: #2C2825;
    --header-bg: #0A0908;
    --header-border: rgba(255,255,255,0.06);
    --header-text: #FFFFFF;
    --header-nav-text: #D6D3D1;
    --header-nav-hover: #FFFFFF;
    --header-menu-btn-bg: #2A2A2A;
    --header-menu-btn-border: rgba(255,255,255,0.1);
    --header-menu-btn-icon: #FFFFFF;
    --metric-line: #2C2825;
    --scrollbar-thumb: #3A3633;
    --scrollbar-thumb-hover: #5A5450;
    --action-bar-bg: #131110;
    --action-bar-border: rgba(255,255,255,0.04);
    --action-bar-btn-bg: rgba(255, 255, 255, 0.04);
    --action-bar-btn-border: rgba(255, 255, 255, 0.08);
    --action-bar-btn-color: #D6D3D1;
    --action-bar-btn-hover-bg: rgba(255, 255, 255, 0.10);
    --action-bar-btn-hover-border: rgba(255, 255, 255, 0.18);
    --action-bar-btn-hover-color: #FFFFFF;
    --action-bar-text-label: #8A8480;
    --action-bar-separator: rgba(255, 255, 255, 0.08);
    --card-shadow: rgba(0,0,0,0.2);
    --card-shadow-hover: rgba(0,0,0,0.35);
    --icon-bg: linear-gradient(135deg, #C9A96E22, #C9A96E0A);
    --icon-color: #C9A96E;
    --label-color: #8A8480;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    cursor: default;
    background-color: var(--surface) !important;
    transition: background-color 0.3s ease;
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
    background-color: var(--header-bg) !important;
    box-shadow: none !important;
    border-bottom: 1px solid var(--header-border) !important;
}
.q-layout__section--marginal { background-color: transparent !important; }

.nav-link {
    color: var(--header-nav-text) !important;
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.12em;
    cursor: pointer;
    transition: color 0.18s ease;
    text-transform: uppercase;
    text-decoration: none;
}
.nav-link:hover {
    color: var(--header-nav-hover) !important;
}

/* Action bar (sub-header) */
.action-bar {
    background-color: var(--action-bar-bg);
    border-bottom: 1px solid var(--action-bar-border);
    padding: 0 2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    height: 48px;
    position: sticky;
    z-index: 10;
    overflow-x: auto;
    transition: background-color 0.3s ease;
}

.action-bar-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0 0.85rem;
    height: 32px;
    border-radius: 8px;
    border: 1px solid var(--action-bar-btn-border);
    background: var(--action-bar-btn-bg);
    color: var(--action-bar-btn-color);
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.18s ease;
    white-space: nowrap;
    text-decoration: none;
}
.action-bar-btn:hover {
    background: var(--action-bar-btn-hover-bg);
    border-color: var(--action-bar-btn-hover-border);
    color: var(--action-bar-btn-hover-color);
    transform: translateY(-1px);
}
.action-bar-btn .material-icons {
    font-size: 16px !important;
    opacity: 0.85;
}
.action-bar-btn.accent-btn {
    background: rgba(201, 169, 110, 0.12);
    border-color: rgba(201, 169, 110, 0.3);
    color: #C9A96E;
}
.action-bar-btn.accent-btn:hover {
    background: rgba(201, 169, 110, 0.22);
    border-color: rgba(201, 169, 110, 0.5);
    color: #E2C48A;
}

/* Dark mode toggle button */
.dark-toggle {
    margin-left: auto;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0 0.75rem;
    height: 30px;
    border-radius: 15px;
    border: 1px solid var(--action-bar-btn-border);
    background: var(--action-bar-btn-bg);
    color: var(--action-bar-btn-color);
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    cursor: pointer;
    transition: all 0.18s ease;
    text-transform: uppercase;
    white-space: nowrap;
}
.dark-toggle:hover {
    background: var(--action-bar-btn-hover-bg);
    color: var(--action-bar-btn-hover-color);
}
.dark-toggle .material-icons {
    font-size: 14px !important;
}

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
.card-hover:hover { transform: translateY(-2px); box-shadow: 0 10px 30px var(--card-shadow-hover) !important; }

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
::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--scrollbar-thumb-hover); }

/* Premium Editorial Styles */
.editorial-title {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-style: italic !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em;
    color: var(--text-primary) !important;
}

.editorial-metric {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-style: italic !important;
    font-weight: 400 !important;
    color: var(--text-primary) !important;
}

.metric-label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.65rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    font-weight: 600 !important;
    color: var(--label-color) !important;
}

.metric-card-line {
    height: 3px;
    width: 32px;
    background-color: var(--metric-line);
    border-radius: 1.5px;
    margin-top: 6px;
    transition: background-color 0.3s ease;
}

.q-menu {
    border: 1px solid var(--border) !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.15) !important;
    border-radius: 12px !important;
}

.q-item {
    font-family: 'Inter', sans-serif !important;
}

.q-card {
    border-radius: 16px !important;
    box-shadow: 0 4px 20px var(--card-shadow) !important;
    border: 1px solid var(--border) !important;
    background-color: var(--card-bg) !important;
    transition: background-color 0.3s ease, border-color 0.3s ease;
}

.q-table__container {
    border-radius: 16px !important;
    box-shadow: 0 4px 20px var(--card-shadow) !important;
    border: 1px solid var(--border) !important;
    background-color: var(--card-bg) !important;
}
.q-table th {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-size: 0.7rem !important;
}
.q-table td {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
}

.title-separator {
    height: 1px;
    background-color: var(--border);
    width: 100%;
    margin-top: 4px;
    margin-bottom: 16px;
    transition: background-color 0.3s ease;
}

/* Dark mode overrides for Quasar components */
.dark-mode .q-page {
    background-color: var(--surface) !important;
}
.dark-mode .q-header {
    background-color: var(--header-bg) !important;
}

/* Page background transitions */
.page-content {
    background-color: var(--surface);
    min-height: 100vh;
    transition: background-color 0.3s ease;
}
"""


def _get_dark_mode() -> bool:
    """Get current dark mode preference from user storage."""
    return app.storage.user.get("dark_mode", True)  # default = True


def _set_dark_mode(enabled: bool):
    """Persist dark mode preference."""
    app.storage.user["dark_mode"] = enabled


@contextmanager
def page_layout(title: str = ""):
    """Context manager that wraps page content with a premium top-nav layout."""
    # Inject global styles
    ui.add_head_html(f"<style>{GLOBAL_CSS}</style>")

    # Inject dark mode class toggler script
    ui.add_head_html("""
    <script>
    function applyDarkMode(enabled) {
        if (enabled) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
    }
    // Immediately apply based on storage (prevents flash)
    (function() {
        try {
            var stored = localStorage.getItem('nicegui:user');
            if (stored) {
                var data = JSON.parse(stored);
                var dm = data.dark_mode !== undefined ? data.dark_mode : true;
                if (dm) document.body.classList.add('dark-mode');
            } else {
                document.body.classList.add('dark-mode');
            }
        } catch(e) {
            document.body.classList.add('dark-mode');
        }
    })();
    </script>
    """)

    ui.colors(primary=PRIMARY, secondary=ACCENT, accent=ACCENT, positive=SUCCESS,
              negative=DANGER, warning=WARNING)

    role = app.storage.user.get("role", "viewer")
    dark_mode = _get_dark_mode()

    # Apply dark mode class on body via JS on each page load
    ui.run_javascript(f"applyDarkMode({str(dark_mode).lower()})")

    # ── Top Header ─────────────────────────────────────────────────────────
    with ui.header().classes("items-center justify-between px-8 py-4 shadow-sm"):
        # Logo block
        with ui.row().classes("items-center gap-3 cursor-pointer").on("click", lambda: ui.navigate.to("/")):
            ui.image("/static/virix_logo.png").style(
                "width: 36px; height: 36px; border-radius: 8px; object-fit: cover;"
            )
            # Text block
            with ui.column().classes("gap-0"):
                ui.html('<div style="font-family: \'Playfair Display\', serif; font-style: italic; font-weight: 600; font-size: 1.4rem; color: var(--header-text); line-height: 1; margin-top: -2px;">Virix.</div>')
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
                    ui.label(item["label"].upper()).classes("nav-link").on("click", lambda _, p=item["path"]: ui.navigate.to(p))

        # Hamburger menu button on the right
        with ui.element("div").style(
            "background-color: var(--header-menu-btn-bg); border: 1px solid var(--header-menu-btn-border); "
            "width: 34px; height: 34px; border-radius: 50%; cursor: pointer; "
            "display: flex; align-items: center; justify-content: center; "
            "flex-shrink: 0;"
        ):
            ui.icon("menu", size="20px").style("color: var(--header-menu-btn-icon); display: block;")
            with ui.menu().classes("w-48"):
                ui.menu_item("Dashboard", on_click=lambda: ui.navigate.to("/")).classes("text-sm")
                if role in ("superadmin", "admin"):
                    ui.menu_item("Admin Panel", on_click=lambda: ui.navigate.to("/admin")).classes("text-sm")
                    ui.menu_item("Audit Logs", on_click=lambda: ui.navigate.to("/audit")).classes("text-sm")
                if role in ("superadmin", "admin", "manager"):
                    ui.menu_item("Maintenance Hub", on_click=lambda: ui.navigate.to("/maintenance")).classes("text-sm")
                    ui.menu_item("Marketing", on_click=lambda: ui.navigate.to("/marketing")).classes("text-sm")
                    ui.menu_item("Import Data", on_click=lambda: ui.navigate.to("/import")).classes("text-sm")
                    ui.menu_item("Settings", on_click=lambda: ui.navigate.to("/settings")).classes("text-sm")
                ui.separator()
                ui.menu_item("Sign Out", on_click=_logout).classes("text-sm text-red-600")

    # ── Action Bar (Quick Access Toolbar) ──────────────────────────────────
    _render_action_bar(role)

    # ── Main Content Container ─────────────────────────────────────────────
    with ui.column().classes("w-full px-12 py-10 gap-6 fade-in page-content"):
        yield


def _render_action_bar(role: str):
    """Render the quick-action toolbar below the header."""
    action_buttons = []

    if role in ("admin", "manager"):
        action_buttons.append({
            "label": "New Tenant Intake",
            "icon": "person_add",
            "path": "/intake",
            "accent": True,
        })
        action_buttons.append({
            "label": "Generate Lease",
            "icon": "description",
            "path": "/lease",
            "accent": False,
        })
    if role == "admin":
        action_buttons.append({
            "label": "Financial Sync",
            "icon": "account_balance",
            "path": "/finance",
            "accent": False,
        })
    action_buttons.append({
        "label": "Scan Expirations",
        "icon": "notifications_active",
        "path": "/actions",
        "accent": False,
    })

    dark_mode = _get_dark_mode()

    with ui.element("div").classes("action-bar"):
        # Separator label
        ui.html('<span style="font-size:0.62rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:var(--action-bar-text-label);margin-right:0.5rem;white-space:nowrap;">Quick&nbsp;Access</span>')

        ui.html('<div style="width:1px;height:20px;background:var(--action-bar-separator);margin-right:0.5rem;"></div>')

        for btn in action_buttons:
            accent_class = "action-bar-btn accent-btn" if btn["accent"] else "action-bar-btn"
            ui.html(
                f'<a class="{accent_class}" href="{btn["path"]}">'
                f'<span class="material-icons">{btn["icon"]}</span>'
                f'{btn["label"]}'
                f'</a>'
            )

        # Spacer + dark mode toggle (right-aligned)
        is_dark = _get_dark_mode()
        toggle_icon = "light_mode" if is_dark else "dark_mode"
        toggle_label = "Light Mode" if is_dark else "Dark Mode"

        def toggle_dark_mode():
            current = _get_dark_mode()
            new_val = not current
            _set_dark_mode(new_val)
            ui.run_javascript(f"applyDarkMode({str(new_val).lower()})")
            # Reload so server re-renders with correct mode
            ui.navigate.to(ui.context.client.page.path)

        ui.button(toggle_label, icon=toggle_icon, on_click=toggle_dark_mode).classes(
            "dark-toggle"
        ).props("flat dense no-caps")

    # Register applyDarkMode as a global (needed on first load)
    ui.run_javascript(f"window.__darkMode = {str(dark_mode).lower()};")


def _logout():
    """Clear auth state and redirect to login."""
    from app.auth import logout
    logout()


def metric_card(label: str, value, icon: str = "info", color: str = ACCENT):
    """A styled metric card matching the premium editorial mockup design."""
    with ui.card().classes("p-6 flex-1 min-w-[220px]").style(
        "box-shadow: 0 4px 20px var(--card-shadow); border: 1px solid var(--border); border-radius: 16px;"
    ):
        with ui.column().classes("gap-1 w-full"):
            ui.label(label).classes("metric-label")
            ui.label(str(value)).classes("editorial-metric text-4xl mt-1").style("line-height: 1;")
            ui.element("div").classes("metric-card-line")


def section_header(title: str, subtitle: str = ""):
    """A styled section header with serif styling and horizontal underline rule."""
    with ui.column().classes("gap-0 mb-4 w-full"):
        ui.label(title).classes("editorial-title text-4xl")
        if subtitle:
            ui.label(subtitle).classes("text-sm mt-1").style("color: var(--text-secondary); font-family: 'Inter', sans-serif;")
        ui.element("div").classes("title-separator")
