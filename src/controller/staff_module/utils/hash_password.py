import os
from cryptography.fernet import Fernet

# Get Fernet key from environment
FERNET_KEY = os.environ.get("FERNET_KEY")
if not FERNET_KEY:
    raise ValueError("FERNET_KEY not set in environment variables")

cipher = Fernet(FERNET_KEY)

def encrypt_password(raw_password: str) -> bytes:
    """Encrypt a password (can be decrypted later)."""
    return cipher.encrypt(raw_password.encode()).decode()

def decrypt_password(encrypted_password: bytes) -> str:
    """Decrypt the password back to string."""
    return cipher.decrypt(encrypted_password).decode()
