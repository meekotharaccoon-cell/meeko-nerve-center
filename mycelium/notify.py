#!/usr/bin/env python3
"""
Notification Router — writes system alerts to data/system_inbox.json
=====================================================================
REPLACES direct Gmail sending for internal system messages.

Previously scripts like self_healer, grant_intelligence, job_agent were
sending emails to meekotharaccoon@gmail.com for system health reports,
grant drafts, validation failures, etc. This cluttered the inbox and
caused email_gateway to read/process them on the next cycle.

NEW RULE: Internal system messages go to data/system_inbox.json ONLY.
The live dashboard reads this file and displays it.
Gmail is for OUTBOUND replies to real humans only.

Usage:
    from mycelium.notify import notify
    notify('grant_draft', 'NLnet Foundation', {'amount': '$50k', ...})
    notify('system_health', 'Health: 67/100', {'issues': [...]})
    notify('validation_failure', '1 failure', {'details': '...'})
"""

import json, datetime, os
from pathlib import Path

DATA  = Path(__file__).parent.parent / 'data'
TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().isoformat()


def notify(category: str, title: str, payload: dict = None, urgent: bool = False):
    """
    Write a notification to data/system_inbox.json instead of emailing.
    The dashboard reads this. No email noise.
    
    Categories: grant_draft, system_health, validation_failure,
                workflow_fix, job_lead, revenue_update, human_action_required
    """
    DATA.mkdir(parents=True, exist_ok=True)
    p = DATA / 'system_inbox.json'
    try:
        inbox = json.loads(p.read_text()) if p.exists() else {'notifications': []}
    except:
        inbox = {'notifications': []}

    entry = {
        'id':       f'{category}_{NOW}',
        'date':     TODAY,
        'time':     NOW,
        'category': category,
        'title':    title,
        'payload':  payload or {},
        'urgent':   urgent,
        'read':     False,
    }

    inbox.setdefault('notifications', []).append(entry)
    # Keep last 200 notifications
    inbox['notifications'] = inbox['notifications'][-200:]
    inbox['last_updated'] = NOW
    inbox['unread_count'] = sum(1 for n in inbox['notifications'] if not n['read'])

    try:
        p.write_text(json.dumps(inbox, indent=2))
        label = '🚨' if urgent else '📬'
        print(f'[notify] {label} {category}: {title}')
    except Exception as e:
        print(f'[notify] Write error: {e}')


def get_unread(category: str = None) -> list:
    """Read unread notifications, optionally filtered by category."""
    p = DATA / 'system_inbox.json'
    try:
        inbox = json.loads(p.read_text()) if p.exists() else {}
        notes = inbox.get('notifications', [])
        if category:
            notes = [n for n in notes if n.get('category') == category]
        return [n for n in notes if not n.get('read')]
    except:
        return []


def mark_read(category: str = None):
    """Mark notifications as read."""
    p = DATA / 'system_inbox.json'
    try:
        inbox = json.loads(p.read_text()) if p.exists() else {}
        for n in inbox.get('notifications', []):
            if not category or n.get('category') == category:
                n['read'] = True
        inbox['unread_count'] = 0
        p.write_text(json.dumps(inbox, indent=2))
    except:
        pass


if __name__ == '__main__':
    # Test
    notify('system_health', 'Test: System healthy', {'score': 100}, urgent=False)
    print('Notification written to data/system_inbox.json')
    print('Check the dashboard to see it. No email sent.')
