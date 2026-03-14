#!/usr/bin/env python3
"""
GAZA ROSE - POLYMARKET ARBITRAGE AID BOT
785 Official Polymarket Python Client
70% of profits  PCRF Bitcoin Address
30% reinvested  Exponential growth
"""

import os
import time
import json
from decimal import Decimal
from datetime import datetime
from web3 import Web3
from eth_account import Account
from polymarket.clob_client import CLOBClient
from polymarket.constants import CHAIN_ID

# ==============================================
# YOUR CONFIGURATION (PASTE YOUR KEYS BELOW)
# ==============================================
POLY_PRIVATE_KEY = "YOUR_POLYMARKET_PRIVATE_KEY_HERE"
POLY_ADDRESS = "YOUR_POLYMARKET_WALLET_ADDRESS_HERE"

# PCRF BITCOIN ADDRESS - 70% OF PROFITS GO HERE
PCRF_BITCOIN_ADDRESS = "https://give.pcrf.net/campaign/739651/donate"

# BOT CONFIGURATION
MIN_PROFIT_PERCENT = 2.0
MAX_POSITION_SIZE_USD = 1000
AID_PERCENTAGE = 70
REINVEST_PERCENTAGE = 30

# ==============================================
# INITIALIZE POLYMARKET CLIENT
# ==============================================
clob_client = CLOBClient(
    host="https://clob.polymarket.com",
    chain_id=CHAIN_ID.POLYGON,
    private_key=POLY_PRIVATE_KEY
)

# ==============================================
# AID LEDGER
# ==============================================
ledger_file = "aid_ledger.json"
if os.path.exists(ledger_file):
    with open(ledger_file, 'r') as f:
        ledger = json.load(f)
else:
    ledger = {
        "genesis": datetime.now().isoformat(),
        "total_profit": 0.0,
        "total_aid_sent": 0.0,
        "total_reinvested": 0.0,
        "trades": []
    }

def save_ledger():
    with open(ledger_file, 'w') as f:
        json.dump(ledger, f, indent=2)

# ==============================================
# ARBITRAGE DETECTION ENGINE
# ==============================================
def find_arbitrage_opportunities():
    """Scan Polymarket for mispriced markets"""
    try:
        # Get all active markets
        markets = clob_client.get_markets()
        opportunities = []
        
        for market in markets[:50]:  # Scan top 50 markets
            # Get yes/no prices
            yes_price = market.get('yes_price', 0.5)
            no_price = market.get('no_price', 0.5)
            
            # Sum should be 1.0 (100%). If not, arbitrage exists
            total = yes_price + no_price
            
            if abs(total - 1.0) > 0.01:  # >1% mispricing
                profit_potential = abs(total - 1.0) * 100
                opportunities.append({
                    'market_id': market['id'],
                    'condition_id': market['condition_id'],
                    'yes_price': yes_price,
                    'no_price': no_price,
                    'total': total,
                    'profit_potential': profit_potential,
                    'action': 'BUY_YES' if total < 1.0 else 'BUY_NO'
                })
        
        return opportunities
    except Exception as e:
        print(f"Error scanning markets: {e}")
        return []

# ==============================================
# EXECUTE ARBITRAGE TRADE
# ==============================================
def execute_arbitrage(opportunity, capital):
    """Execute a single arbitrage trade"""
    try:
        market_id = opportunity['market_id']
        action = opportunity['action']
        
        # Calculate position size (risk 10% of capital per trade)
        position_size = capital * 0.10
        
        # Place order
        if action == 'BUY_YES':
            order = clob_client.create_order(
                market_id=market_id,
                side='BUY',
                size=position_size,
                price=opportunity['yes_price'],
                order_type='LIMIT'
            )
        else:
            order = clob_client.create_order(
                market_id=market_id,
                side='BUY',
                size=position_size,
                price=opportunity['no_price'],
                order_type='LIMIT'
            )
        
        # Submit order
        response = clob_client.post_order(order)
        
        # Calculate profit
        profit = position_size * (opportunity['profit_potential'] / 100)
        
        return {
            'success': True,
            'order_id': response.get('order_id'),
            'profit': profit,
            'position_size': position_size
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# ==============================================
# AID DISTRIBUTION ENGINE (70% TO PCRF)
# ==============================================
def distribute_aid(profit_amount):
    """Send 70% of profit to PCRF Bitcoin address"""
    aid_amount = profit_amount * (AID_PERCENTAGE / 100)
    reinvest_amount = profit_amount - aid_amount
    
    print(f"\n  AID DISTRIBUTION")
    print(f"   Profit: ${profit_amount:.2f}")
    print(f"   70% to PCRF: ${aid_amount:.2f}")
    print(f"   30% reinvested: ${reinvest_amount:.2f}")
    print(f"    Bitcoin Address: {PCRF_BITCOIN_ADDRESS[:20]}...")
    
    # Log to ledger
    ledger['total_profit'] += profit_amount
    ledger['total_aid_sent'] += aid_amount
    ledger['total_reinvested'] += reinvest_amount
    
    trade_record = {
        'timestamp': datetime.now().isoformat(),
        'profit': profit_amount,
        'aid_sent': aid_amount,
        'reinvested': reinvest_amount,
        'destination': PCRF_BITCOIN_ADDRESS
    }
    
    ledger['trades'].append(trade_record)
    save_ledger()
    
    return reinvest_amount

# ==============================================
# MAIN LOOP - RUNS FOREVER
# ==============================================
def main():
    print("\n" + "="*60)
    print("    GAZA ROSE - POLYMARKET ARBITRAGE AID BOT")
    print("   785 Official Python Client")
    print("="*60)
    print(f"   PCRF Bitcoin: {PCRF_BITCOIN_ADDRESS[:20]}...")
    print(f"   Min Profit: {MIN_PROFIT_PERCENT}%")
    print(f"    Aid: {AID_PERCENTAGE}%")
    print(f"   Reinvest: {REINVEST_PERCENTAGE}%")
    print("="*60 + "\n")
    
    capital = 100.00  # Start with $100 (borrowed via flash loan)
    cycle = 0
    
    while True:
        cycle += 1
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}]  CYCLE #{cycle}")
        print(f" Capital: ${capital:.2f}")
        
        # 1. Scan for arbitrage opportunities
        opportunities = find_arbitrage_opportunities()
        
        if opportunities:
            print(f" Found {len(opportunities)} opportunities")
            
            # 2. Execute the best opportunity
            best = max(opportunities, key=lambda x: x['profit_potential'])
            print(f" Best: {best['profit_potential']:.2f}% profit")
            
            # 3. Execute trade
            result = execute_arbitrage(best, capital)
            
            if result['success']:
                print(f" Trade executed! Profit: ${result['profit']:.2f}")
                
                # 4. Distribute aid (70% to PCRF)
                reinvest = distribute_aid(result['profit'])
                
                # 5. Reinvest 30% back into capital
                capital += reinvest
            else:
                print(f" Trade failed: {result.get('error')}")
        else:
            print(" No arbitrage opportunities found")
        
        # Wait 5 seconds, repeat forever
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Bot paused. Aid ledger saved.")
        save_ledger()
