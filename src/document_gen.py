import os
from fpdf import FPDF
from datetime import datetime

DOCS_BASE_DIR = "documents"

def save_tenant_documents(tenant_name, unit_number, files):
    """
    Creates a dedicated folder and saves uploaded Streamlit files.
    """
    # Create folder name like documents/Unit_101_John_Smith/
    folder_name = f"{unit_number}_{tenant_name.replace(' ', '_')}"
    tenant_dir = os.path.join(DOCS_BASE_DIR, folder_name)
    os.makedirs(tenant_dir, exist_ok=True)
    
    saved_paths = []
    
    for file_label, uploaded_file in files.items():
        if uploaded_file is not None:
            # Construct a clean filename
            # Streamlit UploadedFile has a .name attribute
            ext = os.path.splitext(uploaded_file.name)[1]
            filename = f"{file_label.replace(' ', '_')}{ext}"
            filepath = os.path.join(tenant_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            saved_paths.append(filepath)
            
    return tenant_dir, saved_paths

def generate_lease_agreement(tenant_name, unit_number, rent_amount, start_date, end_date):
    """
    Generates a basic PDF lease agreement and saves it in the tenant's folder.
    """
    folder_name = f"{unit_number}_{tenant_name.replace(' ', '_')}"
    tenant_dir = os.path.join(DOCS_BASE_DIR, folder_name)
    os.makedirs(tenant_dir, exist_ok=True)
    
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="RESIDENTIAL LEASE AGREEMENT", ln=True, align='C')
    pdf.ln(10)
    
    # Body
    pdf.set_font("Arial", size=12)
    body_text = f"This Lease Agreement is made on {datetime.now().strftime('%Y-%m-%d')}, \nbetween the Landlord and {tenant_name} (the 'Tenant').\n\n"
    body_text += f"1. PROPERTY: The Landlord agrees to rent the premises located at Unit {unit_number}.\n"
    body_text += f"2. TERM: The lease shall begin on {start_date} and end on {end_date}.\n"
    body_text += f"3. RENT: The Tenant agrees to pay monthly rent in the amount of ${rent_amount}.\n"
    
    pdf.multi_cell(0, 10, txt=body_text)
    
    # Signatures
    pdf.ln(20)
    pdf.cell(100, 10, txt="_______________________", ln=False)
    pdf.cell(100, 10, txt="_______________________", ln=True)
    pdf.cell(100, 10, txt="Landlord Signature", ln=False)
    pdf.cell(100, 10, txt="Tenant Signature", ln=True)
    
    filepath = os.path.join(tenant_dir, "Generated_Lease_Agreement.pdf")
    pdf.output(filepath)
    
    return filepath
