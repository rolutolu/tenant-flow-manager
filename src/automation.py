import os
# from twilio.rest import Client

def send_reference_checks(tenant_name, ref_phone, ref_name="Reference"):
    """
    Skeleton logic for sending an automated SMS to a reference using Twilio.
    User will need to add their Twilio Account SID, Auth Token, and Phone Number.
    """
    
    # --- TWILIO CONFIGURATION (Add actual values here later) ---
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "your_account_sid_here")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "your_auth_token_here")
    TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "+1234567890")
    # -------------------------------------------------------------
    
    message_body = (
        f"Hello {ref_name}, you have been listed as a reference for {tenant_name}. "
        f"Please reply YES to confirm they were a tenant/employee in good standing, "
        f"or call us at 1-800-555-0199 for any concerns. Thank you!"
    )
    
    # This is uncommented and functional once credentials are provided, 
    # but for now we'll just simulate the action.
    try:
        # client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        # message = client.messages.create(
        #     body=message_body,
        #     from_=TWILIO_PHONE_NUMBER,
        #     to=ref_phone
        # )
        
        print(f"[SIMULATED SMS to {ref_phone}]: {message_body}")
        
        return True, f"Simulated Twilio SMS sent to {ref_phone}!"
        
    except Exception as e:
        return False, f"Failed to send message: {str(e)}"

def check_rent_increases(data_file="data/tenants.xlsx"):
    """
    Scans the Excel file for leases ending soon to trigger rent increase notices.
    Returns a list of tenants needing notice.
    """
    import pandas as pd
    from datetime import datetime, timedelta
    
    if not os.path.exists(data_file):
        return []
        
    try:
        df = pd.read_excel(data_file)
        today = datetime.now()
        notice_period_days = 90 # 3 months roughly
        
        needs_notice = []
        for index, row in df.iterrows():
            if pd.notna(row['Lease_End_Date']):
                end_date_str = str(row['Lease_End_Date']).split(' ')[0]
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                
                days_until_end = (end_date - today).days
                
                # Flag if it's coming up within ~3 months but not already expired
                if 0 < days_until_end <= notice_period_days:
                    needs_notice.append({
                        "Tenant_Name": row['Tenant_Name'],
                        "Unit": row['Unit'],
                        "End_Date": end_date_str,
                        "Days_Left": days_until_end
                    })
                    
        return needs_notice
    except Exception as e:
        print(f"Error checking rent increases: {e}")
        return []

def draft_rent_increase_notice(tenant_name, unit, current_rent=None):
    """
    Simulates drafting and sending an email notice.
    """
    subject = f"Rent Increase Notice - Unit {unit}"
    body = f"Dear {tenant_name},\n\nPlease be advised that as your lease is approaching its end date, your rent will be adjusted..."
    print(f"[SIMULATED EMAIL to {tenant_name}]:\nSubject: {subject}\nBody:\n{body}")
    return True, f"Drafted and sent notice to {tenant_name}."

