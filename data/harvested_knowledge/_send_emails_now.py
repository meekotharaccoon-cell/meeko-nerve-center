#!/usr/bin/env python3
"""
MEEKO MYCELIUM - DIRECT EMAIL SENDER
Uses Gmail SMTP + App Password to send all outreach emails NOW.
Run: python send_emails_now.py
"""
import smtplib, json, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

GMAIL_USER = "mickowood86@gmail.com"
GMAIL_PASS = os.environ.get("GMAIL_PASS", "")  # 16-char app password
GALLERY    = "https://meekotharaccoon-cell.github.io/gaza-rose-gallery"
GITHUB     = "https://github.com/meekotharaccoon-cell"
SENT_LOG   = "sent_log.json"

EMAILS = [
    {
        "id": "pcrf_partnership",
        "to": "info@pcrf.net",
        "subject": "Artist Partnership — Gaza Rose Gallery Donating 70% of Sales to PCRF",
        "body": """Hi PCRF team,

My name is Meeko. I'm a self-taught digital artist and I built something specifically for your organization: Gaza Rose Gallery.

It's a fully autonomous gallery of 56 original 300 DPI digital flower artworks, each sold for $1, with 70% of every sale committed to PCRF. The system runs 24 hours a day on free infrastructure — no ads, no investors, no corporate partners. Just art and a direct line to your work.

I'm writing because I want to make sure the money reaches you with as little friction as possible. PayPal's donation processing takes roughly 3% before it reaches a nonprofit. I'd rather find a better path — whether that's a direct wire, a crypto address you already use, or a specific donation portal tied to your organization.

I have two questions:

1. Is there a preferred payment method that maximizes what you actually receive — ideally one with fees under 1%?

2. Would you be open to a brief acknowledgment or partnership letter? I'm not looking for anything promotional. I want to ensure that when I transfer donations, they're attributed correctly and auditable on my end.

The gallery is open source: https://github.com/meekotharaccoon-cell/gaza-rose-gallery

Thank you for everything you do. The children you serve are the reason this exists.

Meeko
mickowood86@gmail.com
Gaza Rose Gallery — """ + GALLERY,
    },
    {
        "id": "cloudinary_cdn",
        "to": "support@cloudinary.com",
        "subject": "Free CDN Access Request — Open Source Humanitarian Art Gallery",
        "body": """Hi Cloudinary,

I'm a solo digital artist and I built Gaza Rose Gallery (""" + GALLERY + """) — a fully open-source, autonomous digital art gallery where 70% of every $1 sale goes directly to the Palestine Children's Relief Fund.

The entire stack runs on free infrastructure: GitHub Pages hosts it, GitHub Actions runs it, PayPal and Bitcoin handle payments. Total monthly cost: $0. That's intentional — every dollar belongs to the mission.

I have 12 high-resolution artworks (300 DPI, 50–125 MB each PNG files) that are too large to serve from GitHub. Your CDN and automatic WebP conversion would solve this completely — and it's exactly the kind of technical problem Cloudinary was built for.

I'm writing to ask whether you have a humanitarian or open-source free tier for projects like this. I'm not a company. I'm one person with a keyboard and a cause.

If a free account isn't possible, I completely understand. But if it is, I'd credit Cloudinary visibly in the gallery and in the GitHub README — which is public and indexed.

The project GitHub: """ + GITHUB + """

Thank you for reading this,
Meeko
mickowood86@gmail.com""",
    },
    {
        "id": "strike_api_access",
        "to": "support@strike.me",
        "subject": "API Access for Humanitarian Lightning Payments — Gaza Rose Gallery",
        "body": """Hi Strike team,

I just signed up for Strike and I'm building Lightning Network payments into Gaza Rose Gallery (""" + GALLERY + """) — a $1-per-artwork digital gallery where 70% of sales goes to the Palestine Children's Relief Fund.

Lightning is the right tool for this. Near-zero fees on $1 transactions means more money reaches Gaza. PayPal takes ~49 cents on every dollar I sell. That's not acceptable when the mission is this direct.

I'd like to use the Strike API to:
- Generate Lightning invoices when a buyer clicks "Pay" on a piece
- Poll payment status and auto-deliver the download link on confirmation
- Keep everything serverless — no backend, just GitHub Actions and a Cloudflare Worker

I understand I may need to upgrade to a business account for API access. I'm happy to do whatever that requires. My goal is to make Lightning the default payment method so PayPal becomes the backup.

Can you tell me the fastest path to get API access for a small humanitarian creator? I've already built the Cloudflare Worker for the integration — I just need the key.

Thank you,
Meeko
mickowood86@gmail.com
""" + GALLERY,
    },
    {
        "id": "github_sponsors",
        "to": "sponsors@github.com",
        "subject": "GitHub Sponsors Application — Gaza Rose Mycelium (Open Source Humanitarian)",
        "body": """Hi GitHub Sponsors team,

I'd like to apply for GitHub Sponsors for Gaza Rose Gallery — an autonomous, open-source humanitarian art system that runs entirely on GitHub infrastructure.

What it is: 56 original digital flower artworks, $1 each, 70% of every sale routed to the Palestine Children's Relief Fund. The system promotes itself, checks its own health, responds to emails, and updates its own memory — all via GitHub Actions, zero monthly cost.

GitHub org: meekotharaccoon-cell
Main repo: """ + GITHUB + """/meeko-nerve-center
Gallery: """ + GALLERY + """

What makes this worth sponsoring: the entire architecture is open source and replicable. Anyone running a humanitarian project could fork this and have a fully autonomous fundraising system in an afternoon. Sponsorship would let me document it properly, add more art, and potentially build a toolkit for other causes to use.

I'm a solo developer and artist. This started as an experiment in ethical automation and became something real. I'd be honored to be part of GitHub Sponsors.

Happy to provide any additional information.

Meeko
mickowood86@gmail.com""",
    },
    {
        "id": "tech_for_palestine",
        "to": "hello@techforpalestine.org",
        "subject": "Open Source Humanitarian Gallery Built on GitHub — Sharing for the Community",
        "body": """Hi Tech for Palestine,

I built something I think belongs in your community: Gaza Rose Gallery.

It's a fully autonomous digital art gallery — 56 original 300 DPI floral artworks by me (Meeko), $1 each, 70% committed to PCRF. The whole system runs on free GitHub infrastructure: GitHub Pages hosts the gallery, GitHub Actions handles promotion and health checks, PayPal and Bitcoin handle payments. No ads, no investors, no middlemen I can avoid.

The architecture I built — which I'm calling the Meeko Mycelium — treats the whole system like a living organism. It has a memory (a private GitHub repo that stores state), a heartbeat (twice-daily GitHub Actions schedules), a voice (it posts to platforms automatically), and hands (it processes payments). All of it is open source.

I'm sharing this because I think the pattern is useful beyond my gallery. Anyone running a humanitarian tech project could fork this and have a self-sustaining fundraising system without a server, without a monthly bill, without much technical background.

The repos are at: """ + GITHUB + """
The gallery is live at: """ + GALLERY + """

If this is useful to your community, please share it. If there's a better place to submit it, point me there.

Thank you for what you do,
Meeko
mickowood86@gmail.com""",
    },
    {
        "id": "producthunt_hunter",
        "to": "hello@producthunt.com",
        "subject": "Submission Inquiry — Gaza Rose Gallery (Humanitarian AI Art System)",
        "body": """Hi Product Hunt team,

I'm wondering if Gaza Rose Gallery would be a good fit for a Product Hunt launch and whether there's a process for humanitarian/open-source projects.

What it is: A fully autonomous digital art gallery built by a solo artist (me, Meeko). 56 original 300 DPI digital flower artworks. $1 each. 70% of every sale goes to the Palestine Children's Relief Fund. The system runs entirely on free GitHub infrastructure — it promotes itself, monitors itself, and now replies to emails automatically via AI. Zero monthly cost.

What makes it interesting technically: The entire stack is serverless and free. GitHub Actions replaces a backend. A private GitHub repo acts as persistent AI memory. Lightning Network (via Strike) is being integrated for near-zero-fee $1 payments. The whole architecture is open source and documented.

What makes it interesting as a product: It's a proof that one person with a keyboard and free cloud tools can build something with genuine humanitarian impact that runs itself indefinitely.

Gallery: """ + GALLERY + """
Code: """ + GITHUB + """

I know Product Hunt has a launch process — I'm not asking to skip it, just to understand whether this fits and if there's a recommended path for projects like this.

Thank you,
Meeko
mickowood86@gmail.com""",
    },
]

def load_sent():
    try:
        with open(SENT_LOG) as f:
            return json.load(f)
    except:
        return {}

def save_sent(sent):
    with open(SENT_LOG, "w") as f:
        json.dump(sent, f, indent=2)

def send(to, subject, body):
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
        print("ERROR: Set GMAIL_PASS environment variable first.")
        print("Get it: myaccount.google.com/security → 2-Step Verification → App Passwords")
        print("\nAll 6 emails ready to send:")
        for e in EMAILS:
            print(f"  → {e['to']} | {e['subject']}")
        return

    sent = load_sent()
    for e in EMAILS:
        if e["id"] in sent:
            print(f"Already sent: {e['id']}")
            continue
        try:
            send(e["to"], e["subject"], e["body"])
            sent[e["id"]] = {
                "to": e["to"],
                "subject": e["subject"],
                "sent_at": datetime.now(timezone.utc).isoformat()
            }
            save_sent(sent)
            print(f"SENT: {e['to']}")
        except Exception as ex:
            print(f"FAILED {e['to']}: {ex}")

if __name__ == "__main__":
    run()
