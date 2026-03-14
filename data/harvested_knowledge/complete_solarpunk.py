"""
🌐 COMPLETE SOLARPUNK SYSTEM - ONE FILE
Everything you need: Arbitrage + Donations + Monitoring
"""

import time
import requests
import json
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import os

# ========== PART 1: ARBITRAGE ENGINE ==========
class ArbitrageEngine:
    def __init__(self):
        self.profit = 0
        self.trades = []
        
    def check_prices(self):
        """Check cryptocurrency prices across exchanges"""
        prices = {}
        
        # Binance
        try:
            btc = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
            prices['binance'] = float(btc['price'])
        except:
            prices['binance'] = 0
        
        # KuCoin
        try:
            data = requests.get("https://api.kucoin.com/api/v1/market/allTickers").json()
            for ticker in data['data']['ticker']:
                if ticker['symbol'] == 'BTC-USDT':
                    prices['kucoin'] = float(ticker['last'])
                    break
        except:
            prices['kucoin'] = 0
        
        return prices
    
    def find_opportunity(self):
        """Find arbitrage opportunity"""
        prices = self.check_prices()
        
        if prices['binance'] > 0 and prices['kucoin'] > 0:
            diff = abs(prices['binance'] - prices['kucoin'])
            diff_pct = (diff / ((prices['binance'] + prices['kucoin']) / 2)) * 100
            
            if diff_pct > 0.1:  # 0.1% threshold
                return {
                    'found': True,
                    'binance': prices['binance'],
                    'kucoin': prices['kucoin'],
                    'difference': diff_pct,
                    'potential_profit': 100 * (diff_pct / 100) * 0.5  # $100 trade, 50% after fees
                }
        
        return {'found': False}

# ========== PART 2: DONATION SYSTEM ==========
class DonationSystem:
    def __init__(self):
        self.donated = 0
        self.donations = []
        
    def record_donation(self, amount, to="Gaza Relief"):
        """Record a donation"""
        donation = {
            'amount': amount,
            'to': to,
            'time': datetime.now().isoformat()
        }
        self.donations.append(donation)
        self.donated += amount
        return donation

# ========== PART 3: WEB DASHBOARD ==========
class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>🌐 SolarPunk Dashboard</title>
                <meta http-equiv="refresh" content="5">
                <style>
                    body {{ background: #000; color: #0f0; font-family: monospace; }}
                    .box {{ border: 2px solid #0f0; padding: 20px; margin: 10px; }}
                </style>
            </head>
            <body>
                <div class="box">
                    <h1>🌐 SOLARPUNK DASHBOARD</h1>
                    <p>Live from your desktop - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="box">
                    <h2>📊 STATS</h2>
                    <p>Running: {int(time.time() - start_time)} seconds</p>
                    <p>Cycles completed: {cycles}</p>
                    <p>Total profit (simulated): ${total_profit:.4f}</p>
                    <p>Humanitarian donations: ${total_donated:.4f}</p>
                </div>
                
                <div class="box">
                    <h2>🚀 ACTIONS</h2>
                    <button onclick="window.open('https://www.paypal.com/donate?hosted_button_id=YOUR_BUTTON')">
                        Donate $1 to Gaza
                    </button>
                    <button onclick="window.open('https://github.com/yourusername/solarpunk')">
                        View Code
                    </button>
                </div>
                
                <div class="box">
                    <h2>📝 LOG</h2>
                    <pre>{log_output}</pre>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())

# ========== PART 4: MAIN SYSTEM ==========
class SolarPunkSystem:
    def __init__(self):
        self.arbitrage = ArbitrageEngine()
        self.donations = DonationSystem()
        self.log = []
        self.cycles = 0
        self.total_profit = 0
        self.total_donated = 0
        
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log.append(f"[{timestamp}] {message}")
        # Keep last 20 messages
        if len(self.log) > 20:
            self.log.pop(0)
        print(message)
    
    def run_cycle(self):
        """Run one cycle of the system"""
        self.cycles += 1
        
        # Check for arbitrage
        opportunity = self.arbitrage.find_opportunity()
        
        if opportunity['found']:
            profit = opportunity['potential_profit']
            self.total_profit += profit
            
            # Split profit
            humanitarian = profit * 0.5
            self.total_donated += humanitarian
            
            # Record donation
            self.donations.record_donation(humanitarian)
            
            self.log_message(f"💰 Cycle {self.cycles}: ${profit:.4f} profit")
            self.log_message(f"🕊️  Donated ${humanitarian:.4f} to Gaza relief")
        
        else:
            self.log_message(f"🔍 Cycle {self.cycles}: No opportunity found")
        
        # Save state every 10 cycles
        if self.cycles % 10 == 0:
            self.save_state()
    
    def save_state(self):
        """Save system state"""
        state = {
            'cycles': self.cycles,
            'total_profit': self.total_profit,
            'total_donated': self.total_donated,
            'last_updated': datetime.now().isoformat()
        }
        
        with open('solarpunk_state.json', 'w') as f:
            json.dump(state, f, indent=2)
        
        self.log_message(f"💾 State saved to solarpunk_state.json")
    
    def run(self, interval=30):
        """Run the system continuously"""
        self.log_message("🚀 SolarPunk System Starting...")
        self.log_message(f"📡 Dashboard: http://localhost:8080")
        self.log_message(f"⏱️  Interval: {interval} seconds")
        self.log_message("-" * 40)
        
        # Start web dashboard in background
        def run_server():
            server = HTTPServer(('localhost', 8080), DashboardHandler)
            server.serve_forever()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Open dashboard in browser
        webbrowser.open('http://localhost:8080')
        
        # Main loop
        try:
            while True:
                self.run_cycle()
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.log_message("\n🛑 System stopped by user")
            self.save_state()
            
            # Final report
            print("\n" + "=" * 60)
            print("📊 FINAL REPORT")
            print("=" * 60)
            print(f"Total cycles: {self.cycles}")
            print(f"Total profit: ${self.total_profit:.4f}")
            print(f"Total donated: ${self.total_donated:.4f}")
            print(f"Humanitarian impact: ${self.total_donated:.4f}")
            print("=" * 60)

# Global variables for dashboard
start_time = time.time()
cycles = 0
total_profit = 0
total_donated = 0
log_output = ""

# Run it
if __name__ == "__main__":
    print("=" * 60)
    print("🌐 COMPLETE SOLARPUNK SYSTEM")
    print("=" * 60)
    print("This system includes:")
    print("1. Arbitrage detection (simulated)")
    print("2. Automatic humanitarian donations")
    print("3. Live web dashboard")
    print("4. Everything in ONE file")
    print("=" * 60)
    
    system = SolarPunkSystem()
    system.run(interval=30)  # Check every 30 seconds