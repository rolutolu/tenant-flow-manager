"""Finance Dashboard for managing ledgers, transactions, and accountant exports."""

import io
from datetime import datetime

import pandas as pd
from nicegui import ui

from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, CARD_BG, BORDER
from app.services.finance_service import (
    get_transactions, get_financial_summary, add_transaction, update_transaction_status,
)
from app.services.tenant_service import get_all_tenants
from app.services.notification_service import send_nsf_notice


@ui.page("/finance")
@require_role("admin", "manager")
def finance_page():
    user_id = get_user_id()
    tenants = get_all_tenants(user_id)
    tenant_options = {
        t["id"]: f"{t['name']} (Unit {t['unit']})" for t in tenants
    }

    with page_layout(title="Financials & Ledger"):
        section_header("Financial Dashboard", "Track rent payments, late fees, and export accountant-ready reports")

        summary = get_financial_summary(user_id)
        with ui.row().classes("w-full gap-6 mb-6 flex-wrap"):
            with ui.card().classes("flex-1 p-6 items-center text-center shadow-sm").style(
                f"background: {CARD_BG}; border: 1px solid {BORDER}"
            ):
                ui.icon("account_balance", size="32px", color="positive")
                ui.label("Total Income").classes("text-sm text-slate-500 mt-2")
                ui.label(f"${summary['total_income']:,.2f}").classes("text-2xl font-bold text-slate-800")

            with ui.card().classes("flex-1 p-6 items-center text-center shadow-sm").style(
                f"background: {CARD_BG}; border: 1px solid {BORDER}"
            ):
                ui.icon("receipt_long", size="32px", color="warning")
                ui.label("Outstanding Charges").classes("text-sm text-slate-500 mt-2")
                ui.label(f"${summary['outstanding_charges']:,.2f}").classes("text-2xl font-bold text-slate-800")

        with ui.row().classes("w-full gap-4 mb-4 justify-between items-center flex-wrap"):
            with ui.row().classes("gap-2 flex-wrap"):
                ui.button("Add Manual Transaction", icon="add", on_click=lambda: add_tx_dialog.open()).props("outline")
                ui.button("NSF Notice", icon="warning", on_click=lambda: nsf_dialog.open()).props("outline color=warning")

            with ui.row().classes("gap-2 flex-wrap"):
                ui.button(
                    "Scan Bank Emails (Demo)",
                    icon="smart_toy",
                    on_click=lambda: ui.notify(
                        "Demo only: configure email/AI integration to auto-import E-Transfers.",
                        type="info",
                    ),
                ).props("unelevated color=indigo")

                def _flatten_transactions():
                    txns = get_transactions(user_id)
                    flat = []
                    for t in txns:
                        row = dict(t)
                        row["tenant_name"] = (t.get("tenants") or {}).get("name", "N/A")
                        row["unit_label"] = (t.get("units") or {}).get("unit_number", "N/A")
                        flat.append(row)
                    return flat, txns

                def export_csv():
                    flat, _ = _flatten_transactions()
                    df = pd.DataFrame(flat)
                    if not df.empty:
                        df = df.drop(columns=["tenants", "units"], errors="ignore")
                    csv_data = df.to_csv(index=False)
                    ui.download(csv_data.encode("utf-8"), f"financials_{datetime.now().strftime('%Y%m%d')}.csv")

                def export_excel():
                    flat, _ = _flatten_transactions()
                    df = pd.DataFrame(flat)
                    if not df.empty:
                        df = df.drop(columns=["tenants", "units"], errors="ignore")
                    buffer = io.BytesIO()
                    df.to_excel(buffer, index=False, engine="openpyxl")
                    ui.download(
                        buffer.getvalue(),
                        f"financials_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    )

                ui.button("Export CSV", icon="download", on_click=export_csv).props("outline")
                ui.button("Export Excel", icon="table_view", on_click=export_excel).props("unelevated color=primary")

        with ui.dialog() as add_tx_dialog, ui.card().classes("p-6 w-96"):
            ui.label("New Transaction").classes("text-xl font-bold mb-4")
            tx_type = ui.select(label="Type", options=["Charge", "Payment"], value="Charge").classes("w-full mb-2").props("outlined")
            tx_cat = ui.select(
                label="Category",
                options=["Rent", "Late Fee", "Maintenance", "Deposit", "Other"],
                value="Rent",
            ).classes("w-full mb-2").props("outlined")
            tx_amt = ui.number(label="Amount ($)", value=0).classes("w-full mb-4").props("outlined")

            def save_tx():
                if add_transaction(user_id, tx_type.value, tx_cat.value, tx_amt.value):
                    ui.notify("Transaction saved", type="positive")
                    add_tx_dialog.close()
                    ui.navigate.to("/finance")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=add_tx_dialog.close).props("flat")
                ui.button("Save", on_click=save_tx).props("unelevated color=primary")

        with ui.dialog() as nsf_dialog, ui.card().classes("p-6 w-96"):
            ui.label("NSF / Returned Payment").classes("text-xl font-bold mb-4")
            nsf_tenant = ui.select(label="Tenant", options=tenant_options).classes("w-full mb-2").props("outlined")
            nsf_amount = ui.number(label="Returned Amount ($)", value=0, min=0).classes("w-full mb-2").props("outlined")
            nsf_penalty = ui.number(label="Admin Fee ($)", value=25, min=0).classes("w-full mb-4").props("outlined")

            def process_nsf():
                if not nsf_tenant.value:
                    return ui.notify("Select a tenant", type="warning")
                tenant = next((t for t in tenants if t["id"] == nsf_tenant.value), None)
                if not tenant:
                    return ui.notify("Tenant not found", type="negative")
                amount = nsf_amount.value or 0
                penalty = nsf_penalty.value or 25
                add_transaction(
                    user_id, "Charge", "Late Fee", penalty,
                    tenant_id=tenant["id"], notes="NSF administrative fee", status="Pending",
                )
                add_transaction(
                    user_id, "Charge", "Rent", amount,
                    tenant_id=tenant["id"], status="Pending", notes="NSF returned payment",
                )
                success, msg = send_nsf_notice(
                    tenant["name"],
                    tenant["unit"],
                    amount,
                    penalty,
                    email=tenant.get("email") or "",
                    user_id=user_id,
                )
                ui.notify(msg, type="positive" if success else "negative")
                nsf_dialog.close()
                ui.navigate.to("/finance")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=nsf_dialog.close).props("flat")
                ui.button("Send Notice & Charge", on_click=process_nsf).props("unelevated color=warning")

        transactions = get_transactions(user_id)
        if not transactions:
            ui.label("No transactions found.").classes("text-slate-500 italic mt-4")
        else:
            flat_transactions = []
            for t in transactions:
                flat = dict(t)
                flat["tenant_name"] = (t.get("tenants") or {}).get("name", "N/A")
                flat["unit_label"] = (t.get("units") or {}).get("unit_number", "N/A")
                flat_transactions.append(flat)

            columns = [
                {"name": "date", "label": "Date", "field": "date", "sortable": True, "align": "left"},
                {"name": "type", "label": "Type", "field": "type", "sortable": True, "align": "left"},
                {"name": "category", "label": "Category", "field": "category", "align": "left"},
                {"name": "tenant", "label": "Tenant", "field": "tenant_name", "align": "left"},
                {"name": "unit", "label": "Unit", "field": "unit_label", "align": "left"},
                {"name": "amount", "label": "Amount", "field": "amount", "sortable": True, "align": "right"},
                {"name": "status", "label": "Status", "field": "status", "align": "center"},
                {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
            ]

            def set_status(e):
                row = e.args
                new_status = row.get("new_status")
                if not new_status:
                    return
                if update_transaction_status(row["id"], new_status):
                    ui.notify(f"Status set to {new_status}", type="positive")
                    ui.navigate.to("/finance")

            tbl = ui.table(columns=columns, rows=flat_transactions, row_key="id").classes("w-full shadow-sm").style(
                f"border: 1px solid {BORDER}"
            )
            tbl.add_slot("body-cell-actions", """
                <q-td :props="props">
                    <q-btn flat dense size="sm" label="Pending" color="warning"
                           @click="$parent.$emit('set_status', {...props.row, new_status: 'Pending'})" />
                    <q-btn flat dense size="sm" label="Cleared" color="positive"
                           @click="$parent.$emit('set_status', {...props.row, new_status: 'Cleared'})" />
                    <q-btn flat dense size="sm" label="Failed" color="negative"
                           @click="$parent.$emit('set_status', {...props.row, new_status: 'Failed'})" />
                </q-td>
            """)
            tbl.on("set_status", set_status)
