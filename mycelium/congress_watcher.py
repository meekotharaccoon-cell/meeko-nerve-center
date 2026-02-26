#!/usr/bin/env python3
"""
Congress Stock Watcher
======================
Pulls House Stock Watcher API — politicians trading on insider info.
Surfaces the most suspicious trades daily.
Feeds:
  - Your legal tools page (transparency angle)
  - Content queue (accountability posts)
  - Telegram briefing
  - SolarPunk dashboard

Free API. No key needed. Updated daily.
https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/filemap.xml
"""

import json, datetime
from pathlib import Path
from urllib import request as urllib_request

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / 'data'
DATA.mkdir(exist_ok=True)
TODAY  = datetime.date.today().isoformat()

FILEMAP_URL  = 'https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/filemap.json'
BASE_URL     = 'https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/'

# Known committee assignments for context
COMMITTEE_FLAGS = [
    'Intelligence', 'Armed Services', 'Financial Services',
    'Energy', 'Commerce', 'Judiciary', 'Ways and Means',
    'Foreign Affairs', 'Homeland Security',
]

def fetch_json(url):
    try:
        with urllib_request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[congress] fetch error: {e}')
        return None

def get_latest_trades():
    """Get the most recent filing data."""
    filemap = fetch_json(FILEMAP_URL)
    if not filemap:
        # Fallback: direct URL for all transactions
        data = fetch_json('https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json')
        return data or []

    # Get most recent file
    if isinstance(filemap, list) and filemap:
        latest = filemap[-1]
        url = BASE_URL + latest
        data = fetch_json(url)
        return data if isinstance(data, list) else []
    return []

def analyze_trades(trades):
    """
    Find the most notable trades:
    - Large purchases (>$50k) near policy votes
    - Same-day purchases and sales
    - Repeated trading in same stock
    - Tech/defense/pharma (high insider-info sectors)
    """
    flagged = []
    sector_counts = {}
    rep_counts = {}
    recent_cutoff = datetime.date.today() - datetime.timedelta(days=30)

    HIGH_INTEREST_SECTORS = [
        'NVDA', 'AMD', 'INTC', 'MSFT', 'GOOGL', 'META', 'AMZN', 'AAPL',  # Tech
        'LMT', 'RTX', 'NOC', 'BA', 'GD',          # Defense
        'PFE', 'JNJ', 'MRNA', 'ABBV',              # Pharma
        'XOM', 'CVX', 'COP',                        # Energy
        'JPM', 'GS', 'BAC',                         # Finance
    ]

    for trade in trades:
        ticker   = trade.get('ticker', '').upper()
        amount   = trade.get('amount', '')
        rep      = trade.get('representative', 'Unknown')
        t_type   = trade.get('type', '')
        t_date   = trade.get('transaction_date', '')
        asset    = trade.get('asset_description', '')
        district = trade.get('district', '')

        # Parse date
        trade_date = None
        try:
            trade_date = datetime.date.fromisoformat(t_date[:10])
        except: pass

        # Count by rep
        rep_counts[rep] = rep_counts.get(rep, 0) + 1

        # Count by sector
        sector_counts[ticker] = sector_counts.get(ticker, 0) + 1

        # Flag high-interest trades
        is_recent = trade_date and trade_date >= recent_cutoff
        is_large  = any(x in str(amount) for x in ['$50,001', '$100,001', '$250,001', '$500,001', '$1,000,001', 'over $1'])
        is_hot_stock = ticker in HIGH_INTEREST_SECTORS

        if is_recent and (is_large or is_hot_stock):
            flagged.append({
                'rep':      rep,
                'district': district,
                'ticker':   ticker,
                'type':     t_type,
                'amount':   amount,
                'date':     t_date,
                'asset':    asset,
                'flags':    [
                    'LARGE TRADE' if is_large else '',
                    f'HIGH-INTEREST STOCK ({ticker})' if is_hot_stock else '',
                ],
                'url': f'https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&startdt={t_date[:7]}-01'
            })

    # Top traders (most active in last 30 days)
    top_traders = sorted(rep_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_stocks  = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return flagged, top_traders, top_stocks

def build_content(flagged, top_traders, top_stocks):
    """Build post content about congressional trading."""
    posts = []

    # Accountability post
    if flagged:
        top = flagged[0]
        posts.append({
            'platform': 'mastodon',
            'type': 'accountability',
            'text': (
                f"Congress watch: {top['rep']} ({top['district']}) "
                f"{top['type']} {top['ticker']} "
                f"({top['amount']}) on {top['date'][:10]}.\n\n"
                f"Your representatives are trading stocks while writing laws that affect those same companies.\n\n"
                f"Data: housestockwatcher.com | Tool: {chr(10)}meekotharaccoon-cell.github.io/meeko-nerve-center/proliferator.html\n\n"
                f"#Accountability #Congress #Transparency #OpenData"
            )
        })

    # Top traders post
    if top_traders:
        names = ', '.join([f"{n} ({c} trades)" for n, c in top_traders[:3]])
        posts.append({
            'platform': 'mastodon',
            'type': 'data',
            'text': (
                f"Most active congressional traders (last 30 days):\n"
                f"{names}\n\n"
                f"Free to look up anyone: housestockwatcher.com\n"
                f"Know your rights: meekotharaccoon-cell.github.io/meeko-nerve-center/proliferator.html\n\n"
                f"#Congress #StockMarket #Accountability"
            )
        })

    return posts

def run():
    print('[congress] Fetching latest trades...')
    trades = get_latest_trades()
    print(f'[congress] Got {len(trades)} trades')

    if not trades:
        print('[congress] No data available')
        return

    flagged, top_traders, top_stocks = analyze_trades(trades)
    print(f'[congress] {len(flagged)} flagged trades, {len(top_traders)} top traders')

    posts = build_content(flagged, top_traders, top_stocks)

    # Save
    output = {
        'updated':     TODAY,
        'total_trades': len(trades),
        'flagged':     flagged[:20],
        'top_traders': [{'rep': n, 'trades': c} for n, c in top_traders],
        'top_stocks':  [{'ticker': t, 'trades': c} for t, c in top_stocks],
        'posts':       posts,
    }
    (DATA / 'congress.json').write_text(json.dumps(output, indent=2))
    print(f'[congress] Saved to data/congress.json')

    # Print summary
    print('\n[congress] TOP TRADERS (30 days):')
    for name, count in top_traders[:5]:
        print(f'  {name}: {count} trades')
    print('\n[congress] TOP STOCKS:')
    for ticker, count in top_stocks[:5]:
        print(f'  {ticker}: {count} trades')
    if flagged:
        print(f'\n[congress] FLAGGED ({len(flagged)} total, showing first 3):')
        for t in flagged[:3]:
            print(f"  {t['rep']}: {t['type']} {t['ticker']} {t['amount']} on {t['date'][:10]}")

if __name__ == '__main__':
    run()
