-- ============================================================================
-- Tenant Flow Manager — Supabase Schema Setup
-- Run this in your Supabase SQL Editor:
--   https://supabase.com/dashboard/project/hvyhnlqxlrzqifcbvhkp/sql/new
-- ============================================================================

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username    TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'manager', 'viewer')),
    created_by  UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- Tenants table with user ownership
CREATE TABLE IF NOT EXISTS tenants (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    unit            TEXT, -- Deprecated in Phase 1, use unit_id instead
    unit_address    TEXT, -- Deprecated in Phase 1
    unit_id         UUID, -- Added in Phase 1 to relate to units table
    rent_amount     NUMERIC NOT NULL DEFAULT 0,
    lease_start     TEXT,
    lease_end       TEXT,
    bank_info       TEXT DEFAULT '',
    banking_set_up  TEXT DEFAULT 'No',
    move_in_status  TEXT DEFAULT 'Pending',
    lease_signed    TEXT DEFAULT 'No',
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, unit)
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id       BIGINT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    amount          NUMERIC NOT NULL,
    payment_type    TEXT DEFAULT 'PAD',
    status          TEXT DEFAULT 'Completed',
    date            DATE DEFAULT CURRENT_DATE,
    notes           TEXT DEFAULT ''
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id       BIGINT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    filename        TEXT NOT NULL,
    filepath        TEXT NOT NULL,
    doc_type        TEXT DEFAULT 'Other',
    uploaded_at     TIMESTAMPTZ DEFAULT now()
);

-- ── Marketing Configurations ──────────────────────────────────────────────
-- Stores encrypted Meta API credentials for each user
CREATE TABLE IF NOT EXISTS marketing_configs (
    user_id         UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    access_token    TEXT NOT NULL, -- Encrypted
    ad_account_id   TEXT NOT NULL, -- Encrypted
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Phase 1: Enterprise Expansion (Properties & Units) ────────────────────

CREATE TABLE IF NOT EXISTS properties (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    address         TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS units (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    property_id     UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    unit_number     TEXT NOT NULL,
    status          TEXT DEFAULT 'Vacant',
    default_rent    NUMERIC DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Phase 1: Audit Logs ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_logs (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action          TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    entity_id       TEXT NOT NULL,
    old_value       JSONB,
    new_value       JSONB,
    timestamp       TIMESTAMPTZ DEFAULT NOW()
);

-- ── Phase 2: Financial Engine (Ledgers & Transactions) ────────────────────

CREATE TABLE IF NOT EXISTS transactions (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id       BIGINT REFERENCES tenants(id) ON DELETE SET NULL,
    unit_id         UUID REFERENCES units(id) ON DELETE SET NULL,
    type            TEXT NOT NULL, -- "Charge" or "Payment"
    category        TEXT NOT NULL, -- "Rent", "Late Fee", "Maintenance", "Deposit"
    amount          NUMERIC NOT NULL,
    date            DATE NOT NULL DEFAULT CURRENT_DATE,
    status          TEXT DEFAULT 'Cleared', -- "Pending", "Cleared", "Failed"
    stripe_id       TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Phase 3: Operations (Maintenance) ─────────────────────────────────────

CREATE TABLE IF NOT EXISTS maintenance_requests (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id       BIGINT REFERENCES tenants(id) ON DELETE CASCADE,
    unit_id         UUID REFERENCES units(id) ON DELETE CASCADE,
    issue           TEXT NOT NULL,
    urgency         TEXT DEFAULT 'Low', -- "Low", "Medium", "High", "Emergency"
    status          TEXT DEFAULT 'Open', -- "Open", "In Progress", "Resolved"
    contractor      TEXT,
    cost            NUMERIC DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);

-- Disable RLS (we use service_role key from server-side, RLS not needed)
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE tenants DISABLE ROW LEVEL SECURITY;
ALTER TABLE payments DISABLE ROW LEVEL SECURITY;
ALTER TABLE documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE marketing_configs DISABLE ROW LEVEL SECURITY;
ALTER TABLE properties DISABLE ROW LEVEL SECURITY;
ALTER TABLE units DISABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE transactions DISABLE ROW LEVEL SECURITY;
ALTER TABLE maintenance_requests DISABLE ROW LEVEL SECURITY;
