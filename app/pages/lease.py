"""Lease Management page — generate leases, view status, browse documents."""

from nicegui import ui, run
from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, ACCENT, CARD_BG, BORDER
from app.services.tenant_service import get_all_tenants, delete_tenant, update_tenant
from app.services.lease_service import generate_lease_pdf
from app.services.document_service import (
    list_all_document_folders, get_signed_url, get_document_by_filepath, delete_document,
)
from app.services.notification_service import send_lease_email
from app.services.property_service import get_properties
from app.services.audit_service import log_action
from app.components.tenant_edit_dialog import open_tenant_edit_dialog
from app.models.database import get_client


@ui.page("/lease")
@require_role("admin", "manager")
async def lease_page():
    user_id = get_user_id()
    doc_browser_id = "document-browser-section"
    last_lease_path = {"path": None}

    # Fetch initial DB state asynchronously
    all_folders_list = await run.io_bound(list_all_document_folders)
    tenants = await run.io_bound(get_all_tenants, user_id)
    properties_list = await run.io_bound(get_properties, user_id)
    tenant_options = {t["id"]: f"{t['name']} (Unit {t['unit']})" for t in tenants}

    with page_layout(title="Lease Management"):
        section_header("Lease Management", "Generate agreements, track signatures, and browse documents")

        async def refresh_files(selected_val=None):
            file_container.clear()
            folder = selected_val or folder_selector.value
            if not folder:
                return

            client = get_client()
            try:
                path_prefix = f"tenants/{folder}"
                files = await run.io_bound(client.storage.from_("documents").list, path_prefix)

                with file_container:
                    if files:
                        for f in files:
                            if f["name"] == ".emptyFolderPlaceholder":
                                continue

                            filename = f["name"]
                            full_file_path = f"{path_prefix}/{filename}"
                            doc_record = await run.io_bound(get_document_by_filepath, full_file_path)

                            with ui.row().classes(
                                "items-center justify-between w-full p-3 rounded-lg hover:bg-slate-50 border border-slate-100"
                            ):
                                with ui.row().classes("items-center gap-3"):
                                    ui.icon("description", size="20px", color="primary")
                                    ui.label(filename).classes("text-sm font-medium")

                                with ui.row().classes("gap-1"):
                                    async def view_file(p=full_file_path):
                                        url = await run.io_bound(get_signed_url, p)
                                        if url:
                                            ui.navigate.to(url, new_tab=True)
                                        else:
                                            ui.notify("Could not get file link", type="negative")

                                    ui.button(
                                        "View",
                                        on_click=view_file,
                                    ).props("flat dense color=primary")

                                    def confirm_delete(p=full_file_path, doc=doc_record):
                                        with ui.dialog() as dlg, ui.card().classes("p-6"):
                                            ui.label(f"Delete {p.split('/')[-1]}?").classes("font-semibold mb-4")
                                            with ui.row().classes("gap-2 justify-end"):
                                                ui.button("Cancel", on_click=dlg.close).props("flat")

                                                async def do_delete():
                                                    success = await run.io_bound(delete_document, doc["id"], p) if doc else False
                                                    if doc and success:
                                                        await run.io_bound(log_action, user_id, "DOCUMENT_DELETED", "document", doc["id"])
                                                        ui.notify("Document deleted", type="positive")
                                                        dlg.close()
                                                        await refresh_files(folder)
                                                    else:
                                                        ui.notify("Failed to delete document", type="negative")

                                                ui.button("Delete", on_click=do_delete).props("unelevated color=negative")

                                        dlg.open()

                                    ui.button("Delete", on_click=confirm_delete).props("flat dense color=negative")
                    else:
                        ui.label("No files in this folder.").classes("text-sm text-slate-500")
            except Exception as err:
                with file_container:
                    ui.label(f"Error: {str(err)}").classes("text-negative")

        async def handle_jump(e):
            row_data = e.args
            target = f"{row_data['unit']}_{row_data['name'].replace(' ', '_')}"
            folder_selector.value = target
            await refresh_files(target)
            ui.notify(f"Showing documents for {row_data['name']}")
            ui.run_javascript(
                f'document.getElementById("{doc_browser_id}").scrollIntoView({{behavior: "smooth"}})'
            )

        with ui.row().classes("w-full gap-6 flex-wrap items-start"):

            with ui.card().classes("p-6 rounded-2xl shadow-sm card-hover flex-1 min-w-[350px]").style(
                f"background: {CARD_BG}; border: 1px solid {BORDER}"
            ):
                with ui.row().classes("items-center gap-3 mb-4"):
                    with ui.element("div").classes("rounded-xl p-2.5").style(f"background: {ACCENT}18"):
                        ui.icon("description", size="24px", color="primary")
                    ui.label("Generate Lease").classes("text-lg font-semibold")
                prop_options = {p["id"]: p["name"] for p in properties_list}

                tenant_picker = ui.select(
                    label="Select Tenant (optional)",
                    options=tenant_options,
                    with_input=True,
                ).classes("w-full").props("outlined clearable")

                t_name = ui.input(label="Tenant Name").classes("w-full").props("outlined")
                prop_selector = ui.select(label="Property", options=prop_options).classes("w-full").props("outlined")
                t_unit = ui.input(label="Unit Number").classes("w-full").props("outlined")
                t_rent = ui.number(label="Rent ($)", value=1500).classes("w-full").props("outlined")
                t_start = ui.input(label="Lease Start (YYYY-MM-DD)").classes("w-full").props("outlined")
                t_end = ui.input(label="Lease End (YYYY-MM-DD)").classes("w-full").props("outlined")

                def on_tenant_pick(e):
                    if not e.value:
                        return
                    tenant = next((t for t in tenants if t["id"] == e.value), None)
                    if tenant:
                        t_name.value = tenant["name"]
                        t_unit.value = tenant["unit"]
                        t_rent.value = tenant.get("rent_amount") or 0
                        t_start.value = tenant.get("lease_start") or ""
                        t_end.value = tenant.get("lease_end") or ""

                tenant_picker.on_value_change(on_tenant_pick)

                post_gen_row = ui.row().classes("w-full gap-2 mt-2")
                post_gen_row.set_visibility(False)

                async def on_gen():
                    if not t_name.value or not prop_selector.value or not t_unit.value:
                        return ui.notify("Tenant Name, Property, and Unit Number are required", type="warning")
                    if not t_start.value or not t_end.value:
                        return ui.notify("Lease start and end dates are required", type="warning")
                    try:
                        prop_name = prop_options[prop_selector.value]
                        path = await run.io_bound(
                            generate_lease_pdf,
                            tenant_name=t_name.value,
                            unit=str(t_unit.value),
                            rent_amount=t_rent.value or 0,
                            start_date=t_start.value,
                            end_date=t_end.value,
                            property_name=prop_name,
                            tenant_id=tenant_picker.value,
                        )
                        last_lease_path["path"] = path
                        ui.notify("Lease generated!", type="positive")
                        folders = await run.io_bound(list_all_document_folders)
                        folder_selector.options = folders
                        post_gen_row.set_visibility(True)
                    except Exception as ex:
                        ui.notify(str(ex), type="negative")

                ui.button("Generate", on_click=on_gen, icon="add").classes("w-full mt-2").props("unelevated rounded")

                with post_gen_row:
                    async def mark_signed():
                        tenant = next(
                            (t for t in tenants if t["name"] == t_name.value and t["unit"] == str(t_unit.value)),
                            None,
                        )
                        if tenant:
                            ok = await run.io_bound(update_tenant, tenant["id"], lease_signed="Yes")
                            if ok:
                                ui.notify("Lease marked as signed", type="positive")
                            else:
                                ui.notify("Could not update tenant", type="negative")
                        else:
                            ui.notify("Could not update tenant", type="negative")

                    async def send_lease():
                        tenant = next(
                            (t for t in tenants if t["name"] == t_name.value and t["unit"] == str(t_unit.value)),
                            None,
                        )
                        if not tenant or not tenant.get("email"):
                            return ui.notify("Tenant email is required. Edit tenant to add email.", type="warning")
                        if not last_lease_path["path"]:
                            return ui.notify("Generate a lease first", type="warning")
                        success, msg = await run.io_bound(
                            send_lease_email,
                            tenant["name"], tenant["email"], last_lease_path["path"], user_id=user_id
                        )
                        ui.notify(msg, type="positive" if success else "negative")

                    ui.button("Mark Signed", on_click=mark_signed, icon="draw").props("outline size=sm")
                    ui.button("Send Lease", on_click=send_lease, icon="email").props("outline size=sm")

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
                        if delete_tenant(row_data["id"]):
                            ui.notify(f"Deleted {row_data['name']}", type="positive")
                            ui.navigate.to("/lease")
                        else:
                            ui.notify("Failed to delete tenant", type="negative")

                    def handle_edit(e):
                        row = e.args
                        if isinstance(row, list):
                            row = row[0] if row else {}
                        if not isinstance(row, dict) or not row:
                            ui.notify("Could not load tenant data for editing.", type="warning")
                            return
                        open_tenant_edit_dialog(row, on_saved=lambda: ui.navigate.to("/lease"))

                    tbl = ui.table(columns=cols, rows=rows).classes("w-full").props("flat")
                    tbl.add_slot("body-cell-docs", """
                        <q-td :props="props">
                            <q-btn flat round color="primary" icon="folder"
                                   @click="$parent.$emit('jump', props.row)" />
                        </q-td>
                    """)
                    tbl.add_slot("body-cell-actions", """
                        <q-td :props="props">
                            <q-btn flat round color="primary" icon="edit"
                                   @click="$parent.$emit('edit_row', props.row)" />
                            <q-btn flat round color="negative" icon="delete"
                                   @click="$parent.$emit('delete_row', props.row)" />
                        </q-td>
                    """)
                    tbl.on("jump", handle_jump)
                    tbl.on("delete_row", handle_delete)
                    tbl.on("edit_row", handle_edit)
                else:
                    ui.label("No tenants.").classes("text-slate-500")

        with ui.card().classes("w-full p-6 mt-4").props(f'id="{doc_browser_id}"').style(
            f"background: {CARD_BG}; border: 1px solid {BORDER}"
        ):
            ui.label("Cloud Document Browser").classes("text-lg font-semibold mb-4")

            folder_selector = ui.select(
                label="Folder",
                options=all_folders_list,
                on_change=lambda e: refresh_files(e.value),
            ).classes("w-full max-w-sm").props("outlined")

            file_container = ui.column().classes("w-full mt-3")

            if not all_folders_list:
                ui.label("No folders found.").classes("text-sm text-slate-500")
