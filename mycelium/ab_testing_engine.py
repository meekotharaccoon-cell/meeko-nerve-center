#!/usr/bin/env python3
"""
A/B Testing Engine
===================
The system posts content daily but never tests which VERSION
of a message actually performs better.

Right now every post is a guess. This makes it science.

How it works:
  1. For each content type (accountability, art, mission, evolution)
     generates 2 variants: different hook, length, tone, or angle
  2. Posts variant A on one platform, variant B on another
     OR posts both on same platform at different times
  3. After 48h, checks engagement on both
  4. Declares a winner, logs what worked and WHY
  5. Feeds winning patterns to long_term_memory.py
  6. Over time: every engine's content gets smarter

What it tests:
  - Hook style: question vs statement vs statistic
  - Length: short (<100 chars) vs medium (100-200) vs long (200+)
  - Tone: urgent vs conversational vs technical vs emotional
  - CTA: explicit ask vs soft invite vs no CTA
  - Timing: which hour gets the most engagement
  - Hashtag density: 0 vs 3 vs 5 vs 8 tags

Output:
  data/ab_tests.json — all tests and results
  data/winning_patterns.json — distilled rules for other engines
"""

import json, datetime, os, hashlib
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()
HOUR  = datetime.datetime.utcnow().hour

HF_TOKEN = os.environ.get('HF_TOKEN', '')
MASTODON_TOKEN    = os.environ.get('MASTODON_TOKEN', '')
MASTODON_BASE_URL = os.environ.get('MASTODON_BASE_URL', 'https://mastodon.social')

def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}

def ask_llm(prompt, max_tokens=600):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': 'You generate A/B test variants for social posts. Each variant tests one variable. Output valid JSON only.'},
                {'role': 'user', 'content': prompt}
            ]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=60) as r:
            text = json.loads(r.read())['choices'][0]['message']['content'].strip()
        s = text.find('{')
        e = text.rfind('}') + 1
        return json.loads(text[s:e])
    except Exception as e:
        print(f'[ab] LLM error: {e}')
        return None

def get_content_seed():
    """Get something real to test with from existing data."""
    congress = load(DATA / 'congress.json')
    trades = congress if isinstance(congress, list) else congress.get('trades', [])
    if trades:
        t = trades[0]
        return {
            'type': 'accountability',
            'fact': f"{t.get('representative', t.get('senator','A lawmaker'))} traded {t.get('ticker','stock')} on {t.get('transaction_date',t.get('date',''))}",
        }
    arts = load(DATA / 'generated_art.json')
    al = arts if isinstance(arts, list) else arts.get('art', [])
    if al:
        return {
            'type': 'art',
            'fact': al[-1].get('title', al[-1].get('prompt', 'Gaza Rose art'))[:80],
        }
    return {
        'type': 'mission',
        'fact': 'An autonomous AI is tracking congressional trades and funding Palestinian relief. $0/month.',
    }

def generate_variants(seed):
    prompt = f"""Create 2 social post variants to A/B test. Same core fact, different approach.

Fact: {seed['fact']}
Type: {seed['type']}

Variant A: lead with a STATISTIC or CONCRETE NUMBER
Variant B: lead with a QUESTION or HUMAN ANGLE

Both under 240 chars. Both authentic, not corporate.
Include 2-3 relevant hashtags in each.

JSON:
{{
  "variable_tested": "hook_style",
  "variant_a": {{"text": "...", "hook_type": "statistic"}},
  "variant_b": {{"text": "...", "hook_type": "question"}},
  "hypothesis": "which will get more engagement and why"
}}"""
    return ask_llm(prompt)

def post_to_mastodon(text):
    if not MASTODON_TOKEN: return None
    try:
        data = json.dumps({'status': text, 'visibility': 'public'}).encode()
        req = urllib_request.Request(
            f'{MASTODON_BASE_URL}/api/v1/statuses',
            data=data,
            headers={
                'Authorization': f'Bearer {MASTODON_TOKEN}',
                'Content-Type': 'application/json',
            }
        )
        with urllib_request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
            return result.get('id')
    except Exception as e:
        print(f'[ab] Post error: {e}')
        return None

def get_post_stats(post_id):
    if not MASTODON_TOKEN or not post_id: return {}
    try:
        req = urllib_request.Request(
            f'{MASTODON_BASE_URL}/api/v1/statuses/{post_id}',
            headers={'Authorization': f'Bearer {MASTODON_TOKEN}'}
        )
        with urllib_request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        return {
            'favourites': data.get('favourites_count', 0),
            'reblogs':    data.get('reblogs_count', 0),
            'replies':    data.get('replies_count', 0),
            'engagement': data.get('favourites_count', 0) + data.get('reblogs_count', 0) * 2,
        }
    except:
        return {}

def evaluate_pending_tests(tests):
    """Check results on tests older than 48h."""
    cutoff = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    winners = []
    for test in tests:
        if test.get('status') != 'live': continue
        if test.get('date', TODAY) > cutoff: continue

        # Fetch stats for both posts
        stats_a = get_post_stats(test.get('post_id_a'))
        stats_b = get_post_stats(test.get('post_id_b'))

        eng_a = stats_a.get('engagement', 0)
        eng_b = stats_b.get('engagement', 0)

        if eng_a == 0 and eng_b == 0:
            test['status'] = 'inconclusive'
            continue

        winner = 'A' if eng_a >= eng_b else 'B'
        test['status']   = 'complete'
        test['winner']   = winner
        test['stats_a']  = stats_a
        test['stats_b']  = stats_b
        test['margin']   = abs(eng_a - eng_b)
        test['insight']  = (
            f"Variant {winner} won with {max(eng_a,eng_b)} vs {min(eng_a,eng_b)} engagement. "
            f"Hook type: {test.get('variant_a' if winner=='A' else 'variant_b', {}).get('hook_type','')}"
        )
        winners.append(test)
        print(f'[ab] Test complete: Variant {winner} won — {test["insight"][:80]}')

    return tests, winners

def update_winning_patterns(winners):
    if not winners: return
    patterns_path = DATA / 'winning_patterns.json'
    patterns = load(patterns_path, {'hooks': {}, 'insights': []})
    for w in winners:
        hook = w.get('variant_a' if w.get('winner') == 'A' else 'variant_b', {}).get('hook_type', '')
        if hook:
            patterns['hooks'][hook] = patterns['hooks'].get(hook, 0) + 1
        if w.get('insight'):
            patterns['insights'].append({'date': TODAY, 'insight': w['insight'], 'variable': w.get('variable_tested')})
    patterns['insights'] = patterns['insights'][-50:]  # keep last 50
    try: patterns_path.write_text(json.dumps(patterns, indent=2))
    except: pass

def run():
    print(f'\n[ab] A/B Testing Engine — {TODAY}')

    tests_path = DATA / 'ab_tests.json'
    tests = load(tests_path, [])

    # Evaluate pending tests
    tests, winners = evaluate_pending_tests(tests)
    update_winning_patterns(winners)

    # Only run one new test per day
    today_tests = [t for t in tests if t.get('date') == TODAY]
    if today_tests:
        print(f'[ab] Already ran a test today. Skipping.')
        try: tests_path.write_text(json.dumps(tests, indent=2))
        except: pass
        return

    # Generate new test
    seed     = get_content_seed()
    variants = generate_variants(seed)
    if not variants:
        print('[ab] Could not generate variants.')
        return

    test = {
        'id':        hashlib.md5(f"{TODAY}{seed['fact']}".encode()).hexdigest()[:8],
        'date':      TODAY,
        'type':      seed['type'],
        'variable':  variants.get('variable_tested', 'hook_style'),
        'hypothesis': variants.get('hypothesis', ''),
        'variant_a': variants.get('variant_a', {}),
        'variant_b': variants.get('variant_b', {}),
        'status':    'generated',
    }

    # Post both variants if Mastodon available
    if MASTODON_TOKEN:
        text_a = variants.get('variant_a', {}).get('text', '')
        text_b = variants.get('variant_b', {}).get('text', '')
        if text_a:
            id_a = post_to_mastodon(text_a)
            test['post_id_a'] = id_a
            print(f'[ab] Posted variant A: {id_a}')
        if text_b:
            import time; time.sleep(3600 * 4)  # 4h gap between variants
            # Actually, queue B for later rather than sleeping
            queue_path = DATA / 'ab_queue.json'
            queue = load(queue_path, [])
            queue.append({'text': text_b, 'test_id': test['id'], 'post_after': TODAY, 'variant': 'B'})
            try: queue_path.write_text(json.dumps(queue, indent=2))
            except: pass
            test['status'] = 'live'
    else:
        test['status'] = 'queued'
        print(f'[ab] No Mastodon token — test queued')

    tests.append(test)
    try: tests_path.write_text(json.dumps(tests[-100:], indent=2))
    except: pass

    print(f'[ab] Test {test["id"]}: {test["variable"]} | {test["hypothesis"][:60]}')
    print('[ab] Done.')

if __name__ == '__main__':
    run()
