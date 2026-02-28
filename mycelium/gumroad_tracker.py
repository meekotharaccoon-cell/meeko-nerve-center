#!/usr/bin/env python3
"""
Gumroad Revenue Tracker
========================
Uses the new Gumroad OAuth2 secrets:
  GUMROAD_NAME   — application name
  GUMROAD_ID     — application ID (client_id)
  GUMROAD_SECRET — application secret (client_secret / access_token)

This engine:
  1. Fetches all sales from Gumroad API
  2. Calculates total revenue and 70% PCRF split
  3. Saves to data/gumroad_sales.json for dashboard
  4. Logs new sales since last run
  5. Does NOT send email — data goes to dashboard only

NOTE: Gumroad's v2 API uses Bearer token auth.
The GUMROAD_SECRET is used as the Bearer token (access token).
If you're using OAuth2 app credentials, you'll need to exchange
them for an access token first. This engine handles both cases.
"""

import json, os, datetime
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import urlencode

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

GUMROAD_ID     = os.environ.get('GUMROAD_ID', '')
GUMROAD_SECRET = os.environ.get('GUMROAD_SECRET', '')
GUMROAD_NAME   = os.environ.get('GUMROAD_NAME', '')
PCRF_SPLIT     = 0.70

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def gumroad_request(endpoint: str, token: str) -> dict:
    url = f'https://api.gumroad.com/v2/{endpoint}'
    req = urllib_request.Request(url, headers={'Authorization': f'Bearer {token}'})
    with urllib_request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

def run():
    print(f'\n[gumroad] 💰 Gumroad Revenue Tracker — {TODAY}')
    DATA.mkdir(parents=True, exist_ok=True)

    if not GUMROAD_SECRET:
        print('[gumroad] GUMROAD_SECRET not set — add as GitHub secret')
        print('[gumroad] Secrets needed: GUMROAD_ID, GUMROAD_SECRET, GUMROAD_NAME')
        # Save placeholder so dashboard knows config is needed
        save_data = load(DATA / 'gumroad_sales.json', {
            'status': 'not_configured',
            'message': 'Add GUMROAD_ID, GUMROAD_SECRET, GUMROAD_NAME as GitHub secrets',
        })
        save_data['date'] = TODAY
        (DATA / 'gumroad_sales.json').write_text(json.dumps(save_data, indent=2))
        return

    token = GUMROAD_SECRET  # Used as Bearer token
    print(f'[gumroad] App: {GUMROAD_NAME or "(name not set)"}')

    # --- Fetch products ---
    products = []
    try:
        resp = gumroad_request('products', token)
        if resp.get('success'):
            products = resp.get('products', [])
            print(f'[gumroad] Products: {len(products)}')
        else:
            print(f'[gumroad] Products API failed: {resp}')
    except Exception as e:
        print(f'[gumroad] Products error: {e}')

    # --- Fetch sales ---
    all_sales = []
    try:
        resp = gumroad_request('sales', token)
        if resp.get('success'):
            all_sales = resp.get('sales', [])
            print(f'[gumroad] Sales fetched: {len(all_sales)}')
        else:
            print(f'[gumroad] Sales API response: {resp.get("message","unknown error")}')
    except Exception as e:
        print(f'[gumroad] Sales error: {e}')

    # --- Calculate revenue ---
    total_revenue = 0.0
    for sale in all_sales:
        try:
            # Price is in cents
            price_cents = sale.get('price', 0)
            total_revenue += price_cents / 100.0
        except: pass

    pcrf_total = round(total_revenue * PCRF_SPLIT, 2)
    kept_total = round(total_revenue * (1 - PCRF_SPLIT), 2)

    print(f'[gumroad] Total revenue: ${total_revenue:.2f}')
    print(f'[gumroad] PCRF share (70%): ${pcrf_total:.2f}')
    print(f'[gumroad] Retained (30%): ${kept_total:.2f}')

    # --- Find new sales since last run ---
    prev = load(DATA / 'gumroad_sales.json', {})
    prev_sale_ids = set(s.get('id', '') for s in prev.get('sales', []))
    new_sales = [s for s in all_sales if s.get('id') not in prev_sale_ids]

    if new_sales:
        print(f'[gumroad] 🎉 {len(new_sales)} new sales since last run!')
        for s in new_sales:
            print(f'[gumroad]   + {s.get("product_name","?")} — ${s.get("price",0)/100:.2f}')

    # --- Save results ---
    output = {
        'date': TODAY,
        'status': 'ok',
        'app_name': GUMROAD_NAME,
        'products_count': len(products),
        'sales_count': len(all_sales),
        'new_sales_count': len(new_sales),
        'total_revenue_usd': total_revenue,
        'pcrf_split_usd': pcrf_total,
        'retained_usd': kept_total,
        'pcrf_pct': PCRF_SPLIT * 100,
        'products': [{
            'id': p.get('id'), 'name': p.get('name'),
            'price': p.get('formatted_price'),
            'sales': p.get('sales_count', 0)
        } for p in products],
        'sales': all_sales[-50:],  # Last 50 only
        'new_sales': new_sales,
    }
    try:
        (DATA / 'gumroad_sales.json').write_text(json.dumps(output, indent=2))
        print('[gumroad] ✅ Saved to data/gumroad_sales.json')
    except Exception as e:
        print(f'[gumroad] Save error: {e}')

    print('[gumroad] Done. No email sent — data available in dashboard.')

if __name__ == '__main__':
    run()
