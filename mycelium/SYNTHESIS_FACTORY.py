# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
SYNTHESIS_FACTORY — Auto-builds new engines using free AI (HuggingFace)
PATCHED v3: Uses AI_CLIENT.py (HF free tier) instead of Anthropic API.
Hard boundaries. Can NEVER touch .github/ or delete existing files.
Only creates NEW .py files in mycelium/ and writes to data/.
"""
import os, json, subprocess, sys
from pathlib import Path
from datetime import datetime

# Import shared AI client
sys.path.insert(0, str(Path(__file__).parent))
try:
    from AI_CLIENT import ask_json
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("  AI_CLIENT not found")

FORBIDDEN_PATHS = [".github", ".git", "GUARDIAN", "OMNIBRAIN", "SOLARPUNK_LOOP", "BUILD_YOURSELF"]
ALLOWED_DIRS    = ["mycelium", "data"]

def safe_to_write(filepath):
    fp = filepath.replace("\\", "/").lower()
    for forbidden in FORBIDDEN_PATHS:
        if forbidden.lower() in fp:
            print(f"⛔ BLOCKED write to forbidden path: {filepath}")
            return False
    for allowed in ALLOWED_DIRS:
        if fp.startswith(allowed + "/") or fp.startswith("./" + allowed + "/"):
            return True
    print(f"⛔ BLOCKED write outside allowed dirs: {filepath}")
    return False

def safe_git_add_only():
    subprocess.run(["git", "add", "mycelium/", "data/"], capture_output=True)

def get_gen_number():
    log_f = Path("data/synthesis_log.json")
    if log_f.exists():
        try:
            log = json.loads(log_f.read_text())
            return log.get("gen_count", 0) + 1
        except: pass
    return 1

def discover_opportunities():
    myc = Path("mycelium")
    existing = sorted([f.name for f in myc.glob("*.py") if not f.name.startswith("__")]) if myc.exists() else []
    data_f = Path("data")
    data_files = sorted([f.name for f in data_f.glob("*.json")]) if data_f.exists() else []
    brain_state = {}
    bf = Path("data/brain_state.json")
    if bf.exists():
        try: brain_state = json.loads(bf.read_text())
        except: pass
    seed = {}
    sf = Path("data/omnibrain_seed.json")
    if sf.exists():
        try: seed = json.loads(sf.read_text())
        except: pass
    return existing, data_files, brain_state, seed

def synthesize_new_engine(existing, data_files, brain_state, seed):
    if not AI_AVAILABLE:
        print("AI_CLIENT not available — skipping synthesis")
        return None
    gen = get_gen_number()
    seed_instrs = seed.get("instructions", [])
    priority    = brain_state.get("top_priority", "")
    prompt = f"""You are SYNTHESIS_FACTORY gen {gen} for SolarPunk — Meeko's autonomous income system.

YOUR JOB: Build ONE new Python engine that doesn't exist yet.
This engine will run in GitHub Actions and create passive income for Meeko.

EXISTING ENGINES: {existing}
AVAILABLE DATA: {data_files}
CURRENT PRIORITY: {priority}
SEED INSTRUCTIONS: {seed_instrs}

INCOME STREAMS TO BUILD FOR:
1. Gaza Rose Gallery — Gumroad automation, product listings, sales tracking
2. Medium Partner Program — daily AI articles auto-published
3. Substack newsletter — auto-written and scheduled
4. Affiliate marketing — auto-blog posts with affiliate links
5. Prompt packs on Gumroad — generate and list AI templates

RULES YOU MUST FOLLOW:
- Engine must write output to data/[engine_name]_output.json
- Engine reads config from os.environ (GitHub Secrets)
- Only import: os, json, requests, datetime, pathlib, smtplib, email, re, urllib, time, random
- Engine must be fully functional and self-contained
- NO subprocess calls that use git merge, git checkout, git rm, or git reset
- Do NOT write anything to .github/ directory
- If engine needs an API key, read from os.environ and handle missing gracefully

Pick the engine that provides the MOST value toward first passive income dollar.

Respond ONLY with valid JSON (no markdown, no fences):
{{"filename":"engine_name.py","description":"one sentence","income_stream":"which stream","how_it_makes_money":"specific mechanism","code":"complete python file as string"}}"""
    try:
        return ask_json(prompt, max_tokens=4000)
    except Exception as ex:
        print(f"Synthesis AI error: {ex}")
        return None

def write_engine(result):
    if not result: return False
    fname = result.get("filename","")
    code  = result.get("code","")
    if not fname or not code: return False
    if not fname.endswith(".py"):
        print(f"⛔ BLOCKED non-py: {fname}")
        return False
    fname = Path(fname).name
    target_path = f"mycelium/{fname}"
    if not safe_to_write(target_path):
        return False
    target = Path("mycelium") / fname
    target.write_text(code)
    print(f"✅ Synthesized: {fname}")
    print(f"   → {result.get('description','')}")
    print(f"   💰 {result.get('income_stream','')}")
    return True

def update_log(result, gen):
    log_f = Path("data/synthesis_log.json")
    log = {"gen_count": 0, "built": []}
    if log_f.exists():
        try: log = json.loads(log_f.read_text())
        except: pass
    if result:
        log["built"].append({
            "gen": gen, "filename": result.get("filename",""),
            "description": result.get("description",""),
            "income_stream": result.get("income_stream",""),
            "built_at": datetime.now().isoformat()
        })
    log["gen_count"] = gen
    log["last_run"] = datetime.now().isoformat()
    Path("data").mkdir(exist_ok=True)
    log_f.write_text(json.dumps(log, indent=2))

def main():
    gen = get_gen_number()
    print(f"🏭 SYNTHESIS_FACTORY gen {gen} — using HuggingFace free AI")
    existing, data_files, brain_state, seed = discover_opportunities()
    print(f"   Existing engines: {len(existing)}")
    result = synthesize_new_engine(existing, data_files, brain_state, seed)
    wrote  = write_engine(result)
    update_log(result if wrote else None, gen)
    if wrote:
        safe_git_add_only()
        print(f"   Staged for commit")
    else:
        print("   Nothing new synthesized this run")

if __name__ == "__main__":
    main()
