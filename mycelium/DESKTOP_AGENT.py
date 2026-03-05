#!/usr/bin/env python3
"""
DESKTOP_AGENT.py — SolarPunk local desktop executor
=====================================================
Runs on Meeko's machine. Double-click SOLARPUNK.bat to start.

Loop every 5 min:
  1. Pull latest task queues from GitHub
  2. Execute what can be automated (clipboard, browser tabs)
  3. Show pending manual tasks clearly
  4. Push completion log back to GitHub
  5. Keep local data in sync with repo

Zero friction. System tells desktop what to do. Desktop does it.
"""
import os, json, time, webbrowser, urllib.request, urllib.error
import subprocess, sys, platform
from datetime import datetime, timezone
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
REPO_OWNER  = "meekotharaccoon-cell"
REPO_NAME   = "meeko-nerve-center"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
RAW_BASE    = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main"
API_BASE    = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
LOOP_SEC    = 300   # 5 minutes
LOCAL_DIR   = Path(__file__).parent / "solarpunk_data"
LOG_FILE    = LOCAL_DIR / "desktop_agent_log.json"

LOCAL_DIR.mkdir(exist_ok=True)

# ── Helpers ──────────────────────────────────────────────────────────────────

def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def log(msg):
    prefix = f"  [{datetime.now().strftime('%H:%M:%S')}]"
    print(f"{prefix} {msg}")

def banner(title):
    print(f"\n{'─'*58}")
    print(f"  {title}")
    print(f"{'─'*58}")

def fetch_raw(path):
    try:
        url = f"{RAW_BASE}/{path}?t={int(time.time())}"
        req = urllib.request.Request(url, headers={"User-Agent": "SolarPunk-Desktop/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return None

def push_to_github(path, content_dict, message):
    if not GITHUB_TOKEN:
        return False
    try:
        import urllib.request as ur
        import base64

        content_bytes = json.dumps(content_dict, indent=2).encode()
        content_b64   = base64.b64encode(content_bytes).decode()

        # Get current SHA
        sha = None
        try:
            get_req = ur.Request(
                f"{API_BASE}/contents/{path}",
                headers={"Authorization": f"token {GITHUB_TOKEN}", "User-Agent": "SolarPunk-Desktop"},
            )
            with ur.urlopen(get_req, timeout=10) as r:
                sha = json.loads(r.read())["sha"]
        except Exception:
            pass

        body = {"message": message, "content": content_b64}
        if sha:
            body["sha"] = sha

        data = json.dumps(body).encode()
        put_req = ur.Request(
            f"{API_BASE}/contents/{path}",
            data=data,
            method="PUT",
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Content-Type": "application/json",
                "User-Agent": "SolarPunk-Desktop",
            },
        )
        with ur.urlopen(put_req, timeout=15) as r:
            return r.status in (200, 201)
    except Exception as e:
        log(f"Push failed: {e}")
        return False

def copy_to_clipboard(text):
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        try:
            if platform.system() == "Windows":
                subprocess.run("clip", input=text.encode(), check=True)
                return True
        except Exception:
            pass
    return False

def open_url(url):
    webbrowser.open(url)

# ── Task Executors ────────────────────────────────────────────────────────────

def handle_social_queue(queue_data):
    """Get next unsent post, copy to clipboard, open platform."""
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

    # Copy to clipboard
    copied = copy_to_clipboard(text)
    banner(f"📋 SOCIAL POST READY — {platform_name.upper() or 'SOCIAL'}")
    print(f"\n{text[:300]}\n")
    if copied:
        print("  ✅ COPIED TO CLIPBOARD")
    else:
        print("  ⚠️  Copy manually from above")

    # Open the right platform
    urls = {
        "twitter": "https://twitter.com/compose/tweet",
        "x": "https://twitter.com/compose/tweet",
        "linkedin": "https://www.linkedin.com/feed/",
        "reddit": "https://www.reddit.com/submit",
    }
    target_url = urls.get(platform_name, "https://twitter.com/compose/tweet")
    open_url(target_url)
    print(f"  🌐 Opened {target_url}")
    print(f"  → Just paste and post. {len(pending)-1} more in queue.")

    return len(pending)

def handle_setup_tasks(secrets_data, omnibus_data):
    """Show urgent setup tasks with direct links."""
    critical = []
    if secrets_data:
        missing = secrets_data.get("critical_missing", [])
        for m in missing:
            if m == "GUMROAD_SECRET":
                critical.append({
                    "task": "Add Gumroad token → unlocks 6 products",
                    "url": "https://gumroad.com/settings/advanced",
                    "then": "Copy token → GitHub repo Settings → Secrets → GUMROAD_SECRET",
                })
            elif m == "X_API_KEY":
                critical.append({
                    "task": "Add Twitter API → unlocks 88 queued posts",
                    "url": "https://developer.twitter.com/en/portal/dashboard",
                    "then": "Get keys → GitHub Secrets: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET",
                })

    if critical:
        banner("🔴 SETUP TASKS — SYSTEM IS WAITING ON THESE")
        for i, t in enumerate(critical, 1):
            print(f"\n  {i}. {t['task']}")
            print(f"     → {t['url']}")
            print(f"     → Then: {t['then']}")
        print()
        # Open first one automatically
        open_url(critical[0]["url"])
        log(f"Opened: {critical[0]['url']}")

    return len(critical)

def handle_live_pages(landing_data):
    """Show all live pages."""
    if not landing_data:
        return
    pages = landing_data.get("pages", landing_data) if isinstance(landing_data, dict) else landing_data
    banner("🌐 LIVE PAGES")
    base = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
    urls = [
        f"{base}/index.html",
        f"{base}/store.html",
        f"{base}/links.html",
        f"{base}/social.html",
        f"{base}/opportunities.html",
        f"{base}/weaver.html",
        f"{base}/optimizer.html",
    ]
    for u in urls:
        print(f"  {u}")

def report_status(omnibus, secrets, social_queue):
    """Print clean system status."""
    banner("🧠 SOLARPUNK STATUS")

    health = 0
    if omnibus:
        health = omnibus.get("health_after", omnibus.get("health_before", 0))
        engines_ok   = len(omnibus.get("engines_ok", []))
        engines_fail = len(omnibus.get("engines_failed", []))
        version      = omnibus.get("version", "?")
        last_run     = omnibus.get("completed", "?")[:16].replace("T", " ")
        revenue      = omnibus.get("total_revenue", 0)
        gaza         = omnibus.get("total_to_gaza", 0)
        auto_built   = omnibus.get("engines_auto_built", [])

        color = "🟢" if health >= 70 else "🟡" if health >= 40 else "🔴"
        print(f"\n  {color} Health:   {health}/100")
        print(f"  📦 Engines:  {engines_ok} OK  |  {engines_fail} failed  |  {version}")
        print(f"  ⏱  Last run: {last_run} UTC")
        print(f"  💰 Revenue:  ${revenue:.2f}  |  Gaza: ${gaza:.2f}")
        if auto_built:
            print(f"  🧬 Built:    {', '.join(auto_built)}")

    if secrets:
        missing = secrets.get("critical_missing", [])
        if missing:
            print(f"\n  🔴 Missing secrets: {', '.join(missing)}")

    if social_queue:
        posts = social_queue if isinstance(social_queue, list) else social_queue.get("posts", [])
        pending = [p for p in posts if isinstance(p, dict) and not p.get("sent")]
        print(f"\n  📣 Social queue: {len(pending)} pending posts")

    print()

def write_log(actions):
    """Write what we did locally and push to GitHub."""
    existing = []
    if LOG_FILE.exists():
        try:
            existing = json.loads(LOG_FILE.read_text())
        except Exception:
            pass

    entry = {
        "ts": ts(),
        "actions": actions,
        "platform": platform.system(),
    }
    existing.append(entry)
    existing = existing[-200:]  # Keep last 200

    LOG_FILE.write_text(json.dumps(existing, indent=2))

    # Push to GitHub
    if GITHUB_TOKEN:
        pushed = push_to_github(
            "data/desktop_agent_log.json",
            existing,
            f"🖥️ Desktop agent cycle — {ts()}"
        )
        if pushed:
            log("✅ Synced log to GitHub")
    return entry

# ── Main Loop ─────────────────────────────────────────────────────────────────

def run_cycle():
    log("Fetching system state from GitHub...")

    omnibus   = fetch_raw("data/omnibus_last.json")
    secrets   = fetch_raw("data/secrets_checker_state.json")
    sq        = fetch_raw("data/social_queue.json")
    landing   = fetch_raw("data/live_landing_pages.json")

    actions = []

    # 1. Status
    report_status(omnibus, secrets, sq)

    # 2. Setup tasks (highest priority)
    n_setup = handle_setup_tasks(secrets, omnibus)
    if n_setup:
        actions.append(f"Showed {n_setup} setup tasks, opened browser")

    # 3. Social queue
    n_social = handle_social_queue(sq)
    if n_social:
        actions.append(f"Social: {n_social} posts pending, copied next to clipboard")

    # 4. Live pages summary
    handle_live_pages(landing)

    # 5. Log it
    write_log(actions)

    if not actions:
        log("System is running clean — no manual tasks needed right now.")

def main():
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║   SOLARPUNK DESKTOP AGENT — ONLINE           ║")
    print("  ║   Syncing with nerve center every 5 min...   ║")
    print("  ║   Press Ctrl+C to stop                       ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()

    if not GITHUB_TOKEN:
        print("  ⚠️  No GITHUB_TOKEN — running in read-only mode")
        print("     Set GITHUB_TOKEN env var to enable full sync\n")

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

        log(f"Next cycle in {LOOP_SEC//60} minutes... (Ctrl+C to stop)")
        try:
            time.sleep(LOOP_SEC)
        except KeyboardInterrupt:
            print("\n\n  [STOPPED] SolarPunk Desktop Agent shut down cleanly.")
            break


if __name__ == "__main__":
    main()
