"""Application configuration — loads environment variables and defines constants."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "documents"

# Ensure directories exist
DOCS_DIR.mkdir(exist_ok=True)

# ── Supabase ───────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ── Security ───────────────────────────────────────────────────────────────────
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
# Bug fix #11: Session secret should come from env, not be hardcoded in source
STORAGE_SECRET = os.getenv("STORAGE_SECRET", "tenant-flow-change-me-in-production")

# ── Twilio (optional) ─────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

# ── Meta Marketing API (Facebook / Instagram) ─────────────────────────────────
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID", "")

# ── Amazon SES (email delivery) ───────────────────────────────────────────────
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL", "")

# ── App ────────────────────────────────────────────────────────────────────────
APP_TITLE = "Virix"
APP_HOST = os.getenv("HOST", "0.0.0.0")
# Railway and Render provide the PORT as an environment variable
APP_PORT = int(os.getenv("PORT", 8080))
