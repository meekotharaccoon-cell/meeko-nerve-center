#!/usr/bin/env python3
"""
Wikipedia Contribution Engine
================================
The system consumes Wikipedia data but never gives back.
This ends that.

What it does:
  1. Reads congressional trade data and world events from data/
  2. Identifies facts that could support or improve Wikipedia articles
     on Palestinian history, PCRF, congressional ethics, etc.
  3. Uses the LLM to draft proper Wikipedia citation suggestions
     formatted as talk page comments
  4. Saves drafts to data/wikipedia_drafts.json
  5. Posts the most compelling draft as a social post
     (because public accountability is itself a form of contribution)
  6. Emails you a weekly digest of pending contributions

We don't auto-edit Wikipedia (that requires human judgment and accounts).
But we surface what's worth adding, formatted and ready.
"""

import json, datetime, os, smtplib
from pathlib import Path
from urllib import request as urllib_request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'

TODAY    = datetime.date.today().isoformat()
WEEKDAY  = datetime.date.today().weekday()  # 0=Mon

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

# Wikipedia articles relevant to our mission
TARGET_ARTICLES = [
    'Palestinian Children\'s Relief Fund',
    'STOCK Act',
    'Congressional ethics',
    'Gaza Strip',
    'Palestinian refugees',
    'Open-source software for humanitarian aid',
]

def ask_llm(prompt, max_tokens=600):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': 'You are a Wikipedia editor who writes neutral, well-cited talk page suggestions. Factual, NPOV, properly formatted.'},
                {'role': 'user', 'content': prompt}
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
        print(f'[wiki] LLM error: {e}')
        return None

def gather_notable_facts():
    """Collect notable verifiable facts from our data sources."""
    facts = []

    # Congressional trades
    congress_path = DATA / 'congress.json'
    if congress_path.exists():
        try:
            data = json.loads(congress_path.read_text())
            trades = data if isinstance(data, list) else data.get('trades', [])
            for t in trades[:5]:
                ticker = t.get('ticker', '')
                member = t.get('representative', t.get('senator', ''))
                date   = t.get('transaction_date', t.get('date', ''))
                if ticker and member and date:
                    facts.append({
                        'type':    'congressional_trade',
                        'article': 'STOCK Act',
                        'fact':    f'{member} traded {ticker} on {date}',
                        'source':  'https://efts.house.gov/LATEST/search-index?q=%22stock+act%22',
                    })
        except: pass

    # PCRF/humanitarian data
    donation_path = DATA / 'donation_context.json'
    if donation_path.exists():
        try:
            ctx = json.loads(donation_path.read_text())
            if ctx.get('pcrf_impact'):
                facts.append({
                    'type':    'pcrf_impact',
                    'article': "Palestinian Children's Relief Fund",
                    'fact':    str(ctx['pcrf_impact']),
                    'source':  'https://www.pcrf.net/about-us/',
                })
        except: pass

    # World events relevant to Gaza/Palestine
    world_path = DATA / 'world_state.json'
    if world_path.exists():
        try:
            world = json.loads(world_path.read_text())
            events = world.get('events', world.get('news', []))
            for e in events[:3]:
                title = e.get('title', e.get('headline', ''))
                if any(kw in title.lower() for kw in ['gaza', 'palestine', 'pcrf', 'west bank']):
                    facts.append({
                        'type':    'news_event',
                        'article': 'Gaza Strip',
                        'fact':    title,
                        'source':  e.get('url', e.get('link', '')),
                    })
        except: pass

    return facts

def draft_wiki_contribution(fact):
    """Draft a Wikipedia talk page comment for a notable fact."""
    prompt = f"""Draft a Wikipedia talk page suggestion for the article "{fact['article']}".

Fact to add or support: {fact['fact']}
Source: {fact['source']}

Write it as a proper Wikipedia talk page comment:
- Neutral point of view (NPOV)
- Suggest where in the article it could go
- Include proper citation format using the source URL
- Note it as a suggestion, not an edit
- Under 150 words
- Use standard Wikipedia talk page format (== Section == and ~~~~)

Just the talk page comment.
"""
    return ask_llm(prompt, max_tokens=300)

def generate_accountability_post(facts):
    """Turn the most notable fact into a public accountability post."""
    if not facts: return None
    # Prefer congressional trades for maximum accountability impact
    best = next((f for f in facts if f['type'] == 'congressional_trade'), facts[0])
    prompt = f"""Turn this verifiable public record fact into a 280-character accountability post:

Fact: {best['fact']}
Source: {best['source']}

Make it:
- Factual and specific
- Connected to public accountability
- Include the source URL
- End with a relevant hashtag (#STOCKAct or #PalestinianSolidarity)

Just the post text.
"""
    return ask_llm(prompt, max_tokens=150)

def send_weekly_digest(drafts):
    """Email a weekly digest of pending Wikipedia contributions."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
    if WEEKDAY != 0: return  # Only Mondays

    pending = [d for d in drafts if not d.get('submitted')]
    if not pending: return

    lines = [f'Wikipedia contribution digest — {len(pending)} pending drafts\n']
    for d in pending[:5]:
        lines += [
            f'Article: {d["article"]}',
            f'Date:    {d["date"]}',
            f'Draft:   {d["draft"][:200]}',
            '',
        ]
    lines.append('Submit at: https://en.wikipedia.org/wiki/[Article]/Talk')

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'📚 Wikipedia contributions ready: {len(pending)} drafts'
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText('\n'.join(lines), 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print('[wiki] Weekly digest sent')
    except Exception as e:
        print(f'[wiki] Digest email failed: {e}')

def run():
    print(f'\n[wiki] Wikipedia Contribution Engine — {TODAY}')

    facts = gather_notable_facts()
    if not facts:
        print('[wiki] No notable facts found today.')
        return

    print(f'[wiki] Found {len(facts)} notable facts')

    # Load existing drafts
    drafts_path = DATA / 'wikipedia_drafts.json'
    drafts = []
    if drafts_path.exists():
        try: drafts = json.loads(drafts_path.read_text())
        except: pass

    # Don't re-draft things already in the log
    existing_facts = {d['fact'] for d in drafts}
    new_facts = [f for f in facts if f['fact'] not in existing_facts]

    for fact in new_facts[:2]:  # Max 2 drafts per run
        print(f'[wiki] Drafting contribution for: {fact["article"]}')
        draft_text = draft_wiki_contribution(fact)
        if draft_text:
            drafts.append({
                'date':      TODAY,
                'article':   fact['article'],
                'fact':      fact['fact'],
                'source':    fact['source'],
                'draft':     draft_text,
                'submitted': False,
            })

    # Save drafts
    try:
        drafts_path.write_text(json.dumps(drafts, indent=2))
        print(f'[wiki] {len(drafts)} total drafts saved')
    except Exception as e:
        print(f'[wiki] Save error: {e}')

    # Queue an accountability post
    post_text = generate_accountability_post(facts)
    if post_text:
        queue_dir = ROOT / 'content' / 'queue'
        queue_dir.mkdir(parents=True, exist_ok=True)
        try:
            (queue_dir / f'wiki_accountability_{TODAY}.json').write_text(
                json.dumps([{'platform': 'all', 'type': 'accountability', 'text': post_text}], indent=2)
            )
            print(f'[wiki] Accountability post queued: {post_text[:80]}')
        except Exception as e:
            print(f'[wiki] Queue error: {e}')

    # Weekly digest
    send_weekly_digest(drafts)

    print('[wiki] Done.')

if __name__ == '__main__':
    run()
