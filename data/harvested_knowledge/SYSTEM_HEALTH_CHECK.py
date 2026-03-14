"""
MEEKO MYCELIUM - MASTER SYSTEM HEALTH CHECK
Runs a full diagnostic on every component of your system.
Run this anytime to get a complete status report.
"""
import os
import sys
import json
import sqlite3
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

DESKTOP = Path(r'C:\Users\meeko\Desktop')
NOW = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

results = {
    "timestamp": NOW,
    "components": {},
    "warnings": [],
    "ok": []
}

def check(name):
    def decorator(fn):
        try:
            status = fn()
            results["components"][name] = {"status": "OK", "detail": status}
            results["ok"].append(name)
        except Exception as e:
            results["components"][name] = {"status": "FAIL", "detail": str(e)}
            results["warnings"].append(f"{name}: {e}")
        return fn
    return decorator

print("\n" + "="*60)
print("  MEEKO MYCELIUM - FULL SYSTEM DIAGNOSTIC")
print(f"  {NOW}")
print("="*60)

# ── 1. PYTHON ──────────────────────────────────────────────
print("\n[1/10] Checking Python...")
v = sys.version.split()[0]
results["components"]["Python"] = {"status": "OK", "detail": v}
results["ok"].append("Python")
print(f"  OK: Python {v}")

# ── 2. OLLAMA / LOCAL AI ───────────────────────────────────
print("[2/10] Checking Ollama + local models...")
try:
    r = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
    models = [line.split()[0] for line in r.stdout.strip().split('\n')[1:] if line.strip()]
    results["components"]["Ollama"] = {"status": "OK", "detail": f"{len(models)} models: {', '.join(models)}"}
    results["ok"].append("Ollama")
    print(f"  OK: {len(models)} models loaded: {', '.join(models)}")
except Exception as e:
    results["components"]["Ollama"] = {"status": "FAIL", "detail": str(e)}
    results["warnings"].append(f"Ollama: {e}")
    print(f"  WARN: {e}")

# ── 3. VIRTUAL ENVIRONMENT ─────────────────────────────────
print("[3/10] Checking virtual environment...")
venv = DESKTOP / 'mycelium_env' / 'Scripts' / 'python.exe'
if venv.exists():
    results["components"]["VirtualEnv"] = {"status": "OK", "detail": str(venv)}
    results["ok"].append("VirtualEnv")
    print(f"  OK: mycelium_env found")
else:
    results["components"]["VirtualEnv"] = {"status": "FAIL", "detail": "Not found"}
    results["warnings"].append("VirtualEnv: mycelium_env missing - run: python -m venv mycelium_env")
    print(f"  FAIL: mycelium_env not found")

# ── 4. CREWAI ──────────────────────────────────────────────
print("[4/10] Checking CrewAI...")
try:
    r = subprocess.run([str(venv), '-c', 'import crewai; print(crewai.__version__)'],
                      capture_output=True, text=True, timeout=15)
    if r.returncode == 0:
        ver = r.stdout.strip()
        results["components"]["CrewAI"] = {"status": "OK", "detail": f"v{ver}"}
        results["ok"].append("CrewAI")
        print(f"  OK: CrewAI v{ver}")
    else:
        raise Exception(r.stderr.strip())
except Exception as e:
    results["components"]["CrewAI"] = {"status": "FAIL", "detail": str(e)}
    results["warnings"].append(f"CrewAI: {e}")
    print(f"  WARN: {e}")

# ── 5. GAZA ROSE DATABASE ──────────────────────────────────
print("[5/10] Checking Gaza Rose database...")
db_paths = [
    DESKTOP / 'UltimateAI_Master' / 'gaza_rose.db',
    DESKTOP / 'New' / 'gaza_rose.db'
]
db_ok = []
for db_path in db_paths:
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            conn.close()
            db_ok.append(f"{db_path.parent.name}/gaza_rose.db ({len(tables)} tables)")
        except Exception as e:
            pass
if db_ok:
    results["components"]["GazaRoseDB"] = {"status": "OK", "detail": "; ".join(db_ok)}
    results["ok"].append("GazaRoseDB")
    print(f"  OK: {'; '.join(db_ok)}")
else:
    results["components"]["GazaRoseDB"] = {"status": "WARN", "detail": "DB not found"}
    results["warnings"].append("GazaRoseDB: Database files not found")
    print(f"  WARN: No database found")

# ── 6. GALLERY ART ─────────────────────────────────────────
print("[6/10] Checking Gaza Rose Gallery...")
art_dir = DESKTOP / 'GAZA_ROSE_GALLERY' / 'art'
gallery_html = DESKTOP / 'GAZA_ROSE_GALLERY' / 'index.html'
art_count = 0
if art_dir.exists():
    art_count = len([f for f in os.listdir(art_dir) if f.lower().endswith(('.jpg','.jpeg','.png'))])
gallery_ok = gallery_html.exists()
results["components"]["Gallery"] = {
    "status": "OK" if art_count > 0 and gallery_ok else "WARN",
    "detail": f"{art_count} artworks, HTML: {'OK' if gallery_ok else 'MISSING'}"
}
if art_count > 0:
    results["ok"].append("Gallery")
    print(f"  OK: {art_count} artworks in gallery, HTML present: {gallery_ok}")
else:
    results["warnings"].append("Gallery: No art images found")
    print(f"  WARN: Gallery empty!")

# ── 7. GUMROAD PRODUCTS ────────────────────────────────────
print("[7/10] Checking Gumroad product listings...")
listings = DESKTOP / 'GUMROAD_PRODUCT_LISTINGS.txt'
playbooks_dir = DESKTOP / 'New' / 'New folder'
pdf_count = 0
if playbooks_dir.exists():
    pdf_count = len([f for f in os.listdir(playbooks_dir) if f.endswith('.pdf')])
listings_ok = listings.exists()
results["components"]["GumroadProducts"] = {
    "status": "OK" if listings_ok else "WARN",
    "detail": f"Listings file: {'OK' if listings_ok else 'MISSING'}, PDFs ready: {pdf_count}"
}
results["ok"].append("GumroadProducts")
print(f"  OK: {pdf_count} PDFs ready, listings file: {listings_ok}")

# ── 8. PCRF DONATION LINK ──────────────────────────────────
print("[8/10] Verifying PCRF donation link...")
try:
    req = urllib.request.Request(
        'https://give.pcrf.net/campaign/739651/donate',
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    resp = urllib.request.urlopen(req, timeout=10)
    code = resp.getcode()
    results["components"]["PCRFLink"] = {"status": "OK", "detail": f"HTTP {code} - Link is live"}
    results["ok"].append("PCRFLink")
    print(f"  OK: PCRF donation link is live (HTTP {code})")
except Exception as e:
    results["components"]["PCRFLink"] = {"status": "WARN", "detail": f"Could not reach: {e}"}
    results["warnings"].append(f"PCRFLink: {e}")
    print(f"  WARN: Could not verify PCRF link: {e}")

# ── 9. ULTIMATEAI MASTER ───────────────────────────────────
print("[9/10] Checking UltimateAI Master...")
master = DESKTOP / 'UltimateAI_Master' / 'ultimate_ai_master_v15.py'
subsystems = DESKTOP / 'UltimateAI_Master' / 'subsystems'
subsys_count = len(list(subsystems.glob('*.py'))) if subsystems.exists() else 0
crypto_connector = DESKTOP / 'UltimateAI_Master' / 'connect_crypto.py'
if master.exists():
    results["components"]["UltimateAI"] = {"status": "OK", "detail": f"v15 present, {subsys_count} subsystems, crypto connector: {'OK' if crypto_connector.exists() else 'MISSING'}"}
    results["ok"].append("UltimateAI")
    print(f"  OK: ultimate_ai_master_v15.py, {subsys_count} subsystems, crypto connector: {crypto_connector.exists()}")
else:
    results["components"]["UltimateAI"] = {"status": "FAIL", "detail": "Master script not found"}
    results["warnings"].append("UltimateAI: Master script missing")
    print(f"  FAIL: Master script not found")

# ── 9b. CRYPTO CONFIG ──────────────────────────────────────
print("[9b] Checking crypto configuration...")
try:
    db_path = DESKTOP / 'UltimateAI_Master' / 'gaza_rose.db'
    conn = sqlite3.connect(str(db_path))
    phantom = conn.execute("SELECT value FROM crypto_config WHERE key='phantom_address'").fetchone()
    conn.close()
    if phantom:
        addr = phantom[0]
        short = f"{addr[:8]}...{addr[-6:]}"
        results["components"]["CryptoConfig"] = {"status": "OK", "detail": f"Phantom address on file: {short}"}
        results["ok"].append("CryptoConfig")
        print(f"  OK: Phantom address configured ({short})")
    else:
        results["components"]["CryptoConfig"] = {"status": "WARN", "detail": "No crypto configured yet - run connect_crypto.py"}
        results["warnings"].append("CryptoConfig: Run connect_crypto.py to set up Coinbase + Phantom")
        print(f"  WARN: No crypto configured yet - run connect_crypto.py")
except Exception as e:
    results["components"]["CryptoConfig"] = {"status": "WARN", "detail": str(e)}
    print(f"  WARN: Could not check crypto config: {e}")

# ── 10. WALLET SAFETY CHECK ────────────────────────────────
print("[10/10] Verifying no old wallet addresses remain...")
old_wallet = "bc1qctk9vwlckh2sl6zm7l3y08" + "mgem9gt8u3vlkeu"  # split so this file doesn't self-detect
THIS_SCRIPT = os.path.abspath(__file__)
found_in = []
for root, dirs, files in os.walk(DESKTOP):
    dirs[:] = [d for d in dirs if d not in ['mycelium_env', 'node_modules', '__pycache__', '.git']]
    for f in files:
        if not f.endswith(('.exe','.zip','.db','.png','.jpg','.jpeg','.pdf','.pyc')):
            try:
                path = os.path.join(root, f)
                if os.path.abspath(path) == THIS_SCRIPT:
                    continue
                content = open(path, 'r', encoding='utf-8', errors='ignore').read()
                if old_wallet in content:
                    found_in.append(path.replace(str(DESKTOP), ''))
            except:
                pass

if found_in:
    results["components"]["WalletSafety"] = {"status": "FAIL", "detail": f"OLD WALLET FOUND IN: {found_in}"}
    results["warnings"].append(f"OLD WALLET STILL IN {len(found_in)} FILES - run fix_pcrf.py again!")
    print(f"  FAIL: Old wallet found in {len(found_in)} files!")
    for f in found_in:
        print(f"    {f}")
else:
    results["components"]["WalletSafety"] = {"status": "OK", "detail": "No old wallet addresses found"}
    results["ok"].append("WalletSafety")
    print(f"  OK: No old wallet addresses in any files")

# ── FINAL REPORT ───────────────────────────────────────────
total = len(results["components"])
ok_count = len(results["ok"])
warn_count = len(results["warnings"])

print("\n" + "="*60)
print(f"  SYSTEM HEALTH: {ok_count}/{total} components OK")
print("="*60)

if results["warnings"]:
    print(f"\n  WARNINGS ({warn_count}):")
    for w in results["warnings"]:
        print(f"    * {w}")
else:
    print("\n  ALL SYSTEMS HEALTHY - READY TO LAUNCH")

# Save report
report = DESKTOP / f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(report, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\n  Report saved: {report.name}")
print("="*60 + "\n")
