"""Document service — manages file uploads to Supabase Storage and record-keeping in Postgres."""

import os
from app.models.database import get_client

BUCKET_NAME = "documents"


def save_uploaded_file(tenant_id: int, tenant_name: str, unit: str, 
                       filename: str, content: bytes, doc_type: str = "Other") -> str:
    """Upload a file to Supabase Storage and record it in the database."""
    client = get_client()
    
    # 1. Prepare cloud path: tenants/unit_name/filename
    # Example: tenants/101_John_Doe/id_card.pdf
    safe_name = tenant_name.replace(" ", "_")
    cloud_path = f"tenants/{unit}_{safe_name}/{filename}"
    
    try:
        # 2. Upload to Supabase Storage
        # We use 'upsert=True' so if you upload the same file again, it overwrites
        client.storage.from_(BUCKET_NAME).upload(
            path=cloud_path,
            file=content,
            file_options={"cache-control": "3600", "upsert": "true"}
        )
        
        # 3. Save reference in the 'documents' table
        client.table("documents").insert({
            "tenant_id": tenant_id,
            "filename": filename,
            "filepath": cloud_path, # This is the storage path
            "doc_type": doc_type
        }).execute()
        
        return cloud_path
    except Exception as e:
        print(f"[ERROR] Failed to upload document: {e}")
        raise e


def get_tenant_documents(tenant_id: int) -> list[dict]:
    """Fetch all document records for a specific tenant."""
    client = get_client()
    resp = client.table("documents").select("*").eq("tenant_id", tenant_id).execute()
    return resp.data


def get_signed_url(filepath: str, expires_in: int = 60) -> str:
    """Generate a temporary (signed) URL to view a private document."""
    client = get_client()
    try:
        resp = client.storage.from_(BUCKET_NAME).create_signed_url(filepath, expires_in)
        return resp.get("signedURL")
    except Exception as e:
        print(f"[ERROR] Failed to generate signed URL: {e}")
        return ""


def delete_document(doc_id: int, filepath: str):
    """Delete document from both Storage and Database."""
    client = get_client()
    try:
        # Delete from Storage
        client.storage.from_(BUCKET_NAME).remove([filepath])
        # Delete from Database
        client.table("documents").delete().eq("id", doc_id).execute()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to delete document: {e}")
        return False


def list_all_document_folders() -> list[str]:
    """
    List top-level folders in the storage bucket.
    Note: This is a helper for the UI folder browser.
    """
    client = get_client()
    try:
        # List items in the 'tenants/' prefix
        resp = client.storage.from_(BUCKET_NAME).list("tenants")
        return [item['name'] for item in resp if 'id' not in item] # folders usually don't have IDs in the list response
    except Exception:
        return []
