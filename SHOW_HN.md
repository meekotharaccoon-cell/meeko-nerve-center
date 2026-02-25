# Show HN: I built a self-healing autonomous AI that runs at $0/month and raises money for Gaza

*Copy this exactly into https://news.ycombinator.com/submit — Title + URL + Text fields below*

---

## TITLE (copy this exactly)

```
Show HN: Self-healing autonomous AI system, $0/month, open source, aimed at Gaza/Sudan/Congo
```

## URL

```
https://github.com/meekotharaccoon-cell/meeko-nerve-center
```

## TEXT (copy this exactly)

```
I built an autonomous system that runs entirely on GitHub Actions + GitHub Pages
at zero cost. Here’s what it actually does:

• Harvests knowledge daily from GitHub API, Wikipedia, arXiv, HackerNews, NASA
  — no scraping, all public APIs, zero auth required
• Runs a strategy brain (local Ollama when available, rule-based fallback in
  the cloud) that reads yesterday’s engagement signals and decides what to
  emphasize today
• Self-heals: when a workflow fails, a separate workflow triggers immediately,
  reads the actual error logs, diagnoses the error type, applies auto-fixes
  where possible, and writes plain-English instructions + free alternatives
  for anything it can’t fix automatically
• Generates content weighted toward what’s working based on real traffic/
  engagement data
• Tracks its own forks and updates a “Hall of Forks” in real time

The mission is humanitarian: 70% of all revenue goes to verified charities
for Gaza (PCRF, 4-star Charity Navigator), Congo, and Sudan.

Technically interesting bits:
• The strategy engine falls back gracefully through three tiers:
  Ollama (local LLM) → signal-weighted rules → day-of-week rotation
• The self-healer has a knowledge base of ~12 error categories with
  auto-fix actions for pip installs, git conflicts, missing dirs,
  disk pruning, etc.
• Everything is a single GitHub repo — no external databases, no
  cloud services, no API keys required to run the core system
• It writes its own EVOLVE.bat that gets smarter each generation

Total stack: GitHub Actions, GitHub Pages, Python stdlib + requests,
Ollama (optional), public APIs. $0/month.

Anyone can fork it and aim it at any cause:
https://github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/products/fork-guide.md

Happy to answer questions about the architecture.
```

---

## When to post

Best times for Show HN to hit front page:
- **Tuesday–Thursday, 9am–11am US Eastern** (2pm–4pm UTC)
- Avoid Monday mornings and Friday afternoons
- Don’t post when a major tech news story is breaking

## What to do when comments come in

- Answer every technical question directly and honestly
- If someone asks “why not use X instead” — explain the $0 constraint
- If someone critiques the humanitarian angle — engage respectfully, don’t argue
- If someone offers to contribute — reply quickly, link to spawn.html
- Pin a top comment with the gallery link once you have upvotes

## Other places to post (after HN gets traction)

1. **Dev.to** — mycelium/devto_article.md is already written, just paste it
2. **r/selfhosted** — mycelium/reddit_posts.md has the post ready
3. **r/MachineLearning** — focus on the self-healing + feedback loop architecture
4. **r/opensource** — focus on the $0 stack and AGPL license
5. **Lobste.rs** — same as HN post, technical community
6. **Mastodon/fediverse** — solarpunk and FOSS communities will share this
