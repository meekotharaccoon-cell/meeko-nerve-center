"""
Build the crypto payment page for Gaza Rose Gallery.
Reads phantom_address from Gaza Rose DB and generates a beautiful payment page.
Run after connect_crypto.py to update the gallery with your actual addresses.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(r'C:\Users\meeko\Desktop\UltimateAI_Master\gaza_rose.db')
CONFIG_PATH = Path(r'C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY\payment_config.json')
OUTPUT = Path(r'C:\Users\meeko\Desktop\GAZA_ROSE_GALLERY\payment.html')

# Try loading from DB first, then config file
phantom_address = None
coinbase_commerce_link = ""

try:
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute("SELECT value FROM crypto_config WHERE key='phantom_address'").fetchone()
    if row:
        phantom_address = row[0]
    conn.close()
except:
    pass

if not phantom_address and CONFIG_PATH.exists():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
        phantom_address = cfg.get('phantom_solana', '')

if not phantom_address:
    phantom_address = "YOUR_PHANTOM_SOLANA_ADDRESS"
    print("NOTE: Run connect_crypto.py first to auto-fill your real address.")

# Shorten for display
addr_short = f"{phantom_address[:8]}...{phantom_address[-6:]}" if len(phantom_address) > 20 else phantom_address

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pay with Crypto — Gaza Rose Gallery</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', sans-serif;
      background: #0a0a0a;
      color: white;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .container {{ max-width: 700px; width: 100%; }}
    h1 {{
      text-align: center;
      font-size: 32px;
      margin-bottom: 8px;
      background: linear-gradient(45deg, #FFD700, #f39c12);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    .subtitle {{ text-align: center; color: #888; margin-bottom: 40px; font-size: 15px; }}

    .card {{
      background: #1a1a1a;
      border-radius: 20px;
      padding: 30px;
      margin-bottom: 20px;
      border: 1px solid #2a2a2a;
      transition: border-color 0.3s;
    }}
    .card:hover {{ border-color: #C0395A; }}
    .card-header {{
      display: flex;
      align-items: center;
      gap: 15px;
      margin-bottom: 20px;
    }}
    .coin-icon {{ font-size: 36px; }}
    .card-title {{ font-size: 20px; font-weight: bold; }}
    .card-subtitle {{ color: #888; font-size: 13px; margin-top: 3px; }}

    .address-box {{
      background: #111;
      border: 1px solid #333;
      border-radius: 12px;
      padding: 16px 20px;
      font-family: 'Courier New', monospace;
      font-size: 13px;
      color: #4CAF50;
      word-break: break-all;
      margin: 15px 0;
      position: relative;
    }}
    .copy-btn {{
      display: inline-block;
      background: #C0395A;
      color: white;
      border: none;
      padding: 10px 24px;
      border-radius: 30px;
      cursor: pointer;
      font-weight: bold;
      font-size: 14px;
      transition: 0.3s;
      margin-top: 10px;
    }}
    .copy-btn:hover {{ background: #e04070; transform: scale(1.03); }}
    .copy-btn.copied {{ background: #4CAF50; }}

    .tag {{
      display: inline-block;
      background: #2a1a2a;
      border: 1px solid #C0395A;
      color: #C0395A;
      padding: 3px 10px;
      border-radius: 20px;
      font-size: 11px;
      margin-right: 6px;
      margin-bottom: 6px;
    }}
    .tag.green {{
      background: #1a2a1a;
      border-color: #4CAF50;
      color: #4CAF50;
    }}

    .pcrf-box {{
      background: linear-gradient(135deg, #1a1a2e, #16213e);
      border: 2px solid #C0395A;
      border-radius: 20px;
      padding: 30px;
      text-align: center;
      margin-top: 20px;
    }}
    .pcrf-box h2 {{ color: #FFD700; margin-bottom: 12px; }}
    .pcrf-box p {{ color: #ccc; margin-bottom: 20px; line-height: 1.6; font-size: 14px; }}
    .pcrf-btn {{
      display: inline-block;
      background: #C0395A;
      color: white;
      text-decoration: none;
      padding: 14px 35px;
      border-radius: 30px;
      font-weight: bold;
      font-size: 15px;
      transition: 0.3s;
    }}
    .pcrf-btn:hover {{ background: #ff4d6d; transform: scale(1.05); }}
    .verified {{ color: #4CAF50; font-size: 12px; margin-top: 10px; }}

    .note {{
      background: #1a1a00;
      border: 1px solid #FFD700;
      border-radius: 12px;
      padding: 15px 20px;
      margin: 15px 0;
      font-size: 13px;
      color: #ccc;
    }}
    .note strong {{ color: #FFD700; }}

    .back-link {{
      text-align: center;
      margin-top: 30px;
    }}
    .back-link a {{
      color: #C0395A;
      text-decoration: none;
      font-size: 14px;
    }}
    .back-link a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
<div class="container">

  <h1>Pay with Crypto</h1>
  <div class="subtitle">Gaza Rose Gallery · By Meeko · 70% to PCRF Forever</div>

  <!-- SOLANA / PHANTOM -->
  <div class="card">
    <div class="card-header">
      <div class="coin-icon">◎</div>
      <div>
        <div class="card-title">Solana / USDC (via Phantom)</div>
        <div class="card-subtitle">Instant · Near-zero fees · No middleman</div>
      </div>
    </div>
    <span class="tag green">SOL</span>
    <span class="tag green">USDC on Solana</span>
    <span class="tag">SPL Tokens</span>
    <div class="address-box" id="sol-address">{phantom_address}</div>
    <button class="copy-btn" onclick="copyAddr('sol-address', this)">Copy Solana Address</button>
    <div class="note">
      <strong>How to pay:</strong> Open Phantom in your browser &rarr;
      Send &rarr; paste this address &rarr; enter amount &rarr; confirm.
      Works for SOL or any USDC on Solana.
    </div>
  </div>

  <!-- COINBASE COMMERCE -->
  <div class="card">
    <div class="card-header">
      <div class="coin-icon">₿</div>
      <div>
        <div class="card-title">Bitcoin, Ethereum &amp; More</div>
        <div class="card-subtitle">Via Coinbase Commerce · All major coins accepted</div>
      </div>
    </div>
    <span class="tag">BTC</span>
    <span class="tag">ETH</span>
    <span class="tag">USDC</span>
    <span class="tag">SOL</span>
    <span class="tag">DOGE</span>
    <span class="tag">LTC</span>
    <div class="note" style="margin-top: 15px;">
      <strong>Pay via Coinbase Commerce:</strong> Visit the product listing on
      <a href="https://gumroad.com/meeko" style="color:#C0395A;">Gumroad</a>
      and select your preferred crypto at checkout.
      Or contact <strong>meeko</strong> directly to generate a custom payment charge.
    </div>
  </div>

  <!-- PCRF -->
  <div class="pcrf-box">
    <h2>70% Goes to Palestinian Children</h2>
    <p>
      Every purchase triggers a <strong>70% donation to PCRF</strong> —
      Palestine Children's Relief Fund. Founded 1991.
      Verified 501(c)(3) nonprofit. 4-star Charity Navigator rating.<br><br>
      PCRF provides medical care, surgery sponsorship, and humanitarian aid to Palestinian children.
    </p>
    <a class="pcrf-btn" href="https://give.pcrf.net/campaign/739651/donate" target="_blank">
      Donate Directly to PCRF
    </a>
    <div class="verified">
      Verified at pcrf.net · Charity Navigator 4-Star · EIN on file
    </div>
  </div>

  <div class="back-link">
    <a href="index.html">&larr; Back to Gallery</a>
  </div>

</div>

<script>
function copyAddr(elemId, btn) {{
  const text = document.getElementById(elemId).innerText.trim();
  navigator.clipboard.writeText(text).then(() => {{
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => {{
      btn.textContent = elemId === 'sol-address' ? 'Copy Solana Address' : 'Copy Address';
      btn.classList.remove('copied');
    }}, 2000);
  }});
}}
</script>
</body>
</html>"""

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Payment page written to: {OUTPUT}")
print(f"Phantom address used: {addr_short}")
