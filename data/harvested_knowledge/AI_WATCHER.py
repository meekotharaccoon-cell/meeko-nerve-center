#!/usr/bin/env python3
"""AI_WATCHER — Monitors the AI ecosystem for SolarPunk-relevant developments
Tracks: new models on HuggingFace, trending AI repos on GitHub, AI token moves,
AI startup funding, new tools that could upgrade SolarPunk.
Emails Meeko a weekly AI landscape digest.
Self-upgrades: when it finds a better model, proposes the swap.
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
HF_TOKEN=os.environ.get("HF_TOKEN","")
GH_TOKEN=os.environ.get("GITHUB_TOKEN","")

# What SolarPunk currently uses + what could upgrade it
CURRENT_STACK={
    "text_ai":"claude-sonnet-4-20250514",
    "image_ai":"black-forest-labs/FLUX.1-schnell",
    "hosting":"GitHub Actions",
    "storage":"GitHub repo + JSON files",
    "payments":"Ko-fi + Gumroad",
}

WATCH_CATEGORIES=[
    "autonomous-agents","art-generation","text-to-image","income-generation",
    "email-automation","web-scraping","grant-writing","social-media"
]

def load():
    f=DATA/"ai_watcher_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles":0,"last_digest":None,"discoveries":[],"upgrade_proposals":[]}

def save(s):
    s["discoveries"]=s.get("discoveries",[])[-200:]
    (DATA/"ai_watcher_state.json").write_text(json.dumps(s,indent=2))

def fetch_hf_trending():
    """HuggingFace trending models"""
    try:
        headers={"Authorization":f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
        r=requests.get("https://huggingface.co/api/models?sort=likes&direction=-1&limit=20&pipeline_tag=text-to-image",
            headers=headers,timeout=10)
        models=r.json()
        return [{"name":m.get("modelId",""),"likes":m.get("likes",0),"downloads":m.get("downloads",0),"tags":m.get("tags",[])} for m in models[:10]]
    except: return []

def fetch_hf_new_text_models():
    """New text generation models"""
    try:
        headers={"Authorization":f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
        r=requests.get("https://huggingface.co/api/models?sort=lastModified&direction=-1&limit=10&pipeline_tag=text-generation&filter=en",
            headers=headers,timeout=10)
        models=r.json()
        return [{"name":m.get("modelId",""),"likes":m.get("likes",0),"updated":m.get("lastModified","")} for m in models[:5]]
    except: return []

def fetch_trending_ai_repos():
    """GitHub trending AI repos"""
    try:
        headers={"Authorization":f"token {GH_TOKEN}"} if GH_TOKEN else {}
        r=requests.get("https://api.github.com/search/repositories?q=autonomous+agent+ai+income&sort=stars&order=desc&per_page=5",
            headers=headers,timeout=10)
        repos=r.json().get("items",[])
        return [{"name":r.get("full_name",""),"stars":r.get("stargazers_count",0),"desc":r.get("description","")[:80],"url":r.get("html_url","")} for r in repos]
    except: return []

def analyze_discoveries(image_models,text_models,repos):
    if not API: return None
    img_txt="\n".join([f"  {m['name']} ({m['likes']} likes)" for m in image_models[:5]])
    text_txt="\n".join([f"  {m['name']} ({m['likes']} likes)" for m in text_models[:5]])
    repo_txt="\n".join([f"  {r['name']} ({r['stars']} stars): {r['desc']}" for r in repos[:5]])
    prompt=f"""Analyze AI ecosystem for SolarPunk (autonomous income system, GitHub Actions, Claude API, FLUX image gen).
TRENDING IMAGE MODELS:
{img_txt}
NEW TEXT MODELS:
{text_txt}
RELEVANT REPOS:
{repo_txt}
CURRENT STACK: {json.dumps(CURRENT_STACK)}
Questions: What's new worth integrating? Any model better than current? Any repos to fork/learn from?
ONLY JSON: {{"upgrade_opportunity":true/false,"best_new_image_model":"name or null","best_new_text_tool":"name or null","interesting_repos":["repo1","repo2"],"summary":"2 sentences","action":"what SolarPunk should do next"}}"""
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":400,"messages":[{"role":"user","content":prompt}]},timeout=25)
        t=r.json()["content"][0]["text"]; s,e=t.find("{"),t.rfind("}")+1
        return json.loads(t[s:e])
    except: return None

def send_digest(subject,body):
    if not GMAIL or not GPWD: return False
    try:
        msg=MIMEMultipart(); msg["From"]=GMAIL; msg["To"]=GMAIL; msg["Subject"]=subject
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,GMAIL,msg.as_string())
        return True
    except: return False

def should_send_digest(state):
    if not state.get("last_digest"): return True
    last=datetime.fromisoformat(state["last_digest"])
    return (datetime.now(timezone.utc)-last).days>=7

def run():
    state=load(); state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    print(f"AI_WATCHER cycle {state['cycles']}")

    image_models=fetch_hf_trending()
    text_models=fetch_hf_new_text_models()
    repos=fetch_trending_ai_repos()
    print(f"  Found: {len(image_models)} image models, {len(text_models)} text models, {len(repos)} repos")

    analysis=analyze_discoveries(image_models,text_models,repos)

    # Save discoveries
    discovery={"ts":datetime.now(timezone.utc).isoformat(),"image_models":[m["name"] for m in image_models[:3]],
               "text_models":[m["name"] for m in text_models[:3]],"repos":[r["name"] for r in repos[:3]],
               "analysis":analysis}
    state.setdefault("discoveries",[]).append(discovery)

    if analysis and analysis.get("upgrade_opportunity"):
        state.setdefault("upgrade_proposals",[]).append({"ts":datetime.now(timezone.utc).isoformat(),"proposal":analysis})
        print(f"  UPGRADE OPPORTUNITY: {analysis.get('summary','')}")

    # Weekly digest
    if should_send_digest(state):
        img_lines="\n".join([f"  • {m['name']} ({m['likes']:,} likes)" for m in image_models[:8]])
        text_lines="\n".join([f"  • {m['name']} ({m['likes']:,} likes)" for m in text_models[:5]])
        repo_lines="\n".join([f"  • {r['name']} ⭐{r['stars']:,}\n    {r['desc']}\n    {r['url']}" for r in repos[:5]])
        analysis_section=f"""
AI ANALYSIS:
  Summary: {analysis.get('summary','No analysis available')}
  Action: {analysis.get('action','')}
  Upgrade opportunity: {analysis.get('upgrade_opportunity',False)}
  Best new image model: {analysis.get('best_new_image_model','none')}
  Interesting repos: {', '.join(analysis.get('interesting_repos',[]))}""" if analysis else ""

        body=f"""AI ECOSYSTEM WEEKLY DIGEST
SolarPunk AI Intelligence Report — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

CURRENT STACK:
  Text: {CURRENT_STACK['text_ai']}
  Image: {CURRENT_STACK['image_ai']}

TRENDING IMAGE GENERATION MODELS:
{img_lines}

NEW TEXT/LLM MODELS:
{text_lines}

RELEVANT GITHUB REPOS:
{repo_lines}
{analysis_section}

HOW TO UPGRADE:
To swap image model: edit mycelium/ART_GENERATOR.py -> change model name -> commit
To add new text tool: SELF_BUILDER will auto-integrate if you reply 'integrate [model_name]'

[SolarPunk AI_WATCHER — weekly digest — {datetime.now(timezone.utc).isoformat()[:16]}]"""
        ok=send_digest(f"[SolarPunk] AI Weekly: {len(image_models)} new models scouted",body)
        if ok: state["last_digest"]=datetime.now(timezone.utc).isoformat()
        print(f"  Weekly digest {'sent' if ok else 'queued'}")

    save(state); return state

if __name__=="__main__": run()
