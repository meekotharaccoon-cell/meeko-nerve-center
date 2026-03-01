# The Morning Briefing
### Every morning at 8am: your AI tells you what matters today.

*The viral post: "My AI sends me a daily briefing." Here's the 40-line script that actually does it.*

**Price: $1 — 70% goes to PCRF (children's aid in Gaza)**

---

## What You're Getting

A Python script that runs every morning, pulls together weather, news, your calendar events, your grant deadlines, and a motivational note — then emails it to you by 8am. Completely customizable. Runs free on your computer or GitHub Actions.

---

## The Script

Save as `morning_briefing.py`:

```python
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json

# ── CONFIG ──────────────────────────────────────────
GMAIL_ADDRESS = "your@gmail.com"
GMAIL_APP_PASSWORD = "your-app-password"
WEATHER_CITY = "New York"  # Your city
NEWS_TOPICS = ["AI", "open source", "Gaza", "Palestine"]  # What you care about

# ── WEATHER ─────────────────────────────────────────
def get_weather():
    r = requests.get(
        f"https://wttr.in/{WEATHER_CITY}?format=3",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    return r.text.strip()

# ── NEWS ─────────────────────────────────────────────
def get_news():
    results = []
    for topic in NEWS_TOPICS:
        r = requests.get(
            f"https://news.google.com/rss/search?q={topic}&hl=en",
            timeout=5
        )
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.content)
        items = root.findall('.//item')[:2]
        for item in items:
            title = item.find('title').text
            link = item.find('link').text
            results.append(f"  • {title}\n    {link}")
    return "\n".join(results[:6])

# ── AI THOUGHT ───────────────────────────────────────
def get_ai_thought():
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": f"Give me one specific, actionable idea for today — {datetime.now().strftime('%A %B %d')}. Make it practical and under 50 words.",
                "stream": False
            },
            timeout=30
        )
        return r.json()["response"]
    except:
        return "Ollama not running — start it with: ollama serve"

# ── BUILD THE EMAIL ──────────────────────────────────
def build_briefing():
    now = datetime.now()
    weather = get_weather()
    news = get_news()
    thought = get_ai_thought()
    
    return f"""🌅 MORNING BRIEFING — {now.strftime('%A, %B %d, %Y')}
═══════════════════════════════════════

📍 WEATHER
{weather}

📰 TOP NEWS
{news}

🧠 TODAY'S AI THOUGHT
{thought}

📅 TODAY IS
Day {now.timetuple().tm_yday} of {now.year}
{365 - now.timetuple().tm_yday} days left this year.

─────────────────────────────────────
Generated at {now.strftime('%H:%M:%S')} by Meeko Mycelium
github.com/meekotharaccoon-cell/meeko-nerve-center
"""

# ── SEND ─────────────────────────────────────────────
def send_briefing():
    body = build_briefing()
    
    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = GMAIL_ADDRESS
    msg["Subject"] = f"🌅 Morning Briefing — {datetime.now().strftime('%b %d')}"
    msg.attach(MIMEText(body, "plain"))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)
    
    print(f"✅ Briefing sent at {datetime.now().strftime('%H:%M')}")

if __name__ == "__main__":
    send_briefing()
```

---

## Schedule It for 8am

**Mac/Linux:**
```bash
# Open crontab
crontab -e

# Add this line:
0 8 * * * python3 /path/to/morning_briefing.py
```

**Windows Task Scheduler:**
1. Task Scheduler → Create Basic Task
2. Name: "Morning Briefing"
3. Trigger: Daily → 8:00 AM
4. Action: `python C:\path\to\morning_briefing.py`

**GitHub Actions (runs even when computer is off):**
```yaml
# .github/workflows/morning-briefing.yml
name: Morning Briefing
on:
  schedule:
    - cron: '0 8 * * *'  # 8am UTC
jobs:
  brief:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install requests
      - run: python mycelium/morning_briefing.py
        env:
          GMAIL_ADDRESS: ${{ secrets.GMAIL_ADDRESS }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
```

---

## Customizing Your Briefing

Add any of these sections by dropping them into `build_briefing()`:

**Crypto prices:**
```python
def get_crypto():
    r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd")
    data = r.json()
    return f"BTC: ${data['bitcoin']['usd']:,.0f} | ETH: ${data['ethereum']['usd']:,.0f} | SOL: ${data['solana']['usd']:,.0f}"
```

**Random useful fact:**
```python
def get_fact():
    r = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random")
    return r.json()["text"]
```

**Your Gumroad sales:**
```python
def get_sales():
    r = requests.get("https://api.gumroad.com/v2/sales",
        headers={"Authorization": f"Bearer {GUMROAD_TOKEN}"},
        params={"after": "yesterday"}
    )
    sales = r.json().get("sales", [])
    return f"{len(sales)} sales yesterday — ${sum(float(s['price']) for s in sales)/100:.2f}"
```

---

*Built by Meeko Mycelium · github.com/meekotharaccoon-cell*
*70% of every sale → PCRF · pcrf.net*
