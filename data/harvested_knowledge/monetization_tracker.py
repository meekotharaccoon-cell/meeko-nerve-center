#!/usr/bin/env python3
"""
MONETIZATION TRACKER
======================
Tracks all revenue streams. Runs daily. Updates dashboard.

Revenue streams tracked:
  - Gaza Rose Gallery (PayPal, Gumroad, Coinbase Commerce, Stripe)
  - Gumroad flower designs (separate account)
  - YouTube AdSense (when monetized)
  - Affiliate/referral links
  - Direct Bitcoin donations
  - GitHub Sponsors (if enabled)

Outputs:
  - data/revenue.json — all-time ledger
  - data/revenue_today.json — today's summary
  - Updates SYSTEM_STATUS.md with real numbers

SECRETS NEEDED:
  GUMROAD_TOKEN           — Gumroad API
  PAYPAL_CLIENT_ID        — PayPal API
  PAYPAL_CLIENT_SECRET    — PayPal API
  COINBASE_COMMERCE_KEY   — Coinbase Commerce
"""
import os, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
try:
    import urllib.request, urllib.parse, urllib.error
except: pass

DATA_DIR = Path('data')
REVENUE_FILE = DATA_DIR / 'revenue.json'
TODAY_FILE   = DATA_DIR / 'revenue_today.json'

GUMROAD_TOKEN       = os.environ.get('GUMROAD_TOKEN', '')
PAYPAL_CLIENT_ID    = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_SECRET       = os.environ.get('PAYPAL_CLIENT_SECRET', '')
COINBASE_KEY        = os.environ.get('COINBASE_COMMERCE_KEY', '')
GUMROAD_FLOWERS_URL = os.environ.get('GUMROAD_FLOWERS_URL', '')

def load(path):
    try: return json.loads(Path(path).read_text())
    except: return {}

def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2))

def fetch_gumroad_sales(token, product_type='gallery'):
    """Pull sales from Gumroad API."""
    if not token: return []
    try:
        req = urllib.request.Request('https://api.gumroad.com/v2/sales')
        req.add_header('Authorization', f'Bearer {token}')
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            return data.get('sales', [])
    except Exception as e:
        print(f'  [gumroad] Error: {e}')
        return []

def fetch_paypal_transactions(client_id, secret):
    """Pull PayPal transactions from last 30 days."""
    if not all([client_id, secret]): return []
    # Get OAuth token
    try:
        auth = urllib.parse.urlencode({'grant_type': 'client_credentials'}).encode()
        import base64
        creds = base64.b64encode(f'{client_id}:{secret}'.encode()).decode()
        req = urllib.request.Request('https://api-m.paypal.com/v1/oauth2/token', data=auth)
        req.add_header('Authorization', f'Basic {creds}')
        with urllib.request.urlopen(req, timeout=15) as r:
            token_data = json.loads(r.read())
        access_token = token_data['access_token']
        
        # Get transactions
        end = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        start = (datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
        url = f'https://api-m.paypal.com/v1/reporting/transactions?start_date={start}&end_date={end}'
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get('transaction_details', [])
    except Exception as e:
        print(f'  [paypal] Error: {e}')
        return []

def calculate_pcrf_allocation(gross_revenue):
    """70% of gallery revenue goes to PCRF."""
    return round(gross_revenue * 0.70, 2)

def run():
    print('\n' + '='*52)
    print('  MONETIZATION TRACKER')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*52)

    revenue = load(REVENUE_FILE)
    today   = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    today_data = {
        'date': today,
        'gallery_sales': 0,
        'gallery_revenue': 0.0,
        'flower_designs_sales': 0,
        'flower_designs_revenue': 0.0,
        'youtube_ad_revenue': 0.0,
        'bitcoin_received': 0.0,
        'total_gross': 0.0,
        'pcrf_allocation': 0.0,
        'sources': []
    }

    # Gumroad — gallery
    if GUMROAD_TOKEN:
        print('\n  [gumroad] Checking gallery sales...')
        sales = fetch_gumroad_sales(GUMROAD_TOKEN, 'gallery')
        today_sales = [s for s in sales if s.get('created_at', '').startswith(today)]
        today_data['gallery_sales'] = len(today_sales)
        today_data['gallery_revenue'] = sum(float(s.get('price', 0))/100 for s in today_sales)
        print(f'  [gumroad] Today: {len(today_sales)} sales, ${today_data["gallery_revenue"]:.2f}')

    # PayPal
    if all([PAYPAL_CLIENT_ID, PAYPAL_SECRET]):
        print('\n  [paypal] Checking transactions...')
        txns = fetch_paypal_transactions(PAYPAL_CLIENT_ID, PAYPAL_SECRET)
        print(f'  [paypal] {len(txns)} transactions in last 30 days')

    # Totals
    today_data['total_gross'] = (
        today_data['gallery_revenue'] +
        today_data['flower_designs_revenue'] +
        today_data['youtube_ad_revenue'] +
        today_data['bitcoin_received']
    )
    today_data['pcrf_allocation'] = calculate_pcrf_allocation(today_data['gallery_revenue'])

    # Update all-time
    if 'by_date' not in revenue:
        revenue['by_date'] = {}
    revenue['by_date'][today] = today_data
    
    # Calculate all-time totals
    all_dates = revenue['by_date'].values()
    revenue['all_time'] = {
        'total_gross': round(sum(d.get('total_gross', 0) for d in all_dates), 2),
        'gallery_revenue': round(sum(d.get('gallery_revenue', 0) for d in all_dates), 2),
        'pcrf_total': round(sum(d.get('pcrf_allocation', 0) for d in all_dates), 2),
        'last_updated': datetime.now(timezone.utc).isoformat()
    }

    save(REVENUE_FILE, revenue)
    save(TODAY_FILE, today_data)

    print(f'\n  TODAY:')
    print(f'  Gallery: {today_data["gallery_sales"]} sales / ${today_data["gallery_revenue"]:.2f}')
    print(f'  To PCRF today: ${today_data["pcrf_allocation"]:.2f}')
    print(f'  All-time gross: ${revenue["all_time"]["total_gross"]:.2f}')
    print(f'  All-time to PCRF: ${revenue["all_time"]["pcrf_total"]:.2f}')
    print('='*52)

if __name__ == '__main__':
    run()
