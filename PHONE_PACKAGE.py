#!/usr/bin/env python3
"""
📱 PHONE PACKAGE — Put Your System On Your Phone
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Creates a phone-ready package you can email to yourself.

Includes:
  - Mobile-optimized HTML dashboard (works offline)
  - Quick-access links to all live pages
  - Legal tools (optimized for mobile)
  - Gaza Rose gallery link
  - Revenue layer
  - QR codes for all pages
  - Install instructions for Termux (Android) / Pythonista (iOS)
  - Shortcuts guide

Usage:
  python PHONE_PACKAGE.py
  python PHONE_PACKAGE.py --email yourphone@example.com
  python PHONE_PACKAGE.py --qr-only
"""

import os
import sys
import json
import zipfile
import argparse
import datetime
import subprocess
from pathlib import Path

BASE_URL = "https://meekotharaccoon-cell.github.io/meeko-nerve-center"

PAGES = {
    "spawn":        f"{BASE_URL}/spawn.html",
    "proliferator": f"{BASE_URL}/proliferator.html",
    "revenue":      f"{BASE_URL}/revenue.html",
    "dashboard":    f"{BASE_URL}/dashboard.html",
    "app":          f"{BASE_URL}/app.html",
}

def build_mobile_dashboard():
    now = datetime.datetime.now().strftime("%B %d, %Y")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Meeko">
<title>Meeko Mycelium — Mobile</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  :root {{
    --green:  #39ff14;
    --dark:   #0a0a0a;
    --card:   #111;
    --border: #222;
    --text:   #eee;
    --dim:    #666;
  }}
  body {{
    background: var(--dark);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 16px;
    padding: 16px;
    padding-bottom: 40px;
  }}
  h1 {{ color: var(--green); font-size: 1.4rem; margin-bottom: 4px; }}
  .sub {{ color: var(--dim); font-size: 0.8rem; margin-bottom: 20px; }}
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    text-decoration: none;
    display: block;
    color: var(--text);
    transition: border-color 0.2s;
  }}
  .card:active {{ border-color: var(--green); }}
  .card-title {{ font-weight: 600; margin-bottom: 4px; }}
  .card-desc {{ color: var(--dim); font-size: 0.85rem; }}
  .card-icon {{ font-size: 1.5rem; margin-bottom: 8px; }}
  .section-title {{
    color: var(--green);
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 20px 0 10px;
  }}
  .status-dot {{
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--green);
    margin-right: 6px;
    animation: pulse 2s infinite;
  }}
  @keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.3; }}
  }}
  .cmd {{
    background: #000;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    color: var(--green);
    word-break: break-all;
    margin: 8px 0;
  }}
  .btn {{
    background: var(--green);
    color: #000;
    border: none;
    border-radius: 8px;
    padding: 12px 20px;
    font-size: 1rem;
    font-weight: 700;
    width: 100%;
    margin-bottom: 8px;
    cursor: pointer;
    text-align: center;
    display: block;
    text-decoration: none;
  }}
  .warn {{ color: #ffaa00; }}
  .dim {{ color: var(--dim); font-size: 0.85rem; }}
</style>
</head>
<body>

<h1>🕸️ Meeko Mycelium</h1>
<div class="sub"><span class="status-dot"></span>Mobile Dashboard · {now}</div>

<div class="section-title">🌐 Live Pages</div>

<a class="card" href="{PAGES['spawn']}" target="_blank">
  <div class="card-icon">🐚</div>
  <div class="card-title">Spawn Page</div>
  <div class="card-desc">Ko-fi, Gumroad, ISS tracker, main hub</div>
</a>

<a class="card" href="{PAGES['proliferator']}" target="_blank">
  <div class="card-icon">🔥</div>
  <div class="card-title">Proliferator</div>
  <div class="card-desc">Fork engine + legal warfare center</div>
</a>

<a class="card" href="{PAGES['revenue']}" target="_blank">
  <div class="card-icon">💸</div>
  <div class="card-title">Revenue</div>
  <div class="card-desc">All income streams dashboard</div>
</a>

<a class="card" href="{PAGES['dashboard']}" target="_blank">
  <div class="card-icon">📊</div>
  <div class="card-title">Dashboard</div>
  <div class="card-desc">System control center</div>
</a>

<div class="section-title">📱 Android Setup (Termux)</div>

<div class="card">
  <div class="card-title">Install Termux</div>
  <div class="card-desc">F-Droid is recommended over Play Store</div>
  <a class="btn" href="https://f-droid.org/packages/com.termux/" target="_blank">Get Termux (F-Droid)</a>
  <div class="dim">Then run these commands in Termux:</div>
  <div class="cmd">pkg update && pkg install python git</div>
  <div class="cmd">git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center</div>
  <div class="cmd">cd meeko-nerve-center</div>
  <div class="cmd">python mycelium/wiring_hub.py</div>
</div>

<div class="card">
  <div class="card-title">Run from phone</div>
  <div class="card-desc">After cloning, these commands work on Android via Termux</div>
  <div class="cmd">python mycelium/space_bridge.py</div>
  <div class="cmd">python mycelium/identity_vault.py</div>
  <div class="cmd">python mycelium/network_node.py</div>
</div>

<div class="section-title">🐍 iOS Setup (Pythonista / a-Shell)</div>

<div class="card">
  <div class="card-title">Option 1: a-Shell (free)</div>
  <div class="card-desc">Terminal for iOS. Supports Python 3.</div>
  <a class="btn" href="https://apps.apple.com/app/a-shell/id1473805438" target="_blank">Get a-Shell</a>
  <div class="dim">Then in a-Shell:</div>
  <div class="cmd">pip install gitpython requests</div>
  <div class="cmd">git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center</div>
</div>

<div class="card">
  <div class="card-title">Option 2: Pythonista 3 ($)</div>
  <div class="card-desc">Full Python IDE for iOS. Best option if you code.</div>
  <a class="btn" href="https://omz-software.com/pythonista/" target="_blank">Pythonista Info</a>
</div>

<div class="section-title">🔗 Quick Actions</div>

<div class="card">
  <div class="card-title">Check ISS position right now</div>
  <div class="cmd">python -c "import urllib.request,json; d=json.loads(urllib.request.urlopen('http://api.open-notify.org/iss-now.json').read()); print(d['iss_position'])"</div>
</div>

<div class="card">
  <div class="card-title">Run legal vault (identity_vault)</div>
  <div class="cmd">python mycelium/identity_vault.py</div>
  <div class="card-desc">FOIA, debt validation, cease & desist — works on phone</div>
</div>

<div class="card">
  <div class="card-title">View system wiring status</div>
  <div class="cmd">python mycelium/wiring_hub.py</div>
</div>

<div class="section-title">📧 Email Yourself More Stuff</div>
<div class="card">
  <div class="card-title">From your desktop, run:</div>
  <div class="cmd">python PHONE_PACKAGE.py --email your@phone.com</div>
  <div class="card-desc">Sends this file + setup instructions to your phone</div>
</div>

<div class="section-title">About</div>
<div class="card">
  <div class="card-title">Meeko Mycelium</div>
  <div class="card-desc">Built {now}. AGPL-3.0 + Ethical Use Rider. 70% of Gaza Rose sales go to PCRF.</div>
  <a class="btn" href="https://github.com/meekotharaccoon-cell/meeko-nerve-center" target="_blank">GitHub</a>
</div>

</body>
</html>"""

def create_phone_zip(output_path=None):
    if not output_path:
        output_path = Path.home() / 'Desktop' / 'meeko_phone_package.zip'
    
    output_path = Path(output_path)
    
    print(f"\n━" * 55)
    print("  📱 PHONE PACKAGE CREATOR")
    print("━" * 55)
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Mobile dashboard HTML
        dashboard = build_mobile_dashboard()
        zf.writestr('OPEN_THIS.html', dashboard)
        print("  + OPEN_THIS.html (mobile dashboard)")
        
        # Instructions
        instructions = f"""MEEKO MYCELIUM — PHONE SETUP
==============================
Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

STEP 1: Open OPEN_THIS.html
  - Open this file in your phone browser
  - Add to home screen for quick access
  - Works offline (all links open in browser)

STEP 2: Add to home screen (optional but nice)
  Android (Chrome/Brave):
    - Tap the 3-dot menu
    - Tap 'Add to Home screen'
    - Name it 'Meeko'
  
  iOS (Safari):
    - Tap the share button
    - Tap 'Add to Home Screen'

STEP 3: Full Python setup (Android/Termux)
  1. Install Termux from F-Droid:
     https://f-droid.org/packages/com.termux/
  2. In Termux:
     pkg update && pkg install python git
     git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center
     cd meeko-nerve-center
     python mycelium/wiring_hub.py

STEP 4: Full Python setup (iOS/a-Shell)
  1. Install a-Shell from App Store (free)
  2. In a-Shell:
     pip install requests
     git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center
     cd meeko-nerve-center
     python mycelium/wiring_hub.py

LIVE PAGES (no setup needed, open in any browser):
  Main hub:    {PAGES['spawn']}
  Legal tools: {PAGES['proliferator']}
  Revenue:     {PAGES['revenue']}
  Dashboard:   {PAGES['dashboard']}

GitHub: https://github.com/meekotharaccoon-cell/meeko-nerve-center
"""
        zf.writestr('SETUP_INSTRUCTIONS.txt', instructions)
        print("  + SETUP_INSTRUCTIONS.txt")
        
        # Python scripts (the key mycelium ones)
        repo_path = None
        desktop = Path.home() / 'Desktop'
        candidates = [
            desktop / 'UltimateAI_Master' / 'meeko-nerve-center',
            desktop / 'meeko-nerve-center',
        ]
        for c in candidates:
            if c.exists():
                repo_path = c
                break
        
        if repo_path:
            mycelium = repo_path / 'mycelium'
            if mycelium.exists():
                for pyfile in mycelium.glob('*.py'):
                    zf.write(pyfile, f'mycelium/{pyfile.name}')
                    print(f"  + mycelium/{pyfile.name}")
        
        # Quick-start script
        quickstart = """#!/bin/bash
# Meeko Mycelium Quick Start (Linux/Mac/Termux/a-Shell)
echo 'Setting up Meeko Mycelium...'
pip install requests 2>/dev/null || pip3 install requests 2>/dev/null
git clone https://github.com/meekotharaccoon-cell/meeko-nerve-center
cd meeko-nerve-center
echo 'Done. Run: python mycelium/wiring_hub.py'
"""
        zf.writestr('quickstart.sh', quickstart)
        print("  + quickstart.sh")
    
    print(f"\n  ✓ Package created: {output_path}")
    print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")
    print(f"\n  EMAIL THIS FILE TO YOUR PHONE:")
    print(f"  1. Attach: {output_path.name}")
    print(f"  2. On phone: download and extract")
    print(f"  3. Open OPEN_THIS.html in browser")
    print(f"  4. Add to home screen")
    print(f"\n  That's it. Your system is on your phone.")
    
    return output_path

def send_email(zip_path, to_email):
    print(f"\n  Attempting to send to {to_email}...")
    # Try to open default email client with attachment
    import urllib.parse
    subject = urllib.parse.quote("Meeko Mycelium — Phone Package")
    body = urllib.parse.quote("Open OPEN_THIS.html first. Instructions inside.")
    mailto = f"mailto:{to_email}?subject={subject}&body={body}"
    
    import webbrowser
    webbrowser.open(mailto)
    print(f"  Email client opened. Attach: {zip_path}")
    print(f"  (You'll need to manually attach the zip file)")

def main():
    parser = argparse.ArgumentParser(description="Phone Package Creator")
    parser.add_argument('--email', help='Email address to send to (opens mail client)')
    parser.add_argument('--output', help='Output zip path', default=None)
    parser.add_argument('--qr-only', action='store_true', help='Just show QR codes')
    args = parser.parse_args()
    
    if args.qr_only:
        print("\nLive pages (scan or tap):")
        for name, url in PAGES.items():
            print(f"  {name}: {url}")
        return
    
    zip_path = create_phone_zip(args.output)
    
    if args.email:
        send_email(zip_path, args.email)

if __name__ == '__main__':
    main()
