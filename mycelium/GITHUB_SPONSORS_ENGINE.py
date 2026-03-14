# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""GITHUB_SPONSORS_ENGINE — Manages GitHub Sponsors tier pages + thank-yous
Generates FUNDING.yml, sponsor landing page, sends thank-you emails to new sponsors.
Revenue: 0% fee after $2k/mo threshold.
"""
import os,json,smtplib
from pathlib import Path
from datetime import datetime,timezone
from email.mime.text import MIMEText

DATA=Path("data"); DATA.mkdir(exist_ok=True)
GMAIL=os.environ.get("GMAIL_ADDRESS","")
GPWD=os.environ.get("GMAIL_APP_PASSWORD","")

TIERS=[
    {"name":"Mycelium","amount":1,"desc":"You keep the loop running. 70c goes to Gaza artists.","perks":["Monthly Gaza Rose art drop","SolarPunk Build Log newsletter"]},
    {"name":"Nerve Cell","amount":5,"desc":"You fund 5 loops. Real impact.","perks":["Everything above","Your name in the monthly digest","Early access to new engines"]},
    {"name":"Cortex","amount":20,"desc":"You power 20 art cycles. Significant.","perks":["Everything above","Monthly SolarPunk status call (email Q&A)","Co-design one future engine"]},
    {"name":"Architect","amount":50,"desc":"You help architect the infrastructure.","perks":["Everything above","Direct line to Meeko","Help shape SolarPunk roadmap","Recognition in README"]},
]

def load():
    f=DATA/"sponsors_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles":0,"sponsors":[],"total_monthly":0.0,"thank_you_sent":[]}

def save(s):
    (DATA/"sponsors_state.json").write_text(json.dumps(s,indent=2))

def generate_funding_yml():
    Path(".github").mkdir(exist_ok=True)
    yml="""github: [meekotharaccoon-cell]
ko_fi: meekotharaccoon
custom: ['https://gumroad.com/meekotharaccoon']
"""
    (Path(".github")/"FUNDING.yml").write_text(yml)
    print("  FUNDING.yml updated")

def generate_sponsor_page(state):
    total=state.get("total_monthly",0); count=len(state.get("sponsors",[]))
    tier_html="".join([f"""<div class="tier">
<div class="amount">${t['amount']}/mo</div>
<div class="name">{t['name']}</div>
<p>{t['desc']}</p>
<ul>{''.join(f'<li>{p}</li>' for p in t['perks'])}</ul>
<a href="https://github.com/sponsors/meekotharaccoon-cell" class="btn">Become a {t['name']}</a>
</div>""" for t in TIERS])
    html=f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Sponsor SolarPunk</title>
<style>body{{font-family:sans-serif;background:#0a0a0a;color:#e8e8e8;margin:0;padding:20px;max-width:900px;margin:auto}}
h1{{color:#c8a86b;text-align:center}}p.sub{{text-align:center;color:#888}}
.stats{{display:flex;justify-content:center;gap:40px;margin:20px 0;text-align:center}}
.stat-n{{font-size:32px;color:#c8a86b;font-weight:bold}}.stat-l{{font-size:12px;color:#666}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;margin:20px 0}}
.tier{{background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:20px;text-align:center}}
.amount{{font-size:28px;color:#c8a86b;font-weight:bold}}.name{{color:#aaa;margin:4px 0 12px}}
.tier p{{font-size:13px;color:#999;margin:0 0 12px}}
.tier ul{{text-align:left;font-size:12px;color:#888;padding-left:16px;margin:0 0 16px}}
.btn{{display:inline-block;background:#c8a86b;color:#0a0a0a;padding:8px 16px;border-radius:4px;text-decoration:none;font-weight:bold;font-size:13px}}
</style></head>
<body><h1>Sponsor SolarPunk</h1>
<p class="sub">Fund autonomous AI income for Palestinian artists. Every dollar matters.</p>
<div class="stats">
<div><div class="stat-n">${total:.0f}</div><div class="stat-l">monthly sponsors</div></div>
<div><div class="stat-n">{count}</div><div class="stat-l">supporters</div></div>
<div><div class="stat-n">0%</div><div class="stat-l">platform fee</div></div>
</div>
<div class="grid">{tier_html}</div>
<p style="text-align:center;color:#666;font-size:13px">
GitHub: <a href="https://github.com/meekotharaccoon-cell/meeko-nerve-center" style="color:#c8a86b">meeko-nerve-center</a> |
Ko-fi: <a href="https://ko-fi.com/meekotharaccoon" style="color:#c8a86b">ko-fi.com/meekotharaccoon</a>
</p></body></html>"""
    Path("docs").mkdir(exist_ok=True)
    (Path("docs")/"sponsor.html").write_text(html)
    print("  Sponsor page updated")

def thank_new_sponsors(state):
    inbox=DATA/"sponsors_inbox.json"
    if not inbox.exists(): return
    try: new_sponsors=json.loads(inbox.read_text())
    except: return
    sent={s for s in state.get("thank_you_sent",[])}
    for sponsor in new_sponsors:
        sid=sponsor.get("login","")
        if sid in sent: continue
        tier=next((t for t in TIERS if t["amount"]==sponsor.get("amount",1)),TIERS[0])
        if GMAIL and GPWD and sponsor.get("email"):
            body=(f"Thank you for sponsoring SolarPunk at the {tier['name']} tier!\n\n"
                f"Your ${tier['amount']}/mo directly funds Palestinian artists via Gaza Rose Gallery.\n"
                f"70% of every Ko-fi sale goes straight to Gaza artists.\n\n"
                f"What you get: {', '.join(tier['perks'])}\n\n"
                f"GitHub: https://github.com/meekotharaccoon-cell/meeko-nerve-center\n"
                f"Ko-fi: https://ko-fi.com/meekotharaccoon\n\n"
                f"— Meeko + SolarPunk")
            try:
                msg=MIMEText(body); msg["From"]=GMAIL; msg["To"]=sponsor["email"]
                msg["Subject"]=f"Thank you, {sid}! SolarPunk + Gaza Rose Gallery"
                with smtplib.SMTP("smtp.gmail.com",587) as s:
                    s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,sponsor["email"],msg.as_string())
                state.setdefault("thank_you_sent",[]).append(sid)
                state["sponsors"].append(sponsor)
                state["total_monthly"]=sum(s.get("amount",0) for s in state["sponsors"])
                print(f"  Thank-you sent: {sid}")
            except Exception as e: print(f"  Thank-you failed: {e}")

def run():
    state=load(); state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    print(f"GITHUB_SPONSORS cycle {state['cycles']} | ${state.get('total_monthly',0):.2f}/mo")
    generate_funding_yml()
    generate_sponsor_page(state)
    thank_new_sponsors(state)
    save(state); return state

if __name__=="__main__": run()
