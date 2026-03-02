#!/usr/bin/env python3
"""
morning_briefing.py - Email yourself what happened while you slept.
Fix: nested single-quote f-string expressions (SyntaxError line 73).
Pre-compute HTML fragments before multi-line f-string.
"""

import os, json, smtplib, datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'

def load(f, d=None):
    if d is None: d = {}
    p = DATA / f
    try: return json.loads(p.read_text()) if p.exists() else d
    except: return d

def send_briefing():
    pw   = os.environ.get('GMAIL_APP_PASSWORD', '').strip()
    addr = os.environ.get('GMAIL_ADDRESS', 'meekotharaccoon@gmail.com').strip()

    if not pw:
        print('\033[93mGMAIL_APP_PASSWORD not set. Skipping email.\033[0m')
        return

    now      = datetime.datetime.utcnow()
    briefing = load('briefing_data.json')
    space    = load('space_data.json')
    wiring   = load('wiring_status.json')

    iss = space.get('iss_position', {})
    lat = iss.get('latitude', 'N/A')
    lon = iss.get('longitude', 'N/A')

    conns = wiring.get('connections', {})
    live  = [k for k, v in conns.items() if v]
    dark  = [k for k, v in conns.items() if not v]

    # Pre-compute all dynamic fragments (avoids nested quote errors)
    date_str     = now.strftime('%A, %B %d %Y \xb7 %H:%M UTC')
    ollama_str   = '\u2713 running' if briefing.get('ollama_running') else '\u2717 offline'
    email_str    = '\u2713 live'    if briefing.get('email_enabled')  else '\u2717 dark'
    forks_str    = str(briefing.get('github_forks', 0))
    stars_str    = str(briefing.get('github_stars', 0))
    live_count   = str(len(live))
    dark_count   = str(len(dark))
    live_items   = ''.join('<p style="color:#39ff14">\u2713 ' + c.replace('_', ' ') + '</p>' for c in live)
    dark_items   = ''.join('<p style="color:#ff4444">\u2717 ' + c.replace('_', ' ') + '</p>' for c in dark)
    subject_str  = '\U0001f578\ufe0f Meeko Briefing ' + now.strftime('%m/%d %H:%M')

    body = (
        '<html><body style="background:#0a0a0a;color:#eee;font-family:monospace;padding:24px">'
        '<h1 style="color:#39ff14">\U0001f578\ufe0f Meeko Morning Briefing</h1>'
        '<p style="color:#555">' + date_str + '</p>'
        '<hr style="border-color:#222;margin:16px 0">'
        '<h2 style="color:#39ff14">\U0001f680 Space</h2>'
        '<p>ISS position: ' + str(lat) + '\xb0 lat, ' + str(lon) + '\xb0 lon</p>'
        '<h2 style="color:#39ff14;margin-top:16px">\U0001f578\ufe0f System</h2>'
        '<p>Ollama: ' + ollama_str + '</p>'
        '<p>Email: ' + email_str + '</p>'
        '<p>GitHub forks: ' + forks_str + ' | Stars: ' + stars_str + '</p>'
        '<h2 style="color:#39ff14;margin-top:16px">\U0001f517 Live connections (' + live_count + ')</h2>'
        + live_items +
        '<h2 style="color:#ff4444;margin-top:16px">\u26a0\ufe0f Dark (' + dark_count + ')</h2>'
        + dark_items +
        '<hr style="border-color:#222;margin:16px 0">'
        '<p style="color:#555;font-size:0.8rem">Meeko Mycelium \xb7 '
        '<a href="https://meekotharaccoon-cell.github.io/meeko-nerve-center/status.html" style="color:#39ff14">Live status</a>'
        '</p></body></html>'
    )

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject_str
    msg['From']    = addr
    msg['To']      = addr
    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(addr, pw)
            s.sendmail(addr, addr, msg.as_string())
        print('\033[92m\u2713 Briefing sent to ' + addr + '\033[0m')
    except Exception as e:
        print('\033[91m\u2717 Email failed: ' + str(e) + '\033[0m')

if __name__ == '__main__':
    send_briefing()
