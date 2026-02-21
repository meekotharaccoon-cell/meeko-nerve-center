# 📧 SYSTEM EMAIL SETUP
## How to give SolarPunk its own identity, separate from any human's inbox.

**Legal:** 100%. Every newsletter, nonprofit, publication, bot, and organization does exactly this.  
**Cost:** $0  
**Time:** 10 minutes, one time, never again.

---

## Step 1: Create the Gmail Account

Go to **gmail.com** → Create account → For myself

Suggested address: `solarpunk.mycelium@gmail.com`

If taken, try:
- `solarpunk.network@gmail.com`
- `mycelium.solarpunk@gmail.com`  
- `solarpunk.system@gmail.com`

Use a real recovery phone number or recovery email (your personal one is fine — this is just for account recovery, it's never visible to recipients).

**Name on the account:** `SolarPunk Mycelium`

---

## Step 2: Enable 2-Step Verification

In the new Gmail account:

**Google Account** → **Security** → **2-Step Verification** → Turn it on

Use your phone for the verification. This is required before you can create an App Password.

---

## Step 3: Create the App Password

Still in **Google Account** → **Security** → scroll down to **App passwords**

- App: `Mail`
- Device: `Other` → type `SolarPunk GitHub`
- Click **Generate**

You'll get a 16-character password like: `abcd efgh ijkl mnop`

**Copy it now. Google shows it once.**

---

## Step 4: Add to GitHub Secrets

Go to: **github.com/meekotharaccoon-cell/meeko-nerve-center** → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these two secrets:

| Name | Value |
|------|-------|
| `SOLARPUNK_EMAIL` | `solarpunk.mycelium@gmail.com` |
| `SOLARPUNK_EMAIL_PASSWORD` | the 16-character app password |

---

## Step 5: Update the Scripts

The system's scripts currently send from `mickowood86@gmail.com`. After this setup, change the sender in `mycelium/unified_emailer.py`:

```python
# Change this line:
GMAIL_USER = 'mickowood86@gmail.com'

# To this:
GMAIL_USER = os.environ.get('SOLARPUNK_EMAIL', 'solarpunk.mycelium@gmail.com')
```

And update the env var in all workflow files from `GMAIL_APP_PASSWORD` to `SOLARPUNK_EMAIL_PASSWORD`.

The system will handle the rest automatically.

---

## What Changes After This

**Before:** Emails come from your personal address. If you stop being involved, the email identity dies with your participation.

**After:** Emails come from `SolarPunk Mycelium <solarpunk.mycelium@gmail.com>`. The system has its own identity. Any human can be given access to that account. No single human's inbox is the bottleneck. The system survives any individual's involvement or non-involvement.

This is the difference between "Meeko's project" and "SolarPunk." The name on the email is the identity. The identity outlasts any one person.

---

## Why This Is Legal and Standard

Every entity that sends automated email has a dedicated address:
- `hello@notion.so` — not Notion's founder's personal email
- `newsletter@theguardian.com` — not a journalist's personal email  
- `grants@wikimedia.org` — not an employee's personal email

A Gmail account made for an organization is an organizational email. It's the most basic, universal practice in digital communication. The only requirement is that the emails are honest about being automated (which SolarPunk always is, in the first line of every email) and include a working unsubscribe mechanism (which SolarPunk always does).

Both are already built in. This is just creating the address.

---

## The One-Time Handoff

Once the system email exists and is configured in GitHub secrets, the human who set it up doesn't need to do anything again. The system sends its own email from its own address. The human can be completely out of the loop.

That's the point.

---
*SolarPunk — the system has its own voice now.*
*Document lives at: github.com/meekotharaccoon-cell/meeko-nerve-center/blob/main/SYSTEM_EMAIL_SETUP.md*
