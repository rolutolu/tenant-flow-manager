"""Dashboard page — overview metrics and quick-action cards."""

from datetime import datetime
from nicegui import ui
from app.auth import require_auth, get_user_id, get_user_role, get_current_user
from app.theme import (page_layout, metric_card, section_header,
                        ACCENT, SUCCESS, WARNING, DANGER, CARD_BG, BORDER, TEXT_PRIMARY)
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
    if username == "admin":
        display_name = "Jordan"
    else:
        display_name = username.capitalize()

    with page_layout(title="Dashboard"):
        # Section header renders the Playfair Display serif text and separator line globally
        section_header(f"{greeting}, {display_name}.")

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
        f"border: 1px solid {BORDER}; min-width: 220px; flex: 1"
    ).on("click", lambda: ui.navigate.to(path)):
        with ui.row().classes("items-center gap-3 mb-2"):
            with ui.element("div").classes("rounded-xl p-2.5").style(
                f"background: linear-gradient(135deg, {ACCENT}18, {ACCENT}08);"
            ):
                ui.icon(icon, size="24px").style(f"color: {ACCENT}")
            ui.label(title).classes("font-semibold").style(f"color: {TEXT_PRIMARY}")
        ui.label(description).classes("text-sm text-stone-500")

