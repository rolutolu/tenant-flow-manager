"""Reusable tenant edit dialog for lease and actions pages."""

from nicegui import ui
from app.services.tenant_service import update_tenant


def open_tenant_edit_dialog(tenant: dict, on_saved=None):
    """Open a dialog to edit tenant fields."""
    with ui.dialog() as dialog, ui.card().classes("p-6 w-[480px] max-w-full"):
        ui.label(f"Edit Tenant — {tenant.get('name', '')}").classes("text-xl font-bold mb-4")

        email_input = ui.input(label="Email", value=tenant.get("email") or "").classes("w-full mb-2").props("outlined")
        rent_input = ui.number(label="Rent ($)", value=tenant.get("rent_amount") or 0, min=0, step=25).classes("w-full mb-2").props("outlined")
        lease_start = ui.input(label="Lease Start (YYYY-MM-DD)", value=tenant.get("lease_start") or "").classes("w-full mb-2").props("outlined")
        lease_end = ui.input(label="Lease End (YYYY-MM-DD)", value=tenant.get("lease_end") or "").classes("w-full mb-2").props("outlined")
        lease_signed = ui.select(label="Lease Signed", options=["No", "Yes"], value=tenant.get("lease_signed") or "No").classes("w-full mb-2").props("outlined")
        banking_set_up = ui.select(label="Banking Set Up", options=["No", "Yes"], value=tenant.get("banking_set_up") or "No").classes("w-full mb-2").props("outlined")
        move_in_status = ui.select(
            label="Move-In Status",
            options=["Pending", "In Progress", "Complete"],
            value=tenant.get("move_in_status") or "Pending",
        ).classes("w-full mb-2").props("outlined")
        bank_info = ui.textarea(label="Bank Info", value=tenant.get("bank_info") or "").classes("w-full mb-4").props("outlined")

        def save():
            ok = update_tenant(
                tenant["id"],
                email=email_input.value or "",
                rent_amount=rent_input.value or 0,
                lease_start=lease_start.value or "",
                lease_end=lease_end.value or "",
                lease_signed=lease_signed.value,
                banking_set_up=banking_set_up.value,
                move_in_status=move_in_status.value,
                bank_info=bank_info.value or "",
            )
            if ok:
                ui.notify("Tenant updated", type="positive")
                dialog.close()
                if on_saved:
                    on_saved()
            else:
                ui.notify("Failed to update tenant", type="negative")

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Save", on_click=save, icon="save").props("unelevated color=primary")

    dialog.open()
