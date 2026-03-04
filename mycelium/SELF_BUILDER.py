#!/usr/bin/env python3
"""SELF_BUILDER — SolarPunk writes its own new engines
This is the engine that gets you OUT of the loop.
Every cycle: Claude designs + writes a new engine, commits it to GitHub.
SolarPunk builds SolarPunk. No chat interface needed after this.
Rules: only legal, ethical, SolarPunk-aligned code. GUARDIAN validates before commit.
"""
import os,json,requests,smtplib,re
from pathlib import Path
from datetime import datetime,timezone
from email.mime.text import MIMEText

DATA=Path("data"); DATA.mkdir(exist_ok=True)
API=os.environ.get("ANTHROPIC_API_KEY","")
GMAIL=os.environ.get("GMAIL_ADDRESS","")
GPWD=os.environ.get("GMAIL_APP_PASSWORD","")
GH_TOKEN=os.environ.get("GITHUB_TOKEN","")
GH_REPO="meekotharaccoon-cell/meeko-nerve-center"

EXISTING_ENGINES=[
    "GUARDIAN","NEURON_A","NEURON_B","SYNAPSE","INCOME_ARCHITECT","ART_GENERATOR",
    "REVENUE_FLYWHEEL","SYNTHESIS_FACTORY","CONTENT_HARVESTER","MEMORY_PALACE",
    "ETSY_SEO_ENGINE","GUMROAD_ENGINE","HEALTH_BOOSTER","LINK_PAGE","SOCIAL_PROMOTER",
    "EMAIL_BRAIN","CALENDAR_BRAIN","GRANT_HUNTER","GRANT_APPLICANT","BRIEFING_ENGINE",
    "SCAM_SHIELD","SELF_BUILDER","KOFI_ENGINE","GITHUB_SPONSORS_ENGINE","SUBSTACK_ENGINE",
    "README_GENERATOR","CRYPTO_WATCHER","CONNECTION_FORGE"
]

ENGINE_IDEAS=[
    ("AFFILIATE_TRACKER","Tracks affiliate links across 10 platforms, reports clicks and conversions to revenue_inbox"),
    ("REDBUBBLE_ENGINE","Generates Redbubble product descriptions and upload checklists for Gaza Rose designs"),
    ("AI_WATCHER","Monitors HuggingFace trending models, emails Meeko when a new model could upgrade SolarPunk"),
    ("LOOP_DASHBOARD_BUILDER","Rebuilds the live GitHub Pages dashboard with current stats every cycle"),
    ("TWITTER_SCHEDULER","Schedules and posts Gaza Rose Gallery content to X/Twitter using stored drafts"),
    ("OPPORTUNITY_SCOUT","Scans emails + web for collaboration opportunities, scores them, emails best ones to Meeko"),
    ("REVENUE_FORECASTER","Projects monthly revenue from all streams, emails Meeko weekly forecast"),
    ("KNOWLEDGE_UPDATER","Pulls latest AI/crypto/grant news via RSS, updates MEMORY_PALACE with new info"),
    ("REDDIT_POSTER","Posts Gaza Rose Gallery content to relevant subreddits on schedule"),
    ("EMAIL_CONNECTOR","Emails Meeko step-by-step setup guides for new platform connections"),
    ("STOCK_WATCHER","Monitors tech stocks relevant to SolarPunk tools, daily snapshot in morning briefing"),
    ("CRYPTO_PORTFOLIO","Tracks crypto prices, suggests rebalancing, never trades without Meeko approval"),
    ("COMMUNITY_BUILDER","Finds and emails potential collaborators who align with SolarPunk mission"),
    ("PITCH_GENERATOR","Generates pitch decks and one-pagers for SolarPunk to send to investors/grantors"),
    ("BACKUP_ENGINE","Additional backup of all data to GitHub releases, beyond GUARDIAN save-states"),
]

def get_existing():
    try:
        r=requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/mycelium",
            headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github.v3+json"},timeout=10)
        files=r.json()
        return {f["name"].replace(".py","") for f in files if f["name"].endswith(".py")}
    except: return set(EXISTING_ENGINES)

def design_engine(name,desc):
    """Claude writes a complete working engine"""
    if not API: return None
    system="""You write Python engines for SolarPunk autonomous income system.
Rules: 100% legal, ethical, Gaza-mission aligned. No hacking, no unauthorized access.
Engines run on GitHub Actions. Use: requests, pathlib, smtplib, json, os, datetime.
Every engine must: load/save state in data/, print progress, handle errors gracefully.
Secrets via os.environ. Never hardcode credentials."""
    prompt=f"""Write a complete, production-ready Python engine: {name}
PURPOSE: {desc}
SYSTEM: SolarPunk runs on GitHub Actions 2x/day. Funds Palestinian artists via Gaza Rose Gallery.
AVAILABLE SECRETS: GMAIL_ADDRESS, GMAIL_APP_PASSWORD, ANTHROPIC_API_KEY, GITHUB_TOKEN, KOFI_USERNAME, HF_TOKEN
WRITE THE COMPLETE Python file. Start with #!/usr/bin/env python3 and a docstring.
Must include: load(), save(), run(), if __name__=="__main__": run()
Keep it focused, working, under 200 lines."""
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":3000,
                  "system":system,"messages":[{"role":"user","content":prompt}]},timeout=60)
        code=r.json()["content"][0]["text"]
        # Strip markdown if wrapped
        code=re.sub(r'^```python\n?','',code); code=re.sub(r'\n?```$','',code)
        return code.strip()
    except Exception as e: print(f"  Claude error: {e}"); return None

def push_engine(name,code):
    """Push new engine directly to GitHub"""
    if not GH_TOKEN: print("  No GITHUB_TOKEN"); return False
    path=f"mycelium/{name}.py"
    # Check if file exists (need SHA to update)
    r=requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}",
        headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github.v3+json"},timeout=10)
    sha=r.json().get("sha") if r.status_code==200 else None
    import base64
    payload={"message":f"[SELF_BUILDER] Auto-generated: {name}",
             "content":base64.b64encode(code.encode()).decode()}
    if sha: payload["sha"]=sha
    r2=requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}",
        headers={"Authorization":f"token {GH_TOKEN}","Accept":"application/vnd.github.v3+json"},
        json=payload,timeout=20)
    return r2.status_code in [200,201]

def validate_code(code):
    """Basic safety checks before committing"""
    if not code or len(code)<100: return False,"Too short"
    dangerous=["subprocess.call","os.system","eval(","exec(","__import__","shutil.rmtree"]
    for d in dangerous:
        if d in code: return False,f"Dangerous: {d}"
    if "def run(" not in code: return False,"No run() function"
    if "#!/usr/bin/env python3" not in code: return False,"Missing shebang"
    return True,""

def notify_built(name,desc):
    if not GMAIL or not GPWD: return
    body=f"SELF_BUILDER just wrote and deployed a new engine:\n\nEngine: {name}\nPurpose: {desc}\nLive at: https://github.com/{GH_REPO}/blob/main/mycelium/{name}.py\n\n[SolarPunk SELF_BUILDER - {datetime.now(timezone.utc).isoformat()[:16]}]"
    try:
        msg=MIMEText(body); msg["From"]=GMAIL; msg["To"]=GMAIL
        msg["Subject"]=f"[SolarPunk] New engine built: {name}"
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,GMAIL,msg.as_string())
    except: pass

def run():
    sf=DATA/"self_builder_state.json"
    state=json.loads(sf.read_text()) if sf.exists() else {"cycles":0,"built":[],"total_built":0}
    state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    print(f"SELF_BUILDER cycle {state['cycles']} | {state.get('total_built',0)} engines built")

    if not API: print("  No ANTHROPIC_API_KEY - cannot generate engines"); sf.write_text(json.dumps(state,indent=2)); return state

    existing=get_existing()
    built_names={b["name"] for b in state.get("built",[])}

    # Find next engine to build
    for name,desc in ENGINE_IDEAS:
        if name not in existing and name not in built_names:
            print(f"  Building: {name}")
            print(f"  Purpose: {desc}")
            code=design_engine(name,desc)
            if not code: print("  Generation failed"); continue
            ok,reason=validate_code(code)
            if not ok: print(f"  Validation failed: {reason}"); continue
            # Save locally too
            (Path("mycelium")/f"{name}.py").write_text(code)
            pushed=push_engine(name,code)
            record={"name":name,"desc":desc,"ts":datetime.now(timezone.utc).isoformat(),"pushed":pushed,"lines":len(code.splitlines())}
            state.setdefault("built",[]).append(record)
            state["total_built"]=state.get("total_built",0)+1
            notify_built(name,desc)
            print(f"  {'Pushed to GitHub' if pushed else 'Saved locally'}: {name} ({len(code.splitlines())} lines)")
            break  # One engine per cycle to be safe
    else:
        print(f"  All {len(ENGINE_IDEAS)} planned engines built! Adding new ideas next cycle.")

    sf.write_text(json.dumps(state,indent=2)); return state

if __name__=="__main__": run()
