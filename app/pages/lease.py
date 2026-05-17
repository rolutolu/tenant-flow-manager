"""Lease Management page — generate leases, view status, browse documents."""

from nicegui import ui
from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, ACCENT, SUCCESS, WARNING, TEXT_SECONDARY, CARD_BG, BORDER
from app.services.tenant_service import get_all_tenants, delete_tenant
from app.services.lease_service import generate_lease_pdf
from app.services.document_service import list_all_document_folders, get_signed_url
from app.services.property_service import get_properties
from app.models.database import get_client


@ui.page("/lease")
@require_role("admin", "manager")
def lease_page():
    user_id = get_user_id()
    doc_browser_id = "document-browser-section"

    with page_layout(title="Lease Management"):
        section_header("Lease Management", "Generate agreements, track signatures, and browse documents")

        # ── STATE ───────────────────────────────────────────────────────
        all_folders_list = list_all_document_folders()
        
        # ── CORE FUNCTIONS ──────────────────────────────────────────────
        def refresh_files(selected_val=None):
            """Refresh the file list based on selection."""
            file_container.clear()
            folder = selected_val or folder_selector.value
            if not folder:
                return
                
            client = get_client()
            try:
                path_prefix = f"tenants/{folder}"
                files = client.storage.from_("documents").list(path_prefix)
                
                with file_container:
                    if files:
                        for f in files:
                            if f['name'] == '.emptyFolderPlaceholder': continue
                            
                            filename = f['name']
                            full_file_path = f"{path_prefix}/{filename}"
                            
                            with ui.row().classes("items-center justify-between w-full p-3 rounded-lg hover:bg-slate-50 border border-slate-100"):
                                with ui.row().classes("items-center gap-3"):
                                    ui.icon("description", size="20px", color="primary")
                                    ui.label(filename).classes("text-sm font-medium")
                                
                                # Use a factory function to avoid closure late-binding issues
                                def create_view_func(p):
                                    return lambda: ui.navigate.to(get_signed_url(p), new_tab=True)
                                    
                                ui.button("View", on_click=create_view_func(full_file_path)).props("flat dense color=primary")
                    else:
                        ui.label("No files in this folder.").classes("text-sm text-slate-500")
            except Exception as err:
                with file_container:
                    ui.label(f"Error: {str(err)}").classes("text-negative")

        def handle_jump(e):
            """Jump to a specific tenant's folder from the table."""
            row_data = e.args
            target = f"{row_data['unit']}_{row_data['name'].replace(' ', '_')}"
            
            # Update selector
            folder_selector.value = target
            refresh_files(target)
            
            ui.notify(f"Showing documents for {row_data['name']}")
            ui.run_javascript(f'document.getElementById("{doc_browser_id}").scrollIntoView({{behavior: "smooth"}})')

        # ── UI LAYOUT ───────────────────────────────────────────────────
        with ui.row().classes("w-full gap-6 flex-wrap items-start"):

            # ── Generate Lease ─────────────────────────────────────────────
            with ui.card().classes("p-6 rounded-2xl shadow-sm card-hover flex-1 min-w-[350px]").style(
                f"background: {CARD_BG}; border: 1px solid {BORDER}"
            ):
                with ui.row().classes("items-center gap-3 mb-4"):
                    with ui.element("div").classes("rounded-xl p-2.5").style(f"background: {ACCENT}18"):
                        ui.icon("description", size="24px", color="primary")
                    ui.label("Generate Lease").classes("text-lg font-semibold")

                # Load properties for selection
                properties_list = get_properties(user_id)
                prop_options = {p["id"]: p["name"] for p in properties_list}
                
                t_name = ui.input(label="Tenant Name").classes("w-full").props("outlined")
                
                # Property Selector
                prop_selector = ui.select(
                    label="Property",
                    options=prop_options
                ).classes("w-full").props("outlined")
                
                # Manual Unit Number input (text field so they can type numbers/letters)
                t_unit = ui.input(label="Unit Number").classes("w-full").props("outlined")
                
                t_rent = ui.number(label="Rent ($)", value=1500).classes("w-full").props("outlined")

                def on_gen():
                    if not t_name.value or not prop_selector.value or not t_unit.value:
                        return ui.notify("Tenant Name, Property, and Unit Number are required", type="warning")
                    try:
                        prop_name = prop_options[prop_selector.value]
                        unit_number = str(t_unit.value)
                        
                        generate_lease_pdf(
                            tenant_name=t_name.value,
                            unit=unit_number,
                            rent_amount=t_rent.value or 0,
                            start_date="TBD",
                            end_date="TBD",
                            property_name=prop_name
                        )
                        ui.notify("Lease generated!", type="positive")
                        folder_selector.options = list_all_document_folders()
                    except Exception as ex:
                        ui.notify(str(ex), type="negative")

                ui.button("Generate", on_click=on_gen, icon="add").classes("w-full mt-2").props("unelevated rounded")

            # ── Status Table ───────────────────────────────────────────────
            with ui.card().classes("p-6 rounded-2xl shadow-sm flex-1 min-w-[450px]").style(
                f"background: {CARD_BG}; border: 1px solid {BORDER}"
            ):
                ui.label("Active Tenants").classes("text-lg font-semibold mb-4")
                
                rows = get_all_tenants(user_id)
                if rows:
                    cols = [
                        {"name": "unit", "label": "Unit", "field": "unit", "align": "left"},
                        {"name": "name", "label": "Name", "field": "name", "align": "left"},
                        {"name": "docs", "label": "Files", "field": "docs", "align": "center"},
                        {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
                    ]
                    
                    def handle_delete(e):
                        row_data = e.args
                        tenant_id = row_data["id"]
                        if delete_tenant(tenant_id):
                            ui.notify(f"Deleted {row_data['name']}", type="positive")
                            # A simple refresh
                            ui.navigate.to("/lease")
                        else:
                            ui.notify("Failed to delete tenant", type="negative")

                    tbl = ui.table(columns=cols, rows=rows).classes("w-full").props("flat")
                    tbl.add_slot('body-cell-docs', '''
                        <q-td :props="props">
                            <q-btn flat round color="primary" icon="folder" @click="$parent.$emit('jump', props.row)" />
                        </q-td>
                    ''')
                    tbl.add_slot('body-cell-actions', '''
                        <q-td :props="props">
                            <q-btn flat round color="negative" icon="delete" @click="$parent.$emit('delete_row', props.row)" />
                        </q-td>
                    ''')
                    tbl.on('jump', handle_jump)
                    tbl.on('delete_row', handle_delete)
                else:
                    ui.label("No tenants.").classes("text-slate-500")

        # ── Document Browser ───────────────────────────────────────────────
        with ui.card().classes("w-full p-6 mt-4").props(f'id="{doc_browser_id}"').style(f"background: {CARD_BG}; border: 1px solid {BORDER}"):
            ui.label("Cloud Document Browser").classes("text-lg font-semibold mb-4")
            
            folder_selector = ui.select(
                label="Folder", 
                options=all_folders_list,
                on_change=lambda e: refresh_files(e.value)
            ).classes("w-full max-w-sm").props("outlined")
            
            file_container = ui.column().classes("w-full mt-3")
            
            if not all_folders_list:
                ui.label("No folders found.").classes("text-sm text-slate-500")
