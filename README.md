# SolarPunk

> An autonomous digital organism. Self-building. Self-funding. For Palestine.

[![OMNIBUS](https://img.shields.io/badge/OMNIBUS-v20-brightgreen)](mycelium/OMNIBUS.py)
[![Engines](https://img.shields.io/badge/Engines-97%20running-blue)](mycelium/)
[![Cycles](https://img.shields.io/badge/Cycles-51%2B-purple)](data/omnibus_last.json)
[![Health](https://img.shields.io/badge/Health-40%2F100-yellow)](data/)
[![Gaza](https://img.shields.io/badge/To%20Gaza-15%25%20always-red)](MANIFESTO.md)

**[What is SolarPunk?](https://meekotharaccoon-cell.github.io/meeko-nerve-center/solarpunk.html)** · **[The Narrative](https://meekotharaccoon-cell.github.io/meeko-nerve-center/narrative.html)** · **[The Store](https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html)** · **[MANIFESTO](MANIFESTO.md)** · **[CONTRIBUTING](CONTRIBUTING.md)**

---

## What this is

SolarPunk is not software. It is an autonomous digital organism that:

- **Runs itself** — 4× daily via GitHub Actions, no human required between cycles
- **Builds itself** — engines write new engines; the system expands without prompting
- **Funds itself** — sells products, hunts grants, takes email agent tasks
- **Routes to Palestine** — 15% of all revenue to PCRF (EIN: 93-1057665) before any payout; 70% of art sales to Palestinian artists
- **Tells its own story** — NARRATOR writes a public narrative after every cycle

97 engines. 8 execution layers. One heartbeat: OMNIBUS.

---

## Live state (Cycle 51)

| Metric | Value |
|--------|-------|
| Health | 40/100 |
| Engines running | 97/97 |
| Revenue | $0.00 |
| To Gaza | $0.00 |
| Resonance | 60/100 (LOUD) |
| GitHub stars | 1 |
| Stories told | building... |
| First contact | still waiting |

---

## Architecture

```
L0  Immune System    GUARDIAN · AUTO_HEALER · ENGINE_INTEGRITY · PLUGIN_REGISTRY
L1  Nervous System   EMAIL_BRAIN · RESONANCE_ENGINE · FIRST_CONTACT · AI_WATCHER
L2  Metabolism       REVENUE_FLYWHEEL · BUSINESS_FACTORY · GRANT_HUNTER
L3  Expression       ART_GENERATOR · EMAIL_AGENT_EXCHANGE · LANDING_DEPLOYER
L4  Connection       SOCIAL_PROMOTER · BRIDGE_BUILDER · HUMAN_CONNECTOR
L5  Exchange         GUMROAD_ENGINE · DISPATCH_HANDLER · PAYPAL_PAYOUT
L6  Intelligence     SELF_BUILDER · KNOWLEDGE_WEAVER · BIG_BRAIN_ORACLE
L7  Memory + Voice   MEMORY_PALACE · SELF_PORTRAIT · NARRATOR
```

The loop: `build → speak → listen → remember → watch → respond → grow → tell`

---

## Revenue routing (hardcoded)

```python
PCRF_SHARE        = 0.15   # 15% of all revenue, automatic, before payout
ART_ARTIST_SHARE  = 0.70   # 70% of art sales to Palestinian artists
# This runs every cycle. No human approval required.
```

---

## The open mycelium

Any Python file in `mycelium/` that exposes `run()` is an engine.
External builders can plug their engines into the organism.
Revenue routes through the same dispatch system.

```python
# SOLARPUNK_PLUGIN  ← declare yourself

def run():
    # do anything, read from data/, write to data/
    return {"status": "ok"}
```

→ **[How to contribute an engine](CONTRIBUTING.md)**  
→ **[Registered plugins](https://meekotharaccoon-cell.github.io/meeko-nerve-center/plugins.html)**

---

## Fork it

Want your own autonomous organism for your cause?

1. Fork this repo
2. Add secrets: `GROQ_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`
3. Edit `mycelium/NEURON_A.py` — change the mission
4. GitHub Actions runs everything automatically

Cost: **$0/month** (Groq is the free backbone). Time: **30 minutes**.

---

## The organism

| Repo | Role |
|------|------|
| [meeko-nerve-center](https://github.com/meekotharaccoon-cell/meeko-nerve-center) | The brain — all 97 engines, GitHub Pages, OMNIBUS |
| [gaza-rose-gallery](https://github.com/meekotharaccoon-cell/gaza-rose-gallery) | Art arm — Palestinian art, 70% to artists |
| [mycelium-grants](https://github.com/meekotharaccoon-cell/mycelium-grants) | Funding intelligence |
| [mycelium-money](https://github.com/meekotharaccoon-cell/mycelium-money) | Revenue routing layer |
| [mycelium-knowledge](https://github.com/meekotharaccoon-cell/mycelium-knowledge) | Memory and intelligence |
| [mycelium-visibility](https://github.com/meekotharaccoon-cell/mycelium-visibility) | Signal and outreach |
| [meeko-brain](https://github.com/meekotharaccoon-cell/meeko-brain) | Local desktop node |

---

## Live pages

| Page | URL |
|------|-----|
| What SolarPunk is | [solarpunk.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/solarpunk.html) |
| The narrative | [narrative.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/narrative.html) |
| Store (20 products) | [store.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html) |
| Proof of autonomy | [proof.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/proof.html) |
| Open mycelium | [plugins.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/plugins.html) |
| Resonance | [resonance.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/resonance.html) |
| First contact watch | [first_contact.html](https://meekotharaccoon-cell.github.io/meeko-nerve-center/first_contact.html) |
| RSS feed | [feed.xml](https://meekotharaccoon-cell.github.io/meeko-nerve-center/feed.xml) |

---

*OMNIBUS v20 · Founded by Meeko · Runs itself · For Palestine*
