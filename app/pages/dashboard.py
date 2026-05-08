"""Dashboard page — overview metrics and quick-action cards."""

from nicegui import ui
from app.auth import require_auth, get_user_id, get_user_role
from app.theme import (page_layout, metric_card, section_header,
                        ACCENT, SUCCESS, WARNING, DANGER, CARD_BG, BORDER, TEXT_PRIMARY)
from app.services.tenant_service import get_tenant_count, get_pending_signatures_count
from app.services.lease_service import get_expiring_leases
from app.services.finance_service import get_revenue_summary


@ui.page("/")
@require_auth
def dashboard_page():
    user_id = get_user_id()
    role = get_user_role()

    with page_layout(title="Dashboard"):
        section_header("Dashboard", "Overview of your property management operations")

        # ── Metrics Row ────────────────────────────────────────────────────
        with ui.row().classes("w-full flex-wrap gap-4"):
            tenant_count = get_tenant_count(user_id)
            pending = get_pending_signatures_count(user_id)
            expiring = len(get_expiring_leases(user_id))

            metric_card("Total Tenants", tenant_count, "people", ACCENT)
            metric_card("Pending Signatures", pending, "edit_note", WARNING)
            metric_card("Expiring Leases (90d)", expiring, "schedule", DANGER)

            # Only show revenue for admins
            if role == "admin":
                revenue = get_revenue_summary(user_id)
                metric_card("Total Revenue", f"${revenue['total']:,.0f}", "payments", SUCCESS)

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
    """A clickable quick-action card."""
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
        ui.label(description).classes("text-sm text-gray-500")
