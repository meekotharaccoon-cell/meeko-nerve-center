#!/usr/bin/env python3
"""
Language Engine
================
Free Dictionary API (dictionaryapi.dev) — no auth, no cost.

Use cases:
  1. WORD OF THE DAY — pick a powerful word related to the mission
     (solidarity, resistance, mycelium, commons, sovereignty...)
     Get its full definition, phonetics, etymology
     Generate a post: 'Word the world needs today: [word]'

  2. CONTENT ENRICHMENT — look up key words in generated content
     to make sure they're used correctly and add depth

  3. GLOSSARY BUILDER — build a growing glossary of mission-relevant terms
     (humanitarian, SolarPunk, mutual aid, open source, etc.)
     For the fork guide, README, content

  4. LANGUAGE ACCESSIBILITY — when content uses complex terms,
     auto-fetch plain definitions to include for wider audiences

Outputs:
  - knowledge/language/word_of_day.json
  - knowledge/language/glossary.json     growing mission glossary
  - content/queue/word_post_*.json       daily word post
"""

import json, datetime, random
from pathlib import Path
from urllib import request as urllib_request

ROOT = Path(__file__).parent.parent
KB   = ROOT / 'knowledge'
DATA = ROOT / 'data'
CONT = ROOT / 'content' / 'queue'

for d in [KB / 'language', CONT]:
    d.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()

# Words that carry the mission — rotate through these
MISSION_WORDS = [
    # SolarPunk / Ecology
    'mycelium', 'symbiosis', 'commons', 'resilience', 'rewilding',
    'sovereignty', 'regenerative', 'mutualism',
    # Justice / Solidarity  
    'solidarity', 'resistance', 'liberation', 'dignity', 'sanctuary',
    'testimony', 'bearing witness', 'persistence',
    # Technology / Open Source
    'protocol', 'decentralized', 'transparent', 'open', 'fork',
    'propagate', 'network', 'signal',
    # Hope
    'flourish', 'bloom', 'persevere', 'endure', 'root',
    'grow', 'tend', 'cultivate',
]

DICT_API = 'https://api.dictionaryapi.dev/api/v2/entries/en/'

def lookup(word):
    try:
        req = urllib_request.Request(
            DICT_API + urllib_request.quote(word),
            headers={'User-Agent': 'meeko-nerve-center/2.0'}
        )
        with urllib_request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            if data and isinstance(data, list):
                return data[0]
    except Exception as e:
        print(f'[lang] lookup error for {word}: {e}')
    return None

def extract_definition(entry):
    """Get the cleanest definition from a dictionary entry."""
    if not entry: return None
    meanings = entry.get('meanings', [])
    if not meanings: return None
    
    # Prefer nouns and verbs over exclamations
    preferred = ['noun', 'verb', 'adjective']
    for pos in preferred:
        for m in meanings:
            if m.get('partOfSpeech') == pos:
                defs = m.get('definitions', [])
                if defs:
                    return {
                        'word':          entry.get('word'),
                        'phonetic':      entry.get('phonetic', ''),
                        'origin':        entry.get('origin', ''),
                        'part_of_speech': pos,
                        'definition':    defs[0].get('definition', ''),
                        'example':       defs[0].get('example', ''),
                        'synonyms':      defs[0].get('synonyms', [])[:5],
                    }
    
    # Fallback: first definition of any type
    m = meanings[0]
    defs = m.get('definitions', [])
    if defs:
        return {
            'word':          entry.get('word'),
            'phonetic':      entry.get('phonetic', ''),
            'origin':        entry.get('origin', ''),
            'part_of_speech': m.get('partOfSpeech', ''),
            'definition':    defs[0].get('definition', ''),
            'example':       defs[0].get('example', ''),
            'synonyms':      defs[0].get('synonyms', [])[:5],
        }
    return None

def build_word_post(word_data):
    """Build a social post around a word."""
    w = word_data
    phonetic = f' {w["phonetic"]}' if w.get('phonetic') else ''
    origin   = f'\n\n{w["origin"]}' if w.get('origin') else ''
    example  = f'\n\n"{w["example"]}"' if w.get('example') else ''
    
    post = f"""Word the world needs today:

{w['word'].upper()}{phonetic}
/{w['part_of_speech']}/

{w['definition']}{example}{origin}

This is what we\'re building toward.\n\n#WordOfTheDay #{w['word'].title()} #SolarPunk #Liberation"""
    
    return post

def load_glossary():
    path = KB / 'language' / 'glossary.json'
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return {'terms': {}, 'last_updated': TODAY}

def run():
    print(f'[lang] Language Engine — {TODAY}')
    
    glossary = load_glossary()
    new_terms = 0
    
    # Look up 5 mission words to build the glossary
    words_to_lookup = random.sample(MISSION_WORDS, min(5, len(MISSION_WORDS)))
    
    for word in words_to_lookup:
        if word in glossary['terms']:
            continue  # Already have it
        
        entry = lookup(word)
        if entry:
            definition = extract_definition(entry)
            if definition:
                glossary['terms'][word] = definition
                new_terms += 1
                print(f'[lang] Added: {word} — {definition["definition"][:60]}...')
    
    glossary['last_updated'] = TODAY
    (KB / 'language' / 'glossary.json').write_text(json.dumps(glossary, indent=2))
    
    # Pick word of the day
    # Prefer words not yet in glossary, or rotate through all
    all_words = MISSION_WORDS
    today_word_name = all_words[int(datetime.date.today().toordinal()) % len(all_words)]
    
    entry = lookup(today_word_name)
    word_data = extract_definition(entry) if entry else None
    
    if word_data:
        (KB / 'language' / 'word_of_day.json').write_text(json.dumps({
            'date': TODAY,
            'word': word_data,
        }, indent=2))
        
        post_text = build_word_post(word_data)
        (CONT / f'word_post_{TODAY}.json').write_text(json.dumps([{
            'platform': 'mastodon',
            'type': 'word_of_day',
            'text': post_text,
        }], indent=2))
        
        print(f'[lang] Word of the day: {today_word_name}')
        print(f'[lang] Post generated.')
    
    print(f'[lang] Glossary: {len(glossary["terms"])} terms ({new_terms} new today)')
    return {'word_of_day': today_word_name, 'glossary_size': len(glossary['terms']), 'new_terms': new_terms}

if __name__ == '__main__':
    run()
