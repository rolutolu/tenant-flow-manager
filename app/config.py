"""Application configuration — loads environment variables and defines constants."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "documents"
DB_PATH = DATA_DIR / "tenants.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

# ── Security ───────────────────────────────────────────────────────────────────
APP_PASSWORD = os.getenv("APP_PASSWORD", "admin123")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

# ── Twilio (optional) ─────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

# ── App ────────────────────────────────────────────────────────────────────────
APP_TITLE = "Tenant Flow Manager"
APP_HOST = "127.0.0.1"
APP_PORT = 8080
