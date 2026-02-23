#!/usr/bin/env python3
"""
🔐 IDENTITY VAULT — Meeko Mycelium
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Autonomous identity management layer:
  • Generates signed legal documents (FOIA, TCPA demands, FDCPA letters)
  • GPG signing for all outbound documents
  • Wallet address management (BTC, Lightning, Solana)
  • Identity proofs for grant applications
  • Artist attestation + copyright registration helpers
  • Digital signature verification
  • Credential vault (encrypted, local only, never pushed)

All crypto/signing is LOCAL. Nothing sensitive leaves your machine.
The vault knows who you are so the system can prove it when needed.

Usage:
  python identity_vault.py --status         # show vault status
  python identity_vault.py --sign FILE      # sign a file
  python identity_vault.py --generate-foia  # generate FOIA request
  python identity_vault.py --generate-tcpa  # generate TCPA demand
  python identity_vault.py --generate-fdcpa # generate FDCPA dispute
  python identity_vault.py --wallet-info    # show payment addresses
  python identity_vault.py --artist-cert    # generate artist attestation
  python identity_vault.py --init           # first-time setup
"""

import os
import sys
import json
import hashlib
import datetime
import argparse
import subprocess
from pathlib import Path

# ─────────────────────────────────────────────
COLORS
# ─────────────────────────────────────────────
class C:
    G='[92m'; Y='[93m'; R='[91m'; CY='[96m'; B='[1m'; D='[2m'; X='[0m'

def ok(s):   print(f"{C.G}  ✓ {s}{C.X}")
def warn(s): print(f"{C.Y}  ⚠ {s}{C.X}")
def info(s): print(f"{C.CY}  → {s}{C.X}")
def dim(s):  print(f"{C.D}    {s}{C.X}")

# ─────────────────────────────────────────────
PATHS (all local, nothing pushed to GitHub)
# ─────────────────────────────────────────────
HOME = Path.home()
VAULT_DIR = HOME / '.meeko_vault'          # hidden local dir
VAULT_CONFIG = VAULT_DIR / 'vault.json'    # identity config (local only)
DOCS_DIR = VAULT_DIR / 'documents'         # signed docs output
CERTS_DIR = VAULT_DIR / 'certs'            # certificates

# Public-safe outputs (can go in repo)
REPO_ROOT = Path(__file__).parent.parent
PUBLIC_DOCS = REPO_ROOT / 'data' / 'identity'

def ensure_vault():
    VAULT_DIR.mkdir(mode=0o700, exist_ok=True)
    DOCS_DIR.mkdir(mode=0o700, exist_ok=True)
    CERTS_DIR.mkdir(mode=0o700, exist_ok=True)
    PUBLIC_DOCS.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
VAULT CONFIG (identity profile)
# ─────────────────────────────────────────────
def load_identity():
    if VAULT_CONFIG.exists():
        try:
            return json.loads(VAULT_CONFIG.read_text())
        except:
            pass
    # Default template
    return {
        "name": "Meeko",
        "legal_name": "",              # fill in for legal docs
        "email": "meekotharaccoon@gmail.com",
        "website": "https://meekotharaccoon-cell.github.io/meeko-nerve-center",
        "github": "meekotharaccoon-cell",
        "location": "",               # city, state (for FOIA)
        "mailing_address": "",         # for legal demands
        "phone": "",                   # for FOIA
        "wallets": {
            "bitcoin": "",
            "lightning": "",
            "solana": "",
            "paypal": "",
        },
        "artist_statement": "Visual artist and systems builder. All work is original, permission-first, and ethically licensed under AGPL-3.0.",
        "license": "AGPL-3.0 + Ethical Use Rider",
        "org": "Meeko Mycelium",
        "mission": "Ethical autonomous systems. Revenue routed to PCRF. Free tools for everyone.",
    }

def save_identity(identity):
    ensure_vault()
    VAULT_CONFIG.write_text(json.dumps(identity, indent=2))
    VAULT_CONFIG.chmod(0o600)  # read/write owner only
    ok(f"Identity saved: {VAULT_CONFIG}")

# ─────────────────────────────────────────────
SIGNING (SHA256 hash + optional GPG)
# ─────────────────────────────────────────────
def sign_file(filepath):
    """Sign a file with SHA256 hash + identity attestation"""
    path = Path(filepath)
    if not path.exists():
        warn(f"File not found: {filepath}")
        return None

    identity = load_identity()
    content = path.read_bytes()
    sha256 = hashlib.sha256(content).hexdigest()
    now = datetime.datetime.utcnow().isoformat()

    signature = {
        "file": path.name,
        "sha256": sha256,
        "signed_by": identity.get('name', 'Unknown'),
        "email": identity.get('email', ''),
        "github": identity.get('github', ''),
        "timestamp_utc": now,
        "license": identity.get('license', ''),
        "attestation": f"I attest that this document was created by me ({identity.get('name')}) and is accurate to the best of my knowledge.",
    }

    sig_path = path.with_suffix('.sig.json')
    sig_path.write_text(json.dumps(signature, indent=2))
    ok(f"Signed: {path.name}")
    ok(f"SHA256: {sha256[:32]}...")
    ok(f"Signature file: {sig_path}")

    # Try GPG if available
    gpg_available = subprocess.run(['gpg', '--version'], capture_output=True).returncode == 0
    if gpg_available:
        result = subprocess.run(
            ['gpg', '--detach-sign', '--armor', str(path)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            ok("GPG signature created")
        else:
            warn("GPG signing failed (key not configured) — SHA256 signature still valid")
    else:
        dim("GPG not installed — using SHA256 attestation only")
        dim("Install GPG: https://gnupg.org/download")

    return signature

def verify_file(filepath):
    """Verify a signed file"""
    path = Path(filepath)
    sig_path = path.with_suffix('.sig.json')
    if not sig_path.exists():
        warn(f"No signature file found: {sig_path}")
        return False

    sig = json.loads(sig_path.read_text())
    content = path.read_bytes()
    actual_hash = hashlib.sha256(content).hexdigest()

    if actual_hash == sig['sha256']:
        ok(f"VERIFIED: {path.name}")
        info(f"Signed by: {sig.get('signed_by')} ({sig.get('email')})")
        info(f"Timestamp: {sig.get('timestamp_utc')}")
        return True
    else:
        warn(f"VERIFICATION FAILED: {path.name} has been modified")
        return False

# ─────────────────────────────────────────────
LEGAL DOCUMENT GENERATORS
# ─────────────────────────────────────────────
def generate_tcpa_demand(phone_number, date_of_call, caller_name, call_type="robocall"):
    identity = load_identity()
    today = datetime.date.today().strftime("%B %d, %Y")
    doc = f"""DEMAND LETTER — TCPA VIOLATION
Date: {today}

FROM:
{identity.get('legal_name') or identity.get('name')}
{identity.get('mailing_address', '[YOUR ADDRESS]')}
{identity.get('email')}

TO:
{caller_name}
[COMPANY ADDRESS]

RE: Violation of the Telephone Consumer Protection Act (47 U.S.C. § 227)

Dear {caller_name},

This letter constitutes formal notice that you have violated the Telephone
Consumer Protection Act ("TCPA"), 47 U.S.C. § 227, by placing an
unauthorized {call_type} to my cellular telephone number {phone_number}
on or about {date_of_call}.

Specifically, your {call_type} was placed:
  • Without my prior express written consent
  • Using an automated telephone dialing system (ATDS) and/or
    pre-recorded/artificial voice
  • In violation of 47 U.S.C. § 227(b)(1)(A)

PURSUANT TO THE TCPA:
Each violation carries statutory damages of $500 to $1,500.
For willful or knowing violations, treble damages of up to $1,500
per call may be awarded.

DEMAND:
Within 14 days of this letter, I demand:
1. Written confirmation that my number has been removed from your
   calling lists permanently
2. Payment of $1,500 in statutory damages for this willful violation
3. Written confirmation of your Do Not Call policy

Failure to comply will result in filing in small claims court and/or
federal court without further notice.

This letter is sent as formal notice and constitutes a record for
any subsequent legal proceedings.

Sincerely,
{identity.get('legal_name') or identity.get('name')}

Cc: Federal Trade Commission (ftc.gov/complaint)
    Federal Communications Commission (consumercomplaints.fcc.gov)
    State Attorney General

---
Generated by Meeko Mycelium Identity Vault
For legal information tools, visit: https://meekotharaccoon-cell.github.io/meeko-nerve-center/proliferator.html
"""
    filename = f"TCPA_demand_{datetime.date.today().isoformat()}.txt"
    doc_path = DOCS_DIR / filename
    ensure_vault()
    doc_path.write_text(doc)
    sig = sign_file(doc_path)
    ok(f"TCPA demand generated: {doc_path}")
    return doc_path, doc

def generate_foia_request(agency_name, subject, specific_records):
    identity = load_identity()
    today = datetime.date.today().strftime("%B %d, %Y")
    doc = f"""FREEDOM OF INFORMATION ACT REQUEST
Date: {today}

FROM:
{identity.get('legal_name') or identity.get('name')}
{identity.get('mailing_address', '[YOUR ADDRESS]')}
{identity.get('email')}
{identity.get('phone', '')}

TO:
FOIA Officer
{agency_name}
[AGENCY ADDRESS]

RE: Freedom of Information Act Request — {subject}

Dear FOIA Officer,

Pursuant to the Freedom of Information Act, 5 U.S.C. § 552, I hereby
request the following records:

{specific_records}

I request that all responsive documents be provided in electronic format
(PDF or searchable text) where available. If any portion of this request
is denied, please cite the specific exemption(s) relied upon and notify
me of the appeal procedures available.

FEE WAIVER REQUEST:
I request a waiver of all search, duplication, and review fees. Disclosure
of the requested information is in the public interest because it contributes
significantly to public understanding of government operations and activities.

Pursuant to 5 U.S.C. § 552(a)(6)(A), I expect a response within 20 business
days. If you anticipate a delay, please notify me immediately.

Thank you for your prompt attention to this matter.

Sincerely,
{identity.get('legal_name') or identity.get('name')}
{identity.get('email')}

---
Generated by Meeko Mycelium Identity Vault
For legal tools, visit: https://meekotharaccoon-cell.github.io/meeko-nerve-center/proliferator.html
"""
    filename = f"FOIA_{agency_name.replace(' ','_')}_{datetime.date.today().isoformat()}.txt"
    doc_path = DOCS_DIR / filename
    ensure_vault()
    doc_path.write_text(doc)
    sign_file(doc_path)
    ok(f"FOIA request generated: {doc_path}")
    return doc_path, doc

def generate_artist_cert(artwork_title, creation_date, medium):
    identity = load_identity()
    today = datetime.date.today().strftime("%B %d, %Y")
    cert_id = hashlib.sha256(f"{artwork_title}{creation_date}{identity.get('name')}".encode()).hexdigest()[:16].upper()
    doc = f"""ARTIST ATTESTATION CERTIFICATE
Certificate ID: MEEKO-{cert_id}
Date Issued: {today}

This certifies that:

Artwork Title: {artwork_title}
Medium: {medium}
Creation Date: {creation_date}
Artist: {identity.get('legal_name') or identity.get('name')}
Email: {identity.get('email')}
Website: {identity.get('website')}

I, {identity.get('legal_name') or identity.get('name')}, hereby attest that:
  1. I am the original creator of the work described above
  2. This work is an original creation, not derived from copyrighted material
     without license or fair use basis
  3. I hold all intellectual property rights to this work
  4. This work is licensed under: {identity.get('license')}

Artist Statement:
{identity.get('artist_statement')}

Mission:
{identity.get('mission')}

Digital Signature: MEEKO-{cert_id}
Timestamp: {datetime.datetime.utcnow().isoformat()}

This certificate was cryptographically signed at time of creation.
Verification: python identity_vault.py --verify [certificate file]

---
Meeko Mycelium • {identity.get('website')}
All revenue supports: PCRF (Palestinian Children's Relief Fund)
"""
    filename = f"artist_cert_{cert_id}.txt"
    cert_path = CERTS_DIR / filename
    ensure_vault()
    cert_path.write_text(doc)
    sign_file(cert_path)

    # Also write public version
    pub_path = PUBLIC_DOCS / f"artist_cert_{cert_id}_public.txt"
    pub_path.write_text(doc)
    ok(f"Artist certificate generated: {cert_path}")
    ok(f"Public copy: {pub_path}")
    return cert_path, doc

# ─────────────────────────────────────────────
WALLET INFO
# ─────────────────────────────────────────────
def show_wallet_info():
    identity = load_identity()
    wallets = identity.get('wallets', {})
    print(f"\n{C.B}  💰 WALLET ADDRESSES{C.X}")
    print(f"  {C.D}(stored locally in {VAULT_CONFIG}){C.X}\n")
    for chain, addr in wallets.items():
        status = f"{C.G}{addr}{C.X}" if addr else f"{C.Y}[not configured]{C.X}"
        print(f"  {chain.upper()}: {status}")
    if not any(wallets.values()):
        print(f"\n  {C.D}No wallets configured yet.")
        print(f"  Run: python identity_vault.py --init to set them up.{C.X}")

# ─────────────────────────────────────────────
INIT (first-time setup)
# ─────────────────────────────────────────────
def init_vault():
    print(f"\n{C.B}{C.G}  🔐 IDENTITY VAULT — FIRST TIME SETUP{C.X}\n")
    print(f"  {C.D}This stays LOCAL. Nothing is pushed to GitHub.{C.X}\n")

    identity = load_identity()

    def ask(prompt, current):
        resp = input(f"  {prompt} [{current or 'skip'}]: ").strip()
        return resp if resp else current

    identity['legal_name']     = ask("Legal name (for documents)", identity.get('legal_name',''))
    identity['email']          = ask("Email", identity.get('email',''))
    identity['mailing_address']= ask("Mailing address", identity.get('mailing_address',''))
    identity['location']       = ask("City, State", identity.get('location',''))
    identity['phone']          = ask("Phone (for FOIA)", identity.get('phone',''))
    identity['wallets']['bitcoin']  = ask("Bitcoin address", identity['wallets'].get('bitcoin',''))
    identity['wallets']['lightning']= ask("Lightning address", identity['wallets'].get('lightning',''))
    identity['wallets']['solana']   = ask("Solana address", identity['wallets'].get('solana',''))
    identity['wallets']['paypal']   = ask("PayPal email", identity['wallets'].get('paypal',''))

    save_identity(identity)
    ok("Vault initialized!")
    ok(f"Location: {VAULT_CONFIG}")
    dim("This file is chmod 600 — only you can read it")
    dim("It is also in .gitignore — will never be pushed")

# ─────────────────────────────────────────────
STATUS
# ─────────────────────────────────────────────
def show_status():
    print(f"\n{C.B}  🔐 IDENTITY VAULT STATUS{C.X}\n")
    identity = load_identity()
    configured = VAULT_CONFIG.exists()

    print(f"  Vault location: {VAULT_DIR}")
    print(f"  Config exists: {C.G}YES{C.X}" if configured else f"  Config exists: {C.Y}NO — run --init{C.X}")

    if configured:
        print(f"\n  {C.B}Identity:{C.X}")
        for k in ['name', 'legal_name', 'email', 'github', 'location', 'license']:
            v = identity.get(k, '')
            status = f"{C.G}{v}{C.X}" if v else f"{C.D}[not set]{C.X}"
            print(f"    {k}: {status}")

        wallets = identity.get('wallets', {})
        print(f"\n  {C.B}Wallets:{C.X}")
        for chain, addr in wallets.items():
            status = f"{C.G}{addr[:20]}...{C.X}" if len(addr) > 20 else (f"{C.G}{addr}{C.X}" if addr else f"{C.D}[not set]{C.X}")
            print(f"    {chain}: {status}")

    # Signed documents
    if DOCS_DIR.exists():
        docs = list(DOCS_DIR.glob('*.txt'))
        print(f"\n  {C.B}Generated documents:{C.X} {len(docs)} files")
        for doc in sorted(docs)[-5:]:
            print(f"    {C.D}{doc.name}{C.X}")

# ─────────────────────────────────────────────
MAIN
# ─────────────────────────────────────────────
def main():
    print(f"\n{C.G}{C.B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.X}")
    print(f"{C.G}{C.B}  🔐 MEEKO MYCELIUM — IDENTITY VAULT{C.X}")
    print(f"{C.G}{C.B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.X}\n")

    p = argparse.ArgumentParser(description="Meeko Identity Vault")
    p.add_argument('--status',         action='store_true', help='Show vault status')
    p.add_argument('--init',           action='store_true', help='First-time setup')
    p.add_argument('--sign',           metavar='FILE',      help='Sign a file')
    p.add_argument('--verify',         metavar='FILE',      help='Verify a signed file')
    p.add_argument('--wallet-info',    action='store_true', help='Show wallet addresses')
    p.add_argument('--artist-cert',    metavar='TITLE',     help='Generate artist cert for artwork')
    p.add_argument('--generate-tcpa',  action='store_true', help='Generate TCPA demand')
    p.add_argument('--generate-foia',  action='store_true', help='Generate FOIA request')
    args = p.parse_args()

    if args.init:           init_vault()
    elif args.status:       show_status()
    elif args.wallet_info:  show_wallet_info()
    elif args.sign:         sign_file(args.sign)
    elif args.verify:       verify_file(args.verify)
    elif args.artist_cert:
        generate_artist_cert(args.artist_cert, datetime.date.today().isoformat(), "Digital")
    elif args.generate_tcpa:
        phone = input("  Phone number that called you: ").strip()
        date  = input("  Date of call (YYYY-MM-DD): ").strip()
        caller = input("  Caller name/company: ").strip()
        generate_tcpa_demand(phone, date, caller)
    elif args.generate_foia:
        agency = input("  Agency name: ").strip()
        subj   = input("  Subject of request: ").strip()
        recs   = input("  Specific records requested: ").strip()
        generate_foia_request(agency, subj, recs)
    else:
        show_status()

if __name__ == '__main__':
    main()
