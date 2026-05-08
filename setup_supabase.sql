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
    unit            TEXT NOT NULL,
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

-- Disable RLS (we use service_role key from server-side, RLS not needed)
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE tenants DISABLE ROW LEVEL SECURITY;
ALTER TABLE payments DISABLE ROW LEVEL SECURITY;
ALTER TABLE documents DISABLE ROW LEVEL SECURITY;
