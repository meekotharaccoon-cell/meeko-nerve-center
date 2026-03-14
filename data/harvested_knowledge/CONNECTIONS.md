# System Connections

*Every live integration + every unlock waiting for a secret*

---

## Live (no secrets needed)

| Connection | What it does |
|---|---|
| GitHub API | Fork tracking, wiring status |
| Wikipedia REST API | Daily knowledge harvest |
| arXiv API | AI + humanitarian papers |
| HackerNews Firebase | Daily stories |
| NASA Open APIs | Daily data |
| GitHub Pages | All web hosting |
| GitHub Actions | All automation (34 workflows) |
| Ollama (local) | Private AI reasoning |
| RSS Feeds | Anyone can subscribe to your content |

## Unlock with one secret each

| Secret | What unlocks | Setup time | Where to get it |
|---|---|---|---|
| `NOTION_TOKEN` | Daily reports auto-write to Notion | 5 min | notion.so/my-integrations |
| `TELEGRAM_TOKEN` + `TELEGRAM_CHAT_ID` | Morning briefing on your phone + command interface | 5 min | @BotFather on Telegram |
| `HF_TOKEN` | Daily upload to HuggingFace (30M+ AI users) | 2 min | huggingface.co/settings/tokens |
| `MASTODON_TOKEN` + `MASTODON_SERVER` | Auto-posts to fediverse | 5 min | Any Mastodon instance |
| `GMAIL_APP_PASSWORD` | Grant applications sent automatically | 5 min | myaccount.google.com > App Passwords |
| `GUMROAD_TOKEN` | Fork guide delivery + stats | 2 min | Gumroad Settings > Advanced |

## The fastest unlocks (do these first)

**Telegram (5 min)** — morning briefing on your phone, reply with /posts /fixes /emails
```
1. Message @BotFather on Telegram -> send /newbot
2. Copy the token -> GitHub Secrets -> TELEGRAM_TOKEN
3. Message your new bot once (anything)
4. Run locally: python mycelium/telegram_bot.py --get-chat-id
5. Add the chat ID -> GitHub Secrets -> TELEGRAM_CHAT_ID
```

**HuggingFace (2 min)** — indexed by 30M+ ML/AI researchers
```
1. huggingface.co/settings/tokens -> New token (write)
2. GitHub Secrets -> HF_TOKEN
Done. Daily harvest uploads automatically.
```

**Notion (5 min)** — daily reports appear in your Notion automatically
```
1. notion.so/my-integrations -> New integration
2. GitHub Secrets -> NOTION_TOKEN
3. In Notion: create page "Meeko Nerve Center" -> Share with integration
Done. Reports appear every morning at 7:45am UTC.
```

## What becomes possible when everything is connected

```
You wake up. Telegram message is waiting:
"Gaza focus today. 3 posts queued. 0 fixes needed. 7 draft emails ready."

You reply: /posts
Bot sends you the 3 posts. You copy one, post it manually.

You open Notion. Daily report is already there.
Draft emails are in a Notion page. You open Gmail, paste, send.

HuggingFace shows 47 people downloaded yesterday's knowledge harvest.
One of them starred the repo.

RSS feed has 12 subscribers. They got the newsletter automatically.

All of this happened while you slept.
```
