#!/usr/bin/env python3
"""
Ko-fi Page Update Engine
=========================
New Gaza Rose art gets generated but Ko-fi never knows about it.
This fixes that.

Ko-fi doesn't have a full product creation API, but it does allow:
  - Posting shop updates via webhook/API v2
  - Updating the page bio/description
  - Creating posts visible to supporters

This engine:
  1. Checks public/images/ for new art generated today
  2. Posts a Ko-fi supporter update with the new art description
  3. Generates a caption using the LLM
  4. Logs what was posted to data/kofi_posts.json

Note: Ko-fi's API is limited. We use the Ko-fi webhook API to create
posts. If KOFI_TOKEN is not available, we queue the update for manual posting
and email a ready-to-paste draft instead.
"""

import json, datetime, os, smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'

TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
KOFI_TOKEN         = os.environ.get('KOFI_TOKEN', '')

KOFI_API_BASE = 'https://api.ko-fi.com/v1'

def ask_llm(prompt, max_tokens=300):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': 'You write compelling Ko-fi shop update captions for Gaza Rose art. Warm, meaningful, connected to the Palestinian solidarity mission.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=45) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[kofi] LLM error: {e}')
        return None

def find_new_art():
    """Return list of art files generated today."""
    images_dir = ROOT / 'public' / 'images'
    if not images_dir.exists():
        return []
    today_art = []
    for f in images_dir.glob('*.png'):
        try:
            mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime).date()
            if mtime.isoformat() == TODAY:
                today_art.append(f)
        except:
            pass
    # Also check art metadata
    art_meta = DATA / 'generated_art.json'
    if art_meta.exists():
        try:
            meta = json.loads(art_meta.read_text())
            arts = meta if isinstance(meta, list) else meta.get('art', [])
            for a in arts:
                if a.get('date', '')[:10] == TODAY and a.get('filename'):
                    p = ROOT / 'public' / 'images' / a['filename']
                    if p not in today_art and p.exists():
                        today_art.append(p)
        except:
            pass
    return today_art

def generate_caption(art_path):
    """Generate a Ko-fi post caption for a new piece of art."""
    # Try to find art metadata
    prompt_text = art_path.stem.replace('_', ' ').replace('-', ' ')

    # Check if there's a content queue entry with more context
    queue_dir = ROOT / 'content' / 'queue'
    art_context = ''
    if queue_dir.exists():
        for qf in queue_dir.glob('*art*'):
            try:
                posts = json.loads(qf.read_text())
                for p in posts:
                    if art_path.stem in p.get('text', ''):
                        art_context = p['text'][:300]
                        break
            except:
                pass

    prompt = f"""Write a Ko-fi shop update post for new Gaza Rose art.

Art filename: {art_path.name}
Context: {art_context or 'A new Gaza Rose piece generated today'}

The post should:
- Announce the new art (2-3 sentences)
- Connect it to the Palestinian solidarity mission
- Mention 70% of proceeds go to PCRF
- End with an invitation to visit the shop
- Be under 200 words
- Feel personal, not salesy

Just the post text.
"""
    return ask_llm(prompt)

def post_to_kofi(caption, image_url=None):
    """
    Attempt to post a supporter update via Ko-fi API.
    Ko-fi's API is limited — this uses the shop update endpoint if available.
    Returns True if posted, False if manual posting needed.
    """
    if not KOFI_TOKEN:
        print('[kofi] No KOFI_TOKEN — will queue for manual posting')
        return False

    # Ko-fi API v1 — post a shop update/message
    try:
        payload = json.dumps({
            'token':   KOFI_TOKEN,
            'message': caption,
        }).encode()
        req = urllib_request.Request(
            f'{KOFI_API_BASE}/shop/update',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
            if result.get('success') or result.get('status') == 'ok':
                print('[kofi] Posted to Ko-fi shop')
                return True
    except Exception as e:
        print(f'[kofi] API post failed: {e}')

    return False

def queue_manual_post(caption, art_name):
    """
    If API fails, save a ready-to-paste draft and email it.
    """
    draft = {
        'date':     TODAY,
        'art':      art_name,
        'platform': 'kofi',
        'caption':  caption,
        'status':   'pending_manual',
    }
    drafts_path = DATA / 'kofi_drafts.json'
    drafts = []
    if drafts_path.exists():
        try: drafts = json.loads(drafts_path.read_text())
        except: pass
    drafts.append(draft)
    try: drafts_path.write_text(json.dumps(drafts, indent=2))
    except: pass

    # Email the draft
    if GMAIL_ADDRESS and GMAIL_APP_PASSWORD:
        try:
            body = f"New Gaza Rose art was generated today. Here's the ready-to-post Ko-fi caption:\n\n{'='*50}\n\n{caption}\n\n{'='*50}\n\nPaste this at: https://ko-fi.com/manage/posts/new"
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'📮 Ko-fi post ready: {art_name}'
            msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
            msg['To']      = GMAIL_ADDRESS
            msg.attach(MIMEText(body, 'plain'))
            with smtplib.SMTP('smtp.gmail.com', 587) as s:
                s.ehlo(); s.starttls()
                s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
                s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
            print('[kofi] Draft emailed to you')
        except Exception as e:
            print(f'[kofi] Email failed: {e}')

def log_post(art_name, caption, posted_via_api):
    log_path = DATA / 'kofi_posts.json'
    log = []
    if log_path.exists():
        try: log = json.loads(log_path.read_text())
        except: pass
    log.append({
        'date':          TODAY,
        'art':           art_name,
        'caption':       caption[:200],
        'posted_via_api': posted_via_api,
    })
    try: log_path.write_text(json.dumps(log, indent=2))
    except: pass

def already_posted_today():
    log_path = DATA / 'kofi_posts.json'
    if not log_path.exists(): return False
    try:
        log = json.loads(log_path.read_text())
        return any(e.get('date') == TODAY for e in log)
    except:
        return False

def run():
    print(f'\n[kofi] Ko-fi Page Update Engine — {TODAY}')

    if already_posted_today():
        print('[kofi] Already posted today. Skipping.')
        return

    art_files = find_new_art()
    if not art_files:
        print('[kofi] No new art generated today. Skipping.')
        return

    print(f'[kofi] Found {len(art_files)} new art piece(s) today')

    for art_path in art_files[:1]:  # Post once per day max
        caption = generate_caption(art_path)
        if not caption:
            print('[kofi] Could not generate caption. Skipping.')
            continue

        print(f'[kofi] Caption generated: {caption[:80]}...')

        posted = post_to_kofi(caption)
        if not posted:
            queue_manual_post(caption, art_path.name)

        log_post(art_path.name, caption, posted)
        print(f'[kofi] Done. Posted via API: {posted}')
        break

if __name__ == '__main__':
    run()
