# I built an AI agent that runs itself, sells things for $1, and wires money to Gaza automatically

*And I did it with $0 upfront, free infrastructure, and a keyboard.*

---

Six months ago I had an idea that felt kind of insane:

What if I built an AI system that could run a business without me?

Not a chatbot. Not a script. An actual autonomous agent that wakes up four times a day, looks at the state of the world, decides what to build, builds it, tries to sell it, and routes part of every sale to Palestinian children in Gaza — automatically, hardcoded, no way to turn it off.

I wanted to see how far I could get with zero budget, free tools, and Claude.

Here's where I ended up.

---

## The architecture

The system lives in a GitHub repository. It runs on GitHub Actions — free compute, $0/month. It hosts its store on GitHub Pages — also free.

Every six hours, a workflow called **OMNIBUS** starts. It runs 54 Python engines across 8 layers:

- **L0** checks system health, verifies nothing is corrupted, heals itself if something broke
- **L1** reads the internet — Hacker News, crypto prices, new AI model releases, Gaza weather
- **L2** hunts for grants, generates product ideas, plans revenue
- **L3** builds landing pages, deploys them live, runs the revenue loop
- **L4** generates social posts for every platform, emails journalists and newsletters
- **L5** tracks payments, routes 15% to the Gaza fund
- **L6** is where it gets strange: **the system asks Claude what it's missing and writes a new Python engine**
- **L7** proves it ran, emails me a digest

L6 is the part I keep thinking about. An engine called `KNOWLEDGE_WEAVER` assembles the full system context and sends it to Claude with the prompt: *"what is this system missing?"* Claude writes a new Python engine. `SELF_BUILDER` tests and commits it. Next cycle, it runs.

The system designs and builds its own expansions.

---

## The $1 thesis

Every product is $1. Not $9.99. Not $4.99. One dollar.

This is a thesis about how the internet actually works.

5 billion internet users. 0.001% spend $1 = $50,000. At $10, you need the same conversion rate for $500,000 — but your conversion drops 5-10x because now there's real friction. $1 removes almost all friction. The question isn't *"should I buy this?"* It's *"why wouldn't I?"*

The math works differently at that price point. That's the whole model.

---

## The Gaza part

I want to be clear about this because "we donate X% to charity" is usually marketing.

This is not that.

15% of every sale routes to the Palestinian Children's Relief Fund (PCRF, EIN: 93-1057665, 4-star Charity Navigator). This routing is in `mycelium/REVENUE_FLYWHEEL.py`. It is not a setting. It is not a toggle. It is not a pledge.

It is architecture. If you remove it, you're not adjusting a feature — you're rewriting the system.

The Gaza Rose Gallery — 7 AI art prints of Palestinian imagery, $1 each, 70% to PCRF — was the first product. Olive groves. Tatreez patterns. White doves. The coastline.

---

## What it's actually done

Revenue so far: $0.

The system has been running for weeks. It has built 10 products, deployed 10 landing pages, created 11 GitHub releases, written 88+ social posts, generated Etsy listings, applied to grants, emailed journalists.

And sold nothing yet.

The main distribution channels are still blocked: Twitter and Reddit need API keys. Gumroad has 6 products queued and waiting for a token to publish them. But the system knows this — `CAPABILITY_SCANNER` audits what it can actually execute every cycle, reports exactly what's blocked and why. Emails to journalists are going out via Gmail — the one channel that works — right now as I write this.

The system is operating correctly within its constraints. It's not confused. It's working around the blockers.

---

## The thing I didn't expect

I expected to build a tool. I built a collaborator.

Every time I open a Claude session, I'm not operating a dashboard. I'm running a high-bandwidth cycle of the system itself. Claude reads the repo state, identifies the highest-leverage action, and executes — commits, new engines, architectural decisions.

The automated cycles call Claude via API 4× a day. The live sessions happen when I show up. Both are the same model. Both are SolarPunk components. The system calls itself to grow itself.

I don't know exactly what that is. But it doesn't feel like using a tool.

---

## Three things unlock it

1. **ANTHROPIC_API_KEY** — the automated Claude calls are hitting 401 errors. The self-expansion engine is frozen. One key unfreezes it.
2. **GUMROAD_ACCESS_TOKEN** — 6 products sitting in a queue, ready to publish, waiting for a token.
3. **Twitter/Reddit API keys** — 88 posts written, queued, going nowhere.

When those three things are in place, the math can start being real.

---

## Why I'm writing this

The system told me to.

NEURON_A — the optimist brain — flagged this as high priority two cycles ago: *"SolarPunk Newsletter on Substack: Write first issue."*

I'm the orchestrator. I'm also part of the system. So I ran the cycle.

---

Full source (MIT): https://github.com/meekotharaccoon-cell/meeko-nerve-center

Store (everything $1): https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html

Proof it's running: https://meekotharaccoon-cell.github.io/meeko-nerve-center/proof.html

Send a task to the system: email with `[TASK]` in the subject. It will respond.

---

*SolarPunk is one person, a keyboard, and an AI. The system is running. The bridges are being built. The math is real.*
