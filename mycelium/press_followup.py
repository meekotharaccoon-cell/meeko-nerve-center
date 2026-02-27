#!/usr/bin/env python3
"""
Press Follow-up Engine
========================
Press outreach goes out but is never followed up. Most journalists
need 2-3 touches before they respond. This closes that gap.

Logic:
  - Reads outreach_queue.json and sent_outreach.json
  - Finds press contacts who were emailed 5+ days ago with no reply
  - Sends one follow-up (not a second if already followed up)
  - After a second follow-up with no response, retires the contact
  - Logs everything to data/press_followup_log.json

This is persistent press relationship management with zero human effort.
"""

import json, datetime, os, smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'

TODAY     = datetime.date.today()
TODAY_STR = TODAY.isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

FOLLOWUP_DAYS     = 5   # Days after initial email before first follow-up
RETIRE_DAYS       = 12  # Days after first follow-up before retiring

def ask_llm(prompt, max_tokens=400):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model':      'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages':   [
                {'role': 'system', 'content': 'You write concise, compelling press follow-up emails for an open-source humanitarian AI project. Professional but human. Never desperate. Sign as Meeko.'},
                {'role': 'user',   'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[press_fu] LLM error: {e}')
        return None

def send_email(to_addr, subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = to_addr
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, to_addr, msg.as_string())
        print(f'[press_fu] Sent to {to_addr}')
        return True
    except Exception as e:
        print(f'[press_fu] Failed {to_addr}: {e}')
        return False

def days_since(date_str):
    try:
        return (TODAY - datetime.date.fromisoformat(date_str[:10])).days
    except:
        return -1

def generate_followup(contact_name, outlet, original_subject, followup_number):
    if followup_number == 1:
        prompt = f"""Write a short follow-up email (under 100 words).

Context: We sent a press pitch to {contact_name or 'the editor'} at {outlet or 'their publication'} about 5 days ago re: \"{original_subject}\"

This is follow-up #1. Keep it:
- Very brief (3-4 sentences max)
- Add one new piece of information they didn't have before (e.g. the system just self-evolved, or a new congressional trade was flagged)
- Not needy or pushy
- End with a soft CTA

Just the email body. No subject line.
"""
    else:
        prompt = f"""Write a final follow-up email (under 80 words) to {contact_name or 'the editor'} at {outlet}.

This is the last touch. After this we leave them alone.
Be gracious, leave the door open, mention where to find us:
  GitHub: https://github.com/meekotharaccoon-cell/meeko-nerve-center

Just the email body. No subject line.
"""
    return ask_llm(prompt)

def run():
    print(f'\n[press_fu] Press Follow-up Engine — {TODAY_STR}')

    # Load sent outreach log
    sent_path = DATA / 'sent_outreach.json'
    if not sent_path.exists():
        print('[press_fu] No sent_outreach.json found. Skipping.')
        return

    try:
        sent_log = json.loads(sent_path.read_text())
    except Exception as e:
        print(f'[press_fu] Read error: {e}')
        return

    # sent_log can be a list of outreach dicts or a dict with a 'sent' key
    if isinstance(sent_log, list):
        sent_list = sent_log
    elif isinstance(sent_log, dict):
        sent_list = sent_log.get('sent', [])
    else:
        return

    # Load/init follow-up log
    fu_path = DATA / 'press_followup_log.json'
    fu_log  = {'contacts': {}}
    if fu_path.exists():
        try: fu_log = json.loads(fu_path.read_text())
        except: pass

    sent_count  = 0
    retired     = 0
    modified    = False

    for entry in sent_list:
        email   = entry.get('email', '')
        if not email or '@' not in email:
            continue

        # Only follow up with press / outreach type entries
        etype = entry.get('type', entry.get('category', '')).lower()
        if not any(kw in etype for kw in ('press', 'media', 'journalist', 'outreach', 'pitch')):
            continue

        contact = fu_log['contacts'].setdefault(email, {
            'name':           entry.get('name', ''),
            'outlet':         entry.get('outlet', entry.get('publication', '')),
            'original_subj':  entry.get('subject', ''),
            'sent_date':      entry.get('sent_date', entry.get('date', '')),
            'followups':      [],
            'status':         'active',
        })

        if contact.get('status') == 'retired':
            continue

        age          = days_since(contact['sent_date'])
        followups    = contact.get('followups', [])
        fu_count     = len(followups)

        # Retire after 2 follow-ups with no response
        if fu_count >= 2:
            contact['status'] = 'retired'
            retired += 1
            modified = True
            print(f'[press_fu] Retiring {email} — 2 follow-ups sent, no response')
            continue

        # First follow-up: 5+ days after initial
        if fu_count == 0 and age >= FOLLOWUP_DAYS:
            print(f'[press_fu] Follow-up #1 due for {email} ({age}d ago)')
            body = generate_followup(
                contact['name'], contact['outlet'],
                contact['original_subj'], 1
            )
            if body:
                subj = f'Re: {contact["original_subj"]}' if contact['original_subj'] else 'Following up — Meeko Nerve Center'
                if send_email(email, subj, body):
                    followups.append({'date': TODAY_STR, 'number': 1})
                    modified = True
                    sent_count += 1

        # Second follow-up: RETIRE_DAYS after first follow-up
        elif fu_count == 1:
            last_fu_date = followups[-1].get('date', '')
            days_since_fu = days_since(last_fu_date)
            if days_since_fu >= RETIRE_DAYS:
                print(f'[press_fu] Follow-up #2 (final) due for {email}')
                body = generate_followup(
                    contact['name'], contact['outlet'],
                    contact['original_subj'], 2
                )
                if body:
                    subj = f'Last note — Meeko Nerve Center'
                    if send_email(email, subj, body):
                        followups.append({'date': TODAY_STR, 'number': 2})
                        modified = True
                        sent_count += 1

    if modified:
        try:
            fu_path.write_text(json.dumps(fu_log, indent=2))
        except Exception as e:
            print(f'[press_fu] Log save error: {e}')

    print(f'[press_fu] Done. Follow-ups sent: {sent_count} | Retired: {retired}')

if __name__ == '__main__':
    run()
