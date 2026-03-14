"""
WATCHLIST MONITOR
==================
Runs in the background. Watches your symbols, detects opportunities,
queues AI analysis automatically. YOU still approve everything.

Runs every hour during market hours (Mon-Fri 9:30am-4pm ET for stocks,
24/7 for crypto).

Configure your watchlist below.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))

BASE = Path(r'C:\Users\meeko\Desktop\TRADING_SYSTEM')

# ── YOUR WATCHLIST — edit this ────────────────────────────
STOCK_WATCHLIST = [
    'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN',
    'SPY', 'QQQ',   # ETFs — diversified exposure
]
CRYPTO_WATCHLIST = [
    'BTC-USD', 'ETH-USD', 'SOL-USD',
]
# Full watchlist — analyst runs through all of these
WATCHLIST = STOCK_WATCHLIST + CRYPTO_WATCHLIST

# How often to run analysis (seconds)
STOCK_INTERVAL  = 3600   # 1 hour during market hours
CRYPTO_INTERVAL = 7200   # 2 hours (crypto never sleeps)

ET = ZoneInfo('America/New_York')


def is_market_hours():
    now = datetime.now(ET)
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    market_open  = now.replace(hour=9,  minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0,  second=0, microsecond=0)
    return market_open <= now <= market_close


def run_cycle():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"\n[{ts}] Watchlist monitor cycle")

    try:
        from ai_analyst import AIAnalyst
        analyst = AIAnalyst()

        # Always analyze crypto (24/7 market)
        crypto_symbols = [s for s in WATCHLIST if '-' in s]
        if crypto_symbols:
            print(f"  Analyzing crypto: {crypto_symbols}")
            analyst.analyze_watchlist(crypto_symbols)

        # Analyze stocks only during market hours
        stock_symbols = [s for s in WATCHLIST if '-' not in s]
        if stock_symbols and is_market_hours():
            print(f"  Analyzing stocks: {stock_symbols}")
            analyst.analyze_watchlist(stock_symbols)
        elif stock_symbols:
            print(f"  Market closed — skipping stocks until 9:30am ET")

        # Save monitor heartbeat
        snap = BASE / 'data' / 'monitor_status.json'
        with open(snap, 'w') as f:
            json.dump({
                'last_run': datetime.now().isoformat(),
                'market_hours': is_market_hours(),
                'watchlist': WATCHLIST,
            }, f, indent=2)

    except Exception as e:
        print(f"  ERROR in watchlist cycle: {e}")
        log = BASE / 'logs' / f"monitor_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] ERROR: {e}\n")


if __name__ == '__main__':
    print("\n" + "="*50)
    print("  WATCHLIST MONITOR — running")
    print(f"  Stocks: {STOCK_WATCHLIST}")
    print(f"  Crypto: {CRYPTO_WATCHLIST}")
    print("  Ctrl+C to stop")
    print("="*50)

    # Run immediately on start, then on interval
    run_cycle()

    while True:
        interval = CRYPTO_INTERVAL
        print(f"  Next check in {interval//60} minutes...")
        time.sleep(interval)
        run_cycle()
