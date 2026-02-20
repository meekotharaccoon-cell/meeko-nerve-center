---
title: I built a self-running humanitarian art gallery on GitHub. Zero monthly cost. 70% to Gaza.
published: true
tags: opensource, github, ai, showdev
canonical_url: https://meekotharaccoon-cell.github.io/gaza-rose-gallery
description: How one person used GitHub Actions, free APIs, and AI to build an autonomous gallery that funds pediatric care in Gaza — and why every piece of the architecture is forkable for any cause.
---

# I built a self-running humanitarian art gallery on GitHub. Zero monthly cost. 70% to Gaza.

I'm Meeko. I'm a self-taught digital artist and developer, and six weeks ago I started building something I couldn't find anywhere else: a gallery that runs itself, funds verified humanitarian work, and costs nothing to operate.

This is how it works, why I built it, and how you can fork the whole thing for your own cause.

## The Problem I Was Trying to Solve

I make digital art. I wanted the art to do something real — not symbolic, not awareness-raising, not a campaign. Real economic transfer to people in crisis.

The obstacle: every platform I looked at takes too much. Gumroad charges 10% + $0.50 on a $1 sale. PayPal takes 49 cents. By the time money passes through two middlemen, a $1 donation becomes 12 cents reaching the people it was meant for.

So I built around the middlemen.

## What Gaza Rose Gallery Actually Is

**56 original 300 DPI digital flower artworks.** Each $1. 70% committed to the [Palestine Children's Relief Fund](https://www.pcrf.net) — a verified 501(c)(3) with a 4-star Charity Navigator rating for 12 consecutive years.

But the gallery isn't really about the art. It's about the architecture.

## The Meeko Mycelium — How It Runs Itself

I call the system the Meeko Mycelium because it's designed like a living organism:

**🧠 Brain** — A private GitHub repo that stores system state, connection status, sent emails, and context. Every session, every action, logged and remembered. An AI can read it and know exactly where things stand.

**❤️ Heartbeat** — GitHub Actions schedules that run at 9 AM and 9 PM EST every day. Morning: promote, generate content, check health. Evening: review, prepare tomorrow, sync memory.

**👁️ Eyes** — SerpAPI web searches that monitor mentions, check gallery health, watch for new opportunities.

**🗣️ Voice** — AI-generated posts to Dev.to, Discord, Mastodon. Every post unique. Never spam.

**🤲 Hands** — PayPal, Bitcoin, and Lightning Network (Strike) for payments. Coinbase Commerce for crypto. Zero-fee Lightning checkout built on Cloudflare Workers.

**📬 Email** — An IMAP watcher that reads every incoming reply and uses OpenRouter (GPT-4o-mini) to draft warm, specific, non-templated responses. Sends them automatically. Logs every message ID so it never double-replies.

**Total monthly cost: $0.** GitHub Actions free tier. GitHub Pages free hosting. Free API tiers for everything.

## The Payment Stack

Here's the actual fee math on a $1 sale:

| Method | Fee | You Keep |
|--------|-----|----------|
| Gumroad | $0.60 | $0.40 |
| PayPal | $0.49 | $0.51 |
| Stripe | $0.33 | $0.67 |
| Coinbase Commerce | $0.01 | $0.99 |
| Lightning (Strike) | ~$0.00 | $1.00 |

The gallery offers all of them. The buyer chooses. Lightning is the default recommendation.

## The Grant Pipeline

Because the system is open source and forkable, it qualifies for a different kind of funding than art alone. I've sent formal grant inquiries to:

- Mozilla Foundation (open internet / open source)
- Knight Foundation (Prototype Fund)
- Wikimedia Foundation (Rapid Fund)
- Creative Capital (digital art)
- Eyebeam (new media fellowship)
- Rhizome (net art microgrant)

And applied for fiscal sponsorship through Open Collective so any grant payments have a proper legal home.

## The Part That Surprised Me

I thought the hard part would be the code. It wasn't.

The hard part was believing that one person with free tools and a clear mission could build something that outlasts any single act of generosity. Something that runs at 2 AM when you're asleep. Something that answers emails from PCRF and Mozilla and GitHub Sponsors without you having to be there.

The code is maybe 800 lines total. The architecture took one weekend to design. The art took months.

But the thing that makes it real is the decision to point it at something real.

## Fork It

Every piece is open source:

- **Nerve center** (workflows, AI scripts, email system): https://github.com/meekotharaccoon-cell/meeko-nerve-center
- **Gallery**: https://github.com/meekotharaccoon-cell/gaza-rose-gallery  
- **Live gallery**: https://meekotharaccoon-cell.github.io/gaza-rose-gallery

If you're running a humanitarian project and want this architecture, fork it and replace my art with yours. Change PCRF to your cause. The system doesn't care. It just runs.

If you want to buy a piece and send 70 cents to Gaza: the gallery is live and every download is immediate.

---

*Meeko is a self-taught digital artist and developer. Gaza Rose Gallery is not a company. It's one person's attempt to make technology do something useful.*
