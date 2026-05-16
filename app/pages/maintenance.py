"""Maintenance operations dashboard for managing repair requests."""
from nicegui import ui
from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, ACCENT, SUCCESS, WARNING, CARD_BG, BORDER
from app.services.maintenance_service import get_maintenance_requests, add_maintenance_request, update_maintenance_status

@ui.page("/maintenance")
@require_role("admin", "manager")
def maintenance_page():
    user_id = get_user_id()
    
    with page_layout(title="Maintenance Hub"):
        section_header("Maintenance & Operations", "Track repair requests, assign contractors, and manage unit upkeep")
        
        with ui.row().classes("w-full justify-between items-center mb-6"):
            ui.button("New Ticket", icon="add", on_click=lambda: new_ticket_dialog.open()).props("unelevated rounded")
            ui.button("Check Service Inbox", icon="mail", on_click=lambda: ui.notify("Simulating incoming email parsing... Created 1 new ticket.", type="info")).props("outline")

        # ── Add Ticket Modal ────────────────────────────────────────────
        with ui.dialog() as new_ticket_dialog, ui.card().classes("p-6 w-96"):
            ui.label("Create Ticket").classes("text-xl font-bold mb-4")
            t_issue = ui.textarea(label="Issue Description").classes("w-full mb-2").props("outlined")
            t_urgency = ui.select(label="Urgency", options=["Low", "Medium", "High", "Emergency"], value="Low").classes("w-full mb-4").props("outlined")
            
            def save_ticket():
                if not t_issue.value: return ui.notify("Issue required", type="warning")
                if add_maintenance_request(user_id, t_issue.value, t_urgency.value):
                    ui.notify("Ticket created", type="positive")
                    new_ticket_dialog.close()
                    ui.navigate.to("/maintenance")
            
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=new_ticket_dialog.close).props("flat")
                ui.button("Save", on_click=save_ticket).props("unelevated color=primary")

        # ── Kanban Board ─────────────────────────────────────────────────────
        requests = get_maintenance_requests(user_id)
        
        open_reqs = [r for r in requests if r["status"] == "Open"]
        prog_reqs = [r for r in requests if r["status"] == "In Progress"]
        done_reqs = [r for r in requests if r["status"] == "Resolved"]

        with ui.row().classes("w-full gap-6 items-start flex-nowrap overflow-x-auto"):
            # Column function
            def kanban_col(title, tickets, bg_color):
                with ui.column().classes("flex-1 min-w-[300px] rounded-xl p-4").style(f"background: {bg_color};"):
                    ui.label(f"{title} ({len(tickets)})").classes("text-lg font-bold text-slate-700 mb-2")
                    for t in tickets:
                        urgency_color = "red" if t["urgency"] == "Emergency" else "orange" if t["urgency"] == "High" else "slate"
                        with ui.card().classes("w-full p-4 mb-3 shadow-sm border border-slate-200 cursor-pointer hover:shadow-md transition-all bg-white"):
                            with ui.row().classes("w-full justify-between items-start"):
                                ui.badge(t["urgency"], color=urgency_color).classes("text-[10px]")
                                ui.label(t["created_at"][:10]).classes("text-xs text-slate-400")
                            
                            unit_label = t["units"]["unit_number"] if t.get("units") else "Unknown Unit"
                            ui.label(unit_label).classes("font-semibold mt-2")
                            ui.label(t["issue"]).classes("text-sm text-slate-600 mt-1 line-clamp-2")
                            
                            # Actions
                            with ui.row().classes("w-full justify-end mt-2 gap-1"):
                                if t["status"] != "Resolved":
                                    def mark_done(tid=t["id"]):
                                        update_maintenance_status(tid, "Resolved")
                                        ui.navigate.to("/maintenance")
                                    ui.button(icon="check", on_click=mark_done).props("flat dense color=positive size=sm")
                                if t["status"] == "Open":
                                    def mark_prog(tid=t["id"]):
                                        update_maintenance_status(tid, "In Progress")
                                        ui.navigate.to("/maintenance")
                                    ui.button(icon="play_arrow", on_click=mark_prog).props("flat dense color=primary size=sm")

            kanban_col("Open", open_reqs, "#F8FAFC")
            kanban_col("In Progress", prog_reqs, "#F0F9FF")
            kanban_col("Resolved", done_reqs, "#F0FDF4")
