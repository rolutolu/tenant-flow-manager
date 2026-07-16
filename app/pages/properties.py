"""Properties page for managing buildings and units."""
from nicegui import ui, run
from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, ACCENT, TEXT_SECONDARY, CARD_BG, BORDER, DANGER
from app.services.property_service import (
    get_properties, add_property, get_units_by_property, add_unit,
    update_unit_status, update_unit, delete_unit, delete_property,
)
from app.services.tenant_service import get_all_tenants

@ui.page("/properties")
@require_role("admin", "manager")
async def properties_page():
    user_id = get_user_id()

    with page_layout(title="Properties & Units"):
        section_header("Property Management", "Manage your buildings, complexes, and individual units")

        properties = await run.io_bound(get_properties, user_id)
        tenants = await run.io_bound(get_all_tenants, user_id)
        # Create lookup map: {unit_id: tenant_name}
        tenant_lookup = {t["unit_id"]: t["name"] for t in tenants if t.get("unit_id")}

        # ── Add Property Modal ──────────────────────────────────────────────
        with ui.dialog() as add_prop_dialog, ui.card().classes("w-96 p-6"):
            ui.label("Add New Property").classes("text-xl font-bold mb-4")
            p_name = ui.input(label="Property Name").classes("w-full mb-2").props("outlined")
            p_address = ui.input(label="Address").classes("w-full mb-4").props("outlined")

            async def save_prop():
                if not p_name.value or not p_address.value:
                    return ui.notify("Name and address are required", type="warning")
                ok = await run.io_bound(add_property, user_id, p_name.value, p_address.value)
                if ok:
                    ui.notify("Property added!", type="positive")
                    add_prop_dialog.close()
                    ui.navigate.to("/properties")
                else:
                    ui.notify("Failed to add property", type="negative")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=add_prop_dialog.close).props("flat")
                ui.button("Save", on_click=save_prop).props("unelevated color=primary")

        # ── Add Unit Modal ─────────────────────────────────────────────────
        selected_prop_id_for_unit = {"id": None}
        with ui.dialog() as add_unit_dialog, ui.card().classes("w-96 p-6"):
            ui.label("Add New Unit").classes("text-xl font-bold mb-4")
            u_num = ui.input(label="Unit Number").classes("w-full mb-2").props("outlined")
            u_rent = ui.number(label="Default Rent", value=1000).classes("w-full mb-4").props("outlined")

            async def save_unit():
                if not u_num.value:
                    return ui.notify("Unit number is required", type="warning")
                if not selected_prop_id_for_unit["id"]:
                    return ui.notify("No property selected. Please add a property first.", type="negative")
                ok = await run.io_bound(add_unit, user_id, selected_prop_id_for_unit["id"], u_num.value, u_rent.value)
                if ok:
                    ui.notify("Unit added!", type="positive")
                    add_unit_dialog.close()
                    ui.navigate.to("/properties")
                else:
                    ui.notify("Failed to add unit", type="negative")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=add_unit_dialog.close).props("flat")
                ui.button("Save", on_click=save_unit).props("unelevated color=primary")

        # ── Main View ──────────────────────────────────────────────────────
        with ui.row().classes("w-full justify-end mb-4"):
            ui.button("Add Property", on_click=add_prop_dialog.open, icon="add_business").props("unelevated rounded")

        if not properties:
            with ui.card().classes("w-full p-12 items-center text-center"):
                ui.icon("domain_disabled", size="64px", color="grey-4")
                ui.label("No properties found.").classes("text-xl font-bold mt-4")
                ui.label("Start by adding your first building or complex.").classes("text-slate-500")
                ui.button("Add Property", on_click=add_prop_dialog.open).classes("mt-4").props("outline")
        else:
            with ui.column().classes("w-full gap-6"):
                for prop in properties:
                    with ui.card().classes("w-full p-6").style(f"background: {CARD_BG}; border: 1px solid {BORDER}"):
                        with ui.row().classes("w-full justify-between items-start"):
                            with ui.column().classes("gap-1"):
                                ui.label(prop["name"]).classes("text-xl font-bold")
                                ui.label(prop["address"]).classes("text-sm flex items-center gap-1").style(f"color: {TEXT_SECONDARY}")

                            with ui.row().classes("gap-1 items-center"):
                                def open_unit_dialog(pid=prop["id"]):
                                    selected_prop_id_for_unit["id"] = pid
                                    add_unit_dialog.open()

                                ui.button("Add Unit", on_click=open_unit_dialog, icon="add").props("flat dense")

                                # ── Edit Property ──────────────────────────
                                def open_edit_prop(p=prop):
                                    with ui.dialog() as dlg, ui.card().classes("w-96 p-6"):
                                        ui.label("Edit Property").classes("text-xl font-bold mb-4")
                                        ep_name = ui.input(label="Property Name", value=p["name"]).classes("w-full mb-2").props("outlined")
                                        ep_addr = ui.input(label="Address", value=p["address"]).classes("w-full mb-4").props("outlined")

                                        async def do_edit_prop():
                                            def update_prop_db(pid, name, address, uid):
                                                from app.models.database import get_client
                                                from app.services.audit_service import log_action
                                                client = get_client()
                                                client.table("properties").update({
                                                    "name": name,
                                                    "address": address,
                                                }).eq("id", pid).execute()
                                                log_action(uid, "PROPERTY_UPDATED", "property", pid,
                                                           new_value={"name": name, "address": address})

                                            try:
                                                await run.io_bound(update_prop_db, p["id"], ep_name.value, ep_addr.value, user_id)
                                                ui.notify("Property updated", type="positive")
                                                dlg.close()
                                                ui.navigate.to("/properties")
                                            except Exception as e:
                                                ui.notify(f"Failed: {e}", type="negative")

                                        with ui.row().classes("w-full justify-end gap-2"):
                                            ui.button("Cancel", on_click=dlg.close).props("flat")
                                            ui.button("Save", on_click=do_edit_prop).props("unelevated color=primary")
                                    dlg.open()

                                ui.button(icon="edit", on_click=open_edit_prop).props(
                                    "flat round dense color=primary"
                                ).tooltip("Edit property")

                                # ── Delete Property ──────────────────────────
                                def open_delete_prop(p=prop):
                                    with ui.dialog() as dlg, ui.card().classes("p-6 w-96"):
                                        ui.label(f"Delete '{p['name']}'?").classes("text-lg font-semibold mb-1")
                                        ui.label(
                                            "This will permanently delete the property and ALL its units. "
                                            "Tenant records will not be deleted but their unit link will be lost."
                                        ).classes("text-sm mb-4").style(f"color: {TEXT_SECONDARY}")
                                        with ui.row().classes("gap-2 justify-end w-full"):
                                            ui.button("Cancel", on_click=dlg.close).props("flat")
                                            async def do_delete_prop():
                                                ok = await run.io_bound(delete_property, user_id, p["id"])
                                                if ok:
                                                    ui.notify(f"'{p['name']}' deleted.", type="positive")
                                                    dlg.close()
                                                    ui.navigate.to("/properties")
                                                else:
                                                    ui.notify("Failed to delete property.", type="negative")
                                            ui.button("Delete", on_click=do_delete_prop, icon="delete").props("unelevated color=negative")
                                    dlg.open()

                                ui.button(icon="delete", on_click=open_delete_prop).props(
                                    "flat round dense color=negative"
                                ).tooltip("Delete property")

                        ui.separator().classes("my-4")

                        units = await run.io_bound(get_units_by_property, prop["id"])
                        if not units:
                            ui.label("No units in this property. Add one to get started.").classes("text-sm text-slate-400 italic")
                        else:
                            with ui.row().classes("w-full gap-3 flex-wrap"):
                                for u in units:
                                    status_color = (
                                        "positive" if u["status"] == "Occupied"
                                        else ("warning" if u["status"] == "Maintenance" else "grey")
                                    )
                                    with ui.card().classes("p-3 min-w-[140px] items-center text-center border shadow-none"):
                                        ui.label(u["unit_number"]).classes("font-bold text-lg")
                                        ui.badge(u["status"], color=status_color).classes("text-[10px]")

                                        # Display active tenant if occupied
                                        t_name = tenant_lookup.get(u["id"])
                                        if t_name and u["status"] == "Occupied":
                                            ui.label(t_name).classes("text-xs font-semibold text-indigo-600 mt-1 truncate max-w-[110px]")

                                        ui.label(f"${u['default_rent']}/mo").classes("text-xs text-slate-500 mt-1")

                                        # ── Unit actions ──────────────────
                                        with ui.row().classes("gap-0 mt-1 justify-center"):
                                            def open_edit_unit(unit=u):
                                                with ui.dialog() as dlg, ui.card().classes("w-80 p-6"):
                                                    ui.label("Edit Unit").classes("text-lg font-semibold mb-4")
                                                    eu_num = ui.input(label="Unit Number", value=unit["unit_number"]).classes("w-full mb-2").props("outlined")
                                                    eu_rent = ui.number(label="Default Rent ($)", value=unit["default_rent"]).classes("w-full mb-4").props("outlined")

                                                    async def do_edit_unit():
                                                        ok = await run.io_bound(update_unit, user_id, unit["id"], eu_num.value, eu_rent.value or 0)
                                                        if ok:
                                                            ui.notify("Unit updated", type="positive")
                                                            dlg.close()
                                                            ui.navigate.to("/properties")
                                                        else:
                                                            ui.notify("Failed to update unit", type="negative")

                                                    with ui.row().classes("w-full justify-end gap-2"):
                                                        ui.button("Cancel", on_click=dlg.close).props("flat")
                                                        ui.button("Save", on_click=do_edit_unit).props("unelevated color=primary")
                                                dlg.open()

                                            ui.button(icon="edit", on_click=open_edit_unit).props(
                                                "flat round dense color=primary size=xs"
                                            ).tooltip("Edit unit")

                                            def open_delete_unit(unit=u):
                                                with ui.dialog() as dlg, ui.card().classes("p-5 w-80"):
                                                    ui.label(f"Delete Unit {unit['unit_number']}?").classes("text-base font-semibold mb-2")
                                                    ui.label("This cannot be undone. Tenant records linked to this unit will remain.").classes("text-sm mb-4").style(f"color: {TEXT_SECONDARY}")
                                                    with ui.row().classes("gap-2 justify-end w-full"):
                                                        ui.button("Cancel", on_click=dlg.close).props("flat")
                                                        async def do_delete_unit():
                                                            ok = await run.io_bound(delete_unit, user_id, unit["id"])
                                                            if ok:
                                                                ui.notify(f"Unit {unit['unit_number']} deleted.", type="positive")
                                                                dlg.close()
                                                                ui.navigate.to("/properties")
                                                            else:
                                                                ui.notify("Failed to delete unit.", type="negative")
                                                        ui.button("Delete", on_click=do_delete_unit, icon="delete").props("unelevated color=negative size=sm")
                                                dlg.open()

                                            ui.button(icon="delete", on_click=open_delete_unit).props(
                                                "flat round dense color=negative size=xs"
                                            ).tooltip("Delete unit")
