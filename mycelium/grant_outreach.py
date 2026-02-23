#!/usr/bin/env python3
"""
🌱 GRANT OUTREACH — Meeko Mycelium
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Automatically identifies and prepares applications for:
  • Arts grants (individual artist awards)
  • Tech-for-good fellowships
  • Open source funding (GitHub Sponsors, OpenCollective, NLnet)
  • Humanitarian tech grants
  • Palestinian solidarity / human rights arts funding
  • Solarpunk / mutual aid funding

For each grant: generates a customized application package
using the identity vault, system capabilities, and mission statement.

Usage:
  python grant_outreach.py              # scan + report all opportunities
  python grant_outreach.py --apply NAME # generate application for specific grant
  python grant_outreach.py --list       # list all grant programs tracked
"""

import os
import json
import datetime
import argparse
from pathlib import Path

# Colors
class C:
    G='[92m'; Y='[93m'; CY='[96m'; B='[1m'; D='[2m'; X='[0m'

REPO_ROOT = Path(__file__).parent.parent
GRANT_DATA = REPO_ROOT / 'data' / 'grants'

# ─────────────────────────────────────────────
GRANT DATABASE
# This is the system's knowledge of available funding.
# When email layer is active, it will monitor for new opportunities.
# ─────────────────────────────────────────────
GRANTS = [
    {
        "name": "NLnet Foundation",
        "url": "https://nlnet.nl/propose",
        "amount": "5,000–200,000 EUR",
        "cycle": "quarterly",
        "next_deadline": "2026-04-01",
        "type": "open_source_tech",
        "match": ["open source", "privacy", "decentralized", "free software"],
        "description": "Funds projects that contribute to open internet and privacy-preserving tech.",
        "fit_score": 95,
    },
    {
        "name": "GitHub Sponsors",
        "url": "https://github.com/sponsors",
        "amount": "recurring",
        "cycle": "always_open",
        "next_deadline": "NOW",
        "type": "open_source_funding",
        "match": ["open source", "github"],
        "description": "Direct sponsorship from GitHub users for open source work.",
        "fit_score": 99,
        "action": "Enable GitHub Sponsors on meekotharaccoon-cell account",
    },
    {
        "name": "Open Collective",
        "url": "https://opencollective.com",
        "amount": "recurring + project",
        "cycle": "always_open",
        "next_deadline": "NOW",
        "type": "community_funding",
        "match": ["open source", "community", "collective"],
        "description": "Transparent fundraising for open source projects and communities.",
        "fit_score": 90,
    },
    {
        "name": "Shuttleworth Foundation",
        "url": "https://www.shuttleworthfoundation.org",
        "amount": "250,000+ USD",
        "cycle": "biannual",
        "next_deadline": "2026-03-01",
        "type": "fellowship",
        "match": ["open", "social change", "technology", "education"],
        "description": "Fellowships for people with ideas for social change via openness.",
        "fit_score": 85,
    },
    {
        "name": "Creative Capital",
        "url": "https://creative-capital.org/apply",
        "amount": "50,000 USD",
        "cycle": "annual",
        "next_deadline": "2026-06-01",
        "type": "arts_grant",
        "match": ["artist", "visual art", "media art", "technology"],
        "description": "Supports artists working in all disciplines.",
        "fit_score": 80,
    },
    {
        "name": "Knight Foundation",
        "url": "https://knightfoundation.org/prototype-fund",
        "amount": "up to 35,000 USD",
        "cycle": "rolling",
        "next_deadline": "ROLLING",
        "type": "media_tech",
        "match": ["journalism", "technology", "democracy", "community"],
        "description": "Supports informed and engaged communities.",
        "fit_score": 75,
    },
    {
        "name": "Mozilla Foundation Grants",
        "url": "https://foundation.mozilla.org/en/what-we-fund",
        "amount": "varies",
        "cycle": "rolling",
        "next_deadline": "ROLLING",
        "type": "internet_health",
        "match": ["open internet", "privacy", "AI", "digital rights"],
        "description": "Funds projects promoting a healthy internet.",
        "fit_score": 88,
    },
    {
        "name": "Alchemy Artist Residency",
        "url": "https://alchemy-studio.net",
        "amount": "stipend + studio",
        "cycle": "annual",
        "next_deadline": "RESEARCH_NEEDED",
        "type": "residency",
        "match": ["artist", "technology", "community"],
        "description": "Artist residency focused on technology and community.",
        "fit_score": 70,
    },
]

def generate_application(grant, identity=None):
    """Generate a customized application package for a grant"""
    if not identity:
        # Try to load from vault
        vault_config = Path.home() / '.meeko_vault' / 'vault.json'
        if vault_config.exists():
            identity = json.loads(vault_config.read_text())
        else:
            identity = {
                'name': 'Meeko', 'email': 'meekotharaccoon@gmail.com',
                'website': 'https://meekotharaccoon-cell.github.io/meeko-nerve-center',
                'github': 'meekotharaccoon-cell',
                'mission': 'Ethical autonomous systems. Revenue to PCRF.',
                'artist_statement': 'Visual artist and systems builder.'
            }

    today = datetime.date.today().strftime("%B %d, %Y")
    app = f"""GRANT APPLICATION PACKAGE
Grant: {grant['name']}
URL: {grant['url']}
Amount: {grant['amount']}
Deadline: {grant['next_deadline']}
Generated: {today}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
APPLICANT INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {identity.get('name')}
Email: {identity.get('email')}
Website: {identity.get('website')}
GitHub: github.com/{identity.get('github')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROJECT DESCRIPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Project: Meeko Mycelium — Ethical Autonomous Systems

Overview:
Meeko Mycelium is an open-source autonomous system organism that builds
free ethical infrastructure for communities that lack access to expensive
tools. It self-replicates through GitHub forks, routes 70% of revenue to
the Palestinian Children's Relief Fund, and ships legal tools (TCPA, FDCPA,
FOIA) that help ordinary people protect themselves from corporate and
government overreach.

What It Does:
  • Self-replicating: Every fork is a new autonomous node in the network
  • Legal warfare: Browser-based tools for TCPA, FDCPA, FOIA demands
  • Space bridge: Connects to ISS, NASA, NOAA, Mars rovers (free public APIs)
  • Network node: Bluetooth, WiFi, WebSocket, MQTT hub
  • Revenue layer: Digital goods, art sales, grants → 70% to PCRF
  • Zero cost: Runs entirely on free infrastructure (GitHub Actions)
  • Ethics baked in: AGPL-3.0 + Ethical Use Rider travels with every fork

Technology Stack:
  Python · JavaScript · GitHub Actions · Ollama (local AI, no API costs)
  ChromaDB · SQLite · NASA APIs · NOAA APIs · Open Notify
  All free. All open. All permission-first.

Impact:
  • Legal tools protecting people from robocalls, debt collectors, government opacity
  • Art revenue routing directly to children affected by war
  • Open source infrastructure that anyone can fork and redirect toward any cause
  • Model for $0/month autonomous systems that communities can own

Mission Alignment with {grant['name']}:
{grant['description']}
This project directly advances these goals through open-source autonomous
systems that empower communities, protect rights, and route money to causes
that matter.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LINKS + EVIDENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Main repo: https://github.com/meekotharaccoon-cell/meeko-nerve-center
Live demo: https://meekotharaccoon-cell.github.io/meeko-nerve-center
Gallery: https://meekotharaccoon-cell.github.io/gaza-rose-gallery
Legal tools: https://meekotharaccoon-cell.github.io/meeko-nerve-center/proliferator.html
License: AGPL-3.0 + Ethical Use Rider

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARTIST STATEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{identity.get('artist_statement')}

---
Generated by Meeko Mycelium Grant Outreach
{today}
"""
    return app

def main():
    print(f"\n{C.G}{C.B}  🌱 GRANT OUTREACH SCANNER{C.X}\n")

    p = argparse.ArgumentParser()
    p.add_argument('--list',   action='store_true')
    p.add_argument('--apply',  metavar='NAME')
    args = p.parse_args()

    if args.list or not args.apply:
        print(f"  {C.B}Grant opportunities (sorted by fit):{C.X}\n")
        sorted_grants = sorted(GRANTS, key=lambda g: g['fit_score'], reverse=True)
        for g in sorted_grants:
            score_color = C.G if g['fit_score'] >= 85 else (C.Y if g['fit_score'] >= 70 else C.D)
            print(f"  {score_color}●{C.X} {C.B}{g['name']}{C.X} — {g['amount']}· Deadline: {g['next_deadline']}")
            print(f"    {C.D}{g['description']}{C.X}")
            if g.get('action'):
                print(f"    {C.CY}ACTION NEEDED: {g['action']}{C.X}")
            print()

        # Save scan results
        GRANT_DATA.mkdir(parents=True, exist_ok=True)
        scan_path = GRANT_DATA / f"scan_{datetime.date.today().isoformat()}.json"
        scan_path.write_text(json.dumps(GRANTS, indent=2))
        print(f"  {C.G}✓{C.X} Scan saved: {scan_path}")
        print(f"  {C.D}Run with --apply \"Grant Name\" to generate application package{C.X}")

    if args.apply:
        matching = [g for g in GRANTS if args.apply.lower() in g['name'].lower()]
        if not matching:
            print(f"  {C.Y}No grant found matching: {args.apply}{C.X}")
            return
        grant = matching[0]
        app = generate_application(grant)
        GRANT_DATA.mkdir(parents=True, exist_ok=True)
        app_path = GRANT_DATA / f"application_{grant['name'].replace(' ','_')}_{datetime.date.today().isoformat()}.txt"
        app_path.write_text(app)
        print(app)
        print(f"\n  {C.G}✓{C.X} Application saved: {app_path}")

if __name__ == '__main__':
    main()
