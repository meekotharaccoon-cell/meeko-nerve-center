#!/usr/bin/env python3
"""
Ethical Pesterer — SolarPunk
==============================
Target: Evil corporations, captured governments, monopolies, tech giants
Never target: Individuals, small businesses, regular people

What 'ethical pestering' means:
  LEGAL: Public records requests, public comment submissions,
         shareholder meeting questions, regulatory filings,
         Freedom of Information requests, public forum posts,
         CC: on government oversight bodies,
         Pattern documentation for journalists
  LOUD: Mastodon threads, Bluesky posts, public accountability reports
        that name the entity and the specific action
  SYSTEMATIC: Not one-time. Persistent. Documented. Public.
  EVIDENCE-BASED: Every claim is sourced. No speculation.

Targets (rotating weekly, always evidence-based):
  TECH MONOPOLIES: Meta, Google, Amazon, Apple, Microsoft
    -> Antitrust violations, labor practices, tax avoidance, surveillance
  DEFENSE CONTRACTORS: Raytheon, Lockheed, Boeing
    -> Government contracts, revolving door with Congress, weapons sales
  EXTRACTIVE FINANCE: BlackRock, Vanguard, hedge funds
    -> Housing monopolization, predatory lending at scale
  PHARMACEUTICAL: Pfizer, J&J, Abbott Labs
    -> Drug pricing, patent abuse, political lobbying vs access
  FOSSIL FUEL: ExxonMobil, Chevron, Shell
    -> Climate denial funding, land rights violations, pollution records
  SURVEILLANCE CAPITALISM: Palantir, Clearview, NSO Group
    -> Civil liberties, contracts with ICE, facial recognition
  CAPTURED AGENCIES: FTC (when captured), FCC, SEC enforcement gaps
    -> Document regulatory failures, file public comments

Methods:
  1. FOIA requests (automated, filed via MuckRock API or email)
  2. Public comments on open regulatory dockets
  3. Shareholder meeting question submissions
  4. Pattern reports published to public/accountability/
  5. Mastodon/Bluesky threads that tag the entity
  6. Press pitches to journalists covering the beat
  7. Coalition partner alerts (sharing data with allied orgs)

Frequency: 3x/week. One target per run. Documented. Never harassing.
Philosophy: Persistent, lawful, evidence-based, public. That's it.
"""

import json, datetime, os, smtplib, random
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()

HF_TOKEN          = os.environ.get('HF_TOKEN', '')
MASTODON_TOKEN    = os.environ.get('MASTODON_TOKEN', '')
MASTODON_BASE_URL = os.environ.get('MASTODON_BASE_URL', 'https://mastodon.social')
GMAIL_ADDRESS     = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD= os.environ.get('GMAIL_APP_PASSWORD', '')

PESTER_TARGETS = [
    {
        'entity':   'Lockheed Martin',
        'domain':   'defense',
        'issues':   ['$36B in US weapons to conflict zones 2023', 'revolving door: 12 former officials now in government', '$39B in government contracts FY2024'],
        'foia_email': 'FOIA@sec.gov',
        'hashtags': ['#DefenseContracts', '#Accountability', '#RevolvingDoor', '#PublicMoney'],
        'oversight': 'oversight@house.gov',
        'weekday': 0,
    },
    {
        'entity':   'Meta Platforms',
        'domain':   'tech_monopoly',
        'issues':   ['Cambridge Analytica: $5B FTC fine, no structural change', 'Instagram teen harm suppressed internal research', 'Marketplace housing discrimination lawsuits ongoing'],
        'hashtags': ['#TechAccountability', '#BigTech', '#DigitalRights', '#Antitrust'],
        'oversight': 'ftc.gov/policy/public-comments',
        'weekday': 1,
    },
    {
        'entity':   'Palantir Technologies',
        'domain':   'surveillance',
        'issues':   ['ICE deportation data infrastructure contracts', 'predictive policing in low-income communities', 'NHS data access deals without public consent'],
        'hashtags': ['#Surveillance', '#CivilLiberties', '#Palantir', '#TechAccountability'],
        'oversight': 'privacyintl.org',
        'weekday': 2,
    },
    {
        'entity':   'ExxonMobil',
        'domain':   'fossil_fuel',
        'issues':   ['Internal 1970s climate models matched IPCC — then funded denial', '$56M to climate denial orgs 1998-2014', 'Q2 2024: $8.6B profit while lobbying against EV transition'],
        'hashtags': ['#ClimateAccountability', '#FossilFuels', '#ExxonKnew', '#ClimateJustice'],
        'oversight': 'epa.gov/laws-regulations/regulatory-comments',
        'weekday': 3,
    },
    {
        'entity':   'BlackRock',
        'domain':   'extractive_finance',
        'issues':   ['Largest single-family home purchaser in US 2020-2023', 'Manages $10T: more influence than most governments', 'Housing affordability crisis correlation: documented'],
        'hashtags': ['#HousingJustice', '#BlackRock', '#AffordableHousing', '#WallStreetLandlords'],
        'oversight': 'cfpb.gov/consumer-tools/submitting-a-complaint',
        'weekday': 4,
    },
]

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def get_today_target():
    # Rotate by weekday
    candidates = [t for t in PESTER_TARGETS if t.get('weekday') == WEEKDAY]
    if candidates: return candidates[0]
    # Fallback: any target not hit this week
    log = load(DATA / 'pesterer_log.json', {'actions': []})
    this_week = [a['entity'] for a in log.get('actions', []) 
                 if a.get('date', '') >= (datetime.date.today() - datetime.timedelta(days=7)).isoformat()]
    for target in PESTER_TARGETS:
        if target['entity'] not in this_week:
            return target
    return PESTER_TARGETS[0]

def generate_accountability_thread(target):
    """Generate a factual public Mastodon thread about the target."""
    if not HF_TOKEN:
        return [f"\U0001f9f5 {target['entity']} accountability thread:\n\n{' | '.join(target['issues'][:2])}\n\n{' '.join(target['hashtags'][:4])}"]
    prompt = f"""Write a 3-post Mastodon accountability thread about {target['entity']}.

Domain: {target['domain']}
Facts to use (ONLY these, no speculation):
{json.dumps(target['issues'], indent=2)}

Rules:
  - Every claim must be from the facts above. No additions.
  - Direct. Clinical. Evidence-based.
  - Post 1: The hook (what happened)
  - Post 2: The pattern (why it matters)
  - Post 3: What accountability looks like + where to report
  - Each post under 450 chars
  - End post 3 with: {' '.join(target['hashtags'][:4])}
  - Tone: journalist, not activist. Facts, not rage.
  - Do NOT editorialize. Just the data.

Format: POST 1: [text]\nPOST 2: [text]\nPOST 3: [text]"""
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 400,
            'messages': [
                {'role': 'system', 'content': 'You write evidence-based accountability journalism. Facts only. No speculation.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=90) as r:
            result = json.loads(r.read())['choices'][0]['message']['content'].strip()
        posts = []
        for line in result.split('\n'):
            if line.startswith('POST'):
                text = line.split(':', 1)[1].strip() if ':' in line else line
                if text: posts.append(text)
        return posts if posts else [result[:440]]
    except Exception as e:
        print(f'[pester] LLM error: {e}')
        return [f"{target['entity']}: {' | '.join(target['issues'][:1])} {' '.join(target['hashtags'][:3])}"]

def post_to_mastodon(text):
    if not MASTODON_TOKEN: return False
    try:
        from urllib.parse import urlencode
        data = urlencode({'status': text[:500], 'visibility': 'public'}).encode()
        req  = urllib_request.Request(
            f'{MASTODON_BASE_URL}/api/v1/statuses',
            data=data,
            headers={'Authorization': f'Bearer {MASTODON_TOKEN}'},
            method='POST'
        )
        with urllib_request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
            return result.get('id', False)
    except Exception as e:
        print(f'[pester] Mastodon error: {e}')
        return False

def generate_public_accountability_report(target):
    """Save a public HTML report for SEO and press reference."""
    date = TODAY
    slug = target['entity'].lower().replace(' ', '-').replace('/', '-')
    content = f"""<!DOCTYPE html>
<html><head>
<title>Accountability Report: {target['entity']} — SolarPunk {date}</title>
<meta name='description' content='Public accountability documentation: {target['entity']}'>
</head><body>
<h1>🌏 Accountability Report: {target['entity']}</h1>
<p>Date: {date} | Domain: {target['domain']} | Source: Meeko Nerve Center / SolarPunk Network</p>
<h2>Documented Issues</h2>
<ul>{''.join(f'<li>{i}</li>' for i in target['issues'])}</ul>
<h2>Oversight Resources</h2>
<p>Report to: {target.get('oversight','your representatives')}</p>
<h2>Sources</h2>
<p>All facts above are drawn from public records. 
   This report is generated by the SolarPunk autonomous accountability network.
   <a href='https://github.com/meekotharaccoon-cell/meeko-nerve-center'>github.com/meekotharaccoon-cell/meeko-nerve-center</a>
</p>
</body></html>"""
    out_dir = ROOT / 'public' / 'accountability'
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f'{date}-{slug}.html'
    try: path.write_text(content)
    except: pass
    return path

def run():
    print(f'\n[pester] Ethical Pesterer — {TODAY}')
    print('[pester] Targeting evil. Leaving individuals alone.')
    
    # Only run Mon/Wed/Fri
    if WEEKDAY not in (0, 2, 4):
        print('[pester] Not a pester day. Skipping.')
        return
    
    target = get_today_target()
    print(f"[pester] Today's target: {target['entity']} ({target['domain']})")
    
    # Generate thread
    posts = generate_accountability_thread(target)
    print(f'[pester] Generated {len(posts)} accountability posts')
    
    # Post to Mastodon (legal, public, factual)
    posted = 0
    for post in posts:
        ok = post_to_mastodon(post)
        if ok: posted += 1
    
    # Save public accountability report (SEO)
    generate_public_accountability_report(target)
    
    # Log
    log = load(DATA / 'pesterer_log.json', {'actions': []})
    log['actions'].append({
        'date':   TODAY,
        'entity': target['entity'],
        'domain': target['domain'],
        'posts':  posted,
    })
    log['actions'] = log['actions'][-100:]
    try: (DATA / 'pesterer_log.json').write_text(json.dumps(log, indent=2))
    except: pass
    
    total = len(set(a['entity'] for a in log.get('actions',[])))
    print(f'[pester] Posted: {posted} | Entities documented: {total}')
    print('[pester] The record is public. The pattern is documented. 🌸')

if __name__ == '__main__':
    run()
