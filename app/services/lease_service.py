"""Lease PDF generation and rent increase notice handling."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from fpdf import FPDF
from app.config import DOCS_DIR
from app.services.document_service import get_tenant_folder, sanitize_name
from app.models.database import get_connection


def generate_lease_pdf(tenant_name: str, unit: str, rent_amount: float,
                       start_date: str, end_date: str) -> str:
    """Generate a PDF lease agreement and return the file path."""
    folder = get_tenant_folder(tenant_name, unit)

    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 12, txt="RESIDENTIAL LEASE AGREEMENT", ln=True, align="C")
    pdf.ln(8)

    # Date line
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, txt=f"Date: {datetime.now().strftime('%B %d, %Y')}", ln=True)
    pdf.ln(4)

    # Body
    pdf.set_font("Arial", size=12)
    body = (
        f"This Lease Agreement is entered into between the Landlord and "
        f"{tenant_name} (hereinafter referred to as the 'Tenant').\n\n"
        f"1. PROPERTY: The Landlord agrees to rent the premises located at "
        f"Unit {unit} to the Tenant.\n\n"
        f"2. TERM: The lease shall commence on {start_date} and terminate on "
        f"{end_date}.\n\n"
        f"3. RENT: The Tenant agrees to pay a monthly rent of ${rent_amount:,.2f}, "
        f"due on the 1st of each month via Pre-Authorized Debit (PAD).\n\n"
        f"4. PAYMENT FREQUENCY: Monthly.\n\n"
        f"5. LATE FEES: Any returned payments (NSF/ISF) will incur an additional "
        f"administrative charge. The tenant will be required to submit an "
        f"e-transfer within 48 hours of notification.\n"
    )
    pdf.multi_cell(0, 8, txt=body)

    # Signature lines
    pdf.ln(20)
    pdf.cell(90, 8, txt="_______________________", ln=False)
    pdf.cell(20, 8, txt="", ln=False)
    pdf.cell(90, 8, txt="_______________________", ln=True)
    pdf.cell(90, 8, txt="Landlord Signature", ln=False)
    pdf.cell(20, 8, txt="", ln=False)
    pdf.cell(90, 8, txt="Tenant Signature", ln=True)

    pdf.ln(10)
    pdf.cell(90, 8, txt="Date: _________________", ln=False)
    pdf.cell(20, 8, txt="", ln=False)
    pdf.cell(90, 8, txt="Date: _________________", ln=True)

    filepath = folder / "Lease_Agreement.pdf"
    pdf.output(str(filepath))
    return str(filepath)


def generate_rent_increase_notice(tenant_name: str, unit: str,
                                  current_rent: float, new_rent: float,
                                  effective_date: str) -> str:
    """Generate a rent increase notice PDF and return the file path."""
    folder = get_tenant_folder(tenant_name, unit)

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, txt="NOTICE OF RENT INCREASE", ln=True, align="C")
    pdf.ln(8)

    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, txt=f"Date: {datetime.now().strftime('%B %d, %Y')}", ln=True)
    pdf.ln(4)

    pdf.set_font("Arial", size=12)
    body = (
        f"Dear {tenant_name},\n\n"
        f"Please be advised that effective {effective_date}, the monthly rent for "
        f"Unit {unit} will be adjusted from ${current_rent:,.2f} to ${new_rent:,.2f}.\n\n"
        f"This notice is being provided in accordance with the required 90-day "
        f"notice period.\n\n"
        f"Please sign below to acknowledge receipt of this notice. A signed copy "
        f"will be provided to you via email for your records.\n"
    )
    pdf.multi_cell(0, 8, txt=body)

    pdf.ln(20)
    pdf.cell(90, 8, txt="_______________________", ln=False)
    pdf.cell(20, 8, txt="", ln=False)
    pdf.cell(90, 8, txt="_______________________", ln=True)
    pdf.cell(90, 8, txt="Tenant Signature", ln=False)
    pdf.cell(20, 8, txt="", ln=False)
    pdf.cell(90, 8, txt="Date", ln=True)

    filepath = folder / "Rent_Increase_Notice.pdf"
    pdf.output(str(filepath))
    return str(filepath)


def get_expiring_leases(days: int = 90) -> list[dict]:
    """Return tenants whose leases expire within the given number of days."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM tenants WHERE lease_end IS NOT NULL AND lease_end != ''").fetchall()
        today = datetime.now()
        results = []
        for row in rows:
            d = dict(row)
            try:
                end_date = datetime.strptime(d["lease_end"].split(" ")[0], "%Y-%m-%d")
                days_left = (end_date - today).days
                if 0 < days_left <= days:
                    d["days_left"] = days_left
                    results.append(d)
            except (ValueError, AttributeError):
                continue
        return sorted(results, key=lambda x: x["days_left"])
    finally:
        conn.close()
