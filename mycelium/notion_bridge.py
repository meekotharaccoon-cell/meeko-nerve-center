#!/usr/bin/env python3
"""
Notion Bridge
=============
Writes daily system outputs directly into Notion.
Requires: NOTION_TOKEN secret (get from notion.so/my-integrations)

What it writes:
  1. Daily Strategy page   -> Notion database
  2. Content Queue         -> Notion database  
  3. System Health report  -> Notion page
  4. FIXES_NEEDED content  -> Notion page
  5. Draft Emails          -> Notion database

Setup (one time, 5 minutes):
  1. Go to https://www.notion.so/my-integrations
  2. Create integration called "Meeko Nerve Center"
  3. Copy the token -> add as NOTION_TOKEN in GitHub Secrets
  4. In Notion, create a page called "Meeko Nerve Center"
  5. Share that page with your integration (click Share -> invite)
  6. Run this script once to auto-create all databases
"""

import os, json, datetime, urllib.request, urllib.error
from pathlib import Path

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / 'data'
TODAY  = datetime.date.today().isoformat()

NOTION_TOKEN   = os.environ.get('NOTION_TOKEN', '')
NOTION_VERSION = '2022-06-28'
NOTION_API     = 'https://api.notion.com/v1'

# ── HTTP helpers ──────────────────────────────────────────────────
def notion_request(method, path, body=None):
    if not NOTION_TOKEN:
        print('[notion] No NOTION_TOKEN - skipping')
        return None
    url = NOTION_API + path
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, method=method, headers={
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Notion-Version': NOTION_VERSION,
        'Content-Type': 'application/json',
    })
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f'[notion] HTTP {e.code}: {e.read().decode()[:200]}')
        return None
    except Exception as e:
        print(f'[notion] Error: {e}')
        return None

def search_notion(query):
    return notion_request('POST', '/search', {'query': query, 'page_size': 5})

def find_or_create_parent_page(title='Meeko Nerve Center'):
    """Find the parent page by searching for it."""
    results = search_notion(title)
    if results:
        for r in results.get('results', []):
            if r.get('object') == 'page':
                t = r.get('properties', {}).get('title', {}).get('title', [])
                if t and title.lower() in t[0].get('plain_text', '').lower():
                    return r['id']
    return None

def create_page(parent_id, title, content_blocks):
    """Create or update a page under parent_id."""
    return notion_request('POST', '/pages', {
        'parent': {'page_id': parent_id},
        'properties': {
            'title': {'title': [{'text': {'content': title}}]}
        },
        'children': content_blocks
    })

def text_block(text, bold=False):
    annotations = {'bold': bold}
    return {
        'object': 'block', 'type': 'paragraph',
        'paragraph': {'rich_text': [{
            'type': 'text', 'text': {'content': str(text)[:2000]},
            'annotations': annotations
        }]}
    }

def heading_block(text, level=2):
    t = f'heading_{level}'
    return {'object': 'block', 'type': t, t: {
        'rich_text': [{'type': 'text', 'text': {'content': str(text)[:300]}}]
    }}

def divider_block():
    return {'object': 'block', 'type': 'divider', 'divider': {}}

def code_block(text):
    return {
        'object': 'block', 'type': 'code',
        'code': {
            'rich_text': [{'type': 'text', 'text': {'content': str(text)[:2000]}}],
            'language': 'plain text'
        }
    }

# ── Write functions ────────────────────────────────────────────────
def write_daily_report(parent_id):
    """Write today's full system report to Notion."""
    blocks = [
        heading_block(f'System Report — {TODAY}', 1),
        divider_block(),
    ]

    # Strategy
    strat_path = DATA / 'strategy.json'
    if strat_path.exists():
        try:
            s = json.loads(strat_path.read_text())
            blocks += [
                heading_block('Strategy Today', 2),
                text_block(f"Primary crisis: {s.get('primary_crisis', 'Gaza')}"),
                text_block(f"Revenue focus: {s.get('revenue_channel', 'gallery')}"),
                text_block(f"Reasoning: {s.get('reasoning', 'Rule-based')}"[:500]),
                divider_block(),
            ]
        except: pass

    # What's working
    ww_path = DATA / 'what_works.json'
    if ww_path.exists():
        try:
            ww = json.loads(ww_path.read_text())
            summary = ww.get('summary', {})
            blocks += [
                heading_block('Signal Data (What Works)', 2),
                text_block(f"Total 14-day views: {summary.get('total_14d_views', 0)}"),
                text_block(f"Top content: {summary.get('top_content', 'N/A')}"),
                text_block(f"Top channel: {summary.get('top_channel', 'N/A')}"),
                divider_block(),
            ]
        except: pass

    # Healer status
    heal_path = DATA / 'heal_report.json'
    if heal_path.exists():
        try:
            h = json.loads(heal_path.read_text())
            blocks += [
                heading_block('System Health', 2),
                text_block(f"Auto-healed total: {h.get('total_healed', 0)}"),
                text_block(f"Open issues: {h.get('needs_human', 0)}"),
                divider_block(),
            ]
        except: pass

    # Fixes needed
    fixes_path = ROOT / 'FIXES_NEEDED.md'
    if fixes_path.exists():
        fixes = fixes_path.read_text()[:3000]
        blocks += [
            heading_block('Fixes Needed', 2),
            code_block(fixes),
            divider_block(),
        ]

    blocks.append(text_block(
        f'Repo: https://github.com/meekotharaccoon-cell/meeko-nerve-center | '
        f'Dashboard: https://meekotharaccoon-cell.github.io/meeko-nerve-center/dashboard.html'
    ))

    result = create_page(parent_id, f'Daily Report {TODAY}', blocks)
    if result:
        print(f'[notion] Daily report written: {result.get("url", "ok")}')
    return result

def write_content_queue(parent_id):
    """Write today's content queue to Notion."""
    queue_path = ROOT / 'content' / 'queue' / 'latest.json'
    if not queue_path.exists():
        print('[notion] No content queue found')
        return
    try:
        queue = json.loads(queue_path.read_text())
    except:
        return

    blocks = [
        heading_block(f'Content Queue — {TODAY}', 1),
        text_block('Copy any of these posts to share manually. System tracks which get the best engagement.'),
        divider_block(),
    ]

    posts = queue if isinstance(queue, list) else queue.get('posts', [])
    for i, post in enumerate(posts[:10], 1):
        platform = post.get('platform', 'general')
        text     = post.get('text', str(post))[:500]
        blocks += [
            heading_block(f'Post {i} ({platform})', 3),
            code_block(text),
        ]

    result = create_page(parent_id, f'Content Queue {TODAY}', blocks)
    if result:
        print(f'[notion] Content queue written: {result.get("url", "ok")}')
    return result

def write_draft_emails(parent_id):
    """Write DRAFT_EMAILS.md to Notion."""
    emails_path = ROOT / 'DRAFT_EMAILS.md'
    if not emails_path.exists():
        print('[notion] No DRAFT_EMAILS.md found')
        return
    content = emails_path.read_text()[:5000]
    blocks  = [
        heading_block(f'Draft Emails — {TODAY}', 1),
        text_block('Review each email below, then copy/paste into your email client.'),
        divider_block(),
        code_block(content),
    ]
    result = create_page(parent_id, f'Draft Emails {TODAY}', blocks)
    if result:
        print(f'[notion] Draft emails written: {result.get("url", "ok")}')
    return result

# ── Main ──────────────────────────────────────────────────────────
def run():
    if not NOTION_TOKEN:
        print('[notion] NOTION_TOKEN not set.')
        print('[notion] Setup:')
        print('  1. Go to https://www.notion.so/my-integrations')
        print('  2. Create integration: "Meeko Nerve Center"')
        print('  3. Copy token -> GitHub repo Settings -> Secrets -> NOTION_TOKEN')
        print('  4. In Notion, create a page "Meeko Nerve Center" and share with the integration')
        return

    print('[notion] Finding parent page...')
    parent_id = find_or_create_parent_page('Meeko Nerve Center')
    if not parent_id:
        print('[notion] Parent page not found. Create a Notion page called "Meeko Nerve Center"')
        print('[notion] Then share it with your integration (Share -> Invite -> your integration)')
        return

    print(f'[notion] Parent page: {parent_id}')
    write_daily_report(parent_id)
    write_content_queue(parent_id)
    write_draft_emails(parent_id)
    print('[notion] Done. Open Notion to see your updates.')

if __name__ == '__main__':
    run()
