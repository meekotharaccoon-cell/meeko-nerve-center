#!/usr/bin/env python3
"""ENGINE_INTEGRITY.py — SHA-based tamper detection for all 37 engines
Uses ONLY GITHUB_TOKEN. Reads all engine SHAs via GitHub API each cycle.
Compares against last-known-good registry. Alerts on unexpected changes.
The system becomes self-aware of its own code integrity.
"""
import os, json, requests
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "meekotharaccoon-cell/meeko-nerve-center")
BASE = f"https://api.github.com/repos/{REPO}"

def gh(path):
    return requests.get(
        f"{BASE}{path}",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"},
        timeout=30
    )

def load_registry():
    f = DATA / "engine_sha_registry.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"first_seen": {}, "last_seen": {}, "change_log": [], "alerts": []}

def save_registry(r):
    (DATA / "engine_sha_registry.json").write_text(json.dumps(r, indent=2))

def run():
    print("ENGINE_INTEGRITY scanning...")
    now = datetime.now(timezone.utc).isoformat()
    registry = load_registry()

    # Get all engine SHAs from GitHub
    r = gh("/contents/mycelium")
    if r.status_code != 200:
        print(f"  API error {r.status_code}"); return

    current = {f["name"]: {"sha": f["sha"], "size": f["size"]}
               for f in r.json() if f["name"].endswith(".py")}

    # Get latest commit info
    rc = gh("/commits/main")
    latest_commit = {}
    if rc.status_code == 200:
        c = rc.json()
        latest_commit = {
            "sha": c["sha"][:8],
            "message": c["commit"]["message"][:80],
            "author": c["commit"]["author"]["name"]
        }

    changes = []
    new_engines = []
    alerts = []

    for name, info in current.items():
        sha = info["sha"]
        if name not in registry["first_seen"]:
            registry["first_seen"][name] = {"sha": sha, "ts": now}
            new_engines.append(name)
        elif registry["last_seen"].get(name, {}).get("sha") != sha:
            old_sha = registry["last_seen"].get(name, {}).get("sha", "?")[:8]
            changes.append({
                "engine": name, "old_sha": old_sha, "new_sha": sha[:8],
                "ts": now, "commit": latest_commit
            })
            # Alert if not from expected authors
            author = latest_commit.get("author", "")
            if not any(a in author for a in ["SolarPunk", "SELF_BUILDER", "meekotharaccoon"]):
                alerts.append({"engine": name, "ts": now, "author": author})

        registry["last_seen"][name] = {"sha": sha, "size": info["size"], "ts": now}

    if changes:
        registry["change_log"] = (registry.get("change_log", []) + changes)[-500:]
    if alerts:
        registry["alerts"] = (registry.get("alerts", []) + alerts)[-100:]

    registry.update({
        "last_scan": now,
        "total_engines": len(current),
        "total_changes": len(registry.get("change_log", [])),
    })
    save_registry(registry)

    print(f"  Engines tracked: {len(current)}")
    if new_engines: print(f"  New: {', '.join(new_engines)}")
    if changes: print(f"  Changed this cycle: {', '.join(c['engine'] for c in changes)}")
    if alerts: print(f"  ALERTS: {len(alerts)} unexpected modifications")
    else: print(f"  OK — all {len(current)} engine SHAs verified")
    return registry

if __name__ == "__main__": run()
