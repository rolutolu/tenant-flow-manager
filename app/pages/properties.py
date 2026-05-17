"""Properties page for managing buildings and units."""
from nicegui import ui
from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, ACCENT, TEXT_SECONDARY, CARD_BG, BORDER
from app.services.property_service import get_properties, add_property, get_units_by_property, add_unit, update_unit_status
from app.services.tenant_service import get_all_tenants

@ui.page("/properties")
@require_role("admin", "manager")
def properties_page():
    user_id = get_user_id()
    
    with page_layout(title="Properties & Units"):
        section_header("Property Management", "Manage your buildings, complexes, and individual units")
        
        properties = get_properties(user_id)
        tenants = get_all_tenants(user_id)
        # Create lookup map: {unit_id: tenant_name}
        tenant_lookup = {t["unit_id"]: t["name"] for t in tenants if t.get("unit_id")}
        
        # ── Add Property Modal ──────────────────────────────────────────────
        with ui.dialog() as add_prop_dialog, ui.card().classes("w-96 p-6"):
            ui.label("Add New Property").classes("text-xl font-bold mb-4")
            p_name = ui.input(label="Property Name").classes("w-full mb-2").props("outlined")
            p_address = ui.input(label="Address").classes("w-full mb-4").props("outlined")
            
            def save_prop():
                if not p_name.value or not p_address.value:
                    return ui.notify("Name and address are required", type="warning")
                if add_property(user_id, p_name.value, p_address.value):
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
            
            def save_unit():
                if not u_num.value:
                    return ui.notify("Unit number is required", type="warning")
                # Bug fix #8: Guard against null property_id
                if not selected_prop_id_for_unit["id"]:
                    return ui.notify("No property selected. Please add a property first.", type="negative")
                if add_unit(user_id, selected_prop_id_for_unit["id"], u_num.value, u_rent.value):
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
                                ui.label(prop["address"]).classes("text-sm text-slate-500 flex items-center gap-1").style(f"color: {TEXT_SECONDARY}")
                            
                            def open_unit_dialog(pid=prop["id"]):
                                selected_prop_id_for_unit["id"] = pid
                                add_unit_dialog.open()
                                
                            ui.button("Add Unit", on_click=open_unit_dialog, icon="add").props("flat dense")

                        ui.separator().classes("my-4")
                        
                        units = get_units_by_property(prop["id"])
                        if not units:
                            ui.label("No units in this property. Add one to get started.").classes("text-sm text-slate-400 italic")
                        else:
                            with ui.row().classes("w-full gap-3 flex-wrap"):
                                for u in units:
                                    status_color = "positive" if u["status"] == "Occupied" else ("warning" if u["status"] == "Maintenance" else "grey")
                                    with ui.card().classes("p-3 min-w-[120px] items-center text-center border shadow-none"):
                                        ui.label(u["unit_number"]).classes("font-bold text-lg")
                                        ui.badge(u["status"], color=status_color).classes("text-[10px]")
                                        
                                        # Display active tenant if occupied
                                        t_name = tenant_lookup.get(u["id"])
                                        if t_name and u["status"] == "Occupied":
                                            ui.label(t_name).classes("text-xs font-semibold text-indigo-600 mt-1 truncate max-w-[100px]")
                                            
                                        ui.label(f"${u['default_rent']}/mo").classes("text-xs text-slate-500 mt-1")
