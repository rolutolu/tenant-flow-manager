"""Data Ingestion page for bulk importing tenants, units, and properties via Excel/CSV."""
from nicegui import ui
from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, ACCENT, TEXT_SECONDARY, CARD_BG, BORDER
from app.services.ingestion_service import parse_file, process_bulk_import

@ui.page("/import")
@require_role("admin", "manager")
def import_page():
    user_id = get_user_id()
    
    # State tracking
    state = {
        "df": None,
        "filename": "",
        "columns": [],
        "mapping": {
            "Property": None,
            "Unit": None,
            "Tenant": None,
            "Rent": None
        }
    }
    
    with page_layout(title="Data Ingestion"):
        section_header("Bulk Data Import", "Upload an Excel or CSV file to quickly onboard properties, units, and tenants")
        
        # ── Step 1: Upload File ──────────────────────────────────────────
        upload_card = ui.card().classes("w-full p-6 mb-6 shadow-sm").style(f"background: {CARD_BG}; border: 1px solid {BORDER}")
        with upload_card:
            ui.label("1. Upload Data File").classes("text-lg font-bold mb-2")
            ui.label("Accepts .xlsx or .csv files.").classes("text-sm mb-4").style(f"color: {TEXT_SECONDARY}")
            
            def handle_upload(e):
                try:
                    file_obj = getattr(e, 'file', None) or e
                    content = file_obj.read() if hasattr(file_obj, 'read') else file_obj.content.read()
                    file_name = getattr(file_obj, 'name', getattr(file_obj, 'filename', 'data.csv'))
                    
                    df = parse_file(content, file_name)
                    if df is not None and not df.empty:
                        state["df"] = df
                        state["filename"] = file_name
                        state["columns"] = df.columns.tolist()
                        ui.notify(f"Successfully parsed {len(df)} rows from {file_name}", type="positive")
                        
                        # Auto-guess mappings
                        for col in state["columns"]:
                            col_lower = col.lower()
                            if "prop" in col_lower or "build" in col_lower: state["mapping"]["Property"] = col
                            elif "unit" in col_lower or "apt" in col_lower: state["mapping"]["Unit"] = col
                            elif "name" in col_lower or "tenant" in col_lower: state["mapping"]["Tenant"] = col
                            elif "rent" in col_lower or "amount" in col_lower: state["mapping"]["Rent"] = col
                        
                        refresh_mapping_ui()
                    else:
                        ui.notify("File is empty or unsupported format.", type="negative")
                except Exception as err:
                    ui.notify(f"Failed to process file: {str(err)}", type="negative")
            
            ui.upload(label="Drag & Drop Excel/CSV", auto_upload=True, on_upload=handle_upload, max_files=1).classes("w-full max-w-lg").props('accept=".csv,.xlsx,.xls"')
            
        # ── Step 2: Map Columns ──────────────────────────────────────────
        mapping_area = ui.column().classes("w-full gap-4")
        
        def refresh_mapping_ui():
            mapping_area.clear()
            if state["df"] is None:
                return
                
            with mapping_area:
                with ui.card().classes("w-full p-6 shadow-sm").style(f"background: {CARD_BG}; border: 1px solid {BORDER}"):
                    ui.label(f"2. Map Columns for '{state['filename']}'").classes("text-lg font-bold mb-4")
                    
                    with ui.row().classes("w-full gap-6 flex-wrap"):
                        ui.select(label="Property Name Column *", options=state["columns"], value=state["mapping"].get("Property"), on_change=lambda e: state["mapping"].update({"Property": e.value})).classes("flex-1 min-w-[200px]").props("outlined")
                        ui.select(label="Unit Number Column *", options=state["columns"], value=state["mapping"].get("Unit"), on_change=lambda e: state["mapping"].update({"Unit": e.value})).classes("flex-1 min-w-[200px]").props("outlined")
                    with ui.row().classes("w-full gap-6 flex-wrap mt-2"):
                        ui.select(label="Tenant Name Column *", options=state["columns"], value=state["mapping"].get("Tenant"), on_change=lambda e: state["mapping"].update({"Tenant": e.value})).classes("flex-1 min-w-[200px]").props("outlined")
                        ui.select(label="Rent Amount Column", options=state["columns"], value=state["mapping"].get("Rent"), on_change=lambda e: state["mapping"].update({"Rent": e.value})).classes("flex-1 min-w-[200px]").props("outlined clearable")
                    
                    def run_import():
                        try:
                            ui.notify("Processing... this may take a moment.", type="info")
                            p_cnt, u_cnt, t_cnt = process_bulk_import(user_id, state["df"], state["mapping"])
                            ui.notify(f"Success! Added {p_cnt} properties, {u_cnt} units, and {t_cnt} tenants.", type="positive", timeout=5000)
                            # Reset
                            state["df"] = None
                            refresh_mapping_ui()
                        except ValueError as ve:
                            ui.notify(str(ve), type="warning")
                        except Exception as e:
                            ui.notify(f"Import failed: {str(e)}", type="negative")
                            
                    ui.button("Start Bulk Import", on_click=run_import, icon="cloud_upload").classes("mt-6").props("unelevated color=primary size=lg")
