from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken

# Initialize Fernet with the key from your settings
try:
    f = Fernet(settings.FERNET_KEY)
except Exception as e:
    raise ValueError(f"Invalid FERNET_KEY in settings.py. It must be a valid Fernet key. Error: {e}")

def encrypt_data(data_str: str) -> str:
    """
    Encrypts a string and returns a URL-safe text token.
    """
    if not data_str:
        return ""
    try:
        data_bytes = data_str.encode('utf-8')
        encrypted_bytes = f.encrypt(data_bytes)
        return encrypted_bytes.decode('utf-8')
    except Exception:
        # Handle encryption errors, though they are rare
        return ""

def decrypt_data(encrypted_token: str) -> str:
    """
    Decrypts a Fernet token (string) and returns the original string.
    Returns an empty string if decryption fails or token is empty.
    """
    if not encrypted_token:
        return ""
    try:
        encrypted_bytes = encrypted_token.encode('utf-8')
        decrypted_bytes = f.decrypt(encrypted_bytes)
        return decrypted_bytes.decode('utf-8')
    except (InvalidToken, TypeError):
        # If the token is invalid or not a string, return a safe value
        return "Decryption Failed: Invalid data."
    except Exception:
        # Catch other potential errors
        return "Decryption Failed."