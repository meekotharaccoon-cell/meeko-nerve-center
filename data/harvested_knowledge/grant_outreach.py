#!/usr/bin/env python3
"""
# GRANT OUTREACH - Meeko Mycelium
Automatically identifies and prepares applications for:
  - Arts grants (individual artist awards)
  - Tech-for-good fellowships
  - Open source funding (GitHub Sponsors, OpenCollective, NLnet)
  - Humanitarian tech grants
  - Palestinian solidarity / human rights arts funding
  - Solarpunk / mutual aid funding

Usage:
  python grant_outreach.py              # scan + report all opportunities
  python grant_outreach.py --apply NAME # generate application for specific grant
  python grant_outreach.py --list       # list all grant programs tracked
"""

import os, json, datetime, argparse
from pathlib import Path

class C:
    G='[92m'; Y='[93m'; CY='[96m'; B='[1m'; D='[2m'; X='[0m'

REPO_ROOT  = Path(__file__).parent.parent
GRANT_DATA = REPO_ROOT / 'data' / 'grants'

# GRANT DATABASE
# This is the system's knowledge of available funding.
# When email layer is active, it will monitor for new opportunities.
GRANTS = [
    {
        'name': 'NLnet Foundation',
        'url': 'https://nlnet.nl/propose',
        'amount': '5,000-200,000 EUR',
        'cycle': 'quarterly',
        'next_deadline': '2026-04-01',
        'type': 'open_source_tech',
        'match': ['open source', 'privacy', 'decentralized', 'free software'],
        'description': 'Funds projects that contribute to open internet and privacy-preserving tech.',
        'fit_score': 95,
    },
    {
        'name': 'GitHub Sponsors',
        'url': 'https://github.com/sponsors',
        'amount': 'recurring',
        'cycle': 'always_open',
        'next_deadline': 'NOW',
        'type': 'open_source_funding',
        'match': ['open source', 'github'],
        'description': 'Direct sponsorship from GitHub users for open source work.',
        'fit_score': 99,
        'action': 'Enable GitHub Sponsors on meekotharaccoon-cell account',
    },
    {
        'name': 'Open Collective',
        'url': 'https://opencollective.com',
        'amount': 'recurring + project',
        'cycle': 'always_open',
        'next_deadline': 'NOW',
        'type': 'community_funding',
        'match': ['open source', 'community', 'collective'],
        'description': 'Transparent fundraising for open source projects and communities.',
        'fit_score': 90,
    },
    {
        'name': 'Shuttleworth Foundation',
        'url': 'https://www.shuttleworthfoundation.org',
        'amount': '250,000+ USD',
        'cycle': 'biannual',
        'next_deadline': '2026-03-01',
        'type': 'fellowship',
        'match': ['open', 'social change', 'technology', 'education'],
        'description': 'Fellowships for people with ideas for social change via openness.',
        'fit_score': 85,
    },
    {
        'name': 'Creative Capital',
        'url': 'https://creative-capital.org/apply',
        'amount': '50,000 USD',
        'cycle': 'annual',
        'next_deadline': '2026-06-01',
        'type': 'arts_grant',
        'match': ['artist', 'visual art', 'media art', 'technology'],
        'description': 'Supports artists working in all disciplines.',
        'fit_score': 80,
    },
    {
        'name': 'Knight Foundation',
        'url': 'https://knightfoundation.org/prototype-fund',
        'amount': 'up to 35,000 USD',
        'cycle': 'rolling',
        'next_deadline': 'ROLLING',
        'type': 'media_tech',
        'match': ['journalism', 'technology', 'democracy', 'community'],
        'description': 'Supports informed and engaged communities.',
        'fit_score': 75,
    },
    {
        'name': 'Mozilla Foundation Grants',
        'url': 'https://foundation.mozilla.org/en/what-we-fund',
        'amount': 'varies',
        'cycle': 'rolling',
        'next_deadline': 'ROLLING',
        'type': 'internet_health',
        'match': ['open internet', 'privacy', 'AI', 'digital rights'],
        'description': 'Funds projects promoting a healthy internet.',
        'fit_score': 88,
    },
]

def generate_application(grant, identity=None):
    if not identity:
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
    today = datetime.date.today().strftime('%B %d, %Y')
    app = (
        'GRANT APPLICATION PACKAGE\n'
        + f"Grant: {grant['name']}\nURL: {grant['url']}\n"
        + f"Amount: {grant['amount']}\nDeadline: {grant['next_deadline']}\nGenerated: {today}\n\n"
        + '=' * 52 + '\nAPPLICANT INFORMATION\n' + '=' * 52 + '\n'
        + f"Name: {identity.get('name')}\nEmail: {identity.get('email')}\n"
        + f"Website: {identity.get('website')}\nGitHub: github.com/{identity.get('github')}\n\n"
        + '=' * 52 + '\nPROJECT DESCRIPTION\n' + '=' * 52 + '\n'
        + 'Project: Meeko Nerve Center - Ethical Autonomous Systems\n\n'
        + 'Overview:\n'
        + 'An open-source autonomous system that self-replicates through GitHub forks,\n'
        + "routes 70% of revenue to the Palestinian Children's Relief Fund, and ships\n"
        + 'legal tools (TCPA, FDCPA, FOIA) to protect ordinary people.\n\n'
        + 'Stack: Python, GitHub Actions, GitHub Pages, Ollama (local AI)\n'
        + 'Cost: $0/month. License: AGPL-3.0\n\n'
        + f"Mission alignment with {grant['name']}:\n{grant['description']}\n\n"
        + '=' * 52 + '\nLINKS\n' + '=' * 52 + '\n'
        + 'Repo: https://github.com/meekotharaccoon-cell/meeko-nerve-center\n'
        + 'Live: https://meekotharaccoon-cell.github.io/meeko-nerve-center\n'
        + 'Gallery: https://meekotharaccoon-cell.github.io/gaza-rose-gallery\n'
        + f"\nArtist statement: {identity.get('artist_statement')}\n"
        + '\n---\nGenerated by Meeko Nerve Center Grant Outreach\n' + today + '\n'
    )
    return app

def main():
    print(f"\n{C.G}{C.B}  GRANT OUTREACH SCANNER{C.X}\n")
    p = argparse.ArgumentParser()
    p.add_argument('--list',  action='store_true')
    p.add_argument('--apply', metavar='NAME')
    args = p.parse_args()

    if args.list or not args.apply:
        print(f'  {C.B}Grant opportunities (sorted by fit):{C.X}\n')
        for g in sorted(GRANTS, key=lambda g: g['fit_score'], reverse=True):
            col = C.G if g['fit_score'] >= 85 else (C.Y if g['fit_score'] >= 70 else C.D)
            print(f"  {col}*{C.X} {C.B}{g['name']}{C.X} - {g['amount']} | Deadline: {g['next_deadline']}")
            print(f"    {C.D}{g['description']}{C.X}")
            if g.get('action'):
                print(f"    {C.CY}ACTION NEEDED: {g['action']}{C.X}")
            print()
        GRANT_DATA.mkdir(parents=True, exist_ok=True)
        scan_path = GRANT_DATA / f"scan_{datetime.date.today().isoformat()}.json"
        scan_path.write_text(json.dumps(GRANTS, indent=2))
        print(f'  {C.G}OK{C.X} Scan saved: {scan_path}')

    if args.apply:
        matching = [g for g in GRANTS if args.apply.lower() in g['name'].lower()]
        if not matching:
            print(f'  {C.Y}No grant found matching: {args.apply}{C.X}')
            return
        grant = matching[0]
        app = generate_application(grant)
        GRANT_DATA.mkdir(parents=True, exist_ok=True)
        app_path = GRANT_DATA / f"application_{grant['name'].replace(' ','_')}_{datetime.date.today().isoformat()}.txt"
        app_path.write_text(app)
        print(app)
        print(f'  {C.G}OK{C.X} Application saved: {app_path}')

if __name__ == '__main__':
    main()
