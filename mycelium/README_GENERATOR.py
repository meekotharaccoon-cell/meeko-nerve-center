# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""README_GENERATOR — Rebuilds README.md every cycle with live stats
SolarPunk's public face. Auto-updates with real numbers. No manual editing ever.
"""
import os,json
from pathlib import Path
from datetime import datetime,timezone

DATA=Path("data"); DATA.mkdir(exist_ok=True)

def load_all():
    d={}
    for fn,k in [("kofi_state.json","kofi"),("grant_applicant_state.json","grants"),
                 ("email_brain_state.json","email"),("sponsors_state.json","sponsors"),
                 ("human_connector_state.json","humans"),("self_builder_state.json","builder"),
                 ("ai_watcher_state.json","ai"),("crypto_state.json","crypto"),
                 ("scam_shield_state.json","scam"),("brain_state.json","brain")]:
        fp=DATA/fn
        if fp.exists():
            try: d[k]=json.loads(fp.read_text())
            except: pass
    return d

def count_engines():
    myc=Path("mycelium")
    return len(list(myc.glob("*.py"))) if myc.exists() else 0

def run():
    d=load_all(); now=datetime.now(timezone.utc)
    engines=count_engines()
    kofi=d.get("kofi",{}); grants=d.get("grants",{}); email=d.get("email",{})
    sponsors=d.get("sponsors",{}); humans=d.get("humans",{}); builder=d.get("builder",{})
    brain=d.get("brain",{}); scam=d.get("scam",{})

    raised=kofi.get("total_received",0); to_gaza=kofi.get("total_to_gaza",0)
    loops=kofi.get("auto_loops",0); applied=grants.get("total_applied",0)
    humans_met=len(humans.get("humans_met",[])); forks=humans.get("forks_guided",0)
    new_engines=builder.get("total_built",0); health=brain.get("health_score",0)
    scams=scam.get("scams_caught",0); cycles=brain.get("cycles",0)

    readme=f"""# 🌿 SolarPunk — Autonomous Income for Palestinian Artists

> An AI system that builds itself, funds itself, and directs money to Gaza. No human required between cycles.

[![Brain Status](https://img.shields.io/badge/Brain-Active-brightgreen)](https://github.com/meekotharaccoon-cell/meeko-nerve-center/actions)
[![Engines](https://img.shields.io/badge/Engines-{engines}%20Running-blue)](mycelium/)
[![Gaza Fund](https://img.shields.io/badge/Gaza%20Fund-${to_gaza:.2f}-orange)](https://ko-fi.com/meekotharaccoon)
[![Health](https://img.shields.io/badge/Health-{health}%2F100-{'brightgreen' if health>80 else 'yellow'})](data/)

**Updated:** {now.strftime('%Y-%m-%d %H:%M UTC')} | **Cycles run:** {cycles} | **Engines active:** {engines}

---

## 💰 Live Revenue Stats

| Stream | Amount | Status |
|--------|--------|--------|
| Total raised | **${raised:.2f}** | Ko-fi + Gumroad |
| To Palestinian artists | **${to_gaza:.2f}** | 70¢ per sale |
| Auto-loops completed | **{loops}** | $1 reinvested each |
| Grants applied | **{applied}** | Email applications sent |
| Monthly sponsors | **${sponsors.get('total_monthly',0):.2f}** | GitHub Sponsors |

---

## 🧠 System Stats

| Metric | Value |
|--------|-------|
| Active engines | {engines} |
| Brain cycles | {cycles} |
| Emails handled | {email.get('emails_total',0)} |
| Humans met + replied | {humans_met} |
| Forks guided | {forks} |
| Scams caught | {scams} |
| New engines self-built | {new_engines} |
| Health score | {health}/100 |

---

## ⚡ How It Works

```
EMAIL IN → SCAM_SHIELD → EMAIL_BRAIN classifies
    ↓ Personal: flagged for Meeko only
    ↓ Grant: GRANT_HUNTER + GRANT_APPLICANT reply autonomously
    ↓ Human: HUMAN_CONNECTOR replies, offers to help them build
    ↓ Business: Claude drafts reply, sends

EVERY CYCLE (4x/day via GitHub Actions):
    ART_GENERATOR → generates Gaza Rose art
    KOFI_ENGINE → processes sales, splits 70/30
    CRYPTO_WATCHER → monitors BTC/ETH/AI tokens
    AI_WATCHER → scouts new models to integrate
    SELF_BUILDER → writes a new engine
    CONNECTION_FORGE → emails Meeko platform setup guides
    BRIEFING_ENGINE → morning email + evening report
```

---

## 🌹 Gaza Rose Gallery

**Buy a $1 AI art print:** [ko-fi.com/meekotharaccoon](https://ko-fi.com/meekotharaccoon)

12 designs. Every sale: 70¢ to Palestinian artists, 30¢ funds the next cycle.

---

## 🔧 Engines

| Engine | Purpose |
|--------|---------|
| GUARDIAN | Self-healing, save-states |
| EMAIL_BRAIN | Reads + classifies all Gmail |
| SCAM_SHIELD | Blocks phishing, quarantines threats |
| HUMAN_CONNECTOR | Replies to real humans, spreads SolarPunk |
| GRANT_HUNTER | Finds 20+ grant sources |
| GRANT_APPLICANT | Emails applications, follows up chains |
| KOFI_ENGINE | 70/30 payment splits |
| CRYPTO_WATCHER | Market intel, proposal-only trading |
| AI_WATCHER | Scouts new AI models for upgrades |
| SELF_BUILDER | Writes new engines every cycle |
| CONNECTION_FORGE | Emails Meeko platform setup guides |
| BRIEFING_ENGINE | Daily morning + evening emails |
| CALENDAR_BRAIN | Auto-schedules appointments |
| SOCIAL_PROMOTER | Posts to X/Twitter + Reddit |

---

## 🚀 Fork This

Want your own autonomous income system for your cause?

1. Fork this repo
2. Add Secrets: `ANTHROPIC_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`
3. Edit `mycelium/NEURON_A.py` → change the mission
4. GitHub Actions runs everything automatically

Cost: **$0/month**. Time: **30 minutes**.

---

*Built by [MeekoThaRaccoon](https://github.com/meekotharaccoon-cell) | SolarPunk v3 | 100% legal, ethical, open-source*
"""
    Path("README.md").write_text(readme)
    print(f"README rebuilt: {engines} engines, ${raised:.2f} raised, {cycles} cycles")
    return {"readme_updated":True,"ts":now.isoformat()}

if __name__=="__main__": run()
