#!/usr/bin/env python3
"""
Language Engine
================
Free Dictionary API -> language intelligence for the system.

Use cases:
  - Verify words used in generated content are real
  - Build vocabulary for specific causes (Gaza, SolarPunk, climate)
  - Generate "word of the day" content (high engagement)
  - Accessibility: define technical/activist terms for new audiences
  - Etymology research: find the roots of key mission words

API: dictionaryapi.dev (free, no auth)
https://api.dictionaryapi.dev/api/v2/entries/en/<word>

Outputs:
  - data/vocabulary.json        mission vocabulary with definitions
  - content/queue/word_*.json   word-of-the-day content posts
  - knowledge/language/latest.md language intelligence digest
"""

import json, datetime
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'
CONT  = ROOT / 'content' / 'queue'

for d in [KB / 'language', CONT]:
    d.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()

# Core vocabulary of the mission
# These are words that matter — for content, for accessibility, for framing
MISSION_VOCABULARY = [
    # SolarPunk canon
    'solarpunk', 'mutual', 'solidarity', 'commons', 'decentralized',
    'regenerative', 'resilience', 'abundance', 'symbiosis',
    # Humanitarian
    'humanitarian', 'displacement', 'sovereignty', 'dignity', 'refugee',
    'resistance', 'liberation', 'occupation', 'ceasefire', 'aid',
    # Tech/crypto
    'transparency', 'open-source', 'protocol', 'consensus', 'immutable',
    'decentralized', 'proliferate', 'autonomy',
    # Power/politics
    'accountability', 'corruption', 'sanction', 'leverage', 'complicit',
]

def fetch_definition(word):
    """Get definition from free Dictionary API."""
    url = f'https://api.dictionaryapi.dev/api/v2/entries/en/{urllib_request.quote(word)}'
    try:
        req = urllib_request.Request(url, headers={'User-Agent': 'meeko-nerve-center/2.0'})
        with urllib_request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            if not data or not isinstance(data, list): return None

            entry = data[0]
            result = {
                'word':     entry.get('word', word),
                'phonetic': entry.get('phonetic', ''),
                'origin':   entry.get('origin', ''),
                'meanings': [],
            }

            for meaning in entry.get('meanings', [])[:2]:  # max 2 parts of speech
                defs = meaning.get('definitions', [])[:1]  # max 1 definition each
                if defs:
                    result['meanings'].append({
                        'part': meaning.get('partOfSpeech', ''),
                        'def':  defs[0].get('definition', ''),
                        'example': defs[0].get('example', ''),
                        'synonyms': defs[0].get('synonyms', [])[:5],
                    })

            return result
    except Exception as e:
        return None

def pick_word_of_day():
    """Pick today\'s word based on date (consistent, not random)."""
    day_index = datetime.date.today().timetuple().tm_yday
    return MISSION_VOCABULARY[day_index % len(MISSION_VOCABULARY)]

def build_word_post(word_data):
    """Generate a word-of-the-day social post."""
    if not word_data or not word_data.get('meanings'): return None

    word    = word_data['word']
    phonetic = word_data.get('phonetic', '')
    origin  = word_data.get('origin', '')
    meaning = word_data['meanings'][0]

    lines = [f'📚 Word: **{word}**']
    if phonetic: lines.append(f'{phonetic}')
    lines.append(f'')
    lines.append(f"{meaning['part']}: {meaning['def']}")
    if meaning.get('example'):
        lines.append(f'\"{ meaning["example"] }\"')
    if origin:
        lines.append(f'\nOrigin: {origin[:100]}')
    lines.append(f'\n#Language #WordOfTheDay #{word.capitalize()} #SolarPunk')

    return '\n'.join(lines)

def run():
    print(f'[language] Language Engine — {TODAY}')

    vocabulary = {}
    fetched = 0

    # Load existing vocabulary
    vocab_path = DATA / 'vocabulary.json'
    if vocab_path.exists():
        try: vocabulary = json.loads(vocab_path.read_text())
        except: pass

    # Fetch definitions for words we don\'t have yet
    for word in MISSION_VOCABULARY:
        if word in vocabulary: continue  # already have it
        defn = fetch_definition(word)
        if defn:
            vocabulary[word] = defn
            fetched += 1
            print(f'[language] Defined: {word}')

    # Save vocabulary
    (DATA / 'vocabulary.json').write_text(json.dumps(vocabulary, indent=2))
    print(f'[language] Vocabulary: {len(vocabulary)} words ({fetched} new today)')

    # Word of the day
    wod = pick_word_of_day()
    word_data = vocabulary.get(wod)
    if not word_data:
        word_data = fetch_definition(wod)
        if word_data: vocabulary[wod] = word_data

    post_text = build_word_post(word_data)
    if post_text:
        post = [{'platform': 'mastodon', 'type': 'word_of_day', 'text': post_text, 'word': wod}]
        (CONT / f'word_{TODAY}.json').write_text(json.dumps(post, indent=2))
        print(f'[language] Word of the day: {wod}')

    # Digest
    lines = [f'# Language Intelligence — {TODAY}', '',
             f'{len(vocabulary)} words in mission vocabulary', '',
             f'## Word of the Day: {wod}', '']
    if word_data and word_data.get('meanings'):
        lines.append(f"{word_data['meanings'][0]['def']}")
    if word_data and word_data.get('origin'):
        lines.append(f'\nOrigin: {word_data["origin"]}')

    (KB / 'language' / f'{TODAY}.md').write_text('\n'.join(lines))
    (KB / 'language' / 'latest.md').write_text('\n'.join(lines))

    return {'vocabulary_size': len(vocabulary), 'word_of_day': wod}

if __name__ == '__main__':
    run()
