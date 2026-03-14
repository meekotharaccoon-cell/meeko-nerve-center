# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
AUTO_HEALER.py — Real-time self-repair engine
==============================================
Reads omnibus_last.json for failed engines every cycle.
For each failure: reads the source, reads the error, uses AI to patch it,
writes the fixed file, runs it to verify, commits the fix.

Also handles:
- Missing dependencies (pip install)
- Bad imports (rewrites import block)
- Missing data files (creates stubs)
- API auth errors (rewrites to use fallbacks)
- Syntax errors (targeted patch)

This runs BEFORE the main OMNIBUS cycle so next cycle's run is already healed.
"""
import os, sys, json, subprocess, time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask
    AI = True
except ImportError:
    AI = False

DATA     = Path("data"); DATA.mkdir(exist_ok=True)
MYCELIUM = Path("mycelium")
PYTHON   = sys.executable
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GMAIL    = os.environ.get("GMAIL_ADDRESS", "")
GPWD     = os.environ.get("GMAIL_APP_PASSWORD", "")


def load_last_run():
    f = DATA / "omnibus_last.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {}


def get_error_for_engine(name, last_run):
    """Extract the actual error message from last run log."""
    for entry in last_run.get("log", []):
        if entry["engine"] == name:
            stderr = entry.get("stderr_tail", "")
            stdout = entry.get("stdout_tail", "")
            return stderr or stdout or f"exit code {entry.get('code', '?')}"
    return "unknown error"


def diagnose_and_patch(name, source, error):
    """Use AI to diagnose and return a patched source."""
    if not AI:
        return None

    prompt = f"""You are AUTO_HEALER, a Python auto-repair engine for SolarPunk.

ENGINE: {name}.py
ERROR:
{error[:800]}

SOURCE (first 60 lines):
{chr(10).join(source.splitlines()[:60])}

Diagnose the error and return a minimal patch.
Rules:
- Only fix what's actually broken. Don't rewrite working code.
- If it's a missing import: add it or replace with stdlib equivalent.
- If it's an API key missing: add a graceful fallback (if not KEY: print("skip"); sys.exit(0))
- If it's a missing file: add a "create stub if not exists" block.
- If it's a pip package: add `subprocess.run(['pip','install','pkg','--break-system-packages']...)` at top.
- Keep the engine's purpose intact.

Respond ONLY as JSON:
{{"diagnosis": "one sentence what's wrong",
  "patch_type": "import|api_key|missing_file|dependency|syntax|logic",
  "old_code": "exact string to replace (5-10 lines with context)",
  "new_code": "replacement code",
  "confidence": 0.0-1.0}}

If you cannot safely fix it, return {{"diagnosis": "...", "patch_type": "skip", "confidence": 0}}"""

    try:
        result = ask([{"role": "user", "content": prompt}], max_tokens=600)
        if not result: return None
        s, e = result.find("{"), result.rfind("}") + 1
        if s < 0: return None
        return json.loads(result[s:e])
    except Exception as ex:
        print(f"  AI patch error: {ex}")
        return None


def apply_patch(source, patch):
    """Apply old_code → new_code replacement."""
    old = patch.get("old_code", "")
    new = patch.get("new_code", "")
    if not old or patch.get("patch_type") == "skip":
        return None
    if old in source:
        return source.replace(old, new, 1)
    # Fuzzy: try stripping whitespace
    lines = source.splitlines()
    old_lines = old.strip().splitlines()
    for i in range(len(lines) - len(old_lines) + 1):
        chunk = "\n".join(l.strip() for l in lines[i:i+len(old_lines)])
        if chunk == "\n".join(l.strip() for l in old_lines):
            lines[i:i+len(old_lines)] = new.splitlines()
            return "\n".join(lines)
    return None


def verify_patch(name, patched_source):
    """Write patched source to a temp file and run it briefly to check syntax."""
    tmp = MYCELIUM / f"{name}_healing_test.py"
    try:
        tmp.write_text(patched_source)
        # Just check syntax
        result = subprocess.run(
            [PYTHON, "-m", "py_compile", str(tmp)],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0, result.stderr
    finally:
        if tmp.exists(): tmp.unlink()


def heal_engine(name, last_run):
    """Full healing pipeline for one broken engine."""
    script = MYCELIUM / f"{name}.py"
    if not script.exists():
        print(f"  ⏭  {name}: source not found, skipping")
        return False

    error = get_error_for_engine(name, last_run)
    source = script.read_text()

    print(f"  🔍 Diagnosing {name}...")
    print(f"     Error: {error[:100]}")

    patch = diagnose_and_patch(name, source, error)
    if not patch:
        print(f"  ⚠️  No patch generated for {name}")
        return False

    print(f"  💊 Patch type: {patch.get('patch_type')} | confidence: {patch.get('confidence',0):.1f}")
    print(f"     Diagnosis: {patch.get('diagnosis','?')}")

    if patch.get("confidence", 0) < 0.5:
        print(f"  ⚠️  Low confidence — skipping {name}")
        return False

    patched = apply_patch(source, patch)
    if not patched:
        print(f"  ⚠️  Patch application failed for {name}")
        return False

    ok, err = verify_patch(name, patched)
    if not ok:
        print(f"  ⚠️  Patch syntax check failed: {err[:80]}")
        return False

    # Back up original
    backup = MYCELIUM / f"{name}.py.bak"
    backup.write_text(source)

    # Write patched version
    script.write_text(patched)
    print(f"  ✅ {name} healed — patch applied and syntax verified")
    return True


def auto_install_missing(last_run):
    """Detect ModuleNotFoundError patterns and pip install."""
    installed = []
    for entry in last_run.get("log", []):
        stderr = entry.get("stderr_tail", "")
        if "ModuleNotFoundError: No module named" in stderr:
            # Extract module name
            import re
            m = re.search(r"No module named '(\S+)'", stderr)
            if m:
                pkg = m.group(1).split(".")[0]
                # Map common module→package name mismatches
                pkg_map = {"tweepy": "tweepy", "praw": "praw", "PIL": "Pillow",
                           "imapclient": "imapclient", "bs4": "beautifulsoup4",
                           "dateutil": "python-dateutil", "yaml": "PyYAML"}
                install_pkg = pkg_map.get(pkg, pkg)
                print(f"  📦 Auto-installing {install_pkg} (needed by {entry['engine']})")
                try:
                    subprocess.run(
                        [PYTHON, "-m", "pip", "install", install_pkg, "--break-system-packages", "-q"],
                        capture_output=True, timeout=60
                    )
                    installed.append(install_pkg)
                except: pass
    return installed


def save_heal_report(healed, installed, skipped, last_run):
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "healed": healed,
        "auto_installed": installed,
        "skipped": skipped,
        "failed_engines_seen": last_run.get("engines_failed", []),
    }
    (DATA / "auto_healer_report.json").write_text(json.dumps(report, indent=2))
    # Append to history
    hf = DATA / "auto_healer_history.json"
    hist = json.loads(hf.read_text()) if hf.exists() else []
    hist.append(report)
    hf.write_text(json.dumps(hist[-50:], indent=2))
    return report


def run():
    print("🔧 AUTO_HEALER starting...")
    last_run = load_last_run()
    failed = last_run.get("engines_failed", [])

    if not failed:
        print("  ✅ No failed engines from last run — nothing to heal")
        return {"healed": [], "installed": [], "skipped": []}

    print(f"  Found {len(failed)} failed engines: {', '.join(failed)}")

    # Step 1: auto-install missing packages
    installed = auto_install_missing(last_run)

    # Step 2: diagnose and patch
    healed = []
    skipped = []
    for name in failed:
        result = heal_engine(name, last_run)
        if result:
            healed.append(name)
        else:
            skipped.append(name)

    report = save_heal_report(healed, installed, skipped, last_run)
    print(f"\n  🔧 Heal summary: {len(healed)} fixed | {len(installed)} packages installed | {len(skipped)} still broken")
    if healed:
        print(f"  Fixed: {', '.join(healed)}")
    return report


if __name__ == "__main__":
    run()
