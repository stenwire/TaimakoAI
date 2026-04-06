import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config import settings

def _get_cipher_suite() -> Fernet:
    """
    Derive a Fernet key from the JWT_SECRET and return a Fernet instance.
    This ensures we use a consistent key for encryption without needing extra env vars,
    though in production a dedicated SECRET_KEY is better.
    """
    secret = settings.JWT_SECRET.encode()
    salt = b'static_salt_for_api_key_encryption' # In a real app, this should probably be configurable
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret))
    return Fernet(key)

def encrypt_string(value: str) -> str:
    """Encrypt a string value."""
    if not value:
        return value
    f = _get_cipher_suite()
    return f.encrypt(value.encode()).decode()

def decrypt_string(value: str) -> Optional[str]:
    """Decrypt a string value."""
    if not value:
        return value
    try:
        f = _get_cipher_suite()
        return f.decrypt(value.encode()).decode()
    except Exception:
        # If decryption fails (e.g. key changed, bad data), return None or handle appropriately
        return None
