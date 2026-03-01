#!/usr/bin/env python3
"""
Social Poster — v2 (Directive + Memory Aware)
=============================================
Now reads directives and memory context before generating posts.

If human said "double down on viral fork angle" → posts emphasize forks.
If human said "pause mastodon" → skips Mastodon.
If memory says "shorter posts get more engagement" → uses that.

This is the engine that talks to the world.
Now it listens to you first.
"""

import json, os, datetime
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import urlencode

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M')

MASTODON_TOKEN     = os.environ.get('MASTODON_TOKEN', '')
MASTODON_BASE_URL  = os.environ.get('MASTODON_BASE_URL', 'https://mastodon.social')
BLUESKY_HANDLE     = os.environ.get('BLUESKY_HANDLE', '')
BLUESKY_APP_PWD    = os.environ.get('BLUESKY_APP_PASSWORD', '') or os.environ.get('BLUESKY_PASSWORD', '')
HF_TOKEN           = os.environ.get('HF_TOKEN', '')


def load_json(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}


# ── Load directive + memory context ─────────────────────────────────────────
def load_directives():
    d = load_json(DATA / 'directives.json')
    if d and d.get('date') == TODAY:
        return d
    return {'pause': [], 'priority': [], 'amplify': [], 'suppress': [],
            'build_next': None, 'tone': None, 'human_message': ''}

def load_content_context():
    """Get memory context for content generation."""
    memory = load_json(DATA / 'long_term_memory.json')
    if not memory: return ''
    ctx = memory.get('contexts', {})
    if ctx.get('updated') == TODAY:
        return ctx.get('social_poster', '') or ctx.get('content_engine', '') or ctx.get('general', '')
    return ''

def load_brain_state():
    """Get today's brain state for context."""
    return load_json(DATA / 'three_d_brain.json')


# ── Generate post with context ────────────────────────────────────────────────
def generate_post(topic, directives, memory_ctx, brain):
    """Generate a social post informed by directives and memory."""
    if not HF_TOKEN:
        return _fallback_post(topic, directives)

    # Build context from directives
    directive_notes = ''
    if directives.get('human_message'):
        directive_notes += f"Human's focus today: {directives['human_message']}. "
    if 'viral' in directives.get('amplify', []) or 'fork' in directives.get('amplify', []):
        directive_notes += 'Emphasize the fork/viral angle. '
    tone = directives.get('tone', 'normal')
    if tone == 'urgent':
        directive_notes += 'Tone: urgent, call to action. '
    elif tone == 'experimental':
        directive_notes += 'Tone: experimental, try something different. '

    # Brain state context
    brain_notes = ''
    if brain:
        rev   = brain.get('revenue', {})
        reach = brain.get('reach', {})
        impact = brain.get('impact', {})
        brain_notes = (
            f'Current state: ${rev.get("grand_total", 0):.2f} revenue, '
            f'{reach.get("github_forks", 0)} forks, '
            f'impact score {impact.get("impact_score", 0)}/100. '
        )

    system_prompt = (
        'You write authentic social media posts for a SolarPunk autonomous AI project.\n'
        + (f'Memory context: {memory_ctx}\n' if memory_ctx else '')
        + (f'Brain state: {brain_notes}\n' if brain_notes else '')
        + (f'Directive: {directive_notes}\n' if directive_notes else '')
        + 'Posts are real, not promotional. Show the actual work. 250-400 chars. No hashtag spam.'
    )

    topics = {
        'daily_state': f'Write a brief authentic post about the system\'s current state and what it\'s working on today. Make it feel real, not like marketing. Include {brain_notes}',
        'product':     'Write a post about the $1 AI guide products that fund Palestinian children. Be specific about the cause and the price.',
        'fork':        'Write a post inviting developers to fork this autonomous AI system. Emphasize it costs $0/month and is genuinely useful.',
        'grant':       'Write a post about pursuing grants to fund ethical AI + Palestinian solidarity work.',
        'art':         'Write a post about the Gaza Rose generative art series and its cause.',
        'congress':    'Write a post about tracking congressional stock trades for accountability.',
    }
    user_prompt = topics.get(topic, topics['daily_state'])

    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': 300,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[social] LLM error: {e}')
        return _fallback_post(topic, directives)

def _fallback_post(topic, directives):
    templates = {
        'daily_state': f'🌹 SolarPunk AI running daily cycle [{TODAY}]. Congressional tracking, grant hunting, cause commerce. $0/month. Open source.\n\nhttps://github.com/meekotharaccoon-cell/meeko-nerve-center\n\n#SolarPunk #EthicalAI',
        'fork':        f'🌱 Fork this autonomous AI system free:\nhttps://github.com/meekotharaccoon-cell/meeko-nerve-center\n\nRuns on GitHub Actions. $0/month. Self-evolving. 70% to PCRF.\n\n#OpenSource #SolarPunk',
        'product':     f'🌹 $1 AI guides → 70% to Palestinian children\'s medical relief.\nhttps://github.com/meekotharaccoon-cell/meeko-nerve-center\n\n#CauseCommerce #Palestine #PCRF',
    }
    return templates.get(topic, templates['daily_state'])


# ── Post to Mastodon ──────────────────────────────────────────────────────────
def post_mastodon(text):
    if not MASTODON_TOKEN:
        print('[social] No MASTODON_TOKEN')
        return False
    base = MASTODON_BASE_URL.rstrip('/')
    body = urlencode({'status': text, 'visibility': 'public'}).encode()
    req  = urllib_request.Request(
        f'{base}/api/v1/statuses',
        data=body,
        headers={'Authorization': f'Bearer {MASTODON_TOKEN}',
                 'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST'
    )
    try:
        with urllib_request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
        if result.get('id'):
            print(f'[social] ✅ Mastodon: {result.get("url", "posted")}')
            return True
        print(f'[social] Mastodon error: {result}')
        return False
    except Exception as e:
        print(f'[social] Mastodon error: {e}')
        return False


# ── Post to Bluesky ──────────────────────────────────────────────────────────
def post_bluesky(text):
    if not BLUESKY_HANDLE or not BLUESKY_APP_PWD:
        print('[social] No Bluesky credentials')
        return False
    try:
        # Auth
        auth_req = urllib_request.Request(
            'https://bsky.social/xrpc/com.atproto.server.createSession',
            data=json.dumps({'identifier': BLUESKY_HANDLE, 'password': BLUESKY_APP_PWD}).encode(),
            headers={'Content-Type': 'application/json'}, method='POST'
        )
        with urllib_request.urlopen(auth_req, timeout=15) as r:
            auth = json.loads(r.read())
        token = auth.get('accessJwt')
        did   = auth.get('did')
        if not token:
            print(f'[social] Bluesky auth failed')
            return False
        # Post
        post_req = urllib_request.Request(
            'https://bsky.social/xrpc/com.atproto.repo.createRecord',
            data=json.dumps({
                'repo': did, 'collection': 'app.bsky.feed.post',
                'record': {
                    'text': text[:300],
                    'createdAt': datetime.datetime.utcnow().isoformat() + 'Z',
                    '$type': 'app.bsky.feed.post',
                }
            }).encode(),
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib_request.urlopen(post_req, timeout=15) as r:
            result = json.loads(r.read())
        if result.get('uri'):
            print(f'[social] ✅ Bluesky: {result["uri"]}')
            return True
        print(f'[social] Bluesky post error: {result}')
        return False
    except Exception as e:
        print(f'[social] Bluesky error: {e}')
        return False


# ── Log post ─────────────────────────────────────────────────────────────────
def log_post(platform, text, success):
    log_path = DATA / 'social_posts.json'
    log = load_json(log_path, [])
    log.append({
        'timestamp': NOW, 'platform': platform,
        'text': text[:500], 'success': success,
        'directive_context': load_directives().get('human_message', ''),
    })
    try: log_path.write_text(json.dumps(log[-200:], indent=2))
    except: pass


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    print(f'\n[social] Social Poster v2 (Directive + Memory Aware) — {TODAY}')

    directives  = load_directives()
    memory_ctx  = load_content_context()
    brain       = load_brain_state()

    if memory_ctx:
        print(f'[social] Memory context: {memory_ctx[:100]}...')
    if directives.get('human_message'):
        print(f'[social] 🎯 Directive: {directives["human_message"]}')

    # Check for suppressed platforms
    paused = [p.lower() for p in directives.get('pause', [])]
    mastodon_active = 'mastodon' not in paused and 'social' not in paused
    bluesky_active  = 'bluesky'  not in paused and 'social' not in paused

    if not mastodon_active: print('[social] Mastodon paused by directive')
    if not bluesky_active:  print('[social] Bluesky paused by directive')

    # Choose topic based on directives + brain state
    amplify = [a.lower() for a in directives.get('amplify', [])]
    priority = [p.lower() for p in directives.get('priority', [])]

    if 'fork' in amplify or 'viral' in amplify:
        topic = 'fork'
    elif 'product' in priority or 'gumroad' in priority:
        topic = 'product'
    elif 'grants' in priority or 'grants' in amplify:
        topic = 'grant'
    elif 'art' in amplify:
        topic = 'art'
    else:
        topic = 'daily_state'

    print(f'[social] Topic: {topic} (from directives + brain state)')

    # Generate post
    post_text = generate_post(topic, directives, memory_ctx, brain)
    print(f'[social] Generated post ({len(post_text)} chars):')
    print(f'  {post_text[:120]}...')

    # Post to active platforms
    results = []
    if mastodon_active and MASTODON_TOKEN:
        ok = post_mastodon(post_text)
        log_post('mastodon', post_text, ok)
        results.append(('mastodon', ok))

    if bluesky_active and BLUESKY_HANDLE and BLUESKY_APP_PWD:
        ok = post_bluesky(post_text)
        log_post('bluesky', post_text, ok)
        results.append(('bluesky', ok))

    success_count = sum(1 for _, ok in results if ok)
    print(f'[social] Done. Posted to {success_count}/{len(results)} platforms.')


if __name__ == '__main__':
    run()
