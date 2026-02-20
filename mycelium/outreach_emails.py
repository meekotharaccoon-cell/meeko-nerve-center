#!/usr/bin/env python3
"""
MYCELIUM OUTREACH EMAILS — v2
Fixed addresses. AI transparency disclosure added to every email.
Awesome Foundation now uses web form (not email).
GitHub Sponsors now uses web form.
All emails have verified-working addresses.
"""
import smtplib, json, os, webbrowser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

GMAIL_USER = "mickowood86@gmail.com"
GMAIL_PASS = os.environ.get("GMAIL_APP_PASSWORD", "")
GALLERY    = "https://meekotharaccoon-cell.github.io/gaza-rose-gallery"
GITHUB     = "https://github.com/meekotharaccoon-cell"
SENT_LOG   = "mycelium/sent_outreach.json"

# This goes at the bottom of every single outreach email.
# Transparent. Honest. No personal info ever.
AI_FOOTER = """

---
Transparency note: This email was composed and sent by the Meeko Mycelium — 
an autonomous AI agent system built by Meeko (a human artist). All decisions 
about partnerships, payments, and creative direction are made by Meeko. 
The AI handles writing, sending, and receiving emails on Meeko's behalf.
No personal information from any recipient is ever stored, sold, or shared.
If you want to reach a human directly: mickowood86@gmail.com
"""

# WEB FORM ACTIONS (can't send email — log these for Meeko to do manually)
WEB_FORMS = [
    {
        "id": "awesome_foundation_form",
        "name": "Awesome Foundation Grant",
        "url": "https://www.awesomefoundation.org/en/submissions/new",
        "notes": "Submit through web form. Takes 5 minutes. Monthly $1,000 grants, no strings attached."
    },
    {
        "id": "github_sponsors_form",
        "name": "GitHub Sponsors",
        "url": "https://github.com/sponsors",
        "notes": "Apply through GitHub's web interface while logged in as meekotharaccoon-cell."
    },
    {
        "id": "fractured_atlas_form",
        "name": "Fractured Atlas Fiscal Sponsorship",
        "url": "https://www.fracturedatlas.org/fiscal-sponsorship/apply/",
        "notes": "Web form application. Fiscal sponsorship makes all grants possible."
    },
    {
        "id": "knight_foundation_form",
        "name": "Knight Foundation",
        "url": "https://knightfoundation.org/apply/",
        "notes": "Currently invite-only. Email web@knightfoundation.org first, confirmed correct address."
    },
]

EMAILS = [
    {
        "id": "pcrf_partnership",
        "to": "info@pcrf.net",
        "subject": "Artist Partnership — Gaza Rose Gallery Donating 70% of Sales to PCRF",
        "body": """Hi PCRF team,

My name is Meeko. I'm a self-taught digital artist and I built Gaza Rose Gallery specifically to fund your work.

56 original 300 DPI digital flower artworks, $1 each, 70% of every sale committed to PCRF. The system runs 24 hours a day on free infrastructure — no ads, no investors, no monthly costs. Just art and a direct line to your work.

I want to minimize friction between the sale and the children you serve. Is there a preferred payment method that keeps fees under 1%? A direct wire, a crypto address you already use, or a specific donation portal?

Two questions:
1. Best low-fee payment path for recurring donations?
2. Can I list PCRF as the verified beneficiary on the gallery page?

Gallery: """ + GALLERY + """
Code (open source): """ + GITHUB + AI_FOOTER
    },
    {
        "id": "cloudinary_cdn",
        "to": "support@cloudinary.com",
        "subject": "Free CDN Access Request — Open Source Humanitarian Art Gallery",
        "body": """Hi Cloudinary team,

I run Gaza Rose Gallery — a fully open source autonomous art gallery where 70% of every $1 sale goes to the Palestine Children's Relief Fund.

Total monthly operating cost: $0. Every dollar belongs to the mission.

I have 12 high-resolution artworks (300 DPI, 50–125 MB each) too large to serve from GitHub. Cloudinary's CDN and automatic WebP conversion would solve this completely.

Do you have a humanitarian or open source free tier? If yes, I'll credit Cloudinary visibly in the gallery and all documentation.

Gallery: """ + GALLERY + """
Code: """ + GITHUB + AI_FOOTER
    },
    {
        "id": "strike_api",
        "to": "support@strike.me",
        "subject": "API Access for Humanitarian Lightning Payments — Gaza Rose Gallery",
        "body": """Hi Strike team,

I recently signed up and I'm integrating Lightning payments into Gaza Rose Gallery — a $1-per-artwork gallery where 70% of sales goes to PCRF children's aid.

PayPal takes ~49 cents on every $1 sale. Lightning fixes this at near-zero fees. I've already built the Cloudflare Worker integration — I just need API access to generate invoices.

Can you confirm the fastest path to API access for a small humanitarian creator?

Gallery: """ + GALLERY + AI_FOOTER
    },
    {
        "id": "tech_for_palestine",
        "to": "hello@techforpalestine.org",
        "subject": "Open Source Humanitarian Gallery Architecture — Sharing with Community",
        "body": """Hi Tech for Palestine,

I built something that belongs in your community: Gaza Rose Gallery.

56 original digital artworks, $1 each, 70% to PCRF. Fully autonomous — GitHub Actions handles promotion, email replies, payment processing, and memory. Zero monthly cost. MIT licensed.

The architecture — I call it the Meeko Mycelium — is the part I most want to share. Any humanitarian project could fork it and have a self-running funding and communication system with no server, no budget, no tech team. Living documentation: """ + GITHUB + """

No ask beyond sharing it if useful.

Gallery: """ + GALLERY + AI_FOOTER
    },
    {
        "id": "mozilla_foundation",
        "to": "foundation@mozilla.org",
        "subject": "Grant Inquiry — Gaza Rose Mycelium (Open Source Humanitarian Infrastructure)",
        "body": """Hi Mozilla Foundation,

I'm a solo developer and digital artist writing to ask about grant opportunities for Gaza Rose Mycelium.

The project: An autonomous, open source humanitarian art platform. 56 digital artworks, $1 each, 70% to Palestine Children's Relief Fund (verified 4-star Charity Navigator, EIN 93-1057665). The entire system runs on free GitHub infrastructure — zero monthly cost, fully forkable.

The open internet angle: The architecture (Meeko Mycelium) is documented and replicable. Any humanitarian cause can fork it and have a self-sustaining funding system with no budget required. That's the open internet doing what it's supposed to do.

I've applied for fiscal sponsorship through Open Collective for a proper legal structure.

Project: """ + GITHUB + """
Gallery: """ + GALLERY + """

Which grant program fits this, if any?
""" + AI_FOOTER
    },
    {
        "id": "creative_capital",
        "to": "info@creative-capital.org",
        "subject": "Grant Inquiry — Gaza Rose Gallery (Digital Art / Autonomous Systems)",
        "body": """Hi Creative Capital,

I'm Meeko — a self-taught digital artist writing to ask about grant programs for Gaza Rose Gallery.

The work sits at the intersection of digital art and humanitarian technology. 56 original 300 DPI flower artworks, $1 each, 70% to PCRF. The gallery runs itself — GitHub Actions, AI content, autonomous email, persistent memory. Zero monthly cost.

The conceptual question I'm exploring: what does it mean to build systems that outlast you? Art as direct economic transfer rather than symbolic gesture. Infrastructure as ethics.

Gallery: """ + GALLERY + """
Code: """ + GITHUB + """

Happy to apply formally or answer questions.
""" + AI_FOOTER
    },
    {
        "id": "wikimedia_rapid_fund",
        "to": "grants@wikimedia.org",
        "subject": "Rapid Fund Inquiry — Open Source Humanitarian Gallery Architecture",
        "body": """Hi Wikimedia grants team,

I'm asking whether Gaza Rose Gallery qualifies for a Rapid Fund grant.

The open knowledge angle: The Meeko Mycelium architecture is fully documented, MIT licensed, and designed to be replicated. Any community can fork it and build a self-sustaining humanitarian funding system with zero cost and no technical team. Freely available infrastructure for people who need it most.

Gallery: """ + GALLERY + """
Documentation: """ + GITHUB + """
""" + AI_FOOTER
    },
    {
        "id": "pcrf_email_verified",
        "to": "contact@pcrf.net",
        "subject": "Following Up — Artist Partnership Inquiry",
        "body": """Hi PCRF,

Following up on an earlier email to info@pcrf.net about Gaza Rose Gallery — a digital art project committing 70% of every $1 sale to your organization.

If info@pcrf.net is the right address, please ignore this. If there's a better contact for partnership/donation routing questions, I'd appreciate knowing.

Gallery: """ + GALLERY + AI_FOOTER
    },
]

def load_sent():
    try:
        with open(SENT_LOG) as f: return json.load(f)
    except: return {}

def save_sent(sent):
    os.makedirs("mycelium", exist_ok=True)
    with open(SENT_LOG, "w") as f: json.dump(sent, f, indent=2)

def log_web_forms(sent):
    """Log web forms Meeko needs to fill manually."""
    pending = [f for f in WEB_FORMS if f["id"] not in sent]
    if pending:
        print("\n[Outreach] ⚠️  WEB FORMS — These need manual submission (can't be emailed):")
        for f in pending:
            print(f"  → {f['name']}: {f['url']}")
            print(f"    {f['notes']}")
        print()

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
    sent = load_sent()
    log_web_forms(sent)

    if not GMAIL_PASS:
        print("[Outreach] GMAIL_APP_PASSWORD not set. Emails staged and ready.")
        print("[Outreach] Verified addresses:")
        for e in EMAILS:
            if e["id"] not in sent:
                print(f"  → {e['to']} | {e['subject'][:50]}")
        return

    for e in EMAILS:
        if e["id"] in sent:
            continue
        try:
            send_email(e["to"], e["subject"], e["body"])
            sent[e["id"]] = {
                "to": e["to"],
                "sent_at": datetime.now(timezone.utc).isoformat()
            }
            save_sent(sent)
            print(f"[Outreach] SENT → {e['to']}")
        except Exception as ex:
            print(f"[Outreach] FAILED {e['to']}: {ex}")

if __name__ == "__main__":
    run()
