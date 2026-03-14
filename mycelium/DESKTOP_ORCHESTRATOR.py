# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
DESKTOP_ORCHESTRATOR.py — The engine that makes old blueprints live again
=========================================================================
Meeko's desktop is full of digital blueprints — .py, .bat, .ps1 files
that were built for various missions but never got properly connected.

This engine:
  1. Reads data/desktop_blueprints.json (catalog from BRAVE_BRIDGE)
  2. Uses AI to understand what each blueprint does
  3. Updates broken connections (paths, tokens, secrets)
  4. Runs what can run safely now
  5. Queues what needs human confirmation
  6. Writes a "resurrection report" to data/resurrections.json

Think of it as: SolarPunk inherits everything you ever built.
The old tools become part of the organism.

Blueprints already seen on desktop:
  MASTER_CONNECT.ps1     — connection hub (being rebuilt as v2)
  LOCAL_GITHUB_BRIDGE.py — Ollama + GitHub sync
  DAILY_LAUNCH.py        — runs all subsystems in order
  DO_WHAT_YOU_CAN.py     — cross-repo repair + secret sync
  CLAUDE_ENGINE.py       — Claude briefing generator
  solarpunk_agent.py     — desktop task executor
  EVOLVE.bat             — evolution cycle launcher
  MEEKO_LAUNCH.bat       — full system launcher (revenue + agent + dashboard)
  MASTER_LAUNCH.bat      — menu launcher for all subsystems
"""
import os, json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

DATA    = Path("data"); DATA.mkdir(exist_ok=True)
DESKTOP = Path.home() / "Desktop"
PYTHON  = sys.executable

try:
    from AI_CLIENT import ask
    AI_ONLINE = True
except ImportError:
    AI_ONLINE = False
    def ask(messages, **kw): return ""


# Known blueprint catalog with what each one does + how to resurrect it
KNOWN_BLUEPRINTS = {
    "LOCAL_GITHUB_BRIDGE.py": {
        "purpose": "Sync local Ollama AI analysis to GitHub meeko-brain repo",
        "broken_because": "Uses CONDUCTOR_TOKEN from .secrets file — needs updating to GITHUB_TOKEN",
        "fix": "update_env_var",
        "runnable": True,
        "run_safely": False,  # reads .secrets, heavy
        "resurrection": "wire into L1 as LOCAL_ANALYSIS engine when desktop is connected",
    },
    "DAILY_LAUNCH.py": {
        "purpose": "Run all subsystems in sequence: Ollama → evolution → analytics → crew → report",
        "broken_because": "Hardcoded paths to mycelium_env which may not exist",
        "fix": "update_python_path",
        "runnable": True,
        "run_safely": False,
        "resurrection": "replace with OMNIBUS — already does everything this does, better",
    },
    "DO_WHAT_YOU_CAN.py": {
        "purpose": "Cross-repo CI fixes, secret sync, free market data, fire conductor dispatch",
        "broken_because": "Uses CONDUCTOR_TOKEN + old atomic-agents repos + Alpaca (broken 401)",
        "fix": "update_tokens",
        "runnable": True,
        "run_safely": False,
        "resurrection": "port the secret-sync part into SECRETS_CHECKER as SYNC mode",
    },
    "CLAUDE_ENGINE.py": {
        "purpose": "Generate Claude briefing page at docs/claude_briefing.html",
        "broken_because": "Standalone version — repo has better version in mycelium/",
        "fix": "already_fixed",
        "runnable": True,
        "run_safely": True,
        "resurrection": "already in OMNIBUS L7, this desktop copy is obsolete",
    },
    "solarpunk_agent.py": {
        "purpose": "Desktop agent: pull task queue from GitHub, copy posts to clipboard, open URLs",
        "broken_because": "Uses GITHUB_TOKEN env var — set it in System Environment Variables",
        "fix": "set_GITHUB_TOKEN_env",
        "runnable": True,
        "run_safely": False,
        "resurrection": "run via SOLARPUNK.bat — the bridge between GitHub state and your browser",
    },
    "SOLARPUNK.bat": {
        "purpose": "Launch solarpunk_agent.py — the desktop-to-GitHub bridge",
        "broken_because": "Downloads agent from GitHub main — now outdated, better local copy exists",
        "fix": "point_to_local_agent",
        "runnable": True,
        "run_safely": True,
        "resurrection": "double-click to start the desktop agent loop",
    },
    "EVOLVE.bat": {
        "purpose": "Run mycelium/evolve.py evolution cycle + git commit",
        "broken_because": "evolve.py may not exist in repo mycelium/ — check",
        "fix": "verify_evolve_engine",
        "runnable": True,
        "run_safely": False,
        "resurrection": "OMNIBUS already does evolution — this is redundant unless offline",
    },
    "MEEKO_LAUNCH.bat": {
        "purpose": "Start Revenue Engine (7781), Agent (7780), Dashboard (7779), OMNI orchestrator",
        "broken_because": "Hardcoded paths: REVENUE_ENGINE.py, AUTONOMOUS_AGENT.py, LIVE_DASHBOARD.py — check if they exist",
        "fix": "verify_paths",
        "runnable": True,
        "run_safely": False,
        "resurrection": "powerful local launch — verify component paths first",
    },
    "MASTER_CONNECT.ps1": {
        "purpose": "Wire desktop to SolarPunk: clone repo, install deps, launch Brave debug port, Getscreen, WhatsApp, scheduled task",
        "broken_because": "v1 — being superseded by MASTER_CONNECT_V2.ps1 with Brave CDP + blueprint resurrection",
        "fix": "update_to_v2",
        "runnable": True,
        "run_safely": True,
        "resurrection": "run as admin at any time to re-wire everything",
    },
}


def load_state():
    f = DATA / "desktop_orchestrator_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "resurrected": [], "queued": [], "total_blueprints": 0}


def save_state(s):
    (DATA / "desktop_orchestrator_state.json").write_text(json.dumps(s, indent=2))


def analyze_blueprints_with_ai(blueprints):
    """Use AI to understand unknown blueprints."""
    unknown = [b for b in blueprints if b["name"] not in KNOWN_BLUEPRINTS]
    if not unknown or not AI_ONLINE:
        return {}
    
    names = [b["name"] for b in unknown[:10]]
    analysis = ask([{"role": "user", "content": (
        f"These files exist on a developer's desktop: {names}. "
        f"For each, guess: (1) what it probably does based on name, (2) if it's safe to run. "
        f"Reply as JSON: {{\"filename\": {{\"purpose\": \"...\", \"safe\": true/false}}}}"
    )}], max_tokens=500)
    
    try:
        return json.loads(analysis.strip().strip("```json").strip("```").strip())
    except:
        return {}


def check_brave_cdp():
    """Check if Brave debug port is live."""
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:9222/json/version", timeout=3) as r:
            data = json.loads(r.read())
            return True, data.get("Browser", "unknown")
    except:
        return False, "offline"


def run():
    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1
    ts = datetime.now(timezone.utc).isoformat()
    print(f"DESKTOP_ORCHESTRATOR cycle {state['cycles']}")

    # Load blueprint catalog
    catalog_file = DATA / "desktop_blueprints.json"
    if not catalog_file.exists():
        print("  ⏳ No blueprint catalog yet — BRAVE_BRIDGE must run first")
        save_state(state)
        return state

    catalog = json.loads(catalog_file.read_text())
    blueprints = catalog.get("files", [])
    state["total_blueprints"] = len(blueprints)
    print(f"  Blueprints cataloged: {len(blueprints)}")

    # Check Brave
    brave_live, brave_ver = check_brave_cdp()
    print(f"  Brave CDP: {'✅ ' + brave_ver if brave_live else '⚠️  offline (run MASTER_CONNECT.ps1)'}")

    # Analyze known blueprints
    resurrection_report = []
    run_queue = []
    manual_queue = []

    for bp in blueprints:
        name = bp["name"]
        info = KNOWN_BLUEPRINTS.get(name, {})
        
        entry = {
            "name": name,
            "size": bp.get("size", 0),
            "purpose": info.get("purpose", "unknown"),
            "status": "unknown",
            "resurrection": info.get("resurrection", "needs_analysis"),
        }

        if info.get("run_safely") and info.get("runnable"):
            entry["status"] = "ready_to_run"
            run_queue.append(name)
        elif info.get("runnable") and not info.get("run_safely"):
            entry["status"] = "needs_verification"
            manual_queue.append({"name": name, "purpose": info.get("purpose", "?"), "fix": info.get("fix", "?")})
        elif not info:
            entry["status"] = "unknown_needs_analysis"
        
        resurrection_report.append(entry)

    # Write resurrection report
    report = {
        "generated_at": ts,
        "total_blueprints": len(blueprints),
        "ready_to_run": run_queue,
        "needs_verification": [m["name"] for m in manual_queue],
        "brave_live": brave_live,
        "brave_version": brave_ver,
        "blueprints": resurrection_report,
        "action_summary": (
            f"Found {len(blueprints)} blueprints. "
            f"{len(run_queue)} ready to run. "
            f"{len(manual_queue)} need path/token fixes. "
            f"Brave CDP: {'live' if brave_live else 'offline'}."
        ),
    }
    (DATA / "resurrections.json").write_text(json.dumps(report, indent=2))

    # Generate tasks for TASK_ATOMIZER
    tasks = []
    for m in manual_queue[:5]:
        tasks.append({
            "id": f"resurrect_{m['name'].replace('.', '_')}",
            "task": f"Fix and integrate {m['name']}: {m['purpose']}",
            "fix_needed": m.get("fix", "verify"),
            "priority": 4,
            "source": "DESKTOP_ORCHESTRATOR",
        })
    
    if tasks:
        tasks_file = DATA / "resurrection_tasks.json"
        tasks_file.write_text(json.dumps(tasks, indent=2))
        print(f"  {len(tasks)} resurrection tasks queued for TASK_ATOMIZER")

    state["resurrected"] = run_queue
    state["queued"]      = [m["name"] for m in manual_queue]
    state["last_run"]    = ts
    save_state(state)

    print(f"  Ready: {run_queue or 'none yet'}")
    print(f"  Need fixing: {[m['name'] for m in manual_queue[:3]]}")
    print(f"  Report: data/resurrections.json")
    return state


if __name__ == "__main__":
    run()
