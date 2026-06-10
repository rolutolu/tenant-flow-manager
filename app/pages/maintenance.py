"""Maintenance operations dashboard for managing repair requests."""

from nicegui import ui
from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, CARD_BG, BORDER
from app.services.maintenance_service import (
    get_maintenance_requests, add_maintenance_request,
    update_maintenance_status, update_maintenance_request,
)
from app.services.tenant_service import get_all_tenants


@ui.page("/maintenance")
@require_role("admin", "manager")
def maintenance_page():
    user_id = get_user_id()
    tenants = get_all_tenants(user_id)
    tenant_options = {t["id"]: f"{t['name']} (Unit {t['unit']})" for t in tenants}

    with page_layout(title="Maintenance Hub"):
        section_header("Maintenance & Operations", "Track repair requests, assign contractors, and manage unit upkeep")

        with ui.row().classes("w-full justify-between items-center mb-6"):
            ui.button("New Ticket", icon="add", on_click=lambda: new_ticket_dialog.open()).props("unelevated rounded")
            ui.button(
                "Import from Email (Demo)",
                icon="mail",
                on_click=lambda: ui.notify(
                    "Demo only: configure email parsing to auto-create tickets.",
                    type="info",
                ),
            ).props("outline")

        with ui.dialog() as new_ticket_dialog, ui.card().classes("p-6 w-96"):
            ui.label("Create Ticket").classes("text-xl font-bold mb-4")
            t_tenant = ui.select(label="Tenant (optional)", options=tenant_options).classes("w-full mb-2").props(
                "outlined clearable"
            )
            t_issue = ui.textarea(label="Issue Description").classes("w-full mb-2").props("outlined")
            t_urgency = ui.select(
                label="Urgency", options=["Low", "Medium", "High", "Emergency"], value="Low"
            ).classes("w-full mb-4").props("outlined")

            def save_ticket():
                if not t_issue.value:
                    return ui.notify("Issue required", type="warning")
                tenant_id = t_tenant.value
                unit_id = None
                if tenant_id:
                    tenant = next((t for t in tenants if t["id"] == tenant_id), None)
                    if tenant:
                        unit_id = tenant.get("unit_id")
                if add_maintenance_request(user_id, t_issue.value, t_urgency.value, tenant_id, unit_id):
                    ui.notify("Ticket created", type="positive")
                    new_ticket_dialog.close()
                    ui.navigate.to("/maintenance")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=new_ticket_dialog.close).props("flat")
                ui.button("Save", on_click=save_ticket).props("unelevated color=primary")

        requests = get_maintenance_requests(user_id)
        open_reqs = [r for r in requests if r["status"] == "Open"]
        prog_reqs = [r for r in requests if r["status"] == "In Progress"]
        done_reqs = [r for r in requests if r["status"] == "Resolved"]
        total_resolved_cost = sum(r.get("cost") or 0 for r in done_reqs)

        with ui.row().classes("w-full gap-6 items-start flex-nowrap overflow-x-auto"):
            def kanban_col(title, tickets, bg_color):
                with ui.column().classes("flex-1 min-w-[300px] rounded-xl p-4").style(f"background: {bg_color};"):
                    header = f"{title} ({len(tickets)})"
                    if title == "Resolved":
                        header += f" — ${total_resolved_cost:,.2f} total"
                    ui.label(header).classes("text-lg font-bold text-slate-700 mb-2")
                    for t in tickets:
                        urgency_color = (
                            "red" if t["urgency"] == "Emergency"
                            else "orange" if t["urgency"] == "High"
                            else "slate"
                        )
                        with ui.expansion(t["issue"][:40], icon="build").classes(
                            "w-full mb-3 bg-white rounded-lg shadow-sm border border-slate-200"
                        ).props("dense"):
                            with ui.column().classes("p-3 gap-2 w-full"):
                                with ui.row().classes("w-full justify-between"):
                                    ui.badge(t["urgency"], color=urgency_color).classes("text-[10px]")
                                    ui.label(t["created_at"][:10]).classes("text-xs text-slate-400")
                                unit_label = (t.get("units") or {}).get("unit_number", "Unknown Unit")
                                ui.label(unit_label).classes("font-semibold")
                                ui.label(t["issue"]).classes("text-sm text-slate-600")

                                contractor_input = ui.input(
                                    label="Contractor", value=t.get("contractor") or ""
                                ).classes("w-full").props("outlined dense")
                                cost_input = ui.number(
                                    label="Cost ($)", value=t.get("cost") or 0, min=0
                                ).classes("w-full").props("outlined dense")

                                def save_details(tid=t["id"], c=contractor_input, cost=cost_input):
                                    if update_maintenance_request(tid, contractor=c.value, cost=cost.value or 0):
                                        ui.notify("Ticket updated", type="positive")

                                ui.button("Save Details", on_click=save_details, icon="save").props(
                                    "flat dense size=sm"
                                )

                                with ui.row().classes("w-full justify-end gap-1"):
                                    if t["status"] != "Resolved":
                                        def mark_done(tid=t["id"]):
                                            update_maintenance_status(tid, "Resolved")
                                            ui.navigate.to("/maintenance")

                                        ui.button(icon="check", on_click=mark_done).props(
                                            "flat dense color=positive size=sm"
                                        ).tooltip("Mark Resolved")
                                    if t["status"] == "Open":
                                        def mark_prog(tid=t["id"]):
                                            update_maintenance_status(tid, "In Progress")
                                            ui.navigate.to("/maintenance")

                                        ui.button(icon="play_arrow", on_click=mark_prog).props(
                                            "flat dense color=primary size=sm"
                                        ).tooltip("In Progress")

            kanban_col("Open", open_reqs, "#F8FAFC")
            kanban_col("In Progress", prog_reqs, "#F0F9FF")
            kanban_col("Resolved", done_reqs, "#F0FDF4")
