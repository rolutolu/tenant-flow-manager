"""Maintenance operations dashboard for managing repair requests."""

from nicegui import ui, run
from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, CARD_BG, BORDER
from app.services.maintenance_service import (
    get_maintenance_requests, add_maintenance_request,
    update_maintenance_status, update_maintenance_request,
)
from app.services.tenant_service import get_all_tenants


@ui.page("/maintenance")
@require_role("admin", "manager")
async def maintenance_page():
    user_id = get_user_id()
    tenants = await run.io_bound(get_all_tenants, user_id)
    tenant_options = {t["id"]: f"{t['name']} (Unit {t['unit']})" for t in tenants}

    with page_layout(title="Maintenance Hub"):
        section_header("Maintenance & Operations", "Track repair requests, assign contractors, and manage unit upkeep")

        # ── "Coming Soon" blur overlay (matches marketing page pattern) ──
        with ui.element("div").classes("w-full relative"):
            # Blur the content behind
            with ui.element("div").classes("blur-content"):
                with ui.row().classes("w-full justify-between items-center mb-6"):
                    ui.button("New Ticket", icon="add").props("unelevated rounded")
                    ui.button("Import from Email (Demo)", icon="mail").props("outline")

                requests = await run.io_bound(get_maintenance_requests, user_id)
                open_reqs = [r for r in requests if r["status"] == "Open"]
                prog_reqs = [r for r in requests if r["status"] == "In Progress"]
                done_reqs = [r for r in requests if r["status"] == "Resolved"]

                with ui.row().classes("w-full gap-6 items-start flex-nowrap overflow-x-auto"):
                    def kanban_col(title, tickets, bg_color):
                        with ui.column().classes("flex-1 min-w-[300px] rounded-xl p-4").style(f"background: {bg_color};"):
                            header = f"{title} ({len(tickets)})"
                            ui.label(header).classes("text-lg font-bold text-slate-700 mb-2")
                            if not tickets:
                                ui.label("No tickets").classes("text-sm text-slate-400 italic")

                    kanban_col("Open", open_reqs, "#F8FAFC")
                    kanban_col("In Progress", prog_reqs, "#F0F9FF")
                    kanban_col("Resolved", done_reqs, "#F0FDF4")

            # Lock overlay on top
            with ui.element("div").classes("lock-overlay"):
                with ui.card().classes("p-8 items-center gap-4 text-center shadow-2xl"):
                    ui.icon("construction", size="64px", color="grey-4")
                    ui.label("Maintenance Hub — Coming Soon").classes("text-xl font-bold")
                    ui.label(
                        "This feature is currently under development. "
                        "Ticket management and contractor tracking will be available in a future update."
                    ).classes("text-slate-500 max-w-xs")

