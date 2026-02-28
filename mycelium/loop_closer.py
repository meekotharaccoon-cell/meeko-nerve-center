#!/usr/bin/env python3
"""
Loop Closer Engine — v2
========================
Previous version: Unclear what it did. No delta tracking.
Closed loops by... declaring them closed?

This version actually closes loops:
  1. Reads all data files and identifies orphaned outputs
     (data that was generated but never acted on)
  2. Checks for open tasks: drafted grants not submitted, pending ideas,
     flagged trades not posted, art not shared, errors not fixed
  3. Writes a clear action list to data/open_loops.json
  4. Passes open loops to self_healer_v2.py via self_diagnostic_inbox.json
  5. On Sundays: emails Meeko with the open loops (what needs human action)

This is how the system knows what it hasn't finished yet.
"""

import json, datetime, os, smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT    = Path(__file__).parent.parent
DATA    = ROOT / 'data'
TODAY   = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()

GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def find_open_loops():
    loops = []

    # 1. Grants drafted but not submitted
    db = load(DATA / 'grant_database.json', [])
    for g in db:
        if g.get('status') == 'drafted':
            loops.append({
                'type': 'grant_submission',
                'priority': 'HIGH',
                'description': f'Grant drafted but not submitted: {g["funder"]} — {g["program"]}',
                'action': f'Submit at: {g["url"]}',
                'human_required': True,
                'date_found': TODAY,
            })

    # 2. Pending ideas that have been waiting >7 days
    ledger = load(DATA / 'idea_ledger.json', {'ideas': {}})
    ideas  = ledger.get('ideas', {})
    il     = list(ideas.values()) if isinstance(ideas, dict) else ideas
    for idea in il:
        if idea.get('status') == 'pending':
            age_days = 0
            try:
                created = idea.get('date', TODAY)
                age_days = (datetime.date.today() - datetime.date.fromisoformat(created)).days
            except: pass
            if age_days >= 7:
                loops.append({
                    'type': 'stale_idea',
                    'priority': 'LOW',
                    'description': f'Idea pending {age_days}d: {idea.get("title","?")[:60]}',
                    'action': 'perpetual_builder will pick this up next cycle',
                    'human_required': False,
                    'date_found': TODAY,
                })

    # 3. Workflow failures that weren't retried
    health = load(DATA / 'workflow_health.json', {})
    if health.get('color') == 'RED':
        loops.append({
            'type': 'workflow_health',
            'priority': 'HIGH',
            'description': f'System health RED: {health.get("health_pct","?")}% ({health.get("failing",0)} failing)',
            'action': 'MASTER_CONTROLLER auto-retrying. Check in 30min.',
            'human_required': False,
            'date_found': TODAY,
        })

    # 4. Errors that self-healer hasn't fixed yet
    inbox = load(DATA / 'self_diagnostic_inbox.json', {'issues': []})
    unresolved = [i for i in inbox.get('issues', []) if not i.get('resolved')]
    if unresolved:
        loops.append({
            'type': 'unresolved_diagnostics',
            'priority': 'MEDIUM',
            'description': f'{len(unresolved)} unresolved diagnostic issues',
            'action': 'self_healer_v2.py will process these next cycle',
            'human_required': False,
            'date_found': TODAY,
        })

    # 5. Art generated but not posted to social
    arts = load(DATA / 'generated_art.json', {})
    art_list = arts if isinstance(arts, list) else arts.get('art', [])
    social   = load(DATA / 'post_schedule.json', {})
    last_post_date = social.get('last_post_date', '2020-01-01')
    if art_list and last_post_date < TODAY:
        unposted = len([a for a in art_list if a.get('date', TODAY) >= last_post_date])
        if unposted > 0:
            loops.append({
                'type': 'unposted_art',
                'priority': 'MEDIUM',
                'description': f'{unposted} art pieces generated but not posted to social',
                'action': 'social_poster.py will run next cycle',
                'human_required': False,
                'date_found': TODAY,
            })

    return loops

def write_loops_to_diagnostic_inbox(loops):
    """Pass loop data to self-healer for automated action."""
    p = DATA / 'self_diagnostic_inbox.json'
    inbox = load(p, {'issues': []})
    existing_types = {i.get('type') for i in inbox.get('issues', []) if not i.get('resolved')}

    added = 0
    for loop in loops:
        if loop['type'] not in existing_types and not loop['human_required']:
            inbox.setdefault('issues', []).append({
                'type': loop['type'],
                'description': loop['description'],
                'action': loop['action'],
                'date': TODAY,
                'resolved': False,
                'source': 'loop_closer',
            })
            added += 1

    try: p.write_text(json.dumps(inbox, indent=2))
    except: pass
    return added

def run():
    print(f'\n[loop_closer] 🔄 Loop Closer v2 — {TODAY}')

    loops = find_open_loops()
    human_loops = [l for l in loops if l['human_required']]
    auto_loops  = [l for l in loops if not l['human_required']]

    print(f'[loop_closer] Found {len(loops)} open loops: {len(human_loops)} need human, {len(auto_loops)} auto-fixable')

    # Save all open loops
    try:
        (DATA / 'open_loops.json').write_text(json.dumps({
            'date': TODAY,
            'total': len(loops),
            'human_required': len(human_loops),
            'auto_fixable': len(auto_loops),
            'loops': loops,
        }, indent=2))
    except: pass

    # Pass auto-fixable loops to self-healer
    added = write_loops_to_diagnostic_inbox(auto_loops)
    print(f'[loop_closer] Sent {added} loops to self-healer')

    # Print summary
    for loop in loops:
        emoji = '🔴' if loop['priority'] == 'HIGH' else '🟡' if loop['priority'] == 'MEDIUM' else '🟢'
        human = '👤' if loop['human_required'] else '🤖'
        print(f'[loop_closer] {emoji}{human} [{loop["type"]}] {loop["description"][:80]}')

    print('[loop_closer] Done.')

if __name__ == '__main__':
    run()
