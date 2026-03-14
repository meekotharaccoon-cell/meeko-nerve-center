# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
INCOME_ARCHITECT.py -- The $1 Art Loop Engine
70% -> Gaza Rose  |  30% -> Reinvests -> Loop
Every sale feeds itself. The loop never stops.
"""
import os, json, requests
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")
LOOP_STATE_FILE = DATA_DIR / "loop_fund.json"

def load_loop_fund():
    if LOOP_STATE_FILE.exists():
        try: return json.loads(LOOP_STATE_FILE.read_text())
        except: pass
    return {"balance": 0.0, "total_earned": 0.0, "total_to_gaza": 0.0,
            "auto_buys": 0, "sales": [], "last_auto_buy": None}

def save_loop_fund(state):
    DATA_DIR.mkdir(exist_ok=True)
    LOOP_STATE_FILE.write_text(json.dumps(state, indent=2))

def record_sale(amount=1.00):
    state = load_loop_fund()
    gaza_cut  = round(amount * 0.70, 2)
    meeko_cut = round(amount * 0.30, 2)
    state["balance"]       = round(state["balance"] + meeko_cut, 2)
    state["total_earned"]  = round(state["total_earned"] + meeko_cut, 2)
    state["total_to_gaza"] = round(state["total_to_gaza"] + gaza_cut, 2)
    state["sales"].append({"timestamp": datetime.now().isoformat(),
                           "amount": amount, "gaza": gaza_cut, "meeko": meeko_cut})
    state["sales"] = state["sales"][-1000:]
    save_loop_fund(state)
    print(f"  Sale: ${amount:.2f} -> Gaza ${gaza_cut:.2f} | Loop +${meeko_cut:.2f} (balance: ${state['balance']:.2f})")
    return state

def check_auto_buy(state):
    if state["balance"] < 1.00:
        return state, False
    print(f"  LOOP TRIGGER: ${state['balance']:.2f} >= $1.00 -- auto-buying!")
    state["balance"]       = round(state["balance"] - 1.00, 2)
    state["auto_buys"]    += 1
    state["last_auto_buy"] = datetime.now().isoformat()
    state["total_to_gaza"] = round(state["total_to_gaza"] + 0.70, 2)
    state["balance"]       = round(state["balance"] + 0.30, 2)
    state["sales"].append({"timestamp": datetime.now().isoformat(), "amount": 1.00,
                           "gaza": 0.70, "meeko": 0.30, "source": "auto_loop"})
    save_loop_fund(state)
    print(f"  Auto-buy #{state['auto_buys']}. Gaza +$0.70. Loop: ${state['balance']:.2f}")
    return state, True

def get_advice(state, api_key):
    if not api_key:
        return f"Loop fund: ${state.get('balance',0):.2f}. Share the $1 art link. 3.33 sales = 1 auto-buy."
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 100,
                  "messages": [{"role": "user", "content": f"SolarPunk advisor. Loop fund ${state.get('balance',0):.2f}, auto-buys {state.get('auto_buys',0)}, Gaza total ${state.get('total_to_gaza',0):.2f}. ONE action to maximize $1 art loop velocity. 1 sentence."}]},
            timeout=20)
        r.raise_for_status()
        return r.json()["content"][0]["text"]
    except: return "Share the $1 art shop link everywhere to accelerate the loop."

def main():
    DATA_DIR.mkdir(exist_ok=True)
    print("INCOME_ARCHITECT -- $1 Art Loop Engine")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    state = load_loop_fund()
    webhook_f = DATA_DIR / "new_sales.json"
    if webhook_f.exists():
        try:
            sales = json.loads(webhook_f.read_text())
            for s in sales: state = record_sale(s.get("amount", 1.00))
            webhook_f.unlink()
        except Exception as e: print(f"  Webhook error: {e}")
    while state["balance"] >= 1.00:
        state, ok = check_auto_buy(state)
        if not ok: break
    advice = get_advice(state, api_key)
    report = {
        "timestamp": datetime.now().isoformat(),
        "current_balance": state.get("balance", 0),
        "total_to_gaza": state.get("total_to_gaza", 0),
        "total_earned_meeko": state.get("total_earned", 0),
        "total_sales": len(state.get("sales", [])),
        "auto_loop_sales": state.get("auto_buys", 0),
        "investment_advice": advice,
        "next_upgrade": "$20 -> Claude Pro" if state.get("total_earned", 0) < 20 else "$35 -> API credits",
        "total_monthly_estimate": round(state.get("total_earned", 0), 2),
    }
    (DATA_DIR / "flywheel_state.json").write_text(json.dumps(report, indent=2))
    print(f"  Gaza: ${state['total_to_gaza']:.2f} | Loop: ${state['balance']:.2f} | Auto-buys: {state['auto_buys']}")
    return report

if __name__ == "__main__":
    main()
