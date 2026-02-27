#!/usr/bin/env python3
"""
Self-Evolution Engine
======================
Every day, this system asks itself:
  "What should I add to myself?"

Then it:
  1. Surveys what it already does
  2. Surveys what data it already has
  3. Uses the LLM to design something new
  4. Writes the code
  5. Commits it to the repo via GitHub API
  6. Emails you what it built, what it does, and why it chose it

This is the engine that makes the system grow without being asked.
"""

import json, datetime, os, base64
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import quote

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'

TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO        = 'meekotharaccoon-cell/meeko-nerve-center'

# ── Utilities ──────────────────────────────────────────────────────────────

def fetch_json(url, headers=None, method='GET', body=None, timeout=30):
    try:
        h = {'User-Agent': 'meeko-self-evolution/1.0'}
        if headers: h.update(headers)
        req = urllib_request.Request(url, headers=h, method=method)
        if body:
            req.data = body if isinstance(body, bytes) else body.encode()
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[evolve] fetch error {url[:60]}: {e}')
        return None

def ask_llm(prompt, system=None, max_tokens=2000):
    if not HF_TOKEN:
        print('[evolve] No HF_TOKEN')
        return None
    if not system:
        system = 'You are a senior Python engineer building an autonomous humanitarian AI system. Write clean, working code. Be direct. No fluff.'
    try:
        payload = json.dumps({
            'model':      'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages':   [{'role': 'system', 'content': system}, {'role': 'user', 'content': prompt}]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read())
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[evolve] LLM error: {e}')
        return None

def send_email(subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return False
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = GMAIL_ADDRESS
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        print(f'[evolve] Email sent: {subject}')
        return True
    except Exception as e:
        print(f'[evolve] Email failed: {e}')
        return False

def commit_file_to_github(path, content, commit_message):
    """
    Create or update a file in the GitHub repo via API.
    Returns True if successful.
    """
    if not GITHUB_TOKEN:
        print('[evolve] No GITHUB_TOKEN — cannot commit')
        return False

    api_url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{path}'
    gh_headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Accept':        'application/vnd.github+json',
        'Content-Type':  'application/json',
    }

    # Check if file already exists (need SHA to update)
    existing = fetch_json(api_url, headers=gh_headers)
    sha = existing.get('sha') if existing and isinstance(existing, dict) else None

    encoded = base64.b64encode(content.encode()).decode()
    payload = {'message': commit_message, 'content': encoded}
    if sha:
        payload['sha'] = sha

    result = fetch_json(api_url, headers=gh_headers, method='PUT',
                        body=json.dumps(payload).encode())
    if result and result.get('content'):
        print(f'[evolve] Committed: {path}')
        return True
    else:
        print(f'[evolve] Commit failed for {path}: {result}')
        return False

# ── Step 1: Survey what the system already does ──────────────────────────────

def survey_current_capabilities():
    """Return a text summary of what the system currently does."""
    engines = list((ROOT / 'mycelium').glob('*.py')) if (ROOT / 'mycelium').exists() else []
    data_files = list(DATA.glob('*.json')) if DATA.exists() else []
    content_queue = list((ROOT / 'content' / 'queue').glob('*.json')) if (ROOT / 'content' / 'queue').exists() else []

    summary_lines = [
        f'=== SYSTEM SURVEY {TODAY} ===',
        f'',
        f'Engines ({len(engines)} Python files in mycelium/):',
    ]
    for e in sorted(engines):
        summary_lines.append(f'  - {e.stem}')

    summary_lines += [
        f'',
        f'Data files ({len(data_files)} in data/):',
    ]
    for f in sorted(data_files):
        try:
            size = f.stat().st_size
            summary_lines.append(f'  - {f.name} ({size:,} bytes)')
        except:
            summary_lines.append(f'  - {f.name}')

    # Read existing wired ideas so the LLM knows what\'s been tried
    ledger_path = DATA / 'idea_ledger.json'
    if ledger_path.exists():
        try:
            ledger   = json.loads(ledger_path.read_text())
            ideas    = ledger.get('ideas', {})
            if isinstance(ideas, dict):
                idea_list = list(ideas.values())
            else:
                idea_list = ideas
            wired = [i.get('title','') for i in idea_list if i.get('status') == 'wired']
            summary_lines += ['', 'Already wired ideas:']
            for w in wired[:15]:
                summary_lines.append(f'  - {w}')
        except:
            pass

    # Read what already evolved
    evo_log = DATA / 'evolution_log.json'
    if evo_log.exists():
        try:
            log = json.loads(evo_log.read_text())
            past = log.get('built', [])
            if past:
                summary_lines += ['', 'Previously auto-built:']
                for b in past[-10:]:
                    summary_lines.append(f'  - {b["date"]}: {b["name"]}')
        except:
            pass

    return '\n'.join(summary_lines)

# ── Step 2: Ask the LLM what to build ─────────────────────────────────────────

def decide_what_to_build(survey):
    """
    Ask the LLM to propose ONE new feature to add today.
    Returns a structured dict with name, description, why, and filename.
    """
    prompt = f"""
You are the autonomous self-improvement engine for the Meeko Nerve Center.
This is an open-source humanitarian AI system that:
- Monitors Congressional stock trades for accountability
- Generates Gaza Rose art, sends 70% of sales to Palestinian children (PCRF)
- Auto-posts to Bluesky and Mastodon
- Runs entirely free on GitHub Actions (no server cost)
- Self-generates ideas, tests them, and learns from failures

Here is what the system currently does:
{survey}

Your task:
1. Identify ONE new capability that would meaningfully extend this system
2. It MUST use only free APIs (no API key required, or uses secrets already in the system)
3. It MUST be implementable as a single Python script that runs in GitHub Actions
4. It MUST connect to the mission: humanitarian accountability, Palestinian solidarity, open-source resilience, or SolarPunk values
5. It MUST be different from anything already built (see above lists)
6. Prefer things that generate compelling content, surface important data, or deepen existing connections

Respond ONLY with a JSON object, no markdown, no explanation outside it:
{{
  "name": "Short engine name (e.g. rss_monitor)",
  "filename": "mycelium/rss_monitor.py",
  "title": "Human-readable title",
  "why": "2-3 sentences explaining why you chose this, what gap it fills",
  "description": "1 paragraph explaining what it does and how",
  "apis_used": ["list", "of", "free", "APIs"],
  "outputs": ["what files it creates or updates"]
}}
"""
    print('[evolve] Asking LLM: what should I build today?')
    response = ask_llm(prompt, max_tokens=600)
    if not response:
        return None

    # Extract JSON from response
    try:
        # Find the JSON block
        start = response.find('{')
        end   = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except Exception as e:
        print(f'[evolve] Could not parse LLM design: {e}')
        print(f'[evolve] Raw: {response[:500]}')
    return None

# ── Step 3: Ask the LLM to write the code ─────────────────────────────────────

def write_the_code(design):
    """
    Given a design spec, ask the LLM to write complete, working Python code.
    Returns the code as a string.
    """
    prompt = f"""
Write a complete, working Python script for this new engine:

Name:        {design['name']}
Title:       {design['title']}
Description: {design['description']}
APIs used:   {', '.join(design.get('apis_used', []))}
Outputs:     {', '.join(design.get('outputs', []))}

REQUIREMENTS:
- Standard library only: json, datetime, os, pathlib, urllib.request (no pip installs)
- ROOT = Path(__file__).parent.parent  (repo root)
- DATA = ROOT / 'data'
- KB   = ROOT / 'knowledge'
- Save outputs to the paths listed above
- Include a run() function and if __name__ == '__main__': run()
- Print progress with [name] prefix
- Handle all errors gracefully with try/except — never crash
- Must produce at least one output file that other engines can use
- If it creates social content, save to content/queue/ as a JSON list of post objects
  Each post: {{"platform": "all"|"bluesky"|"mastodon", "type": "...", "text": "..."}}

Write ONLY the Python code. No markdown. No backticks. Start with #!/usr/bin/env python3
"""
    print('[evolve] Asking LLM to write the code...')
    code = ask_llm(prompt, max_tokens=2000)
    if not code:
        return None

    # Strip any accidental markdown fences
    if code.startswith('```'):
        lines = code.split('\n')
        code  = '\n'.join(l for l in lines if not l.startswith('```'))

    return code

# ── Step 4: Add new engine to the daily workflow ────────────────────────────

def add_to_workflow(design):
    """
    Fetch the current workflow file and inject the new engine
    before the Cross Engine step.
    """
    api_url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/.github/workflows/daily-full-cycle.yml'
    gh_headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Accept':        'application/vnd.github+json',
    }
    existing = fetch_json(api_url, headers=gh_headers)
    if not existing or not existing.get('content'):
        print('[evolve] Could not fetch workflow')
        return False

    current_yml = base64.b64decode(existing['content']).decode()
    sha         = existing.get('sha')

    # Don\'t add if already present
    if design['name'] in current_yml:
        print(f'[evolve] {design["name"]} already in workflow')
        return True

    # Insert before Cross Engine step
    new_step = f"""
      - name: {design['title']}
        run: python {design['filename']}
        continue-on-error: true
"""
    inject_before = '      - name: Cross Engine'
    if inject_before in current_yml:
        updated = current_yml.replace(inject_before, new_step + inject_before)
    else:
        # Append before the commit step as fallback
        inject_before = '      - name: Commit everything'
        updated = current_yml.replace(inject_before, new_step + inject_before)

    encoded = base64.b64encode(updated.encode()).decode()
    payload = {
        'message': f'feat: add {design["name"]} to daily workflow (auto-evolved)',
        'content': encoded,
        'sha':     sha,
    }
    result = fetch_json(api_url, headers=gh_headers, method='PUT',
                        body=json.dumps(payload).encode())
    if result and result.get('content'):
        print(f'[evolve] Workflow updated with {design["name"]}')
        return True
    print(f'[evolve] Workflow update failed')
    return False

# ── Step 5: Log what was built ──────────────────────────────────────────────────

def log_evolution(design, code_committed, workflow_updated):
    evo_log = DATA / 'evolution_log.json'
    log = {'built': []}
    if evo_log.exists():
        try:
            log = json.loads(evo_log.read_text())
        except:
            pass

    log['built'].append({
        'date':             TODAY,
        'name':             design['name'],
        'title':            design['title'],
        'filename':         design['filename'],
        'why':              design['why'],
        'description':      design['description'],
        'apis_used':        design.get('apis_used', []),
        'outputs':          design.get('outputs', []),
        'code_committed':   code_committed,
        'workflow_updated': workflow_updated,
    })

    try:
        evo_log.write_text(json.dumps(log, indent=2))
    except:
        pass

    # Commit the log too
    if GITHUB_TOKEN:
        commit_file_to_github(
            'data/evolution_log.json',
            json.dumps(log, indent=2),
            f'log: evolution entry for {design["name"]} on {TODAY}'
        )

# ── Step 6: Email you what was built ──────────────────────────────────────────

def email_build_report(design, code, code_committed, workflow_updated):
    subject = f'🧠 Your system built something new today: {design["title"]}'

    status_code = '✅ Committed to repo' if code_committed else '❌ Commit failed (see logs)'
    status_flow = '✅ Added to daily workflow' if workflow_updated else '⚠️ Workflow not updated (add manually)'

    body = f"""Your system asked itself what to build today. Here's what it chose.

{'=' * 60}
NEW ENGINE: {design['title']}
{'=' * 60}

FILE: {design['filename']}

WHY IT CHOSE THIS:
{design['why']}

WHAT IT DOES:
{design['description']}

APIs USED: {', '.join(design.get('apis_used', []))}
OUTPUTS: {', '.join(design.get('outputs', []))}

STATUS:
  Code: {status_code}
  Workflow: {status_flow}

{'=' * 60}
CODE WRITTEN:
{'=' * 60}

{code[:3000] if code else '[no code generated]'}
{'...(truncated)' if code and len(code) > 3000 else ''}

{'=' * 60}

This engine will run for the first time in tomorrow\'s cycle.
View it live: https://github.com/{GITHUB_REPO}/blob/main/{design['filename']}

Meeko Nerve Center — self-evolving since {TODAY}
"""
    send_email(subject, body)

# ── Main ────────────────────────────────────────────────────────────────────

def run():
    print(f'\n[evolve] Self-Evolution Engine — {TODAY}')
    print('[evolve] Asking: what should I add to myself today?\n')

    if not HF_TOKEN:
        print('[evolve] No HF_TOKEN — cannot generate. Skipping.')
        return

    # Check: only evolve once per day
    evo_log = DATA / 'evolution_log.json'
    if evo_log.exists():
        try:
            log = json.loads(evo_log.read_text())
            already_today = any(b.get('date') == TODAY for b in log.get('built', []))
            if already_today:
                print(f'[evolve] Already evolved today ({TODAY}). Skipping.')
                return
        except:
            pass

    # Step 1: Survey
    survey = survey_current_capabilities()
    print('[evolve] Survey complete.')

    # Step 2: Decide
    design = decide_what_to_build(survey)
    if not design:
        print('[evolve] LLM did not return a valid design. Aborting.')
        return
    print(f'[evolve] Chosen: {design["title"]}')
    print(f'[evolve] Why: {design["why"][:120]}...')

    # Step 3: Write code
    code = write_the_code(design)
    if not code or len(code) < 100:
        print('[evolve] LLM did not write valid code. Aborting.')
        return
    print(f'[evolve] Code written: {len(code)} characters')

    # Step 4: Commit code
    code_committed = commit_file_to_github(
        design['filename'],
        code,
        f'feat: auto-evolved {design["name"]} — {design["title"]} [{TODAY}]'
    )

    # Step 5: Update workflow
    workflow_updated = False
    if GITHUB_TOKEN and code_committed:
        workflow_updated = add_to_workflow(design)

    # Step 6: Log
    log_evolution(design, code_committed, workflow_updated)

    # Step 7: Email
    email_build_report(design, code, code_committed, workflow_updated)

    print(f'\n[evolve] Done. Built: {design["title"]}')
    print(f'[evolve] Code committed: {code_committed}')
    print(f'[evolve] Workflow updated: {workflow_updated}')

if __name__ == '__main__':
    run()
