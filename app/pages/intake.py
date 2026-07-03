"""Intake & Screening page — tenant onboarding with document upload and reference checks."""

from nicegui import ui, events
from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, SUCCESS, TEXT_SECONDARY
from app.services.tenant_service import add_tenant
from app.services.document_service import save_uploaded_file
from app.services.notification_service import send_reference_check, send_reference_email
from app.services.property_service import get_properties, get_units_by_property
from app.services.reference_service import log_reference_check, update_reference_status, get_checks_for_tenant


@ui.page("/intake")
@require_role("admin", "manager")
def intake_page():
    user_id = get_user_id()
    state = {"tenant_id": None, "pending_refs": []}

    with page_layout(title="Intake & Screening"):
        section_header("New Tenant Intake", "Collect documents and verify references for prospective tenants")

        with ui.stepper().classes("w-full").props("vertical") as stepper:

            # ── Step 1: Basic Info ─────────────────────────────────────────
            with ui.step("Tenant Information", icon="person"):
                ui.label("Enter the prospective tenant's details").classes("text-sm mb-3").style(
                    f"color: {TEXT_SECONDARY}"
                )

                properties = get_properties(user_id)
                prop_options = {p["id"]: p["name"] for p in properties}
                unit_options = {}

                with ui.row().classes("w-full gap-4 flex-wrap"):
                    name_input = ui.input(label="Full Name").classes("flex-1 min-w-[250px]").props("outlined")
                    email_input = ui.input(label="Email").classes("flex-1 min-w-[250px]").props("outlined")

                    def on_prop_change(e):
                        if e.value:
                            units = get_units_by_property(e.value)
                            vacant_units = {
                                u["id"]: f"Unit {u['unit_number']} (${u['default_rent']})"
                                for u in units if u["status"] in ["Vacant", "Notice"]
                            }
                            unit_select.options = vacant_units
                            unit_select.value = None
                        else:
                            unit_select.options = {}

                    prop_select = ui.select(
                        label="Property", options=prop_options, on_change=on_prop_change
                    ).classes("flex-1 min-w-[250px]").props("outlined")

                with ui.row().classes("w-full gap-4 flex-wrap"):
                    unit_select = ui.select(label="Available Unit", options=unit_options).classes(
                        "flex-1 min-w-[250px]"
                    ).props("outlined")
                    rent_input = ui.number(label="Agreed Rent ($)", value=0, min=0, step=50).classes(
                        "flex-1 min-w-[250px]"
                    ).props("outlined")

                    def on_unit_change(e):
                        if e.value:
                            selected_unit = next(
                                (u for p in properties for u in get_units_by_property(p["id"]) if u["id"] == e.value),
                                None,
                            )
                            if selected_unit:
                                rent_input.value = selected_unit["default_rent"]

                    unit_select.on_value_change(on_unit_change)

                with ui.row().classes("w-full gap-4 flex-wrap"):
                    lease_start_input = ui.input(label="Lease Start (YYYY-MM-DD)").classes(
                        "flex-1 min-w-[200px]"
                    ).props("outlined")
                    lease_end_input = ui.input(label="Lease End (YYYY-MM-DD)").classes(
                        "flex-1 min-w-[200px]"
                    ).props("outlined")

                with ui.stepper_navigation():
                    ui.button("Next", on_click=stepper.next, icon="arrow_forward").props("unelevated rounded")

            # ── Step 2: Document Upload ────────────────────────────────────
            with ui.step("Document Collection", icon="upload_file"):
                ui.label("Upload required identification and financial documents").classes(
                    "text-sm mb-3"
                ).style(f"color: {TEXT_SECONDARY}")

                uploaded_files = {}
                ready_indicators = {}

                def handle_upload(e: events.UploadEventArguments, doc_type: str):
                    try:
                        file_obj = getattr(e, "file", None) or e
                        content = file_obj.read() if hasattr(file_obj, "read") else file_obj.content.read()
                        file_name = getattr(file_obj, "name", getattr(file_obj, "filename", "document"))
                        uploaded_files[doc_type] = {"name": file_name, "content": content}
                        if doc_type in ready_indicators:
                            ready_indicators[doc_type].set_visibility(True)
                        ui.notify(f"{doc_type} is ready to save!", type="positive")
                    except Exception as err:
                        ui.notify(f"Failed to read file: {str(err)}", type="negative")

                def handle_reject(e):
                    ui.notify("File rejected! Check file type (.pdf, .jpg, .png) and size (Max 20MB).", type="negative")

                with ui.column().classes("w-full gap-4"):
                    for doc_type, label, accept in [
                        ("Gov_ID", "Government ID (PDF/Image)", '.accept=".pdf,.jpg,.png,image/*"'),
                        ("Deposit_Slip", "Direct Deposit Slip", '.accept=".pdf,.jpg,.png,image/*"'),
                        ("Bank_Statements", "6 Months Bank Statements", '.accept=".pdf"'),
                    ]:
                        with ui.row().classes("items-center gap-2"):
                            ui.label(label).classes("font-medium text-sm")
                            ready_indicators[doc_type] = ui.badge("Ready", color="positive").props("rounded").classes("text-[10px]")
                            ready_indicators[doc_type].set_visibility(False)
                        ui.upload(
                            label="Choose file",
                            on_upload=lambda e, dt=doc_type: handle_upload(e, dt),
                            on_rejected=handle_reject,
                            auto_upload=True,
                            max_files=1,
                            max_file_size=20_000_000,
                        ).classes("w-full").props(accept)

                with ui.stepper_navigation():
                    ui.button("Back", on_click=stepper.previous, icon="arrow_back").props("flat")
                    ui.button("Next", on_click=stepper.next, icon="arrow_forward").props("unelevated rounded")

            # ── Step 3: References ─────────────────────────────────────────
            with ui.step("Reference Checks", icon="fact_check"):
                ui.label("Send inquiry to landlord or employer references").classes(
                    "text-sm mb-3"
                ).style(f"color: {TEXT_SECONDARY}")

                ui.label(
                    "Reference emails use Amazon SES when configured in .env. SMS uses Twilio if configured."
                ).classes("text-xs italic mb-4").style("color: #64748b;")

                ref_type = ui.radio(["Landlord", "Employer"], value="Landlord").props("inline")
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    ref_name = ui.input(label="Reference Name").classes("flex-1 min-w-[150px]").props("outlined")
                    ref_phone = ui.input(label="Reference Phone").classes("flex-1 min-w-[150px]").props("outlined")
                    ref_email = ui.input(label="Reference Email").classes("flex-1 min-w-[150px]").props("outlined")

                ref_result = ui.label("").classes("text-sm mt-2")
                ref_result.set_visibility(False)
                ref_table_container = ui.column().classes("w-full mt-4 gap-2")

                def refresh_ref_table():
                    ref_table_container.clear()
                    checks = []
                    if state["tenant_id"]:
                        checks = get_checks_for_tenant(state["tenant_id"])
                    elif state["pending_refs"]:
                        checks = state["pending_refs"]

                    with ref_table_container:
                        if not checks:
                            ui.label("No reference checks sent yet.").classes("text-sm text-slate-500")
                            return
                        for check in checks:
                            with ui.row().classes("items-center justify-between w-full p-2 border border-slate-100 rounded-lg"):
                                name = check.get("ref_name", "Reference")
                                channel = check.get("channel", "")
                                status = check.get("status", "Sent")
                                ui.label(f"{name} ({channel}) — {status}").classes("text-sm")
                                if check.get("id") and state["tenant_id"]:
                                    cid = check["id"]

                                    def mark_status(s, check_id=cid):
                                        if update_reference_status(check_id, s):
                                            refresh_ref_table()
                                            ui.notify(f"Marked as {s}", type="positive")

                                    with ui.row().classes("gap-1"):
                                        ui.button(icon="check", on_click=lambda s="Confirmed": mark_status(s)).props(
                                            "flat dense color=positive size=sm"
                                        ).tooltip("Mark Confirmed")
                                        ui.button(icon="close", on_click=lambda s="Declined": mark_status(s)).props(
                                            "flat dense color=negative size=sm"
                                        ).tooltip("Mark Declined")

                def record_ref(channel: str):
                    entry = {
                        "ref_name": ref_name.value or "Reference",
                        "ref_phone": ref_phone.value or "",
                        "ref_email": ref_email.value or "",
                        "ref_type": ref_type.value,
                        "channel": channel,
                        "status": "Sent",
                    }
                    if state["tenant_id"]:
                        check_id = log_reference_check(
                            user_id=user_id,
                            tenant_id=state["tenant_id"],
                            ref_name=entry["ref_name"],
                            ref_phone=entry["ref_phone"],
                            ref_email=entry["ref_email"],
                            ref_type=entry["ref_type"],
                            channel=channel,
                        )
                        if check_id:
                            entry["id"] = check_id
                    else:
                        state["pending_refs"].append(entry)
                    refresh_ref_table()

                def send_ref_sms():
                    if not ref_phone.value:
                        ui.notify("Please provide a phone number for SMS", type="warning")
                        return
                    success, msg = send_reference_check(
                        tenant_name=name_input.value or "Prospective Tenant",
                        ref_phone=ref_phone.value,
                        ref_name=ref_name.value or "Reference",
                    )
                    if success:
                        record_ref("SMS")
                    ref_result.text = msg
                    ref_result.set_visibility(True)
                    ui.notify(msg, type="positive" if success else "negative")

                def send_ref_email_action():
                    if not ref_email.value:
                        ui.notify("Please provide an email address", type="warning")
                        return
                    success, msg = send_reference_email(
                        tenant_name=name_input.value or "Prospective Tenant",
                        ref_email=ref_email.value,
                        ref_name=ref_name.value or "Reference",
                        user_id=user_id,
                    )
                    if success:
                        record_ref("Email")
                    ref_result.text = msg
                    ref_result.set_visibility(True)
                    ui.notify(msg, type="positive" if success else "negative")

                with ui.row().classes("gap-3 mt-2"):
                    ui.button("Send SMS", on_click=send_ref_sms, icon="sms").props("unelevated rounded")
                    ui.button("Send Email", on_click=send_ref_email_action, icon="email").props("outline rounded")

                refresh_ref_table()

                with ui.stepper_navigation():
                    ui.button("Back", on_click=stepper.previous, icon="arrow_back").props("flat")
                    ui.button("Next", on_click=stepper.next, icon="arrow_forward").props("unelevated rounded")

            # ── Step 4: Confirm & Save ─────────────────────────────────────
            with ui.step("Confirm & Save", icon="check_circle"):
                ui.label("Review the information and save the tenant record").classes(
                    "text-sm mb-3"
                ).style(f"color: {TEXT_SECONDARY}")

                result_area = ui.column().classes("w-full gap-2")

                def save_tenant():
                    if not name_input.value or not unit_select.value:
                        ui.notify("Name and Unit are required", type="warning")
                        return

                    unit_text = (
                        unit_select.options.get(unit_select.value, "Unknown").split(" ")[1]
                        if unit_select.value else "Unknown"
                    )

                    try:
                        tenant_id = add_tenant(
                            user_id=user_id,
                            name=name_input.value,
                            unit=unit_text,
                            unit_id=unit_select.value,
                            rent_amount=rent_input.value or 0,
                            email=email_input.value or "",
                            lease_start=lease_start_input.value or "",
                            lease_end=lease_end_input.value or "",
                        )
                    except Exception as e:
                        if "duplicate key" in str(e).lower():
                            ui.notify(f"Unit {unit_text} is already occupied or registered.", type="negative")
                        else:
                            ui.notify(f"Database error: {str(e)}", type="negative")
                        return

                    state["tenant_id"] = tenant_id
                    for ref in state["pending_refs"]:
                        log_reference_check(
                            user_id=user_id,
                            tenant_id=tenant_id,
                            ref_name=ref.get("ref_name", ""),
                            ref_phone=ref.get("ref_phone", ""),
                            ref_email=ref.get("ref_email", ""),
                            ref_type=ref.get("ref_type", "Landlord"),
                            channel=ref.get("channel", "SMS"),
                        )
                    state["pending_refs"].clear()
                    refresh_ref_table()

                    saved_count = 0
                    if not uploaded_files:
                        ui.notify("Warning: No documents were uploaded for this tenant", type="warning")

                    for doc_type, file_data in uploaded_files.items():
                        try:
                            save_uploaded_file(
                                tenant_id=tenant_id,
                                tenant_name=name_input.value,
                                unit=unit_text,
                                filename=file_data["name"],
                                content=file_data["content"],
                                doc_type=doc_type,
                            )
                            saved_count += 1
                        except Exception as e:
                            ui.notify(f"Failed to upload {doc_type}: {str(e)}", type="negative")

                    with result_area:
                        result_area.clear()
                        ui.icon("check_circle", size="48px").style(f"color: {SUCCESS}")
                        ui.label(f"Tenant '{name_input.value}' saved to Unit {unit_text}!").classes(
                            "text-lg font-semibold"
                        )
                        ui.label(f"{saved_count} document(s) uploaded and stored securely.").classes(
                            "text-sm"
                        ).style(f"color: {TEXT_SECONDARY}")

                    ui.notify("Tenant onboarded successfully!", type="positive")
                    uploaded_files.clear()
                    for badge in ready_indicators.values():
                        badge.set_visibility(False)

                with ui.stepper_navigation():
                    ui.button("Back", on_click=stepper.previous, icon="arrow_back").props("flat")
                    ui.button("Save Tenant", on_click=save_tenant, icon="save").props(
                        "unelevated color=positive rounded"
                    )
