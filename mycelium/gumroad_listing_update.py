#!/usr/bin/env python3
"""
Gumroad Listing Update Engine
================================
New Gaza Rose art exists in public/images but is never listed for sale.
This fixes that.

Gumroad API v2:
  POST /products — create a new product listing
  PUT  /products/:id — update existing

This engine:
  1. Finds art generated today not yet listed on Gumroad
  2. Generates a product title and description with the LLM
  3. Creates the Gumroad listing via API (if GUMROAD_TOKEN available)
  4. If no token, emails you a ready-to-paste listing
  5. Tracks listed art in data/gumroad_listings.json

Price: $5 default. 70% earmarked for PCRF in description.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import urlencode
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'

TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GUMROAD_TOKEN      = os.environ.get('GUMROAD_TOKEN', '')

DEFAULT_PRICE_CENTS = 500  # $5.00
GUMROAD_API = 'https://api.gumroad.com/v2'

def ask_llm(prompt, max_tokens=400):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': 'You write compelling Gumroad product listings for Gaza Rose digital art. Meaningful, connected to Palestinian solidarity, clear about the PCRF donation.'},
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
        print(f'[gumroad] LLM error: {e}')
        return None

def find_unlisted_art():
    """Find art files not yet in gumroad_listings.json."""
    images_dir = ROOT / 'public' / 'images'
    if not images_dir.exists(): return []

    listed = set()
    listings_path = DATA / 'gumroad_listings.json'
    if listings_path.exists():
        try:
            listed = {e['filename'] for e in json.loads(listings_path.read_text())}
        except: pass

    new_art = []
    for f in sorted(images_dir.glob('*.png'), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.name not in listed:
            new_art.append(f)

    return new_art[:3]  # Process at most 3 per run

def generate_listing(art_path):
    """
    Generate product title + description for a Gumroad listing.
    Returns (title, description) tuple.
    """
    prompt = f"""Write a Gumroad product listing for a Gaza Rose digital art piece.

Filename: {art_path.name}

Provide:
1. A compelling product title (max 60 chars)
2. A product description (150-250 words) that:
   - Describes the art emotionally and visually
   - Explains the Gaza Rose project and its meaning
   - States clearly: 70% of proceeds go to Palestinian children via PCRF
   - Includes PCRF link: https://www.pcrf.net
   - Notes it's a high-resolution digital download
   - Feels like art, not marketing

Respond as JSON only:
{{"title": "...", "description": "..."}}
"""
    result = ask_llm(prompt)
    if not result: return None, None
    try:
        start = result.find('{')
        end   = result.rfind('}') + 1
        parsed = json.loads(result[start:end])
        return parsed.get('title', ''), parsed.get('description', '')
    except:
        return None, None

def create_gumroad_product(title, description, art_path):
    """Create a Gumroad product listing via API."""
    if not GUMROAD_TOKEN:
        print('[gumroad] No GUMROAD_TOKEN — will queue for manual listing')
        return None

    try:
        # Build the public URL for the art (GitHub Pages)
        repo_base = 'https://meekotharaccoon-cell.github.io/meeko-nerve-center'
        image_url = f'{repo_base}/images/{art_path.name}'

        data = urlencode({
            'access_token':  GUMROAD_TOKEN,
            'name':          title,
            'description':   description,
            'price':         DEFAULT_PRICE_CENTS,
            'url':           image_url,
            'published':     'true',
            'tags':          'gaza rose, palestine, solidarity, digital art, humanitarian',
        }).encode()

        req = urllib_request.Request(
            f'{GUMROAD_API}/products',
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        with urllib_request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
            if result.get('success'):
                product = result.get('product', {})
                print(f'[gumroad] Listed: {title} — {product.get("short_url", "")}')
                return product
    except Exception as e:
        print(f'[gumroad] API error: {e}')
    return None

def email_listing_draft(title, description, art_name):
    """Email a ready-to-paste Gumroad listing draft."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    body = f"""New Gaza Rose art needs a Gumroad listing. Here's the ready-to-paste content.

Art file: {art_name}

{'='*50}
TITLE:
{title}

DESCRIPTION:
{description}

PRICE: $5.00
TAGS: gaza rose, palestine, solidarity, digital art, humanitarian
{'='*50}

Create listing at: https://gumroad.com/products/new

Or add GUMROAD_TOKEN to your GitHub secrets to automate this fully.
"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🛍️ Gumroad listing ready: {title[:40]}'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[gumroad] Draft emailed')
    except Exception as e:
        print(f'[gumroad] Email failed: {e}')

def log_listing(art_name, title, product_id, listed_via_api):
    log_path = DATA / 'gumroad_listings.json'
    log = []
    if log_path.exists():
        try: log = json.loads(log_path.read_text())
        except: pass
    log.append({
        'date':           TODAY,
        'filename':       art_name,
        'title':          title,
        'gumroad_id':     product_id,
        'listed_via_api': listed_via_api,
    })
    try: log_path.write_text(json.dumps(log, indent=2))
    except: pass

def run():
    print(f'\n[gumroad] Gumroad Listing Update Engine — {TODAY}')

    art_files = find_unlisted_art()
    if not art_files:
        print('[gumroad] No unlisted art found. All caught up.')
        return

    print(f'[gumroad] {len(art_files)} unlisted art piece(s) found')

    for art_path in art_files:
        print(f'[gumroad] Processing: {art_path.name}')
        title, description = generate_listing(art_path)
        if not title or not description:
            print(f'[gumroad] Could not generate listing for {art_path.name}')
            continue

        product = create_gumroad_product(title, description, art_path)

        if product:
            log_listing(art_path.name, title, product.get('id'), True)
        else:
            email_listing_draft(title, description, art_path.name)
            log_listing(art_path.name, title, None, False)

    print('[gumroad] Done.')

if __name__ == '__main__':
    run()
