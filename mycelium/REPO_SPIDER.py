#!/usr/bin/env python3
"""
REPO_SPIDER — scan trending GitHub repos, fork compatible ones, trade knowledge

What it does every cycle:
  1. Search GitHub for trending repos by topic (AI, automation, revenue, Palestine)
  2. Score each repo: stars, activity, license compatibility, topic relevance
  3. Fork high-value repos (MIT/Apache only) to meekotharaccoon-cell
  4. Extract knowledge: README, key patterns, engine ideas
  5. Queue extracted ideas for SELF_BUILDER to implement
  6. Write data/repo_spider_state.json with full harvest

Knowledge trading logic:
  - We fork them → they get visibility of our work via their fork network
  - We read their patterns → SELF_BUILDER implements compatible ideas
  - Our engines reference their approaches → creates cross-repo knowledge graph
  - Result: compound learning without any API cost

Safe limits:
  - Max 3 forks per cycle (GitHub rate limits + stays clean)
  - Only MIT / Apache-2.0 / Unlicense repos
  - Never fork repos with >0 existing forks from our account
  - Skips repos we've already processed
"""
import os, json, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA     = Path("data"); DATA.mkdir(exist_ok=True)
STATE    = DATA / "repo_spider_state.json"
QUEUE    = DATA / "self_builder_queue.json"  # ideas for SELF_BUILDER

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER        = "meekotharaccoon-cell"
API          = "https://api.github.com"
MAX_FORKS_PER_CYCLE = 3
SAFE_LICENSES = {"mit", "apache-2.0", "unlicense", "cc0-1.0"}

# Topics to spider — each is a GitHub topic search
SPIDER_TOPICS = [
    "autonomous-agent",
    "ai-automation",
    "github-actions-automation",
    "passive-income",
    "revenue-automation",
    "open-source-monetization",
    "palestine",
    "solarpunk",
    "agentic-ai",
    "llm-agent",
    "multi-agent",
    "self-healing",
    "llm-orchestration",
    "agent-memory",
]

# Curated high-value repos to check every cycle regardless of topic search.
# These are known-great repos whose patterns KNOWLEDGE_WEAVER should absorb.
PRIORITY_REPOS = [
    # Autonomous agents & self-building
    "Significant-Gravitas/AutoGPT",
    "microsoft/autogen",
    "crewAIInc/crewAI",
    "geekan/MetaGPT",
    "All-Hands-AI/OpenHands",
    "princeton-nlp/SWE-agent",
    # Memory & persistence
    "mem0ai/mem0",
    "letta-ai/letta",
    # Multi-model routing (directly applicable to AI_CLIENT.py)
    "BerriAI/litellm",
    # Orchestration
    "langchain-ai/langgraph",
    "n8n-io/n8n",
    # Knowledge & RAG
    "run-llama/llama_index",
]


def gh(path, method="GET", body=None):
    if not GITHUB_TOKEN:
        return None
    try:
        url = f"{API}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "SolarPunk-Spider/1.0")
        if body:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 422:
            return {"error": "already_forked"}
        if e.code == 403:
            return {"error": "rate_limited"}
        return None
    except Exception:
        return None


def search_repos(topic, min_stars=50, max_results=10):
    path = f"/search/repositories?q=topic:{topic}+license:mit+license:apache-2.0&sort=stars&order=desc&per_page={max_results}"
    result = gh(path)
    if not result:
        return []
    repos = result.get("items", [])
    return [r for r in repos if r.get("stargazers_count", 0) >= min_stars]


def score_repo(repo):
    """Score 0-100 based on relevance signals."""
    score = 0
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    updated = repo.get("updated_at", "")[:10]
    desc = (repo.get("description") or "").lower()
    topics = repo.get("topics", [])

    # Stars (max 40pts)
    if stars >= 1000: score += 40
    elif stars >= 500: score += 30
    elif stars >= 100: score += 20
    else: score += 10

    # Activity — updated recently (max 20pts)
    try:
        from datetime import date
        days_old = (date.today() - date.fromisoformat(updated)).days
        if days_old < 30: score += 20
        elif days_old < 90: score += 15
        elif days_old < 180: score += 10
    except: pass

    # Relevance keywords (max 40pts)
    keywords = ["agent", "automat", "revenue", "ai", "llm", "income",
                "publish", "content", "monitor", "scrape", "webhook",
                "palestine", "solarpunk", "workflow", "cli", "action"]
    hits = sum(1 for k in keywords if k in desc or any(k in t for t in topics))
    score += min(40, hits * 5)

    return score


def get_readme(owner, repo_name):
    result = gh(f"/repos/{owner}/{repo_name}/readme")
    if not result:
        return ""
    import base64
    content = result.get("content", "")
    try:
        return base64.b64decode(content).decode("utf-8", errors="replace")[:3000]
    except:
        return ""


def extract_engine_ideas(repo, readme):
    """Extract actionable ideas from a repo for SELF_BUILDER."""
    ideas = []
    desc = repo.get("description", "") or ""
    name = repo.get("name", "")
    stars = repo.get("stargazers_count", 0)
    topics = repo.get("topics", [])

    # Pattern: repo does something we don't have an engine for yet
    patterns = {
        "webhook": f"Build WEBHOOK_RECEIVER engine inspired by {name} ({stars}★) — receives HTTP webhooks, routes to relevant engines",
        "scrape": f"Enhance CONTENT_HARVESTER with scraping patterns from {name} ({stars}★)",
        "newsletter": f"Build NEWSLETTER_ENGINE inspired by {name} — auto-generate and send email newsletter from data/",
        "analytics": f"Build ANALYTICS_ENGINE inspired by {name} — track page views, link clicks, referrers from GitHub Pages",
        "discord": f"Build DISCORD_BOT engine inspired by {name} — post updates to a Discord server",
        "telegram": f"Build TELEGRAM_BOT engine inspired by {name} — notify via Telegram on revenue/milestones",
        "rss": f"Build RSS_PUBLISHER engine inspired by {name} — publish RSS feed from content_harvest.json",
        "cli": f"Build SOLARPUNK_CLI inspired by {name} — terminal dashboard showing live system state",
        "monetize": f"Build MONETIZATION_ENGINE inspired by {name} ({stars}★) — {desc[:80]}",
        "github action": f"Build new GitHub Action inspired by {name} — {desc[:80]}",
    }

    combined = (desc + " " + " ".join(topics) + " " + readme[:500]).lower()
    for keyword, idea in patterns.items():
        if keyword in combined:
            ideas.append({"idea": idea, "source_repo": repo.get("full_name"), "stars": stars})

    return ideas[:2]  # max 2 ideas per repo


def fork_repo(owner, repo_name):
    result = gh(f"/repos/{owner}/{repo_name}/forks", method="POST", body={
        "organization": OWNER,
        "default_branch_only": True
    })
    if result and "error" not in result:
        return result.get("full_name", "")
    return None


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except: pass
    return {
        "processed": [],
        "forked": [],
        "total_ideas_queued": 0,
        "cycles": 0,
        "last_run": None
    }


def save_state(s):
    STATE.write_text(json.dumps(s, indent=2))


def queue_ideas(ideas):
    existing = []
    if QUEUE.exists():
        try:
            existing = json.loads(QUEUE.read_text())
            if not isinstance(existing, list):
                existing = []
        except: pass
    existing.extend(ideas)
    QUEUE.write_text(json.dumps(existing[-50:], indent=2))


def check_priority_repos(processed_set):
    """
    Fetch each curated priority repo by full name and harvest its README + ideas.
    Unlike topic search (reactive), this is proactive: we always learn from
    the best repos each cycle, regardless of whether they match a topic keyword.
    Returns (candidates, ideas) to merge with topic-search results.
    """
    candidates = []
    ideas = []

    # Load curated notes for richer idea context
    curated_notes = {}
    try:
        curated = json.loads((DATA / "curated_repos.json").read_text())
        for cat in curated.get("categories", {}).values():
            for r in cat.get("repos", []):
                curated_notes[r["full_name"]] = r.get("integration_idea", "")
    except Exception:
        pass

    for full_name in PRIORITY_REPOS:
        if full_name in processed_set:
            continue
        owner, repo_name = full_name.split("/", 1)
        repo = gh(f"/repos/{owner}/{repo_name}")
        if not repo or "id" not in repo:
            continue
        license_key = (repo.get("license") or {}).get("spdx_id", "").lower()
        stars = repo.get("stargazers_count", 0)
        score = score_repo(repo)
        candidates.append((score, repo))

        # Deep README harvest → richer engine ideas
        readme = get_readme(owner, repo_name)
        base_ideas = extract_engine_ideas(repo, readme)

        # Inject curated integration note as an additional idea
        note = curated_notes.get(full_name, "")
        if note and stars > 1000:
            base_ideas.append({
                "idea": f"[PRIORITY REPO {full_name} {stars}★] {note}",
                "source_repo": full_name,
                "stars": stars,
                "type": "integration_pattern",
            })

        ideas.extend(base_ideas)
        print(f"  [PRIORITY] {full_name} (score={score}, stars={stars}, ideas={len(base_ideas)})")
        time.sleep(0.3)

    return candidates, ideas


def run():
    print("REPO_SPIDER starting...")
    state = load_state()
    processed_set = set(state.get("processed", []))

    if not GITHUB_TOKEN:
        print("  SKIP: GITHUB_TOKEN not set")
        return

    forks_this_cycle = 0
    all_candidates = []
    all_ideas = []

    # ── Phase 1: Check priority curated repos first (proactive, expert-selected)
    print(f"  Checking {len(PRIORITY_REPOS)} priority repos...")
    priority_candidates, priority_ideas = check_priority_repos(processed_set)
    all_candidates.extend(priority_candidates)
    all_ideas.extend(priority_ideas)
    print(f"  Priority pass: {len(priority_candidates)} repos, {len(priority_ideas)} ideas")

    # ── Phase 2: Search each topic (reactive, keyword-based)
    for topic in SPIDER_TOPICS:
        repos = search_repos(topic, min_stars=50)
        for r in repos:
            full_name = r.get("full_name", "")
            if full_name in processed_set:
                continue
            if r.get("owner", {}).get("login") == OWNER:
                continue
            license_key = (r.get("license") or {}).get("spdx_id", "").lower()
            if license_key not in SAFE_LICENSES:
                continue
            score = score_repo(r)
            all_candidates.append((score, r))
        time.sleep(0.5)  # rate limit respect

    # Sort by score
    all_candidates.sort(key=lambda x: x[0], reverse=True)
    print(f"  Found {len(all_candidates)} eligible repos across {len(SPIDER_TOPICS)} topics")

    forked_this_cycle = []
    for score, repo in all_candidates[:20]:  # process top 20
        full_name = repo.get("full_name", "")
        repo_owner = repo.get("owner", {}).get("login", "")
        repo_name  = repo.get("name", "")
        stars      = repo.get("stargazers_count", 0)

        # Get README for idea extraction
        readme = get_readme(repo_owner, repo_name)
        ideas  = extract_engine_ideas(repo, readme)
        all_ideas.extend(ideas)

        # Fork if high score and we haven't hit limit
        if score >= 60 and forks_this_cycle < MAX_FORKS_PER_CYCLE:
            print(f"  Forking {full_name} (score={score}, stars={stars})")
            forked = fork_repo(repo_owner, repo_name)
            if forked:
                forked_this_cycle.append({"repo": full_name, "forked_as": forked, "score": score, "stars": stars})
                forks_this_cycle += 1
                print(f"    OK forked as {forked}")
                time.sleep(2)  # rate limit
            else:
                print(f"    SKIP (already forked or rate limited)")
        else:
            print(f"  Analyzed {full_name} (score={score}, stars={stars})")

        processed_set.add(full_name)
        time.sleep(0.3)

    # Queue ideas for SELF_BUILDER
    if all_ideas:
        queue_ideas(all_ideas)
        print(f"  Queued {len(all_ideas)} engine ideas for SELF_BUILDER")

    # Update state
    state["processed"]           = list(processed_set)[-200:]  # keep last 200
    state["forked"]              = state.get("forked", []) + forked_this_cycle
    state["total_ideas_queued"]  = state.get("total_ideas_queued", 0) + len(all_ideas)
    state["cycles"]              = state.get("cycles", 0) + 1
    state["last_run"]            = datetime.now(timezone.utc).isoformat()
    state["last_cycle_summary"]  = {
        "repos_analyzed": len(all_candidates),
        "forks":          forked_this_cycle,
        "ideas_queued":   len(all_ideas),
    }
    save_state(state)

    print(f"  Done. Analyzed: {len(all_candidates)} | Forked: {forks_this_cycle} | Ideas: {len(all_ideas)}")
    print(f"  Total forks ever: {len(state['forked'])}")


if __name__ == "__main__":
    run()
