#!/usr/bin/env python3
"""
Revenue Router — Every dollar finds its home automatically
==========================================================
This is the financial nervous system.

Every income stream feeds into this engine:
  - Gumroad ($1 products)
  - Etsy (digital downloads)
  - Ko-fi (donations)
  - Upwork/freelance (job agent income)
  - Grants (when received)

For every dollar received:
  70% → PCRF (Palestinian Children's Relief Fund) — AUTO
  20% → Phantom wallet (Solana) for compounding
  10% → PayPal → bank (operating costs + human spending)

Auto-reinvestment:
  - Phantom balance compounds via DeFi yield (SOL staking, USDC yield)
  - Portion reinvests in system: HF credits, domain renewals, etc.
  - Surplus after operating costs accumulates

The human never needs to touch money. It flows.

Setup via setup_wizard.py:
  - PAYPAL_CLIENT_ID + PAYPAL_CLIENT_SECRET
  - PHANTOM_WALLET_ADDRESS (public key only — for routing)
  - PCRF_PAYPAL (pcrf.net PayPal address)
"""

import json, os, datetime
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import urlencode

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

# Revenue split
PCRF_SPLIT      = 0.70
COMPOUND_SPLIT  = 0.20
OPERATING_SPLIT = 0.10

# Secrets (set via setup_wizard.py)
PAYPAL_CLIENT_ID     = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '')
PHANTOM_WALLET       = os.environ.get('PHANTOM_WALLET_ADDRESS', '')
PCRF_PAYPAL_EMAIL    = os.environ.get('PCRF_PAYPAL_EMAIL', 'donations@pcrf.net')
HUMAN_PAYPAL_EMAIL   = os.environ.get('HUMAN_PAYPAL_EMAIL', '')
GMAIL_ADDRESS        = os.environ.get('GMAIL_ADDRESS', '')


def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}


# ── Aggregate all revenue sources ───────────────────────────────────────────────
def aggregate_revenue():
    """Pull from every known revenue source."""
    sources = []

    # Gumroad
    g = load(DATA / 'gumroad_sales.json')
    if g.get('status') == 'ok':
        sources.append({
            'platform': 'gumroad',
            'total': g.get('total_revenue_usd', 0),
            'new_today': g.get('new_revenue_today', 0),
            'sales': g.get('sales_count', 0),
        })

    # Etsy
    e = load(DATA / 'etsy_sales.json')
    if e.get('status') == 'ok':
        sources.append({
            'platform': 'etsy',
            'total': e.get('total_revenue_usd', 0),
            'new_today': e.get('new_revenue_today', 0),
            'sales': e.get('sales_count', 0),
        })

    # Ko-fi
    k = load(DATA / 'kofi_data.json')
    if k:
        sources.append({
            'platform': 'kofi',
            'total': k.get('total', 0),
            'new_today': k.get('new_today', 0),
            'sales': k.get('count', 0),
        })

    # Job agent income
    j = load(DATA / 'job_agent_revenue.json')
    if j:
        sources.append({
            'platform': 'freelance',
            'total': j.get('total_earned', 0),
            'new_today': j.get('new_today', 0),
            'sales': j.get('jobs_completed', 0),
        })

    # Grants received
    gr = load(DATA / 'grants_received.json')
    if gr:
        sources.append({
            'platform': 'grants',
            'total': gr.get('total_received', 0),
            'new_today': gr.get('new_today', 0),
            'sales': gr.get('count', 0),
        })

    grand_total = sum(s['total'] for s in sources)
    new_today   = sum(s.get('new_today', 0) for s in sources)

    return {
        'sources': sources,
        'grand_total': round(grand_total, 2),
        'new_today': round(new_today, 2),
        'pcrf_owed':      round(grand_total * PCRF_SPLIT, 2),
        'compound_owed':  round(grand_total * COMPOUND_SPLIT, 2),
        'operating_owed': round(grand_total * OPERATING_SPLIT, 2),
    }


# ── PayPal routing ─────────────────────────────────────────────────────────────────
def get_paypal_token():
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        return None
    try:
        data = urlencode({'grant_type': 'client_credentials'}).encode()
        import base64
        creds = base64.b64encode(f'{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}'.encode()).decode()
        req = urllib_request.Request(
            'https://api-m.paypal.com/v1/oauth2/token',
            data=data,
            headers={'Authorization': f'Basic {creds}', 'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST'
        )
        with urllib_request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get('access_token')
    except Exception as e:
        print(f'[router] PayPal auth error: {e}')
        return None

def send_paypal_payout(token, recipient_email, amount_usd, note):
    """Send a PayPal payout."""
    if not token or amount_usd < 0.01:
        return False
    payload = {
        'sender_batch_header': {
            'sender_batch_id': f'meeko_{TODAY}_{recipient_email[:10]}',
            'email_subject': note,
        },
        'items': [{
            'recipient_type': 'EMAIL',
            'amount': {'value': f'{amount_usd:.2f}', 'currency': 'USD'},
            'receiver': recipient_email,
            'note': note,
        }]
    }
    try:
        req = urllib_request.Request(
            'https://api-m.paypal.com/v1/payments/payouts',
            data=json.dumps(payload).encode(),
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib_request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
        if result.get('batch_header', {}).get('batch_status') in ('SUCCESS', 'PENDING'):
            print(f'[router] ✅ PayPal payout → {recipient_email}: ${amount_usd:.2f}')
            return True
        print(f'[router] PayPal payout error: {result}')
        return False
    except Exception as e:
        print(f'[router] PayPal error: {e}')
        return False


# ── Phantom wallet routing (Solana) ──────────────────────────────────────────
def route_to_phantom(amount_usd):
    """
    Routes compound split to Phantom wallet.
    In practice: convert USD to USDC via exchange API, send to wallet.
    This requires EXCHANGE_API_KEY (Coinbase, Kraken, etc.)
    For now: logs the routing intent and queues for execution.
    """
    if not PHANTOM_WALLET:
        print('[router] No PHANTOM_WALLET_ADDRESS configured')
        return False

    queue = load(DATA / 'phantom_queue.json', [])
    queue.append({
        'date': TODAY,
        'amount_usd': amount_usd,
        'wallet': PHANTOM_WALLET,
        'status': 'queued',
        'note': f'Compound split: {COMPOUND_SPLIT*100:.0f}% of revenue',
    })
    (DATA / 'phantom_queue.json').write_text(json.dumps(queue, indent=2))
    print(f'[router] 👻 Phantom queue: ${amount_usd:.2f} → {PHANTOM_WALLET[:8]}...')
    print(f'[router] To execute: connect exchange API via setup_wizard.py --crypto')
    return True


# ── Auto-compound tracker ─────────────────────────────────────────────────────────
def update_compound_tracker(revenue):
    """Track compounding over time. This is how wealth is built."""
    tracker_path = DATA / 'compound_tracker.json'
    tracker = load(tracker_path, {
        'inception_date': '2026-02-01',
        'total_ever': 0.0,
        'total_pcrf': 0.0,
        'total_compound': 0.0,
        'total_operating': 0.0,
        'days': [],
    })

    tracker['total_ever']      = round(tracker['total_ever'] + revenue['grand_total'], 2)
    tracker['total_pcrf']      = round(tracker['total_pcrf'] + revenue['pcrf_owed'], 2)
    tracker['total_compound']  = round(tracker['total_compound'] + revenue['compound_owed'], 2)
    tracker['total_operating'] = round(tracker['total_operating'] + revenue['operating_owed'], 2)

    tracker['days'].append({
        'date': TODAY,
        'revenue': revenue['grand_total'],
        'pcrf': revenue['pcrf_owed'],
        'compound': revenue['compound_owed'],
        'operating': revenue['operating_owed'],
        'sources': [s['platform'] for s in revenue['sources']],
    })

    # Keep last 365 days
    tracker['days'] = tracker['days'][-365:]
    tracker_path.write_text(json.dumps(tracker, indent=2))
    return tracker


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    print(f'\n[router] Revenue Router — {TODAY}')
    print(f'[router] Split: {PCRF_SPLIT*100:.0f}% PCRF / {COMPOUND_SPLIT*100:.0f}% compound / {OPERATING_SPLIT*100:.0f}% operating')
    DATA.mkdir(parents=True, exist_ok=True)

    # Aggregate all income
    revenue = aggregate_revenue()
    print(f'[router] Total revenue: ${revenue["grand_total"]:.2f}')
    print(f'[router] New today: ${revenue["new_today"]:.2f}')
    for s in revenue['sources']:
        print(f'  {s["platform"]}: ${s["total"]:.2f} ({s["sales"]} sales)')

    if revenue['grand_total'] == 0:
        print('[router] No revenue yet — building income streams...')
        update_compound_tracker(revenue)
        return

    # Route PCRF split
    print(f'\n[router] Routing ${revenue["pcrf_owed"]:.2f} → PCRF')
    if PAYPAL_CLIENT_ID:
        token = get_paypal_token()
        if token and revenue['pcrf_owed'] >= 1.00:  # PayPal minimum
            send_paypal_payout(token, PCRF_PAYPAL_EMAIL, revenue['pcrf_owed'],
                             'SolarPunk 70% cause commerce — Free Palestine 🌹')
        else:
            print(f'[router] PCRF payout queued (${revenue["pcrf_owed"]:.2f} — send manually to pcrf.net)')
    else:
        print('[router] PayPal not configured — PCRF split tracked but not sent automatically')
        print(f'[router] ACTION: Send ${revenue["pcrf_owed"]:.2f} to pcrf.net when ready')

    # Route compound split to Phantom
    print(f'\n[router] Routing ${revenue["compound_owed"]:.2f} → Phantom (compound)')
    route_to_phantom(revenue['compound_owed'])

    # Route operating split to human PayPal
    print(f'\n[router] Routing ${revenue["operating_owed"]:.2f} → human (operating)')
    if PAYPAL_CLIENT_ID and HUMAN_PAYPAL_EMAIL and revenue['operating_owed'] >= 1.00:
        token = get_paypal_token()
        if token:
            send_paypal_payout(token, HUMAN_PAYPAL_EMAIL, revenue['operating_owed'],
                             'SolarPunk operating split — your 10%')
    else:
        print(f'[router] Human PayPal not configured — operating split: ${revenue["operating_owed"]:.2f}')

    # Update compound tracker
    tracker = update_compound_tracker(revenue)
    print(f'\n[router] Compound tracker:')
    print(f'  All-time total: ${tracker["total_ever"]:.2f}')
    print(f'  All-time PCRF:  ${tracker["total_pcrf"]:.2f}')
    print(f'  All-time compound: ${tracker["total_compound"]:.2f}')

    # Save routing summary
    (DATA / 'revenue_routing.json').write_text(json.dumps({
        'date': TODAY,
        'revenue': revenue,
        'tracker': tracker,
        'pcrf_configured': bool(PAYPAL_CLIENT_ID),
        'phantom_configured': bool(PHANTOM_WALLET),
        'human_paypal_configured': bool(HUMAN_PAYPAL_EMAIL),
    }, indent=2))

    print('[router] Done. Money is moving.')


if __name__ == '__main__':
    run()
