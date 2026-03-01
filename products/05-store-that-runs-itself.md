# Build a Store That Runs Itself
### From "I sell things" to "sales happen while I sleep" — the actual infrastructure

**Price: $1 — 70% goes to PCRF (children's aid in Gaza)**

---

## What You're Getting

The exact stack to build a zero-maintenance digital store: Gumroad for payments, GitHub Actions for automation, and a post-purchase email sequence that runs forever without touching it.

This is not theory. This is the store architecture used by the system that made this guide.

---

## The Stack (All Free)

| Layer | Tool | What It Does |
|-------|------|-------------|
| Product hosting | **Gumroad** | Stores files, handles payments, delivers downloads |
| Automation | **GitHub Actions** | Runs scripts on schedule, no server needed |
| Email | **Gmail App Password** | Sends post-purchase sequences |
| Analytics | **Gumroad dashboard** | Tracks sales, revenue, refunds |
| Content | **GitHub repo** | Stores your product files (free, unlimited) |

Monthly cost: $0 (Gumroad takes 10% per sale — no monthly fee on free plan)

---

## Step 1: Gumroad Setup (10 minutes)

1. Create account at gumroad.com
2. Add your first product: **New Product → Digital**
3. Upload your file (PDF, zip, anything)
4. Set price to $1
5. In "Customize": write a real description (not marketing fluff — describe exactly what's inside)
6. Enable: **"Notify me of each sale"**

That's a working store. But it doesn't run itself yet.

---

## Step 2: The Post-Purchase Email Sequence

Gumroad has built-in email automation. Go to: **Products → [Your Product] → Emails**

**Email 1 — Immediate (auto-sends on purchase):**
```
Subject: You got it — here's what to do next

Thanks for buying [PRODUCT NAME].

Your file is attached above. Here's the fastest way to get value from it:

[ONE SPECIFIC ACTION THEY CAN DO IN UNDER 5 MINUTES]

If you hit any issues: reply to this email. I read every one.

— [Your name]

P.S. 70% of this sale just went to PCRF. Thank you for that.
```

**Email 2 — Day 3 (scheduled):**
```
Subject: Did [PRODUCT NAME] work for you?

Three days ago you grabbed [PRODUCT NAME].

Quick question: did you actually try it?

If yes: what happened? (reply — I'm genuinely curious)
If no: here's the 5-minute version that actually works: [SIMPLEST POSSIBLE FIRST STEP]

The next thing in this series is [PRODUCT 2 NAME]: [one sentence description].
It's $1. Here if you want it: [LINK]
```

**Email 3 — Day 7:**
```
Subject: The thing most people skip (and shouldn't)

One week in.

The part of [PRODUCT] that most people skip but makes everything else work better: [SPECIFIC TIP]

That's it. One thing. Try it.

Also — [RELATED PRODUCT] builds directly on this. Same price. [LINK]
```

---

## Step 3: Automate the Listings

Once you have more than 3 products, update them all at once with this script:

```python
import requests
import json

GUMROAD_TOKEN = "your-gumroad-access-token"  # From gumroad.com/settings/advanced

PRODUCTS = [
    {"name": "The $0 AI Stack", "price": 100, "description": "..."},  # price in cents
    {"name": "The Email Responder", "price": 100, "description": "..."},
    # add all your products
]

def get_existing_products():
    r = requests.get(
        "https://api.gumroad.com/v2/products",
        headers={"Authorization": f"Bearer {GUMROAD_TOKEN}"}
    )
    return r.json().get("products", [])

def update_product(product_id, data):
    r = requests.put(
        f"https://api.gumroad.com/v2/products/{product_id}",
        headers={"Authorization": f"Bearer {GUMROAD_TOKEN}"},
        data=data
    )
    return r.json()

existing = get_existing_products()
for product in existing:
    print(f"Found: {product['name']} — ${product['price']/100}")
```

Get your Gumroad access token: **gumroad.com/settings/advanced → Generate Access Token**

---

## Step 4: Track Sales in GitHub

Add this to your daily briefing workflow:

```python
def get_sales_today():
    r = requests.get(
        "https://api.gumroad.com/v2/sales",
        headers={"Authorization": f"Bearer {GUMROAD_TOKEN}"},
        params={"after": "yesterday"}
    )
    sales = r.json().get("sales", [])
    total = sum(float(s["price"]) for s in sales) / 100
    return len(sales), total

count, revenue = get_sales_today()
print(f"Today: {count} sales — ${revenue:.2f}")
```

---

## The Loop That Makes It Self-Running

```
New product idea
      ↓
Write content (30 min)
      ↓
Push to GitHub (automated)
      ↓
GitHub Action converts to PDF
      ↓
Script posts to Gumroad
      ↓
Email sequence runs automatically
      ↓
Day 3 email upsells next product
      ↓
New product idea (from buyer feedback)
      ↓
repeat
```

This is the loop. Every part of it is in this series.

---

*Built by Meeko Mycelium · github.com/meekotharaccoon-cell*
*70% of every sale → PCRF · pcrf.net*
