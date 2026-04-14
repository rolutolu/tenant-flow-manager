"""Lease Management page — generate leases, view status, browse documents."""

from nicegui import ui
from app.auth import require_auth
from app.theme import page_layout, section_header, ACCENT, SUCCESS, WARNING, TEXT_SECONDARY
from app.services.tenant_service import get_all_tenants
from app.services.lease_service import generate_lease_pdf
from app.services.document_service import list_all_document_folders, get_tenant_documents
from app.config import DOCS_DIR
import os


@ui.page("/lease")
@require_auth
def lease_page():
    with page_layout(title="Lease Management"):
        section_header("Lease Management", "Generate agreements, track signatures, and browse documents")

        with ui.row().classes("w-full gap-6 flex-wrap items-start"):

            # ── Left: Generate Lease ───────────────────────────────────────
            with ui.card().classes("p-6 rounded-xl shadow-sm flex-1 min-w-[350px]").style(
                "border: 1px solid #E2E8F0"
            ):
                with ui.row().classes("items-center gap-2 mb-4"):
                    ui.icon("description", size="24px").style(f"color: {ACCENT}")
                    ui.label("Generate New Lease").classes("text-lg font-semibold")

                tenant_name = ui.input(label="Tenant Name").classes("w-full").props("outlined")
                unit = ui.input(label="Unit Number").classes("w-full").props("outlined")
                rent = ui.number(label="Monthly Rent ($)", value=1500, min=100, step=50).classes(
                    "w-full"
                ).props("outlined")
                start_date = ui.input(label="Lease Start (YYYY-MM-DD)").classes("w-full").props("outlined")
                end_date = ui.input(label="Lease End (YYYY-MM-DD)").classes("w-full").props("outlined")

                result_label = ui.label("").classes("text-sm mt-2")
                result_label.set_visibility(False)

                def generate():
                    if not tenant_name.value or not unit.value:
                        ui.notify("Tenant name and unit are required", type="warning")
                        return
                    try:
                        path = generate_lease_pdf(
                            tenant_name.value, unit.value,
                            rent.value or 0,
                            start_date.value or "TBD",
                            end_date.value or "TBD",
                        )
                        result_label.text = f"Lease saved to: {path}"
                        result_label.set_visibility(True)
                        ui.notify("Lease PDF generated successfully!", type="positive")
                    except Exception as e:
                        ui.notify(f"Error: {str(e)}", type="negative")

                ui.button("Generate Lease PDF", on_click=generate, icon="picture_as_pdf").classes(
                    "w-full mt-2"
                ).props("unelevated")

            # ── Right: Lease Status Table ──────────────────────────────────
            with ui.card().classes("p-6 rounded-xl shadow-sm flex-1 min-w-[350px]").style(
                "border: 1px solid #E2E8F0"
            ):
                with ui.row().classes("items-center gap-2 mb-4"):
                    ui.icon("list_alt", size="24px").style(f"color: {ACCENT}")
                    ui.label("Lease Status").classes("text-lg font-semibold")

                tenants = get_all_tenants()
                if tenants:
                    columns = [
                        {"name": "unit", "label": "Unit", "field": "unit", "align": "left"},
                        {"name": "name", "label": "Tenant", "field": "name", "align": "left"},
                        {"name": "rent_amount", "label": "Rent", "field": "rent_amount", "align": "right"},
                        {"name": "lease_start", "label": "Start", "field": "lease_start", "align": "center"},
                        {"name": "lease_end", "label": "End", "field": "lease_end", "align": "center"},
                        {"name": "lease_signed", "label": "Signed", "field": "lease_signed", "align": "center"},
                    ]
                    ui.table(columns=columns, rows=tenants).classes("w-full").props(
                        "flat bordered dense"
                    )
                else:
                    ui.label("No tenants in the system yet.").classes("text-sm").style(
                        f"color: {TEXT_SECONDARY}"
                    )

        # ── Bottom: Document Browser ───────────────────────────────────────
        with ui.card().classes("w-full p-6 rounded-xl shadow-sm mt-2").style(
            "border: 1px solid #E2E8F0"
        ):
            with ui.row().classes("items-center gap-2 mb-4"):
                ui.icon("folder_open", size="24px").style(f"color: {ACCENT}")
                ui.label("Document Browser").classes("text-lg font-semibold")

            folders = list_all_document_folders()
            if folders:
                selected_folder = ui.select(
                    label="Select Tenant Folder",
                    options=folders,
                ).classes("w-full max-w-md").props("outlined")

                file_list = ui.column().classes("w-full mt-3")

                def show_files():
                    file_list.clear()
                    if selected_folder.value:
                        folder_path = DOCS_DIR / selected_folder.value
                        if folder_path.exists():
                            files = list(folder_path.iterdir())
                            with file_list:
                                if files:
                                    for f in files:
                                        with ui.row().classes("items-center gap-2"):
                                            ui.icon("insert_drive_file", size="18px").style(
                                                f"color: {TEXT_SECONDARY}"
                                            )
                                            ui.label(f.name).classes("text-sm")
                                else:
                                    ui.label("No files in this folder.").classes("text-sm").style(
                                        f"color: {TEXT_SECONDARY}"
                                    )

                selected_folder.on("update:model-value", lambda: show_files())
            else:
                ui.label("No document folders created yet. Process a new intake first.").classes(
                    "text-sm"
                ).style(f"color: {TEXT_SECONDARY}")
