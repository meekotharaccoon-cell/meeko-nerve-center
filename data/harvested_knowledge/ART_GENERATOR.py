#!/usr/bin/env python3
"""
ART_GENERATOR.py -- AI Art per $1 Purchase
Gaza Rose Gallery: Every piece unique. No two roses bloom the same.
Uses Claude for concept + HuggingFace for actual image generation.
Delivers via email to buyer instantly.
"""
import os, json, requests, smtplib, hashlib
from pathlib import Path
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

DATA_DIR = Path("data")
ART_DIR  = DATA_DIR / "generated_art"

GAZA_THEMES = [
    "Palestinian olive grove at golden hour, watercolor style",
    "Gaza coastline at dawn, impressionist brushstrokes",
    "red rose growing through rubble, hope and resilience",
    "Palestinian tatreez embroidery pattern, geometric vibrant",
    "Mediterranean sea from Gaza beach, abstract expressionism",
    "mother and child silhouette under crescent moon, tender",
    "pomegranate flowers in full bloom, botanical illustration",
    "white dove with olive branch over blue water, peace",
    "traditional keffiyeh patterns, digital textile art",
    "Gaza sunset warm oranges and deep purples, painterly",
    "child flying kite on beach, joyful and colorful",
    "ancient Palestinian architecture moonlit, geometric art",
]

def generate_concept(sale_id, api_key):
    theme = GAZA_THEMES[int(hashlib.md5(sale_id.encode()).hexdigest(), 16) % len(GAZA_THEMES)]
    if not api_key:
        return {"title": f"Gaza Rose #{sale_id[-4:]}", "theme": theme,
                "description": f"Palestinian resilience: {theme}",
                "emoji": "\U0001f339",
                "poem": "Where roses bloom through stone,\nHope needs no permission.\nEvery petal is a home\nRemembered with precision.",
                "sale_id": sale_id}
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 300,
                  "messages": [{"role": "user", "content": f"Gaza Rose Gallery digital art concept. Theme: {theme}. Sale: {sale_id}. Respond ONLY with JSON: {{\"title\": \"poetic title\", \"theme\": \"detailed art description\", \"description\": \"2-sentence meaning\", \"emoji\": \"single emoji\", \"poem\": \"4-line poem\"}}"}]},
            timeout=30)
        r.raise_for_status()
        text = r.json()["content"][0]["text"]
        s, e = text.find("{"), text.rfind("}") + 1
        result = json.loads(text[s:e]) if s >= 0 else {}
        result["sale_id"] = sale_id
        return result
    except Exception as ex:
        return {"title": "Gaza Rose", "theme": theme, "emoji": "\U0001f339",
                "poem": "A rose for Palestine.", "sale_id": sale_id}

def generate_image(concept):
    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        print("  No HF_TOKEN -- text art only")
        return None
    try:
        r = requests.post(
            "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
            headers={"Authorization": f"Bearer {hf_token}"},
            json={"inputs": f"{concept['theme']}, high quality, artistic, Palestinian art style"},
            timeout=120)
        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            ART_DIR.mkdir(parents=True, exist_ok=True)
            img_path = ART_DIR / f"{concept['sale_id']}.png"
            img_path.write_bytes(r.content)
            print(f"  Image: {img_path}")
            return img_path
    except Exception as e: print(f"  Image error: {e}")
    return None

def deliver(buyer_email, concept, img_path=None):
    gmail = os.environ.get("GMAIL_ADDRESS", "")
    gpass = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not gmail or not gpass or not buyer_email: return False
    try:
        msg = MIMEMultipart()
        msg["Subject"] = f"{concept.get('emoji','🌹')} {concept.get('title','Gaza Rose')} -- Your Art"
        msg["From"] = gmail
        msg["To"]   = buyer_email
        body = f"""{concept.get('emoji','🌹')} {concept.get('title','')}
{'='*40}
{concept.get('description','')}

--- A poem ---
{concept.get('poem','')}

Your $1 sent $0.70 to Gaza Rose Gallery.
70 cents toward art, culture, and memory.

The loop never stops.
-- Gaza Rose Gallery x SolarPunk
Sale: {concept.get('sale_id','')}"""
        msg.attach(MIMEText(body, "plain"))
        if img_path and Path(img_path).exists():
            with open(img_path, "rb") as f:
                part = MIMEBase("image", "png")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", "attachment", filename=f"{concept.get('title','art')}.png")
                msg.attach(part)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(gmail, gpass)
            s.send_message(msg)
        print(f"  Delivered to {buyer_email}")
        return True
    except Exception as e:
        print(f"  Delivery error: {e}")
        return False

def main():
    DATA_DIR.mkdir(exist_ok=True)
    print("ART_GENERATOR -- Gaza Rose")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    pending_f = DATA_DIR / "pending_art.json"
    if not pending_f.exists():
        print("  No pending art requests")
        return
    pending = json.loads(pending_f.read_text())
    log = []
    for sale in pending:
        sale_id = sale.get("id", datetime.now().strftime("%Y%m%d%H%M%S"))
        concept  = generate_concept(sale_id, api_key)
        img_path = generate_image(concept)
        delivered = deliver(sale.get("buyer_email", ""), concept, img_path)
        log.append({"sale_id": sale_id, "title": concept.get("title"), "delivered": delivered, "timestamp": datetime.now().isoformat()})
        print(f"  Done: {concept.get('title','?')} | delivered: {delivered}")
    pending_f.unlink()
    log_f = DATA_DIR / "art_log.json"
    existing = []
    if log_f.exists():
        try: existing = json.loads(log_f.read_text())
        except: pass
    log_f.write_text(json.dumps((existing + log)[-500:], indent=2))
    print(f"  Processed {len(log)} requests")

if __name__ == "__main__":
    main()
