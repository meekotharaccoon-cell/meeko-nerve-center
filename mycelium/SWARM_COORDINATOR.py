#!/usr/bin/env python3
"""
SWARM_COORDINATOR.py — ALL HANDS ON DECK
=========================================
SolarPunk reads its own audit, spins up focused repair swarms,
and coordinates them like a hive mind.

Each swarm = a set of engines focused on one broken domain.
In GitHub Actions: triggers parallel workflow dispatches.
In local mode: runs inline.

The self-healing loop:
  REVENUE_AUDIT finds the wounds
  SWARM_COORDINATOR calls the swarms
  Each swarm runs the right engines
  Results feed back into next OMNIBUS cycle
  Repeat until everything is green
"""
import os, json, urllib.request, urllib.error, subprocess, sys, time
from pathlib import Path
from datetime import datetime, timezone

DATA   = Path("data"); DATA.mkdir(exist_ok=True)
MYC    = Path("mycelium")
PYTHON = sys.executable
OWNER  = "meekotharaccoon-cell"
REPO   = "meeko-nerve-center"
TOKEN  = os.environ.get("GITHUB_TOKEN", "")

SWARMS = [
    {
        "name": "SWARM_REVENUE",
        "focus": "Fix all broken buy links and checkout paths",
        "engines": ["GUMROAD_ENGINE", "KOFI_ENGINE", "STORE_BUILDER"],
        "condition": lambda a: a.get("critical_broken", 0) > 0 or a.get("buy_link_issues", 0) > 0,
    },
    {
        "name": "SWARM_CONTENT",
        "focus": "Generate missing product files — art, ZIPs, downloads",
        "engines": ["ART_CATALOG", "ART_GENERATOR", "AGENT_GUMROAD_BUILDER", "QUICK_REVENUE"],
        "condition": lambda a: True,
    },
    {
        "name": "SWARM_SOCIAL",
        "focus": "Drain 200+ post queue — Bluesky, DEV.to, Mastodon, GitHub Gist",
        "engines": ["BLUESKY_ENGINE", "DEV_TO_PUBLISHER", "MASTODON_ENGINE", "AUTONOMOUS_PUBLISHER"],
        "condition": lambda a: True,
    },
    {
        "name": "SWARM_CONNECT",
        "focus": "Test every API key, fix what's broken, report what's alive",
        "engines": ["SECRETS_CHECKER", "BOTTLENECK_SCANNER", "AUTO_HEALER"],
        "condition": lambda a: True,
    },
    {
        "name": "SWARM_STORE",
        "focus": "Rebuild store: working links, art previews, free art CTA front and center",
        "engines": ["STORE_BUILDER", "LANDING_DEPLOYER", "LINK_PAGE"],
        "condition": lambda a: a.get("buy_link_issues", 0) > 0 or not a.get("gumroad_alive", True),
    },
]


def rj(fname, fb=None):
    f = DATA / fname
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return fb if fb is not None else {}


def run_engine(name):
    script = MYC / f"{name}.py"
    if not script.exists():
        return False, "not found"
    try:
        r = subprocess.run([PYTHON, str(script)], capture_output=True,
                           text=True, timeout=90, cwd=Path.cwd())
        return r.returncode == 0, (r.stdout or "")[-150:]
    except Exception as e:
        return False, str(e)[:60]


def dispatch_workflow(inputs):
    """Trigger OMNIBRAIN via workflow_dispatch (needs workflow scope on token)."""
    if not TOKEN: return False, "no token"
    url  = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/OMNIBRAIN.yml/dispatches"
    body = json.dumps({"ref": "main", "inputs": inputs or {}}).encode()
    req  = urllib.request.Request(url, data=body, method="POST",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "SolarPunk-Swarm/1.0",
        })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return True, r.status
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)[:60]


def run():
    ts     = datetime.now(timezone.utc).isoformat()
    is_gha = bool(os.environ.get("GITHUB_RUN_ID"))
    print(f"SWARM_COORDINATOR — ALL HANDS ON DECK — cycle start")
    print(f"  Mode: {'GitHub Actions' if is_gha else 'Local'}")

    audit = rj("revenue_audit.json")
    state = rj("swarm_state.json", {"cycles": 0, "total_engine_runs": 0})
    state["cycles"] = state.get("cycles", 0) + 1

    if not audit:
        print("  No audit yet — running REVENUE_AUDIT first")
        ok, _ = run_engine("REVENUE_AUDIT")
        audit = rj("revenue_audit.json")

    print(f"  Audit: {audit.get('broken', '?')} broken | {audit.get('buy_link_issues', '?')} buy issues | gumroad={audit.get('gumroad_alive', '?')}")

    results = []
    for swarm in SWARMS:
        try:
            active = swarm["condition"](audit)
        except:
            active = True

        if not active:
            print(f"  -- {swarm['name']}: condition not met, skipping")
            continue

        print(f"\n  ** {swarm['name']}: {swarm['focus']}")
        swarm_result = {"swarm": swarm["name"], "engines": {}, "ts": ts}

        for eng in swarm["engines"]:
            ok, out = run_engine(eng)
            swarm_result["engines"][eng] = "ok" if ok else f"fail"
            state["total_engine_runs"] = state.get("total_engine_runs", 0) + 1
            print(f"     {'OK' if ok else 'XX'} {eng}")

        results.append(swarm_result)

    # Human action briefing
    human_actions = audit.get("human_action_required", [])
    state["human_actions_pending"] = human_actions

    state["last_run"]     = ts
    state["swarms"]       = results
    state["audit_snapshot"] = {
        "critical_broken":  audit.get("critical_broken", "?"),
        "buy_link_issues":  audit.get("buy_link_issues", "?"),
        "gumroad_alive":    audit.get("gumroad_alive", False),
        "kofi_alive":       audit.get("kofi_alive", False),
    }

    (DATA / "swarm_state.json").write_text(json.dumps(state, indent=2))

    if human_actions:
        print(f"\n  !! HUMAN REQUIRED ({len(human_actions)}):")
        for ha in human_actions:
            print(f"     [{ha['priority']}] {ha['action']}")
            print(f"         {ha['detail']}")
            print(f"         -> Impact: {ha['impact']}")

    print(f"\n  Swarms run: {len(results)} | All-time engine runs: {state['total_engine_runs']}")
    return state


if __name__ == "__main__":
    run()
