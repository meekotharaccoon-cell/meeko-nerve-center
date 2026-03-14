"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           MEEKO IDENTITY VAULT — SECURE SETUP WIZARD                       ║
║           Your data never leaves this machine.                              ║
║           Encrypted at rest. Decrypted to RAM only.                        ║
║           Never committed to any repo. Never logged.                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

HOW THIS WORKS:
  - You enter your info once in this wizard
  - It encrypts everything with a password YOU choose (we never see it)
  - Stores as identity_vault.enc on your Desktop only
  - The legal engine reads it field-by-field, only when needed
  - Nothing is written to disk unencrypted, ever

WHAT TO DO IF YOU WANT TO DESTROY YOUR VAULT:
  - Delete identity_vault.enc — that's it. It's gone.
"""

import os
import sys
import json
import base64
import hashlib
import getpass
import platform
from datetime import datetime
from pathlib import Path

# ── Check/install dependencies ────────────────────────────────────────────────
def install_deps():
    import subprocess
    print("\n[VAULT] Checking dependencies...")
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
    except ImportError:
        print("[VAULT] Installing cryptography library (one-time)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography", "--quiet"])
        print("[VAULT] ✅ Installed.")

install_deps()

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# ── Paths ─────────────────────────────────────────────────────────────────────
DESKTOP = Path.home() / "Desktop"
VAULT_FILE = DESKTOP / "identity_vault.enc"
SALT_FILE  = DESKTOP / "identity_vault.salt"   # salt is not secret, but is unique to you

# ── Key derivation from password ──────────────────────────────────────────────
def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,   # NIST recommended minimum as of 2023
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def get_or_create_salt() -> bytes:
    if SALT_FILE.exists():
        return SALT_FILE.read_bytes()
    salt = os.urandom(32)
    SALT_FILE.write_bytes(salt)
    return salt

# ── Encrypt / Decrypt ─────────────────────────────────────────────────────────
def encrypt_vault(data: dict, password: str) -> bytes:
    salt = get_or_create_salt()
    key  = derive_key(password, salt)
    f    = Fernet(key)
    return f.encrypt(json.dumps(data, indent=2).encode())

def decrypt_vault(password: str) -> dict | None:
    if not VAULT_FILE.exists():
        return None
    salt = SALT_FILE.read_bytes()
    key  = derive_key(password, salt)
    f    = Fernet(key)
    try:
        raw = f.decrypt(VAULT_FILE.read_bytes())
        return json.loads(raw.decode())
    except InvalidToken:
        return None

# ── Terminal UI helpers ───────────────────────────────────────────────────────
def clear():
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def header():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🔐  MEEKO IDENTITY VAULT                                                   ║
║      Secure · Local Only · Never Uploaded · Your Data, Your Keys           ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

def section(title):
    print(f"\n  ── {title} " + "─" * (60 - len(title)))

def ask(prompt, secret=False, optional=False):
    tag = " (optional, press Enter to skip)" if optional else ""
    if secret:
        val = getpass.getpass(f"  {prompt}{tag}: ")
    else:
        val = input(f"  {prompt}{tag}: ").strip()
    return val if val else None

def confirm(prompt):
    return input(f"\n  {prompt} [y/N]: ").strip().lower() == 'y'

# ── The Vault Schema ──────────────────────────────────────────────────────────
"""
Every field in the vault. Scripts request fields by key name.
The legal engine never gets the whole vault — only what it asks for.
"""
VAULT_FIELDS = {
    # Identity
    "full_legal_name":     "Full legal name (as on ID)",
    "preferred_name":      "Preferred/chosen name (optional)",
    "date_of_birth":       "Date of birth (MM/DD/YYYY)",
    "place_of_birth":      "City, State of birth (optional)",

    # Government IDs
    "ssn":                 "Social Security Number (XXX-XX-XXXX)",
    "state_id_number":     "State ID or Driver's License number",
    "state_id_state":      "Which state issued the ID",
    "state_id_expiry":     "ID expiry date (MM/DD/YYYY)",
    "passport_number":     "Passport number (optional)",

    # Address
    "address_line1":       "Street address",
    "address_line2":       "Apt/unit (optional)",
    "city":                "City",
    "state":               "State (2-letter, e.g. TX)",
    "zip_code":            "ZIP code",
    "county":              "County (needed for some filings)",

    # Contact
    "phone_primary":       "Primary phone number",
    "phone_secondary":     "Secondary phone (optional)",
    "email_primary":       "Primary email address",
    "email_legal":         "Email to use for legal/official correspondence (optional)",

    # Financial
    "bank_routing":        "Bank routing number (optional — for direct deposit forms)",
    "bank_account":        "Bank account number (optional)",
    "bank_name":           "Bank name (optional)",

    # Signature
    "signature_image_path":"Path to signature image file (optional, e.g. C:/Users/meeko/sig.png)",

    # Legal/Professional
    "occupation":          "Occupation or job title",
    "employer_name":       "Employer name (optional)",
    "employer_address":    "Employer address (optional)",
    "monthly_income":      "Approximate monthly income (for benefits screening)",
    "household_size":      "Number of people in household",

    # System metadata
    "_vault_version":      None,   # internal
    "_created":            None,   # internal
    "_last_updated":       None,   # internal
    "_checksum":           None,   # internal tamper detection
}

SENSITIVE_FIELDS = {"ssn", "bank_routing", "bank_account", "state_id_number", "passport_number"}

# ── Vault checksum (tamper detection) ─────────────────────────────────────────
def compute_checksum(data: dict) -> str:
    clean = {k: v for k, v in data.items() if not k.startswith("_")}
    raw = json.dumps(clean, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()

# ── Main wizard ───────────────────────────────────────────────────────────────
def run_new_vault():
    clear()
    header()
    print("""  This wizard will walk you through entering your identity information.
  Everything stays on YOUR computer — encrypted with YOUR password.
  
  ⚠️  IMPORTANT: Choose a strong password you will remember.
      If you forget it, there is no recovery. The vault cannot be
      decrypted without it. (This is a feature, not a bug.)
  
  ⚠️  Fields marked (optional) can be skipped — but more fields = more
      capabilities. You can always update the vault later.
""")

    if not confirm("Ready to begin?"):
        print("\n  Cancelled. Run this wizard again when ready.\n")
        return

    # Password setup
    section("🔑 SET YOUR VAULT PASSWORD")
    print("  This password encrypts everything. Never stored anywhere.\n")
    while True:
        pw1 = getpass.getpass("  Choose a vault password: ")
        pw2 = getpass.getpass("  Confirm vault password:  ")
        if pw1 == pw2 and len(pw1) >= 12:
            password = pw1
            print("  ✅ Password accepted.")
            break
        elif len(pw1) < 12:
            print("  ❌ Password must be at least 12 characters. Try again.")
        else:
            print("  ❌ Passwords don't match. Try again.")

    vault = {
        "_vault_version": "1.0",
        "_created": datetime.now().isoformat(),
        "_last_updated": datetime.now().isoformat(),
    }

    # Identity
    section("👤 IDENTITY")
    vault["full_legal_name"]  = ask("Full legal name (as on government ID)")
    vault["preferred_name"]   = ask("Preferred/chosen name", optional=True)
    vault["date_of_birth"]    = ask("Date of birth (MM/DD/YYYY)")
    vault["place_of_birth"]   = ask("City, State of birth", optional=True)

    # Government IDs
    section("🪪 GOVERNMENT IDs")
    print("  (These are stored encrypted. Only legal document tools read them.)\n")
    vault["ssn"]              = ask("Social Security Number", secret=True)
    vault["state_id_number"]  = ask("State ID / Driver's License number", secret=True)
    vault["state_id_state"]   = ask("Which state issued the ID (2-letter, e.g. TX)")
    vault["state_id_expiry"]  = ask("ID expiry date (MM/DD/YYYY)")
    vault["passport_number"]  = ask("Passport number", secret=True, optional=True)

    # Address
    section("🏠 ADDRESS")
    vault["address_line1"]    = ask("Street address")
    vault["address_line2"]    = ask("Apt/Unit", optional=True)
    vault["city"]             = ask("City")
    vault["state"]            = ask("State (2-letter)")
    vault["zip_code"]         = ask("ZIP code")
    vault["county"]           = ask("County (needed for court filings)", optional=True)

    # Contact
    section("📞 CONTACT")
    vault["phone_primary"]    = ask("Primary phone number")
    vault["phone_secondary"]  = ask("Secondary phone", optional=True)
    vault["email_primary"]    = ask("Primary email")
    vault["email_legal"]      = ask("Email for legal/official mail (if different)", optional=True)

    # Financial
    section("🏦 BANKING (optional — needed for direct deposit forms, benefits)")
    if confirm("Add banking info?"):
        vault["bank_name"]      = ask("Bank name")
        vault["bank_routing"]   = ask("Routing number", secret=True)
        vault["bank_account"]   = ask("Account number", secret=True)
    
    # Legal/Professional
    section("⚖️ LEGAL & PROFESSIONAL")
    vault["occupation"]       = ask("Occupation or job title")
    vault["employer_name"]    = ask("Employer name", optional=True)
    vault["employer_address"] = ask("Employer address", optional=True)
    vault["monthly_income"]   = ask("Approximate monthly income (for benefits screening, e.g. 2500)", optional=True)
    vault["household_size"]   = ask("Number of people in your household (including you)")

    # Signature
    section("✍️  SIGNATURE")
    print("  If you have a signature image (PNG), enter its full path.")
    print("  This gets embedded in generated legal documents.\n")
    vault["signature_image_path"] = ask("Path to signature image (optional)", optional=True)

    # Checksum + finalize
    vault["_checksum"] = compute_checksum(vault)

    # Confirm and encrypt
    section("🔒 ENCRYPTING YOUR VAULT")
    print(f"\n  Vault will be saved to: {VAULT_FILE}")
    print(f"  Salt file saved to:     {SALT_FILE}")
    print("""
  These files contain ONLY encrypted data.
  Without your password, they are meaningless noise.
  
  Keep identity_vault.enc and identity_vault.salt TOGETHER.
  Back them up together to an encrypted USB drive.
  NEVER commit them to any git repo.
""")

    if not confirm("Encrypt and save vault?"):
        print("\n  Cancelled. Nothing was saved.\n")
        return

    encrypted = encrypt_vault(vault, password)
    VAULT_FILE.write_bytes(encrypted)

    print(f"""
  ✅ VAULT CREATED SUCCESSFULLY
  
  Location:    {VAULT_FILE}
  Salt:        {SALT_FILE}
  Fields saved: {len([v for v in vault.values() if v and not str(v).startswith('_')])}
  Checksum:    {vault['_checksum'][:16]}...
  
  Your identity vault is ready. The legal engine, benefits scanner,
  and document generator can now run with your real identity.
  
  NEXT STEPS:
    1. Run LEGAL_ENGINE.py to generate legal documents
    2. Run BENEFITS_SCANNER.py to find programs you qualify for
    3. Run AUTONOMOUS_FILER.py to submit documents automatically
""")

def run_update_vault():
    clear()
    header()
    section("🔄 UPDATE EXISTING VAULT")
    print(f"\n  Vault found at: {VAULT_FILE}\n")

    password = getpass.getpass("  Enter your vault password to unlock: ")
    vault = decrypt_vault(password)

    if vault is None:
        print("\n  ❌ Incorrect password. Cannot open vault.\n")
        return

    # Verify checksum
    stored_checksum = vault.get("_checksum", "")
    computed = compute_checksum(vault)
    if stored_checksum != computed:
        print("\n  ⚠️  WARNING: Vault checksum mismatch. The file may have been tampered with.")
        if not confirm("Continue anyway?"):
            return

    print(f"\n  ✅ Vault unlocked. {len([v for k,v in vault.items() if v and not k.startswith('_')])} fields loaded.")
    print("\n  Which field do you want to update? (Enter field name or 'list' to see all)\n")

    field_map = {k: v for k, v in VAULT_FIELDS.items() if v is not None}

    while True:
        cmd = input("  Field name (or 'done'): ").strip().lower()
        if cmd == 'done':
            break
        if cmd == 'list':
            for k, v in field_map.items():
                current = "✅ set" if vault.get(k) else "○ empty"
                print(f"    {k:<30} {current}  — {v}")
            continue
        if cmd in field_map:
            is_sensitive = cmd in SENSITIVE_FIELDS
            new_val = ask(f"New value for {cmd}", secret=is_sensitive, optional=True)
            if new_val:
                vault[cmd] = new_val
                print(f"  ✅ Updated {cmd}")
        else:
            print(f"  ❌ Unknown field: {cmd}. Type 'list' to see all fields.")

    # Re-checksum and re-encrypt
    vault["_last_updated"] = datetime.now().isoformat()
    vault["_checksum"] = compute_checksum(vault)
    encrypted = encrypt_vault(vault, password)
    VAULT_FILE.write_bytes(encrypted)
    print(f"\n  ✅ Vault updated and re-encrypted.\n")

def run_verify_vault():
    clear()
    header()
    section("🔍 VERIFY VAULT INTEGRITY")
    password = getpass.getpass("\n  Enter your vault password: ")
    vault = decrypt_vault(password)
    if vault is None:
        print("\n  ❌ Incorrect password or corrupted vault.\n")
        return

    stored  = vault.get("_checksum", "")
    computed = compute_checksum(vault)
    match = stored == computed

    print(f"""
  Vault file:     {VAULT_FILE}
  Created:        {vault.get('_created', 'unknown')}
  Last updated:   {vault.get('_last_updated', 'unknown')}
  Fields set:     {len([v for k,v in vault.items() if v and not k.startswith('_')])}
  Checksum match: {"✅ VALID — vault has not been tampered with" if match else "❌ MISMATCH — vault may have been modified"}
  
  Fields present:
""")
    for k, label in VAULT_FIELDS.items():
        if label is None:
            continue
        val = vault.get(k)
        if k in SENSITIVE_FIELDS:
            display = "●●●●●●●● (sensitive, hidden)" if val else "○ not set"
        else:
            display = f"✅ {val}" if val else "○ not set"
        print(f"    {k:<30} {display}")

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    clear()
    header()

    if VAULT_FILE.exists():
        print(f"  ✅ Existing vault found at: {VAULT_FILE}\n")
        print("  What would you like to do?\n")
        print("    1. Update existing vault")
        print("    2. Verify vault integrity")
        print("    3. Create new vault (OVERWRITES existing)")
        print("    4. Exit\n")
        choice = input("  Choice [1-4]: ").strip()
        if choice == "1":
            run_update_vault()
        elif choice == "2":
            run_verify_vault()
        elif choice == "3":
            if confirm("This will OVERWRITE your existing vault. Are you absolutely sure?"):
                run_new_vault()
        else:
            print("\n  Goodbye.\n")
    else:
        print("  No vault found. Starting setup wizard...\n")
        run_new_vault()
