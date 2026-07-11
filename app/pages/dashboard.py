"""Dashboard page — overview metrics and quick-action cards."""

import os
from datetime import datetime
from nicegui import ui, app as nicegui_app
from app.auth import require_auth, get_user_id, get_user_role, get_current_user
from app.theme import (page_layout, metric_card, section_header,
                        ACCENT, SUCCESS, WARNING, DANGER, CARD_BG, BORDER, TEXT_PRIMARY, TEXT_SECONDARY)
from app.services.property_service import get_all_units
from app.services.tenant_service import get_all_tenants
from app.services.maintenance_service import get_maintenance_requests
from app.services.finance_service import get_revenue_summary


@ui.page("/")
@require_auth
def dashboard_page():
    user_id = get_user_id()
    role = get_user_role()

    # Determine time-of-day greeting
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # Get user name for greeting (use Jordan for admin default)
    user_data = get_current_user()
    username = user_data.get("username") or "User"
    display_name = username.capitalize()

    with page_layout(title="Dashboard"):
        # Section header renders the Playfair Display serif text and separator line globally
        section_header(f"{greeting}, {display_name}.")

        # ── Setup Banners ───────────────────────────────────────────────────
        _render_setup_banners(user_id, role)

        # ── Roadmap / Upcoming Features Notice ─────────────────────────────
        with ui.card().classes("w-full p-4 mb-4").style(
            "background: rgba(18, 14, 12, 0.03); border: 1px dashed var(--border); border-radius: 12px; box-shadow: none;"
        ):
            with ui.row().classes("items-center gap-3"):
                ui.icon("info", size="20px").style("color: var(--text-secondary);")
                with ui.column().classes("gap-0"):
                    ui.label("Coming Soon: Automated Email Sending & Bank Email Scanning").classes("font-semibold text-xs").style(
                        "color: var(--text-primary);"
                    )
                    ui.label(
                        "Full automated email broadcasting and direct integration to scan incoming bank deposit alert emails "
                        "are soon-to-be-implemented features currently in active development."
                    ).classes("text-[11px]").style("color: var(--text-secondary);")

        # ── Metrics Row (Mockup Style: Units, Occupancy, MRR, Tickets) ──
        all_units = get_all_units(user_id)
        total_units = len(all_units)
        
        occupied_units = sum(1 for u in all_units if u["status"] == "Occupied")
        occupancy_pct = int((occupied_units / total_units) * 100) if total_units > 0 else 0
        
        tenants = get_all_tenants(user_id)
        mrr_val = sum(t.get("rent_amount") or 0 for t in tenants)
        
        # Format MRR nicely (e.g. $2.1M or $15.2k or $15,200)
        if mrr_val >= 1000000:
            mrr_str = f"${mrr_val/1000000:.1f}M"
        elif mrr_val >= 1000:
            mrr_str = f"${mrr_val/1000:.1f}k"
        else:
            mrr_str = f"${mrr_val:,.0f}"

        tickets = get_maintenance_requests(user_id)
        open_tickets = sum(1 for t in tickets if t["status"] != "Resolved")

        with ui.row().classes("w-full flex-wrap gap-6 mb-6"):
            metric_card("Units", f"{total_units:,}")
            metric_card("Occupancy", f"{occupancy_pct}%")
            metric_card("MRR", mrr_str)
            metric_card("Tickets", f"{open_tickets}")

        # ── Quick Actions ──────────────────────────────────────────────────
        section_header("Quick Actions", "Jump to common tasks")

        with ui.row().classes("w-full flex-wrap gap-4"):
            if role in ("admin", "manager"):
                _action_card("New Tenant Intake", "Start the onboarding process for a new tenant",
                             "person_add", "/intake")
                _action_card("Generate Lease", "Create a new lease agreement PDF",
                             "description", "/lease")
            if role == "admin":
                _action_card("Financial Sync", "Manage PADs and banking information",
                             "account_balance", "/finance")
            _action_card("Scan Expirations", "Check for upcoming lease renewals",
                         "notifications_active", "/actions")

        # ── Revenue Breakdown (admin only) ─────────────────────────────────
        if role == "admin":
            revenue = get_revenue_summary(user_id)
            if revenue["total"] > 0:
                section_header("Revenue Breakdown", "PADs vs E-Transfers")
                with ui.card().classes("w-full p-5 rounded-2xl shadow-sm").style(
                    f"border: 1px solid {BORDER}"
                ):
                    ui.echart({
                        "tooltip": {"trigger": "item"},
                        "legend": {"bottom": "0%"},
                        "series": [{
                            "type": "pie",
                            "radius": ["40%", "70%"],
                            "avoidLabelOverlap": True,
                            "itemStyle": {"borderRadius": 10, "borderColor": "#fff", "borderWidth": 2},
                            "label": {"show": True, "formatter": "{b}: ${c}"},
                            "data": [
                                {"value": revenue["PAD"], "name": f"PAD ({revenue['pad_count']})",
                                 "itemStyle": {"color": ACCENT}},
                                {"value": revenue["E-Transfer"], "name": f"E-Transfer ({revenue['etransfer_count']})",
                                 "itemStyle": {"color": SUCCESS}},
                            ]
                        }]
                    }).classes("w-full h-64")


def _action_card(title: str, description: str, icon: str, path: str):
    """A clickable quick-action card matching the editorial palette."""
    with ui.card().classes(
        "p-5 rounded-2xl shadow-sm card-hover cursor-pointer"
    ).style(
        "border: 1px solid var(--border); min-width: 220px; flex: 1"
    ).on("click", lambda: ui.navigate.to(path)):
        with ui.row().classes("items-center gap-3 mb-2"):
            with ui.element("div").classes("rounded-xl p-2.5").style(
                "background: var(--icon-bg);"
            ):
                ui.icon(icon, size="24px").style("color: var(--icon-color)")
            ui.label(title).classes("font-semibold").style("color: var(--text-primary)")
        ui.label(description).classes("text-sm").style("color: var(--text-secondary)")


# ── Setup Banners ──────────────────────────────────────────────────────────────

_BANNER_MUTE_KEY = "dashboard_banners_muted"
_IMPORT_DISMISSED_KEY = "banner_import_dismissed"
_META_DISMISSED_KEY = "banner_meta_dismissed"


def _render_setup_banners(user_id: str, role: str):
    """Show dismissible setup nudge banners when data or integrations are missing.

    Banners are hidden if:
      - The user has permanently muted all setup banners (via Settings), OR
      - The banner was individually dismissed this session.
    Only shown to admin/manager/superadmin roles.
    """
    if role not in ("superadmin", "admin", "manager"):
        return

    # Respect permanent mute
    if nicegui_app.storage.user.get(_BANNER_MUTE_KEY, False):
        return

    tenants = get_all_tenants(user_id)
    has_tenants = len(tenants) > 0
    has_meta = bool(os.environ.get("META_ACCESS_TOKEN", "").strip())

    # Nothing to show
    if has_tenants and has_meta:
        return

    banners_container = ui.column().classes("w-full gap-3 mb-2")

    with banners_container:
        # ── No-data banner ──────────────────────────────────────────────────
        if not has_tenants and not nicegui_app.storage.user.get(_IMPORT_DISMISSED_KEY, False):
            import_banner = ui.card().classes("w-full").style(
                "background: linear-gradient(135deg, #EEF2FF, #E0E7FF); "
                "border: 1px solid #C7D2FE; border-radius: 14px; padding: 0;"
            )
            with import_banner:
                with ui.row().classes("items-center justify-between w-full p-4 gap-4"):
                    with ui.row().classes("items-center gap-3 flex-1"):
                        with ui.element("div").style(
                            "background: #4F46E5; border-radius: 10px; padding: 8px; "
                            "display: flex; align-items: center; justify-content: center;"
                        ):
                            ui.icon("cloud_upload", size="20px").style("color: white;")
                        with ui.column().classes("gap-0"):
                            ui.label("No tenant data yet").classes("font-semibold text-sm").style(
                                "color: #3730A3;"
                            )
                            ui.label(
                                "Import your existing spreadsheets or files to get started. "
                                "Your data will be reviewed before going live."
                            ).classes("text-xs").style("color: #4338CA;")
                    with ui.row().classes("gap-2 items-center"):
                        ui.button(
                            "Import Data", icon="arrow_forward",
                            on_click=lambda: ui.navigate.to("/import"),
                        ).props("unelevated rounded no-caps size=sm").style(
                            "background: #4F46E5 !important; color: white !important;"
                        )
                        def dismiss_import(b=import_banner):
                            nicegui_app.storage.user[_IMPORT_DISMISSED_KEY] = True
                            b.set_visibility(False)
                        ui.button(icon="close", on_click=dismiss_import).props(
                            "flat round dense size=sm"
                        ).style("color: #6366F1;")

        # ── No-Meta banner ───────────────────────────────────────────────────
        if not has_meta and not nicegui_app.storage.user.get(_META_DISMISSED_KEY, False):
            meta_banner = ui.card().classes("w-full").style(
                "background: linear-gradient(135deg, #FFF7ED, #FFEDD5); "
                "border: 1px solid #FED7AA; border-radius: 14px; padding: 0;"
            )
            with meta_banner:
                with ui.row().classes("items-center justify-between w-full p-4 gap-4"):
                    with ui.row().classes("items-center gap-3 flex-1"):
                        with ui.element("div").style(
                            "background: #EA580C; border-radius: 10px; padding: 8px; "
                            "display: flex; align-items: center; justify-content: center;"
                        ):
                            ui.icon("campaign", size="20px").style("color: white;")
                        with ui.column().classes("gap-0"):
                            ui.label("Meta marketing not connected").classes(
                                "font-semibold text-sm"
                            ).style("color: #9A3412;")
                            ui.label(
                                "Add your META_ACCESS_TOKEN and META_AD_ACCOUNT_ID to your .env "
                                "to enable ad campaign management."
                            ).classes("text-xs").style("color: #C2410C;")
                    with ui.row().classes("gap-2 items-center"):
                        ui.button(
                            "Marketing", icon="arrow_forward",
                            on_click=lambda: ui.navigate.to("/marketing"),
                        ).props("unelevated rounded no-caps size=sm").style(
                            "background: #EA580C !important; color: white !important;"
                        )
                        def dismiss_meta(b=meta_banner):
                            nicegui_app.storage.user[_META_DISMISSED_KEY] = True
                            b.set_visibility(False)
                        ui.button(icon="close", on_click=dismiss_meta).props(
                            "flat round dense size=sm"
                        ).style("color: #F97316;")
