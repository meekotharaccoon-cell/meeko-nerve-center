# YouTube Setup — 10-Minute One-Time Process

Once done, the system auto-updates your descriptions, tracks stats, and responds to comments forever with no intervention.

---

## Step 1: Create a Google Cloud Project (3 minutes)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **"New Project"** → name it "SolarPunk Mycelium" → Create
3. In the left menu: **APIs & Services** → **Enable APIs**
4. Search for and enable: **YouTube Data API v3**
5. It's free. 10,000 units/day quota (description updates use 50 units each)

---

## Step 2: Create OAuth Credentials (3 minutes)

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: "SolarPunk YouTube"
5. Download the JSON — you'll see `client_id` and `client_secret`

---

## Step 3: Get Your Refresh Token (4 minutes)

Run this once on your local machine:

```bash
pip install google-auth-oauthlib
```

Create a file called `get_token.py`:

```python
from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# Replace with your actual values from Step 2
CLIENT_ID = 'your-client-id.apps.googleusercontent.com'
CLIENT_SECRET = 'your-client-secret'

flow = InstalledAppFlow.from_client_config(
    {"installed": {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
     "redirect_uris": ["http://localhost"], "auth_uri": "https://accounts.google.com/o/oauth2/auth",
     "token_uri": "https://oauth2.googleapis.com/token"}},
    scopes=SCOPES
)
creds = flow.run_local_server(port=0)
print('\nREFRESH TOKEN (save this):')
print(creds.refresh_token)
```

```bash
python get_token.py
```

Your browser opens. Sign in to the Google account that owns your YouTube channel. Authorize. Copy the refresh token printed in the terminal.

---

## Step 4: Add GitHub Secrets

Go to your `meeko-nerve-center` repo:
**Settings → Secrets and variables → Actions → New repository secret**

Add these four:

| Secret Name | Value |
|-------------|-------|
| `YOUTUBE_CLIENT_ID` | from Step 2 |
| `YOUTUBE_CLIENT_SECRET` | from Step 2 |
| `YOUTUBE_REFRESH_TOKEN` | from Step 3 |
| `YOUTUBE_CHANNEL_ID` | your channel ID (from YouTube Studio URL) |
| `GUMROAD_FLOWERS_URL` | your flower designs Gumroad URL |

**Your channel ID:** Go to YouTube Studio. The URL will be like:
`https://studio.youtube.com/channel/UCxxxxxxxxxxxxxxx`
The `UCxxxxxxxxxxxxxxx` part is your channel ID.

---

## Step 5: Trigger the Workflow

Go to `meeko-nerve-center` → **Actions** → **YouTube Manager**

First run: set `YT_DRY_RUN` to `true` — it will show you what it WOULD do without making changes.

When you're happy: re-run with `YT_DRY_RUN` set to `false`. Every video gets the updated description.

**From then on:** The workflow runs automatically. New videos get updated within 24 hours.

---

## What It Does After Setup

- **Daily:** Checks for new videos, updates their descriptions with your Gumroad + gallery links
- **Daily:** Logs channel stats (subscribers, views) to `data/youtube_log.json`
- **Weekly:** Scans comments for questions and optionally auto-replies
- **All of it:** Commits results back to the repo automatically, runs with zero intervention

---

## Cost

$0. YouTube Data API is free at this usage level.
Google Cloud has a free tier that covers this comfortably.

---

## Your Two Gumroad Accounts

You have two:
1. **Gaza Rose Gallery Gumroad** — $1 artworks, 70% to PCRF
2. **Flower designs Gumroad** — your commercial designs for sale

The description footer links to both. The videos drive traffic to both.
Set `GUMROAD_FLOWERS_URL` to your flower designs URL.
The gallery link is already hardcoded.
