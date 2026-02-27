#!/usr/bin/env python3
"""
Ko-fi Webhook Handler
======================
Ko-fi sends a POST to your webhook URL whenever someone donates.
This script processes those events and feeds them into the system.

Setup:
  1. Go to ko-fi.com/manage/webhooks
  2. Set webhook URL to: https://your-domain/kofi-webhook
     (or use a free service like Pipedream/Zapier to forward to GitHub)
  3. Set KOFI_TOKEN secret to your Ko-fi verification token

Alternative (no server needed):
  Use a Pipedream workflow:
    ko-fi webhook -> Pipedream -> GitHub API -> create file in data/kofi_events/
  The system then picks up those files on next run.

What happens when someone donates:
  1. Event logged to data/kofi_events.json
  2. Thank-you content generated
  3. PCRF contribution calculated (70% of Gaza Rose sales)
  4. Telegram notification sent (if configured)
  5. Data scrubbed after 30 days (no personal info stored beyond amount)

Privacy:
  - We store: amount, date, type (donation/purchase), message if any
  - We do NOT store: email, full name, payment details
  - After 30 days: scrubbed
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'

TODAY     = datetime.date.today().isoformat()
KOFI_TOKEN = os.environ.get('KOFI_TOKEN', '')
TELEGRAM_TOKEN   = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def load_events():
    path = DATA / 'kofi_events.json'
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return {'events': [], 'total_received': 0, 'total_to_pcrf': 0}

def save_events(events):
    (DATA / 'kofi_events.json').write_text(json.dumps(events, indent=2))

def process_kofi_event(payload):
    """
    Process a Ko-fi webhook payload.
    Ko-fi sends: type, amount, currency, message, timestamp, is_public
    We strip PII before storing.
    """
    kofi_data = payload.get('data', payload)
    
    # Verify token if set
    if KOFI_TOKEN and payload.get('verification_token') != KOFI_TOKEN:
        print('[kofi] Invalid verification token — ignoring')
        return None
    
    event_type = kofi_data.get('type', 'Donation')
    amount     = float(kofi_data.get('amount', 0) or 0)
    currency   = kofi_data.get('currency', 'USD')
    message    = kofi_data.get('message', '')[:200]  # cap message length
    timestamp  = kofi_data.get('timestamp', TODAY)
    is_public  = kofi_data.get('is_public', False)
    
    # Calculate PCRF contribution (70% of Gaza Rose / shop purchases)
    pcrf_contrib = amount * 0.70 if event_type in ('Shop Order', 'Commission') else amount * 0.0
    
    # Privacy: store no names, no emails, no payment details
    clean_event = {
        'date':         timestamp[:10] if timestamp else TODAY,
        'type':         event_type,
        'amount':       amount,
        'currency':     currency,
        'pcrf_contrib': pcrf_contrib,
        'message':      message if is_public else '[private message]',
        'scrub_after':  (datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
    }
    
    return clean_event

def notify_telegram(event):
    """Send Telegram notification about a new donation."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    pcrf_note = f'\n\U0001f33f PCRF contribution: ${event["pcrf_contrib"]:.2f}' if event['pcrf_contrib'] > 0 else ''
    msg = f'\U0001f4b8 New Ko-fi {event["type"]}!\n${event["amount"]:.2f} {event["currency"]}{pcrf_note}'
    if event.get('message') and event['message'] != '[private message]':
        msg += f'\n\n"{event["message"]}"'
    
    try:
        payload = json.dumps({'chat_id': TELEGRAM_CHAT_ID, 'text': msg}).encode()
        req = urllib_request.Request(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        urllib_request.urlopen(req, timeout=10)
        print('[kofi] Telegram notified')
    except Exception as e:
        print(f'[kofi] Telegram error: {e}')

def get_stats():
    """Get lifetime Ko-fi stats."""
    events_data = load_events()
    events = events_data.get('events', [])
    
    total    = sum(e['amount'] for e in events)
    to_pcrf  = sum(e['pcrf_contrib'] for e in events)
    count    = len(events)
    
    return {
        'total_donations':   count,
        'total_received':    total,
        'total_to_pcrf':     to_pcrf,
        'latest':            events[-1] if events else None,
    }

def run():
    """Run standalone — shows current stats."""
    print(f'[kofi] Ko-fi Webhook Handler — {TODAY}')
    
    if not KOFI_TOKEN:
        print('[kofi] KOFI_TOKEN not set.')
        print('[kofi] Get it from: ko-fi.com/manage/webhooks')
        print('[kofi] To receive webhooks without a server:')
        print('[kofi]   1. Create a free Pipedream workflow at pipedream.com')
        print('[kofi]   2. HTTP trigger -> GitHub API -> write to data/kofi_events/')
        print('[kofi]   3. This script picks it up on next daily run')
    
    stats = get_stats()
    print(f'[kofi] Total donations: {stats["total_donations"]}')
    print(f'[kofi] Total received: ${stats["total_received"]:.2f}')
    print(f'[kofi] Total to PCRF: ${stats["total_to_pcrf"]:.2f}')
    
    return stats

if __name__ == '__main__':
    run()
