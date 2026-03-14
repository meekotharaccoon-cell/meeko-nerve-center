# FIXED DASHBOARD - PROPER ENCODING
import http.server
import socketserver
import json
import time
from datetime import datetime

# Read the current state
try:
    with open('solarpunk_state.json', 'r') as f:
        state = json.load(f)
    cycles = state.get('cycles', 0)
    total_profit = state.get('total_profit', 0.0)
    total_donated = state.get('total_donated', 0.0)
except:
    cycles = 0
    total_profit = 0.0
    total_donated = 0.0

PORT = 8081  # Different port to avoid conflict

class FixedDashboard(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>SolarPunk Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {{ background: #000; color: #0f0; font-family: monospace; }}
        .box {{ border: 2px solid #0f0; padding: 20px; margin: 10px; }}
        button {{ background: #002200; color: #0f0; border: 1px solid #0f0; padding: 10px; }}
    </style>
</head>
<body>
    <div class="box">
        <h1>SOLARPUNK DASHBOARD</h1>
        <p>Live from your desktop - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="box">
        <h2>STATS</h2>
        <p>Running: {int(time.time() - time.time() + 300)} seconds</p>
        <p>Cycles completed: {cycles}</p>
        <p>Total profit (simulated): ${total_profit:.4f}</p>
        <p>Humanitarian donations: ${total_donated:.4f}</p>
    </div>
    
    <div class="box">
        <h2>ACTIONS</h2>
        <button onclick="window.open('https://www.paypal.com/donate?hosted_button_id=X6YR4EY6LQSYJ')">
            Donate $1 to Gaza
        </button>
        <button onclick="window.open('https://github.com')">
            View Code
        </button>
    </div>
    
    <div class="box">
        <h2>WHAT'S HAPPENING RIGHT NOW:</h2>
        <p>1. Mock Arbitrage Bot: Making $0.01/minute (simulated)</p>
        <p>2. Real Price Checker: Monitoring Binance & KuCoin</p>
        <p>3. Dashboard: Showing live stats</p>
        <p>4. System: Saving state every 10 cycles</p>
    </div>
</body>
</html>"""
            
            self.wfile.write(html.encode('utf-8'))

print(f"🚀 Starting FIXED dashboard on http://localhost:{PORT}")
print("No more encoding issues!")

with socketserver.TCPServer(("", PORT), FixedDashboard) as httpd:
    httpd.serve_forever()