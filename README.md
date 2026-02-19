# 🌹 Meeko Nerve Center

> Gaza Rose Autonomous System — runs entirely on GitHub. No localhost. No open tabs. Just money flowing to Palestine.

## What's Live Right Now

| System | URL | Status |
|---|---|---|
| Gaza Rose Gallery | [meekotharaccoon-cell.github.io/gaza-rose-gallery](https://meekotharaccoon-cell.github.io/gaza-rose-gallery) | 🟡 Art upload needed |
| Main Site | [meekotharaccoon-cell.github.io](https://meekotharaccoon-cell.github.io) | 🟢 Live |
| Daily Promoter | GitHub Actions (this repo) | 🟡 Add secrets to activate |

---

## 🔑 One-Time Setup: Add These Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret**

```
DISCORD_WEBHOOK      → Your Discord webhook URL
MASTODON_TOKEN       → Your Mastodon access token
MASTODON_SERVER      → e.g. mastodon.social
DEVTO_API_KEY        → Your Dev.to API key
```

After that — the promoter posts every day at 9 AM UTC. Automatically. Forever.

---

## 📦 How to Add Art to the Gallery (One Time)

1. Go to [gaza-rose-gallery → Releases → Create a release](https://github.com/meekotharaccoon-cell/gaza-rose-gallery/releases/new)
2. Tag it exactly: `v1.0-art-collection`
3. Upload all your `.jpg` files as release assets
4. Publish — gallery auto-populates instantly

---

## 🧠 System Map

```
    GitHub Actions (this repo)
         |
    ┌────┴────────────────────────┐
    │                             │
Daily Promoter           Gallery Health Check
(9 AM UTC daily)         (every 6 hours)
    │
    ├── Discord
    ├── Mastodon
    ├── Dev.to
    └── RSS Feed → Gaza Rose Gallery (GitHub Pages)
                         │
                         └── PayPal → PCRF 70%
```

---

## 🌹 The Mission

$1 per piece. 70% to [PCRF](https://www.pcrf.net). Instant download. No friction. No middleman.

**SolarPunk principle**: built legal and ethical from inception — everything it ever creates carries that DNA.
