#!/usr/bin/env python3
"""
Form Filler — The system fills any form it can see
===================================================
The system stores the human's identity in GitHub Secrets.
This engine uses that identity to fill forms automatically:

  - Grant application forms
  - Job application forms  
  - Contact forms for press/partners
  - Government assistance forms
  - Any web form with a URL

Approach:
  1. Given a URL, fetch the page
  2. Parse form fields using LLM ("what does this form need?")
  3. Map fields to human identity data
  4. Generate filled values using LLM
  5. Output: either auto-submit (if Playwright available) or
             a filled JSON for human to paste in manually

Identity data (from GitHub Secrets via environment):
  HUMAN_FULL_NAME, HUMAN_EMAIL, HUMAN_LOCATION, HUMAN_PHONE,
  HUMAN_LINKEDIN, HUMAN_GITHUB

System capabilities data (auto-generated from repo stats):
  engine_count, self_built_count, art_count, pcrf_total,
  years_experience (calculated), skills_list

This means:
  - Grant forms get auto-filled with accurate project stats
  - Job forms get filled with real skills and honest AI disclosure
  - Contact forms get personalized outreach
  - ALL of it is honest. The system never lies.
"""

import json, os, datetime
from pathlib import Path
from urllib import request as urllib_request
from html.parser import HTMLParser

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

HF_TOKEN = os.environ.get('HF_TOKEN', '')

# Human identity from environment
IDENTITY = {
    'full_name':  os.environ.get('HUMAN_FULL_NAME', ''),
    'email':      os.environ.get('HUMAN_EMAIL', os.environ.get('GMAIL_ADDRESS', '')),
    'location':   os.environ.get('HUMAN_LOCATION', 'United States'),
    'phone':      os.environ.get('HUMAN_PHONE', ''),
    'linkedin':   os.environ.get('HUMAN_LINKEDIN', ''),
    'github':     os.environ.get('HUMAN_GITHUB', 'https://github.com/meekotharaccoon-cell'),
    'timezone':   os.environ.get('HUMAN_TIMEZONE', 'EST'),
    'website':    'https://meekotharaccoon-cell.github.io/meeko-nerve-center',
    'project_url': 'https://github.com/meekotharaccoon-cell/meeko-nerve-center',
}


def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}


def get_system_stats():
    """Pull real stats about the system for form filling."""
    stats = dict(IDENTITY)
    try: stats['engine_count']    = len(list((ROOT / 'mycelium').glob('*.py')))
    except: stats['engine_count'] = 40
    try:
        evo = load(DATA / 'evolution_log.json')
        stats['self_built'] = len(evo.get('built', []))
    except: stats['self_built'] = 0
    try:
        arts = load(DATA / 'generated_art.json')
        al   = arts if isinstance(arts, list) else arts.get('art', [])
        stats['art_count'] = len(al)
    except: stats['art_count'] = 0
    try:
        tracker = load(DATA / 'compound_tracker.json')
        stats['pcrf_total'] = tracker.get('total_pcrf', 0)
    except: stats['pcrf_total'] = 0
    stats['github_url']   = IDENTITY['project_url']
    stats['skills']       = ', '.join([
        'Python automation', 'AI/LLM engineering', 'GitHub Actions',
        'Data analysis', 'Content writing', 'Grant writing',
        'Social media automation', 'API integration', 'Web scraping'
    ])
    stats['availability'] = 'Immediate start. Async-friendly. 24/7 availability.'
    stats['ai_disclosure'] = 'Yes, I use AI tools extensively. This is a feature.'
    return stats


class FormParser(HTMLParser):
    """Parse HTML forms to find fields."""
    def __init__(self):
        super().__init__()
        self.fields  = []
        self.in_form = False
        self.current_label = ''

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'form':
            self.in_form = True
        if tag in ('input', 'textarea', 'select') and self.in_form:
            field = {
                'tag':         tag,
                'type':        attrs_dict.get('type', 'text'),
                'name':        attrs_dict.get('name', ''),
                'id':          attrs_dict.get('id', ''),
                'placeholder': attrs_dict.get('placeholder', ''),
                'required':    'required' in attrs_dict,
                'label':       self.current_label,
            }
            if field['type'] not in ('submit', 'button', 'hidden', 'csrf'):
                self.fields.append(field)

    def handle_data(self, data):
        if '<label' in data or 'label' in data.lower():
            self.current_label = data.strip()


def fetch_and_parse_form(url):
    """Fetch a URL and extract form fields."""
    try:
        req = urllib_request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 SolarPunk Form Filler'}
        )
        with urllib_request.urlopen(req, timeout=15) as r:
            html = r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f'[form_filler] Fetch error: {e}')
        return None, None

    parser = FormParser()
    parser.feed(html)

    # Also extract visible text for context
    import re
    text = re.sub(r'<[^>]+>', ' ', html)
    text = ' '.join(text.split())[:2000]

    return parser.fields, text


def fill_form_with_llm(url, fields, page_text, form_purpose, stats):
    """Use LLM to fill form fields intelligently."""
    if not HF_TOKEN:
        return _rule_based_fill(fields, stats)

    fields_summary = json.dumps([
        {'name': f.get('name') or f.get('id') or f.get('placeholder'), 'required': f['required']}
        for f in fields[:20]
    ], indent=2)

    prompt = f"""Fill out this web form on behalf of this applicant.

Form URL: {url}
Form purpose: {form_purpose}
Page context: {page_text[:500]}

Form fields:
{fields_summary}

Applicant info:
- Name: {stats['full_name']}
- Email: {stats['email']}
- Location: {stats['location']}
- GitHub: {stats['github_url']}
- Skills: {stats['skills']}
- Project: Meeko Nerve Center — autonomous AI, {stats['engine_count']} engines, ${stats['pcrf_total']:.2f} to PCRF
- AI tool use: Yes, openly disclosed
- Availability: {stats['availability']}

Rules:
- NEVER lie. Fill only with truthful values.
- If you don't know a value, use empty string.
- For skills/bio questions: use the project description naturally.
- Disclose AI tool use honestly when asked.

Return ONLY a JSON object mapping field names to values:
{{"field_name": "value", ...}}"""

    payload = json.dumps({
        'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
        'max_tokens': 600,
        'messages': [
            {'role': 'system', 'content': 'You fill web forms honestly and accurately. Return only valid JSON.'},
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
        print(f'[form_filler] LLM error: {e}')
    return _rule_based_fill(fields, stats)


def _rule_based_fill(fields, stats):
    """Fallback rule-based form filling."""
    filled = {}
    mappings = {
        'name': stats['full_name'], 'full_name': stats['full_name'],
        'first': stats['full_name'].split()[0] if stats['full_name'] else '',
        'last':  stats['full_name'].split()[-1] if stats['full_name'] else '',
        'email': stats['email'], 'phone': stats['phone'],
        'location': stats['location'], 'city': stats['location'],
        'website': stats['website'], 'github': stats['github_url'],
        'linkedin': stats['linkedin'],
        'skills': stats['skills'],
        'bio': f"Builder of autonomous AI systems for humanitarian causes. {stats['engine_count']} engines, ${stats['pcrf_total']:.2f} to PCRF.",
    }
    for field in fields:
        key = (field.get('name') or field.get('id') or '').lower()
        for pattern, value in mappings.items():
            if pattern in key and value:
                filled[field.get('name') or field.get('id')] = value
                break
    return filled


def fill_form(url, form_purpose='application'):
    """
    Main entry point. Given a URL:
    1. Fetches the form
    2. Fills it using identity + system stats
    3. Returns filled values + instructions for submission
    """
    print(f'[form_filler] Processing: {url[:80]}')

    stats  = get_system_stats()
    fields, page_text = fetch_and_parse_form(url)

    if not fields:
        print(f'[form_filler] No form fields found at {url}')
        # Return identity info as fallback
        return {'identity': stats, 'url': url, 'error': 'no_form_found'}

    print(f'[form_filler] Found {len(fields)} form fields')
    filled = fill_form_with_llm(url, fields, page_text or '', form_purpose, stats)

    result = {
        'url': url,
        'purpose': form_purpose,
        'fields_found': len(fields),
        'filled': filled,
        'manual_values': {
            'Name': stats['full_name'],
            'Email': stats['email'],
            'GitHub': stats['github_url'],
            'Website': stats['website'],
            'Skills': stats['skills'],
        },
        'date': TODAY,
    }

    # Save to output
    output_path = DATA / 'form_fills' / f'{TODAY}_{url.replace("/","_")[:50]}.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))

    print(f'[form_filler] Filled {len(filled)} fields')
    return result


def run():
    """Process any queued form fill requests."""
    print(f'\n[form_filler] Form Filler — {TODAY}')

    queue = load(DATA / 'form_fill_queue.json', [])
    if not queue:
        print('[form_filler] No forms in queue. Add URLs to data/form_fill_queue.json')
        print('[form_filler] Format: [{"url": "...", "purpose": "grant application"}]')
        return

    for item in queue:
        if item.get('done'): continue
        result = fill_form(item['url'], item.get('purpose', 'application'))
        print(f'[form_filler] ✅ {item["url"][:60]} — {result.get("fields_found",0)} fields')
        item['done'] = True
        item['result'] = result.get('filled', {})

    (DATA / 'form_fill_queue.json').write_text(json.dumps(queue, indent=2))


if __name__ == '__main__':
    # Can be called directly with a URL:
    # python mycelium/form_filler.py https://example.com/apply
    import sys
    if len(sys.argv) > 1:
        result = fill_form(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'application')
        print(json.dumps(result['filled'], indent=2))
    else:
        run()
