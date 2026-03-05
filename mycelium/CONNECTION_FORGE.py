#!/usr/bin/env python3
"""CONNECTION_FORGE — SolarPunk emails itself setup guides
Every cycle: finds unconnected platforms, emails Meeko step-by-step wiring instructions.
SolarPunk guides itself to new connections via email.
THIS is how the system expands without the chat interface.
"""
import os,json,smtplib,requests
from pathlib import Path
from datetime import datetime,timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA=Path("data"); DATA.mkdir(exist_ok=True)
GMAIL=os.environ.get("GMAIL_ADDRESS","")
GPWD=os.environ.get("GMAIL_APP_PASSWORD","")
API=os.environ.get("ANTHROPIC_API_KEY","")
GH_REPO="meekotharaccoon-cell/meeko-nerve-center"
GH_SECRETS_URL=f"https://github.com/{GH_REPO}/settings/secrets/actions"

# Every platform SolarPunk can connect to + what it unlocks
CONNECTIONS=[
    {
        "name":"Redbubble",
        "value":"passive income from art prints, stickers, shirts — zero fulfillment",
        "revenue":"$5-80/mo","effort":"30 min setup",
        "steps":[
            "Go to redbubble.com -> Sign up or login",
            "Create artist account: MeekoThaRaccoon",
            "Upload Gaza Rose art (from data/art_orders.json fulfilled images)",
            "Set prices: base + 20% markup",
            "Add to bio: 'Gaza Rose Gallery — $1 AI art funds Palestinian artists'",
            "Copy your Redbubble profile URL",
            "Email it to yourself — REDBUBBLE_ENGINE will track it automatically"
        ],
        "secret_needed":None
    },
    {
        "name":"Etsy",
        "value":"marketplace for digital downloads — Gaza Rose prints as instant downloads",
        "revenue":"$10-150/mo","effort":"1 hour setup",
        "steps":[
            "Go to etsy.com/sell -> Open a shop",
            "Shop name: GazaRoseGallery",
            "Create listing: '$1 Gaza Rose Digital Print — Instant Download'",
            "Upload art from ART_GENERATOR output",
            "Price: $1.00, category: Digital Downloads",
            "Get your Etsy API key: etsy.com/developers/register",
            f"Add to GitHub Secrets ({GH_SECRETS_URL}): ETSY_API_KEY=your_key",
            "ETSY_SEO_ENGINE will auto-optimize your listings"
        ],
        "secret_needed":"ETSY_API_KEY"
    },
    {
        "name":"Gumroad",
        "value":"direct digital sales, 0% fee on free plan",
        "revenue":"$5-50/mo","effort":"20 min",
        "steps":[
            "Go to gumroad.com -> Sign up",
            "Create product: 'Gaza Rose AI Art Bundle' — $1",
            "Upload 12 Gaza Rose images as ZIP",
            "Get API token: app.gumroad.com/settings/advanced -> API",
            f"Add to GitHub Secrets ({GH_SECRETS_URL}): GUMROAD_ACCESS_TOKEN=your_token",
            "GUMROAD_ENGINE will manage listings automatically"
        ],
        "secret_needed":"GUMROAD_ACCESS_TOKEN"
    },
    {
        "name":"Ko-fi Webhooks via Pipedream",
        "value":"receive real payment notifications when someone buys",
        "revenue":"unlocks full $1 art loop","effort":"15 min",
        "steps":[
            "Go to pipedream.com -> Sign up free",
            "New workflow -> HTTP trigger -> copy webhook URL",
            "Go to ko-fi.com -> Settings -> API -> paste webhook URL",
            "Add filter in Pipedream: write event data to GitHub file via API",
            "Test: buy your own $1 art -> KOFI_ENGINE auto-processes it",
            f"Confirm Ko-fi username in Secrets ({GH_SECRETS_URL}): KOFI_USERNAME=meekotharaccoon"
        ],
        "secret_needed":"KOFI_USERNAME"
    },
    {
        "name":"Substack",
        "value":"newsletter monetization — paid subscriptions for SolarPunk Build Log",
        "revenue":"$35-175/mo","effort":"30 min",
        "steps":[
            "Go to substack.com -> Start a publication",
            "Name: 'SolarPunk Build Log'",
            "Description: 'An AI building its own income to fund Palestinian artists. Live.'",
            "Enable paid subscriptions: $5/mo or $50/yr",
            "First issue: data/substack_draft.txt is ready to paste and publish",
            "Enable email-to-post in Settings -> Publishing",
            f"Add Substack email address to Secrets: SUBSTACK_EMAIL=publish@yourpub.substack.com"
        ],
        "secret_needed":"SUBSTACK_EMAIL"
    },
    {
        "name":"HuggingFace Spaces (public demo)",
        "value":"public-facing SolarPunk demo, drives traffic and trust",
        "revenue":"indirect — builds audience","effort":"45 min",
        "steps":[
            "Go to huggingface.co -> New Space",
            "Name: solarpunk-gaza-rose",
            "Framework: Gradio",
            "Upload a simple demo: generate Gaza Rose art on demand",
            "Link from your GitHub README",
            f"Confirm HF_TOKEN in Secrets ({GH_SECRETS_URL})"
        ],
        "secret_needed":"HF_TOKEN"
    },
    {
        "name":"OpenCollective",
        "value":"accept donations with full transparency — ideal for humanitarian mission",
        "revenue":"$20-200/mo","effort":"30 min",
        "steps":[
            "Go to opencollective.com -> Create Collective",
            "Name: SolarPunk Gaza Rose Fund",
            "Category: Open Source, Humanitarian",
            "Connect your bank account or PayPal",
            "Set goal: $500/mo for artist fund",
            "Share link in morning briefing email"
        ],
        "secret_needed":None
    },
    {
        "name":"GitHub Sponsors",
        "value":"recurring monthly income, 0% fee after $2k/mo",
        "revenue":"$10-145/mo","effort":"10 min (approval pending)",
        "steps":[
            "Go to github.com/sponsors/meekotharaccoon-cell",
            "Check approval status (takes 1-3 weeks)",
            "Once approved: tiers are already configured by GITHUB_SPONSORS_ENGINE",
            "Share sponsor button in all emails and README",
            ".github/FUNDING.yml already set up"
        ],
        "secret_needed":None
    },
    {
        "name":"Stripe (payment processing)",
        "value":"direct card payments for any SolarPunk product",
        "revenue":"unlocks direct checkout","effort":"30 min",
        "steps":[
            "Go to stripe.com -> Create account",
            "Get API keys: dashboard.stripe.com/apikeys",
            f"Add to GitHub Secrets ({GH_SECRETS_URL}): STRIPE_SECRET_KEY=sk_live_...",
            "SolarPunk can then create payment links programmatically",
            "Each Gaza Rose sale can have its own Stripe link"
        ],
        "secret_needed":"STRIPE_SECRET_KEY"
    },
    {
        "name":"Twitter/X API (full posting)",
        "value":"autonomous social promotion of Gaza Rose Gallery",
        "revenue":"drives traffic -> sales","effort":"already connected",
        "steps":[
            "Keys already in GitHub Secrets (X_API_KEY etc)",
            "SOCIAL_PROMOTER posts automatically",
            "Check: github.com actions logs to confirm posts going through"
        ],
        "secret_needed":None
    },
]

def load():
    f=DATA/"connection_forge_state.json"
    if f.exists():
        try: return json.loads(f.read_text())
        except: pass
    return {"cycles":0,"guides_sent":[],"connections_active":[]}

def save(s):
    (DATA/"connection_forge_state.json").write_text(json.dumps(s,indent=2))

def check_active_secrets():
    """Guess which connections are active based on env vars"""
    active=[]
    if os.environ.get("GMAIL_ADDRESS"): active.append("Gmail")
    if os.environ.get("GUMROAD_ACCESS_TOKEN"): active.append("Gumroad")
    if os.environ.get("HF_TOKEN"): active.append("HuggingFace")
    if os.environ.get("X_API_KEY"): active.append("Twitter/X")
    if os.environ.get("REDDIT_CLIENT_ID"): active.append("Reddit")
    if os.environ.get("KOFI_USERNAME"): active.append("Ko-fi")
    return active

def build_setup_email(conn,active):
    """Craft a clear setup guide email for one connection"""
    steps_txt="\n".join([f"  {i+1}. {s}" for i,s in enumerate(conn["steps"])])
    secret_note=f"\nSECRET NEEDED: Add '{conn['secret_needed']}' to GitHub Secrets\n{GH_SECRETS_URL}\n" if conn.get("secret_needed") else "\nNo GitHub Secret needed for this one.\n"
    return f"""SolarPunk is ready to connect to {conn['name']}.

WHY: {conn['value']}
REVENUE POTENTIAL: {conn['revenue']}
YOUR TIME: {conn['effort']}

SETUP STEPS:
{steps_txt}
{secret_note}
Once connected, SolarPunk handles everything else automatically.
Active connections so far: {', '.join(active)}

[SolarPunk CONNECTION_FORGE — building bridges autonomously]
[GitHub: https://github.com/{GH_REPO}]"""

def send_setup_email(conn,body):
    if not GMAIL or not GPWD: print(f"  [FORGE] Would email: {conn['name']} setup guide"); return False
    try:
        msg=MIMEMultipart()
        msg["From"]=GMAIL; msg["To"]=GMAIL
        msg["Subject"]=f"[SolarPunk] Connect to {conn['name']} — {conn['revenue']} potential"
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls(); s.login(GMAIL,GPWD); s.sendmail(GMAIL,GMAIL,msg.as_string())
        return True
    except Exception as e: print(f"  email error: {e}"); return False

def run():
    state=load(); state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    print(f"CONNECTION_FORGE cycle {state['cycles']}")
    active=check_active_secrets()
    state["connections_active"]=active
    print(f"  Active connections: {', '.join(active)}")
    sent_names=set(state.get("guides_sent",[]))
    # Send 1 setup guide per cycle (don't spam)
    for conn in CONNECTIONS:
        if conn["name"] not in sent_names and conn["name"] not in active:
            body=build_setup_email(conn,active)
            ok=send_setup_email(conn,body)
            if ok or not GMAIL:
                state.setdefault("guides_sent",[]).append(conn["name"])
                print(f"  Setup guide {'sent' if ok else 'logged'}: {conn['name']} ({conn['revenue']})")
            break
    else:
        print(f"  All {len(CONNECTIONS)} connection guides sent!")
    save(state); return state

if __name__=="__main__": run()
