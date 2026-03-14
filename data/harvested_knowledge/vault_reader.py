"""
VAULT READER — The only file that touches identity_vault.enc

Every script that needs identity data calls get_field() or get_fields() here.
Scripts NEVER get the whole vault. They request named fields only.
Nothing is ever written to disk. Decrypted data lives in RAM only.

Usage:
    from vault_reader import get_field, get_fields, vault_available

    name = get_field("full_legal_name")
    data = get_fields(["full_legal_name", "address_line1", "city", "state", "zip_code"])
"""

import os
import json
import base64
import getpass
import hashlib
from pathlib import Path
from functools import lru_cache

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

DESKTOP    = Path.home() / "Desktop"
VAULT_FILE = DESKTOP / "identity_vault.enc"
SALT_FILE  = DESKTOP / "identity_vault.salt"

# Session cache — decrypted once per script run, held in RAM, never written
_SESSION_VAULT = None
_SESSION_PASSWORD = None

def vault_available() -> bool:
    return VAULT_FILE.exists() and SALT_FILE.exists() and CRYPTO_AVAILABLE

def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def _unlock_vault(password: str = None) -> dict | None:
    global _SESSION_VAULT, _SESSION_PASSWORD
    if _SESSION_VAULT is not None:
        return _SESSION_VAULT
    if not vault_available():
        return None
    if password is None:
        password = getpass.getpass("  [VAULT] Enter vault password to unlock: ")
    salt = SALT_FILE.read_bytes()
    key  = _derive_key(password, salt)
    f    = Fernet(key)
    try:
        raw = f.decrypt(VAULT_FILE.read_bytes())
        _SESSION_VAULT = json.loads(raw.decode())
        _SESSION_PASSWORD = password
        return _SESSION_VAULT
    except InvalidToken:
        print("  [VAULT] ❌ Incorrect password.")
        return None

def get_field(field_name: str, password: str = None) -> str | None:
    """Get a single field from the vault. Prompts for password if not unlocked."""
    vault = _unlock_vault(password)
    if vault is None:
        return None
    return vault.get(field_name)

def get_fields(field_names: list, password: str = None) -> dict:
    """Get multiple fields. Returns dict of {field_name: value}."""
    vault = _unlock_vault(password)
    if vault is None:
        return {}
    return {k: vault.get(k) for k in field_names}

def get_all_non_sensitive(password: str = None) -> dict:
    """Get all non-sensitive fields (excludes SSN, bank info, ID numbers)."""
    SENSITIVE = {"ssn", "bank_routing", "bank_account", "state_id_number", "passport_number"}
    vault = _unlock_vault(password)
    if vault is None:
        return {}
    return {k: v for k, v in vault.items() if k not in SENSITIVE and not k.startswith("_")}

def lock_vault():
    """Clear the in-memory vault. Call when done."""
    global _SESSION_VAULT, _SESSION_PASSWORD
    _SESSION_VAULT = None
    _SESSION_PASSWORD = None

def verify_integrity(password: str = None) -> bool:
    """Returns True if vault checksum matches."""
    vault = _unlock_vault(password)
    if vault is None:
        return False
    stored = vault.get("_checksum", "")
    clean = {k: v for k, v in vault.items() if not k.startswith("_")}
    computed = hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest()
    return stored == computed
