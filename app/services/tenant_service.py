"""CRUD operations for tenants in the SQLite database."""

from app.models.database import get_connection, encrypt_value, decrypt_value


def add_tenant(name: str, unit: str, rent_amount: float,
               lease_start: str = "", lease_end: str = "",
               bank_info: str = "", banking_set_up: str = "No",
               move_in_status: str = "Pending", lease_signed: str = "No") -> int:
    """Insert a new tenant and return their ID."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO tenants (name, unit, rent_amount, lease_start, lease_end,
                                    bank_info, banking_set_up, move_in_status, lease_signed)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, unit, rent_amount, lease_start, lease_end,
             encrypt_value(bank_info), banking_set_up, move_in_status, lease_signed)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_tenants() -> list[dict]:
    """Return all tenants as a list of dicts (bank_info decrypted)."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM tenants ORDER BY id").fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["bank_info"] = decrypt_value(d.get("bank_info", ""))
            result.append(d)
        return result
    finally:
        conn.close()


def get_tenant(tenant_id: int) -> dict | None:
    """Return a single tenant by ID."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,)).fetchone()
        if row:
            d = dict(row)
            d["bank_info"] = decrypt_value(d.get("bank_info", ""))
            return d
        return None
    finally:
        conn.close()


def get_tenant_by_unit(unit: str) -> dict | None:
    """Return a single tenant by unit identifier."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tenants WHERE unit = ?", (unit,)).fetchone()
        if row:
            d = dict(row)
            d["bank_info"] = decrypt_value(d.get("bank_info", ""))
            return d
        return None
    finally:
        conn.close()


def update_tenant(tenant_id: int, **kwargs) -> bool:
    """Update specific fields for a tenant. Encrypts bank_info automatically."""
    if not kwargs:
        return False
    if "bank_info" in kwargs:
        kwargs["bank_info"] = encrypt_value(kwargs["bank_info"])
    set_clause = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [tenant_id]
    conn = get_connection()
    try:
        conn.execute(f"UPDATE tenants SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return True
    finally:
        conn.close()


def delete_tenant(tenant_id: int) -> bool:
    """Delete a tenant by ID."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM tenants WHERE id = ?", (tenant_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def get_tenant_count() -> int:
    """Return total number of tenants."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM tenants").fetchone()
        return row["cnt"]
    finally:
        conn.close()


def get_pending_signatures_count() -> int:
    """Return count of tenants who haven't signed their lease yet."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM tenants WHERE lease_signed != 'Yes'").fetchone()
        return row["cnt"]
    finally:
        conn.close()
