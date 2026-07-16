"""Lease PDF generation and rent increase notice handling."""

from datetime import datetime
import io
from fpdf import FPDF
from app.services.document_service import save_uploaded_file
from app.models.database import get_client


def generate_lease_pdf(tenant_name: str, unit: str, rent_amount: float,
                       start_date: str, end_date: str, property_name: str = "",
                       tenant_id: int = None) -> str:
    """Generate a PDF lease agreement and return the cloud path."""
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
    prop_str = f"Unit {unit} in Property: {property_name}" if property_name else f"Unit {unit}"
    body = (
        f"This Lease Agreement is entered into between the Landlord and "
        f"{tenant_name} (hereinafter referred to as the 'Tenant').\n\n"
        f"1. PROPERTY: The Landlord agrees to rent the premises located at "
        f"{prop_str} to the Tenant.\n\n"
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

    # Generate PDF in memory
    pdf_output = pdf.output(dest='S')
    content = pdf_output if isinstance(pdf_output, bytes) else pdf_output.encode('latin-1')

    # Get tenant ID — use provided ID or fall back to name+unit lookup
    if not tenant_id:
        client = get_client()
        tenant_resp = client.table("tenants").select("id").eq("name", tenant_name).eq("unit", unit).execute()
        if not tenant_resp.data:
            raise Exception(f"Tenant '{tenant_name}' at Unit '{unit}' not found.")
        tenant_id = tenant_resp.data[0]['id']

    # Upload to Supabase Storage
    cloud_path = save_uploaded_file(
        tenant_id=tenant_id,
        tenant_name=tenant_name,
        unit=unit,
        filename="Lease_Agreement.pdf",
        content=content,
        doc_type="Lease"
    )

    return cloud_path


def generate_rent_increase_notice(tenant_name: str, unit: str,
                                  current_rent: float, new_rent: float,
                                  effective_date: str, tenant_id: int = None) -> str:
    """Generate a rent increase notice PDF and return the cloud path."""
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

    # Generate PDF in memory
    pdf_output = pdf.output(dest='S')
    content = pdf_output if isinstance(pdf_output, bytes) else pdf_output.encode('latin-1')

    # Get tenant ID — use provided ID or fall back to name+unit lookup
    if not tenant_id:
        client = get_client()
        tenant_resp = client.table("tenants").select("id").eq("name", tenant_name).eq("unit", unit).execute()
        if not tenant_resp.data:
            raise Exception(f"Tenant '{tenant_name}' at Unit '{unit}' not found.")
        tenant_id = tenant_resp.data[0]['id']

    # Upload to Supabase Storage
    cloud_path = save_uploaded_file(
        tenant_id=tenant_id,
        tenant_name=tenant_name,
        unit=unit,
        filename="Rent_Increase_Notice.pdf",
        content=content,
        doc_type="Notice"
    )

    return cloud_path


def get_expiring_leases(user_id: str, days: int = 90) -> list[dict]:
    """Return tenants whose leases expire within the given number of days."""
    client = get_client()
    response = (
        client.table("tenants")
        .select("*")
        .eq("user_id", user_id)
        .neq("lease_end", "")
        .not_.is_("lease_end", "null")
        .execute()
    )
    today = datetime.now()
    results = []
    for row in (response.data or []):
        try:
            end_str = row["lease_end"].split(" ")[0]
            end_date = datetime.strptime(end_str, "%Y-%m-%d")
            days_left = (end_date - today).days
            if 0 < days_left <= days:
                row["days_left"] = days_left
                results.append(row)
        except (ValueError, AttributeError):
            continue
    return sorted(results, key=lambda x: x["days_left"])
