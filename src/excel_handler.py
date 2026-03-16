import pandas as pd
import os
from datetime import datetime

DATA_FILE = "data/tenants.xlsx"

def append_bank_info(tenant_name, unit, bank_account):
    """
    Placeholder: Appends new tenant banking info for PADs.
    In real life, this might call a banking API or just update the Excel.
    """
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_excel(DATA_FILE)
            # Find the row and update
            mask = (df['Tenant_Name'] == tenant_name) & (df['Unit'] == unit)
            if mask.any():
                df.loc[mask, 'Banking_Set_Up'] = 'Yes'
                df.to_excel(DATA_FILE, index=False)
                return True, f"Banking info appended for {tenant_name}."
            return False, "Tenant not found in records."
        except Exception as e:
            return False, str(e)
    return False, "Database not found."

def cross_reference_rent(monthly_report_file):
    """
    Placeholder: Compares rent spreadsheet vs banking system.
    Takes a mocked monthly report file path and compares it.
    """
    # Fake logic for simulation
    return True, "Cross-reference complete. All Scheduled PADs match the master spreadsheet."

def flag_returned_payments():
    """
    Placeholder: Flags NSF payments and triggers notifications.
    """
    # Fake logic for simulation
    nsf_cases = [{"Tenant": "Jane Doe", "Unit": "Unit_102", "Amount": 1600}]
    return nsf_cases, "NSF Check complete."
