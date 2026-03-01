#!/usr/bin/env python3
"""
Notion Directives Reader — Phase 0 of every cycle
===================================================
This is how YOU steer the system without touching code.

Create a Notion page called "DIRECTIVES" and write anything:
  - "Focus on grants this week, Gumroad traffic is low"
  - "Don't post on Mastodon until Friday"
  - "Priority: product 11 — build it about Ollama vision models"
  - "PAUSE: email system, something is wrong"
  - "double down on the viral fork angle"

This script runs as Phase 0 — before ANYTHING else.
It reads your directives, parses them with HF inference into structured
commands, and writes data/directives.json which every other engine reads
at startup.

Result: your words become system behavior within one cycle.
No code changes. No GitHub commits. Just Notion.
"""

import json, os, datetime
from pathlib import Path
from urllib import request as urllib_request
from urllib.error import HTTPError

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

NOTION_TOKEN   = os.environ.get('NOTION_TOKEN', '')
NOTION_VERSION = '2022-06-28'
NOTION_API     = 'https://api.notion.com/v1'
HF_TOKEN       = os.environ.get('HF_TOKEN', '')

# ── HTTP helpers ──────────────────────────────────────────────────────────────
def notion_req(method, path, body=None):
    if not NOTION_TOKEN:
        return None
    url = NOTION_API + path
    data = json.dumps(body).encode() if body else None
    req = urllib_request.Request(url, data=data, method=method, headers={
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Notion-Version': NOTION_VERSION,
        'Content-Type': 'application/json',
    })
    try:
        with urllib_request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except HTTPError as e:
        print(f'[directives] Notion {e.code}: {e.read().decode()[:200]}')
        return None
    except Exception as e:
        print(f'[directives] Notion error: {e}')
        return None

def hf_infer(prompt, max_tokens=800):
    if not HF_TOKEN:
        return None
    payload = json.dumps({
        'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
        'max_tokens': max_tokens,
        'messages': [
            {'role': 'system', 'content': 'You parse human directives into structured JSON for an autonomous AI system. Return only valid JSON, no markdown, no explanation.'},
            {'role': 'user', 'content': prompt}
        ]
    }).encode()
    try:
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=30) as r:
            text = json.loads(r.read())['choices'][0]['message']['content'].strip()
        s = text.find('{')
        e = text.rfind('}') + 1
        if s >= 0 and e > s:
            return json.loads(text[s:e])
    except Exception as e:
        print(f'[directives] HF error: {e}')
    return None


# ── Notion page reader ────────────────────────────────────────────────────────
def find_directives_page():
    """Search Notion for the DIRECTIVES page."""
    result = notion_req('POST', '/search', {
        'query': 'DIRECTIVES',
        'filter': {'value': 'page', 'property': 'object'},
        'page_size': 10
    })
    if not result:
        return None
    for r in result.get('results', []):
        if r.get('object') != 'page':
            continue
        # Get title from properties
        props = r.get('properties', {})
        title_prop = props.get('title', {}).get('title', [])
        title_text = ''.join(t.get('plain_text', '') for t in title_prop)
        if 'DIRECTIVE' in title_text.upper():
            return r['id']
    return None

def read_page_blocks(page_id):
    """Read all text blocks from a Notion page."""
    result = notion_req('GET', f'/blocks/{page_id}/children?page_size=100')
    if not result:
        return ''
    lines = []
    for block in result.get('results', []):
        btype = block.get('type', '')
        rich = block.get(btype, {}).get('rich_text', [])
        text = ''.join(t.get('plain_text', '') for t in rich)
        if text.strip():
            lines.append(text.strip())
    return '\n'.join(lines)


# ── Parse directives ──────────────────────────────────────────────────────────
def parse_directives(raw_text):
    """
    Parse freeform human text into structured directives.
    Falls back to simple keyword parsing if HF unavailable.
    """
    text_lower = raw_text.lower()

    # Default structure
    directives = {
        'date': TODAY,
        'raw': raw_text[:2000],
        'pause': [],          # engines to pause
        'priority': [],       # what to focus on
        'suppress': [],       # topics/channels to suppress
        'amplify': [],        # things to do more of
        'build_next': None,   # specific product/feature to build
        'tone': None,         # 'urgent', 'calm', 'experimental'
        'human_message': '',  # anything else for the system to know
        'parsed_by': 'keyword',
    }

    # Keyword fallback parsing
    if 'pause' in text_lower or 'stop' in text_lower:
        for engine in ['email', 'mastodon', 'bluesky', 'gumroad', 'grants', 'social']:
            if engine in text_lower:
                directives['pause'].append(engine)

    if 'focus' in text_lower or 'priority' in text_lower:
        for topic in ['grants', 'gumroad', 'products', 'social', 'content', 'viral', 'email']:
            if topic in text_lower:
                directives['priority'].append(topic)

    if 'double down' in text_lower or 'amplify' in text_lower or 'more' in text_lower:
        for topic in ['grants', 'gumroad', 'fork', 'viral', 'content', 'art', 'mastodon']:
            if topic in text_lower:
                directives['amplify'].append(topic)

    if 'build' in text_lower and ('product' in text_lower or 'feature' in text_lower):
        # Extract what comes after 'build'
        idx = text_lower.find('build')
        snippet = raw_text[idx:idx+100].strip()
        directives['build_next'] = snippet

    # Try HF for richer parsing
    if HF_TOKEN and raw_text.strip():
        parsed = hf_infer(f"""Parse these human directives for an autonomous AI system into JSON.

Directives text:
{raw_text[:1000]}

Return JSON with these fields:
{{
  "pause": ["list of engines/systems to pause"],
  "priority": ["list of things to focus on"],
  "suppress": ["list of things to do less of"],
  "amplify": ["list of things to do more of"],
  "build_next": "specific thing to build or null",
  "tone": "urgent|calm|experimental|normal",
  "human_message": "summary of what the human wants in 1 sentence"
}}""")
        if parsed:
            for key in ['pause', 'priority', 'suppress', 'amplify', 'build_next', 'tone', 'human_message']:
                if parsed.get(key):
                    directives[key] = parsed[key]
            directives['parsed_by'] = 'llm'

    return directives


# ── Write directives to repo ──────────────────────────────────────────────────
def write_directives(directives):
    DATA.mkdir(parents=True, exist_ok=True)
    path = DATA / 'directives.json'
    path.write_text(json.dumps(directives, indent=2))
    print(f'[directives] Written to data/directives.json')


# ── Create the DIRECTIVES page if it doesn't exist ───────────────────────────
def ensure_directives_page():
    """Create a starter DIRECTIVES page in Notion if none exists."""
    result = notion_req('POST', '/pages', {
        'parent': {'type': 'workspace', 'workspace': True},
        'properties': {
            'title': [{'type': 'text', 'text': {'content': 'DIRECTIVES — Steer the System'}}]
        },
        'children': [
            {'object': 'block', 'type': 'callout', 'callout': {
                'rich_text': [{'type': 'text', 'text': {'content': 'Write your directives below. This page is read by the system at the start of every cycle. Plain English. No special syntax required.'}}],
                'icon': {'type': 'emoji', 'emoji': '🎯'},
                'color': 'green_background'
            }},
            {'object': 'block', 'type': 'heading_2', 'heading_2': {
                'rich_text': [{'type': 'text', 'text': {'content': 'Current Directives'}}]
            }},
            {'object': 'block', 'type': 'paragraph', 'paragraph': {
                'rich_text': [{'type': 'text', 'text': {'content': 'No directives yet — system running on default strategy.'}}]
            }},
            {'object': 'block', 'type': 'divider', 'divider': {}},
            {'object': 'block', 'type': 'heading_2', 'heading_2': {
                'rich_text': [{'type': 'text', 'text': {'content': 'Examples'}}]
            }},
            {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {
                'rich_text': [{'type': 'text', 'text': {'content': '"Focus on grants this week — Gumroad traffic is low"'}}]
            }},
            {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {
                'rich_text': [{'type': 'text', 'text': {'content': '"Pause email system until Saturday"'}}]
            }},
            {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {
                'rich_text': [{'type': 'text', 'text': {'content': '"Build product 11 about Ollama vision models"'}}]
            }},
            {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {
                'rich_text': [{'type': 'text', 'text': {'content': '"Double down on the viral fork angle, it is getting traction"'}}]
            }},
            {'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {
                'rich_text': [{'type': 'text', 'text': {'content': '"Urgent: the grant deadline is Friday, prioritize grant_auto_submitter"'}}]
            }},
        ]
    })
    if result and not result.get('error'):
        print(f'[directives] Created DIRECTIVES page: {result.get("url", "ok")}')
        return result['id']
    return None


# ── Context injector (called by other engines) ────────────────────────────────
def get_directives():
    """Called by other engines at startup to check for active directives."""
    path = DATA / 'directives.json'
    if path.exists():
        try:
            d = json.loads(path.read_text())
            if d.get('date') == TODAY:
                return d
        except:
            pass
    return {'date': TODAY, 'pause': [], 'priority': [], 'suppress': [], 'amplify': [], 'build_next': None, 'tone': None, 'human_message': '', 'raw': ''}

def is_paused(engine_name):
    """Quick check: should this engine skip this cycle?"""
    d = get_directives()
    paused = [p.lower() for p in d.get('pause', [])]
    return any(engine_name.lower() in p or p in engine_name.lower() for p in paused)


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    print(f'\n[directives] Phase 0 — Reading human directives from Notion')

    if not NOTION_TOKEN:
        print('[directives] No NOTION_TOKEN — writing empty directives')
        write_directives(get_directives())
        return

    # Find DIRECTIVES page
    page_id = find_directives_page()

    if not page_id:
        print('[directives] No DIRECTIVES page found — creating one')
        page_id = ensure_directives_page()
        if not page_id:
            print('[directives] Could not create page — writing empty directives')
            write_directives(get_directives())
            return
        # New page has no directives yet
        directives = get_directives()
        directives['human_message'] = 'DIRECTIVES page just created — waiting for human input'
        write_directives(directives)
        print('[directives] DIRECTIVES page created in Notion. Go write your priorities there!')
        return

    # Read the page
    raw_text = read_page_blocks(page_id)
    print(f'[directives] Read {len(raw_text)} chars from DIRECTIVES page')

    if not raw_text.strip() or 'No directives yet' in raw_text:
        print('[directives] No active directives — system running on default strategy')
        write_directives(get_directives())
        return

    # Parse directives
    directives = parse_directives(raw_text)
    write_directives(directives)

    # Report
    print(f'[directives] Parsed by: {directives["parsed_by"]}')
    if directives['pause']:
        print(f'[directives] PAUSED: {directives["pause"]}')
    if directives['priority']:
        print(f'[directives] PRIORITY: {directives["priority"]}')
    if directives['amplify']:
        print(f'[directives] AMPLIFY: {directives["amplify"]}')
    if directives['build_next']:
        print(f'[directives] BUILD NEXT: {directives["build_next"]}')
    if directives['human_message']:
        print(f'[directives] MESSAGE: {directives["human_message"]}')
    print('[directives] Done. All engines will read this before acting.')


if __name__ == '__main__':
    run()
