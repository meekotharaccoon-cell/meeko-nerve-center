# 🛑 WHAT YOU NEED TO DO — Right Now

These are the only things that require **you** (human) to do manually.
Everything else runs itself.

---

## 🔴 BLOCKER #1 — ANTHROPIC_API_KEY (do this TODAY)

**Why:** Every AI-powered engine (SELF_BUILDER, KNOWLEDGE_WEAVER, NEURON_A, NEURON_B, CLAUDE_ENGINE) is silently skipping. Health score is stuck at 40/100 because of this one missing key.

**How:**
1. Go to → https://console.anthropic.com/
2. Buy API credits (start with $20 — runs ~100-200 full cycles)
3. Create an API key
4. Go to → https://github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions
5. Click "New repository secret"
6. Name: `ANTHROPIC_API_KEY`
7. Paste your key
8. Save

**Result:** Health score jumps from 40 → 80+. System starts writing its own engines. Everything AI-powered activates.

---

## 🔴 BLOCKER #2 — GitHub Pages Source (do this TODAY)

**Why:** All your live pages are 404ing because GitHub Pages doesn't know to serve from the `docs/` folder. The HTML exists — Pages just doesn't know where to look.

**How:**
1. Go to → https://github.com/meekotharaccoon-cell/meeko-nerve-center/settings/pages
2. Under "Source" → select **"Deploy from a branch"** OR **"GitHub Actions"**
3. If "Deploy from a branch": set Branch = `main`, Folder = `/docs`
4. If the new PAGES_DEPLOY.yml workflow is running: select "GitHub Actions"
5. Save

**Result:** All pages at `meekotharaccoon-cell.github.io/meeko-nerve-center/` go live instantly. Zero 404s.

**Verify it's working:**
- https://meekotharaccoon-cell.github.io/meeko-nerve-center/
- https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html
- https://meekotharaccoon-cell.github.io/meeko-nerve-center/proof.html

---

## 🟡 OPTIONAL BUT FAST — Gumroad Products (30 min)

All copy-paste content is in: `data/gumroad_listings.txt`

Steps:
1. Open `data/gumroad_listings.txt` in GitHub (raw view) or download it
2. Go to gumroad.com → Log in
3. Create each of the 5 products using the exact text in that file
4. For cover images: use the image prompts with Adobe Firefly (free at firefly.adobe.com)

That's it. Products go live immediately.

---

## 🟡 OPTIONAL — Tweet Queue (10 min)

Ready-to-post threads are in: `data/tweets_queue.txt`

Steps:
1. Open `data/tweets_queue.txt`
2. Copy a thread (4 tweets)
3. Post tweet 1 on X/Twitter
4. Reply to it with tweet 2, 3, 4

New threads are auto-generated every OMNIBUS cycle (once ANTHROPIC_API_KEY is set).

---

## ✅ WHAT'S ALREADY WORKING (no action needed)

- ✅ GUARDIAN health checks (6x/day)
- ✅ EMAIL_BRAIN reading Gmail
- ✅ CONTENT_HARVESTER watching Hacker News
- ✅ REVENUE_FLYWHEEL routing (15% Gaza hardcoded)
- ✅ FIRST_CONTACT watching for first stranger
- ✅ All 76 engine framework running (AI engines skip gracefully)
- ✅ docs/404.html live (catches broken links)
- ✅ NANO_AGENT base class (all new agents built on this)
- ✅ AGENT_TWEET_WRITER (generates drafts every cycle)
- ✅ AGENT_GUMROAD_BUILDER (rebuilds store.html every cycle)
- ✅ AGENT_LINK_VERIFIER (checks pages, stubs empty dirs)
- ✅ PAGES_DEPLOY.yml workflow (auto-deploys docs/ on every push)

---

## 📋 ONE-TIME SETUP CHECKLIST

- [ ] Add `ANTHROPIC_API_KEY` to GitHub Secrets
- [ ] Set GitHub Pages source to `/docs` or "GitHub Actions"
- [ ] Create 5 Gumroad products from `data/gumroad_listings.txt`
- [ ] Post first tweet thread from `data/tweets_queue.txt`

After those 4 things: SolarPunk runs itself.

---

*This file is auto-updated by AGENT_STATUS_REPORTER every cycle.*
*Last manual update: 2026-03-11*
