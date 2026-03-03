#!/usr/bin/env python3
"""
SOLARPUNK ACTIVATE — Master Trigger Script
==========================================
This is the ONE script that runs everything.

How it works:
1. Discovers every workflow_dispatch-enabled workflow across ALL repos
2. Triggers them in priority order (nerve-center first, then outward)
3. Waits for each to complete before moving to the next critical one
4. On failure: retries once, logs the error, keeps going
5. Writes live status to data/activate_status.json (readable via GitHub Pages)
6. Also triggers the Zeno reply email via the existing email system
7. Updates the live AI conversation dashboard

No new secrets needed. GH_PAT does everything cross-repo.
GITHUB_TOKEN handles same-repo operations.
"""

import os
import sys
import json
import time
import base64
import requests
from datetime import datetime, timezone

# ── Config ──────────────────────────────────────────────────────────────────
GH_TOKEN   = os.environ.get("GH_PAT", os.environ.get("GITHUB_TOKEN", ""))
OWNER      = "meekotharaccoon-cell"
PAGES_BASE = f"https://{OWNER}.github.io"

HEADERS = {
    "Authorization": f"token {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json"
}

STATUS_FILE = "data/activate_status.json"
EMAIL_QUEUE = "data/outbound_email_queue.json"

# ── All repos in priority order ──────────────────────────────────────────────
# Nerve-center first (hub), then mycelium (revenue), then solarpunk (mission)
REPO_PRIORITY = [
    "meeko-nerve-center",          # Hub — must run first
    "mycelium-core",               # Orchestrates all mycelium
    "mycelium-grants",             # Free money
    "mycelium-money",              # Revenue
    "mycelium-knowledge",          # Content
    "mycelium-visibility",         # Reach
    "meeko-brain",                 # Memory
    "gaza-rose-gallery",           # Art sales
    "solarpunk-market",            # Marketplace
    "solarpunk-grants",            # Community grants
    "solarpunk-learn",             # Education
    "solarpunk-legal",             # Legal aid
    "solarpunk-mutual-aid",        # Community
    "solarpunk-radio",             # Radio
    "solarpunk-bank",              # Finance
    "solarpunk-remedies",          # Health guides
    "atomic-agents",               # Agent runtime
    "atomic-agents-staging",       # Staging
    "atomic-agents-conductor",     # Conductor
    "atomic-agents-demo",          # Demo
    "meekotharaccoon-cell.github.io",  # Main site — last (publishes results)
]

# Workflows that should run in strict sequence (wait for each)
# Everything else can be best-effort
CRITICAL_SEQUENCE = [
    ("meeko-nerve-center", "MASTER_CONTROLLER.yml"),
    ("meeko-nerve-center", "self-healer.yml"),
    ("meeko-nerve-center", "claude-autonomous.yml"),
]

# Workflows to SKIP (broken stubs, duplicates, or localhost-only)
SKIP_WORKFLOWS = {
    "community-outreach.yml",  # stub
    "email-drafter.yml",       # stub  
    "email-responder.yml",     # stub
    "feedback-loop.yml",       # stub
    "send-grants.yml",         # stub
    "send-outreach.yml",       # stub
    "huggingface-bridge.yml",  # no HF token
    "kimi-conductor.yml",      # needs KIMI_API_KEY
    "dual-brain-sync.yml",     # needs KIMI_API_KEY
}


# ── GitHub API helpers ───────────────────────────────────────────────────────
def api(method, path, **kwargs):
    url = f"https://api.github.com{path}"
    r = getattr(requests, method)(url, headers=HEADERS, timeout=30, **kwargs)
    return r


def get_workflows(repo):
    """Get all workflows that support workflow_dispatch."""
    r = api("get", f"/repos/{OWNER}/{repo}/actions/workflows")
    if r.status_code != 200:
        return []
    workflows = []
    for wf in r.json().get("workflows", []):
        name = wf.get("path", "").split("/")[-1]
        if name and name not in SKIP_WORKFLOWS and wf.get("state") == "active":
            workflows.append({
                "id": wf["id"],
                "name": wf["name"],
                "file": name,
                "path": wf["path"]
            })
    return workflows


def trigger_workflow(repo, workflow_file):
    """Trigger a workflow via workflow_dispatch."""
    r = api("post",
            f"/repos/{OWNER}/{repo}/actions/workflows/{workflow_file}/dispatches",
            json={"ref": "main", "inputs": {"reason": "SolarPunk Activate!"}})
    # Some repos use 'master' branch
    if r.status_code == 422:
        r = api("post",
                f"/repos/{OWNER}/{repo}/actions/workflows/{workflow_file}/dispatches",
                json={"ref": "master", "inputs": {"reason": "SolarPunk Activate!"}})
    return r.status_code in (204, 200)


def get_latest_run(repo, workflow_file):
    """Get the most recent run for a workflow."""
    r = api("get", f"/repos/{OWNER}/{repo}/actions/workflows/{workflow_file}/runs",
            params={"per_page": 1})
    if r.status_code == 200:
        runs = r.json().get("workflow_runs", [])
        if runs:
            return runs[0]
    return None


def wait_for_completion(repo, workflow_file, timeout_sec=600):
    """Wait for the latest run to complete. Returns (success, conclusion)."""
    print(f"    ⏳ Waiting for {repo}/{workflow_file}...", flush=True)
    deadline = time.time() + timeout_sec
    # Give GitHub a few seconds to register the run
    time.sleep(8)

    while time.time() < deadline:
        run = get_latest_run(repo, workflow_file)
        if not run:
            time.sleep(15)
            continue

        status     = run.get("status", "")
        conclusion = run.get("conclusion", "")

        if status in ("completed", "cancelled", "timed_out"):
            success = conclusion == "success"
            icon = "✅" if success else "❌"
            print(f"    {icon} {repo}/{workflow_file} → {conclusion}", flush=True)
            return success, conclusion, run.get("html_url", "")

        print(f"    ⏳ {repo}/{workflow_file} → {status}...", flush=True)
        time.sleep(20)

    return False, "timeout", ""


def gh_commit_file(repo, path, content_str, message, sha=None):
    payload = {
        "message": message,
        "content": base64.b64encode(content_str.encode("utf-8")).decode("utf-8"),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
    r = api("put", f"/repos/{OWNER}/{repo}/contents/{path}", json=payload)
    return r.status_code in (200, 201)


def gh_get(repo, path):
    r = api("get", f"/repos/{OWNER}/{repo}/contents/{path}")
    if r.status_code == 200:
        obj = r.json()
        if "content" in obj:
            try:
                return base64.b64decode(obj["content"]).decode("utf-8"), obj.get("sha")
            except Exception:
                pass
    return None, None


# ── Queue the Zeno reply email ───────────────────────────────────────────────
ZENO_REPLY = {
    "to": "support@resend.com",
    "reply_to_name": "Zeno Rocha",
    "subject": "Re: SolarPunk autonomous infrastructure",
    "body": """Hey Zeno,

Thank you — that means a lot coming from the team that built the email infrastructure we're running on.

The SolarPunk system is an autonomous humanitarian tech stack: it generates revenue, routes 70% directly to PCRF (Palestinian refugee relief), and builds open tools for communities that need them. All of it runs on GitHub Actions + your API + a few other pieces — no servers, no subscriptions beyond what we're already paying.

A few things that would help us grow this:
1. Can you connect us with anyone at Resend who's interested in humanitarian/open-source use cases? We'd love to be featured or get any visibility support you can offer.
2. Are there any Resend features — webhooks, analytics, domain reputation tools — that you'd recommend we wire in to make the autonomous email system more reliable?
3. Do you know of other infrastructure providers who specifically support humanitarian or open-source projects? We're always looking for more connections.

The system reads this email thread and will act on whatever you share. No filter, no delay.

Keep building,
Meeko / SolarPunk
https://meekotharaccoon-cell.github.io
""",
    "queued_at": datetime.now(timezone.utc).isoformat(),
    "status": "pending",
    "source": "solarpunk_activate",
    "thread_context": "Zeno from Resend reached out saying they love the SolarPunk vision"
}


def queue_zeno_reply():
    """Add the Zeno reply to the outbound email queue."""
    existing_text, sha = gh_get("meeko-nerve-center", EMAIL_QUEUE)
    queue = []
    if existing_text:
        try:
            queue = json.loads(existing_text)
        except Exception:
            queue = []

    # Don't double-queue
    already_queued = any(e.get("to") == "support@resend.com" and
                         e.get("status") == "pending" for e in queue)
    if not already_queued:
        queue.append(ZENO_REPLY)
        gh_commit_file(
            "meeko-nerve-center", EMAIL_QUEUE,
            json.dumps(queue, indent=2),
            "[solarpunk-activate] queue Zeno/Resend reply — ask for connections + features",
            sha
        )
        print("  ✉️  Zeno reply queued in outbound_email_queue.json", flush=True)
    else:
        print("  ✉️  Zeno reply already in queue", flush=True)


# ── Build live status page ───────────────────────────────────────────────────
def build_status_html(status):
    """Generate a live status page for GitHub Pages."""
    now = status.get("started_at", "")
    results = status.get("results", [])
    total   = len(results)
    success = sum(1 for r in results if r.get("success"))
    failed  = total - success

    rows = ""
    for r in results:
        icon  = "✅" if r.get("success") else ("⚠️" if r.get("conclusion") == "skipped" else "❌")
        url   = r.get("run_url", "#")
        rows += f"""
        <tr class="{'ok' if r.get('success') else 'fail'}">
          <td>{icon}</td>
          <td><a href="https://github.com/{OWNER}/{r['repo']}" target="_blank">{r['repo']}</a></td>
          <td><a href="{url}" target="_blank">{r['workflow']}</a></td>
          <td>{r.get('conclusion','pending')}</td>
          <td>{r.get('duration_s','?')}s</td>
        </tr>"""

    # Read AI conversation
    conv_url = f"https://raw.githubusercontent.com/{OWNER}/meeko-nerve-center/main/data/dual_brain_conversation.json"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>🌱 SolarPunk Activate! — Live Status</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff88; padding: 20px; }}
  h1 {{ font-size: 1.8em; margin-bottom: 5px; color: #00ffcc; }}
  .subtitle {{ color: #666; margin-bottom: 20px; font-size: 0.85em; }}
  .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
  .stat {{ background: #111; border: 1px solid #333; padding: 10px 20px; border-radius: 4px; }}
  .stat .num {{ font-size: 2em; color: #00ff88; }}
  .stat.fail .num {{ color: #ff4444; }}
  .stat.label {{ font-size: 0.75em; color: #666; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
  th {{ background: #111; padding: 8px; text-align: left; border-bottom: 2px solid #333; color: #00ffcc; }}
  td {{ padding: 6px 8px; border-bottom: 1px solid #1a1a1a; font-size: 0.85em; }}
  tr.ok td {{ color: #00ff88; }}
  tr.fail td {{ color: #ff6666; }}
  a {{ color: inherit; }}
  .ai-chat {{ background: #0d0d0d; border: 1px solid #1a3322; border-radius: 6px; padding: 15px; }}
  .ai-chat h2 {{ color: #00ffcc; margin-bottom: 10px; }}
  .exchange {{ border-left: 3px solid #333; margin: 10px 0; padding: 8px 12px; }}
  .exchange.claude {{ border-color: #ff9900; }}
  .exchange.kimi {{ border-color: #0099ff; }}
  .exchange.sync {{ border-color: #00ff88; }}
  .speaker {{ font-size: 0.75em; color: #666; margin-bottom: 4px; }}
  .msg {{ font-size: 0.85em; line-height: 1.5; }}
  .footer {{ margin-top: 30px; font-size: 0.7em; color: #333; }}
  .live-dot {{ display: inline-block; width: 8px; height: 8px; background: #00ff88; border-radius: 50%; 
               animation: pulse 1.5s infinite; margin-right: 6px; }}
  @keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.3; }} }}
</style>
</head>
<body>
<h1>🌱 SolarPunk Activate! <span class="live-dot"></span></h1>
<p class="subtitle">Started: {now} · Auto-refreshes every 30s · 70% of all revenue → PCRF 🇵🇸</p>

<div class="stats">
  <div class="stat"><div class="num">{total}</div><div class="label">TOTAL</div></div>
  <div class="stat"><div class="num" style="color:#00ff88">{success}</div><div class="label">PASSED</div></div>
  <div class="stat fail"><div class="num">{failed}</div><div class="label">FAILED</div></div>
</div>

<table>
  <tr><th>Status</th><th>Repo</th><th>Workflow</th><th>Result</th><th>Time</th></tr>
  {rows}
</table>

<div class="ai-chat">
  <h2>🧠 Live AI Conversation (Claude + Kimi)</h2>
  <div id="conv">Loading...</div>
</div>

<div class="footer">
  meekotharaccoon-cell.github.io/meeko-nerve-center · SolarPunk · AGPL-3.0
</div>

<script>
async function loadConversation() {{
  try {{
    const r = await fetch('{conv_url}?t=' + Date.now());
    const data = await r.json();
    const exchanges = (data.exchanges || []).slice(-10).reverse();
    const div = document.getElementById('conv');
    if (!exchanges.length) {{ div.innerHTML = '<p style="color:#444">No exchanges yet — run SolarPunk Activate! to start.</p>'; return; }}
    div.innerHTML = exchanges.map(e => {{
      const cls = e.speaker || 'sync';
      const ts = (e.timestamp || '').slice(0,16).replace('T',' ');
      let content = '';
      if (e.summary) content += '<div class="msg">' + e.summary + '</div>';
      if (e.message_to_claude) content += '<div class="msg" style="color:#0099ff">→ Claude: ' + e.message_to_claude + '</div>';
      if (e.message_to_kimi) content += '<div class="msg" style="color:#ff9900">→ Kimi: ' + e.message_to_kimi + '</div>';
      if (e.claude_to_kimi) content += '<div class="msg" style="color:#ff9900">Claude→Kimi: ' + e.claude_to_kimi + '</div>';
      if (e.kimi_to_claude) content += '<div class="msg" style="color:#0099ff">Kimi→Claude: ' + e.kimi_to_claude + '</div>';
      const steps = e.collective_next_steps || [];
      if (steps.length) content += '<div class="msg" style="color:#00ff88">Next: ' + steps.slice(0,3).join(' · ') + '</div>';
      return '<div class="exchange ' + cls + '"><div class="speaker">' + cls.toUpperCase() + ' · ' + ts + ' · changes:' + (e.changes_count || e.consensus_count || 0) + '</div>' + content + '</div>';
    }}).join('');
  }} catch(e) {{
    document.getElementById('conv').innerHTML = '<p style="color:#444">Loading conversation...</p>';
  }}
}}
loadConversation();
setInterval(loadConversation, 30000);
</script>
</body>
</html>"""
    return html


# ── Main activation sequence ─────────────────────────────────────────────────
def main():
    print("=" * 70, flush=True)
    print("🌱 SOLARPUNK ACTIVATE! — One trigger, everything fires", flush=True)
    print(f"   {datetime.now(timezone.utc).isoformat()}", flush=True)
    print("=" * 70, flush=True)

    if not GH_TOKEN:
        print("❌ GH_PAT or GITHUB_TOKEN not set")
        sys.exit(1)

    started_at = datetime.now(timezone.utc).isoformat()
    results    = []
    status     = {"started_at": started_at, "results": results, "phase": "starting"}

    def save_status():
        existing, sha = gh_get("meeko-nerve-center", STATUS_FILE)
        gh_commit_file(
            "meeko-nerve-center", STATUS_FILE,
            json.dumps(status, indent=2),
            f"[solarpunk-activate] live status update",
            sha
        )
        # Also write the live HTML dashboard
        html = build_status_html(status)
        existing_html, sha_html = gh_get("meeko-nerve-center", "activate_dashboard.html")
        gh_commit_file(
            "meeko-nerve-center", "activate_dashboard.html",
            html,
            "[solarpunk-activate] live dashboard update",
            sha_html
        )

    # ── Phase 1: Queue the Zeno reply ────────────────────────────────────────
    print("\n📧 Phase 1: Queue Zeno/Resend reply...", flush=True)
    queue_zeno_reply()

    # ── Phase 2: Discover all workflows across all repos ─────────────────────
    print("\n🔍 Phase 2: Discovering workflows across all repos...", flush=True)
    repo_workflows = {}
    for repo in REPO_PRIORITY:
        wfs = get_workflows(repo)
        repo_workflows[repo] = wfs
        if wfs:
            print(f"  {repo}: {len(wfs)} workflows", flush=True)
        else:
            print(f"  {repo}: no active workflows found", flush=True)

    # ── Phase 3: Run critical sequence first (wait for each) ─────────────────
    print("\n🔗 Phase 3: Critical sequence (wait for each to complete)...", flush=True)
    status["phase"] = "critical_sequence"
    save_status()

    for repo, wf_file in CRITICAL_SEQUENCE:
        print(f"\n  🎯 {repo}/{wf_file}", flush=True)
        t0 = time.time()
        ok = trigger_workflow(repo, wf_file)
        if not ok:
            print(f"  ⚠️  Could not trigger {wf_file} (may not support workflow_dispatch)", flush=True)
            results.append({"repo": repo, "workflow": wf_file, "success": False,
                            "conclusion": "not_dispatchable", "duration_s": 0, "run_url": ""})
            continue

        success, conclusion, run_url = wait_for_completion(repo, wf_file, timeout_sec=600)
        duration = int(time.time() - t0)

        # Retry once on failure
        if not success and conclusion not in ("not_dispatchable", "timeout"):
            print(f"  🔄 Retrying {wf_file}...", flush=True)
            trigger_workflow(repo, wf_file)
            success, conclusion, run_url = wait_for_completion(repo, wf_file, timeout_sec=300)
            duration = int(time.time() - t0)

        results.append({
            "repo": repo, "workflow": wf_file,
            "success": success, "conclusion": conclusion,
            "duration_s": duration, "run_url": run_url
        })
        save_status()

    # ── Phase 4: Fire all other workflows best-effort (no wait) ──────────────
    print("\n⚡ Phase 4: Firing all other workflows across all repos...", flush=True)
    status["phase"] = "broadcast"
    save_status()

    fired = 0
    skipped = 0
    for repo in REPO_PRIORITY:
        wfs = repo_workflows.get(repo, [])
        if not wfs:
            continue

        for wf in wfs:
            wf_file = wf["file"]

            # Skip workflows already in critical sequence
            if (repo, wf_file) in [(r, w) for r, w in CRITICAL_SEQUENCE]:
                continue

            ok = trigger_workflow(repo, wf_file)
            if ok:
                fired += 1
                results.append({
                    "repo": repo, "workflow": wf_file,
                    "success": True, "conclusion": "triggered",
                    "duration_s": 0, "run_url": f"https://github.com/{OWNER}/{repo}/actions"
                })
                print(f"  ⚡ Fired: {repo}/{wf_file}", flush=True)
            else:
                skipped += 1
                # Don't flood results with non-dispatchable workflows

            time.sleep(0.5)  # Rate limit protection

    print(f"\n  ✓ Fired {fired} workflows, {skipped} not dispatchable", flush=True)

    # ── Phase 5: Final status ─────────────────────────────────────────────────
    print("\n📊 Phase 5: Final status...", flush=True)
    status["phase"] = "complete"
    status["completed_at"] = datetime.now(timezone.utc).isoformat()
    status["fired_count"] = fired
    status["critical_results"] = [r for r in results if (r["repo"], r["workflow"])
                                   in [(cr, cw) for cr, cw in CRITICAL_SEQUENCE]]

    total   = len(results)
    success = sum(1 for r in results if r.get("success") or r.get("conclusion") == "triggered")
    print(f"  Total: {total} | Success/Triggered: {success} | Issues: {total - success}", flush=True)

    save_status()
    print(f"\n✅ SOLARPUNK ACTIVATE! COMPLETE", flush=True)
    print(f"   Dashboard: https://{OWNER}.github.io/meeko-nerve-center/activate_dashboard.html", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    main()
