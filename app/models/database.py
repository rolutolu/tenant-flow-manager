"""SQLite database initialization and encryption helpers."""

import sqlite3
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from app.config import DB_PATH, ENCRYPTION_KEY


# ── Encryption ─────────────────────────────────────────────────────────────────

def _get_fernet():
    """Return a Fernet instance if an encryption key is configured."""
    if ENCRYPTION_KEY:
        return Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
    return None


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value. Returns the plaintext unchanged if no key is set."""
    f = _get_fernet()
    if f and plaintext:
        return f.encrypt(plaintext.encode()).decode()
    return plaintext


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a string value. Returns the ciphertext unchanged if no key is set."""
    f = _get_fernet()
    if f and ciphertext:
        try:
            return f.decrypt(ciphertext.encode()).decode()
        except (InvalidToken, Exception):
            return ciphertext  # Return as-is if decryption fails (e.g., not encrypted)
    return ciphertext


# ── Database Connection ────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database with row_factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── Schema ─────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    unit            TEXT    NOT NULL UNIQUE,
    rent_amount     REAL    NOT NULL DEFAULT 0,
    lease_start     TEXT,
    lease_end       TEXT,
    bank_info       TEXT    DEFAULT '',
    banking_set_up  TEXT    DEFAULT 'No',
    move_in_status  TEXT    DEFAULT 'Pending',
    lease_signed    TEXT    DEFAULT 'No',
    created_at      TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS payments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id       INTEGER NOT NULL,
    amount          REAL    NOT NULL,
    payment_type    TEXT    DEFAULT 'PAD',
    status          TEXT    DEFAULT 'Completed',
    date            TEXT    DEFAULT (date('now')),
    notes           TEXT    DEFAULT '',
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id       INTEGER NOT NULL,
    filename        TEXT    NOT NULL,
    filepath        TEXT    NOT NULL,
    doc_type        TEXT    DEFAULT 'Other',
    uploaded_at     TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
"""


def init_db():
    """Create tables if they do not exist."""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
