#!/usr/bin/env python3
"""
PRODUCT_DELIVERY_ENGINE.py — auto-delivers products when sales happen
=====================================================================
Watches Gmail for Ko-fi / Gumroad sale notifications.
Extracts buyer email. Sends them their download link immediately.
Meeko never touches this. Ever.

FLOW:
  Sale on Ko-fi or Gumroad
  → notification email → meekotharaccoon@gmail.com
  → this engine reads it (IMAP)
  → finds buyer email + product
  → looks up download URL from product_registry.json
  → emails buyer their link (SMTP)
  → logs to data/delivery_log.json
"""
import os, json, re, smtplib, imaplib, email
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA       = Path("data"); DATA.mkdir(exist_ok=True)
GMAIL_ADDR = os.environ.get("GMAIL_ADDRESS", "meekotharaccoon@gmail.com")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASSWORD", "")

PRODUCT_KEYWORDS = {
    "solarpunk": "solarpunk-starter",
    "build your own": "solarpunk-starter",
    "local ai agent": "local-ai-agent",
    "ollama": "local-ai-agent",
    "github actions": "github-actions-autonomous",
    "prompt packs": "ai-prompt-packs",
    "ai prompt": "ai-prompt-packs",
    "gaza rose": "gaza-art-pack",
    "art prints": "gaza-art-pack",
    "art pack": "gaza-art-pack",
    "palestine": "gaza-art-pack",
}

DELIVERY_TEMPLATE = """\
Hi! 🌹

Thank you so much for your purchase — you're now part of something that matters.

{gaza_line}

Here's your download link:

🔗 {download_url}

Direct download — no login, no expiry, bookmark it and come back any time.

{extra}

Questions? Just reply to this email.

With gratitude,
SolarPunk™
Autonomous AI · Built by Meeko · Funded for Gaza
https://meekotharaccoon-cell.github.io/meeko-nerve-center/

PCRF EIN: 93-1057665 · 4★ Charity Navigator · Gaza since 1991
"""

EXTRAS = {
    "solarpunk-starter": "Your purchase is already funding the next iteration of this system. Fork and build yours: https://github.com/meekotharaccoon-cell/meeko-nerve-center",
    "local-ai-agent": "First step: install Ollama at https://ollama.ai — then follow Chapter 2 of the guide.",
    "github-actions-autonomous": "The templates in this guide are the same architecture SolarPunk runs on. Fork and adapt freely.",
    "ai-prompt-packs": "These prompts work with Claude, GPT-4, Gemini, and local Ollama models.",
    "gaza-art-pack": "Your 70% contribution goes directly to Palestinian children via PCRF. Thank you.",
}


def find_product(subject, body):
    text = (subject + " " + body).lower()
    for kw, pid in PRODUCT_KEYWORDS.items():
        if kw in text:
            return pid
    return None


def find_buyer_email(body, sender):
    emails = re.findall(r'[\w.+\-]+@[\w\-]+\.[\w.]+', body)
    skip = {GMAIL_ADDR.lower(), "noreply@ko-fi.com", "no-reply@gumroad.com",
            "noreply@gumroad.com", "receipts@ko-fi.com"}
    for e in emails:
        el = e.lower()
        if el not in skip and len(e) < 80 and "." in el.split("@")[-1]:
            return e
    return None


def send_email(to, pid, registry):
    product = registry.get(pid, {})
    title   = product.get("title", "Your SolarPunk Purchase")
    price   = product.get("price", 0)
    pct     = 70 if "art" in pid else 15
    dl_url  = (product.get("gumroad_url") or
               product.get("download_url") or
               "https://meekotharaccoon-cell.github.io/meeko-nerve-center/store.html")

    gaza_amount = price * (pct / 100)
    gaza_line   = f"${gaza_amount:.2f} of your ${price:.2f} is going to Palestinian children via PCRF right now."
    extra       = EXTRAS.get(pid, "")

    body = DELIVERY_TEMPLATE.format(
        gaza_line=gaza_line, download_url=dl_url, extra=extra)

    msg = MIMEMultipart()
    msg["From"]    = GMAIL_ADDR
    msg["To"]      = to
    msg["Subject"] = f"Your download: {title} 🌹"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as s:
        s.login(GMAIL_ADDR, GMAIL_PASS)
        s.sendmail(GMAIL_ADDR, to, msg.as_string())


def check_inbox():
    """Check Gmail for unread sale notifications."""
    sales = []
    try:
        conn = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        conn.login(GMAIL_ADDR, GMAIL_PASS)
        conn.select("INBOX")

        searches = [
            '(UNSEEN FROM "ko-fi")',
            '(UNSEEN FROM "gumroad")',
        ]
        for search in searches:
            _, nums = conn.search(None, search)
            for num in nums[0].split():
                _, data = conn.fetch(num, "(RFC822)")
                msg     = email.message_from_bytes(data[0][1])
                subject = msg.get("Subject", "")
                sender  = msg.get("From", "")
                body    = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body += part.get_payload(decode=True).decode("utf-8", errors="replace")
                else:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
                sales.append({"num": num, "subject": subject, "sender": sender, "body": body[:2000]})
                conn.store(num, "+FLAGS", "\\Seen")

        conn.logout()
    except Exception as e:
        print(f"  Gmail error: {e}")
    return sales


def run():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\nPRODUCT_DELIVERY_ENGINE — {ts}")

    if not GMAIL_PASS:
        print("  SKIP: no GMAIL_APP_PASSWORD")
        return {"status": "no_gmail"}

    log_path = DATA / "delivery_log.json"
    log      = json.loads(log_path.read_text()) if log_path.exists() else {"deliveries": [], "total": 0}

    reg_path = DATA / "product_registry.json"
    registry = json.loads(reg_path.read_text()).get("products", {}) if reg_path.exists() else {}

    sales     = check_inbox()
    delivered = 0
    print(f"  Unread sale emails: {len(sales)}")

    for sale in sales:
        pid   = find_product(sale["subject"], sale["body"])
        buyer = find_buyer_email(sale["body"], sale["sender"])

        if not pid:
            print(f"  Unknown product: {sale['subject'][:50]}")
            continue
        if not buyer:
            print(f"  No buyer email found in: {sale['subject'][:50]}")
            continue

        print(f"  Delivering {pid} to {buyer}...")
        try:
            send_email(buyer, pid, registry)
            log["deliveries"].append({"ts": ts, "buyer": buyer, "pid": pid, "ok": True})
            log["total"] = log.get("total", 0) + 1
            delivered += 1
            print(f"  ✓ Delivered {pid} to {buyer}")
        except Exception as e:
            print(f"  FAIL: {e}")
            log["deliveries"].append({"ts": ts, "buyer": buyer, "pid": pid, "ok": False, "error": str(e)[:60]})

    log["last_run"] = ts
    log_path.write_text(json.dumps(log, indent=2))

    state = {"ts": ts, "sales_found": len(sales), "delivered": delivered}
    (DATA / "delivery_engine_state.json").write_text(json.dumps(state, indent=2))
    print(f"  Done: {delivered}/{len(sales)} delivered")
    return state


if __name__ == "__main__":
    run()
