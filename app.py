import streamlit as st
import pandas as pd
import os
from src.automation import send_reference_checks

# App Configuration
st.set_page_config(page_title="Tenant Flow Manager", layout="wide")
st.title("🏙️ Tenant Flow Manager")

# Directory setup
DOCS_DIR = "documents"
os.makedirs(DOCS_DIR, exist_ok=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📂 Intake & Screening", 
    "✍️ Lease Management", 
    "💰 Financial Sync",
    "🔔 Action Center"
])

with tab1:
    st.header("New Tenant Intake")
    
    with st.expander("1. Document Collection", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            tenant_name = st.text_input("Tenant Full Name")
            unit_number = st.text_input("Unit Number")
            
        with col2:
            st.write("Upload Required Documents")
            id_doc = st.file_uploader("Gov ID (PDF/Image)", type=['pdf', 'jpg', 'png'])
            deposit_slip = st.file_uploader("Direct Deposit Slip", type=['pdf', 'jpg', 'png'])
            bank_statements = st.file_uploader("6 Months Bank Statements", type=['pdf'])
            
        if st.button("Verify & Save Documents"):
            if not tenant_name or not unit_number:
                st.error("Please enter Name and Unit Number.")
            else:
                missing = []
                if not id_doc: missing.append("Gov ID")
                if not deposit_slip: missing.append("Direct Deposit Slip")
                if not bank_statements: missing.append("Bank Statements")
                
                if missing:
                    st.warning(f"⚠️ Missing required documents: {', '.join(missing)}")
                else:
                    from src.document_gen import save_tenant_documents
                    files = {
                        "Gov ID": id_doc,
                        "Direct Deposit Slip": deposit_slip,
                        "Bank Statements": bank_statements
                    }
                    tenant_dir, saved_paths = save_tenant_documents(tenant_name, unit_number, files)
                    st.success("All documents verified!")
                    st.info(f"Documents saved successfully in `{tenant_dir}`")
                    
    with st.expander("2. Reference Management", expanded=False):
        st.write("Send inquiry emails/texts to landlord and job references.")
        ref_type = st.radio("Reference Type", ["Landlord", "Employer"])
        ref_name = st.text_input("Reference Name")
        ref_phone = st.text_input("Reference Phone Number (for SMS)")
        ref_email = st.text_input("Reference Email")
        
        if st.button("Send Inquiry via Twilio (SMS)"):
            if not ref_phone:
                st.error("Please provide a phone number.")
            else:
                success, msg = send_reference_checks(
                    tenant_name=tenant_name if tenant_name else "Prospective Tenant", 
                    ref_phone=ref_phone, 
                    ref_name=ref_name
                )
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
                    
with tab2:
    st.header("Lease Generation & Status")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Generate New Lease")
        l_tenant = st.text_input("Tenant Name for Lease")
        l_unit = st.text_input("Unit for Lease")
        l_rent = st.number_input("Monthly Rent ($)", min_value=100.0, step=50.0, value=1500.0)
        l_start = st.date_input("Lease Start Date")
        l_end = st.date_input("Lease End Date")
        
        if st.button("Generate Lease PDF"):
            if not l_tenant or not l_unit:
                st.error("Please provide tenant name and unit.")
            else:
                from src.document_gen import generate_lease_agreement
                filepath = generate_lease_agreement(
                    l_tenant, l_unit, l_rent, 
                    l_start.strftime('%Y-%m-%d'), 
                    l_end.strftime('%Y-%m-%d')
                )
                st.success(f"Lease generated successfully at `{filepath}`")
                
                with open(filepath, "rb") as f:
                    st.download_button("⬇️ Download Lease PDF", f, file_name=f"{l_unit}_Lease_Agreement.pdf")
                    
    with col2:
        st.subheader("Document Status & Pipeline")
        if os.path.exists(DOCS_DIR):
            folders = [f for f in os.listdir(DOCS_DIR) if os.path.isdir(os.path.join(DOCS_DIR, f))]
            if folders:
                selected_folder = st.selectbox("Select Tenant Folder to View Files", folders)
                folder_path = os.path.join(DOCS_DIR, selected_folder)
                files = os.listdir(folder_path)
                
                st.write(f"**Files in {selected_folder}:**")
                for f in files:
                    st.write(f"📄 {f}")
            else:
                st.info("No unit folders created yet. Process a new intake first.")
        else:
            st.info("Documents directory not found.")
    
with tab3:
    st.header("Financial Synchronization (Excel)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Banking Integration")
        st.write("Append newly collected bank info to the master spreadsheet.")
        b_tenant = st.text_input("Tenant Name", key="bank_t")
        b_unit = st.text_input("Unit", key="bank_u")
        b_acc = st.text_input("Bank Account / Transit (Optional/Mock)", type="password")
        
        if st.button("Append to PAD System"):
            from src.excel_handler import append_bank_info
            success, msg = append_bank_info(b_tenant, b_unit, b_acc)
            if success:
                st.success(msg)
            else:
                st.error(msg)
                
    with col2:
        st.subheader("2. Monthly Cross-Reference")
        st.write("Compare monthly rent spreadsheet against banking system.")
        uploaded_report = st.file_uploader("Upload Monthly Bank Report (.csv)", type=['csv'])
        if st.button("Run Cross-Reference Check"):
            from src.excel_handler import cross_reference_rent
            # Simulated check
            success, msg = cross_reference_rent("mock_path")
            st.success(msg)
            
        st.subheader("3. Returns Reporting (NSF)")
        st.write("Flag returned payments and trigger 48h e-transfer notices.")
        if st.button("Check for Returns"):
            from src.excel_handler import flag_returned_payments
            nsf_cases, msg = flag_returned_payments()
            if nsf_cases:
                st.warning(f"Found {len(nsf_cases)} returned payment(s):")
                for case in nsf_cases:
                    st.write(f"- **{case['Tenant']}** ({case['Unit']}): ${case['Amount']}")
                    if st.button(f"Send 48h E-transfer Notice to {case['Tenant']}", key=f"nsf_{case['Unit']}"):
                        st.success(f"Notice sent to {case['Tenant']}!")
            else:
                st.success("No returns found.")

with tab4:
    st.header("Action Center & Compliance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Today's Tasks")
        st.write("Scan 'Lease End Dates' daily and flag units that require action.")
        
        if st.button("Scan for Upcoming Lease Expirations"):
            from src.automation import check_rent_increases
            upcoming = check_rent_increases()
            
            if upcoming:
                st.warning(f"Found {len(upcoming)} lease(s) expiring within 90 days!")
                for item in upcoming:
                    with st.expander(f"⚠️ {item['Tenant_Name']} (Unit {item['Unit']}) - {item['Days_Left']} days left", expanded=True):
                        st.write(f"**Lease End Date:** {item['End_Date']}")
                        if st.button(f"Draft & Email Rent Increase Notice", key=f"notice_{item['Unit']}"):
                            from src.automation import draft_rent_increase_notice
                            success, msg = draft_rent_increase_notice(item['Tenant_Name'], item['Unit'])
                            st.success(msg)
            else:
                st.success("No leases expiring within the next 90 days.")
                
    with col2:
        st.subheader("📊 System Overview")
        st.write("Current Database Status:")
        
        import pandas as pd
        if os.path.exists("data/tenants.xlsx"):
            df = pd.read_excel("data/tenants.xlsx")
            st.dataframe(df, use_container_width=True)
            
            st.metric("Total Active Tenants", len(df))
            st.metric("Pending Signatures", len(df[df['Lease_Signed'] != 'Yes']))
        else:
            st.info("Database file not found.")

