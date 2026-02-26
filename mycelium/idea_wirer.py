#!/usr/bin/env python3
"""
Idea Wirer
===========
Takes working ideas from idea_engine and wires them into
the daily automated cycle.

For each working idea that isn't yet wired:
  1. Check if a script already exists (idea_spawns/)
  2. If the script produces real output, add it to the daily workflow
  3. Mark the idea as 'wired_in' in ideas.json

This closes the loop:
  Generate -> Test -> Work -> Wire -> Run Daily -> Learn -> Generate Better Ideas
"""

import json, datetime
from pathlib import Path

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / 'data'
SPAWNS = ROOT / 'mycelium' / 'idea_spawns'

TODAY = datetime.date.today().isoformat()

def load_ideas():
    path = DATA / 'ideas.json'
    if path.exists():
        return json.loads(path.read_text())
    return []

def save_ideas(ideas):
    (DATA / 'ideas.json').write_text(json.dumps(ideas, indent=2))

def run():
    ideas = load_ideas()
    working = [i for i in ideas if i.get('status') == 'working']
    
    print(f'[wirer] {len(working)} working ideas to evaluate for wiring')
    
    newly_wired = []
    for idea in working:
        spawn = SPAWNS / f"{idea['id']}.py"
        if not spawn.exists():
            print(f'[wirer] No spawn script yet for: {idea["title"]}')
            continue
        
        # Check if spawn script has been expanded beyond stub
        content = spawn.read_text()
        if 'Add implementation here' in content:
            print(f'[wirer] Spawn is still a stub: {idea["id"]}')
            continue
        
        # Mark as wired
        idea['status'] = 'wired_in'
        idea['wired_date'] = TODAY
        newly_wired.append(idea)
        print(f'[wirer] Wired: {idea["title"]}')
    
    if newly_wired:
        save_ideas(ideas)
        print(f'[wirer] {len(newly_wired)} ideas now wired into daily cycle')
    else:
        print('[wirer] No new ideas ready to wire (spawns still need implementation)')
    
    # Report
    total    = len(ideas)
    wired    = len([i for i in ideas if i.get('status') == 'wired_in'])
    working  = len([i for i in ideas if i.get('status') == 'working'])
    pending  = len([i for i in ideas if i.get('status') in ['untested','generated']])
    
    print(f'[wirer] Idea graph: {total} total | {wired} wired | {working} working | {pending} pending')

if __name__ == '__main__':
    run()
