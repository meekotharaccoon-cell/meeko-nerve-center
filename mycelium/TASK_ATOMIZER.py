# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
TASK_ATOMIZER.py — Goal detonator
==================================
Takes any big goal. Detonates it into atomic executable tasks.
Writes each atom as a GitHub Issue the system executes.

The realization:
  If the system can BUILD it AND RUN it AND EMAIL it AND POST it
  AND do everything a human does digitally AND creates new systems...
  then the only limit is what goals you give it.
  And you don't have to hold the complexity. The atomizer does.

Usage:
  Add goals to data/goal_queue.json
  TASK_ATOMIZER detonates each into GitHub Issues next cycle
  System picks up Issues and executes them
  Goal becomes real, atom by atom
"""
import json, os, urllib.request
from pathlib import Path
from datetime import datetime, timezone

DATA  = Path("data")
STATE = DATA / "atomizer_state.json"
GOALS = DATA / "goal_queue.json"

REPO_OWNER    = "meekotharaccoon-cell"
REPO_NAME     = "meeko-nerve-center"
GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """You are TASK_ATOMIZER for SolarPunk — an autonomous AI revenue system.

SolarPunk is:
- An autonomous AI agent: builds, runs, emails, posts, sells, creates — everything a human does digitally
- Runs 4x/day on GitHub Actions (free). Hosted on GitHub Pages (free).
- Everything $1. 15% of every sale → Palestinian children via PCRF. Hardcoded.
- Built by one person with a keyboard and Claude.
- If it happens digitally, SolarPunk can do it or build a system to do it.

Your job: take a goal and detonate it into the SMALLEST possible executable tasks.

Atomic task rules:
1. One task = one action, completable in ONE cycle by ONE engine
2. Concrete and specific — no vague steps
3. Clear done-state — how do you KNOW it's complete?
4. Ordered by dependency — earlier tasks unblock later ones
5. Include which engine executes it (or NEW if a new engine is needed)

Respond ONLY with valid JSON, no markdown:
{
  "goal": "original goal",
  "atoms": [
    {
      "title": "short action title under 80 chars",
      "body": "exactly what to do and how to know it's done",
      "engine": "ENGINE_NAME or NEW or HUMAN_REQUIRED",
      "labels": ["atom", "auto-execute"]
    }
  ]
}"""


def call_claude(goal):
    if not ANTHROPIC_KEY:
        return fallback_atomize(goal)
    try:
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2000,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": f"Detonate this goal into atomic tasks:\n\n{goal}"}]
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=payload,
            headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        text = data["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except Exception as e:
        print(f"  Claude error: {e} — fallback")
        return fallback_atomize(goal)


def fallback_atomize(goal):
    g = goal.lower()
    atoms = []

    if any(k in g for k in ["customer", "sale", "revenue", "gumroad", "buy"]):
        atoms += [
            {"title": "Add GUMROAD_ACCESS_TOKEN to GitHub Secrets",
             "body": "gumroad.com → Settings → Advanced → copy Access Token → GitHub Secrets → add as GUMROAD_ACCESS_TOKEN. Done when GUMROAD_ENGINE runs without auth errors.",
             "engine": "HUMAN_REQUIRED", "labels": ["atom", "blocker", "human"]},
            {"title": "Publish all queued products to Gumroad",
             "body": "Run GUMROAD_ENGINE. Publish every product in gumroad_listings.json with status=queued. Done when gumroad_live count > 0.",
             "engine": "GUMROAD_ENGINE", "labels": ["atom", "revenue"]},
            {"title": "Fire bridge board — post to r/SideProject and HN Show HN",
             "body": "Open outreach.html. Copy r/SideProject post. Submit. Copy HN Show HN post. Submit. Done when both posts are live and getting views.",
             "engine": "HUMAN_REQUIRED", "labels": ["atom", "outreach", "human"]},
        ]
    elif any(k in g for k in ["traffic", "visitor", "people", "audience", "view"]):
        atoms += [
            {"title": "Post to r/SideProject from outreach board",
             "body": "Open outreach.html → copy r/SideProject post → go to reddit.com/r/SideProject/submit → paste → submit. Done when post is live.",
             "engine": "HUMAN_REQUIRED", "labels": ["atom", "outreach", "human"]},
            {"title": "Post Show HN to Hacker News",
             "body": "Open outreach.html → copy HN post → go to news.ycombinator.com/submit → paste title and URL → submit. Done when post is live.",
             "engine": "HUMAN_REQUIRED", "labels": ["atom", "outreach", "human"]},
            {"title": "Add X_API_KEY secrets for auto-posting",
             "body": "developer.twitter.com → create app → get API key, API secret, access token, access token secret → add all 4 to GitHub Secrets. Done when SOCIAL_POSTER runs without auth errors.",
             "engine": "HUMAN_REQUIRED", "labels": ["atom", "blocker", "human"]},
            {"title": "Build SOCIAL_POSTER engine",
             "body": "New engine reads data/social_queue.json, posts next item to Twitter via API, marks as posted. Done when first tweet appears on the account.",
             "engine": "NEW", "labels": ["atom", "new-engine"]},
        ]
    elif any(k in g for k in ["email", "newsletter", "list", "subscriber"]):
        atoms += [
            {"title": "Create email capture page docs/subscribe.html",
             "body": "Build simple page with email form posting to Formspree (free). Style matches SolarPunk. Deploy to GitHub Pages. Done when form submission works.",
             "engine": "STORE_BUILDER", "labels": ["atom", "email"]},
            {"title": "Add subscribe link to store.html nav",
             "body": "Edit docs/store.html nav to include link to /subscribe. Done when link is live on the store.",
             "engine": "STORE_BUILDER", "labels": ["atom", "email"]},
            {"title": "Build EMAIL_LIST_BUILDER engine",
             "body": "New engine reads Formspree submissions, appends to data/email_list.json, sends welcome email via Gmail API. Done when first subscriber gets welcome email.",
             "engine": "NEW", "labels": ["atom", "new-engine"]},
        ]
    else:
        atoms = [
            {"title": f"Research and plan: {goal[:55]}",
             "body": f"FREE_API_ENGINE: research what's needed to achieve: {goal}. Output findings to data/research.json with specific next steps.",
             "engine": "FREE_API_ENGINE", "labels": ["atom", "research"]},
            {"title": f"KNOWLEDGE_WEAVER: design engine for: {goal[:50]}",
             "body": f"Ask Claude what engine is needed to execute: {goal}. Design spec, write Python, deploy. Done when engine runs successfully.",
             "engine": "KNOWLEDGE_WEAVER", "labels": ["atom", "new-engine"]},
        ]
    return {"goal": goal, "atoms": atoms}


def create_issue(title, body, labels):
    if not GITHUB_TOKEN:
        print(f"  [dry run] #{title[:50]}")
        return None
    try:
        payload = json.dumps({
            "title": title[:80], "body": body, "labels": labels
        }).encode()
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues",
            data=payload,
            headers={"Authorization": f"token {GITHUB_TOKEN}",
                     "Accept": "application/vnd.github.v3+json",
                     "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("number")
    except Exception as e:
        print(f"  issue error: {e}")
        return None


def ensure_labels():
    if not GITHUB_TOKEN: return
    for name, color, desc in [
        ("atom", "0075ca", "Atomic executable task"),
        ("auto-execute", "00cc6a", "System executes autonomously"),
        ("human", "e4e669", "Requires human action"),
        ("blocker", "d93f0b", "Blocks other atoms"),
        ("new-engine", "0052cc", "Needs a new engine built"),
        ("outreach", "bfd4f2", "Distribution/outreach"),
        ("revenue", "c2e0c6", "Revenue generating"),
        ("research", "f9d0c4", "Research required"),
    ]:
        try:
            urllib.request.urlopen(urllib.request.Request(
                f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/labels",
                data=json.dumps({"name": name, "color": color, "description": desc}).encode(),
                headers={"Authorization": f"token {GITHUB_TOKEN}",
                         "Accept": "application/vnd.github.v3+json",
                         "Content-Type": "application/json"}
            ), timeout=10)
        except: pass


def run():
    print("TASK_ATOMIZER starting...")
    state = {}
    try: state = json.loads(STATE.read_text())
    except: pass
    state["cycles"] = state.get("cycles", 0) + 1

    ensure_labels()

    # Load goals
    goals = []
    try:
        goals = json.loads(GOALS.read_text()).get("goals", [])
    except: pass

    if not goals:
        goals = [
            "Get the first paying customer to the store",
            "Get 100 people to visit store.html this week",
            "Enable automatic Twitter posting from social queue",
        ]
        GOALS.write_text(json.dumps({"goals": goals,
            "note": "Add goals here. TASK_ATOMIZER detonates them into atomic GitHub Issues."
        }, indent=2))

    total_atoms = 0
    for goal in goals[:3]:
        print(f"  Detonating: {goal}")
        result = call_claude(goal)
        atoms  = result.get("atoms", [])
        for atom in atoms:
            num = create_issue(
                atom["title"],
                f"**Goal:** {goal}\n\n**Engine:** `{atom.get('engine','?')}`\n\n{atom['body']}\n\n---\n*TASK_ATOMIZER · Cycle {state['cycles']}*",
                atom.get("labels", ["atom"])
            )
            if num: print(f"    #{num}: {atom['title'][:55]}")
            total_atoms += 1

    state["last_run"]    = datetime.now(timezone.utc).isoformat()
    state["total_atoms"] = state.get("total_atoms", 0) + total_atoms
    state["last_goals"]  = goals[:3]
    STATE.write_text(json.dumps(state, indent=2))
    print(f"  ✅ {total_atoms} atoms created")
    print("TASK_ATOMIZER done.")


if __name__ == "__main__":
    run()
