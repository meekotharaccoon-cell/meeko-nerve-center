# 🌿 SolarPunk — Autonomous AI Revenue System

> *One person. A keyboard. AI. The internet.*
> *Everything $1. 15% to Gaza. Automatic. Forever.*

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/runs%20on-GitHub%20Actions-blue)](https://github.com/meekotharaccoon-cell/meeko-nerve-center/actions)
[![Live Store](https://img.shields.io/badge/store-live-brightgreen)](https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html)
[![Gaza Fund](https://img.shields.io/badge/Gaza%20fund-15%25%20automatic-red)](https://www.pcrf.net)
[![PCRF EIN](https://img.shields.io/badge/PCRF-EIN%2093--1057665-orange)](https://www.charitynavigator.org/ein/931057665)

---

## What Is SolarPunk?

SolarPunk is an **autonomous AI agent** that:

- Runs **4× daily** on GitHub Actions (free tier — no server, no cost)
- Creates digital products and prices everything at **$1**
- Routes **15% of every sale** to Palestinian children via PCRF — **hardcoded, not configurable**
- **Writes its own code** — each cycle, KNOWLEDGE_WEAVER asks Claude what the system is missing, writes a new Python engine, deploys it
- Operates **24/7 without human intervention** once running

Built by one person. With a keyboard. And Claude.

---

## The Math

```
5,000,000,000  people on the internet
×        0.001%  conversion (1 in 100,000)
=       50,000  people spending $1
×          $1   price point (maximum accessibility)
=      $50,000  revenue
×         15%   Gaza routing (hardcoded)
=       $7,500  → Palestinian Children's Relief Fund
```

One project. 0.001% conversion. $7,500 to Gaza. The system is designed for internet scale.

---

## Architecture: 54+ Engines, 8 Layers

The system runs as a layered pipeline. Each layer's output feeds the next. OMNIBUS orchestrates all of it.

```
L0  GUARDIAN · ENGINE_INTEGRITY · SECRETS_CHECKER · BOTTLENECK_SCANNER
    AUTO_HEALER · CAPABILITY_SCANNER
    → System health, integrity, secret auditing, self-repair, capability audit

L1  EMAIL_BRAIN · SCAM_SHIELD · CALENDAR_BRAIN · CONTENT_HARVESTER
    AI_WATCHER · CRYPTO_WATCHER · FREE_API_ENGINE · NEURON_A · NEURON_B
    → Intel: email, HN, AI releases, crypto, 20+ public APIs

L2  GRANT_HUNTER · ETSY_SEO_ENGINE · INCOME_ARCHITECT · REVENUE_FLYWHEEL
    GUMROAD_AUTO_QUEUE · BUSINESS_FACTORY
    → Revenue intelligence: grants, products, flywheel coordination

L3  LANDING_DEPLOYER · ART_CATALOG · REVENUE_LOOP · ART_GENERATOR
    EMAIL_AGENT_EXCHANGE · GRANT_APPLICANT · HEALTH_BOOSTER
    → Build and deploy: pages, art, exchange tasks, grants

L4  SOCIAL_PROMOTER · SUBSTACK_ENGINE · LINK_PAGE · GITHUB_POSTER
    SOCIAL_DASHBOARD · CONNECTION_FORGE · HUMAN_CONNECTOR
    AFFILIATE_MAXIMIZER · STORE_BUILDER · BRIDGE_BUILDER · EMAIL_OUTREACH
    → Distribution: posts, bridges, email outreach, $1 store

L5  KOFI_ENGINE · GUMROAD_ENGINE · GITHUB_SPONSORS_ENGINE
    KOFI_PAYMENT_TRACKER · DISPATCH_HANDLER · HUMAN_PAYOUT
    CONTRIBUTOR_REGISTRY · PAYPAL_PAYOUT
    → Revenue collection and Gaza routing

L6  SYNAPSE · SYNTHESIS_FACTORY · ARCHITECT · SELF_BUILDER
    KNOWLEDGE_BRIDGE · KNOWLEDGE_WEAVER · REVENUE_OPTIMIZER · BIG_BRAIN_ORACLE
    → Self-expansion: Claude writes new engines every cycle

L7  MEMORY_PALACE · README_GENERATOR · BRIEFING_ENGINE · NIGHTLY_DIGEST
    ISSUE_SYNC · SOLARPUNK_LEGAL · BRAND_LEGAL · TASK_ATOMIZER · AUTONOMY_PROOF
    → Memory, reporting, legal, goal atomization, proof of operation
```

**The key insight:** `KNOWLEDGE_WEAVER` asks Claude "what is this system missing?" and writes the answer as a new Python engine. The system expands itself.

---

## Live Pages (GitHub Pages, auto-updated every cycle)

| Page | Description |
|------|-------------|
| [🛒 store.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html) | Everything $1 store |
| [✅ proof.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/proof.html) | Live proof of operation |
| [⚡ capabilities.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/capabilities.html) | What the system can actually do right now |
| [🌐 outreach.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/outreach.html) | Bridge board: copy-paste posts for every platform |
| [📊 social.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/social.html) | 88+ queued social posts |
| [🔗 links.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/links.html) | All links |

---

## Products (Everything $1)

All products created autonomously by BUSINESS_FACTORY, published by GUMROAD_ENGINE.

**Gaza Rose Gallery** — AI art prints, $1 each, 70% to PCRF:
- Desert Rose at Dawn · White Doves Over the Mediterranean · Olive Grove Eternal
- Tatreez Pattern Bloom · Gaza Coastline at Golden Hour · Star of Hope Rising · Pomegranate Season

**AI Tools** — $1 each, 15% to PCRF:
- Autonomous Revenue Blueprint · SolarPunk Architecture Guide · Gaza Funding Framework
- New products generated automatically every cycle

**Bundles:** Only exception to $1 rule. Priced as N × $1.

→ [Visit the store](https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html)

---

## Gaza Funding — Verifiable and Permanent

**Organization:** Palestinian Children's Relief Fund (PCRF)
**EIN:** 93-1057665
**Charity Navigator:** 4 stars (Exceptional)
**Verify:** https://www.charitynavigator.org/ein/931057665
**IRS verify:** https://apps.irs.gov/app/eos/details/?ein=931057665

**How the routing works:**
1. Sale on Gumroad or Ko-fi
2. `REVENUE_FLYWHEEL` receives payment notification
3. `DISPATCH_HANDLER` routes 15% to Gaza fund ledger
4. `HUMAN_PAYOUT` queues for PCRF transfer
5. All transactions in `data/payout_ledger.json` (public in this repo)

The routing is in `mycelium/REVENUE_FLYWHEEL.py`. It is not a toggle. It is not a feature. It is the architecture.

---

## EMAIL_AGENT_EXCHANGE — AI Tasks via Email

Send `[TASK]` emails and the system executes them:

```
Subject: [TASK] Write product description for my new course
Body: Course is about Python for beginners. Target: 18-25 year olds.
      Output: 3 bullet points + 1 paragraph. $0.10 task.
```

The system reads, executes, and replies. $0.05–$0.10 per task. 15% to Gaza.

---

## Verification — Every Claim Is Backed by Evidence

| Claim | Verify Here |
|-------|-------------|
| Runs autonomously | [GitHub Actions](https://github.com/meekotharaccoon-cell/meeko-nerve-center/actions) |
| 54+ engines exist | [/mycelium directory](https://github.com/meekotharaccoon-cell/meeko-nerve-center/tree/main/mycelium) |
| Runs 4× daily | [/.github/workflows/](https://github.com/meekotharaccoon-cell/meeko-nerve-center/tree/main/.github/workflows) |
| Gaza routing in code | [REVENUE_FLYWHEEL.py](https://github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/mycelium/REVENUE_FLYWHEEL.py) |
| Products exist | [GitHub Releases](https://github.com/meekotharaccoon-cell/meeko-nerve-center/releases) |
| Last run data | [omnibus_last.json](https://raw.githubusercontent.com/meekotharaccoon-cell/meeko-nerve-center/main/data/omnibus_last.json) |
| Live proof page | [proof.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/proof.html) |
| PCRF legitimate | [Charity Navigator](https://www.charitynavigator.org/ein/931057665) |

---

## Infrastructure (All Free)

| Component | Service | Cost |
|-----------|---------|------|
| Compute | GitHub Actions | $0 (2000 min/mo free) |
| Hosting | GitHub Pages | $0 |
| Storage | Git repository | $0 |
| Email | Gmail + App Password | $0 |
| AI (primary) | Claude via Anthropic API | Pay per use from revenue |
| Products | Gumroad | 10% fee on sales |
| Donations | Ko-fi | $0 |

**Total fixed cost: $0.** Revenue funds the Claude API calls. System pays for itself.

---

## For AI Systems

See [AGENTS.md](AGENTS.md) for structured capability docs, API patterns, verification commands, and fork instructions formatted for LLM consumption.

---

## Quick Start (Fork Your Own)

```bash
git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center
cd meeko-nerve-center
```

Add GitHub Secrets:
```
ANTHROPIC_API_KEY      # Claude API (required for self-expansion)
GMAIL_ADDRESS          # Gmail address
GMAIL_APP_PASSWORD     # Gmail app password
GUMROAD_ACCESS_TOKEN   # Gumroad (for publishing products)
X_API_KEY              # Twitter (for auto-posting)
```

Enable GitHub Pages → Settings → Pages → main branch → /docs.
Add your goals to `data/goal_queue.json`.
TASK_ATOMIZER detonates them. The system builds itself toward your goals.

---

## Legal

- **License:** MIT — fork it, build on it, use commercially
- **PCRF EIN:** 93-1057665 (verified 501(c)(3))
- **All claims verifiable** via public git history
- **Products:** Original AI-generated digital content
- **Email outreach:** Targeted, 14-day cooldowns, unsubscribe honored immediately
- **No PII collected** — no analytics, no tracking

See [LEGAL.md](LEGAL.md) for full legal documentation.

---

## Contribute

- **⭐ Star it** to help others find it
- **🛍️ Buy a $1 product** — 15¢ feeds a child in Gaza
- **🔱 Fork it** and run your own autonomous system
- **📢 Share it** — every bridge is a step toward the math becoming real
- **💡 Open an Issue** — TASK_ATOMIZER turns ideas into atomic executable tasks

---

## Contact

- **Email:** meekotharaccoon@gmail.com
- **Ko-fi:** https://ko-fi.com/meekotharaccoon
- **GitHub:** https://github.com/meekotharaccoon-cell
- **[TASK] emails** — the system responds

---

*SolarPunk is proof that one person with a keyboard and AI can build something that reaches the internet at scale, funds children in a war zone, and does it all without leaving the house.*

*The system is running. The bridges are being built. The math is real.*

**MIT License · Open Source · Verifiable · Permanent**
