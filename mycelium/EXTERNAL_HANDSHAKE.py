import json
import os

def check_access():
    vault_path = 'knowledge_ingest/CREDENTIALS_SAFE.json'
    if not os.path.exists(vault_path): return
    
    with open(vault_path, 'r') as f:
        creds = json.load(f)
    
    active_paths = []
    if creds['COMMERCE']['STRIPE_API_KEY'] != "PENDING": active_paths.append("Payment_Processing")
    if creds['CRYPTO']['MAIN_WALLET_ADDRESS'] != "PENDING": active_paths.append("Arbitrage_Liquidity")
    if creds['SOCIAL_ORCHESTRATION']['TELEGRAM_BOT_TOKEN'] != "PENDING": active_paths.append("Global_Voice")
    
    print(f"📡 Handshaker: Active Revenue Pathways: {active_paths}")
    return active_paths

if __name__ == "__main__":
    check_access()
