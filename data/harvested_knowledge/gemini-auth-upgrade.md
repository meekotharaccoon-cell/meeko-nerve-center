# Gemini Auth Upgrade Guide

**Purpose:** Upgrade from API Key authentication (20-250 RPD) to Google Login (1,000 RPD)

---

## Background

API Key authentication has severe rate limits:
- Free tier: ~20 requests per day (RPD)
- With billing: ~250 RPD

Google Login OAuth provides:
- 1,000 RPD per account
- More stable for overnight runs

---

## Steps for Each Agent (PC1, PC2, PC3)

### 1. SSH to the Agent

```bash
# From manager machine
ssh pc1  # or pc2, pc3
```

### 2. Remove Existing API Key (if set)

```bash
# Check current auth method
echo $GEMINI_API_KEY
cat ~/.gemini/config.json

# Unset API key to force OAuth
unset GEMINI_API_KEY
# Also remove from .bashrc if present
sed -i '/GEMINI_API_KEY/d' ~/.bashrc
```

### 3. Start Gemini Interactive Mode

```bash
gemini
```

This will open a browser window (or provide a URL) for Google OAuth.

### 4. Complete OAuth in Browser

1. Click the authentication link shown in terminal
2. Sign in with Google account
3. Grant permissions to Gemini CLI
4. Browser will show "Authentication successful"

### 5. Verify OAuth Credentials Saved

```bash
ls -la ~/.gemini/
# Should see: oauth_creds.json
```

### 6. Test Authentication

```bash
gemini -p "Say hello and confirm you're working"
```

Expected: Response without rate limit errors.

### 7. Verify Rate Limit

```bash
# Run multiple quick tests
for i in {1..10}; do
    gemini -p "Say $i" --no-yolo
    sleep 2
done
```

All 10 should complete without 429 errors.

---

## Checklist

| Agent | SSH Access | OAuth Complete | Creds File | Test OK |
|-------|------------|----------------|------------|---------|
| PC1 (backend) | [ ] | [ ] | [ ] | [ ] |
| PC2 (frontend) | [ ] | [ ] | [ ] | [ ] |
| PC3 (tests) | [ ] | [ ] | [ ] | [ ] |

---

## Troubleshooting

### "No browser available"

If agent is headless:
```bash
# On agent, start gemini and get URL
gemini

# Copy the auth URL shown
# Open on any machine with browser
# Complete auth, copy callback URL
# Paste callback URL back into agent terminal
```

### "OAuth credentials expired"

```bash
rm ~/.gemini/oauth_creds.json
gemini  # Re-authenticate
```

### "Permission denied"

Ensure the Google account has Gemini API access enabled at:
https://aistudio.google.com/

---

## Post-Upgrade

After all agents are upgraded:

1. Update any scripts that set `GEMINI_API_KEY`
2. Verify overnight runs don't hit rate limits
3. Monitor logs for 429 errors (should be rare now)

---

**Created:** Sprint 1, February 2026
**Status:** Requires physical/SSH access to each agent
