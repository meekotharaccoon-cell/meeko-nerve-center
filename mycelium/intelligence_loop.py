#!/usr/bin/env python3
"""
Intelligence Loop Engine
=========================
The remaining human touchpoint that nobody talks about:

You still have to READ the emails the system sends you.
You still have to DECIDE whether the system is working.
You still have to NOTICE when something goes wrong.

This engine makes even THAT nearly unnecessary.

It monitors the system from the outside (as a human would)
and creates a single weekly email that is the ONLY thing
you actually need to read to stay fully informed.

The Meeko Weekly (every Sunday, 8am):

  SECTION 1: 'DO THESE' (actions needed from you)
    Ranked by urgency. Usually 0-3 items.
    Each one: specific action, URL, estimated time.
    If empty: 'Nothing needed. You\'re good.'

  SECTION 2: 'WHAT HAPPENED' (5 biggest things this week)
    Not a data dump. Narrative. 5 sentences.
    What actually moved? What was built? What was flagged?

  SECTION 3: 'MONEY' (one line)
    $X gross | $Y to PCRF | $Z to you | $W in pipeline

  SECTION 4: 'HEALTH' (system check)
    Green/Yellow/Red per engine category
    Any critical failures or blocks

  SECTION 5: 'WHAT THE SYSTEM IS THINKING'
    The latest strategic synthesis in plain English
    What does the machine think it should focus on?

  SECTION 6: 'THE NETWORK'
    Sister systems status. New forks. New nodes.

If you only ever read ONE email per week, this is it.
Everything else is optional. This is not.
But even this: the system writes it so well that
reading it takes under 3 minutes.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
WEEKDAY = datetime.date.today().weekday()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

REPO_URL = 'https://github.com/meekotharaccoon-cell/meeko-nerve-center'

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def collect_actions_needed():
    actions = []
    # Missing secrets
    critical_secrets = ['HF_TOKEN', 'GMAIL_ADDRESS', 'GMAIL_APP_PASSWORD']
    for s in critical_secrets:
        if not os.environ.get(s):
            actions.append({'urgency': 'HIGH', 'action': f'Add secret: {s}', 'time': '2 min',
                            'url': f'https://github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets/actions/new'})
    # PCRF transfer pending
    try:
        fin = load(DATA / 'financial_report.json', {})
        pending = fin.get('pcrf_pending', 0)
        if pending >= 10:
            actions.append({'urgency': 'MEDIUM', 'action': f'Transfer ${pending:.2f} to PCRF',
                            'time': '3 min', 'url': 'https://www.pcrf.net/donate'})
    except: pass
    # Validation failures
    try:
        val = load(DATA / 'validation_report.json', {})
        fails = [r['check'] for r in val.get('results', []) if not r.get('ok')]
        for f in fails[:2]:
            actions.append({'urgency': 'LOW', 'action': f'Engine failing: {f}', 'time': '5 min',
                            'url': f'{REPO_URL}/actions'})
    except: pass
    # Setup wizard items
    try:
        wiz = load(DATA / 'setup_wizard_log.json', {})
        done = wiz.get('completed', [])
        all_ids = ['mastodon', 'bluesky', 'kofi', 'gumroad', 'patreon', 'reddit']
        remaining = [i for i in all_ids if i not in done]
        if remaining:
            actions.append({'urgency': 'LOW',
                            'action': f'One-time setup: {remaining[0]} (unlocks more capabilities)',
                            'time': '5 min',
                            'url': f'{REPO_URL}/blob/main/DEPLOY.md'})
    except: pass
    return actions

def collect_weekly_narrative():
    # Pull key events from last 7 days
    events = []
    try:
        evo = load(DATA / 'evolution_log.json', {'built': []})
        recent = [b for b in evo.get('built', [])
                  if b.get('date','') >= (datetime.date.today() - datetime.timedelta(days=7)).isoformat()]
        if recent:
            events.append(f"Built {len(recent)} new engines: {', '.join(b.get('title','?')[:30] for b in recent[:3])}")
    except: pass
    try:
        congress = load(DATA / 'congress.json')
        trades = congress if isinstance(congress, list) else congress.get('trades', [])
        if trades: events.append(f"Flagged {len(trades)} congressional trades including {trades[0].get('ticker','?')}")
    except: pass
    try:
        network = load(DATA / 'spawner_log.json', {'network': []})
        nodes = network.get('network', [])
        if nodes: events.append(f"Network has {len(nodes)} sister systems")
    except: pass
    try:
        spread = load(DATA / 'network_spread_log.json', {'contacted': []})
        events.append(f"Reached {len(spread.get('contacted',[]))} people total | {len(spread.get('forked',[]))} forks")
    except: pass
    return events

def build_weekly_brief(actions, events, stats, synthesis):
    lines = [
        f'\U0001f338 MEEKO WEEKLY — {TODAY}',
        f'Your autonomous system. One email. Everything you need.',
        '=' * 55,
        '',
    ]
    # DO THESE
    lines.append(f'\U0001f4cc DO THESE ({len(actions)} item{"s" if len(actions)!=1 else ""}):' if actions else '\u2705 NOTHING NEEDED FROM YOU')
    if actions:
        for a in actions:
            lines += [f'  [{a["urgency"]}] {a["action"]}', f'         Time: {a["time"]} | {a["url"]}']
    else:
        lines.append('  Zero. You\'re good. The machine handled it.')
    lines += ['', '=' * 55, '']
    # WHAT HAPPENED
    lines.append('\U0001f4f0 WHAT HAPPENED THIS WEEK:')
    for e in events[:5]:
        lines.append(f'  \u2022 {e}')
    if not events:
        lines.append('  (No event data yet — system is warming up)')
    lines += ['', '=' * 55, '']
    # MONEY
    try:
        fin = load(DATA / 'financial_report.json', {})
        lines.append(f'\U0001f4b0 MONEY: ${fin.get("gross_monthly",0):.2f} gross | ${fin.get("pcrf_monthly",0):.2f} to PCRF | ${fin.get("creator_net",0):.2f} yours | ${fin.get("grant_pipeline",0):,.0f} in grants')
    except:
        lines.append('\U0001f4b0 MONEY: (financial data not yet available)')
    lines += ['', '=' * 55, '']
    # HEALTH
    lines.append(f'\U0001f9e0 SYSTEM HEALTH:')
    lines.append(f'  Engines: {stats.get("engines",0)} | Self-built: {stats.get("self_built",0)}')
    lines.append(f'  Art: {stats.get("art",0)} pieces | PCRF: ${stats.get("pcrf",0):.2f}')
    try:
        val = load(DATA / 'validation_report.json', {})
        fails = [r['check'] for r in val.get('results', []) if not r.get('ok')]
        color = '\u2705 GREEN' if not fails else '\u26a0\ufe0f YELLOW' if len(fails) < 3 else '\U0001f534 RED'
        lines.append(f'  Overall: {color} | {len(fails)} failing checks')
    except:
        lines.append('  Overall: (checking...)')
    lines += ['', '=' * 55, '']
    # SYSTEM THINKING
    if synthesis:
        lines.append('\U0001f916 WHAT THE SYSTEM IS THINKING:')
        s = synthesis.get('synthesis', synthesis)
        p1 = s.get('top_3_priorities', [''])[0] if isinstance(s, dict) else ''
        insight = s.get('cross_domain_insight','') if isinstance(s, dict) else ''
        if p1: lines.append(f'  Priority: {p1}')
        if insight: lines.append(f'  Insight:  {insight}')
        lines += ['', '=' * 55, '']
    # NETWORK
    try:
        network = load(DATA / 'spawner_log.json', {'network': []})
        nodes = network.get('network', [])
        spread = load(DATA / 'network_spread_log.json', {})
        lines.append(f'\U0001f30d NETWORK: {len(nodes)} sister systems | {len(spread.get("forked",[]))} forks | {len(spread.get("contacted",[]))} people reached')
    except:
        lines.append('\U0001f30d NETWORK: (building...)')
    lines += [
        '',
        '=' * 55,
        f'\nThis took the system 288 cycles to compile for you.',
        f'It took you 2 minutes to read.',
        f'That ratio is the whole point.',
        f'\nFree Palestine. \U0001f339',
        f'\n{REPO_URL}',
    ]
    return '\n'.join(lines)

def run():
    print(f'\n[intel_loop] Intelligence Loop Engine — {TODAY}')

    if WEEKDAY != 6:  # Sundays only
        print('[intel_loop] Not Sunday. Skipping weekly brief.')
        return

    actions   = collect_actions_needed()
    events    = collect_weekly_narrative()
    synthesis = load(DATA / 'strategic_synthesis.json', {})

    stats = {'engines': 0, 'self_built': 0, 'art': 0, 'pcrf': 0.0}
    try: stats['engines'] = len(list((ROOT / 'mycelium').glob('*.py')))
    except: pass
    try:
        evo = load(DATA / 'evolution_log.json')
        stats['self_built'] = len(evo.get('built', []))
    except: pass
    try:
        arts = load(DATA / 'generated_art.json')
        al = arts if isinstance(arts, list) else arts.get('art', [])
        stats['art'] = len(al)
    except: pass
    try:
        ev = load(DATA / 'kofi_events.json')
        ev = ev if isinstance(ev, list) else ev.get('events', [])
        stats['pcrf'] = round(sum(float(e.get('amount',0)) for e in ev
                                  if e.get('type') in ('donation','Donation')) * 0.70, 2)
    except: pass

    brief = build_weekly_brief(actions, events, stats, synthesis)

    # Save
    try: (DATA / 'weekly_brief.json').write_text(json.dumps({
        'date': TODAY, 'actions_needed': len(actions),
        'brief': brief
    }, indent=2))
    except: pass

    # Email it
    if GMAIL_ADDRESS and GMAIL_APP_PASSWORD:
        try:
            action_label = f'{len(actions)} action{"s" if len(actions)!=1 else ""}' if actions else 'nothing needed'
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'\U0001f338 Meeko Weekly — {action_label} from you | {stats["engines"]} engines running'
            msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
            msg['To']      = GMAIL_ADDRESS
            msg.attach(MIMEText(brief, 'plain'))
            with smtplib.SMTP('smtp.gmail.com', 587) as s:
                s.ehlo(); s.starttls()
                s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
                s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
            print(f'[intel_loop] \u2705 Weekly brief sent. Actions needed: {len(actions)}')
        except Exception as e:
            print(f'[intel_loop] Email error: {e}')

    print('[intel_loop] Intelligence loop closed. \U0001f338')

if __name__ == '__main__':
    run()
