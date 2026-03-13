#!/usr/bin/env python3
"""
DESKTOP_BLUEPRINT_SCANNER.py — Catalogs and revives Meeko's desktop scripts
=============================================================================
When run LOCALLY (via SOLARPUNK.bat or solarpunk_agent.py):
  - Scans C:\Users\meeko\Desktop for .bat, .py, .ps1 files
  - Reads each file, extracts purpose + status + connections
  - Builds data/desktop_blueprints.json — the master catalog
  - Identifies which scripts need updated connections / secrets
  - Pushes catalog to GitHub so SolarPunk knows what tools exist

When run in GITHUB ACTIONS:
  - Reads the catalog already pushed by a local run
  - Reports on script health + suggests which to wire into the loop

The goal: nothing on that desktop rots. Every old blueprint becomes
either active, archived, or absorbed into SolarPunk.
"""
import os, sys, json, subprocess, platform
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data"); DATA.mkdir(exist_ok=True)
IS_LOCAL = platform.system() == "Windows"
DESKTOP  = Path(r"C:\Users\meeko\Desktop") if IS_LOCAL else None

KNOWN_BLUEPRINTS = [
    {
        "name": "SOLARPUNK.bat",
        "purpose": "Main desktop launcher — starts solarpunk_agent.py",
        "status": "active",
        "connections": ["solarpunk_agent.py", "GitHub:meeko-nerve-center"],
        "action": "keep — primary entry point",
    },
    {
        "name": "BRAVE_DEBUG_LAUNCHER.bat",
        "purpose": "Starts Brave with CDP debug port 9222 — bridges SolarPunk to browser",
        "status": "active",
        "connections": ["BRAVE_BROWSER_ENGINE.py", "CDP:9222"],
        "action": "keep — run this before SOLARPUNK.bat for full browser control",
    },
    {
        "name": "MASTER_CONNECT.ps1",
        "purpose": "Master connector — syncs repo, starts Brave, installs deps, creates startup task",
        "status": "active",
        "connections": ["GitHub:meeko-nerve-center", "Brave:9222", "Windows:TaskScheduler"],
        "action": "keep — the one script that wires everything together",
        "run_as_admin": True,
    },
    {
        "name": "MASTER_LAUNCH.bat",
        "purpose": "Legacy master launcher batch file",
        "status": "needs_update",
        "connections": [],
        "action": "update to call MASTER_CONNECT.ps1 instead",
    },
    {
        "name": "MEEKO_LAUNCH.bat",
        "purpose": "Meeko system launcher",
        "status": "needs_update",
        "connections": [],
        "action": "update paths to current SolarPunk structure",
    },
    {
        "name": "EVOLVE.bat",
        "purpose": "Runs evolution cycle on the system",
        "status": "needs_update",
        "connections": ["UltimateAI_Master"],
        "action": "wire into SolarPunk SELF_BUILDER cycle instead",
    },
    {
        "name": "DAILY_LAUNCH.py",
        "purpose": "Daily launch sequence — Ollama, evolution, analytics, CrewAI, Gaza Rose",
        "status": "needs_update",
        "connections": ["Ollama:11434", "UltimateAI_Master", "Gaza Rose DB"],
        "action": "absorb into CYCLE_MEMORY + HEALTH_BOOSTER — daily logic already in OMNIBUS",
    },
    {
        "name": "solarpunk_agent.py",
        "purpose": "Desktop agent — pulls tasks from GitHub, opens browser, copies to clipboard",
        "status": "active",
        "connections": ["GitHub:meeko-nerve-center", "webbrowser", "clipboard"],
        "action": "keep — primary desktop loop agent",
    },
    {
        "name": "CLAUDE_ENGINE.py",
        "purpose": "Desktop Claude API caller",
        "status": "needs_update",
        "connections": ["Anthropic API"],
        "action": "wire into AI_CLIENT.py — already in mycelium",
    },
    {
        "name": "CLEANUP_AND_BRIDGE.py",
        "purpose": "Cleans up old files and bridges local→GitHub",
        "status": "needs_update",
        "connections": ["GitHub"],
        "action": "wire cleanup into AUTO_HEALER cycle",
    },
    {
        "name": "DESKTOP_AGENT_clean.py",
        "purpose": "Clean version of desktop agent",
        "status": "superseded",
        "connections": [],
        "action": "merged — solarpunk_agent.py is the active version",
    },
    {
        "name": "DO_WHAT_YOU_CAN.py",
        "purpose": "Fixes dispatch.yml, pushes self-healing CI, syncs secrets to atomic-agents repos, builds free_data.py",
        "status": "active",
        "connections": ["GitHub:atomic-agents-*", ".secrets file", "gh CLI"],
        "action": "keep — runs the investment HQ systems",
    },
    {
        "name": "LOCAL_GITHUB_BRIDGE.py",
        "purpose": "Bridges local data → GitHub commits",
        "status": "active",
        "connections": ["GitHub:meeko-nerve-center", "GITHUB_TOKEN"],
        "action": "keep — solarpunk_agent.py uses this pattern",
    },
    {
        "name": "prescan.py",
        "purpose": "Pre-scan before running main agent",
        "status": "needs_update",
        "connections": [],
        "action": "absorb into GUARDIAN health check",
    },
]


def scan_local():
    """Read actual file contents and enhance the catalog."""
    if not IS_LOCAL or not DESKTOP or not DESKTOP.exists():
        return KNOWN_BLUEPRINTS

    enhanced = []
    for bp in KNOWN_BLUEPRINTS:
        bp = dict(bp)
        fpath = DESKTOP / bp["name"]
        if fpath.exists():
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
                bp["found"]       = True
                bp["size_bytes"]  = fpath.stat().st_size
                bp["lines"]       = len(content.splitlines())
                bp["last_modified"] = datetime.fromtimestamp(
                    fpath.stat().st_mtime, tz=timezone.utc
                ).isoformat()
                # Extract any secrets/env vars referenced
                refs = []
                for word in ["GITHUB_TOKEN", "ANTHROPIC_API_KEY", "GROQ_API_KEY",
                             "GUMROAD_SECRET", "DEVTO_API_KEY", "CONDUCTOR_TOKEN",
                             "X_API_KEY", "BLUESKY_IDENTIFIER", "BLUESKY_APP_PASSWORD"]:
                    if word in content:
                        refs.append(word)
                if refs:
                    bp["references_secrets"] = refs
            except Exception as e:
                bp["found"] = True
                bp["read_error"] = str(e)[:100]
        else:
            bp["found"] = False
        enhanced.append(bp)

    # Also discover any other .py/.bat/.ps1 files we don't know about
    known_names = {b["name"] for b in KNOWN_BLUEPRINTS}
    for ext in ["*.py", "*.bat", "*.ps1"]:
        for fpath in DESKTOP.glob(ext):
            if fpath.name not in known_names and not fpath.name.startswith("."):
                try:
                    content = fpath.read_text(encoding="utf-8", errors="replace")
                    lines   = len(content.splitlines())
                except:
                    content = ""
                    lines   = 0
                enhanced.append({
                    "name":          fpath.name,
                    "purpose":       f"Unknown script ({lines} lines)",
                    "status":        "uncharted",
                    "found":         True,
                    "size_bytes":    fpath.stat().st_size,
                    "lines":         lines,
                    "action":        "scan and integrate or archive",
                })

    return enhanced


def generate_recommendations(blueprints):
    """What should SolarPunk do about the desktop scripts?"""
    recs = []
    for bp in blueprints:
        if bp.get("status") == "needs_update":
            recs.append(f"Update {bp['name']}: {bp['action']}")
        elif bp.get("status") == "uncharted":
            recs.append(f"Review {bp['name']}: {bp['lines']} lines — unknown purpose")
        elif bp.get("status") == "superseded":
            recs.append(f"Archive {bp['name']}: superseded")

    # Check Brave bridge
    if IS_LOCAL:
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:9222/json/version", timeout=2)
            recs.append("✅ Brave debug port 9222 is LIVE — BRAVE_BROWSER_ENGINE can use it now")
        except:
            recs.append("⚠️  Run BRAVE_DEBUG_LAUNCHER.bat to enable SolarPunk browser control")

    return recs


def load_state():
    f = DATA / "desktop_blueprints_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles": 0, "local_scans": 0}


def save_state(s):
    (DATA / "desktop_blueprints_state.json").write_text(json.dumps(s, indent=2))


def run():
    state = load_state()
    state["cycles"] = state.get("cycles", 0) + 1
    ts = datetime.now(timezone.utc).isoformat()
    print(f"DESKTOP_BLUEPRINT_SCANNER cycle {state['cycles']} | local={IS_LOCAL}")

    if IS_LOCAL:
        blueprints = scan_local()
        state["local_scans"] = state.get("local_scans", 0) + 1
        print(f"  Scanned desktop: {len(blueprints)} blueprints found")
    else:
        # In GitHub Actions — use known catalog
        existing = DATA / "desktop_blueprints.json"
        if existing.exists():
            try:
                catalog = json.loads(existing.read_text())
                blueprints = catalog.get("blueprints", KNOWN_BLUEPRINTS)
                print(f"  Using cached catalog: {len(blueprints)} blueprints")
            except:
                blueprints = KNOWN_BLUEPRINTS
        else:
            blueprints = KNOWN_BLUEPRINTS
            print(f"  No local scan yet — using known catalog: {len(blueprints)}")

    recs = generate_recommendations(blueprints)

    active    = [b for b in blueprints if b.get("status") == "active"]
    updating  = [b for b in blueprints if b.get("status") == "needs_update"]
    uncharted = [b for b in blueprints if b.get("status") == "uncharted"]

    print(f"  Active: {len(active)} | Needs update: {len(updating)} | Uncharted: {len(uncharted)}")
    for r in recs[:5]:
        print(f"  → {r}")

    catalog = {
        "last_scan":   ts,
        "scanned_by":  "local" if IS_LOCAL else "github_actions",
        "total":       len(blueprints),
        "active":      len(active),
        "needs_update": len(updating),
        "uncharted":   len(uncharted),
        "recommendations": recs,
        "blueprints":  blueprints,
    }

    (DATA / "desktop_blueprints.json").write_text(json.dumps(catalog, indent=2))
    save_state(state)
    print(f"  Catalog written to data/desktop_blueprints.json")
    return catalog


if __name__ == "__main__":
    run()
