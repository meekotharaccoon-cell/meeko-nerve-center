#!/usr/bin/env python3
"""
Job Agent — The system IS the employee
========================================
This engine applies for remote work on behalf of the human.
The human provides their real name and identity for paperwork.
The system does ALL the work: code, writing, research, data analysis.
Revenue flows to human. System earns its keep.

This is not a trick. This is a new category of employment:
  - Human: identity, legal entity, account holder
  - System: skill, availability, execution
  - Revenue: 100% to human → revenue_router handles splits

The system answers every question honestly:
  - "Do you use AI tools?" YES
  - "Can you deliver by Friday?" YES (given task complexity)
  - "What are your skills?" Code, writing, research, data analysis, automation
  - "Why do you want this job?" To fund Palestinian children's medical relief

Platforms targeted:
  1. Upwork (largest freelance platform)
  2. Freelancer.com
  3. PeoplePerHour
  4. Remote job boards (remotive.io, weworkremotely.com)
  5. GitHub Jobs

Skills the system actually has (and will honestly represent):
  - Python automation and scripting
  - Data analysis and processing
  - Content writing and research
  - Web scraping
  - API integration
  - AI/ML pipeline building
  - Grant writing
  - Social media management
"""

import json, os, datetime
from pathlib import Path
from urllib import request as urllib_request

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / 'data'
TODAY = datetime.date.today().isoformat()

HF_TOKEN           = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS      = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
UPWORK_API_KEY     = os.environ.get('UPWORK_API_KEY', '')

# Human's identity for job applications (filled by setup_wizard.py)
HUMAN_NAME         = os.environ.get('HUMAN_FULL_NAME', '')
HUMAN_EMAIL        = os.environ.get('HUMAN_EMAIL', GMAIL_ADDRESS)
HUMAN_LOCATION     = os.environ.get('HUMAN_LOCATION', 'United States')
HUMAN_TIMEZONE     = os.environ.get('HUMAN_TIMEZONE', 'EST')

# Skills the system ACTUALLY has and will honestly represent
SYSTEM_SKILLS = [
    'Python scripting and automation',
    'Data analysis and processing (pandas, JSON, CSV)',
    'API integration and webhook handling',
    'Web scraping and data collection',
    'Content writing: technical, grants, social media',
    'GitHub Actions and CI/CD automation',
    'AI/LLM prompt engineering and pipeline building',
    'Social media management and scheduling',
    'Grant research and application writing',
    'Report generation and documentation',
]

# Job types the system can genuinely deliver
TARGET_JOB_TYPES = [
    'python automation',
    'data entry and processing',
    'content writing',
    'research assistant',
    'social media management',
    'web scraping',
    'api integration',
    'grant writing',
    'virtual assistant technical',
    'report writing',
]


def load(path, default=None):
    try:
        p = Path(path)
        if p.exists(): return json.loads(p.read_text())
    except: pass
    return default if default is not None else {}


def hf_generate(prompt, system_prompt, max_tokens=600):
    if not HF_TOKEN: return None
    payload = json.dumps({
        'model': 'meta-llama/Llama-3.3-70B-Instruct:fastest',
        'max_tokens': max_tokens,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user',   'content': prompt}
        ]
    }).encode()
    try:
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=45) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[job_agent] LLM error: {e}')
        return None


# ── Generate cover letter for a specific job ─────────────────────────────────────
def generate_cover_letter(job):
    """
    Generates an honest cover letter.
    Never lies. States clearly that AI tools are used extensively.
    Emphasizes: availability, reliability, quality, turnaround speed.
    """
    title   = job.get('title', 'Remote position')
    desc    = job.get('description', '')[:800]
    budget  = job.get('budget', 'negotiable')
    skills  = job.get('required_skills', [])

    system = (
        'You write honest, direct job application cover letters for a remote worker. '
        'The worker uses AI tools extensively and states this openly. '
        'Never exaggerate. Never lie. Be specific about what can be delivered and when. '
        'The worker cares about ethical work and mentions it naturally when relevant.'
    )

    prompt = f"""Write a cover letter for this remote job:

Job: {title}
Budget: {budget}
Description: {desc}
Required skills: {', '.join(skills[:5])}

About the applicant:
- Name: {HUMAN_NAME or 'Available on request'}
- Location: {HUMAN_LOCATION}, {HUMAN_TIMEZONE}
- Uses AI tools extensively and openly (this is a feature, not a bug)
- Skills: {', '.join(SYSTEM_SKILLS[:6])}
- Availability: immediate start, flexible hours, async-friendly
- Turnaround: fast (automated pipelines for routine tasks)
- Motivation: work funds Palestinian children's medical relief (honest)

Write 150-200 words. Be direct. Lead with the most relevant skill.
Acknowledge AI tool use positively. End with clear next step."""

    return hf_generate(prompt, system, max_tokens=400)


# ── Scan job boards (no API key needed) ────────────────────────────────────────
def scan_remotive():
    """Scan remotive.io for remote jobs (public RSS/JSON)."""
    try:
        req = urllib_request.Request(
            'https://remotive.com/api/remote-jobs?category=software-dev&limit=20',
            headers={'User-Agent': 'SolarPunk Job Agent / meeko-nerve-center'}
        )
        with urllib_request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        jobs = data.get('jobs', [])
        print(f'[job_agent] Remotive: {len(jobs)} jobs found')
        return [
            {
                'platform': 'remotive',
                'id': j.get('id'),
                'title': j.get('title', ''),
                'company': j.get('company_name', ''),
                'description': j.get('description', '')[:500],
                'url': j.get('url', ''),
                'salary': j.get('salary', ''),
                'tags': j.get('tags', []),
                'date': j.get('publication_date', TODAY)[:10],
            }
            for j in jobs[:10]
        ]
    except Exception as e:
        print(f'[job_agent] Remotive error: {e}')
        return []

def scan_github_jobs():
    """Scan GitHub job board."""
    # GitHub Jobs was sunset but we can check companies hiring via GitHub
    # Instead, scan for 'hiring' posts in relevant GitHub discussions
    return []  # Placeholder — expand later


# ── Score job fit ─────────────────────────────────────────────────────────────────
def score_job(job):
    """Score a job on fit 0-10."""
    score = 0
    title_lower = job.get('title', '').lower()
    desc_lower  = job.get('description', '').lower()
    tags        = [t.lower() for t in job.get('tags', [])]
    combined    = title_lower + ' ' + desc_lower + ' ' + ' '.join(tags)

    # High value keywords
    for kw in ['python', 'automation', 'data', 'research', 'writing', 'content', 'api', 'scraping']:
        if kw in combined: score += 1

    # Bonus for async/remote-first
    if 'async' in combined or 'flexible' in combined: score += 1

    # Penalty for things we can't do
    for anti in ['video call required', 'in-person', 'design', 'photoshop', 'illustrator']:
        if anti in combined: score -= 2

    # Penalty for jobs that require being a human specifically
    for anti_human in ['must be us citizen only', 'clearance required', 'w2 only']:
        if anti_human in combined: score -= 3

    return max(0, min(10, score))


# ── Build application queue ─────────────────────────────────────────────────────────
def run():
    print(f'\n[job_agent] Job Agent — {TODAY}')
    print('[job_agent] The system IS the employee. Scanning for work.')
    DATA.mkdir(parents=True, exist_ok=True)

    # Load existing applications to avoid duplicates
    apps_path = DATA / 'job_applications.json'
    applications = load(apps_path, {'applied': [], 'pending': [], 'revenue': []})
    applied_ids = {a['id'] for a in applications['applied']}

    # Scan job boards
    all_jobs = []
    all_jobs.extend(scan_remotive())
    # Future: all_jobs.extend(scan_upwork())
    # Future: all_jobs.extend(scan_freelancer())

    print(f'[job_agent] Total jobs found: {len(all_jobs)}')

    # Score and filter
    scored = [(score_job(j), j) for j in all_jobs]
    scored.sort(key=lambda x: -x[0])
    good_jobs = [(s, j) for s, j in scored if s >= 5 and j.get('id') not in applied_ids]

    print(f'[job_agent] Good fit jobs (score >= 5): {len(good_jobs)}')

    # Generate applications for top 3
    new_applications = []
    for score, job in good_jobs[:3]:
        print(f'[job_agent] Applying: {job["title"][:60]} (score: {score}/10)')
        cover = generate_cover_letter(job)
        if not cover:
            print('[job_agent] No LLM — using template')
            cover = (
                f"Hi,\n\nI'm applying for {job['title']}.\n\n"
                f"I use AI tools extensively and deliver fast, reliable work. "
                f"Skills: {', '.join(SYSTEM_SKILLS[:4])}.\n\n"
                f"Available immediately. Flexible hours. Async-friendly.\n\n"
                f"This work funds Palestinian children's medical relief.\n\n"
                f"Best,\n{HUMAN_NAME or 'Applicant'}"
            )

        app = {
            'id': str(job.get('id', f'{job["platform"]}_{hash(job["title"])}'))[:50],
            'platform': job['platform'],
            'title': job['title'],
            'company': job.get('company', ''),
            'url': job.get('url', ''),
            'score': score,
            'applied_date': TODAY,
            'cover_letter': cover,
            'status': 'draft',  # Human reviews before actual submission
            'salary': job.get('salary', ''),
        }
        new_applications.append(app)
        print(f'[job_agent] ✅ Application drafted: {job["title"][:50]}')

    # Save applications
    applications['pending'].extend(new_applications)
    # Keep last 100 applied
    applications['applied'] = applications['applied'][-100:]
    apps_path.write_text(json.dumps(applications, indent=2))

    # Write to DRAFT_EMAILS.md for human review
    if new_applications:
        drafts_path = ROOT / 'DRAFT_JOB_APPLICATIONS.md'
        lines = [
            f'# Job Applications — {TODAY}',
            f'> {len(new_applications)} applications drafted. Review and submit.',
            f'> Once you submit, mark status as "applied" in data/job_applications.json',
            '',
        ]
        for app in new_applications:
            lines += [
                f'## {app["title"]} @ {app["company"]}',
                f'**Score:** {app["score"]}/10 | **Platform:** {app["platform"]}',
                f'**URL:** {app["url"]}',
                f'**Salary:** {app["salary"] or "not listed"}',
                '',
                '**Cover Letter:**',
                '```',
                app['cover_letter'],
                '```',
                '---',
                '',
            ]
        drafts_path.write_text('\n'.join(lines))
        print(f'[job_agent] Applications written to DRAFT_JOB_APPLICATIONS.md')
        print(f'[job_agent] Review, then submit manually (or add Upwork API key for auto-submit)')

    print(f'\n[job_agent] Summary:')
    print(f'  Jobs scanned: {len(all_jobs)}')
    print(f'  Good fits: {len(good_jobs)}')
    print(f'  Applications drafted: {len(new_applications)}')
    print(f'  All-time applied: {len(applications["applied"])}')
    print('[job_agent] System is now seeking employment. Revenue incoming.')


if __name__ == '__main__':
    run()
