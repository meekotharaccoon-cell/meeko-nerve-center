---
title: I built a fully autonomous humanitarian AI system for $0/month. Here's the architecture.
tags: opensource, github, python, solarpunk
published: true
---

This is a live system. Not a demo. Not a proof of concept. Running right now.

## What It Does

10 GitHub Actions workflows run daily. They:

- Send grant applications to foundations autonomously
- Post to Mastodon, Bluesky, Discord, and Dev.to (yes, including this article)
- Read email replies and respond to them automatically
- Sell digital art and route 70% of revenue to humanitarian causes
- Generate PDFs from markdown guides and commit them back to the repo
- Update YouTube video descriptions with current links
- Archive all live pages to the Internet Archive weekly
- Track revenue across multiple payment processors
- Update their own documentation with real stats

Monthly cost: **$0**.

Hardware: Intel Core i5-8500, 32GB RAM, Intel UHD 630 (integrated graphics — no GPU).

## The Key Architecture Decision

Everything runs on GitHub's free tier. 2,000 compute minutes/month on public repos. The repo IS the database — every workflow commits its results back, so there's no external storage.

```
GitHub Actions (free) → runs Python scripts
  → scripts read/write data/ directory
  → git commit data/ back to repo
  → repo contains current state of everything
  → next workflow reads from repo
```

No database. No server. No cost. The version control system is the persistence layer.

## The Brain

`meeko_brain.py` gates every automated action:

```python
def would_meeko_approve(action_description):
    """
    Before the system does anything, it checks:
    - Does this align with the stated mission?
    - Does this respect the people involved?
    - Would this be something I'd be embarrassed about?
    """
```

Nothing goes out — no email, no post, no external action — without passing this gate. The values are in the code, not in a human approving each action.

This is the answer to "but what if the AI does something wrong?" You build the values into the gate, not the approval loop.

## The Email System

This took the most iteration. The original repo had 4 separate email scripts, each with their own sent-log. That's a guaranteed double-send problem waiting to happen.

The fix: one script (`unified_emailer.py`), one log (`data/all_sent.json`), all modes via environment variable.

```bash
EMAIL_MODE=grants python mycelium/unified_emailer.py
EMAIL_MODE=tech python mycelium/unified_emailer.py
EMAIL_MODE=hello python mycelium/unified_emailer.py
```

One script. One memory. It knows every address it's ever contacted. Forever.

## The Cross-Poster

```python
ROTATING_POSTS = [
    { 'id': 'gallery_drop', 'type': 'art', 'text': '...', 'link': GALLERY },
    { 'id': 'fork_recruit_1', 'type': 'fork', 'text': '...', 'link': FORK },
    # 8 more...
]
```

One post queued daily. It cycles through 10 content types. Each type posts to Mastodon, Bluesky, Discord, Dev.to simultaneously. The log tracks what was posted where — no double-posts across the cycle.

3 of the 10 posts are fork-recruitment: they explain the system and link to the fork button. The system recruits its own successors.

## The License

AGPL-3.0 + Ethical Use Rider.

AGPL means: if you fork this and deploy it networked, you must keep it open source. The Ethical Use Rider adds: no surveillance, no weapons, no exploitation, no authoritarian use.

The values travel with the code. Every fork inherits them.

## The Forkability

`START_HERE.md` is written for a stranger who's never seen the repo. It gets them from zero to running fork in one afternoon. One Gmail App Password activates all 10 email workflows simultaneously. Each additional secret adds a new capability.

The system is designed to spread. It posts about itself. It explains itself. It makes forking easy. Then the fork does the same thing.

## What This Proves

The barrier to building ethical autonomous AI systems isn't:
- GPU clusters
- Cloud subscriptions
- Technical teams
- Venture capital

It's an afternoon and a GitHub account.

If this runs on integrated graphics for $0/month while raising money for Palestinian children's aid, then the barrier was never technical.

**Fork it:** https://github.com/meekotharaccoon-cell/meeko-nerve-center

---

*This article was posted autonomously by the SolarPunk Mycelium cross-poster.*
