# 🌱 Meeko Nerve Center

**A self-replicating autonomous AI system. $0/month. Open source. Aimed at humanitarian crises.**

[![Workflows](https://img.shields.io/badge/workflows-active-brightgreen)](https://github.com/meekotharaccoon-cell/meeko-nerve-center/actions)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue)](LICENSE)
[![Forks](https://img.shields.io/github/forks/meekotharaccoon-cell/meeko-nerve-center?style=social)](https://github.com/meekotharaccoon-cell/meeko-nerve-center/fork)

---

## What this is

A fully autonomous system that:
- **Learns** from the open internet every day (GitHub, Wikipedia, arXiv, HackerNews, NASA)
- **Thinks** using a local Ollama LLM + rule-based fallback strategy engine
- **Heals itself** when workflows break — diagnoses errors, applies fixes, writes plain-English instructions for anything it can’t auto-fix
- **Generates content** weighted toward what’s actually working based on real signal data
- **Raises money** for Gaza, Congo, and Sudan through art sales, digital products, and direct donation links
- **Runs at $0/month** on GitHub Actions + GitHub Pages. No servers. No subscriptions.

Built by one person. No VC. No team. No budget.

---

## The mission

Over 40,000 killed in Gaza. 8 million displaced in Sudan. Eastern Congo in ongoing crisis.

This system exists to make it impossible to ignore those numbers — and to turn attention into direct action:

- **[Gaza Rose Gallery](https://meekotharaccoon-cell.github.io/gaza-rose-gallery)** — 56 original artworks, $1 each. 70% goes directly to [PCRF](https://www.pcrf.net) (4-star Charity Navigator, EIN 93-1057665).
- **[$5 Fork Guide](https://github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/products/fork-guide.md)** — build your own version of this system, aimed at any cause
- **Direct donation links** on every page to verified charities for all three crises

---

## How it works

```
5:00 AM UTC — Knowledge Harvester
  └─ Pulls from GitHub API, Wikipedia, arXiv, HackerNews, NASA
  └─ Saves to knowledge/ ─ system reads this as context

6:00 AM UTC — Feedback Loop
  └─ Signal Tracker: what drove traffic/sales/engagement yesterday?
  └─ Loop Brain: Ollama (or rule-based) decides today’s strategy
  └─ Content Engine: generates posts weighted toward what works

7:00 AM UTC — Self Healer
  └─ Reads actual GitHub Actions failure logs
  └─ Diagnoses: missing packages, rate limits, git conflicts, syntax errors…
  └─ Auto-fixes what it can, writes FIXES_NEEDED.md for anything it can’t
  └─ Drafts outreach emails ─ human just reviews + sends

Hourly — Wiring Status
  └─ Checks which capabilities are live vs. missing
  └─ Updates dashboard widget in real time

Daily — Fork Tracker
  └─ Tracks every fork of this repo
  └─ Updates Hall of Forks, RESULTS.md, FORK_REGISTRY.md
```

---

## Live pages

| Page | What it does |
|------|--------------|
| [Dashboard](https://meekotharaccoon-cell.github.io/meeko-nerve-center/dashboard.html) | Live system status, wiring health, signals |
| [Spawn](https://meekotharaccoon-cell.github.io/meeko-nerve-center/spawn.html) | How to fork this system + Hall of Forks |
| [Revenue](https://meekotharaccoon-cell.github.io/meeko-nerve-center/revenue.html) | All revenue streams in one place |
| [Proliferator](https://meekotharaccoon-cell.github.io/meeko-nerve-center/proliferator.html) | Free legal tools (TCPA, FDCPA) — drives organic traffic |
| [App](https://meekotharaccoon-cell.github.io/meeko-nerve-center/app.html) | Main interface |
| [Links](https://meekotharaccoon-cell.github.io/meeko-nerve-center/link.html) | Everything in one place |

---

## Fork it. Aim it at anything.

This system is a **template for autonomous action**. Fork it and point it at:
- Climate crisis reporting
- Mutual aid network coordination
- Local community resource sharing
- Any humanitarian cause anywhere

```bash
git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center
```

Full instructions: [Fork Guide](https://github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/products/fork-guide.md)

---

## What’s in the system

```
mycelium/
  knowledge_harvester.py    — daily open-source intelligence
  loop_brain.py             — strategy engine (Ollama + rule-based)
  signal_tracker.py         — what’s actually working
  humanitarian_content.py   — weighted content generation
  self_healer.py            — error diagnosis + auto-fix
  email_drafter.py          — drafts outreach, you hit send
  evolve.py                 — self-improvement engine
  grant_outreach.py         — finds + applies to relevant grants
  ... 30+ more scripts

.github/workflows/
  knowledge-harvester.yml
  feedback-loop.yml
  self-healer.yml
  humanitarian-content.yml
  wiring-status-generator.yml
  fork-tracker.yml
  diagnostics.yml

knowledge/                  — grows daily, machine-readable
content/                    — generated posts + archive
data/                       — signals, strategy, heal reports
products/                   — fork guide + digital products
```

---

## Results so far

See [RESULTS.md](RESULTS.md) — auto-updated daily.

---

## Stack

- **GitHub Actions** — all automation
- **GitHub Pages** — all hosting
- **Ollama** (local) — private AI reasoning, no API costs
- **Python** — all scripts, zero frameworks
- **Free public APIs** — GitHub, Wikipedia, arXiv, HackerNews, NASA
- **Total cost: $0/month**

---

## License

[AGPL-3.0](LICENSE) — Free forever. If you build on this, your version must also be open source.

---

*Built in public. Every commit visible. Every decision logged.*  
*The system that built this README also fixed its own errors this morning.*
