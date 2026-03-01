#!/usr/bin/env python3
"""
Unique Content Guard
=====================
Prevents the system from sending duplicate emails or duplicate social posts.

Problem it solves:
  - Multiple workflows run the same engine on the same day
  - Each run sends the same email = inbox floods with duplicates
  - Social posts repeat the same content cycle after cycle

How it works:
  - Maintains a fingerprint log per engine per day
  - Engines call guard.check(engine_name, content) before sending
  - If fingerprint already logged today → returns False (skip)
  - If new → logs fingerprint → returns True (send)
  - Resets daily

Any engine can import and use this:
  from unique_content_guard import guard
  if guard.should_send('my_engine', content_string):
      send_email(...)
"""

import json, datetime, hashlib
from pathlib import Path

DATA  = Path(__file__).parent.parent / 'data'
TODAY = datetime.date.today().isoformat()

class UniqueContentGuard:
    def __init__(self):
        self.log_path = DATA / 'content_fingerprints.json'
        self.log = self._load()
        # Clean old dates
        self.log = {k: v for k, v in self.log.items() if k.startswith(TODAY)}

    def _load(self):
        try:
            p = self.log_path
            if p.exists(): return json.loads(p.read_text())
        except: pass
        return {}

    def _save(self):
        try: self.log_path.write_text(json.dumps(self.log, indent=2))
        except: pass

    def fingerprint(self, content):
        return hashlib.md5(str(content).encode()).hexdigest()[:16]

    def should_send(self, engine_name, content):
        """
        Returns True if this content hasn't been sent today by this engine.
        Call this before any email send or social post.
        """
        fp = self.fingerprint(content)
        key = f'{TODAY}:{engine_name}:{fp}'
        if key in self.log:
            print(f'[guard] Duplicate blocked: {engine_name} already sent this content today')
            return False
        self.log[key] = {
            'engine': engine_name,
            'date': TODAY,
            'fp': fp,
            'ts': datetime.datetime.utcnow().isoformat()
        }
        self._save()
        return True

    def mark_sent(self, engine_name, content):
        """Explicitly mark content as sent (for engines that check separately)."""
        fp = self.fingerprint(content)
        key = f'{TODAY}:{engine_name}:{fp}'
        self.log[key] = {
            'engine': engine_name,
            'date': TODAY,
            'fp': fp,
            'ts': datetime.datetime.utcnow().isoformat()
        }
        self._save()

    def stats(self):
        today_entries = [v for k, v in self.log.items() if k.startswith(TODAY)]
        by_engine = {}
        for e in today_entries:
            eng = e.get('engine', 'unknown')
            by_engine[eng] = by_engine.get(eng, 0) + 1
        return {'today_total': len(today_entries), 'by_engine': by_engine}

guard = UniqueContentGuard()

def run():
    print(f'[guard] Unique Content Guard — {TODAY}')
    stats = guard.stats()
    print(f'[guard] Today: {stats["today_total"]} content fingerprints logged')
    for eng, count in stats['by_engine'].items():
        print(f'[guard]   {eng}: {count} unique sends')
    print('[guard] Done.')

if __name__ == '__main__':
    run()
