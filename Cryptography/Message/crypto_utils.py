import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken

def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a secure key from a password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_message(message: str, password: str) -> str:
    """Encrypt a text message using a password."""
    salt = os.urandom(16)
    key = derive_key(password, salt)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(message.encode())
    return base64.urlsafe_b64encode(salt + encrypted).decode()

def decrypt_message(encrypted_b64: str, password: str) -> str:
    """Decrypt a message using a password."""
    try:
        data = base64.urlsafe_b64decode(encrypted_b64)
        salt = data[:16]
        encrypted = data[16:]
        key = derive_key(password, salt)
        fernet = Fernet(key)
        return fernet.decrypt(encrypted).decode()
    except (InvalidToken, ValueError):
        return "Error: Wrong password or corrupted message!"

def encrypt_file(file_path: str, password: str) -> str:
    """Encrypt a text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    encrypted = encrypt_message(content, password)
    out_file = file_path + ".enc"
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(encrypted)
    return out_file

def decrypt_file(file_path: str, password: str) -> str:
    """Decrypt an encrypted text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        encrypted = f.read()
    decrypted = decrypt_message(encrypted, password)
    out_file = file_path.replace(".enc", "_decrypted.txt")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(decrypted)
    return out_file
