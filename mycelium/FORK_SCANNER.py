# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
FORK_SCANNER — find people who forked our repo and reach out

A fork = someone thought "I want this" and clicked.
We never let that signal pass without acting.

1. Get all forks of meeko-nerve-center
2. Score each forker: builder? AI? Palestine solidarity?
3. For score >= 50: craft personalized outreach via Claude
4. Queue to outreach_state.json for EMAIL_OUTREACH to send
"""
import os, json, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA   = Path("data"); DATA.mkdir(exist_ok=True)
STATE  = DATA / "fork_scanner_state.json"
OUTBOX = DATA / "outreach_state.json"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
API_KEY      = os.environ.get("ANTHROPIC_API_KEY", "").strip()
OWNER        = "meekotharaccoon-cell"
REPO         = "meeko-nerve-center"
API          = "https://api.github.com"
MODEL        = "claude-haiku-4-5-20251001"


def gh(path):
    if not GITHUB_TOKEN: return None
    try:
        req = urllib.request.Request(f"{API}{path}")
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "SolarPunk-ForkScanner/1.0")
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except: return None


def score_forker(user):
    score = 20
    bio   = (user.get("bio") or "").lower()
    blog  = (user.get("blog") or "").lower()
    repos = user.get("public_repos", 0)
    followers = user.get("followers", 0)

    keywords = ["ai", "ml", "build", "maker", "indie", "hack", "automat",
                "python", "revenue", "startup", "freelan", "open source",
                "palestine", "gaza", "solidarity", "activist"]
    score += min(40, sum(1 for k in keywords if k in bio) * 8)
    if repos > 50: score += 15
    elif repos > 10: score += 8
    if followers > 100: score += 15
    elif followers > 10: score += 7
    if blog: score += 10
    return min(100, score)


def craft_message(user, score):
    if not API_KEY: return None
    name  = user.get("name") or user.get("login", "there")
    bio   = user.get("bio") or ""
    login = user.get("login", "")
    email = user.get("email") or ""

    system = """Write short genuine personal messages to people who forked an open-source project.
Tone: human, curious, appreciative. Not salesy. Under 80 words.
Output ONLY JSON: {"subject": "...", "body": "..."}"""

    prompt = f"""@{login} ({name}) just forked SolarPunk — autonomous AI revenue system, 15% to Palestine.
Bio: {bio[:100]}
Score: {score}/100
Email: {'yes' if email else 'no'}
Write a short followup message."""

    try:
        payload = json.dumps({"model": MODEL, "max_tokens": 256, "system": system,
            "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload,
            headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = json.loads(r.read())["content"][0]["text"].strip()
            return json.loads(raw.replace("```json","").replace("```","").strip())
    except: return None


def run():
    print("FORK_SCANNER starting...")
    if not GITHUB_TOKEN:
        print("  SKIP: GITHUB_TOKEN not set"); return

    state = {}
    if STATE.exists():
        try: state = json.loads(STATE.read_text())
        except: pass

    processed_set = set(state.get("processed", []))
    forks = gh(f"/repos/{OWNER}/{REPO}/forks?sort=newest&per_page=30")
    if not forks:
        print("  No forks yet (or API error)")
        state["cycles"] = state.get("cycles", 0) + 1
        state["last_run"] = datetime.now(timezone.utc).isoformat()
        STATE.write_text(json.dumps(state, indent=2))
        return

    print(f"  Found {len(forks)} forks total")
    new_forkers = []

    for fork in forks:
        fork_owner = fork.get("owner", {}).get("login", "")
        if fork_owner in processed_set or fork_owner == OWNER:
            continue

        user  = gh(f"/users/{fork_owner}") or {}
        score = score_forker(user)
        print(f"  Fork: @{fork_owner} score={score}")

        entry = {"login": fork_owner, "name": user.get("name", ""),
                 "email": user.get("email", ""), "bio": user.get("bio", ""),
                 "score": score, "forked_at": fork.get("created_at", ""),
                 "profile": f"https://github.com/{fork_owner}"}

        if score >= 50:
            msg = craft_message(user, score)
            if msg:
                entry.update({"outreach_subject": msg.get("subject",""),
                               "outreach_body": msg.get("body",""),
                               "outreach_status": "pending"})
                print(f"    Outreach crafted: {msg.get('subject','')}")

        new_forkers.append(entry)
        processed_set.add(fork_owner)
        time.sleep(0.5)

    state["processed"] = list(processed_set)
    state["forkers"]   = state.get("forkers", []) + new_forkers
    state["cycles"]    = state.get("cycles", 0) + 1
    state["last_run"]  = datetime.now(timezone.utc).isoformat()
    STATE.write_text(json.dumps(state, indent=2))

    outreach = {}
    if OUTBOX.exists():
        try: outreach = json.loads(OUTBOX.read_text())
        except: pass
    if not isinstance(outreach, dict): outreach = {}
    pending = outreach.get("pending", [])
    for f in new_forkers:
        if f.get("outreach_status") == "pending":
            pending.append({"type": "fork_followup",
                            "to": f.get("email") or f"https://github.com/{f['login']}",
                            "subject": f.get("outreach_subject",""),
                            "body": f.get("outreach_body",""),
                            "login": f["login"], "score": f["score"]})
    outreach["pending"] = pending
    OUTBOX.write_text(json.dumps(outreach, indent=2))

    print(f"  New: {len(new_forkers)} | Total processed: {len(processed_set)}")


if __name__ == "__main__":
    run()
