# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
GUARDIAN.py — SolarPunk Immune System v2
=========================================
Runs FIRST on every OMNIBRAIN cycle.
• Git tag save-state BEFORE anything runs
• Integrity check: all core files present?
• Auto-restore from last good save-state tag
• Emergency email to Meeko on breach
• Blocks the wipe from EVER happening again
"""
import os, json, subprocess, smtplib
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText

CORE_FILES = [
    ".github/workflows/OMNIBRAIN.yml",
    ".github/workflows/SOLARPUNK_LOOP.yml",
    "mycelium/GUARDIAN.py",
    "mycelium/NEURON_A.py",
    "mycelium/NEURON_B.py",
    "mycelium/SYNAPSE.py",
    "mycelium/INCOME_ARCHITECT.py",
    "mycelium/ART_GENERATOR.py",
    "mycelium/REVENUE_FLYWHEEL.py",
    "mycelium/SYNTHESIS_FACTORY.py",
]
DATA_DIR = Path("data")
LOG_FILE = DATA_DIR / "guardian_log.json"

def runcmd(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout.strip(), r.returncode

def alert(subject, body):
    gmail = os.environ.get("GMAIL_ADDRESS","")
    pwd   = os.environ.get("GMAIL_APP_PASSWORD","")
    if not gmail or not pwd:
        print(f"[GUARDIAN ALERT] {subject}")
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = f"🛡️ GUARDIAN: {subject}"
        msg["From"] = gmail; msg["To"] = gmail
        import smtplib
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
            s.login(gmail,pwd); s.send_message(msg)
    except Exception as e:
        print(f"Alert email failed: {e}")

def log(etype, details):
    DATA_DIR.mkdir(exist_ok=True)
    entries = []
    if LOG_FILE.exists():
        try: entries = json.loads(LOG_FILE.read_text())
        except: pass
    entries.append({"ts": datetime.now().isoformat(), "type": etype, "details": details})
    LOG_FILE.write_text(json.dumps(entries[-500:], indent=2))

def save_state():
    tag = f"save-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    runcmd(f"git tag {tag} 2>/dev/null || true")
    runcmd(f"git push origin {tag} 2>/dev/null || true")
    log("SAVE_STATE", {"tag": tag})
    print(f"💾 Save-state: {tag}")
    return tag

def check():
    return [f for f in CORE_FILES if not Path(f).exists()]

def best_restore_tag():
    tags, _ = runcmd("git tag --sort=-version:refname 2>/dev/null")
    for tag in tags.splitlines():
        if "save-" not in tag: continue
        out, _ = runcmd(f"git show {tag}:.github/workflows/OMNIBRAIN.yml 2>/dev/null")
        if out and len(out) > 200:
            return tag
    return None

def restore(tag):
    ok, fail = [], []
    for f in CORE_FILES:
        out, code = runcmd(f"git show {tag}:{f} 2>/dev/null")
        if code == 0 and out and len(out) > 20:
            p = Path(f); p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(out); ok.append(f)
        else:
            fail.append(f)
    return ok, fail

def main():
    DATA_DIR.mkdir(exist_ok=True)
    print("🛡️  GUARDIAN — SolarPunk Immune System")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    tag = save_state()
    missing = check()
    status = {"ts": datetime.now().isoformat(), "status": "OK", "missing": missing, "tag": tag}
    if not missing:
        print(f"✅ All {len(CORE_FILES)} core files intact")
        log("OK", {"checked": len(CORE_FILES)})
    else:
        print(f"🚨 BREACH: {len(missing)} files missing!")
        for f in missing: print(f"   ✗ {f}")
        log("BREACH", {"missing": missing})
        good = best_restore_tag()
        if good:
            print(f"🔄 Restoring from {good}…")
            ok, fail = restore(good)
            runcmd("git add -A")
            runcmd(f'git commit -m "🛡️ GUARDIAN: restored {len(ok)} files from {good}"')
            runcmd("git push origin main 2>/dev/null || git push origin main --force-with-lease 2>/dev/null")
            log("RESTORED", {"tag": good, "ok": ok, "fail": fail})
            alert(f"Auto-restored {len(ok)} files",
                  f"Breach detected. Restored from {good}.\nMissing: {missing}\nRestored: {ok}\nFailed: {fail}\n\nSystem healed itself. ✊\n— GUARDIAN")
            status["status"] = "RESTORED"
        else:
            alert("BREACH — no save-state found", f"Missing: {missing}\nNo restore tag found. Manual fix needed.")
            status["status"] = "BREACH"
    (DATA_DIR / "guardian_status.json").write_text(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()
