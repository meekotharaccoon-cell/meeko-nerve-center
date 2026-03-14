# TODO — Updated 2026-02-20

## 4 THINGS ONLY MEEKO DOES (in order of impact)

### 1. Get Gmail App Password (10 minutes — unlocks ALL email automation)
This single step makes the mycelium read and reply to all your emails automatically.
- Go to: myaccount.google.com/security
- Click: 2-Step Verification (enable if not on)
- Scroll down: App Passwords
- App: Mail, Device: Other → name it "Mycelium"
- Copy the 16-character password shown (shown ONCE)
- Go to: github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions
- Add secret: GMAIL_APP_PASSWORD = [that 16-char password]
- DONE. Mycelium now reads and replies to every email. AI-generated, never repeated.

### 2. Get Strike API Key (5 minutes — unlocks zero-fee Lightning payments)
- Go to: dashboard.strike.me (you're already signed in)
- Left sidebar: look for "API" or "Developer" section
- Click "API Key" → Create API Key
- Scopes to select: invoices.read, invoices.write, payment-of-invoices.read
- Name it: "Gaza Rose Gallery"
- Copy the key (shown ONCE — save it!)
- Add to nerve-center secrets as: STRIKE_API_KEY
- Tell Claude your Strike username and worker URL once deployed

### 3. Deploy Lightning Worker to Cloudflare (15 minutes — connects Strike to gallery)
- Go to: workers.cloudflare.com → free account
- Create Worker → paste code from nerve-center/mycelium/lightning_checkout.js
- Add env vars: STRIKE_API_KEY (from step 2)
- Add KV namespace called PENDING and bind it
- Copy the worker URL (something.workers.dev)
- Tell Claude the URL — Claude updates gallery to use it

### 4. Add DEVTO_API_KEY for article publishing (optional but free reach)
- dev.to → Settings → Account → DEV API Keys → Generate
- Add to nerve-center secrets as: DEVTO_API_KEY

## OUTREACH EMAILS — STAGED AND READY
These are written in mycelium/outreach_emails.py. Will auto-send once GMAIL_APP_PASSWORD is set:
- PCRF (info@pcrf.net) — partnership + donation routing
- Cloudinary (support@cloudinary.com) — free CDN for 12 large images
- Strike (support@strike.me) — business API access
- GitHub Sponsors (sponsors@github.com) — apply for funding

## GUMROAD — OFFICIALLY DEAD
PayPal banned Gumroad in Q4 2024. Their fee on $1 = $0.60. Removed from stack.
Never use Gumroad again for Gaza Rose.

## LARGE IMAGE SOLUTION
Still waiting on Cloudinary reply. Once they respond (auto-replied by mycelium),
Claude updates gallery to load those 12 from Cloudinary CDN URLs.
