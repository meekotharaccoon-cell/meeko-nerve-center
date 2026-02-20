#!/usr/bin/env python3
"""
Publish the Dev.to article once.
Runs in mycelium morning pulse if DEVTO_API_KEY is set and article not yet published.
"""
import os, json, requests

DEVTO_KEY = os.environ.get('DEVTO_API_KEY', '')
STATE_FILE = 'mycelium/devto_published.json'

def run():
    if not DEVTO_KEY:
        print('[Dev.to] No DEVTO_API_KEY — skipping')
        return
    
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
            if state.get('published'):
                print(f'[Dev.to] Already published: {state.get("url")}')
                return
    except:
        pass

    with open('mycelium/devto_article.md') as f:
        content = f.read()
    
    # Strip frontmatter for body, use it for metadata
    lines = content.split('\n')
    in_front = False
    front_lines = []
    body_lines = []
    for i, line in enumerate(lines):
        if i == 0 and line == '---':
            in_front = True
            continue
        if in_front and line == '---':
            in_front = False
            continue
        if in_front:
            front_lines.append(line)
        else:
            body_lines.append(line)
    
    r = requests.post(
        'https://dev.to/api/articles',
        headers={'api-key': DEVTO_KEY, 'Content-Type': 'application/json'},
        json={
            'article': {
                'title': 'I built a self-running humanitarian art gallery on GitHub. Zero monthly cost. 70% to Gaza.',
                'published': True,
                'body_markdown': '\n'.join(body_lines),
                'tags': ['opensource', 'github', 'ai', 'showdev'],
                'canonical_url': 'https://meekotharaccoon-cell.github.io/gaza-rose-gallery'
            }
        },
        timeout=30
    )
    
    if r.status_code in (200, 201):
        data = r.json()
        url = data.get('url', '')
        print(f'[Dev.to] PUBLISHED: {url}')
        with open(STATE_FILE, 'w') as f:
            json.dump({'published': True, 'url': url, 'id': data.get('id')}, f)
    else:
        print(f'[Dev.to] FAILED: {r.status_code} {r.text[:200]}')

if __name__ == '__main__':
    run()
