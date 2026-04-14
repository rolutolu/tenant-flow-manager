"""Financial Sync page — banking integration, PAD reconciliation, NSF management, revenue dashboard."""

from nicegui import ui
from app.auth import require_auth
from app.theme import (page_layout, section_header, metric_card,
                        ACCENT, SUCCESS, WARNING, DANGER, TEXT_SECONDARY)
from app.services.tenant_service import get_all_tenants
from app.services.finance_service import (
    update_banking_info, cross_reference_pads, flag_returned_payments,
    get_revenue_summary,
)
from app.services.notification_service import send_nsf_notice


@ui.page("/finance")
@require_auth
def finance_page():
    with page_layout(title="Financial Sync"):
        section_header("Financial Synchronization", "Manage banking, PADs, returns, and revenue tracking")

        with ui.row().classes("w-full gap-6 flex-wrap items-start"):

            # ── Banking Integration ────────────────────────────────────────
            with ui.card().classes("p-6 rounded-xl shadow-sm flex-1 min-w-[350px]").style(
                "border: 1px solid #E2E8F0"
            ):
                with ui.row().classes("items-center gap-2 mb-4"):
                    ui.icon("account_balance", size="24px").style(f"color: {ACCENT}")
                    ui.label("Banking Integration").classes("text-lg font-semibold")
                ui.label("Add or update encrypted banking info for PAD scheduling").classes(
                    "text-sm mb-3"
                ).style(f"color: {TEXT_SECONDARY}")

                tenants = get_all_tenants()
                tenant_options = {t["id"]: f"{t['unit']} - {t['name']}" for t in tenants}
                selected_tenant = ui.select(
                    label="Select Tenant",
                    options=tenant_options
                ).classes("w-full").props("outlined")

                bank_input = ui.input(
                    label="Bank Account / Transit Number",
                    password=True,
                    password_toggle_button=True,
                ).classes("w-full").props("outlined")

                bank_result = ui.label("").classes("text-sm mt-1")
                bank_result.set_visibility(False)

                def save_bank():
                    if not selected_tenant.value or not bank_input.value:
                        ui.notify("Select a tenant and enter bank info", type="warning")
                        return
                    success, msg = update_banking_info(selected_tenant.value, bank_input.value)
                    bank_result.text = msg
                    bank_result.set_visibility(True)
                    ui.notify(msg, type="positive" if success else "negative")

                ui.button("Encrypt & Save to PAD System", on_click=save_bank, icon="lock").classes(
                    "w-full mt-2"
                ).props("unelevated")

            # ── Monthly Reconciliation ─────────────────────────────────────
            with ui.card().classes("p-6 rounded-xl shadow-sm flex-1 min-w-[350px]").style(
                "border: 1px solid #E2E8F0"
            ):
                with ui.row().classes("items-center gap-2 mb-4"):
                    ui.icon("compare_arrows", size="24px").style(f"color: {ACCENT}")
                    ui.label("Monthly Reconciliation").classes("text-lg font-semibold")
                ui.label("Cross-reference rent roll against scheduled PADs before the 1st").classes(
                    "text-sm mb-3"
                ).style(f"color: {TEXT_SECONDARY}")

                recon_result = ui.column().classes("w-full gap-2")

                def run_reconciliation():
                    recon_result.clear()
                    success, msg, discrepancies = cross_reference_pads()
                    with recon_result:
                        if success:
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("check_circle", size="20px").style(f"color: {SUCCESS}")
                                ui.label(msg).classes("text-sm font-medium").style(f"color: {SUCCESS}")
                        else:
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("warning", size="20px").style(f"color: {WARNING}")
                                ui.label(msg).classes("text-sm font-medium").style(f"color: {WARNING}")
                            for d in discrepancies:
                                ui.label(f"  {d['unit']} - {d['tenant']}: {d['issue']}").classes(
                                    "text-sm ml-6"
                                )

                ui.button("Run Cross-Reference Check", on_click=run_reconciliation,
                          icon="sync").classes("w-full").props("unelevated")

        # ── Returns Management ─────────────────────────────────────────────
        with ui.card().classes("w-full p-6 rounded-xl shadow-sm").style(
            "border: 1px solid #E2E8F0"
        ):
            with ui.row().classes("items-center gap-2 mb-4"):
                ui.icon("report_problem", size="24px").style(f"color: {DANGER}")
                ui.label("Returns Management (NSF/ISF)").classes("text-lg font-semibold")
            ui.label(
                "Flag returned payments and send 48-hour e-transfer notices"
            ).classes("text-sm mb-3").style(f"color: {TEXT_SECONDARY}")

            nsf_container = ui.column().classes("w-full gap-3")

            def check_returns():
                nsf_container.clear()
                cases, msg = flag_returned_payments()
                with nsf_container:
                    if cases:
                        ui.label(msg).classes("text-sm font-medium").style(f"color: {WARNING}")
                        for case in cases:
                            with ui.card().classes("p-4 rounded-lg w-full").style(
                                "border: 1px solid #FED7AA; background: #FFFBEB"
                            ):
                                with ui.row().classes("items-center justify-between w-full"):
                                    with ui.column().classes("gap-0"):
                                        ui.label(
                                            f"{case.get('tenant_name', 'Unknown')} — {case.get('unit', 'N/A')}"
                                        ).classes("font-semibold")
                                        ui.label(
                                            f"Amount: ${case.get('amount', 0):,.2f}"
                                        ).classes("text-sm text-gray-600")
                                    ui.button(
                                        "Send 48h Notice",
                                        on_click=lambda _, c=case: _send_notice(c),
                                        icon="email",
                                    ).props("unelevated color=warning size=sm")
                    else:
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("check_circle", size="20px").style(f"color: {SUCCESS}")
                            ui.label("No returned payments found.").classes("text-sm").style(
                                f"color: {SUCCESS}"
                            )

            ui.button("Check for Returns", on_click=check_returns, icon="search").props("unelevated")

        # ── Revenue Dashboard ──────────────────────────────────────────────
        with ui.card().classes("w-full p-6 rounded-xl shadow-sm").style(
            "border: 1px solid #E2E8F0"
        ):
            with ui.row().classes("items-center gap-2 mb-4"):
                ui.icon("bar_chart", size="24px").style(f"color: {ACCENT}")
                ui.label("Revenue Dashboard").classes("text-lg font-semibold")

            revenue = get_revenue_summary()
            with ui.row().classes("w-full gap-4 flex-wrap"):
                metric_card("PAD Revenue", f"${revenue['PAD']:,.0f}", "account_balance", ACCENT)
                metric_card("E-Transfer Revenue", f"${revenue['E-Transfer']:,.0f}", "send_to_mobile", SUCCESS)
                metric_card("Total Revenue", f"${revenue['total']:,.0f}", "payments", "#8B5CF6")


def _send_notice(case: dict):
    """Send a 48-hour notice for a specific NSF case."""
    success, msg = send_nsf_notice(
        tenant_name=case.get("tenant_name", "Tenant"),
        unit=case.get("unit", "N/A"),
        amount=case.get("amount", 0),
    )
    ui.notify(msg, type="positive" if success else "negative")
