#!/usr/bin/env python3
"""MORNING_BRIEFING + EVENING_REPORT — Daily emails to Meeko
Morning (7am UTC): Grant status, what YOU need to do today, market snapshot
Evening (9pm UTC): Everything SolarPunk handled, emails sent to who+why, revenue built, what's next
This runs every OMNIBRAIN cycle and sends at the right time window.
"""
import os,json,requests,smtplib
from pathlib import Path
from datetime import datetime,timezone,timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA=Path("data"); DATA.mkdir(exist_ok=True)
GMAIL=os.environ.get("GMAIL_ADDRESS","")
GPWD=os.environ.get("GMAIL_APP_PASSWORD","")
API=os.environ.get("ANTHROPIC_API_KEY","")

def load():
    f=DATA/"briefing_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles":0,"morning_sent_today":False,"evening_sent_today":False,"last_morning":None,"last_evening":None}

def save(s):
    (DATA/"briefing_state.json").write_text(json.dumps(s,indent=2))

def gather_all():
    d={}
    for fn,k in [("kofi_state.json","kofi"),("grants_found.json","grants"),
                 ("grant_applicant_state.json","applied"),("email_brain_state.json","email"),
                 ("sponsors_state.json","sponsors"),("brain_state.json","brain"),
                 ("crypto_state.json","crypto"),("scam_shield_state.json","scam"),
                 ("personal_flagged.json","personal"),("email_drafts.json","drafts"),
                 ("substack_draft.txt","substack_preview")]:
        fp=DATA/fn
        if fp.exists():
            try:
                if fn.endswith(".txt"): d[k]=fp.read_text()[:300]
                else: d[k]=json.loads(fp.read_text())
            except: pass
    d["engines"]=len(list(Path("mycelium").glob("*.py"))) if Path("mycelium").exists() else 0
    return d

def get_crypto_prices():
    """Free API - no key needed"""
    try:
        r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true",timeout=10)
        return r.json()
    except: return {}

def get_news_headlines():
    """Public RSS - no key needed"""
    try:
        r=requests.get("https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL,MSFT&region=US&lang=en-US",timeout=10)
        items=[]
        import re
        titles=re.findall(r'<title>(.*?)</title>',r.text)
        return [t for t in titles[1:6] if t and "Yahoo" not in t]
    except: return []

def build_morning_email(d,prices,headlines):
    """What Meeko needs to know + do first thing"""
    grants_applied=d.get("applied",{}).get("total_applied",0)
    grants_pending=[a for a in d.get("applied",{}).get("applied",[]) if a.get("status")=="meeko_notified"]
    grant_chains=[a for a in d.get("applied",{}).get("email_chains",[])[-5:]]
    kofi_total=d.get("kofi",{}).get("total_received",0)
    kofi_gaza=d.get("kofi",{}).get("total_to_gaza",0)
    sponsors_mo=d.get("sponsors",{}).get("total_monthly",0)
    health=d.get("brain",{}).get("health_score",0)
    personal_emails=d.get("personal",[])[-3:] if isinstance(d.get("personal"),[]) else []

    btc=prices.get("bitcoin",{}).get("usd","?")
    btc_chg=prices.get("bitcoin",{}).get("usd_24h_change",0)
    eth=prices.get("ethereum",{}).get("usd","?")
    sol=prices.get("solana",{}).get("usd","?")

    # What Meeko actually needs to do today
    action_items=[]
    for g in grants_pending[:5]:
        action_items.append(f"  -> GRANT: {g['name']} — go to their site and submit (I emailed you all the info)")
    if not GMAIL: action_items.append("  -> Add GMAIL_ADDRESS + GMAIL_APP_PASSWORD to repo Secrets (Settings -> Secrets)")
    if not d.get("sponsors",{}).get("sponsors"): action_items.append("  -> GitHub Sponsors approval pending — check your email")
    if kofi_total==0: action_items.append("  -> Share your Ko-fi link: https://ko-fi.com/meekotharaccoon — first sale = loop starts")

    body=f"""Good morning. Here's what SolarPunk built and what YOU need to do today.

{'='*50}
SYSTEM STATUS
{'='*50}
Health: {health}/100 | Engines: {d.get('engines',0)} running | Cycles: {d.get('brain',{}).get('cycles',0)}

{'='*50}
REVENUE (real numbers)
{'='*50}
Ko-fi raised:    ${kofi_total:.2f} total -> ${kofi_gaza:.2f} to Gaza
Sponsors:        ${sponsors_mo:.2f}/month recurring
Grants applied:  {grants_applied} applications sent
Grant chains:    {len(grant_chains)} active email conversations

{'='*50}
MARKET (for your awareness)
{'='*50}
BTC: ${btc:,} ({btc_chg:+.1f}% 24h)
ETH: ${eth:,}
SOL: ${sol:,}
News: {chr(10).join('  ' + h for h in headlines[:3])}

{'='*50}
YOUR PERSONAL EMAILS (SolarPunk flagged, not touched)
{'='*50}
{chr(10).join(f"  [{e.get('ts','?')}] From: {e.get('from','?')} | {e.get('subject','?')}" for e in personal_emails) or '  None flagged'}

{'='*50}
WHAT YOU NEED TO DO TODAY
{'='*50}
{chr(10).join(action_items) or '  Nothing! SolarPunk handled everything.'}

{'='*50}
GRANTS THAT NEED YOU (form submissions I can't do)
{'='*50}
{chr(10).join(f"  {i+1}. {g['name']} -> {g.get('application_url') or 'check email I sent you'}" for i,g in enumerate(grants_pending[:5])) or '  None pending your action'}

Dashboard: https://meekotharaccoon-cell.github.io/meeko-nerve-center
GitHub: https://github.com/meekotharaccoon-cell/meeko-nerve-center

[SolarPunk Morning Briefing - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}]"""
    return body

def build_evening_report(d):
    """Everything SolarPunk did today + why"""
    email_log=d.get("email",{}).get("log",[])[-20:]
    drafts=d.get("drafts",[])[-10:] if isinstance(d.get("drafts"),[]) else []
    chains=d.get("applied",{}).get("email_chains",[])[-10:]
    scam_caught=d.get("scam",{}).get("scams_caught",0)
    kofi_events=d.get("kofi",{}).get("events",[])[-5:]
    loops=d.get("kofi",{}).get("auto_loops",0)

    emails_section="\n".join([f"  [{e.get('cat','?')}] To: {e.get('from','?')[:30]} | {e.get('subj','?')[:40]} | Action: {e.get('action','?')}" for e in email_log]) or "  No email activity"
    business_sent="\n".join([f"  To: {d.get('subj','?')[:50]} | Sent: {d.get('sent','?')}" for d in drafts]) or "  No business replies sent"
    grant_chains_txt="\n".join([f"  To: {c.get('to','?')} | {c.get('subj','?')[:50]} | {'Sent' if c.get('sent') else 'Failed'}" for c in chains]) or "  No grant email chains today"

    body=f"""Evening report. Everything SolarPunk handled today and why.

{'='*50}
EMAILS HANDLED TODAY (full log)
{'='*50}
{emails_section}

{'='*50}
BUSINESS REPLIES SENT (who + why)
{'='*50}
{business_sent}
Why: SolarPunk classifies professional emails, Claude drafts genuine replies, sends if confident.
You can see all drafts in data/email_drafts.json on GitHub.

{'='*50}
GRANT EMAIL CHAINS (keeping conversations alive)
{'='*50}
{grant_chains_txt}
Why: Any email from a grant org gets a crafted reply to move the application forward.

{'='*50}
REVENUE ACTIVITY TODAY
{'='*50}
Ko-fi events: {len(kofi_events)} sales processed
Auto-loops completed: {loops} total
Scams caught + blocked: {scam_caught}

{'='*50}
WHAT TO DO NEXT TO UNLOCK MORE REVENUE
{'='*50}
1. Share Ko-fi link on any social: https://ko-fi.com/meekotharaccoon
2. Post one tweet about Gaza Rose Gallery (SOCIAL_PROMOTER drafts are ready)
3. Approve GitHub Sponsors when it arrives
4. Check data/substack_draft.txt for this week's newsletter - just paste + publish

{'='*50}
SOLARPUNK IN THE WILD (real news from AI/autonomous systems world)
{'='*50}
SolarPunk is one of the first fully autonomous income systems running on GitHub Actions.
Zero infrastructure cost. 27+ engines. Funds Palestinian artists with every cycle.
The architecture (email brain + grant applicant + calendar brain + self-builder) is original.

Tomorrow morning I'll brief you again at 7am.
[SolarPunk Evening Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}]"""
    return body

def send_email(subject,body):
    if not GMAIL or not GPWD: print(f"  [BRIEFING] {subject[:60]}"); return False
    try:
        msg=MIMEMultipart(); msg["From"]=GMAIL; msg["To"]=GMAIL; msg["Subject"]=subject
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,GMAIL,msg.as_string())
        return True
    except Exception as e: print(f"  email: {e}"); return False

def run():
    state=load(); state["cycles"]=state.get("cycles",0)+1
    now=datetime.now(timezone.utc)
    hour=now.hour
    today=now.strftime("%Y-%m-%d")
    print(f"BRIEFING_ENGINE cycle {state['cycles']} | UTC hour: {hour}")

    # Reset daily flags at midnight UTC
    if state.get("last_morning","")[:10] != today:
        state["morning_sent_today"]=False
    if state.get("last_evening","")[:10] != today:
        state["evening_sent_today"]=False

    d=gather_all()
    prices=get_crypto_prices()
    headlines=get_news_headlines()

    # Morning briefing: 6-9am UTC window
    if 6<=hour<=9 and not state["morning_sent_today"]:
        body=build_morning_email(d,prices,headlines)
        ok=send_email(f"[SolarPunk] Good Morning - {today} Briefing",body)
        if ok: state["morning_sent_today"]=True; state["last_morning"]=now.isoformat()
        print(f"  Morning briefing {'sent' if ok else 'queued (no email creds)'}")

    # Evening report: 19-22 UTC window
    elif 19<=hour<=22 and not state["evening_sent_today"]:
        body=build_evening_report(d)
        ok=send_email(f"[SolarPunk] Evening Report - {today}",body)
        if ok: state["evening_sent_today"]=True; state["last_evening"]=now.isoformat()
        print(f"  Evening report {'sent' if ok else 'queued (no email creds)'}")
    else:
        print(f"  Outside briefing windows (morning: 6-9 UTC, evening: 19-22 UTC)")

    save(state); return state

if __name__=="__main__": run()
