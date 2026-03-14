#!/usr/bin/env python3
"""
morning_briefing.py — Email yourself what happened while you slept.
Runs automatically in GitHub Actions heartbeat (8am UTC).
Requires GMAIL_APP_PASSWORD secret.

Get app password: myaccount.google.com/apppasswords
Add to GitHub: repo Settings > Secrets > GMAIL_APP_PASSWORD
"""

import os
import json
import smtplib
import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'

def load(f, d={}):
    p = DATA / f
    try: return json.loads(p.read_text()) if p.exists() else d
    except: return d

def send_briefing():
    pw    = os.environ.get('GMAIL_APP_PASSWORD', '').strip()
    addr  = os.environ.get('GMAIL_ADDRESS', 'meekotharaccoon@gmail.com').strip()
    
    if not pw:
        print("\033[93mGMAIL_APP_PASSWORD not set. Skipping email.\033[0m")
        print("Add it: github.com/meekotharaccoon-cell/meeko-nerve-center/settings/secrets")
        return

    now     = datetime.datetime.utcnow()
    briefing = load('briefing_data.json')
    space    = load('space_data.json')
    state    = load('system_state.json')
    wiring   = load('wiring_status.json')

    iss = space.get('iss_position', {})
    lat = iss.get('latitude', 'N/A')
    lon = iss.get('longitude', 'N/A')
    
    conns = wiring.get('connections', {})
    live  = [k for k,v in conns.items() if v]
    dark  = [k for k,v in conns.items() if not v]

    body = f"""<html><body style="background:#0a0a0a;color:#eee;font-family:monospace;padding:24px">
<h1 style="color:#39ff14">🕸️ Meeko Morning Briefing</h1>
<p style="color:#555">{now.strftime('%A, %B %d %Y · %H:%M UTC')}</p>
<hr style="border-color:#222;margin:16px 0">

<h2 style="color:#39ff14">🚀 Space</h2>
<p>ISS position: {lat}° lat, {lon}° lon</p>

<h2 style="color:#39ff14;margin-top:16px">🕸️ System</h2>
<p>Ollama: {'\u2713 running' if briefing.get('ollama_running') else '\u2717 offline'}</p>
<p>Email: {'\u2713 live' if briefing.get('email_enabled') else '\u2717 dark'}</p>
<p>GitHub forks: {briefing.get('github_forks',0)} | Stars: {briefing.get('github_stars',0)}</p>

<h2 style="color:#39ff14;margin-top:16px">🔗 Live connections ({len(live)})</h2>
{''.join(f'<p style="color:#39ff14">✓ {c.replace("_"," ")}</p>' for c in live)}

<h2 style="color:#ff4444;margin-top:16px">⚠️ Dark ({len(dark)})</h2>
{''.join(f'<p style="color:#ff4444">✗ {c.replace("_"," ")}</p>' for c in dark)}

<hr style="border-color:#222;margin:16px 0">
<p style="color:#555;font-size:0.8rem">
Meeko Mycelium · <a href="https://meekotharaccoon-cell.github.io/meeko-nerve-center/status.html" style="color:#39ff14">Live status</a>
</p>
</body></html>"""

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🕸️ Meeko Briefing {now.strftime('%m/%d %H:%M')}"
    msg['From']    = addr
    msg['To']      = addr
    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(addr, pw)
            s.sendmail(addr, addr, msg.as_string())
        print(f"\033[92m✓ Briefing sent to {addr}\033[0m")
    except Exception as e:
        print(f"\033[91m✗ Email failed: {e}\033[0m")
        print("Check: myaccount.google.com/apppasswords")

if __name__ == '__main__':
    send_briefing()
