"""Service for managing import submissions in the superadmin approval queue."""

import uuid
from datetime import datetime, timezone

from app.models.database import get_client
from app.services.ingestion_service import execute_import

BUCKET_NAME = "documents"


# ── Submission helpers ─────────────────────────────────────────────────────────

def _upload_to_storage(file_bytes: bytes, filename: str) -> str | None:
    """Upload raw file bytes to Supabase Storage. Returns the storage path or None."""
    client = get_client()
    storage_path = f"imports/{uuid.uuid4()}_{filename}"
    try:
        client.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"cache-control": "3600", "upsert": "true"},
        )
        return storage_path
    except Exception as e:
        print(f"[WARN] Could not upload import file to Storage: {e}")
        return None


def submit_spreadsheet(
    user_id: str,
    filename: str,
    file_bytes: bytes,
    column_mapping: dict,
    mapped_rows: list[dict],
) -> str | None:
    """Store the original file in Storage and queue a spreadsheet submission for approval.

    Returns the new submission UUID, or None on failure.
    """
    storage_path = _upload_to_storage(file_bytes, filename)

    client = get_client()
    try:
        response = client.table("import_submissions").insert({
            "submitted_by":   user_id,
            "filename":       filename,
            "file_type":      "spreadsheet",
            "storage_path":   storage_path,
            "column_mapping": column_mapping,
            "mapped_rows":    mapped_rows,
            "row_count":      len(mapped_rows),
            "status":         "pending",
        }).execute()
        return response.data[0]["id"] if response.data else None
    except Exception as e:
        print(f"[ERROR] Failed to create spreadsheet submission: {e}")
        return None


def submit_raw_file(user_id: str, filename: str, file_bytes: bytes) -> str | None:
    """Upload a raw file to Storage and queue a raw submission for manual review.

    Returns the new submission UUID, or None on failure.
    """
    storage_path = _upload_to_storage(file_bytes, filename)
    if not storage_path:
        return None

    client = get_client()
    try:
        response = client.table("import_submissions").insert({
            "submitted_by": user_id,
            "filename":     filename,
            "file_type":    "raw",
            "storage_path": storage_path,
            "row_count":    0,
            "status":       "pending",
        }).execute()
        return response.data[0]["id"] if response.data else None
    except Exception as e:
        print(f"[ERROR] Failed to create raw submission: {e}")
        return None


# ── Query helpers ──────────────────────────────────────────────────────────────

def get_pending_submissions() -> list[dict]:
    """Return all pending submissions with submitter username. Superadmin only."""
    client = get_client()
    try:
        response = (
            client.table("import_submissions")
            .select("*, submitter:users!submitted_by(username)")
            .eq("status", "pending")
            .order("submitted_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"[ERROR] Failed to fetch pending submissions: {e}")
        return []


def get_user_submissions(user_id: str) -> list[dict]:
    """Return all submissions made by a specific user (for their history view)."""
    client = get_client()
    try:
        response = (
            client.table("import_submissions")
            .select("id, filename, file_type, row_count, status, submitted_at, rejection_note")
            .eq("submitted_by", user_id)
            .order("submitted_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"[ERROR] Failed to fetch user submissions: {e}")
        return []


# ── Review actions ─────────────────────────────────────────────────────────────

def approve_submission(
    submission_id: str,
    reviewer_id: str,
    rows_override: list[dict] | None = None,
) -> tuple[bool, str]:
    """Run the import for a submission and mark it approved.

    rows_override: if provided, these rows are used instead of what is stored in
    the DB (allows the reviewer to edit rows before approving).
    """
    client = get_client()
    try:
        response = client.table("import_submissions").select("*").eq("id", submission_id).execute()
        if not response.data:
            return False, "Submission not found."

        sub = response.data[0]

        if sub["file_type"] != "spreadsheet":
            return False, "Raw file submissions must be imported manually via Supabase."

        rows = rows_override if rows_override is not None else (sub.get("mapped_rows") or [])
        if not rows:
            return False, "No rows to import."

        submitted_by = sub["submitted_by"]
        p_cnt, u_cnt, t_cnt = execute_import(submitted_by, rows)

        client.table("import_submissions").update({
            "status":      "approved",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_by": reviewer_id,
        }).eq("id", submission_id).execute()

        return True, f"Approved — {p_cnt} properties, {u_cnt} units, {t_cnt} tenants created."
    except Exception as e:
        return False, f"Approval failed: {str(e)}"


def reject_submission(
    submission_id: str,
    reviewer_id: str,
    note: str = "",
) -> tuple[bool, str]:
    """Mark a submission as rejected with an optional note."""
    client = get_client()
    try:
        client.table("import_submissions").update({
            "status":         "rejected",
            "reviewed_at":    datetime.now(timezone.utc).isoformat(),
            "reviewed_by":    reviewer_id,
            "rejection_note": note,
        }).eq("id", submission_id).execute()
        return True, "Submission rejected."
    except Exception as e:
        return False, f"Reject failed: {str(e)}"


def get_download_url(storage_path: str, expires_in: int = 300) -> str:
    """Generate a short-lived signed URL (default 5 min) for the original file."""
    client = get_client()
    try:
        resp = client.storage.from_(BUCKET_NAME).create_signed_url(storage_path, expires_in)
        return resp.get("signedURL") or ""
    except Exception as e:
        print(f"[ERROR] Failed to generate download URL: {e}")
        return ""
