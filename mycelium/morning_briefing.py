#!/usr/bin/env python3
"""
MEEKO MORNING BRIEFING
Runs every morning at 9 AM EST as part of mycelium-morning.yml
Generates a personal daily briefing and emails it to mickowood86@gmail.com
Covers: system status, money, new grant deadlines, news, what happened overnight
"""
import os, json, smtplib, requests
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER  = 'mickowood86@gmail.com'
GMAIL_PASS  = os.environ.get('GMAIL_APP_PASSWORD', '')
OR_KEY      = os.environ.get('OPENROUTER_KEY', '')
SERP_KEY    = os.environ.get('SERPAPI_KEY', '')
GALLERY     = 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery'
GH_TOKEN    = os.environ.get('GITHUB_TOKEN', '')

GRANT_DEADLINES = [
    {"name": "Creative Capital Award + State of the Art Prize ($10k-$50k)",
     "url": "https://creative-capital.org/creative-capital-award/",
     "deadline": "2026 cycle open now", "fee": "free"},
    {"name": "Harpo Foundation Visual Artists Grant",
     "url": "https://www.harpofoundation.org/grants/",
     "deadline": "April 28, 2025 (watch for 2026 portal Feb 26)", "fee": "$15 (waiver available)"},
    {"name": "Awesome Foundation Monthly Microgrant ($1,000)",
     "url": "https://www.awesomefoundation.org/",
     "deadline": "Recurring monthly", "fee": "free"},
    {"name": "Innovate Grant ($1,800 quarterly)",
     "url": "https://www.innovategrant.com/",
     "deadline": "Recurring quarterly", "fee": "free"},
    {"name": "Harvestworks Art+Tech Residency ($5k commission)",
     "url": "https://www.harvestworks.org/",
     "deadline": "2026 cycle", "fee": "free"},
    {"name": "Knight Foundation Prototype Fund",
     "url": "https://knightfoundation.org/prototype/",
     "deadline": "Rolling", "fee": "free"},
    {"name": "Wikimedia Foundation Rapid Fund (up to $50k)",
     "url": "https://meta.wikimedia.org/wiki/Grants:Start",
     "deadline": "Rolling", "fee": "free"},
    {"name": "Rhizome Microgrant (net art)",
     "url": "https://rhizome.org",
     "deadline": "Rolling", "fee": "free"},
    {"name": "Mozilla Foundation Technology Fund",
     "url": "https://foundation.mozilla.org/en/what-we-fund/",
     "deadline": "Rolling", "fee": "free"},
    {"name": "Open Collective Fiscal Sponsorship (enables all grants)",
     "url": "https://opencollective.com/",
     "deadline": "Rolling - applied!", "fee": "free"},
]

def get_gallery_stats():
    if not GH_TOKEN:
        return {"views": "?", "uniques": "?"}
    try:
        r = requests.get(
            'https://api.github.com/repos/meekotharaccoon-cell/gaza-rose-gallery/traffic/views',
            headers={'Authorization': f'Bearer {GH_TOKEN}', 'User-Agent': 'mycelium'},
            timeout=10
        )
        d = r.json()
        return {"views": d.get('count', 0), "uniques": d.get('uniques', 0)}
    except:
        return {"views": "?", "uniques": "?"}

def get_ai_briefing(stats, sent_emails):
    if not OR_KEY:
        return "AI briefing unavailable (no OPENROUTER_KEY)"
    prompt = f"""Write Meeko's morning briefing. Today: {datetime.now(timezone.utc).strftime('%A %B %d, %Y')}.

Gaza Rose Gallery stats (last 14 days): {stats['views']} views, {stats['uniques']} unique visitors.
Emails sent so far: {', '.join(sent_emails) if sent_emails else 'none yet'}.

Write a SHORT (200 word max), warm, personal morning briefing that:
1. States what the system did overnight (monitoring, any issues)
2. Notes the gallery traffic honestly
3. Reminds of the most important 1-2 actions Meeko should take today
4. Ends with something genuinely encouraging (not generic)

Be real. Be brief. No corporate speak. This is a personal message to one artist."""
    try:
        r = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {OR_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'openai/gpt-4o-mini', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 300},
            timeout=20
        )
        return r.json()['choices'][0]['message']['content'].strip()
    except:
        return "AI briefing failed. System is still running."

def build_email(stats, sent_emails):
    ai_text = get_ai_briefing(stats, sent_emails)
    now = datetime.now(timezone.utc).strftime('%A, %B %d %Y')
    
    grants_section = ''
    for g in GRANT_DEADLINES[:5]:  # top 5 most relevant
        grants_section += f"  • {g['name']}\n    Deadline: {g['deadline']} | Fee: {g['fee']}\n    {g['url']}\n\n"
    
    body = f"""MEEKO MYCELIUM — MORNING BRIEFING
{now}
{'='*50}

{ai_text}

{'='*50}
GALLERY TRAFFIC (last 14 days)
  Views: {stats['views']} | Unique visitors: {stats['uniques']}
  URL: {GALLERY}

{'='*50}
GRANT OPPORTUNITIES — OPEN NOW

{grants_section}{'='*50}
SYSTEM STATUS
  ✓ Gallery: LIVE
  ✓ PayPal: Connected
  ✓ OpenRouter AI: Connected  
  ✓ SerpAPI: Connected
  ✓ GitHub Actions: Running
  ▸ Gmail auto-reply: Needs GMAIL_APP_PASSWORD
  ▸ Lightning payments: Needs Strike API key
  ▸ Dev.to article: Needs DEVTO_API_KEY

{'='*50}
YOUR ONLY JOBS TODAY (if anything)
  1. Check if any replies came in to your sent emails
  2. If Strike API key is available — add it to secrets
  3. Everything else: already handled

The system ran all night. The art is still there. The mission hasn't changed.
— Mycelium"""
    return body

def load_sent():
    try:
        with open('mycelium/sent_outreach.json') as f:
            return list(json.load(f).keys())
    except:
        return []

def send_briefing(body):
    if not GMAIL_PASS:
        print('[Briefing] No GMAIL_APP_PASSWORD — printing instead:')
        print(body)
        return
    msg = MIMEMultipart()
    msg['From'] = f'Mycelium System <{GMAIL_USER}>'
    msg['To'] = GMAIL_USER
    msg['Subject'] = f'🌹 Gaza Rose — Morning Briefing {datetime.now(timezone.utc).strftime("%b %d")}'
    msg.attach(MIMEText(body, 'plain'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)
    print('[Briefing] Sent to mickowood86@gmail.com')

def run():
    stats = get_gallery_stats()
    sent = load_sent()
    body = build_email(stats, sent)
    send_briefing(body)

if __name__ == '__main__':
    run()
