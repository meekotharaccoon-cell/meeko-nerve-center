# Hacker News: Ask HN / Show HN

**Title:**
Show HN: Autonomous humanitarian AI on a 6-core i5, integrated graphics, $0/month

**Body:**
I built a fully autonomous system that runs 10 scheduled workflows daily on GitHub's free tier. It sells digital art ($1/piece, 70% to PCRF), sends grant applications, reads and responds to email, posts to social media, generates PDFs, and archives itself — without anyone touching it.

The hardware: Intel Core i5-8500, 32GB RAM, Intel UHD 630 (integrated graphics, no GPU). The cloud cost: $0. Everything runs on GitHub Actions free tier — 2,000 minutes/month on public repos.

The interesting parts:
- meeko_brain.py gates every automated action against a values file. Nothing goes out without passing an ethics check.
- unified_emailer.py replaced 4 parallel scripts that would have caused double-sends. One script, one log, all modes.
- The whole thing is AGPL-3.0 + Ethical Use Rider — forks can't be closed-sourced, can't be used for surveillance or weapons.
- START_HERE.md gets a stranger from zero to running fork in one afternoon.

The architecture question I found interesting: at what point does "human oversight" mean the human sets the values rather than approves each action? The system runs itself. The human built the brain. Those feel like different jobs.

https://github.com/meekotharaccoon-cell/meeko-nerve-center

Happy to answer questions about any piece of it.
