"""Intake & Screening page — tenant onboarding with document upload and reference checks."""

from nicegui import ui, events
from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, ACCENT, SUCCESS, CARD_BG, BORDER, TEXT_SECONDARY
from app.services.tenant_service import add_tenant
from app.services.document_service import save_uploaded_file
from app.services.notification_service import send_reference_check, send_reference_email


@ui.page("/intake")
@require_role("admin", "manager")
def intake_page():
    user_id = get_user_id()

    with page_layout(title="Intake & Screening"):
        section_header("New Tenant Intake", "Collect documents and verify references for prospective tenants")

        with ui.stepper().classes("w-full").props("vertical") as stepper:

            # ── Step 1: Basic Info ─────────────────────────────────────────
            with ui.step("Tenant Information", icon="person"):
                ui.label("Enter the prospective tenant's details").classes("text-sm mb-3").style(
                    f"color: {TEXT_SECONDARY}"
                )
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    name_input = ui.input(label="Full Name").classes("flex-1 min-w-[250px]").props("outlined")
                    unit_input = ui.input(label="Unit Number").classes("flex-1 min-w-[250px]").props("outlined")
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    unit_address_input = ui.input(label="Unit Address").classes("flex-1 min-w-[250px]").props("outlined")
                    rent_input = ui.number(label="Monthly Rent ($)", value=1500, min=100, step=50).classes(
                        "flex-1 min-w-[250px]"
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
                        # NiceGUI v2.0+ wraps the file inside the `e.file` attribute
                        file_obj = getattr(e, 'file', None) or e  # Fallback for different NiceGUI versions
                        
                        content = file_obj.read() if hasattr(file_obj, 'read') else file_obj.content.read()
                        file_name = getattr(file_obj, 'name', getattr(file_obj, 'filename', 'document'))
                        
                        uploaded_files[doc_type] = {
                            "name": file_name,
                            "content": content,
                        }
                        if doc_type in ready_indicators:
                            ready_indicators[doc_type].set_visibility(True)
                        ui.notify(f"{doc_type} is ready to save!", type="positive")
                    except Exception as err:
                        ui.notify(f"Failed to read file: {str(err)}", type="negative")

                def handle_reject(e):
                    ui.notify("File rejected! Check file type (.pdf, .jpg, .png) and size (Max 20MB).", type="negative")

                with ui.column().classes("w-full gap-4"):
                    with ui.row().classes("items-center gap-2"):
                        ui.label("Government ID (PDF/Image)").classes("font-medium text-sm")
                        ready_indicators["Gov_ID"] = ui.badge("Ready", color="positive").props("rounded").classes("text-[10px]")
                        ready_indicators["Gov_ID"].set_visibility(False)
                    ui.upload(
                        label="Choose file",
                        on_upload=lambda e, dt="Gov_ID": handle_upload(e, dt),
                        on_rejected=handle_reject,
                        auto_upload=True,
                        max_files=1,
                        max_file_size=20_000_000,
                    ).classes("w-full").props('accept=".pdf,.jpg,.png,image/*"')

                    with ui.row().classes("items-center gap-2"):
                        ui.label("Direct Deposit Slip").classes("font-medium text-sm")
                        ready_indicators["Deposit_Slip"] = ui.badge("Ready", color="positive").props("rounded").classes("text-[10px]")
                        ready_indicators["Deposit_Slip"].set_visibility(False)
                    ui.upload(
                        label="Choose file",
                        on_upload=lambda e, dt="Deposit_Slip": handle_upload(e, dt),
                        on_rejected=handle_reject,
                        auto_upload=True,
                        max_files=1,
                        max_file_size=20_000_000,
                    ).classes("w-full").props('accept=".pdf,.jpg,.png,image/*"')

                    with ui.row().classes("items-center gap-2"):
                        ui.label("6 Months Bank Statements").classes("font-medium text-sm")
                        ready_indicators["Bank_Statements"] = ui.badge("Ready", color="positive").props("rounded").classes("text-[10px]")
                        ready_indicators["Bank_Statements"].set_visibility(False)
                    ui.upload(
                        label="Choose file",
                        on_upload=lambda e, dt="Bank_Statements": handle_upload(e, dt),
                        on_rejected=handle_reject,
                        auto_upload=True,
                        max_files=1,
                        max_file_size=20_000_000,
                    ).classes("w-full").props('accept=".pdf"')

                with ui.stepper_navigation():
                    ui.button("Back", on_click=stepper.previous, icon="arrow_back").props("flat")
                    ui.button("Next", on_click=stepper.next, icon="arrow_forward").props("unelevated rounded")

            # ── Step 3: References ─────────────────────────────────────────
            with ui.step("Reference Checks", icon="fact_check"):
                ui.label("Send inquiry to landlord or employer references").classes(
                    "text-sm mb-3"
                ).style(f"color: {TEXT_SECONDARY}")
                
                ui.label("*Note: Email integration is currently simulated and not fully implemented.*").classes(
                    "text-xs italic mb-4"
                ).style("color: #f59e0b;") # Orange warning color

                ref_type = ui.radio(
                    ["Landlord", "Employer"], value="Landlord"
                ).props("inline")
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    ref_name = ui.input(label="Reference Name").classes("flex-1 min-w-[150px]").props("outlined")
                    ref_phone = ui.input(label="Reference Phone").classes("flex-1 min-w-[150px]").props("outlined")
                    ref_email = ui.input(label="Reference Email").classes("flex-1 min-w-[150px]").props("outlined")

                ref_result = ui.label("").classes("text-sm mt-2")
                ref_result.set_visibility(False)

                def send_ref_sms():
                    if not ref_phone.value:
                        ui.notify("Please provide a phone number for SMS", type="warning")
                        return
                    success, msg = send_reference_check(
                        tenant_name=name_input.value or "Prospective Tenant",
                        ref_phone=ref_phone.value,
                        ref_name=ref_name.value or "Reference",
                    )
                    ref_result.text = msg
                    ref_result.set_visibility(True)
                    ui.notify(msg, type="positive" if success else "negative")

                def send_ref_email():
                    if not ref_email.value:
                        ui.notify("Please provide an email address", type="warning")
                        return
                    success, msg = send_reference_email(
                        tenant_name=name_input.value or "Prospective Tenant",
                        ref_email=ref_email.value,
                        ref_name=ref_name.value or "Reference",
                    )
                    ref_result.text = msg
                    ref_result.set_visibility(True)
                    ui.notify(msg, type="positive" if success else "negative")

                with ui.row().classes("gap-3 mt-2"):
                    ui.button("Send SMS", on_click=send_ref_sms, icon="sms").props("unelevated rounded")
                    ui.button("Send Email", on_click=send_ref_email, icon="email").props("outline rounded")

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
                    if not name_input.value or not unit_input.value:
                        ui.notify("Name and Unit are required", type="warning")
                        return

                    # Save tenant to database with user_id
                    tenant_id = add_tenant(
                        user_id=user_id,
                        name=name_input.value,
                        unit=unit_input.value,
                        unit_address=unit_address_input.value,
                        rent_amount=rent_input.value or 0,
                    )

                    # Save uploaded documents
                    saved_count = 0
                    if not uploaded_files:
                        ui.notify("Warning: No documents were uploaded for this tenant", type="warning")
                    
                    for doc_type, file_data in uploaded_files.items():
                        try:
                            save_uploaded_file(
                                tenant_id=tenant_id,
                                tenant_name=name_input.value,
                                unit=unit_input.value,
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
                        ui.label(f"Tenant '{name_input.value}' saved to Unit {unit_input.value}!").classes(
                            "text-lg font-semibold"
                        )
                        ui.label(f"{saved_count} document(s) uploaded and stored securely.").classes(
                            "text-sm"
                        ).style(f"color: {TEXT_SECONDARY}")

                    ui.notify("Tenant onboarded successfully!", type="positive")

                with ui.stepper_navigation():
                    ui.button("Back", on_click=stepper.previous, icon="arrow_back").props("flat")
                    ui.button("Save Tenant", on_click=save_tenant, icon="save").props(
                        "unelevated color=positive rounded"
                    )
