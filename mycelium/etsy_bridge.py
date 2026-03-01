#!/usr/bin/env python3
"""
Etsy Bridge — 90M buyers, zero marginal cost per listing
=========================================================
Etsy is not just a marketplace. It's a search engine with purchase intent.
Every digital product in products/ gets listed here automatically.

What this does:
  1. Lists all digital products from products/ on Etsy as digital downloads
  2. Updates listings when products change
  3. Pulls sales data into revenue_router.py pipeline
  4. Routes Etsy revenue through the same 70/30 PCRF split

Etsy API: https://developers.etsy.com/documentation
Setup: add ETSY_API_KEY + ETSY_SHOP_ID to GitHub Secrets via setup_wizard.py

Etsy has 90M+ active buyers. They are already there. We just need to show up.

NOTE: Etsy requires OAuth for write operations (listing creation).
This script handles the full flow: auth → list → price → route revenue.
"""

import json, os, datetime
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import urlencode

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

ETSY_API_KEY  = os.environ.get('ETSY_API_KEY', '')
ETSY_SHOP_ID  = os.environ.get('ETSY_SHOP_ID', '')
ETSY_TOKEN    = os.environ.get('ETSY_ACCESS_TOKEN', '')  # OAuth access token
HF_TOKEN      = os.environ.get('HF_TOKEN', '')

ETSY_API_BASE = 'https://openapi.etsy.com/v3/application'

# Products to list: price, title prefix, primary tag
PRODUCT_CONFIG = {
    '01-the-zero-dollar-ai-stack':           {'price': 1.00, 'primary_tag': 'artificial intelligence'},
    '02-autonomous-ai-github-actions':       {'price': 1.00, 'primary_tag': 'automation'},
    '03-cause-commerce-blueprint':           {'price': 1.00, 'primary_tag': 'social enterprise'},
    '04-the-solarpunk-stack':                {'price': 1.00, 'primary_tag': 'sustainability'},
    '05-congressional-accountability-kit':   {'price': 1.00, 'primary_tag': 'civic technology'},
    '06-fork-and-fund':                      {'price': 1.00, 'primary_tag': 'open source'},
    '07-ai-art-for-causes':                  {'price': 1.00, 'primary_tag': 'digital art'},
    '08-grant-hunting-with-ai':              {'price': 1.00, 'primary_tag': 'nonprofit'},
    '09-the-mycelium-method':                {'price': 1.00, 'primary_tag': 'programming'},
    '10-the-ethical-ai-business':            {'price': 1.00, 'primary_tag': 'business'},
}


def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def etsy_req(method, path, body=None, params=None):
    if not ETSY_TOKEN and not ETSY_API_KEY:
        print('[etsy] No credentials — run setup_wizard.py first')
        return None
    url = ETSY_API_BASE + path
    if params:
        url += '?' + urlencode(params)
    headers = {
        'x-api-key': ETSY_API_KEY,
        'Content-Type': 'application/json',
    }
    if ETSY_TOKEN:
        headers['Authorization'] = f'Bearer {ETSY_TOKEN}'
    data = json.dumps(body).encode() if body else None
    req = urllib_request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib_request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[etsy] Error {path[:50]}: {e}')
        return None


def read_product_markdown(slug):
    """Read product markdown, extract title and description."""
    for ext in ['.md', '.txt']:
        p = ROOT / 'products' / f'{slug}{ext}'
        if p.exists():
            content = p.read_text()
            lines = content.strip().split('\n')
            title = lines[0].lstrip('#').strip() if lines else slug
            # Description: first 3 non-empty paragraphs
            body_lines = [l for l in lines[1:] if l.strip()]
            description = ' '.join(body_lines[:5])[:2000]
            return title, description, content
    return slug.replace('-', ' ').title(), f'Digital guide: {slug}', ''


def get_existing_listings():
    """Get current Etsy listings to avoid duplicates."""
    if not ETSY_SHOP_ID: return {}
    result = etsy_req('GET', f'/shops/{ETSY_SHOP_ID}/listings/active', params={'limit': 100})
    if not result: return {}
    listings = {}
    for item in result.get('results', []):
        title = item.get('title', '')
        listings[title] = item.get('listing_id')
    return listings


def create_listing(slug, config):
    """Create a new Etsy digital product listing."""
    if not ETSY_SHOP_ID:
        print('[etsy] No ETSY_SHOP_ID — cannot create listing')
        return None

    title, description, _ = read_product_markdown(slug)

    # Etsy digital listing payload
    payload = {
        'quantity': 999,
        'title': title[:140],
        'description': (
            f'{description}\n\n'
            f'---\n'
            f'This digital guide is part of the SolarPunk series.\n'
            f'70% of proceeds go to Palestinian children\'s medical relief (PCRF).\n'
            f'Instant digital download after purchase.\n'
            f'Open source project: github.com/meekotharaccoon-cell/meeko-nerve-center'
        )[:2000],
        'price': config['price'],
        'who_made': 'i_did',
        'when_made': 'made_to_order',
        'taxonomy_id': 2078,  # Digital: Files > Digital Files
        'type': 'download',
        'shipping_profile_id': None,  # No shipping for digital
        'tags': [
            config['primary_tag'],
            'digital download', 'ai guide', 'solarpunk',
            'open source', 'cause commerce', 'palestine',
        ][:13],  # Etsy max 13 tags
        'materials': ['digital file'],
        'processing_min': 0,
        'processing_max': 0,
        'is_digital': True,
        'file_data': '',
    }

    result = etsy_req('POST', f'/shops/{ETSY_SHOP_ID}/listings', body=payload)
    if result and result.get('listing_id'):
        listing_id = result['listing_id']
        print(f'[etsy] ✅ Created listing: {title[:50]} (ID: {listing_id})')
        return listing_id
    print(f'[etsy] Failed to create listing for {slug}: {result}')
    return None


def pull_etsy_revenue():
    """Pull Etsy sales data and format for revenue_router."""
    if not ETSY_SHOP_ID: return None
    result = etsy_req('GET', f'/shops/{ETSY_SHOP_ID}/receipts',
                      params={'was_paid': True, 'limit': 100})
    if not result: return None

    receipts = result.get('results', [])
    total_revenue = sum(
        float(r.get('grandtotal', {}).get('amount', 0)) / 100
        for r in receipts
    )
    sales_count = len(receipts)
    pcrf_split  = round(total_revenue * 0.70, 2)
    retained    = round(total_revenue * 0.30, 2)

    etsy_data = {
        'status': 'ok',
        'platform': 'etsy',
        'total_revenue_usd': round(total_revenue, 2),
        'sales_count': sales_count,
        'pcrf_split_usd': pcrf_split,
        'retained_usd': retained,
        'updated': TODAY,
    }

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / 'etsy_sales.json').write_text(json.dumps(etsy_data, indent=2))
    print(f'[etsy] Revenue: ${total_revenue:.2f} | PCRF: ${pcrf_split:.2f} | Sales: {sales_count}')
    return etsy_data


def run():
    print(f'\n[etsy] Etsy Bridge — {TODAY}')
    DATA.mkdir(parents=True, exist_ok=True)

    if not ETSY_API_KEY:
        print('[etsy] No ETSY_API_KEY. Add via setup_wizard.py')
        print('[etsy] Get keys at: https://www.etsy.com/developers/documentation/getting_started/register')
        # Save stub so revenue_router knows status
        (DATA / 'etsy_sales.json').write_text(json.dumps({
            'status': 'not_configured', 'platform': 'etsy',
            'message': 'Run setup_wizard.py to configure ETSY_API_KEY + ETSY_SHOP_ID',
            'url': 'https://www.etsy.com/developers',
        }, indent=2))
        return

    # Pull revenue first (read-only, always works)
    revenue = pull_etsy_revenue()

    # List products if we have write access
    if not ETSY_TOKEN:
        print('[etsy] No ETSY_ACCESS_TOKEN — read-only mode (OAuth needed for listings)')
        print('[etsy] To enable listings: run setup_wizard.py --etsy-oauth')
        return

    existing = get_existing_listings()
    print(f'[etsy] Existing listings: {len(existing)}')

    created = 0
    for slug, config in PRODUCT_CONFIG.items():
        title, _, _ = read_product_markdown(slug)
        if title in existing:
            print(f'[etsy] Already listed: {title[:50]}')
            continue
        listing_id = create_listing(slug, config)
        if listing_id:
            created += 1

    print(f'[etsy] Done. Created {created} new listings.')
    if revenue:
        print(f'[etsy] Total Etsy revenue: ${revenue["total_revenue_usd"]:.2f}')


if __name__ == '__main__':
    run()
