"""Intake & Screening page — tenant onboarding with document upload and reference checks."""

from nicegui import ui, events
from app.auth import require_auth
from app.theme import page_layout, section_header, ACCENT, SUCCESS
from app.services.tenant_service import add_tenant
from app.services.document_service import save_uploaded_file
from app.services.notification_service import send_reference_check


@ui.page("/intake")
@require_auth
def intake_page():
    with page_layout(title="Intake & Screening"):
        section_header("New Tenant Intake", "Collect documents and verify references for prospective tenants")

        with ui.stepper().classes("w-full").props("vertical") as stepper:

            # ── Step 1: Basic Info ─────────────────────────────────────────
            with ui.step("Tenant Information", icon="person"):
                ui.label("Enter the prospective tenant's details").classes("text-sm text-gray-500 mb-3")
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    name_input = ui.input(label="Full Name").classes("flex-1 min-w-[250px]").props("outlined")
                    unit_input = ui.input(label="Unit Number").classes("flex-1 min-w-[250px]").props("outlined")
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    rent_input = ui.number(label="Monthly Rent ($)", value=1500, min=100, step=50).classes(
                        "flex-1 min-w-[250px]"
                    ).props("outlined")

                with ui.stepper_navigation():
                    ui.button("Next", on_click=stepper.next, icon="arrow_forward").props("unelevated")

            # ── Step 2: Document Upload ────────────────────────────────────
            with ui.step("Document Collection", icon="upload_file"):
                ui.label("Upload required identification and financial documents").classes(
                    "text-sm text-gray-500 mb-3"
                )

                uploaded_files = {}

                def handle_upload(e: events.UploadEventArguments, doc_type: str):
                    uploaded_files[doc_type] = {
                        "name": e.name,
                        "content": e.content.read(),
                    }
                    ui.notify(f"{doc_type} uploaded successfully", type="positive")

                with ui.column().classes("w-full gap-4"):
                    ui.label("Government ID (PDF/Image)").classes("font-medium text-sm")
                    ui.upload(
                        label="Choose file",
                        on_upload=lambda e: handle_upload(e, "Gov_ID"),
                        auto_upload=True,
                        max_files=1,
                    ).classes("w-full").props('accept=".pdf,.jpg,.png"')

                    ui.label("Direct Deposit Slip").classes("font-medium text-sm")
                    ui.upload(
                        label="Choose file",
                        on_upload=lambda e: handle_upload(e, "Deposit_Slip"),
                        auto_upload=True,
                        max_files=1,
                    ).classes("w-full").props('accept=".pdf,.jpg,.png"')

                    ui.label("6 Months Bank Statements").classes("font-medium text-sm")
                    ui.upload(
                        label="Choose file",
                        on_upload=lambda e: handle_upload(e, "Bank_Statements"),
                        auto_upload=True,
                        max_files=1,
                    ).classes("w-full").props('accept=".pdf"')

                with ui.stepper_navigation():
                    ui.button("Back", on_click=stepper.previous, icon="arrow_back").props("flat")
                    ui.button("Next", on_click=stepper.next, icon="arrow_forward").props("unelevated")

            # ── Step 3: References ─────────────────────────────────────────
            with ui.step("Reference Checks", icon="fact_check"):
                ui.label("Send inquiry to landlord or employer references").classes(
                    "text-sm text-gray-500 mb-3"
                )
                ref_type = ui.radio(
                    ["Landlord", "Employer"], value="Landlord"
                ).props("inline")
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    ref_name = ui.input(label="Reference Name").classes("flex-1 min-w-[200px]").props("outlined")
                    ref_phone = ui.input(label="Reference Phone").classes("flex-1 min-w-[200px]").props("outlined")

                ref_result = ui.label("").classes("text-sm mt-2")
                ref_result.set_visibility(False)

                def send_ref():
                    if not ref_phone.value:
                        ui.notify("Please provide a phone number", type="warning")
                        return
                    success, msg = send_reference_check(
                        tenant_name=name_input.value or "Prospective Tenant",
                        ref_phone=ref_phone.value,
                        ref_name=ref_name.value or "Reference",
                    )
                    ref_result.text = msg
                    ref_result.set_visibility(True)
                    ui.notify(msg, type="positive" if success else "negative")

                ui.button("Send SMS Inquiry", on_click=send_ref, icon="send").props("unelevated")

                with ui.stepper_navigation():
                    ui.button("Back", on_click=stepper.previous, icon="arrow_back").props("flat")
                    ui.button("Next", on_click=stepper.next, icon="arrow_forward").props("unelevated")

            # ── Step 4: Confirm & Save ─────────────────────────────────────
            with ui.step("Confirm & Save", icon="check_circle"):
                ui.label("Review the information and save the tenant record").classes(
                    "text-sm text-gray-500 mb-3"
                )

                result_area = ui.column().classes("w-full gap-2")

                def save_tenant():
                    if not name_input.value or not unit_input.value:
                        ui.notify("Name and Unit are required", type="warning")
                        return

                    # Save tenant to database
                    tenant_id = add_tenant(
                        name=name_input.value,
                        unit=unit_input.value,
                        rent_amount=rent_input.value or 0,
                    )

                    # Save uploaded documents
                    saved_count = 0
                    for doc_type, file_data in uploaded_files.items():
                        save_uploaded_file(
                            tenant_id=tenant_id,
                            tenant_name=name_input.value,
                            unit=unit_input.value,
                            filename=file_data["name"],
                            content=file_data["content"],
                            doc_type=doc_type,
                        )
                        saved_count += 1

                    with result_area:
                        result_area.clear()
                        ui.icon("check_circle", size="48px").style(f"color: {SUCCESS}")
                        ui.label(f"Tenant '{name_input.value}' saved to Unit {unit_input.value}!").classes(
                            "text-lg font-semibold"
                        )
                        ui.label(f"{saved_count} document(s) uploaded and stored securely.").classes(
                            "text-sm text-gray-500"
                        )

                    ui.notify("Tenant onboarded successfully!", type="positive")

                with ui.stepper_navigation():
                    ui.button("Back", on_click=stepper.previous, icon="arrow_back").props("flat")
                    ui.button("Save Tenant", on_click=save_tenant, icon="save").props(
                        "unelevated color=positive"
                    )
