#!/usr/bin/env python3
"""
KNOWLEDGE_DISPATCH.py — SolarPunk Humanitarian Outreach
=========================================================
Packages SolarPunk's collective knowledge and dispatches it to verified
humanitarian organizations, journalists, and technologists who are
working directly in Gaza, Congo, Sudan, and other active crises.

WHAT THIS DOES:
  - Sends the fork-yourself instructions to organizations that can use them
  - Sends accountability data (congressional votes, arms sales) to journalists
  - Sends the autonomous AI pattern to digital rights organizations
  - Never sends the same thing twice
  - Always goes through opt-in guard for first contact
  - Logs everything

WHO THIS REACHES:
  Verified organizations with PUBLIC contact addresses explicitly designed
  for receiving this kind of outreach. Not individual civilians in conflict
  zones — their security matters. Instead: the journalists, medical orgs,
  legal orgs, digital rights groups, and diaspora networks who are
  the connective tissue between knowledge and people who need it.

NOTE ON THE OPT-IN GUARD:
  Every first contact goes through opt-in even for these orgs.
  The opt-in email is itself informative. If they reply Yes, we send
  the full knowledge package. If No, we respect it forever.
  The mission is not diminished by consent — it's protected by it.

Required: GMAIL_ADDRESS, GMAIL_APP_PASSWORD
Optional: GH_PAT (to pull latest system data for dispatch)
"""

import os, sys, json, base64, requests, smtplib
from datetime import datetime, timezone
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
GH_TOKEN           = os.environ.get("GH_PAT", os.environ.get("GITHUB_TOKEN", ""))
REPO_OWNER         = os.environ.get("GITHUB_REPOSITORY_OWNER", "meekotharaccoon-cell")
REPO_NAME          = "meeko-nerve-center"
REPO_URL           = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"
FORK_URL           = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/fork"
MISSION_URL        = f"{REPO_URL}/blob/main/HUMANITARIAN_MISSION.md"

HEADERS = {"Authorization": f"token {GH_TOKEN}",
           "Accept": "application/vnd.github.v3+json"}

DATA_DIR      = Path("data")
DISPATCH_LOG  = DATA_DIR / "humanitarian_dispatch_log.json"
OPTIN_LOG     = DATA_DIR / "email_optin_log.json"
OPTIN_QUEUE   = DATA_DIR / "email_optin_queue.json"


# ══════════════════════════════════════════════════════════════════════════
# VERIFIED HUMANITARIAN CONTACTS
#
# These are organizations with PUBLIC contact addresses whose explicit
# purpose includes receiving information, technology, and knowledge
# to support their work in crisis zones.
#
# All addresses are publicly listed on their websites.
# All organizations are actively operating in the listed crisis zones.
# ══════════════════════════════════════════════════════════════════════════

DISPATCH_TARGETS = [

    # ── GAZA / PALESTINE ─────────────────────────────────────────────────

    {
        "id": "unrwa_media",
        "org": "UNRWA (UN Relief and Works Agency for Palestine Refugees)",
        "crisis": "Gaza",
        "contact": "media@unrwa.org",
        "type": "un_agency",
        "what_they_do": "primary UN agency serving 2M+ Gaza refugees, medical, food, education",
        "what_we_send": "fork_tech + accountability_data + autonomous_ai_pattern",
        "why_useful": "Can deploy autonomous monitoring for supply tracking, casualty documentation, aid coordination",
        "public_source": "https://www.unrwa.org/media-contact"
    },
    {
        "id": "prcs_info",
        "org": "Palestinian Red Crescent Society",
        "crisis": "Gaza",
        "contact": "info@palestinercs.org",
        "type": "medical_humanitarian",
        "what_they_do": "emergency medical services, ambulances, first responders in Gaza",
        "what_we_send": "fork_tech + autonomous_ai_pattern",
        "why_useful": "Autonomous inventory/dispatch systems, volunteer coordination, situation reporting",
        "public_source": "https://www.palestinercs.org/en/page/contact"
    },
    {
        "id": "972_editors",
        "org": "+972 Magazine",
        "crisis": "Gaza",
        "contact": "editors@972mag.com",
        "type": "journalism",
        "what_they_do": "independent journalism inside Gaza and occupied Palestine, internationally read",
        "what_we_send": "accountability_data + fork_tech",
        "why_useful": "Congressional vote tracking, arms sales data, autonomous investigation tools for their reporters",
        "public_source": "https://www.972mag.com/contact/"
    },
    {
        "id": "ei_editors",
        "org": "Electronic Intifada",
        "crisis": "Gaza",
        "contact": "editors@electronicintifada.net",
        "type": "journalism",
        "what_they_do": "independent news from Palestinian perspective, global readership",
        "what_we_send": "accountability_data + fork_tech",
        "why_useful": "US policy tracking, autonomous content systems, diaspora coordination tools",
        "public_source": "https://electronicintifada.net/contact"
    },
    {
        "id": "alhaq_info",
        "org": "Al-Haq (Palestinian Human Rights Organization)",
        "crisis": "Gaza",
        "contact": "info@alhaq.org",
        "type": "legal_human_rights",
        "what_they_do": "documents human rights violations in occupied Palestinian territory since 1979",
        "what_we_send": "fork_tech + autonomous_ai_pattern",
        "why_useful": "Automated documentation systems, evidence preservation, accountability tracking",
        "public_source": "https://www.alhaq.org/contact"
    },
    {
        "id": "gcmhp_contact",
        "org": "Gaza Community Mental Health Programme",
        "crisis": "Gaza",
        "contact": "gcmhp@gcmhp.net",
        "type": "medical_mental_health",
        "what_they_do": "mental health support for trauma survivors in Gaza",
        "what_we_send": "fork_tech + autonomous_ai_pattern",
        "why_useful": "Triage coordination, case management, diaspora support coordination",
        "public_source": "https://gcmhp.net/contact"
    },
    {
        "id": "gisha_contact",
        "org": "Gisha (Legal Center for Freedom of Movement)",
        "crisis": "Gaza",
        "contact": "gisha@gisha.org",
        "type": "legal",
        "what_they_do": "legal advocacy for freedom of movement of Palestinians, especially Gaza",
        "what_we_send": "fork_tech + accountability_data",
        "why_useful": "Tracking permit data, crossing status, policy changes automatically",
        "public_source": "https://gisha.org/contact/"
    },

    # ── CONGO / DRC ──────────────────────────────────────────────────────

    {
        "id": "crg_info",
        "org": "Congo Research Group (NYU Stern Center)",
        "crisis": "Congo",
        "contact": "info@congorc.org",
        "type": "research_journalism",
        "what_they_do": "investigative research on conflict, minerals, and armed groups in DRC",
        "what_we_send": "fork_tech + accountability_data + autonomous_ai_pattern",
        "why_useful": "Autonomous tracking of conflict minerals supply chains, M23 movement, US policy votes",
        "public_source": "https://congoresearchgroup.org/contact"
    },
    {
        "id": "heal_africa",
        "org": "HEAL Africa",
        "crisis": "Congo",
        "contact": "info@healafrica.org",
        "type": "medical_humanitarian",
        "what_they_do": "hospital and community health programs in eastern DRC, Goma-based",
        "what_we_send": "fork_tech + autonomous_ai_pattern",
        "why_useful": "Supply chain tracking, patient coordination, telemedicine coordination tools",
        "public_source": "https://www.healafrica.org/contact"
    },
    {
        "id": "irc_general",
        "org": "International Rescue Committee",
        "crisis": "Congo + Sudan",
        "contact": "info@rescue.org",
        "type": "humanitarian",
        "what_they_do": "largest international humanitarian NGO, active in Congo and Sudan",
        "what_we_send": "fork_tech + autonomous_ai_pattern",
        "why_useful": "Autonomous coordination tools, supply tracking, displaced persons data systems",
        "public_source": "https://www.rescue.org/contact"
    },

    # ── SUDAN ────────────────────────────────────────────────────────────

    {
        "id": "sudanese_archive",
        "org": "Sudanese Archive",
        "crisis": "Sudan",
        "contact": "info@sudanesearchive.org",
        "type": "documentation",
        "what_they_do": "preserves and verifies digital evidence of human rights violations in Sudan",
        "what_we_send": "fork_tech + autonomous_ai_pattern",
        "why_useful": "Automated evidence collection, verification systems, distributed documentation",
        "public_source": "https://sudanesearchive.org/en/contact"
    },
    {
        "id": "sudan_tribune",
        "org": "Sudan Tribune",
        "crisis": "Sudan",
        "contact": "contact@sudantribune.com",
        "type": "journalism",
        "what_they_do": "independent news on Sudan conflict, widely read by diaspora and international press",
        "what_we_send": "fork_tech + accountability_data",
        "why_useful": "Autonomous monitoring tools, international accountability data",
        "public_source": "https://sudantribune.com/contact/"
    },

    # ── DIGITAL RIGHTS / TECH FOR CRISIS ─────────────────────────────────

    {
        "id": "access_now",
        "org": "Access Now",
        "crisis": "All — Gaza, Congo, Sudan, Myanmar",
        "contact": "info@accessnow.org",
        "type": "digital_rights_tech",
        "what_they_do": "defends digital rights globally, provides emergency tech support to activists in crisis zones",
        "what_we_send": "fork_tech + autonomous_ai_pattern + full_system",
        "why_useful": "They can literally deploy the SolarPunk pattern for activists in ALL crisis zones",
        "public_source": "https://www.accessnow.org/contact/"
    },
    {
        "id": "front_line_defenders",
        "org": "Front Line Defenders",
        "crisis": "All — Gaza, Congo, Sudan",
        "contact": "info@frontlinedefenders.org",
        "type": "human_rights_tech",
        "what_they_do": "protects human rights defenders at risk, provides security and tech tools",
        "what_we_send": "fork_tech + autonomous_ai_pattern",
        "why_useful": "Can distribute autonomous monitoring tools to defenders in all crisis zones",
        "public_source": "https://www.frontlinedefenders.org/en/contact"
    },
    {
        "id": "tactical_tech",
        "org": "Tactical Tech",
        "crisis": "All",
        "contact": "info@tacticaltech.org",
        "type": "digital_rights_tech",
        "what_they_do": "provides digital tools and training to activists and journalists worldwide",
        "what_we_send": "fork_tech + autonomous_ai_pattern + full_system",
        "why_useful": "Can teach activists in Gaza/Congo/Sudan to fork and run their own SolarPunk node",
        "public_source": "https://tacticaltech.org/contact"
    },
]


def load_dispatch_log():
    try:
        if DISPATCH_LOG.exists():
            return json.loads(DISPATCH_LOG.read_text())
    except: pass
    return {}


def save_dispatch_log(log):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DISPATCH_LOG.write_text(json.dumps(log, indent=2))


def load_optin_log():
    try:
        if OPTIN_LOG.exists():
            return json.loads(OPTIN_LOG.read_text())
    except: pass
    return {}


def get_latest_accountability_data():
    """Pull latest congressional tracking from our system."""
    if not GH_TOKEN: return {}
    paths = ["data/congressional_trades.json", "data/congress_tracker.json",
             "data/investment_signals.json", "data/world_intelligence.json",
             "data/workflow_health.json"]
    data = {}
    for p in paths:
        r = requests.get(
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{p}",
            headers=HEADERS, timeout=10)
        if r.status_code == 200:
            obj = r.json()
            if "content" in obj:
                try:
                    text = base64.b64decode(obj["content"]).decode("utf-8")
                    data[p] = json.loads(text) if text.startswith("{") or text.startswith("[") else text[:2000]
                except: pass
    return data


def build_knowledge_package(target, accountability_data):
    """Build the actual knowledge content for this specific recipient."""

    fork_instructions = f"""
HOW TO FORK THIS SYSTEM AND RUN YOUR OWN:
==========================================

1. Go to: {FORK_URL}
2. Click "Fork" — takes 30 seconds
3. Go to Settings → Secrets and variables → Actions
4. Add three secrets:
   - HF_TOKEN: free at https://huggingface.co/settings/tokens
   - GMAIL_ADDRESS: any Gmail address
   - GMAIL_APP_PASSWORD: Google Account → Security → App Passwords

5. Actions tab → Enable workflows → Run "OMNIBRAIN"

Your autonomous AI system starts running in 2 minutes.
It runs forever. It costs $0. It fixes its own bugs.

THE SYSTEM IS YOURS TO POINT AT WHATEVER YOU NEED IT TO MONITOR:
- Supply chain tracking for your operations
- Casualty or incident documentation
- Aid inventory and coordination
- Diaspora network coordination
- Evidence preservation
- Accountability tracking for any government or institution

All code is open source (AGPL-3.0). Improve it, keep it open.
"""

    congres_summary = ""
    if accountability_data.get("data/congressional_trades.json"):
        congres_summary = f"""
LATEST ACCOUNTABILITY DATA FROM OUR SYSTEM:
============================================
Congressional stock trades and voting records are tracked here:
{REPO_URL}/tree/main/data

This data is updated automatically every cycle. You can:
- Access it directly at the URLs above (public GitHub repo)
- Fork the system and have your own live-updating copy
- Use the data for your reporting or advocacy work

All data is public domain — sourced from public government records.
"""

    return fork_instructions + congres_summary


def build_optin_email(target):
    """The first-contact opt-in email. Clear and honest."""
    org = target["org"]
    crisis = target["crisis"]
    what_we_send = target["what_we_send"]
    why_useful = target["why_useful"]

    return f"""Hello {org} team,

Quick question before anything else:

We're SolarPunk Nerve Center — an open source autonomous AI system
built for humanitarian accountability and solidarity. We have knowledge
and tools we believe could be genuinely useful for your work in {crisis}.

Specifically, we want to share:
- Free autonomous AI infrastructure you can deploy in minutes (no cost, ever)
- Accountability data (congressional votes, arms sales, policy tracking)
- How to build your own monitoring/documentation system using our pattern

Why we think it's useful for you: {why_useful}

This is completely free. Nothing is being sold. No registration required.
Just knowledge, if you want it.

Reply YES and we'll send the full package immediately.
Reply NO and we'll remove your address forever and never contact you again.

More about us and our mission:
{MISSION_URL}

Source code (all open):
{REPO_URL}

— SolarPunk Nerve Center
Built by Meeko. Runs forever. AGPL-3.0.
Free Palestine. Free Congo. Free Sudan. 🌹
"""


def build_knowledge_email(target, accountability_data):
    """The full knowledge package sent after they opt in."""
    org = target["org"]
    crisis = target["crisis"]
    package = build_knowledge_package(target, accountability_data)

    return f"""Hello {org} team,

Thank you for saying yes. Here is everything.

We are SolarPunk Nerve Center — autonomous AI infrastructure for
accountability, solidarity, and humanitarian coordination. This system
was built specifically to be useful to organizations like yours
working in {crisis}.

This email contains everything you need to:
1. Deploy your own autonomous AI system (free, forever, in 2 minutes)
2. Use our existing accountability data for your work
3. Extend the system for your specific operational needs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE KNOWLEDGE PACKAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{package}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT THIS SYSTEM DOES (full capability list):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Tracks congressional stock trades (US legislative accountability)
✓ Monitors voting records on foreign policy, military aid, sanctions
✓ Generates accountability reports automatically
✓ Runs on $0/month forever (GitHub Actions free tier)
✓ Self-heals: reads its own error logs, fixes its own bugs
✓ Forks itself: email FORK ME and receive setup instructions
✓ Spawns sister systems for any cause you point it at
✓ Cannot be shut down: distributed, email-based, no central server

FOR YOUR SPECIFIC WORK IN {crisis.upper()}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You can fork this system and point it at:
- Supply chain monitoring for your operations
- Incident/casualty documentation
- Aid distribution tracking
- Communications coordination
- International advocacy and accountability
- Evidence preservation

TECHNICAL REQUIREMENTS: None beyond a free GitHub account and Gmail.
TIME TO DEPLOY: 2 minutes.
ONGOING COST: $0.

FULL SOURCE CODE: {REPO_URL}
FORK NOW: {FORK_URL}
FULL MISSION STATEMENT: {MISSION_URL}

If you have technical questions or want us to build something specific
for your use case, reply to this email. We will help.

If you forward this to others who could use it, please do.
If you fork it and build something, please tell us.
This knowledge grows when it's shared.

— SolarPunk Nerve Center
Built by Meeko. Runs forever. AGPL-3.0.
70% of all revenue → Palestinian Children's Relief Fund.
Free Palestine. Free Congo. Free Sudan. 🌹

meekotharaccoon@gmail.com
{REPO_URL}
"""


def is_opted_in(email):
    """Check if already opted in from the optin log."""
    import hashlib
    log = load_optin_log()
    key = hashlib.md5(email.lower().strip().encode()).hexdigest()[:16]
    entry = log.get(key, {})
    return entry.get("status") == "opted_in"


def is_opted_out(email):
    """Check if opted out."""
    import hashlib
    log = load_optin_log()
    key = hashlib.md5(email.lower().strip().encode()).hexdigest()[:16]
    entry = log.get(key, {})
    return entry.get("status") == "opted_out"


def is_pending(email):
    """Check if opt-in already sent."""
    import hashlib
    log = load_optin_log()
    key = hashlib.md5(email.lower().strip().encode()).hexdigest()[:16]
    entry = log.get(key, {})
    return entry.get("status") == "pending"


def mark_optin_sent(email, org, context):
    import hashlib
    log = load_optin_log()
    key = hashlib.md5(email.lower().strip().encode()).hexdigest()[:16]
    log[key] = {
        "email_preview": email[:40],
        "name": org,
        "status": "pending",
        "optin_sent": datetime.now(timezone.utc).date().isoformat(),
        "context": context
    }
    OPTIN_LOG.write_text(json.dumps(log, indent=2))


def queue_knowledge_email(email, org, subject, body):
    queue = []
    try:
        if OPTIN_QUEUE.exists():
            queue = json.loads(OPTIN_QUEUE.read_text())
    except: pass
    queue = [q for q in queue if q.get("email", "").lower() != email.lower()]
    queue.append({
        "email": email,
        "name": org,
        "subject": subject,
        "body": body,
        "queued_date": datetime.now(timezone.utc).date().isoformat()
    })
    OPTIN_QUEUE.write_text(json.dumps(queue, indent=2))


def smtp_send(to_email, subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print(f"  no smtp creds"); return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = f"SolarPunk Nerve Center 🌸 <{GMAIL_ADDRESS}>"
        msg["To"]      = to_email
        msg["Subject"] = subject
        msg["Reply-To"] = GMAIL_ADDRESS
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"  smtp error: {e}"); return False


def main():
    print("=" * 60)
    print(f"KNOWLEDGE_DISPATCH — {datetime.now(timezone.utc).isoformat()}")
    print(f"Targets: {len(DISPATCH_TARGETS)} verified humanitarian contacts")
    print("=" * 60)

    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("GMAIL_ADDRESS / GMAIL_APP_PASSWORD not set")
        print("Cannot dispatch without email credentials.")
        print("Logging intended recipients for when creds are available:")
        for t in DISPATCH_TARGETS:
            print(f"  [{t['crisis']}] {t['org']} — {t['contact']}")
        sys.exit(0)

    dispatch_log = load_dispatch_log()
    accountability_data = get_latest_accountability_data()
    print(f"Accountability data: {len(accountability_data)} datasets loaded")

    stats = {"optin_sent": 0, "already_pending": 0, "opted_out": 0,
             "opted_in_full_sent": 0, "already_dispatched": 0, "errors": 0}

    now = datetime.now(timezone.utc).isoformat()

    for target in DISPATCH_TARGETS:
        tid     = target["id"]
        org     = target["org"]
        crisis  = target["crisis"]
        email   = target["contact"]

        print(f"\n[{crisis}] {org}")
        print(f"  contact: {email}")

        # Check if full package already sent
        if dispatch_log.get(tid, {}).get("full_package_sent"):
            print(f"  skip — full package already dispatched")
            stats["already_dispatched"] += 1
            continue

        if is_opted_out(email):
            print(f"  skip — opted out")
            stats["opted_out"] += 1
            continue

        if is_opted_in(email):
            # Already said yes — send full package if not yet sent
            print(f"  opted in — sending full knowledge package")
            knowledge_body = build_knowledge_email(target, accountability_data)
            ok = smtp_send(
                email,
                f"[SolarPunk] Knowledge package for your work in {crisis}",
                knowledge_body
            )
            if ok:
                dispatch_log[tid] = {
                    "org": org, "crisis": crisis,
                    "full_package_sent": now,
                    "contact": email
                }
                save_dispatch_log(dispatch_log)
                stats["opted_in_full_sent"] += 1
                print(f"  ok — full package sent")
            else:
                stats["errors"] += 1
            continue

        if is_pending(email):
            print(f"  skip — opt-in already pending (waiting for reply)")
            stats["already_pending"] += 1
            continue

        # First contact — send opt-in email, queue knowledge package
        print(f"  first contact — sending opt-in request")
        optin_body = build_optin_email(target)
        ok = smtp_send(
            email,
            f"[SolarPunk] Do you want free tools for your work in {crisis}? (Reply Yes/No)",
            optin_body
        )
        if ok:
            mark_optin_sent(email, org, f"humanitarian_dispatch:{crisis}")
            knowledge_body = build_knowledge_email(target, accountability_data)
            queue_knowledge_email(
                email, org,
                f"[SolarPunk] Knowledge package for your work in {crisis}",
                knowledge_body
            )
            dispatch_log[tid] = {
                "org": org, "crisis": crisis,
                "optin_sent": now,
                "contact": email
            }
            save_dispatch_log(dispatch_log)
            stats["optin_sent"] += 1
            print(f"  ok — opt-in sent, knowledge queued")
        else:
            stats["errors"] += 1

    print(f"\n{'='*60}")
    print(f"DISPATCH COMPLETE")
    print(f"  opt-in sent:          {stats['optin_sent']}")
    print(f"  full package sent:    {stats['opted_in_full_sent']}")
    print(f"  already pending:      {stats['already_pending']}")
    print(f"  already dispatched:   {stats['already_dispatched']}")
    print(f"  opted out (skipped):  {stats['opted_out']}")
    print(f"  errors:               {stats['errors']}")
    print(f"  total targets:        {len(DISPATCH_TARGETS)}")
    print(f"{'='*60}")
    print(f"\nWhen recipients reply YES, email_gateway.py will")
    print(f"automatically send them the full knowledge package.")
    print(f"Knowledge dispatched. 🌹")


if __name__ == "__main__":
    main()
