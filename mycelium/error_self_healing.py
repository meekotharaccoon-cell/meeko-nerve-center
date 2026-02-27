#!/usr/bin/env python3
"""
Error Self-Healing Engine
==========================
Engines fail silently. This ends that.

Every run:
  1. Reads GitHub Actions logs for the last workflow run
  2. Identifies any steps that failed
  3. Reads the failing engine's source code
  4. Asks the LLM to diagnose the error and patch the code
  5. Commits the patch directly to the repo
  6. Emails you: what broke, what the diagnosis was, what the fix is

This is the system's immune system.
"""

import json, datetime, os, base64, re
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'

TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO        = 'meekotharaccoon-cell/meeko-nerve-center'

# Engines we will NOT auto-patch (core infrastructure — too risky)
NO_TOUCH = {'self_evolution', 'error_self_healing', 'privacy_scrubber'}

# ── GitHub API helpers ───────────────────────────────────────────────────────

def gh(path, method='GET', body=None, timeout=30):
    if not GITHUB_TOKEN: return None
    url = f'https://api.github.com/repos/{GITHUB_REPO}{path}'
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Accept':        'application/vnd.github+json',
        'User-Agent':    'meeko-self-healing/1.0',
    }
    try:
        req = urllib_request.Request(url, headers=headers, method=method)
        if body:
            req.data = body if isinstance(body, bytes) else body.encode()
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[heal] GH API error {path[:60]}: {e}')
        return None

def ask_llm(prompt, system='You are a Python debugger. Be precise. Write working code.', max_tokens=1500):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model':      'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages':   [{'role':'system','content':system},{'role':'user','content':prompt}]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization':f'Bearer {HF_TOKEN}','Content-Type':'application/json'}
        )
        with urllib_request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[heal] LLM error: {e}')
        return None

def send_email(subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return
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
    except Exception as e:
        print(f'[heal] Email failed: {e}')

# ── Step 1: Find failed steps in the last workflow run ──────────────────────────────

def get_recent_failures():
    """
    Returns list of {step_name, conclusion, engine_name} for failed steps.
    """
    # Get most recent workflow run
    runs = gh('/actions/runs?per_page=3&status=completed')
    if not runs or not runs.get('workflow_runs'):
        print('[heal] No completed runs found')
        return []

    latest = runs['workflow_runs'][0]
    run_id = latest['id']
    print(f'[heal] Checking run #{run_id} ({latest.get("created_at","")})')

    # Get jobs in that run
    jobs = gh(f'/actions/runs/{run_id}/jobs')
    if not jobs or not jobs.get('jobs'):
        return []

    failures = []
    for job in jobs['jobs']:
        for step in job.get('steps', []):
            if step.get('conclusion') == 'failure':
                name = step.get('name', '')
                # Map step name to engine filename
                # e.g. "Art + Cause" -> art_cause_generator
                engine = name.lower().replace(' + ', '_').replace(' ', '_').replace('-', '_')
                failures.append({
                    'step_name':   name,
                    'engine_name': engine,
                    'job_id':      job['id'],
                    'run_id':      run_id,
                })

    print(f'[heal] Found {len(failures)} failed steps')
    return failures

def get_job_log(job_id):
    """Fetch the log text for a job."""
    try:
        url = f'https://api.github.com/repos/{GITHUB_REPO}/actions/jobs/{job_id}/logs'
        headers = {
            'Authorization': f'Bearer {GITHUB_TOKEN}',
            'Accept':        'application/vnd.github+json',
        }
        req = urllib_request.Request(url, headers=headers)
        with urllib_request.urlopen(req, timeout=20) as r:
            return r.read().decode('utf-8', errors='replace')[-4000:]  # last 4000 chars
    except Exception as e:
        print(f'[heal] Log fetch error: {e}')
        return ''

# ── Step 2: Find the actual engine file ──────────────────────────────────────────────

def find_engine_file(engine_name):
    """Search mycelium/ for a file matching the engine name."""
    mycelium = ROOT / 'mycelium'
    if not mycelium.exists(): return None, None

    # Try exact match first
    candidates = [
        mycelium / f'{engine_name}.py',
    ]
    # Also try fuzzy: split words and find best overlap
    for f in mycelium.glob('*.py'):
        stem = f.stem.lower()
        words = set(engine_name.replace('_',' ').split())
        file_words = set(stem.replace('_',' ').split())
        if len(words & file_words) >= 1:
            candidates.append(f)

    for c in candidates:
        if c.exists():
            try:
                return c, c.read_text()
            except:
                pass
    return None, None

# ── Step 3: Diagnose and patch ───────────────────────────────────────────────────

def diagnose_and_patch(engine_file, engine_code, error_log):
    """
    Ask LLM to read the error log + source code and return a fixed version.
    Returns (diagnosis, patched_code) or (None, None).
    """
    prompt = f"""A Python engine in a GitHub Actions workflow failed. Diagnose and fix it.

ERROR LOG (last 4000 chars):
{error_log}

CURRENT SOURCE CODE ({engine_file.name}):
{engine_code[:6000]}

Tasks:
1. Identify the root cause of the failure in 2-3 sentences
2. Write the complete fixed Python file

Rules:
- Fix ONLY what's broken. Don't refactor unrelated code.
- Standard library only (no pip installs)
- Preserve all existing functionality
- If the error is an external API being down (not a code bug), add a graceful fallback or retry
- If the error is a missing file/directory, add creation logic
- Start fixed code with #!/usr/bin/env python3

Respond ONLY as JSON:
{{"diagnosis": "root cause in 2-3 sentences", "fixed_code": "complete fixed file content"}}
"""
    result = ask_llm(prompt, max_tokens=2000)
    if not result: return None, None
    try:
        start = result.find('{')
        end   = result.rfind('}') + 1
        parsed = json.loads(result[start:end])
        diagnosis   = parsed.get('diagnosis', '')
        fixed_code  = parsed.get('fixed_code', '')
        if fixed_code.startswith('```'):
            fixed_code = '\n'.join(l for l in fixed_code.split('\n') if not l.startswith('```'))
        return diagnosis, fixed_code
    except Exception as e:
        print(f'[heal] Parse error: {e}')
        return None, None

# ── Step 4: Commit the patch ──────────────────────────────────────────────────────────

def commit_patch(filepath, content, engine_name, diagnosis):
    api_url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{filepath}'
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Accept':        'application/vnd.github+json',
        'Content-Type':  'application/json',
    }
    existing = None
    try:
        req = urllib_request.Request(api_url, headers=headers)
        with urllib_request.urlopen(req, timeout=15) as r:
            existing = json.loads(r.read())
    except: pass

    sha = existing.get('sha') if existing else None
    encoded = base64.b64encode(content.encode()).decode()
    msg = f'fix: auto-heal {engine_name} [{TODAY}] — {diagnosis[:80]}'
    payload = {'message': msg, 'content': encoded}
    if sha: payload['sha'] = sha

    try:
        req = urllib_request.Request(api_url, data=json.dumps(payload).encode(),
                                     headers=headers, method='PUT')
        with urllib_request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
        return bool(result.get('content'))
    except Exception as e:
        print(f'[heal] Commit failed: {e}')
        return False

# ── Healing log ────────────────────────────────────────────────────────────────────

def load_heal_log():
    p = DATA / 'healing_log.json'
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return {'heals': []}

def save_heal_log(log):
    try: (DATA / 'healing_log.json').write_text(json.dumps(log, indent=2))
    except: pass

def already_healed_today(log, engine_name):
    return any(
        h.get('engine') == engine_name and h.get('date') == TODAY
        for h in log.get('heals', [])
    )

# ── Main ───────────────────────────────────────────────────────────────────

def run():
    print(f'\n[heal] Error Self-Healing Engine — {TODAY}')

    if not GITHUB_TOKEN or not HF_TOKEN:
        print('[heal] Missing GITHUB_TOKEN or HF_TOKEN. Skipping.')
        return

    heal_log = load_heal_log()
    failures = get_recent_failures()

    if not failures:
        print('[heal] No failures found. System is healthy.')
        return

    healed = []
    skipped = []

    for f in failures:
        engine_name = f['engine_name']
        step_name   = f['step_name']

        # Skip protected engines
        if any(nt in engine_name for nt in NO_TOUCH):
            print(f'[heal] Skipping protected engine: {engine_name}')
            skipped.append(step_name)
            continue

        # Skip if already healed today
        if already_healed_today(heal_log, engine_name):
            print(f'[heal] Already healed {engine_name} today. Skipping.')
            continue

        print(f'[heal] Attempting to heal: {step_name} ({engine_name})')

        # Get error log
        error_log = get_job_log(f['job_id'])
        if not error_log:
            print(f'[heal] No log available for {step_name}')
            skipped.append(step_name)
            continue

        # Find source file
        engine_file, engine_code = find_engine_file(engine_name)
        if not engine_file:
            print(f'[heal] Cannot find source for: {engine_name}')
            skipped.append(step_name)
            continue

        # Diagnose and patch
        diagnosis, fixed_code = diagnose_and_patch(engine_file, engine_code, error_log)
        if not diagnosis or not fixed_code:
            print(f'[heal] LLM could not generate a fix for {engine_name}')
            skipped.append(step_name)
            continue

        # Commit the patch
        rel_path = f'mycelium/{engine_file.name}'
        committed = commit_patch(rel_path, fixed_code, engine_name, diagnosis)

        # Log it
        heal_log['heals'].append({
            'date':      TODAY,
            'engine':    engine_name,
            'step':      step_name,
            'diagnosis': diagnosis,
            'committed': committed,
            'file':      rel_path,
        })
        save_heal_log(heal_log)

        healed.append({
            'step':      step_name,
            'engine':    engine_name,
            'diagnosis': diagnosis,
            'committed': committed,
            'file':      rel_path,
        })

        print(f'[heal] ✅ {engine_name} — {diagnosis[:80]}')

    # Email summary
    if healed:
        lines = [f'Your system healed {len(healed)} engine(s) automatically.\n']
        for h in healed:
            status = '✅ Patched & committed' if h['committed'] else '⚠️ Patch written but commit failed'
            lines += [
                f'ENGINE: {h["step"]}',
                f'FILE:   {h["file"]}',
                f'STATUS: {status}',
                f'DIAGNOSIS: {h["diagnosis"]}',
                '',
            ]
        if skipped:
            lines.append(f'Skipped (protected or no log): {', '.join(skipped)}')
        lines.append('\nNo action needed. Patches take effect next run.')
        send_email(f'🩹 Self-healed {len(healed)} engine(s)', '\n'.join(lines))
    elif skipped:
        print(f'[heal] Nothing healed. Skipped: {skipped}')

    print(f'[heal] Done. Healed: {len(healed)} | Skipped: {len(skipped)}')

if __name__ == '__main__':
    run()
