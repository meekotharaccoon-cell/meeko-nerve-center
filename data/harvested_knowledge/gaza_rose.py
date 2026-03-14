#!/usr/bin/env python3
"""
Gaza Rose - Enhanced Revenue Tracker with Source Tracking
PCRF: "https://give.pcrf.net/campaign/739651/donate" (70%)
Features: Source tracking, CSV import, batch add, optional webhook server, retry logic
"""

import sqlite3
import urllib.request
import urllib.error
import json
import sys
import os
import csv
import time
from datetime import datetime
from typing import Optional, List, Dict

DB_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "gaza_rose.db")
PCRF = "https://give.pcrf.net/campaign/739651/donate"
ALLOCATION = 0.70

# Optional Flask import
FLASK_AVAILABLE = False
try:
    from flask import Flask, request
    import threading
    FLASK_AVAILABLE = True
except ImportError:
    pass

def fetch_json(url: str, timeout: int = 10, max_retries: int = 3) -> Optional[Dict]:
    """Fetch JSON with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'GazaRose/2.0'})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Rate limited
                wait = 2 ** attempt
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
    return None

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    print("Initializing database...")
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS txs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                revenue_usd REAL NOT NULL,
                btc REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                txid TEXT UNIQUE,
                verified_at TIMESTAMP,
                source TEXT,
                description TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_status ON txs(status);
            CREATE INDEX IF NOT EXISTS idx_source ON txs(source);
            CREATE INDEX IF NOT EXISTS idx_created ON txs(created_at);
        """)
    print("✓ Database ready")

def get_btc_price() -> Optional[float]:
    data = fetch_json("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
    if data and 'bitcoin' in data:
        return data['bitcoin']['usd']
    return None

def add_revenue(usd_amount: float, source: str = "manual", description: str = ""):
    print(f"\nAdding ${usd_amount:.2f} from {source}...")
    price = get_btc_price()
    if not price:
        print("✗ Could not get BTC price")
        return False
    
    btc_amount = round((usd_amount * ALLOCATION) / price, 8)
    
    with db() as conn:
        conn.execute(
            "INSERT INTO txs (revenue_usd, btc, source, description) VALUES (?, ?, ?, ?)",
            (usd_amount, btc_amount, source, description)
        )
        tx_id = conn.lastrowid
    
    print(f"✓ Added: ${usd_amount:.2f} → {btc_amount:.8f} BTC @ ${price:,.0f}")
    print(f"  Source: {source}")
    if description:
        print(f"  Desc: {description}")
    print(f"Payment: bitcoin:{PCRF}?amount={btc_amount}")
    return True

def add_batch(json_file: str):
    """Add multiple transactions from JSON file."""
    print(f"\nProcessing batch from {json_file}...")
    
    try:
        with open(json_file, 'r') as f:
            transactions = json.load(f)
    except Exception as e:
        print(f"✗ Error reading JSON: {e}")
        return False
    
    if not isinstance(transactions, list):
        print("✗ JSON must be a list of transactions")
        return False
    
    price = get_btc_price()
    if not price:
        print("✗ Could not get BTC price")
        return False
    
    added = 0
    failed = 0
    
    with db() as conn:
        for tx in transactions:
            try:
                usd = float(tx.get('amount', 0))
                source = tx.get('source', 'batch')
                desc = tx.get('description', '')
                
                btc = round((usd * ALLOCATION) / price, 8)
                
                conn.execute(
                    "INSERT INTO txs (revenue_usd, btc, source, description) VALUES (?, ?, ?, ?)",
                    (usd, btc, source, desc)
                )
                added += 1
            except Exception as e:
                print(f"  Failed to add transaction: {e}")
                failed += 1
    
    print(f"\n✓ Batch complete: {added} added, {failed} failed")
    print(f"Total to send: {added * ALLOCATION * 100:.0f}% of revenue")
    return True

def import_upwork_csv(csv_file: str):
    """Import Upwork CSV export."""
    print(f"\nImporting Upwork CSV: {csv_file}...")
    
    if not os.path.exists(csv_file):
        print(f"✗ File not found: {csv_file}")
        return False
    
    transactions = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Try common Upwork CSV formats
                amount = None
                date = None
                desc = ""
                
                # Look for amount column
                for col in ['Amount', 'amount', 'Total', 'total', 'Earnings', 'earnings']:
                    if col in row:
                        try:
                            amount = float(row[col])
                            break
                        except:
                            continue
                
                # Look for description
                for col in ['Description', 'description', 'Title', 'title', 'Project', 'project']:
                    if col in row:
                        desc = row[col]
                        break
                
                if amount and amount > 0:
                    transactions.append({
                        'amount': amount,
                        'source': 'Upwork',
                        'description': desc[:100]
                    })
    except Exception as e:
        print(f"✗ Error reading CSV: {e}")
        return False
    
    if not transactions:
        print("No valid transactions found in CSV")
        return False
    
    print(f"Found {len(transactions)} transactions")
    
    # Save to temp JSON and use batch add
    temp_file = "temp_upwork.json"
    with open(temp_file, 'w') as f:
        json.dump(transactions, f)
    
    result = add_batch(temp_file)
    
    try:
        os.remove(temp_file)
    except:
        pass
    
    return result

def check_pending():
    print("\nChecking pending transactions...")
    with db() as conn:
        pending = conn.execute("SELECT * FROM txs WHERE status = 'pending' AND txid IS NOT NULL").fetchall()
    
    if not pending:
        print("No pending transactions")
        return
    
    verified = 0
    for tx in pending:
        data = fetch_json(f"https://blockstream.info/api/tx/{tx['txid']}")
        if data and data.get('status', {}).get('confirmed', False):
            with db() as conn:
                conn.execute("UPDATE txs SET status = 'verified', verified_at = CURRENT_TIMESTAMP WHERE id = ?", (tx['id'],))
            verified += 1
            print(f"✓ Verified: {tx['txid'][:16]}...")
    
    print(f"\nVerified {verified} of {len(pending)} transactions")

def show_status():
    print("\n" + "="*60)
    print("GAZA ROSE - SYSTEM STATUS")
    print("="*60)
    
    with db() as conn:
        overall = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'verified' THEN 1 ELSE 0 END) as verified,
                SUM(revenue_usd) as revenue,
                SUM(btc) as btc
            FROM txs
        """).fetchone()
        
        by_source = conn.execute("""
            SELECT source, COUNT(*) as count, SUM(revenue_usd) as total
            FROM txs
            GROUP BY source
            ORDER BY total DESC
        """).fetchall()
    
    print(f"\nPCRF: {PCRF}")
    print(f"70% FOREVER")
    print(f"\nTotal Revenue: ${overall['revenue'] or 0:.2f} USD")
    print(f"Total BTC:     {overall['btc'] or 0:.8f} BTC")
    print(f"Transactions:  {overall['verified'] or 0}/{overall['total'] or 0} verified")
    
    if by_source:
        print("\nBy Source:")
        for row in by_source:
            if row['source']:
                print(f"  {row['source'][:15]:15} : ${row['total']:8.2f} ({row['count']} tx)")
    
    print("="*60)

def start_webhook_server(port: int = 5000):
    """Start optional Flask webhook server for Stripe/Gumroad."""
    if not FLASK_AVAILABLE:
        print("✗ Flask not installed. Run: pip install flask")
        return False
    
    app = Flask(__name__)
    
    @app.route('/webhook/stripe', methods=['POST'])
    def stripe_webhook():
        event = request.get_json()
        if event and event.get('type') == 'invoice.paid':
            amount = event['data']['object']['amount_paid'] / 100
            customer = event['data']['object'].get('customer_email', 'unknown')
            add_revenue(amount, 'Stripe', f'Subscription from {customer}')
        return '', 200
    
    @app.route('/webhook/gumroad', methods=['POST'])
    def gumroad_webhook():
        data = request.get_json()
        if data and data.get('sale'):
            amount = float(data['sale']['price'])
            product = data['sale'].get('product_name', 'Unknown')
            add_revenue(amount, 'Gumroad', product)
        return '', 200
    
    @app.route('/health', methods=['GET'])
    def health():
        return {'status': 'ok', 'pcrf': PCRF}, 200
    
    def run_server():
        app.run(host='0.0.0.0', port=port, debug=False)
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    print(f"✓ Webhook server started on port {port}")
    print(f"  Stripe: http://localhost:{port}/webhook/stripe")
    print(f"  Gumroad: http://localhost:{port}/webhook/gumroad")
    print(f"  Health: http://localhost:{port}/health")
    print("\nPress Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nServer stopped")

def main():
    if len(sys.argv) < 2:
        print("""Commands:
  init                              Initialize database
  add AMOUNT [source] [desc]        Add revenue with optional source
  batch JSON_FILE                   Add multiple from JSON
  import-upwork CSV_FILE            Import Upwork CSV
  check                             Verify pending transactions
  status                            Show system status
  webhook [PORT]                    Start webhook server (needs Flask)
  verify TXID                       Verify specific transaction""")
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "init":
        init_db()
    elif cmd == "add" and len(sys.argv) > 2:
        amount = float(sys.argv[2])
        source = sys.argv[3] if len(sys.argv) > 3 else "manual"
        desc = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        add_revenue(amount, source, desc)
    elif cmd == "batch" and len(sys.argv) > 2:
        add_batch(sys.argv[2])
    elif cmd == "import-upwork" and len(sys.argv) > 2:
        import_upwork_csv(sys.argv[2])
    elif cmd == "check":
        check_pending()
    elif cmd == "status":
        show_status()
    elif cmd == "webhook":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
        start_webhook_server(port)
    elif cmd == "verify" and len(sys.argv) > 2:
        data = fetch_json(f"https://blockstream.info/api/tx/{sys.argv[2]}")
        if data:
            print(json.dumps(data, indent=2))
            confirmed = data.get('status', {}).get('confirmed', False)
            print(f"\nStatus: {'✓ CONFIRMED' if confirmed else '⏳ PENDING'}")
        else:
            print("Not found")

if __name__ == "__main__":
    main()
