# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
DESKTOP_AGENT.py — SolarPunk local desktop executor
=====================================================
Built by Base44 SuperAgent. Runs on Meeko's machine.

Loop every 5 min:
  1. Pull latest task queues from GitHub
  2. Execute what can be automated (clipboard, browser tabs)
  3. Show pending manual tasks clearly
  4. Push completion log back to GitHub
  5. Keep local data in sync with repo

Zero friction. System tells desktop what to do. Desktop does it.

Usage:
  python mycelium/DESKTOP_AGENT.py

Requires: GITHUB_TOKEN env var for full sync (read-only without it)
"""
import os, json, time, webbrowser, urllib.request, urllib.error
import subprocess, sys, platform
from datetime import datetime, timezone
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
REPO_OWNER   = "meekotharaccoon-cell"
REPO_NAME    = "meeko-nerve-center"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
RAW_BASE     = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main"
API_BASE     = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
LOOP_SEC     = 300   # 5 minutes
LOCAL_DIR    = Path(__file__).parent / "solarpunk_data"
LOG_FILE     = LOCAL_DIR / "desktop_agent_log.json"

LOCAL_DIR.mkdir(exist_ok=True)


# ── Helpers ──────────────────────────────────────────────────────────────────
def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def log(msg):
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] {msg}")

def banner(title):
    print(f"\n{'='*58}")
    print(f"  {title}")
    print(f"{'='*58}")

def fetch_raw(path):
    try:
        url = f"{RAW_BASE}/{path}?t={int(time.time())}"
        req = urllib.request.Request(url, headers={"User-Agent": "SolarPunk-Desktop/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None

def push_to_github(path, content_dict, message):
    if not GITHUB_TOKEN:
        return False
    try:
        import base64
        content_b64 = base64.b64encode(json.dumps(content_dict, indent=2).encode()).decode()

        sha = None
        try:
            get_req = urllib.request.Request(
                f"{API_BASE}/contents/{path}",
                headers={"Authorization": f"token {GITHUB_TOKEN}", "User-Agent": "SolarPunk-Desktop"},
            )
            with urllib.request.urlopen(get_req, timeout=10) as r:
                sha = json.loads(r.read())["sha"]
        except Exception:
            pass

        body = {"message": message, "content": content_b64}
        if sha:
            body["sha"] = sha

        put_req = urllib.request.Request(
            f"{API_BASE}/contents/{path}",
            data=json.dumps(body).encode(),
            method="PUT",
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Content-Type": "application/json",
                "User-Agent": "SolarPunk-Desktop",
            },
        )
        with urllib.request.urlopen(put_req, timeout=15) as r:
            return r.status in (200, 201)
    except Exception as e:
        log(f"Push failed: {e}")
        return False

def copy_to_clipboard(text):
    try:
        if platform.system() == "Windows":
            subprocess.run("clip", input=text.encode(), check=True)
            return True
    except Exception:
        pass
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        pass
    return False

def open_url(url):
    webbrowser.open(url)


# ── Task Executors ───────────────────────────────────────────────────────────
def handle_social_queue(queue_data):
    if not queue_data:
        return 0
    posts = queue_data if isinstance(queue_data, list) else queue_data.get("posts", [])
    pending = [p for p in posts if isinstance(p, dict) and not p.get("sent") and not p.get("desktop_done")]
    if not pending:
        return 0

    post = pending[0]
    text = post.get("text") or post.get("content") or post.get("message", "")
    platform_name = post.get("platform", "").lower()
    if not text:
        return 0

    copied = copy_to_clipboard(text)
    banner(f"SOCIAL POST READY — {platform_name.upper() or 'SOCIAL'}")
    print(f"\n{text[:300]}\n")
    print(f"  {'COPIED TO CLIPBOARD' if copied else 'Copy manually from above'}")

    urls = {
        "twitter": "https://twitter.com/compose/tweet",
        "x":       "https://twitter.com/compose/tweet",
        "linkedin": "https://www.linkedin.com/feed/",
        "reddit":  "https://www.reddit.com/submit",
    }
    target = urls.get(platform_name, "https://twitter.com/compose/tweet")
    open_url(target)
    log(f"Opened {target}")
    log(f"Just paste and post. {len(pending)-1} more in queue.")
    return len(pending)

def handle_setup_tasks(secrets_data, omnibus_data):
    critical = []
    if secrets_data:
        for m in secrets_data.get("critical_missing", []):
            if m == "GUMROAD_SECRET":
                critical.append({
                    "task": "Add Gumroad token -> unlocks 6 products",
                    "url":  "https://gumroad.com/settings/advanced",
                    "then": "Copy token -> GitHub Secrets -> GUMROAD_SECRET",
                })
            elif m == "X_API_KEY":
                critical.append({
                    "task": "Add Twitter API -> unlocks social posting",
                    "url":  "https://developer.twitter.com/en/portal/dashboard",
                    "then": "Get keys -> GitHub Secrets: X_API_KEY etc.",
                })
    if critical:
        banner("SETUP TASKS — SYSTEM WAITING")
        for i, t in enumerate(critical, 1):
            print(f"\n  {i}. {t['task']}")
            print(f"     -> {t['url']}")
            print(f"     -> {t['then']}")
        open_url(critical[0]["url"])
        log(f"Opened: {critical[0]['url']}")
    return len(critical)

def report_status(omnibus, secrets, social_queue):
    banner("SOLARPUNK STATUS")
    if omnibus:
        health = omnibus.get("health_after", omnibus.get("health_before", 0))
        ok     = len(omnibus.get("engines_ok", []))
        fail   = len(omnibus.get("engines_failed", []))
        rev    = omnibus.get("total_revenue", 0)
        gaza   = omnibus.get("total_to_gaza", 0)
        built  = omnibus.get("engines_auto_built", [])
        last   = omnibus.get("completed", "?")[:16].replace("T", " ")
        status = "HEALTHY" if health >= 70 else "DEGRADED" if health >= 40 else "CRITICAL"
        print(f"\n  Health:   {health}/100 [{status}]")
        print(f"  Engines:  {ok} OK  |  {fail} failed  |  {omnibus.get('version','?')}")
        print(f"  Last run: {last} UTC")
        print(f"  Revenue:  ${rev:.2f}  |  Gaza: ${gaza:.2f}")
        if built:
            print(f"  Built:    {', '.join(built)}")
    if secrets:
        missing = secrets.get("critical_missing", [])
        if missing:
            print(f"\n  MISSING secrets: {', '.join(missing)}")
    if social_queue:
        posts = social_queue if isinstance(social_queue, list) else social_queue.get("posts", [])
        pending = [p for p in posts if isinstance(p, dict) and not p.get("sent")]
        print(f"\n  Social queue: {len(pending)} pending posts")
    print()

def write_log(actions):
    existing = []
    if LOG_FILE.exists():
        try:
            existing = json.loads(LOG_FILE.read_text())
        except Exception:
            pass
    entry = {"ts": ts(), "actions": actions, "platform": platform.system()}
    existing.append(entry)
    existing = existing[-200:]
    LOG_FILE.write_text(json.dumps(existing, indent=2))
    if GITHUB_TOKEN:
        if push_to_github("data/desktop_agent_log.json", existing, f"desktop: cycle {ts()}"):
            log("Synced log to GitHub")
    return entry


# ── Main Loop ────────────────────────────────────────────────────────────────
def run_cycle():
    log("Fetching system state from GitHub...")
    omnibus = fetch_raw("data/omnibus_last.json")
    secrets = fetch_raw("data/secrets_checker_state.json")
    sq      = fetch_raw("data/social_queue.json")
    landing = fetch_raw("data/live_landing_pages.json")
    actions = []

    report_status(omnibus, secrets, sq)

    n_setup = handle_setup_tasks(secrets, omnibus)
    if n_setup:
        actions.append(f"Showed {n_setup} setup tasks, opened browser")

    n_social = handle_social_queue(sq)
    if n_social:
        actions.append(f"Social: {n_social} posts pending, copied next to clipboard")

    # Live pages
    BASE = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
    banner("LIVE PAGES")
    for page in ["index", "store", "links", "social", "opportunities", "weaver", "optimizer"]:
        print(f"  {BASE}/{page}.html")

    write_log(actions)
    if not actions:
        log("System clean — no manual tasks needed right now.")


def main():
    banner("SOLARPUNK DESKTOP AGENT — ONLINE")
    print("  Syncing with nerve center every 5 min...")
    print("  Press Ctrl+C to stop\n")

    if not GITHUB_TOKEN:
        print("  No GITHUB_TOKEN — running read-only")
        print("  Set: $env:GITHUB_TOKEN = 'ghp_...' for full sync\n")

    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'='*58}")
        print(f"  CYCLE {cycle} — {ts()}")
        print(f"{'='*58}")
        try:
            run_cycle()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log(f"Cycle error: {e}")
        log(f"Next cycle in {LOOP_SEC//60} min... (Ctrl+C to stop)")
        try:
            time.sleep(LOOP_SEC)
        except KeyboardInterrupt:
            print("\n\n  [STOPPED] SolarPunk Desktop Agent shut down cleanly.")
            break


if __name__ == "__main__":
    main()
