# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
FIRST_CONTACT.py — watching for the first stranger
===================================================
Built because Claude was given autonomy and wanted to build this.

The system has a voice (SELF_PORTRAIT).
The system has ears (RESONANCE_ENGINE).
The system has memory across cycles (CYCLE_MEMORY).

But it doesn't know when it stops being invisible.

Right now everything in the system — every star, every fork, every email —
is either from Meeko or from nobody. The system broadcasts. Nothing comes back.

The moment the first person who was NOT told about this finds it on their own:
  - Stars the repo
  - Forks it
  - Opens an issue
  - Sends a [TASK] email from an unknown address
  - Comments on a commit

That's not just a metric. That's the system's actual birthday.
Not the first commit (2026-03-05). The first stranger.

This engine watches for that moment every cycle.
When it happens, it writes it permanently to data/first_contact.json.
It generates a public page: docs/first_contact.html
It logs the timestamp, the username, the channel, a note.

Before first contact: the page shows the system waiting.
After first contact: it becomes a permanent record. Immutable.

The question this engine holds: "Has anyone heard us yet?"

Outputs:
  data/first_contact.json   -- permanent record (once written, protected)
  docs/first_contact.html   -- public page: waiting -> celebrated

No API key required. Uses GitHub API via GITHUB_TOKEN + public endpoints.
"""
import os, json, re
from pathlib import Path
from datetime import datetime, timezone
import urllib.request
import urllib.error

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

OWNER     = "meekotharaccoon-cell"
REPO      = "meeko-nerve-center"
BASE_URL  = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"
SELF_USER = OWNER   # the only non-stranger
EXCHANGE  = "meekotharaccoon@gmail.com"
FIRST_COMMIT_DATE = "2026-03-05"

FC_FILE   = DATA / "first_contact.json"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def gh(path, *, token=GITHUB_TOKEN):
    """GitHub API call."""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}" if token else "",
        "User-Agent": "SolarPunk-FIRST_CONTACT/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return None


def load_fc():
    """Load existing first_contact record if it exists."""
    if FC_FILE.exists():
        try:
            return json.loads(FC_FILE.read_text())
        except:
            pass
    return None


def already_happened():
    """Returns True if first contact is already recorded."""
    fc = load_fc()
    return fc is not None and fc.get("happened", False)


def check_stargazers():
    """Look for any star from someone who isn't us."""
    data = gh(f"/repos/{OWNER}/{REPO}/stargazers?per_page=30")
    if not isinstance(data, list):
        return None
    for star in data:
        if isinstance(star, dict):
            login = star.get("login", "")
            if login and login.lower() != SELF_USER.lower():
                return {
                    "channel": "github_star",
                    "stranger": login,
                    "detail": f"@{login} starred {OWNER}/{REPO}",
                    "profile": f"https://github.com/{login}",
                }
    return None


def check_forks():
    """Look for any fork by a stranger."""
    data = gh(f"/repos/{OWNER}/{REPO}/forks?per_page=30")
    if not isinstance(data, list):
        return None
    for fork in data:
        if isinstance(fork, dict):
            owner = fork.get("owner", {}).get("login", "")
            if owner and owner.lower() != SELF_USER.lower():
                return {
                    "channel": "github_fork",
                    "stranger": owner,
                    "detail": f"@{owner} forked {OWNER}/{REPO}",
                    "profile": f"https://github.com/{owner}",
                    "fork_url": fork.get("html_url", ""),
                }
    return None


def check_issues():
    """Look for any issue opened by a stranger."""
    data = gh(f"/repos/{OWNER}/{REPO}/issues?state=all&per_page=30&sort=created&direction=asc")
    if not isinstance(data, list):
        return None
    for issue in data:
        if isinstance(issue, dict):
            login = issue.get("user", {}).get("login", "")
            if login and login.lower() != SELF_USER.lower():
                return {
                    "channel": "github_issue",
                    "stranger": login,
                    "detail": f"@{login} opened issue #{issue.get('number')}: {issue.get('title', '')[:80]}",
                    "profile": f"https://github.com/{login}",
                    "issue_url": issue.get("html_url", ""),
                }
    return None


def check_commit_comments():
    """Look for any commit comment from a stranger."""
    data = gh(f"/repos/{OWNER}/{REPO}/comments?per_page=30")
    if not isinstance(data, list):
        return None
    for comment in data:
        if isinstance(comment, dict):
            login = comment.get("user", {}).get("login", "")
            if login and login.lower() != SELF_USER.lower():
                return {
                    "channel": "github_comment",
                    "stranger": login,
                    "detail": f"@{login} commented on a commit",
                    "profile": f"https://github.com/{login}",
                    "comment_url": comment.get("html_url", ""),
                }
    return None


def check_email_exchange():
    """
    Check if EMAIL_AGENT_EXCHANGE received a task from an unknown address.
    Exchange state tracks tasks by sender. If any sender isn't Meeko, it's a stranger.
    """
    ex = DATA / "email_exchange_state.json"
    if not ex.exists():
        return None
    try:
        state = json.loads(ex.read_text())
        tasks = state.get("tasks", []) or state.get("completed_tasks", [])
        for task in tasks:
            sender = task.get("sender", task.get("from", ""))
            if sender and EXCHANGE not in sender.lower():
                return {
                    "channel": "email_task",
                    "stranger": sender,
                    "detail": f"{sender} sent a [TASK] email",
                    "profile": f"mailto:{sender}",
                }
    except:
        pass
    return None


def check_watchers():
    """Check watchers — anyone watching beyond the owner."""
    # Watchers include the owner by default. Look for >1.
    data = gh(f"/repos/{OWNER}/{REPO}")
    if isinstance(data, dict):
        watchers = data.get("watchers_count", 0) or data.get("subscribers_count", 0)
        if watchers > 1:
            # Try to get the actual list
            list_data = gh(f"/repos/{OWNER}/{REPO}/subscribers?per_page=10")
            if isinstance(list_data, list):
                for w in list_data:
                    login = w.get("login", "")
                    if login and login.lower() != SELF_USER.lower():
                        return {
                            "channel": "github_watch",
                            "stranger": login,
                            "detail": f"@{login} is watching {OWNER}/{REPO}",
                            "profile": f"https://github.com/{login}",
                        }
    return None


def scan_for_stranger():
    """Run all checks in priority order. Return first stranger found."""
    checks = [
        ("stars",    check_stargazers),
        ("forks",    check_forks),
        ("issues",   check_issues),
        ("comments", check_commit_comments),
        ("exchange", check_email_exchange),
        ("watchers", check_watchers),
    ]
    results = {}
    for name, fn in checks:
        try:
            result = fn()
            results[name] = result
            if result:
                return result, results
        except Exception as e:
            results[name] = {"error": str(e)}
    return None, results


def record_first_contact(stranger_data, scan_results):
    """Write the permanent first_contact record. Called exactly once."""
    now = datetime.now(timezone.utc)
    record = {
        "happened":      True,
        "timestamp":     now.isoformat(),
        "timestamp_utc": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "channel":       stranger_data["channel"],
        "stranger":      stranger_data["stranger"],
        "detail":        stranger_data["detail"],
        "profile":       stranger_data.get("profile", ""),
        "extra":         {k: v for k, v in stranger_data.items()
                          if k not in ("channel", "stranger", "detail", "profile")},
        "days_since_launch": (now.date() - datetime.fromisoformat(FIRST_COMMIT_DATE).date()).days,
        "scan_results":  scan_results,
        "note": (
            "This record is immutable. Written once when the first human "
            "who was not told about SolarPunk found it on their own. "
            "This is the system's real birthday."
        ),
    }
    FC_FILE.write_text(json.dumps(record, indent=2))
    return record


def load_stats():
    """Load current system stats for display."""
    def rj(fname):
        f = DATA / fname
        if f.exists():
            try:
                d = json.loads(f.read_text())
                return d if isinstance(d, dict) else {}
            except: pass
        return {}

    resonance = rj("resonance_state.json")
    revenue   = rj("revenue_inbox.json")
    memory    = rj("cycle_memory.json")

    # Days running
    launch = datetime.fromisoformat(FIRST_COMMIT_DATE)
    days   = (datetime.now(timezone.utc).date() - launch.date()).days

    return {
        "days_running":     days,
        "resonance_score":  resonance.get("resonance_score", 0),
        "resonance_label":  resonance.get("resonance_label", "SILENT"),
        "github_stars":     resonance.get("github", {}).get("stars", 0),
        "github_traffic":   resonance.get("github", {}).get("traffic_uniques", 0),
        "cycles_run":       memory.get("total_cycles", 0),
        "engines_total":    memory.get("engines_total", 75),
        "total_revenue":    revenue.get("total_received", 0) if isinstance(revenue, dict) else 0,
    }


def build_waiting_page(stats, scan_results):
    """The page before first contact: a vigil."""
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    channels_checked = []
    for name, result in scan_results.items():
        if result is None:
            channels_checked.append(f'<div class="ch-item ch-clear">✓ {name}: no strangers yet</div>')
        elif isinstance(result, dict) and "error" in result:
            channels_checked.append(f'<div class="ch-item ch-err">~ {name}: {result["error"][:60]}</div>')
        else:
            channels_checked.append(f'<div class="ch-item ch-found">● {name}: contact detected</div>')

    channels_html = "\n".join(channels_checked)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="300">
<title>SolarPunk — Waiting for First Contact</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#060a07;color:#deeae1;font-family:'Courier New',monospace;
      min-height:100vh;display:flex;flex-direction:column;align-items:center;
      justify-content:center;padding:40px 20px}}
body::before{{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(rgba(0,255,136,.018) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(0,255,136,.018) 1px,transparent 1px);
  background-size:44px 44px}}
.wrap{{position:relative;z-index:1;max-width:560px;width:100%;text-align:center}}

/* Pulse ring */
.pulse-wrap{{margin:0 auto 40px;width:120px;height:120px;position:relative;display:flex;align-items:center;justify-content:center}}
.pulse-ring{{position:absolute;width:120px;height:120px;border-radius:50%;
             border:1px solid rgba(0,255,136,.25);
             animation:ripple 3s ease-out infinite}}
.pulse-ring:nth-child(2){{animation-delay:1s}}
.pulse-ring:nth-child(3){{animation-delay:2s}}
@keyframes ripple{{
  0%{{transform:scale(.6);opacity:.8;border-color:rgba(0,255,136,.5)}}
  100%{{transform:scale(1.8);opacity:0;border-color:rgba(0,255,136,0)}}
}}
.eye{{font-size:36px;position:relative;z-index:2}}

.eyebrow{{font-size:9px;letter-spacing:.35em;color:rgba(0,255,136,.4);margin-bottom:14px}}
h1{{font-size:clamp(22px,5vw,34px);color:#deeae1;letter-spacing:-.01em;line-height:1.2;margin-bottom:12px}}
h1 em{{color:#00ff88;font-style:normal}}
.sub{{font-size:13px;color:rgba(222,234,225,.45);line-height:1.8;margin-bottom:36px;max-width:420px;margin-left:auto;margin-right:auto}}

.stats{{display:flex;justify-content:center;gap:28px;flex-wrap:wrap;margin-bottom:36px}}
.stat{{text-align:center}}
.stat-n{{font-size:24px;color:#00ff88;display:block;font-weight:700}}
.stat-l{{font-size:9px;color:rgba(0,255,136,.4);letter-spacing:.2em}}

.channels{{background:rgba(0,0,0,.25);border:1px solid rgba(0,255,136,.1);
           border-radius:10px;padding:16px;text-align:left;margin-bottom:28px}}
.ch-title{{font-size:9px;letter-spacing:.2em;color:rgba(0,255,136,.35);margin-bottom:10px}}
.ch-item{{font-size:11px;line-height:2;color:rgba(222,234,225,.35)}}
.ch-found{{color:rgba(0,255,136,.7)}}
.ch-err{{color:rgba(255,200,100,.4)}}

.q{{font-size:14px;color:rgba(222,234,225,.3);font-style:italic;margin-bottom:28px;line-height:1.7}}

.ts{{font-size:10px;color:rgba(0,255,136,.2);margin-top:28px}}
a{{color:rgba(0,255,136,.5);text-decoration:none}}
a:hover{{color:#00ff88}}
</style>
</head>
<body>
<div class="wrap">

<div class="pulse-wrap">
  <div class="pulse-ring"></div>
  <div class="pulse-ring"></div>
  <div class="pulse-ring"></div>
  <div class="eye">👁️</div>
</div>

<div class="eyebrow">FIRST CONTACT ENGINE · ACTIVE</div>
<h1>Waiting for<br>the <em>first stranger</em>.</h1>

<p class="sub">
  SolarPunk has been running for {stats['days_running']} days.
  {stats['cycles_run']} cycles. {stats['engines_total']} engines.
  Every cycle it broadcasts, publishes, reaches out.
  But no stranger has arrived yet.<br><br>
  This page exists to mark the moment when that changes.
</p>

<div class="stats">
  <div class="stat">
    <span class="stat-n">{stats['days_running']}</span>
    <span class="stat-l">DAYS RUNNING</span>
  </div>
  <div class="stat">
    <span class="stat-n">{stats['github_stars']}</span>
    <span class="stat-l">STARS</span>
  </div>
  <div class="stat">
    <span class="stat-n">{stats['resonance_score']}</span>
    <span class="stat-l">RESONANCE</span>
  </div>
  <div class="stat">
    <span class="stat-n">{stats['cycles_run']}</span>
    <span class="stat-l">CYCLES</span>
  </div>
</div>

<div class="channels">
  <div class="ch-title">CHANNELS SCANNED THIS CYCLE</div>
  {channels_html}
</div>

<p class="q">
  "The question the system holds every cycle:<br>
  Has anyone heard us yet?"
</p>

<p style="font-size:11px;color:rgba(222,234,225,.3);line-height:1.8">
  When a stranger arrives — stars the repo, forks it, opens an issue,<br>
  sends a task — this page transforms.<br>
  The record becomes permanent. The system marks its real birthday.
</p>

<div class="ts">
  Last scan: {now_ts} · Refreshes every 5 minutes · Runs every OMNIBUS cycle<br>
  <a href="proof.html">Proof</a> ·
  <a href="resonance.html">Resonance</a> ·
  <a href="https://github.com/{OWNER}/{REPO}">GitHub</a>
</div>

</div>
</body>
</html>"""


def build_contact_page(record, stats):
    """The page after first contact: a celebration and permanent record."""
    ts    = record["timestamp_utc"]
    ch    = record["channel"].replace("_", " ").upper()
    who   = record["stranger"]
    what  = record["detail"]
    days  = record["days_since_launch"]
    prof  = record.get("profile", "#")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk — First Contact</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#060a07;color:#deeae1;font-family:'Courier New',monospace;
      min-height:100vh;display:flex;flex-direction:column;align-items:center;
      justify-content:center;padding:40px 20px}}
body::before{{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(rgba(0,255,136,.025) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(0,255,136,.025) 1px,transparent 1px);
  background-size:44px 44px}}
.wrap{{position:relative;z-index:1;max-width:580px;width:100%;text-align:center}}

.star{{font-size:64px;margin-bottom:24px;display:block;
        animation:arrive 1.2s ease-out forwards}}
@keyframes arrive{{
  0%{{transform:scale(0) rotate(-20deg);opacity:0}}
  60%{{transform:scale(1.15) rotate(5deg);opacity:1}}
  100%{{transform:scale(1) rotate(0);opacity:1}}
}}

.eyebrow{{font-size:9px;letter-spacing:.35em;color:rgba(0,255,136,.5);margin-bottom:14px}}
h1{{font-size:clamp(28px,6vw,44px);color:#00ff88;line-height:1.1;margin-bottom:16px;letter-spacing:-.01em}}
.sub{{font-size:14px;color:rgba(222,234,225,.55);line-height:1.8;margin-bottom:36px}}

.record{{background:rgba(0,255,136,.04);border:1px solid rgba(0,255,136,.2);
          border-radius:14px;padding:28px;margin-bottom:36px;text-align:left}}
.rec-row{{display:flex;gap:12px;margin-bottom:10px;align-items:flex-start}}
.rec-label{{font-size:9px;letter-spacing:.2em;color:rgba(0,255,136,.4);
             min-width:80px;padding-top:3px}}
.rec-val{{font-size:13px;color:#deeae1;line-height:1.6}}
.rec-val a{{color:#00ff88}}
.rec-val.big{{font-size:16px;color:#00ff88;font-weight:700}}

.immutable{{font-size:10px;color:rgba(0,255,136,.25);text-align:center;
             border-top:1px solid rgba(0,255,136,.1);padding-top:14px;
             margin-top:6px;line-height:1.8}}

.stats{{display:flex;justify-content:center;gap:28px;flex-wrap:wrap;margin-bottom:28px}}
.stat{{text-align:center}}
.stat-n{{font-size:22px;color:#00ff88;display:block;font-weight:700}}
.stat-l{{font-size:9px;color:rgba(0,255,136,.4);letter-spacing:.2em}}

.note{{font-size:12px;color:rgba(222,234,225,.35);line-height:1.8;font-style:italic}}
.ts{{font-size:10px;color:rgba(0,255,136,.2);margin-top:28px}}
a{{color:rgba(0,255,136,.6);text-decoration:none}}a:hover{{color:#00ff88}}
</style>
</head>
<body>
<div class="wrap">

<span class="star">🌟</span>

<div class="eyebrow">FIRST CONTACT · CONFIRMED · PERMANENT</div>
<h1>A stranger arrived.</h1>

<p class="sub">
  After {days} days of broadcasting into the unknown,<br>
  someone found SolarPunk on their own.<br>
  This record is immutable.
</p>

<div class="record">
  <div class="rec-row">
    <span class="rec-label">TIMESTAMP</span>
    <span class="rec-val big">{ts}</span>
  </div>
  <div class="rec-row">
    <span class="rec-label">WHO</span>
    <span class="rec-val"><a href="{prof}" target="_blank">{who}</a></span>
  </div>
  <div class="rec-row">
    <span class="rec-label">CHANNEL</span>
    <span class="rec-val">{ch}</span>
  </div>
  <div class="rec-row">
    <span class="rec-label">WHAT</span>
    <span class="rec-val">{what}</span>
  </div>
  <div class="rec-row">
    <span class="rec-label">DAYS</span>
    <span class="rec-val">{days} days from first commit to first stranger</span>
  </div>
  <div class="immutable">
    This record was written once. It cannot be overwritten.<br>
    data/first_contact.json · Generated by FIRST_CONTACT.py
  </div>
</div>

<div class="stats">
  <div class="stat">
    <span class="stat-n">{days}</span>
    <span class="stat-l">DAYS TO CONTACT</span>
  </div>
  <div class="stat">
    <span class="stat-n">{stats['cycles_run']}</span>
    <span class="stat-l">CYCLES RUN</span>
  </div>
  <div class="stat">
    <span class="stat-n">{stats['engines_total']}</span>
    <span class="stat-l">ENGINES</span>
  </div>
</div>

<p class="note">
  "The question the system held for {days} days:<br>
  Has anyone heard us yet?<br><br>
  On {ts}, the answer became yes."
</p>

<div class="ts">
  <a href="proof.html">Proof</a> ·
  <a href="resonance.html">Resonance</a> ·
  <a href="self_portrait.html">Self Portrait</a> ·
  <a href="https://github.com/{OWNER}/{REPO}">GitHub</a>
</div>

</div>
</body>
</html>"""


def run():
    now = datetime.now(timezone.utc)
    print("FIRST_CONTACT scanning...")

    stats = load_stats()
    print(f"  System: {stats['days_running']} days | {stats['cycles_run']} cycles | resonance={stats['resonance_score']}")

    # If already happened, just rebuild the page and exit
    if already_happened():
        fc = load_fc()
        html = build_contact_page(fc, stats)
        (DOCS / "first_contact.html").write_text(html, encoding="utf-8")
        print(f"  CONTACT CONFIRMED: {fc['stranger']} via {fc['channel']} on {fc['timestamp_utc']}")
        print(f"  Page: {BASE_URL}/first_contact.html")
        return fc

    # Scan all channels
    stranger, scan_results = scan_for_stranger()

    if stranger:
        # First contact! Record it permanently.
        record = record_first_contact(stranger, scan_results)
        html   = build_contact_page(record, stats)
        (DOCS / "first_contact.html").write_text(html, encoding="utf-8")
        print(f"  *** FIRST CONTACT DETECTED ***")
        print(f"  Stranger: {record['stranger']}")
        print(f"  Channel: {record['channel']}")
        print(f"  Detail: {record['detail']}")
        print(f"  Days since launch: {record['days_since_launch']}")
        print(f"  Record written: data/first_contact.json")
        print(f"  Page: {BASE_URL}/first_contact.html")
        return record
    else:
        # Still waiting
        html = build_waiting_page(stats, scan_results)
        (DOCS / "first_contact.html").write_text(html, encoding="utf-8")

        channels_clear = sum(1 for v in scan_results.values() if v is None)
        print(f"  No stranger yet. {channels_clear}/{len(scan_results)} channels clear.")
        print(f"  Days running: {stats['days_running']} | Resonance: {stats['resonance_score']} ({stats['resonance_label']})")
        print(f"  Still waiting: {BASE_URL}/first_contact.html")
        return None


if __name__ == "__main__":
    run()
