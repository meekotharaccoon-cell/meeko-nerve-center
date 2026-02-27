#!/usr/bin/env python3
"""
Autonomy Audit Engine
======================
The system asks itself:
  "What am I still doing manually? What still needs me in the loop?
   What could I fully automate that I'm not automating yet?"

Then it implements the fixes.

This runs once a week (or on demand) and:
  1. Surveys every engine for human-dependency gaps
  2. Uses LLM to identify the highest-impact autonomy gap
  3. Designs and implements the fix
  4. Commits it
  5. Emails you what changed and why

The goal: every task the system could do autonomously, it does.
You are informed. You are never required.
"""

import json, datetime, os, base64
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
KB    = ROOT / 'knowledge'

TODAY     = datetime.date.today().isoformat()
WEEKDAY   = datetime.date.today().weekday()  # 0=Mon, 6=Sun

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO        = 'meekotharaccoon-cell/meeko-nerve-center'

# ── Known autonomy gaps to audit ─────────────────────────────────────────────────────
# Each gap: what the system currently needs from you, how it could be autonomous
KNOWN_GAPS = [
    {
        'id': 'grant_application_submission',
        'description': 'Grant applications still require manual form submission on most platforms',
        'current_state': 'System drafts emails and blurbs but cannot submit web forms autonomously',
        'autonomy_target': 'Auto-detect API-submittable grants, submit via API where possible, draft a pre-filled PDF for manual ones and email it to you ready to copy-paste',
        'impact': 'high',
    },
    {
        'id': 'social_scheduling',
        'description': 'Social posts go out at fixed cron times, not optimized timing',
        'current_state': 'Posts when the workflow runs, not when audience is most active',
        'autonomy_target': 'Analyze past engagement via API, schedule posts for optimal times per platform',
        'impact': 'medium',
    },
    {
        'id': 'ko_fi_page_update',
        'description': 'Ko-fi page content does not update automatically with new art or stats',
        'current_state': 'Manual update required when new Gaza Rose art is generated',
        'autonomy_target': 'Auto-post new art to Ko-fi via their API when generated',
        'impact': 'high',
    },
    {
        'id': 'error_self_healing',
        'description': 'When engines fail, the error is logged but nothing is done about it',
        'current_state': 'continue-on-error means failures are silent and permanent',
        'autonomy_target': 'Detect repeated failures in engine logs, diagnose with LLM, patch the code, commit fix',
        'impact': 'critical',
    },
    {
        'id': 'content_performance_tracking',
        'description': 'System posts content but never learns what resonates',
        'current_state': 'No feedback loop from social engagement back into content decisions',
        'autonomy_target': 'Fetch Mastodon/Bluesky post stats via API, feed top performers back into content strategy',
        'impact': 'high',
    },
    {
        'id': 'donor_followup_sequence',
        'description': 'Donors get one thank-you email and then silence',
        'current_state': 'No ongoing relationship with past donors',
        'autonomy_target': 'Build a 3-touch donor sequence: thank-you on day 0, PCRF impact on day 7, new art on day 30',
        'impact': 'medium',
    },
    {
        'id': 'press_followup',
        'description': 'Press outreach emails go out but are never followed up if no reply',
        'current_state': 'One email, no follow-up, no tracking of who replied',
        'autonomy_target': 'Track sent press emails, auto-follow-up after 5 days if no reply, retire after 2nd follow-up',
        'impact': 'high',
    },
    {
        'id': 'gumroad_listing_update',
        'description': 'Gaza Rose art listings on Gumroad are not updated automatically',
        'current_state': 'New FLUX-generated art exists in public/images but is not listed for sale',
        'autonomy_target': 'Auto-create Gumroad product listings for new art via Gumroad API',
        'impact': 'high',
    },
    {
        'id': 'system_health_alerting',
        'description': 'System health is only visible by reading GitHub Actions logs',
        'current_state': 'No proactive alerting when something important breaks',
        'autonomy_target': 'Daily health score in status email, alert if score drops below 70%',
        'impact': 'medium',
    },
    {
        'id': 'wikipedia_contribution',
        'description': 'System consumes Wikipedia data but never contributes back',
        'current_state': 'One-directional relationship with public knowledge',
        'autonomy_target': 'Draft Wikipedia citation suggestions for Palestinian accountability data, flag for review',
        'impact': 'low',
    },
]

# ── Utilities ─────────────────────────────────────────────────────────────────

def ask_llm(prompt, system='You are a senior Python engineer. Write working code. Be direct.', max_tokens=2000):
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
        print(f'[audit] LLM error: {e}')
        return None

def commit_file(path, content, message):
    if not GITHUB_TOKEN: return False
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{path}'
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Accept':        'application/vnd.github+json',
        'Content-Type':  'application/json',
    }
    existing = None
    try:
        req = urllib_request.Request(url, headers=headers)
        with urllib_request.urlopen(req, timeout=15) as r:
            existing = json.loads(r.read())
    except: pass

    sha     = existing.get('sha') if existing else None
    encoded = base64.b64encode(content.encode()).decode()
    payload = {'message': message, 'content': encoded}
    if sha: payload['sha'] = sha

    try:
        req = urllib_request.Request(url, data=json.dumps(payload).encode(),
                                     headers=headers, method='PUT')
        with urllib_request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
        return bool(result.get('content'))
    except Exception as e:
        print(f'[audit] Commit failed {path}: {e}')
        return False

def send_email(subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return False
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
        return True
    except Exception as e:
        print(f'[audit] Email failed: {e}')
        return False

# ── Step 1: Discover additional gaps dynamically ──────────────────────────────────

def discover_new_gaps():
    """
    Read all engine files and ask LLM if it sees any remaining
    human-dependency that could be automated.
    """
    engines = sorted((ROOT / 'mycelium').glob('*.py')) if (ROOT / 'mycelium').exists() else []
    engine_names = [e.stem for e in engines]

    known_ids = {g['id'] for g in KNOWN_GAPS}

    prompt = f"""
You are auditing an autonomous humanitarian AI system for remaining human dependencies.

Existing engines: {', '.join(engine_names)}

Already identified gaps: {json.dumps([g['id'] for g in KNOWN_GAPS])}

The system's mission:
- Monitor Congressional stock trades and publish accountability content
- Generate Gaza Rose art, sell it, send 70% to Palestinian children via PCRF
- Auto-post to Bluesky + Mastodon
- Self-evolve by building new engines daily
- Reply to all system-related emails autonomously

Identify up to 3 NEW human-dependency gaps not already in the list above.
For each, describe what still requires human action and what full autonomy would look like.

Respond ONLY as JSON array:
[
  {{
    "id": "snake_case_id",
    "description": "what gap this is",
    "current_state": "what still needs a human",
    "autonomy_target": "what full automation looks like",
    "impact": "high|medium|low"
  }}
]
"""
    result = ask_llm(prompt, max_tokens=800)
    if not result: return []
    try:
        start = result.find('[')
        end   = result.rfind(']') + 1
        new_gaps = json.loads(result[start:end])
        return [g for g in new_gaps if g.get('id') not in known_ids]
    except:
        return []

# ── Step 2: Pick highest-impact unresolved gap ───────────────────────────────────

def pick_gap_to_fix(all_gaps, already_fixed):
    impact_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    candidates = [
        g for g in all_gaps
        if g['id'] not in already_fixed
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda g: impact_order.get(g.get('impact','low'), 3))
    return candidates[0]

# ── Step 3: Implement the fix ───────────────────────────────────────────────────────

def implement_fix(gap):
    """
    Ask LLM to write Python code that closes this autonomy gap.
    Returns (filename, code) or (None, None).
    """
    prompt = f"""
Write a complete Python script that closes this autonomy gap in the Meeko Nerve Center:

GAP ID:          {gap['id']}
DESCRIPTION:     {gap['description']}
CURRENT STATE:   {gap['current_state']}
AUTONOMY TARGET: {gap['autonomy_target']}

REQUIREMENTS:
- Standard library only (json, datetime, os, pathlib, urllib.request, smtplib, email)
- ROOT = Path(__file__).parent.parent
- DATA = ROOT / 'data'
- KB   = ROOT / 'knowledge'
- run() function + if __name__ == '__main__': run()
- Print progress with [{gap['id'][:12]}] prefix
- Handle all errors with try/except — never crash
- Use env vars for secrets: HF_TOKEN, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, GITHUB_TOKEN
- If it creates social content: save to content/queue/ as JSON list
- If it sends email: use gmail SMTP on port 587

Write ONLY the Python code. No markdown. No backticks. Start with #!/usr/bin/env python3
"""
    print(f'[audit] Writing code to fix: {gap["id"]}')
    code = ask_llm(prompt, max_tokens=2000)
    if not code or len(code) < 100:
        return None, None
    # Strip any accidental markdown
    if code.startswith('```'):
        code = '\n'.join(l for l in code.split('\n') if not l.startswith('```'))
    filename = f'mycelium/{gap["id"]}.py'
    return filename, code

# ── Log and report ────────────────────────────────────────────────────────────────

def load_audit_log():
    log_path = DATA / 'autonomy_audit.json'
    if log_path.exists():
        try: return json.loads(log_path.read_text())
        except: pass
    return {'fixed': [], 'pending': [], 'last_run': None}

def save_audit_log(log):
    try:
        (DATA / 'autonomy_audit.json').write_text(json.dumps(log, indent=2))
        commit_file('data/autonomy_audit.json',
                    json.dumps(log, indent=2),
                    f'audit: autonomy log updated {TODAY}')
    except Exception as e:
        print(f'[audit] Log save error: {e}')

def email_audit_report(gap, filename, code, committed, all_gaps, still_pending):
    impact_icons = {'critical': '🚨', 'high': '🔴', 'medium': '🟡', 'low': '🟢'}
    icon = impact_icons.get(gap.get('impact', 'medium'), '🔵')

    pending_list = '\n'.join(
        f'  {impact_icons.get(g.get("impact","low"),"⭐")} [{g["impact"]}] {g["description"]}'
        for g in still_pending[:8]
    )

    body = f"""Your system audited itself for remaining human dependencies.

Here's what it fixed today.

{'=' * 60}
{icon} AUTONOMY GAP CLOSED: {gap['description']}
{'=' * 60}

Impact:          {gap['impact'].upper()}
File created:    {filename}
Committed:       {'Yes' % () if committed else 'No (check logs)'}

What was wrong:
{gap['current_state']}

What it built to fix it:
{gap['autonomy_target']}

{'=' * 60}
CODE WRITTEN:
{'=' * 60}

{code[:2500] if code else '[none]'}
{'...(truncated)' if code and len(code) > 2500 else ''}

{'=' * 60}
STILL PENDING ({len(still_pending)} gaps remaining):
{'=' * 60}

{pending_list if pending_list else 'None! Fully autonomous.'}

Next audit: next Sunday.
View audit log: https://github.com/{GITHUB_REPO}/blob/main/data/autonomy_audit.json
"""
    send_email(f'🧠 Autonomy gap closed: {gap["description"][:50]}', body)

# ── Main ───────────────────────────────────────────────────────────────────

def run():
    print(f'\n[audit] Autonomy Audit Engine — {TODAY}')

    # Only run on Sundays (weekday 6) to avoid hammering LLM daily
    # But always run if triggered manually (workflow_dispatch)
    # We check via env var FORCE_AUDIT
    is_sunday = WEEKDAY == 6
    force     = os.environ.get('FORCE_AUDIT', '').lower() in ('1', 'true', 'yes')
    if not is_sunday and not force:
        print(f'[audit] Not Sunday (weekday={WEEKDAY}). Skipping. Set FORCE_AUDIT=1 to override.')
        return

    log = load_audit_log()
    already_fixed = set(log.get('fixed', []))

    # Combine known gaps with dynamically discovered ones
    print('[audit] Discovering new autonomy gaps...')
    new_gaps = discover_new_gaps()
    all_gaps = KNOWN_GAPS + new_gaps

    # Save all pending gaps for visibility
    log['pending'] = [
        {'id': g['id'], 'description': g['description'], 'impact': g.get('impact','medium')}
        for g in all_gaps if g['id'] not in already_fixed
    ]
    log['last_run'] = TODAY

    print(f'[audit] {len(all_gaps)} total gaps | {len(already_fixed)} fixed | {len(log["pending"])} remaining')

    # Pick the highest-impact unresolved gap
    gap = pick_gap_to_fix(all_gaps, already_fixed)
    if not gap:
        print('[audit] All known gaps resolved! System is fully autonomous.')
        send_email('🎉 Full autonomy achieved', 'All identified autonomy gaps have been resolved. The system is fully self-sufficient.')
        save_audit_log(log)
        return

    print(f'[audit] Fixing: [{gap["impact"]}] {gap["description"]}')

    # Implement the fix
    filename, code = implement_fix(gap)
    committed = False
    if filename and code:
        committed = commit_file(
            filename, code,
            f'fix: close autonomy gap "{gap["id"]}" — {gap["description"][:60]} [{TODAY}]'
        )

    # Log it
    if committed:
        log.setdefault('fixed', []).append(gap['id'])
    log.setdefault('history', []).append({
        'date':      TODAY,
        'gap_id':    gap['id'],
        'committed': committed,
        'filename':  filename,
    })
    save_audit_log(log)

    # Tell you what happened
    still_pending = [g for g in all_gaps if g['id'] not in set(log.get('fixed', []))]
    email_audit_report(gap, filename, code, committed, all_gaps, still_pending)

    print(f'[audit] Done. Gap fixed: {gap["id"]} | Committed: {committed}')
    print(f'[audit] Remaining gaps: {len(still_pending)}')

if __name__ == '__main__':
    run()
