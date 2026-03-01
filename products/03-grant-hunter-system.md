# The Grant Hunter System
### "I applied to 47 grants while I slept."

*Real grant sources. Real scripts. What the viral posts won't tell you.*

**Price: $1 — 70% goes to PCRF (children's aid in Gaza)**

---

## What You're Getting

A complete automated grant research and application system: where to find grants, how to qualify them fast, and a Python script that searches, logs, and drafts applications on a schedule — while you sleep.

---

## The Honest Truth About Grants First

Most grant guides online are garbage. They list generic foundations or government portals with no guidance on qualification. Here's what actually works:

**High-hit-rate grant categories for individuals and small orgs:**
- Local community foundations (every city has one — 80% of people never apply)
- State arts councils (most have rolling applications, nobody applies)
- Small business development centers (SBA-adjacent, free and underused)
- Tech nonprofit grants (Mozilla, Shuttleworth, Open Technology Fund)
- Cause-specific foundations (Gaza, Palestine, humanitarian — many exist, few apply)

---

## The Databases That Actually Have Money

| Source | What's There | URL |
|--------|-------------|-----|
| Grants.gov | All federal grants | grants.gov |
| Foundation Directory (free tier) | 150k+ foundations | candid.org |
| Instrumentl | Smart matching | instrumentl.com |
| GrantStation | Rolling deadlines | grantstation.com |
| Local Community Foundation | Your city's money | search "[your city] community foundation" |
| Mozilla Foundation | Tech/open source | foundation.mozilla.org/grants |
| Shuttleworth Foundation | Changemakers | shuttleworthfoundation.org |
| Open Technology Fund | Internet freedom | opentech.fund |

---

## The Fast Qualification Test (30 Seconds Per Grant)

Before spending time on any application, ask these 4 questions:

1. **Do I meet the eligibility criteria?** (location, age, org type, cause)
2. **Is the deadline more than 2 weeks away?** (if not, skip)
3. **Is the award amount worth the time?** (under $500 often isn't)
4. **Has this foundation funded similar work before?** (check their past grants)

If all 4 are yes: apply. If any are no: next.

---

## The Script

Save as `grant_hunter.py`:

```python
import requests
import json
import time
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

# ── CONFIG ──────────────────────────────────────────
GMAIL_ADDRESS = "your@gmail.com"
GMAIL_APP_PASSWORD = "your-app-password"
NOTIFY_EMAIL = "your@gmail.com"
OLLAMA_URL = "http://localhost:11434/api/generate"
LOG_FILE = "grants_log.json"

YOUR_PROFILE = """
Name/Org: [YOUR NAME OR ORG]
Location: [CITY, STATE, COUNTRY]
Work type: [ART / TECH / NONPROFIT / INDIVIDUAL]
Cause focus: [HUMANITARIAN / ENVIRONMENT / EDUCATION / etc]
Annual budget: [UNDER $50K / $50K-$250K / etc]
Current projects: [Brief description]
"""

SEARCH_TERMS = [
    "grants for artists 2026",
    "humanitarian technology grants",
    "open source funding opportunities",
    "community foundation grants rolling deadline",
    "Gaza relief funding opportunities NGO",
]

def load_log():
    try:
        with open(LOG_FILE) as f:
            return json.load(f)
    except:
        return {"found": [], "applied": [], "last_run": None}

def save_log(data):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def search_grants_gov(keyword):
    """Search Grants.gov API for matching grants"""
    url = "https://apply07.grants.gov/grantsws/rest/opportunities/search/"
    params = {
        "keyword": keyword,
        "oppStatuses": "forecasted|posted",
        "rows": 10,
        "startRecordNum": 0
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        grants = []
        for opp in data.get("oppHits", []):
            grants.append({
                "title": opp.get("title"),
                "agency": opp.get("agencyName"),
                "deadline": opp.get("closeDate"),
                "amount": opp.get("awardCeiling"),
                "url": f"https://grants.gov/search-grants?cfda={opp.get('cfdaList', [''])[0]}",
                "source": "grants.gov"
            })
        return grants
    except:
        return []

def qualify_grant(grant):
    """Use AI to quickly assess if grant is worth applying to"""
    prompt = f"""Given this applicant profile:
{YOUR_PROFILE}

And this grant opportunity:
Title: {grant['title']}
Agency: {grant['agency']}
Deadline: {grant['deadline']}
Amount: {grant['amount']}

In 2 sentences maximum: Is this worth applying to? Why or why not?
End with either APPLY or SKIP."""

    r = requests.post(OLLAMA_URL, json={
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    })
    return r.json()["response"]

def draft_application(grant):
    """Draft an application letter"""
    prompt = f"""Write a grant application letter for:

Applicant: {YOUR_PROFILE}
Grant: {grant['title']} from {grant['agency']}

Write a compelling 3-paragraph letter:
1. Who I am and what I do
2. Why I need this grant and what I'll use it for
3. Expected impact and why I'm qualified

Be specific. Be honest. Be human."""

    r = requests.post(OLLAMA_URL, json={
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    })
    return r.json()["response"]

def notify(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = NOTIFY_EMAIL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        s.send_message(msg)

def run():
    log = load_log()
    found_today = []

    for term in SEARCH_TERMS:
        print(f"🔍 Searching: {term}")
        grants = search_grants_gov(term)
        for grant in grants:
            if grant["title"] not in [g["title"] for g in log["found"]]:
                assessment = qualify_grant(grant)
                grant["assessment"] = assessment
                grant["found_date"] = datetime.now().isoformat()
                log["found"].append(grant)
                found_today.append(grant)

                if "APPLY" in assessment:
                    draft = draft_application(grant)
                    grant["draft"] = draft
                    filename = f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(filename, "w") as f:
                        f.write(f"GRANT: {grant['title']}\nURL: {grant['url']}\nDEADLINE: {grant['deadline']}\n\n{draft}")
                    print(f"  ✅ Draft saved: {filename}")

        time.sleep(2)

    log["last_run"] = datetime.now().isoformat()
    save_log(log)

    if found_today:
        notify(
            f"Grant Hunter: {len(found_today)} new opportunities found",
            "\n\n".join([f"{g['title']} — {g['assessment']}" for g in found_today])
        )
        print(f"\n📬 Notified: {len(found_today)} new grants found")

if __name__ == "__main__":
    print("🌱 Grant Hunter starting...")
    run()
```

---

## Schedule It (Run Weekly)

**Windows Task Scheduler:** Every Monday 9am
**Mac/Linux cron:**
```bash
0 9 * * 1 python3 /path/to/grant_hunter.py
```

---

## The Application Templates That Work

**Opening that doesn't get skipped:**
> "I am [NAME], a [ROLE] based in [LOCATION] working on [SPECIFIC PROJECT]. I'm applying for [GRANT NAME] because [SPECIFIC REASON TIED TO THEIR MISSION]."

**The number that gets attention:**
> "In the past [X months], I have [specific measurable thing]. This grant would allow me to [specific measurable outcome]."

**The close that gets callbacks:**
> "I've reviewed [FOUNDATION NAME]'s previous grants to [PAST GRANTEE] and [PAST GRANTEE]. My work aligns with that pattern of [SPECIFIC VALUE THEY FUND]."

---

## What Actually Gets Grants Denied

- Generic applications that could apply to any grant
- Asking for too much with no budget breakdown
- Missing the actual eligibility criteria (not reading the requirements)
- Applying to foundations that don't fund your type of work
- Submitting at the last minute (some portals close early)

---

*Built by Meeko Mycelium · github.com/meekotharaccoon-cell*
*70% of every sale → PCRF · pcrf.net*
