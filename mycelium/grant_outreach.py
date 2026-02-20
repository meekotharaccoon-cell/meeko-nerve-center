#!/usr/bin/env python3
"""
GRANT OUTREACH EMAILS
Verified grant opportunities for humanitarian tech / open source / art for good.
All fully composed. Sent once per ID. AI-replied when responses come in.
"""
import smtplib, json, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

GMAIL_USER = "mickowood86@gmail.com"
GMAIL_PASS = os.environ.get("GMAIL_APP_PASSWORD", "")
GALLERY    = "https://meekotharaccoon-cell.github.io/gaza-rose-gallery"
GITHUB     = "https://github.com/meekotharaccoon-cell"
SENT_LOG   = "mycelium/sent_grants.json"

GRANTS = [
    {
        "id": "mozilla_foundation",
        "to": "foundation@mozilla.org",
        "subject": "Mozilla Foundation Grant Inquiry \u2014 Open Source Humanitarian Art System",
        "body": """Hi Mozilla Foundation team,

I'm a solo developer and artist and I built Gaza Rose Gallery \u2014 a fully open source, serverless humanitarian art system that runs entirely on free infrastructure.

Here's what it does: 56 original digital artworks, $1 each, 70% of every sale routed to the Palestine Children's Relief Fund (4-star Charity Navigator, 12 consecutive years). The system manages itself through GitHub Actions \u2014 promotion, health checks, email responses, AI-generated content, payment processing, and persistent memory. Zero monthly cost. Zero corporate backing. Total operating cost: $0.

I'm writing because the architecture I built \u2014 which I call the Meeko Mycelium \u2014 is fully forkable and replicable. Any humanitarian cause could have a self-sustaining, autonomous fundraising and communication system without servers, without a budget, without technical expertise beyond a few hours of setup.

Mozilla's open internet mission and this project are aligned: decentralized, free, open source infrastructure doing something real for people in crisis.

I'd like to inquire about whether this project qualifies for any Mozilla Foundation grant or fellowship program \u2014 technology, open internet, or humanitarian categories.

Project: """ + GITHUB + """
Gallery: """ + GALLERY + """

Thank you for everything Mozilla does,
Meeko
mickowood86@gmail.com"""
    },
    {
        "id": "creative_capital",
        "to": "info@creative-capital.org",
        "subject": "Grant Inquiry \u2014 Gaza Rose Gallery (Digital Art / Humanitarian Tech)",
        "body": """Hi Creative Capital,

I'm a self-taught digital artist and my name is Meeko. I built Gaza Rose Gallery \u2014 an autonomous gallery of 56 original 300 DPI floral artworks where every $1 purchase sends 70% directly to the Palestine Children's Relief Fund.

The project lives at the intersection of digital art and humanitarian technology. The gallery runs itself: it promotes, monitors, responds to emails, and processes payments without human intervention. It was built to prove that one artist with free tools and a clear mission can create something that outlasts any single act of generosity.

I'm inquiring about whether Gaza Rose Gallery qualifies for any Creative Capital grant programs \u2014 digital media, new media, or interdisciplinary categories.

The gallery: """ + GALLERY + """
The code: """ + GITHUB + """

I'm happy to apply formally or answer any questions.

Meeko
mickowood86@gmail.com"""
    },
    {
        "id": "knight_foundation",
        "to": "web@knightfoundation.org",
        "subject": "Prototype Fund Inquiry \u2014 Autonomous Humanitarian Art Infrastructure",
        "body": """Hi Knight Foundation,

I built something I think fits your Prototype Fund: Gaza Rose Gallery.

It's a fully autonomous, open source digital art platform where 70% of every $1 sale goes directly to verified humanitarian organizations. The entire system \u2014 promotion, payment processing, email communication, AI content generation, system memory \u2014 runs on free GitHub infrastructure with zero monthly cost.

What makes it prototype-worthy: The architecture is a replicable pattern. Any artist, community, or cause could fork it and have a self-sustaining humanitarian funding system with no backend, no server costs, and no technical team. The documentation is part of the project.

This is directly aligned with Knight's interest in how technology can serve communities and open up information. The community here is everyone who can't afford a $10 donation but can spend $1 on a piece of art knowing it directly reaches a child in Gaza, Sudan, or Congo.

Project code: """ + GITHUB + """
Live gallery: """ + GALLERY + """

I'd love to understand if this fits a Prototype Fund application.

Meeko
mickowood86@gmail.com"""
    },
    {
        "id": "eyebeam",
        "to": "info@eyebeam.org",
        "subject": "Fellowship Inquiry \u2014 Gaza Rose Gallery (Art + Tech for Humanitarian Impact)",
        "body": """Hi Eyebeam,

I'm Meeko \u2014 a self-taught digital artist and developer. I built Gaza Rose Gallery and I think what I'm doing fits what Eyebeam supports.

Gaza Rose Gallery is 56 original digital flower artworks. $1 each. 70% to PCRF (Palestine Children's Relief Fund, verified 4-star Charity Navigator). The whole system runs autonomously on free GitHub infrastructure \u2014 I built something I call the Meeko Mycelium, an AI-powered organism that promotes, monitors, responds, and remembers without any human keeping it alive.

What I'm interested in exploring with support from Eyebeam: the ethics of autonomous humanitarian systems, what it means to build infrastructure that runs without you, and how art can be a direct economic transfer rather than a symbolic gesture.

I'm inquiring about fellowship or residency programs that might support this work.

Gallery: """ + GALLERY + """
Code (open source): """ + GITHUB + """

Thank you,
Meeko
mickowood86@gmail.com"""
    },
    {
        "id": "rhizome",
        "to": "info@rhizome.org",
        "subject": "Microgrant Inquiry \u2014 Gaza Rose Gallery (Net Art / Humanitarian Tech)",
        "body": """Hi Rhizome,

I'm Meeko, a digital artist. I built Gaza Rose Gallery \u2014 56 original 300 DPI flower artworks, $1 each, 70% of every sale to the Palestine Children's Relief Fund. The gallery runs autonomously on GitHub Pages and GitHub Actions. No server. No monthly cost. Open source.

This is net art that does something. Not commentary \u2014 actual economic transfer. A buyer pays $1, downloads a 300 DPI artwork, and 70 cents reaches pediatric medical care in Gaza. The system sends the emails, updates its memory, monitors its own health, and generates content \u2014 all without me.

I'm curious whether this fits any Rhizome microgrant or commission program.

Gallery: """ + GALLERY + """
Code: """ + GITHUB + """

Meeko
mickowood86@gmail.com"""
    },
    {
        "id": "wikimedia_foundation",
        "to": "grants@wikimedia.org",
        "subject": "Rapid Fund Inquiry \u2014 Open Source Humanitarian Gallery Architecture",
        "body": """Hi Wikimedia Foundation grants team,

I'm inquiring about whether my project qualifies for a Rapid Fund grant under the open knowledge or technology categories.

I built Gaza Rose Gallery \u2014 a fully open source, autonomous humanitarian art platform. 56 digital artworks, $1 each, 70% to verified charities (Palestine Children's Relief Fund, 4-star Charity Navigator). The system operates itself on free GitHub infrastructure.

The open knowledge angle: the architecture \u2014 which I've named Meeko Mycelium \u2014 is thoroughly documented and designed to be replicated. Anyone running a humanitarian cause could use this pattern to build a self-sustaining, AI-assisted fundraising and communication system with zero cost. The documentation, code, and architecture are all public.

This is the kind of freely available tool that lets communities help themselves without needing a tech team or a budget.

Gallery: """ + GALLERY + """
Code: """ + GITHUB + """

Thank you,
Meeko
mickowood86@gmail.com"""
    }
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
        print("[Grants] GMAIL_APP_PASSWORD not set. All grant emails staged:")
        for g in GRANTS:
            print(f"  -> {g['to']} | {g['subject']}")
        return
    sent = load_sent()
    for g in GRANTS:
        if g["id"] in sent:
            print(f"[Grants] Already sent: {g['id']}")
            continue
        try:
            send_email(g["to"], g["subject"], g["body"])
            sent[g["id"]] = {"to": g["to"], "sent_at": datetime.now(timezone.utc).isoformat()}
            save_sent(sent)
            print(f"[Grants] SENT -> {g['to']}")
        except Exception as ex:
            print(f"[Grants] FAILED {g['to']}: {ex}")

if __name__ == "__main__":
    run()
