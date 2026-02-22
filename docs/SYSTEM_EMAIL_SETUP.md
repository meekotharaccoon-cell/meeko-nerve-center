# System Email — Getting You Out of the Loop

## The Goal

The system has its own email identity.
Your personal email is removed from all automated processes.
You still own the system email. You just don't need to touch it.

## What to Create

**Email:** `solarpunk.mycelium@gmail.com`

(Or: `meeko.mycelium@gmail.com`, `spk.mycelium@gmail.com` — whatever's available)

This is not your personal email. It is the system's email. You create it once. Then you never log into it again unless something breaks.

## Setup Steps

### 1. Create the Gmail account (10 minutes)
1. Go to accounts.google.com/signup
2. Create `solarpunk.mycelium@gmail.com`
3. Use a recovery email (your real one, private, never shown publicly)
4. Enable 2FA (authenticator app, not SMS)
5. Create an App Password: Gmail Settings → Security → App Passwords → "Mail" → Copy it

### 2. Update GitHub Secrets

In meeko-nerve-center: Settings → Secrets → Add:
```
GMAIL_USER = solarpunk.mycelium@gmail.com
GMAIL_APP_PASSWORD = [the app password from step 1]
```

This is the **one secret that unlocks everything.** Every email workflow will now send from the system identity, not from you.

### 3. Update unified_emailer.py sender address

The unified_emailer already has `GMAIL_USER` pulled from environment.
Once the secret is updated, all outgoing emails come from the system.

### 4. What changes

| Before | After |
|--------|-------|
| mickowood86@gmail.com sends | solarpunk.mycelium@gmail.com sends |
| Your inbox gets responses | System inbox gets responses |
| You read and reply manually | email_responder.py reads and replies automatically |
| You are the bottleneck | The loop is closed |

### 5. Forward-only mode (optional)

Set up Gmail forwarding: any email to solarpunk.mycelium@gmail.com that the system can't auto-classify gets forwarded to your real email for review.

This way: the system handles 95% automatically. Only truly novel situations reach you.

## What Human Oversight Actually Means

The system runs itself. You built the values in.
You don't need to be the daily operator.
You are the architect.

You only need to intervene when:
- Something breaks that no script can fix
- A novel ethical situation arises that the brain didn't anticipate
- Money needs to actually move somewhere
- Legal documents need a real signature

Everything else: the system does it.
That's not removing yourself from the loop. That's being at the right level of the loop.
