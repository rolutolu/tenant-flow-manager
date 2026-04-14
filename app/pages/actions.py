"""Action Center & Compliance page — lease expiration scanner and rent increase notices."""

from nicegui import ui
from app.auth import require_auth
from app.theme import (page_layout, section_header, metric_card,
                        ACCENT, SUCCESS, WARNING, DANGER, TEXT_SECONDARY)
from app.services.tenant_service import get_all_tenants, get_tenant_count, get_pending_signatures_count
from app.services.lease_service import get_expiring_leases, generate_rent_increase_notice


@ui.page("/actions")
@require_auth
def actions_page():
    with page_layout(title="Action Center"):
        section_header("Action Center & Compliance",
                       "Proactively manage lease expirations and rent increase notices")

        with ui.row().classes("w-full gap-6 flex-wrap items-start"):

            # ── Left: Lease Expiration Scanner ─────────────────────────────
            with ui.card().classes("p-6 rounded-xl shadow-sm flex-1 min-w-[400px]").style(
                "border: 1px solid #E2E8F0"
            ):
                with ui.row().classes("items-center gap-2 mb-4"):
                    ui.icon("schedule", size="24px").style(f"color: {WARNING}")
                    ui.label("Upcoming Lease Expirations").classes("text-lg font-semibold")
                ui.label(
                    "Scan for leases expiring within 90 days. Rent increase notices must be "
                    "sent 3 months prior to lease expiration."
                ).classes("text-sm mb-3").style(f"color: {TEXT_SECONDARY}")

                results_container = ui.column().classes("w-full gap-3")

                def scan_expirations():
                    results_container.clear()
                    expiring = get_expiring_leases(days=90)
                    with results_container:
                        if expiring:
                            ui.label(
                                f"Found {len(expiring)} lease(s) expiring within 90 days!"
                            ).classes("text-sm font-medium").style(f"color: {WARNING}")

                            for tenant in expiring:
                                with ui.expansion(
                                    f"{tenant['name']} (Unit {tenant['unit']}) — "
                                    f"{tenant['days_left']} days left",
                                    icon="warning",
                                ).classes("w-full").props("dense"):
                                    with ui.column().classes("gap-2 p-3"):
                                        ui.label(f"Lease End: {tenant['lease_end']}").classes("text-sm")
                                        ui.label(
                                            f"Current Rent: ${tenant['rent_amount']:,.2f}"
                                        ).classes("text-sm")

                                        with ui.row().classes("gap-2"):
                                            new_rent = ui.number(
                                                label="New Rent ($)",
                                                value=tenant["rent_amount"] * 1.03,
                                                min=0, step=25
                                            ).classes("w-40").props("outlined dense")

                                            def draft_notice(t=tenant, nr=new_rent):
                                                try:
                                                    path = generate_rent_increase_notice(
                                                        tenant_name=t["name"],
                                                        unit=t["unit"],
                                                        current_rent=t["rent_amount"],
                                                        new_rent=nr.value,
                                                        effective_date=t["lease_end"],
                                                    )
                                                    ui.notify(
                                                        f"Notice generated: {path}",
                                                        type="positive"
                                                    )
                                                except Exception as e:
                                                    ui.notify(f"Error: {str(e)}", type="negative")

                                            ui.button(
                                                "Draft Notice",
                                                on_click=draft_notice,
                                                icon="drafts",
                                            ).props("unelevated size=sm")
                        else:
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("check_circle", size="24px").style(f"color: {SUCCESS}")
                                ui.label("No leases expiring within the next 90 days.").classes(
                                    "font-medium"
                                ).style(f"color: {SUCCESS}")

                ui.button(
                    "Scan for Upcoming Expirations",
                    on_click=scan_expirations,
                    icon="radar",
                ).classes("w-full").props("unelevated")

            # ── Right: System Overview ─────────────────────────────────────
            with ui.column().classes("gap-4 flex-1 min-w-[300px]"):
                with ui.card().classes("p-6 rounded-xl shadow-sm w-full").style(
                    "border: 1px solid #E2E8F0"
                ):
                    with ui.row().classes("items-center gap-2 mb-4"):
                        ui.icon("analytics", size="24px").style(f"color: {ACCENT}")
                        ui.label("System Overview").classes("text-lg font-semibold")

                    with ui.column().classes("gap-3 w-full"):
                        metric_card("Total Active Tenants", get_tenant_count(), "people", ACCENT)
                        metric_card("Pending Signatures", get_pending_signatures_count(),
                                    "edit_note", WARNING)

                # ── Tenant Database ────────────────────────────────────────
                with ui.card().classes("p-6 rounded-xl shadow-sm w-full").style(
                    "border: 1px solid #E2E8F0"
                ):
                    with ui.row().classes("items-center gap-2 mb-4"):
                        ui.icon("table_chart", size="24px").style(f"color: {ACCENT}")
                        ui.label("Current Database").classes("text-lg font-semibold")

                    tenants = get_all_tenants()
                    if tenants:
                        # Hide sensitive bank_info from the display
                        display_tenants = []
                        for t in tenants:
                            dt = {k: v for k, v in t.items() if k != "bank_info"}
                            display_tenants.append(dt)

                        columns = [
                            {"name": "unit", "label": "Unit", "field": "unit", "align": "left"},
                            {"name": "name", "label": "Name", "field": "name", "align": "left"},
                            {"name": "rent_amount", "label": "Rent", "field": "rent_amount", "align": "right"},
                            {"name": "lease_signed", "label": "Signed", "field": "lease_signed", "align": "center"},
                            {"name": "banking_set_up", "label": "Banking", "field": "banking_set_up", "align": "center"},
                        ]
                        ui.table(
                            columns=columns,
                            rows=display_tenants,
                        ).classes("w-full").props("flat bordered dense")
                    else:
                        ui.label("No tenants yet.").classes("text-sm").style(
                            f"color: {TEXT_SECONDARY}"
                        )
