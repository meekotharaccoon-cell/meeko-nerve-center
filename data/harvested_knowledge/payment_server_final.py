#!/usr/bin/env python3
\"\"\"
GAZA ROSE - FINAL PAYMENT SERVER
Native Segwit: bc1qka74n62h3zk9mcv8v8xjtjtwehmnm24w3pfzzr
Taproot: bc1ppmp8e7n8zlxzuafllpdjpdaxmfrrvr46r4jylg6pf38433m4f0ssjeqpah
Artist: Meeko
\"\"\"

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from coinbase_commerce.client import Client

COINBASE_API_KEY = ""
NATIVE_SEGWIT = "bc1qka74n62h3zk9mcv8v8xjtjtwehmnm24w3pfzzr"
ARTIST = "Meeko"
PRICE = 10.00

client = Client(api_key=COINBASE_API_KEY)
app = Flask(__name__)
CORS(app)

@app.route('/create-checkout', methods=['POST'])
def create_checkout():
    try:
        charge = client.charge.create(
            name="Gaza Rose - Final Loop",
            description=f"Artist: {ARTIST}. 100% to UNRWA USA.",
            local_price={"amount": str(PRICE), "currency": "USD"},
            pricing_type="fixed_price",
            metadata={
                "artist": ARTIST,
                "native_segwit": NATIVE_SEGWIT,
                "timestamp": datetime.now().isoformat()
            }
        )
        return jsonify({"success": True, "url": charge.hosted_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "alive",
        "native_segwit": NATIVE_SEGWIT[:20] + "...",
        "artist": ARTIST
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("    GAZA ROSE - FINAL PAYMENT SERVER")
    print("="*60)
    print(f"   Native Segwit: {NATIVE_SEGWIT[:20]}...")
    print(f"   Artist: {ARTIST}")
    print("   Auto-Confirm: READY")
    print("   http://localhost:8006")
    print("="*60 + "\n")
    app.run(host='127.0.0.1', port=8006)
