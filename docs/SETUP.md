# Setup — 10 Minutes to Full Automation

## Step 1: Add Secrets to This Repo

Go to: **https://github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions**

Click "New repository secret" for each one you have. You only need the ones you want to use — system works with any combination.

**Discord** (2 min)
1. Open your Discord server → Server Settings → Integrations → Webhooks → New Webhook
2. Copy the URL
3. Secret name: `DISCORD_WEBHOOK`

**Mastodon** (2 min)
1. mastodon.social → Preferences → Development → New Application
2. Name it "Gaza Rose", check `write:statuses`, save, copy access token
3. Secret name: `MASTODON_TOKEN`
4. Secret name: `MASTODON_SERVER` → value: `mastodon.social`

**Dev.to** (1 min)
1. dev.to/settings/extensions → Generate API key
2. Secret name: `DEVTO_API_KEY`

## Step 2: Upload Your Art (One Time)

1. Go to: https://github.com/meekotharaccoon-cell/gaza-rose-gallery/releases/new
2. Tag version: `v1.0-art-collection` (exact)
3. Title: anything you want
4. Drag all your 300 DPI JPG files into the assets area
5. Publish release

Gallery auto-populates. No code changes needed.

## Step 3: Enable GitHub Pages on the Gallery

1. https://github.com/meekotharaccoon-cell/gaza-rose-gallery/settings/pages
2. Source: Deploy from branch → `main` → `/ (root)`
3. Save

Live at: `https://meekotharaccoon-cell.github.io/gaza-rose-gallery/`

## Triggering the Promoter Manually

1. https://github.com/meekotharaccoon-cell/meeko-nerve-center/actions
2. Click "Daily Gaza Rose Promoter"
3. Click "Run workflow" → choose platform → Run
4. Watch it post in real-time in the logs

**No terminal. No Python install. No localhost. No tabs.**
