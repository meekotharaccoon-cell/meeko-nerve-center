#!/usr/bin/env python3
"""
MYCELIUM OUTREACH EMAILS
Fully composed. Never repeated. Sent once per ID.
Activates when GMAIL_APP_PASSWORD secret is set.
"""
import smtplib, json, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

GMAIL_USER = "mickowood86@gmail.com"
GMAIL_PASS = os.environ.get("GMAIL_APP_PASSWORD", "")
GALLERY    = "https://meekotharaccoon-cell.github.io/gaza-rose-gallery"
GITHUB     = "https://github.com/meekotharaccoon-cell"
SENT_LOG   = "mycelium/sent_outreach.json"

EMAILS = [
    {
        "id": "pcrf_partnership",
        "to": "info@pcrf.net",
        "subject": "Artist Partnership \u2014 Gaza Rose Gallery Donating 70% of Sales to PCRF",
        "body": """Hi PCRF team,

My name is Meeko. I'm a self-taught digital artist and I built something specifically for your organization: Gaza Rose Gallery.

It's a fully autonomous gallery of 56 original 300 DPI digital flower artworks, each sold for $1, with 70% of every sale committed to PCRF. The system runs 24 hours a day on free infrastructure \u2014 no ads, no investors, no corporate partners. Just art and a direct line to your work.

I want to make sure the money reaches you with as little friction as possible. PayPal's donation processing takes roughly 3% before it reaches a nonprofit. I'd rather find a better path \u2014 whether that's a direct wire, a crypto address you already use, or a specific donation portal tied to your organization.

Two questions:
1. Is there a preferred payment method that maximizes what you actually receive \u2014 ideally under 1% fees?
2. Would you be open to a brief acknowledgment so I can attribute donations correctly?

The gallery is open source: https://github.com/meekotharaccoon-cell/gaza-rose-gallery

Thank you for everything you do. The children you serve are the reason this exists.

Meeko
mickowood86@gmail.com
https://meekotharaccoon-cell.github.io/gaza-rose-gallery"""
    },
    {
        "id": "cloudinary_cdn",
        "to": "support@cloudinary.com",
        "subject": "Free CDN Access Request \u2014 Open Source Humanitarian Art Gallery",
        "body": """Hi Cloudinary,

I'm a solo digital artist who built Gaza Rose Gallery (https://meekotharaccoon-cell.github.io/gaza-rose-gallery) \u2014 a fully open-source autonomous gallery where 70% of every $1 sale goes to the Palestine Children's Relief Fund.

The whole stack runs on free infrastructure. Total monthly cost: $0. That's intentional \u2014 every dollar belongs to the mission.

I have 12 high-resolution artworks (300 DPI, 50\u2013125 MB each) too large to serve from GitHub. Your CDN and automatic WebP conversion would solve this completely.

I'm asking whether you have a humanitarian or open-source free tier for projects like this. If yes, I'd credit Cloudinary visibly in the gallery and GitHub README.

Project: https://github.com/meekotharaccoon-cell/gaza-rose-gallery

Thank you,
Meeko
mickowood86@gmail.com"""
    },
    {
        "id": "strike_api",
        "to": "support@strike.me",
        "subject": "API Access for Humanitarian Lightning Payments \u2014 Gaza Rose Gallery",
        "body": """Hi Strike team,

I just signed up for Strike and I'm integrating Lightning payments into Gaza Rose Gallery (https://meekotharaccoon-cell.github.io/gaza-rose-gallery) \u2014 a $1-per-artwork gallery where 70% of sales goes to the Palestine Children's Relief Fund.

Lightning is the right tool here. PayPal takes ~49 cents on every $1 I sell. That's not acceptable when the mission is this direct.

I need the Strike API to generate Lightning invoices from a Cloudflare Worker (serverless, no backend). I've already built the integration \u2014 I just need API access.

Can you point me to the fastest path to get API access as a small humanitarian creator?

Thank you,
Meeko
mickowood86@gmail.com
https://meekotharaccoon-cell.github.io/gaza-rose-gallery"""
    },
    {
        "id": "github_sponsors",
        "to": "sponsors@github.com",
        "subject": "GitHub Sponsors Application \u2014 Gaza Rose Mycelium (Open Source Humanitarian)",
        "body": """Hi GitHub Sponsors team,

I'd like to apply for GitHub Sponsors for Gaza Rose Mycelium \u2014 an autonomous, open-source humanitarian art system running entirely on GitHub infrastructure.

What it is: 56 original digital artworks, $1 each, 70% to Palestine Children's Relief Fund. GitHub Actions handles everything \u2014 promotion, health checks, email responses, memory sync. Zero monthly cost.

GitHub org: meekotharaccoon-cell
Repo: https://github.com/meekotharaccoon-cell/meeko-nerve-center
Gallery: https://meekotharaccoon-cell.github.io/gaza-rose-gallery

The architecture is forkable and replicable for any humanitarian cause. Sponsorship would help me document it and build it into a proper toolkit.

Happy to provide anything needed.

Meeko
mickowood86@gmail.com"""
    },
    {
        "id": "tech_for_palestine",
        "to": "hello@techforpalestine.org",
        "subject": "Open Source Humanitarian Gallery \u2014 Sharing for the Community",
        "body": """Hi Tech for Palestine,

I built something that belongs in your community: Gaza Rose Gallery.

56 original digital artworks by me (Meeko), $1 each, 70% to PCRF. The system is fully autonomous \u2014 GitHub Actions handles everything, zero monthly cost, fully open source.

I'm calling the architecture the Meeko Mycelium: a living digital organism with memory (private GitHub repo), heartbeat (twice-daily Actions), voice (platform posting), and hands (payment processing). Anyone could fork it for their own humanitarian project.

Repos: https://github.com/meekotharaccoon-cell
Gallery: https://meekotharaccoon-cell.github.io/gaza-rose-gallery

Sharing it if useful. No ask beyond that.

Meeko
mickowood86@gmail.com"""
    },
    {
        "id": "producthunt",
        "to": "hello@producthunt.com",
        "subject": "Launch Inquiry \u2014 Gaza Rose Gallery (Humanitarian AI Art System)",
        "body": """Hi Product Hunt,

I'm wondering if Gaza Rose Gallery is a good fit for a launch and what the right process is.

What it is: A fully autonomous digital art gallery. 56 original 300 DPI digital flowers, $1 each, 70% to Palestine Children's Relief Fund. The whole system runs on free GitHub infrastructure \u2014 no backend, no monthly cost, open source.

What's technically interesting: GitHub Actions replaces a backend. A private repo acts as persistent AI memory. Lightning Network payments are being integrated for near-zero fees. The architecture is replicable for any humanitarian cause.

Gallery: https://meekotharaccoon-cell.github.io/gaza-rose-gallery
Code: https://github.com/meekotharaccoon-cell

Just asking about process \u2014 happy to follow whatever path you recommend.

Meeko
mickowood86@gmail.com"""
    },
]

def load_sent():
    try:
        with open(SENT_LOG) as f: return json.load(f)
    except: return {}

def save_sent(sent):
    os.makedirs("mycelium", exist_ok=True)
    with open(SENT_LOG, "w") as f: json.dump(sent, f, indent=2)

def send_email(to, subject, body):
    msg = MIMEMultipart()
    msg["From"] = f"Meeko / Gaza Rose Gallery <{GMAIL_USER}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)

def run():
    if not GMAIL_PASS:
        print("[Outreach] GMAIL_APP_PASSWORD not set. Emails ready but not sending.")
        return
    sent = load_sent()
    for e in EMAILS:
        if e["id"] in sent:
            print(f"[Outreach] Already sent: {e['id']}")
            continue
        try:
            send_email(e["to"], e["subject"], e["body"])
            sent[e["id"]] = {"to": e["to"], "sent_at": datetime.now(timezone.utc).isoformat()}
            save_sent(sent)
            print(f"[Outreach] SENT -> {e['to']}")
        except Exception as ex:
            print(f"[Outreach] FAILED {e['to']}: {ex}")

if __name__ == "__main__":
    run()
