# Virix — Property Management Platform

Virix is a modern, web-based property management system built using **NiceGUI**, **Python**, and **Supabase**. It automates the entire tenant lifecycle: from document collection and reference checks to lease generation, rent increase notices, marketing analytics, and financial ledger tracking.

---

## Features

- **Tenant Intake & Lifecycle**: Handle move-ins, lease parameters, banking setup, and automated occupancy updates.
- **Lease & Notice Generation**: Instantly generate PDF lease agreements and rent increase notices, automatically storing them in Supabase Storage.
- **Marketing Analytics Dashboard**: Real-time integration with Meta Marketing API to view campaign insights, spend, ctr, cpc, and ad performance.
- **Financial Ledger**: Record transactions, clear/fail payments, and track revenue streams (PAD, E-Transfer).
- **Audit Compliance Trail**: Detailed system event logging tracking all key user actions.
- **Bulk Import Workflow**: Dual import paths for Excel/CSV spreadsheet mappings and raw database/document dumps.
- **Security First**: Role-based access control (`superadmin`, `admin`, `manager`, `viewer`) and sensitive data encryption using Fernet keys.

---

## Tech Stack

- **Frontend/Backend UI**: [NiceGUI](https://nicegui.io/) (Python framework built on top of FastAPI, Tailwind CSS, and Quasar)
- **Database / Storage**: [Supabase](https://supabase.com/)
- **PDF Generation**: `fpdf2`
- **Security**: PyJWT, bcrypt, cryptography (Fernet)

---

## Getting Started

### 1. Prerequisites
Ensure you have **Python 3.10+** installed.

### 2. Install Dependencies
Clone the repository and install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory (or customize the existing one):
```ini
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-role-key  # Must be service_role key

# Security
ENCRYPTION_KEY=your-fernet-encryption-key    # Generate with cryptography.fernet.Fernet.generate_key()
STORAGE_SECRET=your-random-nicegui-storage-secret

# Invite System for Registration
INVITE_CODE=your-secret-invite-code           # Gate registration via /register?code=invite_code

# AWS SES (Email Notifications)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
SES_FROM_EMAIL=notices@yourdomain.com

# Twilio (MFA/SMS notifications - optional)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=your_number

# Meta Marketing API (Optional)
META_ACCESS_TOKEN=your_meta_access_token
META_AD_ACCOUNT_ID=act_your_ad_account_id
```

### 4. Database Setup
1. Log in to your Supabase Console.
2. Open the **SQL Editor**.
3. Copy and run the entire contents of [`setup_supabase.sql`](file:///c:/Users/rolut/Downloads/tenant-flow-manager/setup_supabase.sql).

### 5. Seed the Database
To populate the database with realistic mock data (including `superadmin`, `admin`, and `manager` roles, properties, units, tenants, and transactions):
```bash
python create_dummy_data.py
```
*Note: Make sure your `.env` is configured correctly before running the seeding script.*

### 6. Run the Application
Start the local development server:
```bash
python main.py
```
Open your browser and navigate to `http://localhost:8080`.

---

## User Roles & Hierarchy

- **`superadmin`**: Review bulk import submissions, manage system-wide user settings, and bypass normal role constraints.
- **`admin`**: Full account management, property & unit configuration, tenant intake, and team user creation.
- **`manager`**: Daily operations, lease creation, logging financial transactions, and editing tenant details.
- **`viewer`**: Read-only access to dashboards, reports, and audit logs.
