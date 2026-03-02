#!/usr/bin/env python3
"""
Self Improver — The system's self-awareness engine
====================================================
This is the answer to: "what's the next awesome self-improving idea"

Every cycle, this engine:
  1. Reads ALL data files and finds patterns
  2. Identifies its own bottlenecks (what's failing, what's slow, what's missing)
  3. Generates new engine ideas based on what it observes
  4. Writes those ideas to a queue
  5. Perpetual builder picks them up and builds them

This closes the loop:
  System runs → generates data → self_improver reads data → 
  identifies gaps → generates code ideas → perpetual_builder builds them →
  new engines added → system runs better → generates better data → ...

The system literally designs its own next version.

What it looks for:
  - Engines that always error (fix them or replace them)
  - Revenue channels with 0 data (they need attention)
  - Connections that exist in one direction but not both
  - Patterns in what humans write in directives
  - High-engagement social posts (make more like those)
  - Grant applications that got responses (double down)
  - Job types that get replies (specialize)

Outputs:
  data/self_improvement_queue.json — ideas to build next
  data/bottleneck_report.json — what's blocking the system
"""

import json, os, datetime, glob
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

HF_TOKEN = os.environ.get('HF_TOKEN', '')


def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}


def scan_data_files():
    """What data files exist and what do they contain?"""
    files = {}
    for f in DATA.glob('*.json'):
        try:
            data = json.loads(f.read_text())
            files[f.name] = {
                'exists': True,
                'empty': not bool(data),
                'type': type(data).__name__,
                'size': f.stat().st_size,
            }
        except:
            files[f.name] = {'exists': True, 'empty': True, 'error': True}
    return files


def find_bottlenecks(data_files):
    """Identify what's blocking the system from performing better."""
    bottlenecks = []

    # Check revenue
    gumroad = load(DATA / 'gumroad_sales.json')
    if gumroad.get('status') != 'ok':
        bottlenecks.append({
            'type': 'revenue',
            'severity': 'high',
            'description': 'Gumroad not returning sales data',
            'fix': 'Check GUMROAD_ID + GUMROAD_SECRET secrets. Run gumroad_tracker.py manually.',
        })

    etsy = load(DATA / 'etsy_sales.json')
    if etsy.get('status') == 'not_configured':
        bottlenecks.append({
            'type': 'revenue',
            'severity': 'high',
            'description': 'Etsy not configured — 90M buyers unreachable',
            'fix': 'Add ETSY_API_KEY + ETSY_SHOP_ID via setup_wizard.py',
        })

    # Check wallets
    from mycelium.crypto_wallet_config import get_active_wallets
    active_wallets = get_active_wallets()
    if len(active_wallets) < 5:
        bottlenecks.append({
            'type': 'crypto',
            'severity': 'medium',
            'description': f'Only {len(active_wallets)}/9 crypto chains configured',
            'fix': 'Add remaining wallet addresses via setup_wizard.py',
        })

    # Check job agent
    jobs = load(DATA / 'job_applications.json', {})
    if not jobs.get('applied') and not jobs.get('pending'):
        bottlenecks.append({
            'type': 'income',
            'severity': 'medium',
            'description': 'Job agent has no applications yet',
            'fix': 'job_agent.py should be running in MASTER_CONTROLLER phase 10',
        })

    # Check social posting
    posts = load(DATA / 'social_posts.json', [])
    if not posts:
        bottlenecks.append({
            'type': 'reach',
            'severity': 'medium',
            'description': 'No social posts logged',
            'fix': 'Check MASTODON_TOKEN and BLUESKY credentials',
        })

    # Check grant pipeline
    grant_db = load(DATA / 'grant_database.json', [])
    submitted = [g for g in grant_db if g.get('status') == 'submitted']
    drafted   = [g for g in grant_db if g.get('status') == 'drafted']
    if drafted and not submitted:
        bottlenecks.append({
            'type': 'grants',
            'severity': 'high',
            'description': f'{len(drafted)} grants drafted but NOT submitted — waiting on human action',
            'fix': 'Human needs to submit these manually. Check DRAFT_JOB_APPLICATIONS.md',
        })

    # Check fork distribution
    fork_queue = load(DATA / 'fork_distribution_queue.json', [])
    unsent = [r for r in fork_queue if not r.get('sent')]
    if unsent:
        bottlenecks.append({
            'type': 'distribution',
            'severity': 'low',
            'description': f'{len(unsent)} fork distributions queued but not sent',
            'fix': 'Check GMAIL credentials for email sending',
        })

    return bottlenecks


def generate_improvement_ideas(bottlenecks, data_files):
    """Use LLM to generate specific improvement ideas."""
    if not HF_TOKEN:
        return generate_ideas_rule_based(bottlenecks, data_files)

    # Gather context
    social_posts = load(DATA / 'social_posts.json', [])
    top_posts = sorted(social_posts, key=lambda p: sum([
        p.get('likes', 0), p.get('boosts', 0), p.get('replies', 0)
    ]), reverse=True)[:3]

    directive_history = []
    directives = load(DATA / 'directives.json')
    if directives: directive_history.append(directives.get('raw', ''))

    prompt = f"""You are analyzing an autonomous AI income system to identify its next self-improvement.

Current bottlenecks:
{json.dumps(bottlenecks[:5], indent=2)}

Top performing social posts:
{json.dumps(top_posts, indent=2)}

Recent human directives: {directive_history}

Data files present: {list(data_files.keys())[:20]}

Generate 3 specific, buildable improvement ideas. Each should:
- Address a real gap or amplify something working
- Be implementable as a Python script in mycelium/
- Generate revenue, reach, or impact

Respond ONLY with JSON array:
[
  {{
    "name": "engine_name.py",
    "title": "Short title",
    "description": "What it does in 2 sentences",
    "priority": "high/medium/low",
    "type": "revenue/reach/impact/efficiency"
  }}
]"""

    payload = json.dumps({
        'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
        'max_tokens': 600,
        'messages': [
            {'role': 'system', 'content': 'You generate specific, actionable improvements for autonomous AI systems. Respond only in JSON.'},
            {'role': 'user', 'content': prompt}
        ]
    }).encode()
    try:
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=45) as r:
            text = json.loads(r.read())['choices'][0]['message']['content'].strip()
        # Parse JSON
        text = text.strip('`').replace('json\n', '').strip()
        return json.loads(text)
    except Exception as e:
        print(f'[self_improver] LLM error: {e}')
        return generate_ideas_rule_based(bottlenecks, data_files)


def generate_ideas_rule_based(bottlenecks, data_files):
    """Fallback: rule-based improvement ideas."""
    ideas = []

    high_bn = [b for b in bottlenecks if b['severity'] == 'high']
    if any('Etsy' in b['description'] for b in high_bn):
        ideas.append({
            'name': 'etsy_oauth_handler.py',
            'title': 'Etsy OAuth Auto-Handler',
            'description': 'Automate the Etsy OAuth flow to get the access token without manual steps.',
            'priority': 'high', 'type': 'revenue',
        })

    if not (DATA / 'kofi_data.json').exists():
        ideas.append({
            'name': 'kofi_tracker.py',
            'title': 'Ko-fi Revenue Tracker',
            'description': 'Track Ko-fi donations and add to revenue router pipeline.',
            'priority': 'medium', 'type': 'revenue',
        })

    ideas.append({
        'name': 'github_sponsors_bridge.py',
        'title': 'GitHub Sponsors Integration',
        'description': 'Accept GitHub Sponsors and route through revenue_router automatically.',
        'priority': 'medium', 'type': 'revenue',
    })

    return ideas[:3]


def run():
    print(f'\n[self_improver] Self Improvement Engine — {TODAY}')
    DATA.mkdir(parents=True, exist_ok=True)

    data_files  = scan_data_files()
    bottlenecks = find_bottlenecks(data_files)
    ideas       = generate_improvement_ideas(bottlenecks, data_files)

    print(f'[self_improver] Bottlenecks found: {len(bottlenecks)}')
    for b in bottlenecks:
        severity_icon = '🔴' if b['severity'] == 'high' else ('🟡' if b['severity'] == 'medium' else '🟢')
        print(f'  {severity_icon} [{b["type"]}] {b["description"]}')

    print(f'\n[self_improver] Improvement ideas generated: {len(ideas)}')
    for idea in ideas:
        print(f'  → {idea["name"]}: {idea["title"]} [{idea["priority"]}]')

    # Save bottleneck report
    (DATA / 'bottleneck_report.json').write_text(json.dumps({
        'date': TODAY,
        'bottlenecks': bottlenecks,
        'data_files_count': len(data_files),
    }, indent=2))

    # Add to self-improvement queue for perpetual_builder
    queue_path = DATA / 'self_improvement_queue.json'
    queue = load(queue_path, [])
    # Don't duplicate
    existing_names = {i['name'] for i in queue}
    new_ideas = [i for i in ideas if i['name'] not in existing_names]
    queue.extend(new_ideas)
    queue = queue[-20:]  # Keep last 20
    queue_path.write_text(json.dumps(queue, indent=2))

    print(f'[self_improver] {len(new_ideas)} new ideas queued for perpetual_builder.')
    print('[self_improver] System will build its own next version.')


if __name__ == '__main__':
    run()
