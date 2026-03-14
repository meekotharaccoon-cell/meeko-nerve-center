# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""CRYPTO_WATCHER — Market intelligence, never trades without approval
- Monitors BTC, ETH, SOL, relevant AI tokens (FET, OCEAN, AGIX) via free APIs
- Detects significant moves (>5% in 24h)
- Emails Meeko trade PROPOSALS with full reasoning — she clicks yes or no
- Tracks portfolio value if she shares holdings
- Never executes a trade. Never. Meeko approves every single one.
- Also monitors AI token projects relevant to SolarPunk
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

# Tokens relevant to SolarPunk ecosystem
WATCHLIST={
    "bitcoin":"BTC — store of value, main reference",
    "ethereum":"ETH — smart contracts, NFT ecosystem",
    "solana":"SOL — fast/cheap, good for micro-payments",
    "fetch-ai":"FET — autonomous AI agents (directly aligned with SolarPunk)",
    "ocean-protocol":"OCEAN — data marketplace AI token",
    "singularitynet":"AGIX — AGI/AI infrastructure",
    "render-token":"RNDR — GPU compute for AI art (relevant to ART_GENERATOR)",
    "filecoin":"FIL — decentralized storage for SolarPunk data",
}

def load():
    f=DATA/"crypto_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles":0,"prices_history":[],"alerts_sent":[],"portfolio":{},"total_proposals":0}

def save(s):
    s["prices_history"]=s.get("prices_history",[])[-50:]
    s["alerts_sent"]=s.get("alerts_sent",[])[-100:]
    (DATA/"crypto_state.json").write_text(json.dumps(s,indent=2))

def fetch_prices():
    ids=",".join(WATCHLIST.keys())
    try:
        r=requests.get(
            f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true",
            timeout=15,headers={"accept":"application/json"})
        return r.json()
    except Exception as e:
        print(f"  CoinGecko error: {e}")
        return {}

def fetch_fear_greed():
    try:
        r=requests.get("https://api.alternative.me/fng/?limit=1",timeout=10)
        d=r.json()["data"][0]
        return {"value":int(d["value"]),"label":d["value_classification"]}
    except: return {"value":50,"label":"Neutral"}

def analyze_opportunity(prices,fg):
    if not API or not prices: return None
    price_summary="\n".join([f"  {k.upper()}: ${v.get('usd',0):,.2f} ({v.get('usd_24h_change',0):+.1f}% 24h)" for k,v in prices.items()])
    prompt=f"""Analyze crypto market for SolarPunk. Context: small creator, needs revenue, funds Palestinian artists.
PRICES:
{price_summary}
FEAR & GREED: {fg['value']}/100 ({fg['label']})
SOLARPUNK CONTEXT: Autonomous income system. Has small budget for crypto. Prioritizes stable + AI-aligned tokens.
Analyze: any significant opportunities or risks? What AI-aligned tokens (FET, OCEAN, AGIX, RNDR) look interesting?
ONLY JSON: {{"signal":"buy/sell/hold/watch","token":"BTC/ETH/etc","reasoning":"2 sentences","risk":"low/medium/high","action_needed":false,"urgency":"low/medium/high"}}
Set action_needed=true only if genuinely significant move (>10% or major event)."""
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":300,"messages":[{"role":"user","content":prompt}]},timeout=20)
        t=r.json()["content"][0]["text"]; s,e=t.find("{"),t.rfind("}")+1
        return json.loads(t[s:e])
    except: return None

def build_market_summary(prices,fg,analysis,state):
    lines=[]
    for coin_id,(price_data) in prices.items():
        usd=price_data.get("usd",0); chg=price_data.get("usd_24h_change",0)
        desc=WATCHLIST.get(coin_id,"")
        arrow="📈" if chg>2 else ("📉" if chg<-2 else "➡️")
        lines.append(f"  {arrow} {coin_id.upper()[:6]:6} ${usd:>10,.2f}  {chg:+6.1f}%  — {desc}")
    
    alert_section=""
    if analysis and analysis.get("action_needed"):
        alert_section=f"""
⚡ SIGNAL DETECTED: {analysis.get('signal','').upper()} {analysis.get('token','')}
Reasoning: {analysis.get('reasoning','')}
Risk: {analysis.get('risk','')} | Urgency: {analysis.get('urgency','')}
>>> REQUIRES YOUR APPROVAL — SolarPunk will NOT trade without your explicit OK <<<"""

    portfolio_section=""
    if state.get("portfolio"):
        total=sum(state["portfolio"].get(c,0)*prices.get(c,{}).get("usd",0) for c in state["portfolio"])
        portfolio_section=f"\nYOUR PORTFOLIO VALUE: ~${total:,.2f}"

    return "\n".join(lines)+alert_section+portfolio_section

def send_alert(subject,body):
    if not GMAIL or not GPWD: return False
    try:
        msg=MIMEMultipart(); msg["From"]=GMAIL; msg["To"]=GMAIL; msg["Subject"]=subject
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,GMAIL,msg.as_string())
        return True
    except Exception as e: print(f"  alert: {e}"); return False

def check_big_moves(prices,state):
    """Alert on moves >8% that weren't already alerted"""
    alerted={a["coin"] for a in state.get("alerts_sent",[]) if
             (datetime.now(timezone.utc)-datetime.fromisoformat(a["ts"])).total_seconds()<86400}
    for coin,data in prices.items():
        chg=abs(data.get("usd_24h_change",0))
        if chg>8 and coin not in alerted:
            direction="UP" if data.get("usd_24h_change",0)>0 else "DOWN"
            body=(f"CRYPTO ALERT: {coin.upper()} moved {direction} {chg:.1f}% in 24h\n\n"
                f"Current price: ${data.get('usd',0):,.2f}\n"
                f"Context: {WATCHLIST.get(coin,'')}\n\n"
                f"This is INFORMATION ONLY. SolarPunk never trades without your approval.\n"
                f"Reply to this email with 'YES BUY [amount]' or 'YES SELL [amount]' if you want action.\n\n"
                f"[SolarPunk CRYPTO_WATCHER — {datetime.now(timezone.utc).isoformat()[:16]}]")
            ok=send_alert(f"[SolarPunk] CRYPTO ALERT: {coin.upper()} {direction} {chg:.0f}%",body)
            if ok:
                state.setdefault("alerts_sent",[]).append({"coin":coin,"ts":datetime.now(timezone.utc).isoformat(),"chg":chg})
                print(f"  Alert sent: {coin.upper()} {direction} {chg:.1f}%")

def run():
    state=load(); state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    print(f"CRYPTO_WATCHER cycle {state['cycles']}")
    prices=fetch_prices(); fg=fetch_fear_greed()
    if not prices: print("  No price data"); save(state); return state

    # Log prices
    snapshot={"ts":datetime.now(timezone.utc).isoformat(),"fg":fg["value"]}
    for coin,data in prices.items():
        snapshot[coin]={"usd":data.get("usd",0),"chg":data.get("usd_24h_change",0)}
    state.setdefault("prices_history",[]).append(snapshot)

    # Build summary for briefing
    analysis=analyze_opportunity(prices,fg)
    summary=build_market_summary(prices,fg,analysis,state)
    (DATA/"crypto_summary.txt").write_text(summary)
    print(f"  Market updated | Fear&Greed: {fg['value']} ({fg['label']})")
    print(f"  BTC: ${prices.get('bitcoin',{}).get('usd',0):,.0f} | ETH: ${prices.get('ethereum',{}).get('usd',0):,.0f}")

    # Check for big moves -> alert
    check_big_moves(prices,state)

    # AI token spotlight
    ai_tokens={k:v for k,v in prices.items() if k in ["fetch-ai","singularitynet","ocean-protocol","render-token"]}
    if ai_tokens:
        best=max(ai_tokens.items(),key=lambda x:x[1].get("usd_24h_change",0))
        print(f"  AI tokens spotlight: {best[0].upper()} {best[1].get('usd_24h_change',0):+.1f}%")

    save(state); return state

if __name__=="__main__": run()
