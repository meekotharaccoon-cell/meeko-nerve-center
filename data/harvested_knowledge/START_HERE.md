# START HERE — Fork This System in One Afternoon

You found this. That means you can run it.
This document takes you from zero to running system in one sitting.

---

## What You're Getting

A fully autonomous system that:
- Posts content to Mastodon, Bluesky, Discord, Dev.to daily
- Sends grant applications and outreach emails automatically
- Sells your art/products with inline payments
- Responds to emails on your behalf
- Generates PDFs from your guides automatically
- Updates its own documentation with real stats
- Archives itself permanently
- Tracks its own revenue
- Runs on GitHub's free tier ($0/month)

---

## What You Need to Start

- A GitHub account (free)
- A Gmail account (free) — you'll create a dedicated one for this
- A Gumroad account (free) — to sell things
- 1-2 hours

That's it. No server. No credit card. No technical background required beyond being comfortable reading instructions.

---

## Step 1: Fork the Repo (2 minutes)

1. Go to: https://github.com/meekotharaccoon-cell/meeko-nerve-center
2. Click the **Fork** button (top right)
3. Name it whatever you want
4. Click **Create Fork**

Your version is now live. The workflows exist. Nothing is running yet because the secrets are empty.

---

## Step 2: Create Your System Email (10 minutes)

This is the email the system sends from. Not your personal email.

1. Go to accounts.google.com/signup
2. Create: `[yourname].mycelium@gmail.com` (or whatever you want)
3. Enable 2-Factor Authentication
4. Go to Gmail Settings → Security → **App Passwords**
5. Create an App Password for "Mail"
6. Copy the 16-character password — you'll use it in the next step

---

## Step 3: Add Secrets (15 minutes)

Go to your forked repo: **Settings → Secrets and variables → Actions → New repository secret**

Start with these — they unlock the most:

| Secret Name | What It Is | Where to Get It |
|-------------|------------|----------------|
| `GMAIL_APP_PASSWORD` | Your App Password from Step 2 | Gmail Settings |
| `GMAIL_USER` | Your system email address | You just created it |
| `GITHUB_TOKEN` | Auto-provided by GitHub | Already exists |

**Adding this one secret (`GMAIL_APP_PASSWORD`) activates:**
- Daily morning briefing email to yourself
- Automated grant outreach emails
- Automated tech/hello outreach
- Email response system
- All email workflows simultaneously

---

## Step 4: Set Your Cause (5 minutes)

Open `mycelium/unified_emailer.py` in GitHub's web editor.

Change these lines near the top:
```python
GMAIL_USER = 'your.system.email@gmail.com'  # your system email
GALLERY    = 'https://your-gallery-url'      # your gallery/shop URL
GITHUB     = 'https://github.com/yourusername'
```

Open `mycelium/cross_poster.py` and update the gallery/Gumroad links.

That's your customization. Everything else runs as-is.

---

## Step 5: Enable GitHub Pages (3 minutes)

1. Repo Settings → Pages
2. Source: **Deploy from branch**
3. Branch: **main**
4. Folder: **/ (root)**
5. Save

Your spawn.html is now live at:
`https://[yourusername].github.io/meeko-nerve-center`

---

## Step 6: Trigger Your First Workflow (1 minute)

Go to your repo → **Actions** → Find any workflow → Click **Run workflow**

Start with `🌅 Mycelium Morning Pulse`.
Watch it run. If it succeeds: you're live.

---

## What to Add Next (When You Feel Like It)

Each of these adds a new capability. None are required to start.

| Secret | Capability Unlocked |
|--------|--------------------|
| `MASTODON_TOKEN` + `MASTODON_SERVER` | Auto-posts to Mastodon |
| `BLUESKY_HANDLE` + `BLUESKY_APP_PASSWORD` | Auto-posts to Bluesky |
| `DISCORD_WEBHOOK` | Posts to your Discord server |
| `DEVTO_API_KEY` | Publishes articles to Dev.to |
| `GUMROAD_TOKEN` | Tracks your Gumroad sales |
| `YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN` | Manages YouTube descriptions |
| `OPENROUTER_KEY` | Adds AI-generated content (free tier available) |

---

## Point It at Your Cause

The system is built around Gaza Rose Gallery and PCRF.
But it's yours to point anywhere.

Change the gallery URL, the charity, the percentage — and the system works for your cause.
Want 100% to yourself? Change the split. It's a config value.
Want to support a local food bank? Change the charity link. Same system.

---

## The License

AGPL-3.0 + Ethical Use Rider.

**You can:** Fork, run, modify, redistribute, sell things with it.
**You can't:** Use it for surveillance, weapons, exploiting workers, hate.
**You must:** Keep it open source if you distribute it. Your fork inherits the same freedom.

The values propagate with the code.

---

## Questions / Stuck?

Open a GitHub Issue on this repo. Or read the docs in `/docs/`. Or fork and figure it out — that's how this was built.

**One desktop. One keyboard. One afternoon. Your system.**
