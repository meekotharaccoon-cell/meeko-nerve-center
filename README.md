# 🍄 SolarPunk Mycelium

> **One person. One desktop. $0/month. A fully autonomous AI system running right now.**

This isn't a demo. This isn't a template waiting to be filled in.  
This is a live organism — 10 workflows running daily, selling art, sending emails, posting to social media, raising money for humanitarian causes, archiving itself — **without anyone touching it.**

And you can fork it and run your own in one afternoon.

---

## What It Does Right Now

| What | How | Cost |
|------|-----|------|
| Posts to Mastodon, Bluesky, Discord, Dev.to | `cross_poster.py` — daily, rotating content | $0 |
| Sends grant applications and outreach | `unified_emailer.py` — brain-gated, deduped | $0 |
| Sells digital art with inline payments | Gaza Rose Gallery — Gumroad + PayPal | $0 |
| Responds to emails automatically | `email_responder.py` | $0 |
| Updates all YouTube video descriptions | `youtube_manager.py` — daily | $0 |
| Generates and publishes PDFs | GitHub Actions + pandoc | $0 |
| Archives everything permanently | Internet Archive + IPFS | $0 |
| Tracks its own revenue | `monetization_tracker.py` | $0 |
| Updates its own documentation | `living_readme.py` — real stats, always current | $0 |
| Applies for grants autonomously | `unified_emailer.py` — grant mode | $0 |

**Monthly infrastructure cost: $0.**  
Everything runs on GitHub's free tier. 2,000 compute minutes/month. Unlimited public repos.

---

## The Hardware

```
CPU  Intel Core i5-8500 · 6 cores · 3.0GHz
RAM  32GB DDR4
GPU  Intel UHD 630 — integrated graphics. No GPU. This matters.
$    Zero per month
```

If this runs on integrated graphics with $0 in recurring cost,  
it runs on whatever you have.

---

## The Mission

**[Gaza Rose Gallery](https://meekotharaccoon-cell.github.io/gaza-rose-gallery)** — 56 original 300 DPI digital flower artworks. $1 each.  
70% of every sale → Palestine Children's Relief Fund (PCRF) — 4-star Charity Navigator, EIN 93-1057665.  
The system sells them, processes payment, allocates the split, and logs everything. Automatically.

---

## Fork This. Run Your Own.

**[→ START HERE](START_HERE.md)** — takes you from zero to running system in one afternoon.

The short version:
1. Fork this repo (1 click)
2. Create a dedicated Gmail + get App Password (10 min)
3. Add it as a GitHub Secret (2 min)
4. That one secret activates all 10 email workflows simultaneously

Point it at your cause. Your art. Your mission. Same system.

**[→ See the live landing page](https://meekotharaccoon-cell.github.io/meeko-nerve-center/spawn.html)**  
**[→ Read the fork registry](FORK_REGISTRY.md)** — add yourself when yours is running

---

## Architecture

```
                    SOLARPUNK MYCELIUM
                    
        ┌─────────────────────────────────┐
        │         meeko_brain.py          │  ← values gate on every action
        │    "would Meeko approve this?"  │
        └──────────────┬──────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   [Email System]  [Posting]    [Revenue]
   unified_emailer  cross_poster  monetization
   email_responder  youtube_mgr   gumroad/paypal
         │             │             │
         └─────────────┼─────────────┘
                       ▼
              [Memory: data/ directory]
              [committed back to repo]
              [archived to Internet Archive]
              [system knows its own state]
```

---

## All the Repos

| Repo | What |
|------|------|
| **meeko-nerve-center** | Brain, workflows, email, cross-posting — you're here |
| [gaza-rose-gallery](https://github.com/meekotharaccoon-cell/gaza-rose-gallery) | Live gallery — 56 flowers, inline payments, $1 each |
| [solarpunk-legal](https://github.com/meekotharaccoon-cell/solarpunk-legal) | TCPA generator, FOIA generator, debt dispute tools |
| [solarpunk-learn](https://github.com/meekotharaccoon-cell/solarpunk-learn) | Free knowledge library — rights, infrastructure, free money |
| [solarpunk-remedies](https://github.com/meekotharaccoon-cell/solarpunk-remedies) | Herbal medicine guides — 12 plants, 40+ preparations |
| [solarpunk-market](https://github.com/meekotharaccoon-cell/solarpunk-market) | 0% fee marketplace — sellers keep 97.1% |
| [solarpunk-mutual-aid](https://github.com/meekotharaccoon-cell/solarpunk-mutual-aid) | Needs board, offers board, no gatekeeping |
| [solarpunk-grants](https://github.com/meekotharaccoon-cell/solarpunk-grants) | Community-voted micro-grant system |
| [solarpunk-radio](https://github.com/meekotharaccoon-cell/solarpunk-radio) | Autonomous internet radio — daily playlist generation |
| [solarpunk-bank](https://github.com/meekotharaccoon-cell/solarpunk-bank) | Alternatives to predatory banking |

---

## License

**AGPL-3.0 + Ethical Use Rider**

You can: fork, run, modify, sell things with it.  
You can't: use it for surveillance, weapons, or exploiting people.  
You must: keep it open source if you distribute it.

The values travel with the code. Every fork inherits them.

---

## The Point

Most autonomous AI systems require:
- GPU clusters
- Cloud subscriptions  
- Technical teams
- Venture capital

This one requires a GitHub account and an afternoon.

If this can run on integrated graphics with $0/month while raising money for Palestinian children's aid, then the barrier to building ethical autonomous systems isn't technical. It never was.

**Fork it. Prove it again. Add your cause to the registry.**

---

*Runs itself. Updates itself. Spreads itself. Never stops.*
