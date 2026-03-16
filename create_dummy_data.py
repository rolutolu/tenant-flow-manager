import pandas as pd
import os
from datetime import datetime, timedelta

def create_dummy_tenants():
    data_dir = 'c:/Users/rolut/Downloads/tenant-flow-manager/data'
    os.makedirs(data_dir, exist_ok=True)
    
    file_path = os.path.join(data_dir, 'tenants.xlsx')
    
    today = datetime.now()
    
    # Create some dummy data
    data = {
        'Unit': ['Unit_101', 'Unit_102', 'Unit_201'],
        'Tenant_Name': ['John Smith', 'Jane Doe', 'Alice Bob'],
        'Rent_Amount': [1500, 1600, 1550],
        'Lease_Start_Date': [(today - timedelta(days=200)).strftime('%Y-%m-%d'), 
                             (today - timedelta(days=100)).strftime('%Y-%m-%d'),
                             (today - timedelta(days=350)).strftime('%Y-%m-%d')],
        'Lease_End_Date': [(today + timedelta(days=165)).strftime('%Y-%m-%d'),
                           (today + timedelta(days=265)).strftime('%Y-%m-%d'),
                           (today + timedelta(days=15)).strftime('%Y-%m-%d')], # Alice is due for 3-month notice (already past actually, or close)
        'Banking_Set_Up': ['Yes', 'Yes', 'No'],
        'Move_In_Status': ['Completed', 'Completed', 'Completed'],
        'Lease_Signed': ['Yes', 'Yes', 'Yes']
    }
    
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)
    print(f"Created dummy data at {file_path}")

if __name__ == '__main__':
    create_dummy_tenants()
