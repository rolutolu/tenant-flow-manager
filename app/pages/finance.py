"""Finance Dashboard for managing ledgers, transactions, and accountant exports."""
from nicegui import ui
import pandas as pd
from datetime import datetime
from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, ACCENT, SUCCESS, WARNING, CARD_BG, BORDER
from app.services.finance_service import get_transactions, get_financial_summary, add_transaction, create_checkout_session

@ui.page("/finance")
@require_role("admin", "manager")
def finance_page():
    user_id = get_user_id()
    
    with page_layout(title="Financials & Ledger"):
        section_header("Financial Dashboard", "Track rent payments, late fees, and export accountant-ready reports")
        
        # ── KPI Cards ────────────────────────────────────────────────────────
        summary = get_financial_summary(user_id)
        with ui.row().classes("w-full gap-6 mb-6 flex-wrap"):
            with ui.card().classes("flex-1 p-6 items-center text-center shadow-sm").style(f"background: {CARD_BG}; border: 1px solid {BORDER}"):
                ui.icon("account_balance", size="32px", color="positive")
                ui.label("Total Income").classes("text-sm text-slate-500 mt-2")
                ui.label(f"${summary['total_income']:,.2f}").classes("text-2xl font-bold text-slate-800")
                
            with ui.card().classes("flex-1 p-6 items-center text-center shadow-sm").style(f"background: {CARD_BG}; border: 1px solid {BORDER}"):
                ui.icon("receipt_long", size="32px", color="warning")
                ui.label("Outstanding Charges").classes("text-sm text-slate-500 mt-2")
                ui.label(f"${summary['outstanding_charges']:,.2f}").classes("text-2xl font-bold text-slate-800")

        # ── Action Bar ───────────────────────────────────────────────────────
        with ui.row().classes("w-full gap-4 mb-4 justify-between items-center"):
            with ui.row().classes("gap-2"):
                ui.button("Add Manual Transaction", icon="add", on_click=lambda: add_tx_dialog.open()).props("outline")
                ui.button("Process Stripe Payment", icon="payment", on_click=lambda: ui.navigate.to(create_checkout_session(1500, "Rent Payment", "", ""))).props("outline color=secondary")
            
            with ui.row().classes("gap-2"):
                ui.button("Scan Bank Emails (AI)", icon="smart_toy", on_click=lambda: ui.notify("AI Scraper Simulation: Found 2 new E-Transfers. Adding to ledger...", type="info")).props("unelevated color=indigo")
                
                def export_csv():
                    txns = get_transactions(user_id)
                    df = pd.DataFrame(txns)
                    # Bug fix #9: Guard against empty dataframe before accessing columns
                    if not df.empty and "tenants" in df.columns and "units" in df.columns:
                        df["Tenant"] = df["tenants"].apply(lambda x: x.get("name") if isinstance(x, dict) else "")
                        df["Unit"] = df["units"].apply(lambda x: x.get("unit_number") if isinstance(x, dict) else "")
                        df = df.drop(columns=["tenants", "units"], errors="ignore")
                    
                    csv_data = df.to_csv(index=False)
                    ui.download(csv_data.encode("utf-8"), f"financials_{datetime.now().strftime('%Y%m%d')}.csv")

                ui.button("Export to CSV", icon="download", on_click=export_csv).props("unelevated color=primary")

        # ── Add Transaction Modal ────────────────────────────────────────────
        with ui.dialog() as add_tx_dialog, ui.card().classes("p-6 w-96"):
            ui.label("New Transaction").classes("text-xl font-bold mb-4")
            tx_type = ui.select(label="Type", options=["Charge", "Payment"], value="Charge").classes("w-full mb-2").props("outlined")
            tx_cat = ui.select(label="Category", options=["Rent", "Late Fee", "Maintenance", "Deposit", "Other"], value="Rent").classes("w-full mb-2").props("outlined")
            tx_amt = ui.number(label="Amount ($)", value=0).classes("w-full mb-4").props("outlined")
            
            def save_tx():
                if add_transaction(user_id, tx_type.value, tx_cat.value, tx_amt.value):
                    ui.notify("Transaction saved", type="positive")
                    add_tx_dialog.close()
                    ui.navigate.to("/finance")
            
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=add_tx_dialog.close).props("flat")
                ui.button("Save", on_click=save_tx).props("unelevated color=primary")

        # ── Ledger Table ─────────────────────────────────────────────────────
        transactions = get_transactions(user_id)
        if not transactions:
            ui.label("No transactions found.").classes("text-slate-500 italic mt-4")
        else:
            # Bug fix #5: Flatten nested dicts from Supabase join before passing to ui.table
            flat_transactions = []
            for t in transactions:
                flat = dict(t)
                flat["tenant_name"] = (t.get("tenants") or {}).get("name", "N/A")
                flat["unit_label"] = (t.get("units") or {}).get("unit_number", "N/A")
                flat_transactions.append(flat)

            columns = [
                {'name': 'date', 'label': 'Date', 'field': 'date', 'sortable': True, 'align': 'left'},
                {'name': 'type', 'label': 'Type', 'field': 'type', 'sortable': True, 'align': 'left'},
                {'name': 'category', 'label': 'Category', 'field': 'category', 'align': 'left'},
                {'name': 'tenant', 'label': 'Tenant', 'field': 'tenant_name', 'align': 'left'},
                {'name': 'unit', 'label': 'Unit', 'field': 'unit_label', 'align': 'left'},
                {'name': 'amount', 'label': 'Amount', 'field': 'amount', 'sortable': True, 'align': 'right'},
                {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'}
            ]

            ui.table(columns=columns, rows=flat_transactions, row_key='id').classes('w-full shadow-sm').style(f"border: 1px solid {BORDER}")
