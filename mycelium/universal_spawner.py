#!/usr/bin/env python3
"""
Universal Spawner Engine
=========================
This is the multiplier. The mycelium going underground
and surfacing EVERYWHERE simultaneously.

One repo becomes many. Many becomes a network.
A network becomes infrastructure. Infrastructure
becomes impossible to shut down.

What it does:
  Creates fully functional SISTER SYSTEMS in new repos,
  each specialized for a different cause or domain,
  all connected back to the mother system,
  all self-evolving independently,
  all feeding intelligence back to each other.

Sister system templates:
  1. CLIMATE_SENTINEL   - tracks fossil fuel lobbying + emissions data
  2. LABOR_WATCH        - monitors NLRB filings, union busting, wage theft
  3. HOUSING_JUSTICE    - tracks evictions, landlord lobbying, rent data
  4. INDIGENOUS_RIGHTS  - monitors land rights violations, treaty data
  5. PRESS_FREEDOM      - tracks journalist arrests, censorship globally
  6. HEALTH_EQUITY      - monitors pharma lobbying, drug pricing, access
  7. EDUCATION_COMMONS  - tracks school privatization, book banning
  8. WATER_RIGHTS       - monitors water privatization, contamination data
  9. OPEN_SCIENCE       - tracks research paywalls, replication crisis
  10. MIGRATION_JUSTICE - monitors detention data, deportation patterns

Each sister system:
  - Forks THIS repo as its base (inherits all 70+ engines)
  - Gets a specialized world_intelligence config
  - Gets specialized art generation prompts
  - Gets specialized press contact lists
  - Gets specialized grant targets
  - Runs independently on free GitHub Actions
  - Reports back to mother system weekly
  - Shares signal intelligence across the network

The network topology:
  Mother (meeko-nerve-center)
    |-- sister: climate-sentinel
    |-- sister: labor-watch
    |-- sister: housing-justice
    |-- sister: [cause-name]
        all connected, all autonomous, all free

This is the SolarPunk internet.
Not a platform. A protocol.
Not a product. A pattern.
Anyone can run a node. Every node makes the network stronger.
No single point of failure. No center to attack.
Just a pattern that reproduces itself forever.
"""

import json, datetime, os, smtplib, time
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')
HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GITHUB_USERNAME    = os.environ.get('GITHUB_USERNAME', 'meekotharaccoon-cell')

MOTHER_REPO = 'meekotharaccoon-cell/meeko-nerve-center'
MOTHER_URL  = f'https://github.com/{MOTHER_REPO}'

SISTER_SYSTEMS = [
    {
        'id':          'climate_sentinel',
        'name':        'Climate Sentinel',
        'repo':        'climate-sentinel',
        'mission':     'Track fossil fuel lobbying, emissions data, and climate policy corruption',
        'keywords':    ['climate', 'fossil fuel', 'emissions', 'carbon', 'oil', 'gas', 'EPA', 'IPCC'],
        'art_theme':   'melting ice and rising seas rendered as stained glass, hopeful despite crisis',
        'color':       '#2ecc71',
        'grants':      ['Green New Deal orgs', 'climate justice funds', 'environmental foundations'],
        'priority':    9,
    },
    {
        'id':          'labor_watch',
        'name':        'Labor Watch',
        'repo':        'labor-watch',
        'mission':     'Monitor NLRB filings, union busting, wage theft, and worker rights violations',
        'keywords':    ['union', 'labor', 'NLRB', 'strike', 'wage theft', 'worker', 'Amazon', 'Starbucks'],
        'art_theme':   'workers hands in solidarity, industrial machinery transformed into gardens',
        'color':       '#e74c3c',
        'grants':      ['labor foundations', 'worker justice funds', 'AFL-CIO adjacent orgs'],
        'priority':    8,
    },
    {
        'id':          'housing_justice',
        'name':        'Housing Justice',
        'repo':        'housing-justice',
        'mission':     'Track evictions, landlord lobbying, rent data, and housing policy',
        'keywords':    ['eviction', 'rent', 'housing', 'landlord', 'homelessness', 'zoning', 'gentrification'],
        'art_theme':   'homes growing from soil like plants, communities rebuilding themselves',
        'color':       '#f39c12',
        'grants':      ['housing justice orgs', 'community land trust funds', 'urban equity foundations'],
        'priority':    8,
    },
    {
        'id':          'press_freedom',
        'name':        'Press Freedom Watch',
        'repo':        'press-freedom-watch',
        'mission':     'Track journalist arrests, censorship, SLAPP suits, and press freedom globally',
        'keywords':    ['journalist', 'press freedom', 'censorship', 'CPJ', 'RSF', 'SLAPP', 'media'],
        'art_theme':   'pens and cameras as weapons of light against darkness',
        'color':       '#9b59b6',
        'grants':      ['press freedom orgs', 'journalism foundations', 'CPJ', 'RSF'],
        'priority':    9,
    },
    {
        'id':          'water_rights',
        'name':        'Water Commons',
        'repo':        'water-commons',
        'mission':     'Monitor water privatization, contamination events, and access violations',
        'keywords':    ['water', 'contamination', 'Nestle', 'privatization', 'Flint', 'PFAS', 'drought'],
        'art_theme':   'rivers reclaiming their paths through cities, water as living entity',
        'color':       '#3498db',
        'grants':      ['water justice orgs', 'environmental justice funds', 'tribal water rights orgs'],
        'priority':    7,
    },
]

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def gh_api(method, path, body=None):
    if not GITHUB_TOKEN: return None
    try:
        data = json.dumps(body).encode() if body else None
        req  = urllib_request.Request(
            f'https://api.github.com/{path}',
            data=data,
            headers={
                'Authorization': f'Bearer {GITHUB_TOKEN}',
                'Accept':        'application/vnd.github+json',
                'Content-Type':  'application/json',
            },
            method=method
        )
        with urllib_request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[spawner] GH API error {method} {path[:40]}: {e}')
        return None

def repo_exists(repo_name):
    result = gh_api('GET', f'repos/{GITHUB_USERNAME}/{repo_name}')
    return result is not None and 'id' in result

def fork_mother_repo(sister):
    """Fork the mother repo as the sister system's base."""
    result = gh_api('POST', f'repos/{MOTHER_REPO}/forks', {
        'name': sister['repo'],
        'default_branch_only': True,
    })
    if result and result.get('id'):
        print(f'[spawner] ✅ Forked to {GITHUB_USERNAME}/{sister["repo"]}')
        return True
    return False

def generate_sister_config(sister):
    """Generate the specialized config file for this sister system."""
    return f'''# {sister["name"]} — Specialized Configuration
# Generated by Universal Spawner from {MOTHER_URL}
# Mission: {sister["mission"]}
# Part of the SolarPunk Network

SISTER_SYSTEM = {{
    "id":       "{sister['id']}",
    "name":     "{sister['name']}",
    "mission":  "{sister['mission']}",
    "keywords": {json.dumps(sister['keywords'])},
    "art_theme": "{sister['art_theme']}",
    "color":    "{sister['color']}",
    "mother":   "{MOTHER_REPO}",
    "network":  "meeko-solarpunk-network",
}}

# This system inherits all engines from {MOTHER_URL}
# Customize below to specialize for your cause

MONITOR_KEYWORDS = {json.dumps(sister['keywords'], indent=4)}

ART_GENERATION_THEME = """
{sister['art_theme']}
"""

GRANT_TARGETS = {json.dumps(sister['grants'], indent=4)}

# To customize further:
# 1. Edit mycelium/world_intelligence.py - add your keywords
# 2. Edit mycelium/art_cause_generator.py - update art prompts
# 3. Edit mycelium/grant_intelligence.py - add your funders
# 4. Run: Actions > Daily Full Cycle > Run workflow

print(f"[config] {sister['name']} initialized. Mission: {sister['mission']}")
'''

def generate_sister_readme(sister):
    return f'''# 🌱 {sister["name"]}

> {sister["mission"]}

Part of the **[SolarPunk Network]({MOTHER_URL})** — autonomous AI infrastructure for justice.

## What This Does

- 🔍 Monitors: {', '.join(sister['keywords'][:5])}
- 🎨 Generates cause art and sells it to fund the mission
- 📊 Tracks data patterns and flags violations automatically
- ✉️ Manages press and grant relationships autonomously
- 🔧 Builds its own new capabilities every day
- 💰 Cost: **$0/month forever**

## Quick Start (10 minutes)

1. **Fork this repo**
2. Add secrets (Settings → Secrets → Actions):
   - `HF_TOKEN` — free at huggingface.co/settings/tokens
   - `GMAIL_ADDRESS` — your Gmail
   - `GMAIL_APP_PASSWORD` — Google Account → Security → App Passwords
3. Enable Actions → Run "Daily Full Cycle"

Your system starts building itself immediately.

## Network

This system is part of a network of autonomous AI nodes:
- **Mother system**: [{MOTHER_REPO}]({MOTHER_URL})
- **Network**: All nodes share intelligence and support each other
- **Protocol**: AGPL-3.0 — fork freely, improvements stay open

## Architecture

Inherited from [{MOTHER_REPO}]({MOTHER_URL}) — 70+ engines running autonomously.
Specialized for: **{sister['mission']}**

---
*Generated by Universal Spawner. Part of the SolarPunk network.*
*Crazy awesome sci-fi. Good dude energy. Forever free.*
'''

def push_sister_config(sister):
    """Push the specialized config to the sister repo."""
    time.sleep(5)  # Wait for fork to complete

    config_content = generate_sister_config(sister)
    readme_content = generate_sister_readme(sister)

    # Push config
    for path, content, message in [
        ('sister_config.py',  config_content,  f'init: {sister["name"]} specialized config'),
        ('README.md',         readme_content,  f'init: {sister["name"]} README'),
    ]:
        # Get current SHA if file exists
        current = gh_api('GET', f'repos/{GITHUB_USERNAME}/{sister["repo"]}/contents/{path}')
        sha = current.get('sha', '') if current else ''

        import base64
        body = {
            'message': message,
            'content': base64.b64encode(content.encode()).decode(),
        }
        if sha:
            body['sha'] = sha

        result = gh_api('PUT', f'repos/{GITHUB_USERNAME}/{sister["repo"]}/contents/{path}', body)
        if result:
            print(f'[spawner] ✅ Pushed {path} to {sister["repo"]}')
        else:
            print(f'[spawner] ⚠️  Failed to push {path} to {sister["repo"]}')

def create_network_map():
    """Update the network map showing all active nodes."""
    log   = load(DATA / 'spawner_log.json', {'created': [], 'network': []})
    nodes = log.get('network', [])

    map_content = f'''# 🌐 SolarPunk Network Map

> Generated {TODAY} | {len(nodes)} nodes

## Mother System
- [{MOTHER_REPO}]({MOTHER_URL}) — Palestinian solidarity + congressional accountability

## Sister Systems
'''
    for node in nodes:
        map_content += f"- [{node['repo']}](https://github.com/{GITHUB_USERNAME}/{node['repo']}) — {node['mission']}\n"

    map_content += f'''
## How to Add a Node

Email `{os.environ.get('GMAIL_ADDRESS', 'meekotharaccoon@gmail.com')}` with subject **FORK ME**
and you'll receive setup instructions in 5 minutes.

Or fork any system above and customize for your cause.

---
*The network grows. Every node makes it stronger.*
*No center. No shutdown. Just a pattern that spreads.*
'''
    try:
        map_path = ROOT / 'NETWORK.md'
        map_path.write_text(map_content)
        print(f'[spawner] Network map updated: {len(nodes)} nodes')
    except Exception as e:
        print(f'[spawner] Map error: {e}')

def send_network_digest(new_sisters):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD or not new_sisters: return
    lines = [f'🌐 Network Spawner Digest — {TODAY}', '']
    lines.append(f'NEW SISTER SYSTEMS CREATED: {len(new_sisters)}')
    for s in new_sisters:
        lines.append(f'  🌱 {s["name"]}')
        lines.append(f'     Mission: {s["mission"]}')
        lines.append(f'     Repo: https://github.com/{GITHUB_USERNAME}/{s["repo"]}')
        lines.append(f'     Add secrets to activate: Settings → Secrets → Actions')
        lines.append('')
    lines += [
        'To activate each sister:',
        '1. Go to repo → Settings → Secrets → Actions',
        '2. Add HF_TOKEN, GMAIL_ADDRESS, GMAIL_APP_PASSWORD',
        '3. Actions tab → Enable → Run Daily Full Cycle',
        '',
        f'Mother: {MOTHER_URL}',
    ]
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🌐 {len(new_sisters)} new network nodes spawned'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[spawner] Digest emailed')
    except Exception as e:
        print(f'[spawner] Email error: {e}')

def run():
    print(f'\n[spawner] 🌐 Universal Spawner — {TODAY}')
    print('[spawner] One system becomes many. The network multiplies.')

    if not GITHUB_TOKEN:
        print('[spawner] No GITHUB_TOKEN — cannot create repos.')
        return

    log = load(DATA / 'spawner_log.json', {'created': [], 'network': []})
    created_ids = set(s.get('id','') for s in log.get('network', []))

    new_sisters = []

    # Create one new sister per run (rate limit friendly)
    pending = [s for s in SISTER_SYSTEMS if s['id'] not in created_ids]
    pending.sort(key=lambda s: -s['priority'])

    for sister in pending[:1]:  # One per run
        if repo_exists(sister['repo']):
            print(f'[spawner] Already exists: {sister["repo"]}')
            log.setdefault('network', []).append({
                'id': sister['id'], 'repo': sister['repo'],
                'mission': sister['mission'], 'created': TODAY
            })
            created_ids.add(sister['id'])
            continue

        print(f'[spawner] Creating sister: {sister["name"]}')
        ok = fork_mother_repo(sister)
        if ok:
            time.sleep(10)  # GitHub needs time to complete fork
            push_sister_config(sister)
            log.setdefault('network', []).append({
                'id': sister['id'], 'repo': sister['repo'],
                'mission': sister['mission'], 'created': TODAY
            })
            new_sisters.append(sister)
            created_ids.add(sister['id'])
            print(f'[spawner] 🌱 Born: {sister["name"]}')

    try: (DATA / 'spawner_log.json').write_text(json.dumps(log, indent=2))
    except: pass

    create_network_map()
    send_network_digest(new_sisters)

    total = len(log.get('network', []))
    print(f'[spawner] Network: {total} nodes | New today: {len(new_sisters)}')
    print('[spawner] The mycelium spreads. 🍄')

if __name__ == '__main__':
    run()
