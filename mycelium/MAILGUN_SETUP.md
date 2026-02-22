# Mailgun Setup — Free Tier (100 emails/day, open tracking)

5 minutes. Zero cost. Unlocks:
- Open tracking (know when emails are read)
- Click tracking (know which links get clicked)
- Dedicated sending domain (better inbox delivery)
- Event logs (full history of every send)

---

## Step 1: Create Mailgun Account

1. Go to mailgun.com → Sign Up
2. Free tier: 100 emails/day, 3-month trial, no credit card required initially
3. Verify your email

## Step 2: Get Your API Key

1. Dashboard → API Keys → Private API Key
2. Copy it
3. Add to GitHub Secrets: `MAILGUN_API_KEY`

## Step 3: Choose a Sending Domain

**Option A: Mailgun Sandbox (easiest, instant)**
- Mailgun gives you a sandbox domain automatically: `sandbox[hash].mailgun.org`
- Limitation: can only send to verified recipient addresses
- Good for: testing, sending to yourself
- Add to GitHub Secrets: `MAILGUN_DOMAIN` = `sandbox[yourhash].mailgun.org`

**Option B: Your Own Domain (best, ~$12/year)**
- Buy a domain: porkbun.com (cheapest), namecheap.com, or cloudflare.com
- Example: `solarpunkmycelium.org` = $8.06/year at Porkbun
- In Mailgun: Sending → Domains → Add New Domain
- Mailgun gives you 4 DNS records to add
- Add them at your registrar (takes 5 minutes, propagates in ~30 min)
- Result: emails come from `hello@solarpunkmycelium.org`
- This is what makes grant applications look professional

## Step 4: Update GitHub Secrets

```
MAILGUN_API_KEY   = your private API key
MAILGUN_DOMAIN    = sandbox[hash].mailgun.org  OR  yourdomain.org
```

## Step 5: Test

Run the workflow manually:
```
Actions → Any email workflow → Run workflow → dry_run: false
```

mailer_pro.py auto-detects Mailgun credentials and switches from Gmail.

---

## What Open Tracking Tells You

When a foundation program officer opens your grant application email:
- `data/email_opens.json` logs it
- signal_tracker.py picks it up Monday morning
- `data/what_works.json` shows which grant targets engaged
- Cross-referenced with sales data: did engagement lead to anything?

For the first time, the system knows the difference between:
- Email delivered, never opened (wrong target or bad subject line)
- Email opened once (read, not interested)
- Email opened multiple times (interested, forwarding to colleagues)
- Email opened + link clicked (took action)

That's the signal that makes everything smarter.

---

## When You're Ready: Upgrade to Postmark

- postmarkhq.com → $15/month
- Add: `POSTMARK_SERVER_TOKEN` secret
- mailer_pro.py auto-detects and switches
- Dedicated IP = best inbox delivery for cold grant outreach
- The one paid thing in the system that has no equivalent free alternative
