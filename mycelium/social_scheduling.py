#!/usr/bin/env python3
"""
Social Scheduling Engine
=========================
Posts go out when the cron runs, not when people are actually online.
This fixes that.

Every run:
  1. Reads content_performance.json to find which hours get best engagement
  2. Reads content/queue/ for posts waiting to go out
  3. Stamps each queued post with an optimal_send_hour
  4. Social Engine reads that stamp and skips posts not in their window

Optimal hours derived from actual engagement data.
Falls back to research-based defaults if no data yet:
  - Mastodon: 9am, 12pm, 6pm UTC
  - Bluesky: 10am, 2pm, 7pm UTC
"""

import json, datetime, os
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'

TODAY    = datetime.date.today().isoformat()
CURR_HOUR = datetime.datetime.utcnow().hour

HF_TOKEN = os.environ.get('HF_TOKEN', '')

# Research-based defaults (UTC)
DEFAULT_WINDOWS = {
    'mastodon': [9, 12, 18],
    'bluesky':  [10, 14, 19],
    'all':      [9, 12, 18],
}

def ask_llm(prompt, max_tokens=400):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': 'You are a social media timing analyst. Be precise and data-driven.'},
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
        print(f'[schedule] LLM error: {e}')
        return None

def derive_optimal_hours():
    """
    Read content_performance.json and derive best posting hours per platform.
    Returns dict: {platform: [hour1, hour2, hour3]}
    """
    perf_path = DATA / 'content_performance.json'
    if not perf_path.exists():
        print('[schedule] No performance data yet. Using defaults.')
        return DEFAULT_WINDOWS

    try:
        perf = json.loads(perf_path.read_text())
        top_posts = perf.get('top_10', [])
        if len(top_posts) < 5:
            return DEFAULT_WINDOWS

        # Extract hours from top post dates
        # Posts with dates like '2026-02-27T14:32:00'
        hour_scores = {}
        for post in top_posts:
            date_str = post.get('date', '')
            if 'T' in date_str:
                try:
                    hour = int(date_str[11:13])
                    hour_scores[hour] = hour_scores.get(hour, 0) + post.get('score', 1)
                except:
                    pass

        if len(hour_scores) >= 3:
            sorted_hours = sorted(hour_scores, key=hour_scores.get, reverse=True)
            best_3 = sorted(sorted_hours[:3])
            print(f'[schedule] Derived optimal hours from data: {best_3}')
            return {'mastodon': best_3, 'bluesky': best_3, 'all': best_3}

        # Ask LLM to interpret the data
        prompt = f"""Based on this engagement data from a Palestinian solidarity social account,
what are the 3 best UTC hours to post? Posts and their scores:
{json.dumps([(p.get('date','')[:16], p.get('score',0)) for p in top_posts[:10]])}

Respond only as JSON: {{"hours": [h1, h2, h3]}}
"""
        result = ask_llm(prompt, max_tokens=100)
        if result:
            start = result.find('{')
            end = result.rfind('}') + 1
            parsed = json.loads(result[start:end])
            hours = sorted(parsed.get('hours', [9, 12, 18])[:3])
            return {'mastodon': hours, 'bluesky': hours, 'all': hours}

    except Exception as e:
        print(f'[schedule] Error deriving hours: {e}')

    return DEFAULT_WINDOWS

def stamp_queued_posts(windows):
    """
    Read content/queue/*.json, stamp each post with scheduling metadata.
    Social engine will check: if optimal_send_hour is set and current hour
    doesn't match a window, defer the post.
    """
    queue_dir = ROOT / 'content' / 'queue'
    if not queue_dir.exists():
        print('[schedule] No queue directory found.')
        return 0

    stamped = 0
    for queue_file in sorted(queue_dir.glob('*.json')):
        try:
            posts = json.loads(queue_file.read_text())
            if not isinstance(posts, list):
                continue

            modified = False
            for post in posts:
                if 'optimal_send_hour' not in post:
                    platform = post.get('platform', 'all')
                    hours    = windows.get(platform, windows.get('all', [9, 12, 18]))
                    post['optimal_send_hour'] = hours[0]  # first optimal window
                    post['send_windows']      = hours
                    post['scheduled_date']    = TODAY
                    modified = True
                    stamped += 1

            if modified:
                queue_file.write_text(json.dumps(posts, indent=2))

        except Exception as e:
            print(f'[schedule] Error processing {queue_file.name}: {e}')

    return stamped

def save_schedule(windows):
    try:
        schedule = {
            'updated':        TODAY,
            'current_hour':   CURR_HOUR,
            'optimal_windows': windows,
            'in_window_now':  any(abs(CURR_HOUR - h) <= 1 for h in windows.get('all', [])),
        }
        (DATA / 'post_schedule.json').write_text(json.dumps(schedule, indent=2))
        print(f'[schedule] Schedule saved. In window now: {schedule["in_window_now"]}')
    except Exception as e:
        print(f'[schedule] Save error: {e}')

def run():
    print(f'\n[schedule] Social Scheduling Engine — {TODAY} UTC hour {CURR_HOUR}')

    windows = derive_optimal_hours()
    print(f'[schedule] Optimal windows: {windows}')

    stamped = stamp_queued_posts(windows)
    print(f'[schedule] Stamped {stamped} posts with scheduling metadata')

    save_schedule(windows)
    print('[schedule] Done.')

if __name__ == '__main__':
    run()
