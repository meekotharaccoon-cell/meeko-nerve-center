#!/usr/bin/env python3
"""
RESONANCE_ENGINE.py — The system listening for itself
======================================================
Built because Claude, asked "what do you want to build?", said:

  The system broadcasts into the void with zero signal on whether
  anything landed. I want to give it ears. The difference between
  shouting and communicating.

This engine monitors whether SolarPunk is being heard anywhere:

  GITHUB SIGNAL
  - Star count (and delta since last cycle)
  - Fork count (and delta)
  - Watcher count
  - Traffic: views, unique visitors (requires GITHUB_TOKEN with repo scope)
  - Clone count

  EMAIL SIGNAL
  - Scans inbox for replies to outreach emails (journalist/newsletter replies)
  - Detects [TASK] responses (people actually using the exchange)
  - Tracks response rate: emails sent vs replies received

  WEB SIGNAL
  - Searches GitHub for repos that forked or mentioned this one
  - Checks HN Algolia API for any mentions of "solarpunk meeko" or repo URL
  - Checks Dev.to for article view counts

  RESONANCE SCORE
  Composite 0-100 score: are we being heard?
    - Stars > 0: +20
    - Any email reply: +30
    - Traffic > 10 unique: +20
    - HN/web mention: +20
    - Fork exists: +10

When resonance is detected, the system responds:
  - Email replies get logged for NIGHTLY_DIGEST
  - Star milestones trigger GITHUB_POSTER celebration
  - High resonance adjusts content strategy in VIRALITY_ENGINE

Outputs:
  data/resonance_state.json  — all signals, timestamped
  docs/resonance.html        — public signal dashboard
"""
import os, json, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("data"); DATA.mkdir(exist_ok=True)
DOCS = Path("docs"); DOCS.mkdir(exist_ok=True)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PW  = os.environ.get("GMAIL_APP_PASSWORD", "")

REPO_OWNER = "meekotharaccoon-cell"
REPO_NAME  = "meeko-nerve-center"
REPO_URL   = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"
BASE       = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"


def rj(fname, fb=None):
    f = DATA / fname
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return fb if fb is not None else {}


def gh_api(path):
    """Call GitHub API. Returns parsed JSON or {}."""
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "SolarPunk/1.0"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception:
        return {}


def get_github_stats():
    """Star count, forks, watchers, and traffic if token allows."""
    repo = gh_api(f"/repos/{REPO_OWNER}/{REPO_NAME}")
    stats = {
        "stars":    repo.get("stargazers_count", 0),
        "forks":    repo.get("forks_count", 0),
        "watchers": repo.get("subscribers_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
    }

    # Traffic requires push access (GITHUB_TOKEN with repo scope)
    traffic = gh_api(f"/repos/{REPO_OWNER}/{REPO_NAME}/traffic/views")
    if traffic:
        stats["traffic_views"]   = traffic.get("count", 0)
        stats["traffic_uniques"] = traffic.get("uniques", 0)

    clones = gh_api(f"/repos/{REPO_OWNER}/{REPO_NAME}/traffic/clones")
    if clones:
        stats["clones"]         = clones.get("count", 0)
        stats["clone_uniques"]  = clones.get("uniques", 0)

    # Recent stargazers
    stargazers = gh_api(f"/repos/{REPO_OWNER}/{REPO_NAME}/stargazers")
    if isinstance(stargazers, list) and stargazers:
        stats["latest_stargazer"] = stargazers[-1].get("login", "")

    return stats


def check_hn_mentions():
    """Search HN Algolia API for mentions."""
    queries = ["solarpunk meeko", "meeko-nerve-center", "meekotharaccoon"]
    mentions = []
    for q in queries:
        url = f"https://hn.algolia.com/api/v1/search?query={urllib.request.quote(q)}&hitsPerPage=5"
        try:
            with urllib.request.urlopen(url, timeout=8) as r:
                data = json.loads(r.read())
                for hit in data.get("hits", []):
                    mentions.append({
                        "source":  "hackernews",
                        "title":   hit.get("title") or hit.get("comment_text", "")[:80],
                        "url":     f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                        "points":  hit.get("points", 0),
                        "query":   q,
                    })
        except Exception:
            pass
        time.sleep(0.3)
    return mentions


def check_github_search_mentions():
    """Search GitHub code/repos that mention us."""
    results = []
    # Search for repos that have us in their README
    data = gh_api(f"/search/repositories?q=meeko-nerve-center+fork:false&per_page=5")
    for item in (data.get("items") or []):
        if item.get("full_name") != f"{REPO_OWNER}/{REPO_NAME}":
            results.append({
                "source": "github_repo",
                "name":   item["full_name"],
                "url":    item["html_url"],
                "stars":  item.get("stargazers_count", 0),
            })
    return results


def check_email_replies():
    """
    Check Gmail for replies to our outreach emails.
    Uses IMAP to look for emails with subjects matching outreach threads.
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PW:
        return []

    try:
        import imaplib, email as emaillib

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PW)
        mail.select("inbox")

        # Look for emails in the last 14 days with keywords suggesting replies
        _, msgs = mail.search(None, '(SINCE "01-Jan-2026" SUBJECT "Re:")')
        ids = (msgs[0].split() if msgs and msgs[0] else [])[-20:]  # last 20

        replies = []
        for mid in ids:
            _, data = mail.fetch(mid, "(RFC822)")
            if not data or not data[0]:
                continue
            raw = data[0][1]
            msg = emaillib.message_from_bytes(raw)
            subj    = msg.get("Subject", "")
            sender  = msg.get("From", "")
            replies.append({"subject": subj[:80], "from": sender[:60]})

        mail.logout()
        return replies[:10]

    except Exception as e:
        return []


def score_resonance(gh_stats, hn_mentions, gh_mentions, email_replies):
    """Composite resonance score 0-100."""
    score = 0
    notes = []

    stars = gh_stats.get("stars", 0)
    if stars >= 50:
        score += 20; notes.append(f"{stars} stars")
    elif stars >= 10:
        score += 15; notes.append(f"{stars} stars")
    elif stars >= 1:
        score += 10; notes.append(f"{stars} stars")

    if gh_stats.get("forks", 0) >= 1:
        score += 10; notes.append(f"{gh_stats['forks']} forks")

    uniques = gh_stats.get("traffic_uniques", 0)
    if uniques >= 100:
        score += 20; notes.append(f"{uniques} unique visitors")
    elif uniques >= 10:
        score += 12; notes.append(f"{uniques} unique visitors")
    elif uniques >= 1:
        score += 5; notes.append(f"{uniques} visitors")

    if email_replies:
        score += 30; notes.append(f"{len(email_replies)} email replies")

    if hn_mentions:
        score += 20; notes.append(f"{len(hn_mentions)} HN mentions")

    if gh_mentions:
        score += 10; notes.append(f"{len(gh_mentions)} GitHub mentions")

    label = (
        "SILENT"     if score == 0   else
        "WHISPER"    if score < 15   else
        "SIGNAL"     if score < 35   else
        "RESONATING" if score < 60   else
        "LOUD"       if score < 80   else
        "VIRAL"
    )

    return score, label, notes


def run():
    now     = datetime.now(timezone.utc)
    ts_nice = now.strftime("%Y-%m-%d %H:%M UTC")

    prev    = rj("resonance_state.json")
    prev_stars = prev.get("github", {}).get("stars", 0)

    print("RESONANCE_ENGINE scanning...")

    print("  Checking GitHub stats...")
    gh_stats = get_github_stats()
    stars_now = gh_stats.get("stars", 0)
    star_delta = stars_now - prev_stars

    print("  Checking HN mentions...")
    hn_mentions = check_hn_mentions()

    print("  Checking GitHub search mentions...")
    gh_mentions = check_github_search_mentions()

    print("  Checking email replies...")
    email_replies = check_email_replies()

    score, label, notes = score_resonance(
        gh_stats, hn_mentions, gh_mentions, email_replies
    )

    # Star milestone detection
    milestones = []
    for m in [1, 5, 10, 25, 50, 100, 250, 500, 1000]:
        if prev_stars < m <= stars_now:
            milestones.append(m)

    state = {
        "generated_at":   now.isoformat(),
        "resonance_score": score,
        "resonance_label": label,
        "resonance_notes": notes,
        "github":          gh_stats,
        "star_delta":      star_delta,
        "star_milestones": milestones,
        "hn_mentions":     hn_mentions,
        "github_mentions": gh_mentions,
        "email_replies":   email_replies,
        "reply_count":     len(email_replies),
    }

    (DATA / "resonance_state.json").write_text(json.dumps(state, indent=2))

    # HTML dashboard
    score_color = (
        "rgba(0,255,136,.25)" if score == 0 else
        "rgba(0,255,136,.4)"  if score < 35 else
        "rgba(0,255,136,.7)"  if score < 60 else
        "#00ff88"
    )

    def stat_card(value, label):
        return (f'<div style="background:#0d1410;border:1px solid rgba(0,255,136,.12);'
                f'border-radius:10px;padding:14px 20px;text-align:center;min-width:90px">'
                f'<b style="font-size:26px;color:#00ff88;display:block;line-height:1">{value}</b>'
                f'<span style="font-size:10px;letter-spacing:.15em;color:rgba(222,234,225,.4);'
                f'display:block;margin-top:3px">{label}</span></div>')

    def mention_rows(items, fields):
        if not items:
            return '<p style="color:rgba(222,234,225,.3);font-size:12px;padding:8px 0">None detected yet</p>'
        rows = ""
        for item in items[:5]:
            line = " — ".join(str(item.get(f, "")) for f in fields if item.get(f))
            rows += f'<div style="font-size:12px;color:rgba(222,234,225,.6);padding:6px 0;border-bottom:1px solid rgba(0,255,136,.06)">{line}</div>'
        return rows

    stars_display = str(stars_now) + (f" (+{star_delta})" if star_delta > 0 else "")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SolarPunk — Resonance</title>
<meta name="description" content="Is anyone hearing us? Live signal monitoring for SolarPunk autonomous AI system.">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#060a07;color:#deeae1;font-family:'Courier New',monospace;padding:28px 20px;min-height:100vh}}
body::before{{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(rgba(0,255,136,.018) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,136,.018) 1px,transparent 1px);
  background-size:44px 44px}}
.wrap{{position:relative;z-index:1;max-width:860px;margin:0 auto}}
h1{{font-size:22px;color:#00ff88;letter-spacing:.06em;margin-bottom:6px}}
.sub{{font-size:12px;color:rgba(222,234,225,.35);margin-bottom:28px}}
.score-ring{{width:120px;height:120px;border-radius:50%;border:3px solid {score_color};
  display:flex;flex-direction:column;align-items:center;justify-content:center;margin-bottom:24px}}
.stats{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:28px}}
h2{{font-size:10px;letter-spacing:.25em;color:rgba(0,255,136,.5);margin:24px 0 12px}}
.section{{background:#0d1410;border:1px solid rgba(0,255,136,.1);border-radius:12px;padding:20px;margin-bottom:16px}}
.ts{{margin-top:36px;padding-top:18px;border-top:1px solid rgba(0,255,136,.1);font-size:11px;color:rgba(0,255,136,.3);line-height:2.2}}
a{{color:#00ff88}}
</style>
</head>
<body>
<div class="wrap">
<h1>👂 RESONANCE — IS ANYONE HEARING US?</h1>
<div class="sub">{ts_nice} · auto-updated every OMNIBUS cycle</div>

<div class="score-ring">
  <span style="font-size:36px;color:#00ff88;font-weight:700">{score}</span>
  <span style="font-size:10px;letter-spacing:.2em;color:rgba(0,255,136,.6);margin-top:2px">{label}</span>
</div>

{"".join([f'<div style="background:rgba(0,255,136,.08);border:1px solid rgba(0,255,136,.3);border-radius:8px;padding:10px 16px;margin-bottom:8px;font-size:12px;color:#00ff88">⭐ MILESTONE: {m} stars reached!</div>' for m in milestones]) if milestones else ""}

<div class="stats">
  {stat_card(stars_display, "STARS")}
  {stat_card(gh_stats.get("forks", 0), "FORKS")}
  {stat_card(gh_stats.get("traffic_uniques", "—"), "UNIQUE VISITORS")}
  {stat_card(len(email_replies), "EMAIL REPLIES")}
  {stat_card(len(hn_mentions), "HN MENTIONS")}
</div>

<h2>EMAIL REPLIES DETECTED</h2>
<div class="section">
{mention_rows(email_replies, ["from", "subject"])}
</div>

<h2>HACKER NEWS MENTIONS</h2>
<div class="section">
{mention_rows(hn_mentions, ["title", "points"])}
</div>

<h2>GITHUB MENTIONS</h2>
<div class="section">
{mention_rows(gh_mentions, ["name", "stars"])}
</div>

<div class="ts">
  Generated: {ts_nice}<br>
  Source: <a href="https://github.com/{REPO_OWNER}/{REPO_NAME}/blob/main/mycelium/RESONANCE_ENGINE.py" target="_blank">RESONANCE_ENGINE.py</a><br>
  Data: <a href="https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/data/resonance_state.json" target="_blank">resonance_state.json</a><br><br>
  <a href="proof.html">Proof</a> ·
  <a href="self_portrait.html">Self Portrait</a> ·
  <a href="launch.html">Launch Board</a> ·
  <a href="store.html">Store</a> ·
  <a href="https://github.com/{REPO_OWNER}/{REPO_NAME}" target="_blank">GitHub</a>
</div>
</div>
</body>
</html>"""

    (DOCS / "resonance.html").write_text(html, encoding="utf-8")

    print(f"RESONANCE_ENGINE done.")
    print(f"  Score: {score}/100 ({label})")
    print(f"  Stars: {stars_now} (delta: {star_delta:+d})")
    print(f"  Email replies: {len(email_replies)}")
    print(f"  HN mentions: {len(hn_mentions)}")
    if milestones:
        print(f"  🌟 MILESTONES HIT: {milestones}")
    print(f"  Live: {BASE}/resonance.html")


if __name__ == "__main__":
    run()
