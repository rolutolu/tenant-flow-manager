"""Document upload handling with path sanitization."""

import os
import re
from pathlib import Path
from app.config import DOCS_DIR
from app.models.database import get_connection


def sanitize_name(name: str) -> str:
    """Remove dangerous characters from a name used in file paths.

    Strips path separators, parent-directory references, and non-alphanumeric
    characters (except underscores, hyphens, and spaces which become underscores).
    """
    # Remove any path separators and parent references
    name = name.replace("..", "").replace("/", "").replace("\\", "")
    # Keep only alphanumeric, spaces, hyphens, underscores
    name = re.sub(r"[^a-zA-Z0-9 _\-]", "", name)
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "unknown"


def get_tenant_folder(tenant_name: str, unit: str) -> Path:
    """Return the sanitized folder path for a tenant, creating it if needed."""
    safe_name = sanitize_name(tenant_name)
    safe_unit = sanitize_name(unit)
    folder = DOCS_DIR / f"{safe_unit}_{safe_name}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_uploaded_file(tenant_id: int, tenant_name: str, unit: str,
                       filename: str, content: bytes, doc_type: str = "Other") -> str:
    """Save an uploaded file to the tenant's folder and record it in the database.

    Returns the saved filepath.
    """
    folder = get_tenant_folder(tenant_name, unit)
    safe_filename = sanitize_name(Path(filename).stem) + Path(filename).suffix.lower()
    filepath = folder / safe_filename

    with open(filepath, "wb") as f:
        f.write(content)

    # Record in database
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO documents (tenant_id, filename, filepath, doc_type) VALUES (?, ?, ?, ?)",
            (tenant_id, safe_filename, str(filepath), doc_type)
        )
        conn.commit()
    finally:
        conn.close()

    return str(filepath)


def get_tenant_documents(tenant_id: int) -> list[dict]:
    """Return all documents for a tenant."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM documents WHERE tenant_id = ? ORDER BY uploaded_at DESC",
            (tenant_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def list_all_document_folders() -> list[str]:
    """Return a list of all tenant document folder names."""
    if not DOCS_DIR.exists():
        return []
    return [f.name for f in DOCS_DIR.iterdir() if f.is_dir()]
