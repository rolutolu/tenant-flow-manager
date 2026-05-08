"""Supabase database client and encryption helpers."""

from cryptography.fernet import Fernet, InvalidToken
from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_KEY, ENCRYPTION_KEY


# ── Supabase Client (singleton) ───────────────────────────────────────────────

_client: Client | None = None


def get_client() -> Client:
    """Return the Supabase client singleton."""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in your .env file."
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


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
