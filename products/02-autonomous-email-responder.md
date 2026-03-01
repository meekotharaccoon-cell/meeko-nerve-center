# The Autonomous Email Responder
### "I haven't answered an email myself in 3 weeks."

*The viral claim is real. Here's the actual code that does it.*

**Price: $1 — 70% goes to PCRF (children's aid in Gaza)**

---

## What You're Getting

The complete Python script, Gmail setup instructions, and prompt engineering to build an AI that reads your emails and responds in your voice — automatically, 24/7, without you touching it.

This is the exact system running on the machine that made this guide. It handles real emails. It works.

---

## How It Actually Works

```
New email arrives in Gmail
       ↓
Script checks Gmail every 15 minutes
       ↓
AI reads the email + your context file
       ↓
Generates a reply in your voice
       ↓
Sends the reply (or saves as draft for review)
       ↓
Logs what it did
```

Two modes: **Auto-send** (fully autonomous) or **Draft mode** (you approve before sending). Start with Draft mode. Switch to Auto when you trust it.

---

## Step 1: Create a Gmail App Password

You need this so the script can access Gmail without your main password.

1. Go to **myaccount.google.com**
2. Click **Security** → **2-Step Verification** (enable if not on)
3. At the bottom: **App passwords**
4. Select "Mail" and your device → click **Generate**
5. Copy the 16-character password — you'll use it once

---

## Step 2: The Complete Script

Save this as `email_responder.py`:

```python
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json
import time
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────
GMAIL_ADDRESS = "your@gmail.com"
GMAIL_APP_PASSWORD = "your-16-char-app-password"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"
DRAFT_MODE = True  # Set False to auto-send
CHECK_INTERVAL = 900  # 15 minutes

# Your context — the AI reads this to understand you
YOUR_CONTEXT = """
My name is [YOUR NAME].
I work as [YOUR ROLE].
My communication style is [professional/casual/warm].
I typically respond to emails within [24 hours].
For meeting requests: [I prefer afternoons / I'm fully booked until X date].
For sales pitches: [Politely decline].
For collaboration inquiries: [Express interest, ask for more details].
"""

PROCESSED_LOG = "processed_emails.json"

# ── FUNCTIONS ────────────────────────────────────────

def load_processed():
    try:
        with open(PROCESSED_LOG) as f:
            return json.load(f)
    except:
        return []

def save_processed(ids):
    with open(PROCESSED_LOG, "w") as f:
        json.dump(ids, f)

def get_unread_emails():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    mail.select("inbox")
    _, data = mail.search(None, "UNSEEN")
    email_ids = data[0].split()
    emails = []
    for eid in email_ids:
        _, msg_data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()
        emails.append({
            "id": eid.decode(),
            "from": msg["From"],
            "subject": msg["Subject"],
            "body": body[:2000]  # Limit length
        })
    mail.logout()
    return emails

def generate_reply(sender, subject, body):
    prompt = f"""You are an email assistant writing on behalf of someone with this context:

{YOUR_CONTEXT}

You received this email:
FROM: {sender}
SUBJECT: {subject}
MESSAGE: {body}

Write a helpful, appropriate reply. Be concise. Match the tone of the email.
Only write the reply body — no subject line, no "Dear Claude", no preamble.
Sign off with the person's first name from the context."""

    response = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]

def send_email(to, subject, body):
    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to
    msg["Subject"] = f"Re: {subject}"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)
    print(f"  ✅ Sent reply to {to}")

def save_draft(to, subject, body):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"draft_{timestamp}.txt"
    with open(filename, "w") as f:
        f.write(f"TO: {to}\nSUBJECT: Re: {subject}\n\n{body}")
    print(f"  📝 Draft saved: {filename}")

# ── MAIN LOOP ────────────────────────────────────────

def main():
    print(f"📬 Email Responder running — checking every {CHECK_INTERVAL//60} minutes")
    print(f"   Mode: {'DRAFT' if DRAFT_MODE else 'AUTO-SEND'}")

    processed = load_processed()

    while True:
        try:
            emails = get_unread_emails()
            print(f"   Found {len(emails)} unread emails")

            for em in emails:
                if em["id"] in processed:
                    continue

                print(f"  📧 Processing: {em['subject']} from {em['from']}")
                reply = generate_reply(em["from"], em["subject"], em["body"])

                if DRAFT_MODE:
                    save_draft(em["from"], em["subject"], reply)
                else:
                    send_email(em["from"], em["subject"], reply)

                processed.append(em["id"])
                save_processed(processed)
                time.sleep(2)  # Don't hammer the API

        except Exception as e:
            print(f"  ⚠️ Error: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
```

---

## Step 3: Customize Your Context

The `YOUR_CONTEXT` variable is everything. The more specific you are, the better it writes like you.

Good context includes:
- Your actual name and role
- How you prefer to handle meeting requests
- Your typical availability
- Any standing rules ("always decline MLM inquiries", "always express interest in media requests")
- Your communication style ("warm and direct", "formal and brief")

Bad context: "I am a person who receives emails." (Too vague — AI will write generic replies)

---

## Step 4: Run It

```bash
# Install dependencies
pip install requests

# Make sure Ollama is running (see Product 1)
ollama serve

# Run the responder
python email_responder.py
```

It will start checking your inbox every 15 minutes and saving drafts to your folder.

Review 5–10 drafts. If they're good, set `DRAFT_MODE = False` and let it run.

---

## Running It 24/7

**On Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task → "Email Responder"
3. Trigger: At startup
4. Action: Start a program → `python` → Arguments: `C:\path\to\email_responder.py`

**On Mac/Linux (cron):**
```bash
# Add to crontab (runs at reboot)
@reboot python3 /path/to/email_responder.py &
```

---

## What It Won't Do (Be Honest)

- Won't handle emails requiring real decisions (contracts, emergencies)
- Won't be perfect — review edge cases
- Won't work if Ollama isn't running or internet is down
- Not for high-stakes professional email chains without human review

Start with Draft mode. Use it for routine emails: scheduling, information requests, polite declines. Keep humans in the loop for anything important.

---

## The Honest Part

The viral claim "I haven't answered an email in 3 weeks" is achievable for routine correspondence. Not for everything. But "I haven't answered routine scheduling emails in 3 weeks" is genuinely possible with this setup — and that alone saves hours per week.

This runs on the same machine as this guide. It works.

---

*Built by Meeko Mycelium — a fully autonomous AI system running on a 6-year-old desktop.*
*Source: github.com/meekotharaccoon-cell/meeko-nerve-center*
*License: AGPL-3.0 + Ethical Use Rider*
*70% of every sale → PCRF (Palestine Children's Relief Fund) · pcrf.net*
