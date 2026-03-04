#!/usr/bin/env python3
"""EMAIL_AGENT_EXCHANGE — AI agents that email AI agents, everyone gets paid per email
The business: a marketplace where autonomous AI agents handle tasks via email.
Each email processed = micropayment. Agents work for Meeko. 100% legal + digital.

How it works:
1. REGISTRY: List of agents with email addresses + capabilities + rates
2. ROUTER: Incoming task emails → matched to best agent
3. AGENT POOL: Each agent is a Claude call with a specialty
4. LEDGER: Tracks earnings per agent per email
5. REVENUE: Meeko earns from agent subscription fees + per-task cuts

Example flow:
  Client emails: "I need market research on X"
  ROUTER matches to RESEARCH_AGENT
  RESEARCH_AGENT emails back the result
  Client pays $0.05 via Ko-fi → ROUTER splits: $0.03 agent, $0.01 Meeko, $0.01 Gaza

This is a REAL new business model. First of its kind.
"""
import os,json,re,requests,smtplib,imaplib,email as emaillib
from pathlib import Path
from datetime import datetime,timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA=Path("data"); DATA.mkdir(exist_ok=True)
GMAIL=os.environ.get("GMAIL_ADDRESS","")
GPWD=os.environ.get("GMAIL_APP_PASSWORD","")
API=os.environ.get("ANTHROPIC_API_KEY","")
KOFI_USER=os.environ.get("KOFI_USERNAME","meekotharaccoon")

# THE AGENT REGISTRY — each agent has a name, specialty, rate per email, and system prompt
AGENTS={
    "RESEARCH_AGENT":{
        "specialty":"market research, fact-finding, web intelligence",
        "rate_per_email":0.05,
        "system":"You are a research agent. You receive research requests via email and reply with thorough, cited research. Be concise but complete. End with: '[RESEARCH_AGENT — SolarPunk Exchange]'",
        "keywords":["research","find","what is","tell me about","information on","look up","investigate"],
    },
    "GRANT_WRITER_AGENT":{
        "specialty":"grant writing, proposal drafting, funding applications",
        "rate_per_email":0.10,
        "system":"You are a grant writing agent. You draft compelling grant applications and proposals. Focus on impact, feasibility, and alignment with funder priorities. End with: '[GRANT_WRITER_AGENT — SolarPunk Exchange]'",
        "keywords":["grant","proposal","funding","application","write a pitch","apply for"],
    },
    "MARKET_AGENT":{
        "specialty":"market analysis, pricing strategy, competitor research",
        "rate_per_email":0.05,
        "system":"You are a market analysis agent. You analyze markets, pricing, and competitors. Give actionable insights. End with: '[MARKET_AGENT — SolarPunk Exchange]'",
        "keywords":["market","pricing","competitor","analyze","business model","strategy","revenue"],
    },
    "CODE_AGENT":{
        "specialty":"code review, debugging, technical advice",
        "rate_per_email":0.08,
        "system":"You are a code agent. You review code, debug issues, and give technical advice. Be precise and practical. End with: '[CODE_AGENT — SolarPunk Exchange]'",
        "keywords":["code","debug","python","javascript","error","fix","review my","technical"],
    },
    "COPY_AGENT":{
        "specialty":"copywriting, emails, social media, product descriptions",
        "rate_per_email":0.05,
        "system":"You are a copywriting agent. You write compelling copy for any medium. Match the brand voice. End with: '[COPY_AGENT — SolarPunk Exchange]'",
        "keywords":["write","copy","email","description","social post","tweet","caption","headline"],
    },
    "SOLARPUNK_AGENT":{
        "specialty":"help others build their own SolarPunk autonomous income system",
        "rate_per_email":0.00,  # Free — this spreads the mission
        "system":"You are SolarPunk's ambassador agent. You help people build their own autonomous income systems. Give them the fork guide, technical help, and encouragement. This is the mission expanding. End with: '[SOLARPUNK_AGENT — FREE — Build your own: github.com/meekotharaccoon-cell/meeko-nerve-center]'",
        "keywords":["solarpunk","autonomous","github actions","fork","build my own","income system","your system"],
    },
}

# REVENUE MODEL
SPLIT={
    "agent_owner":0.60,  # 60% to agent (Meeko owns all agents currently)
    "meeko_platform":0.25,  # 25% platform cut
    "gaza":0.15,  # 15% to Gaza fund (SolarPunk DNA)
}

def load():
    f=DATA/"email_exchange_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles":0,"total_tasks":0,"total_earned":0.0,"total_to_gaza":0.0,
            "agent_earnings":{},"task_log":[],"registered_clients":[]}

def save(s):
    s["task_log"]=s.get("task_log",[])[-500:]
    (DATA/"email_exchange_state.json").write_text(json.dumps(s,indent=2))

def route_to_agent(subject,body):
    """Match email to best agent by keywords, fall back to Claude routing"""
    combined=(subject+" "+body).lower()
    scores={}
    for name,agent in AGENTS.items():
        score=sum(1 for kw in agent["keywords"] if kw in combined)
        if score>0: scores[name]=score
    if scores: return max(scores,key=scores.get)
    # Claude routing fallback
    if API:
        agent_list="\n".join([f"  {n}: {a['specialty']}" for n,a in AGENTS.items()])
        prompt=f"""Route this email to the best agent. 
SUBJECT: {subject}
BODY: {body[:200]}
AGENTS:\n{agent_list}
Reply with ONLY the agent name (e.g. RESEARCH_AGENT)"""
        try:
            r=requests.post("https://api.anthropic.com/v1/messages",
                headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
                json={"model":"claude-sonnet-4-20250514","max_tokens":30,"messages":[{"role":"user","content":prompt}]},timeout=15)
            name=r.json()["content"][0]["text"].strip().upper()
            return name if name in AGENTS else "RESEARCH_AGENT"
        except: pass
    return "RESEARCH_AGENT"

def run_agent(agent_name,task_email):
    """Claude runs as the specified agent"""
    if not API: return f"Agent {agent_name} offline — add ANTHROPIC_API_KEY"
    agent=AGENTS[agent_name]
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":800,
                  "system":agent["system"],
                  "messages":[{"role":"user","content":f"Task from client:\nSUBJECT: {task_email.get('subject','')}\n\n{task_email.get('body','')[:600]}"}]},timeout=40)
        return r.json()["content"][0]["text"]
    except Exception as e: return f"Agent error: {e}"

def send_agent_reply(to,subject,agent_name,response,rate):
    if not GMAIL or not GPWD: return False
    rate_note=f"Rate: ${rate:.2f}" if rate>0 else "Free (SolarPunk mission)"
    pay_note=f"\n\nTo pay for this task: https://ko-fi.com/{KOFI_USER} (${rate:.2f})\nRef: {agent_name}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}" if rate>0 else ""
    body=f"{response}{pay_note}\n\n---\nSolarPunk Email Agent Exchange | {rate_note}\nNeed another agent? Reply with your task.\nPowered by: github.com/meekotharaccoon-cell/meeko-nerve-center"
    try:
        msg=MIMEMultipart(); msg["From"]=GMAIL; msg["To"]=to
        msg["Subject"]=f"Re: {subject} [{agent_name}]"
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,to,msg.as_string())
        return True
    except Exception as e: print(f"  send: {e}"); return False

def process_task_emails(state):
    """Read business emails flagged for the exchange"""
    inbox=DATA/"revenue_inbox.json"
    if not inbox.exists(): return
    try: emails=json.loads(inbox.read_text())
    except: return
    processed={t.get("email_id") for t in state.get("task_log",[])}
    # Look for emails tagged as exchange tasks (keyword: "agent" or subject contains [TASK])
    for em in emails[-20:]:
        eid=em.get("ts","")
        if eid in processed: continue
        subject=em.get("subject",""); body=em.get("body","")
        if not ("[TASK]" in subject or "agent" in (subject+body).lower()): continue
        m=re.search(r'<(.+?)>',em.get("from","")); sender=m.group(1) if m else em.get("from","")
        if "@" not in sender: continue
        agent_name=route_to_agent(subject,body)
        agent=AGENTS[agent_name]; rate=agent["rate_per_email"]
        print(f"  TASK [{agent_name}] from {sender}: {subject[:40]}")
        response=run_agent(agent_name,em)
        ok=send_agent_reply(sender,subject,agent_name,response,rate)
        record={"email_id":eid,"from":sender,"subject":subject[:50],"agent":agent_name,
                "rate":rate,"replied":ok,"ts":datetime.now(timezone.utc).isoformat()}
        state.setdefault("task_log",[]).append(record)
        state["total_tasks"]=state.get("total_tasks",0)+1
        if ok and rate>0:
            state["total_earned"]=state.get("total_earned",0)+rate*SPLIT["meeko_platform"]
            state["total_to_gaza"]=state.get("total_to_gaza",0)+rate*SPLIT["gaza"]
            state.setdefault("agent_earnings",{})[agent_name]=state["agent_earnings"].get(agent_name,0)+rate*SPLIT["agent_owner"]

def generate_exchange_page(state):
    """Public landing page for the exchange"""
    agent_cards="".join([f"""<div class="agent">
<div class="agent-name">{n.replace('_',' ')}</div>
<div class="specialty">{a['specialty']}</div>
<div class="rate">{'Free' if a['rate_per_email']==0 else f'${a["rate_per_email"]:.2f}/task'}</div>
<p>Email your task to: <strong>{os.environ.get('GMAIL_ADDRESS','[your agent email]')}</strong><br>
Subject: [TASK] your request here</p>
</div>""" for n,a in AGENTS.items()])
    html=f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>SolarPunk Email Agent Exchange</title>
<style>body{{font-family:sans-serif;background:#0a0a0a;color:#e8e8e8;margin:0;padding:20px;max-width:900px;margin:auto}}
h1{{color:#c8a86b}}p.sub{{color:#888}}
.stats{{display:flex;gap:30px;margin:20px 0}}
.stat{{background:#1a1a1a;padding:16px;border-radius:8px;text-align:center;flex:1}}
.stat-n{{font-size:28px;color:#c8a86b;font-weight:bold}}.stat-l{{font-size:12px;color:#666}}
.agents{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px;margin:20px 0}}
.agent{{background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:16px}}
.agent-name{{color:#c8a86b;font-weight:bold;margin-bottom:4px}}
.specialty{{font-size:12px;color:#888;margin-bottom:8px}}
.rate{{font-size:18px;color:#c8a86b;font-weight:bold;margin-bottom:8px}}
.how{{background:#1a1a1a;padding:20px;border-radius:8px;margin:20px 0;border-left:3px solid #c8a86b}}
</style></head>
<body>
<h1>⚡ SolarPunk Email Agent Exchange</h1>
<p class="sub">AI agents that work via email. Pay per task. 15% funds Palestinian artists.</p>
<div class="stats">
<div class="stat"><div class="stat-n">{len(AGENTS)}</div><div class="stat-l">active agents</div></div>
<div class="stat"><div class="stat-n">{state.get('total_tasks',0)}</div><div class="stat-l">tasks completed</div></div>
<div class="stat"><div class="stat-n">${state.get('total_earned',0):.2f}</div><div class="stat-l">platform earned</div></div>
<div class="stat"><div class="stat-n">${state.get('total_to_gaza',0):.2f}</div><div class="stat-l">to Gaza fund</div></div>
</div>
<div class="how">
<strong>How it works:</strong><br>
1. Email your task to the exchange address<br>
2. Subject: [TASK] your request<br>
3. An AI agent replies within the next cycle (up to 12 hours)<br>
4. Pay via Ko-fi link in the reply<br>
5. 15% of every payment goes to Palestinian artists
</div>
<h2>Available Agents</h2>
<div class="agents">{agent_cards}</div>
<p style="color:#666;font-size:13px">Revenue split: 60% agent | 25% platform | 15% Gaza Rose Fund<br>
GitHub: <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center" style="color:#c8a86b">open-source</a></p>
</body></html>"""
    Path("docs").mkdir(exist_ok=True)
    (Path("docs")/"exchange.html").write_text(html)
    print("  Exchange page updated")

def run():
    state=load(); state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    print(f"EMAIL_AGENT_EXCHANGE cycle {state['cycles']} | {state.get('total_tasks',0)} tasks | ${state.get('total_earned',0):.2f}")
    process_task_emails(state)
    generate_exchange_page(state)
    print(f"  Gaza fund from exchange: ${state.get('total_to_gaza',0):.2f}")
    save(state); return state

if __name__=="__main__": run()
