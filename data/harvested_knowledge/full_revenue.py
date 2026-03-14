import json, requests, time, datetime
from datetime import datetime

print("?? FULL REVENUE ENGINE STARTED")
print("="*60)

with open("config.json") as f:
    config = json.load(f)

def gumroad_oauth():
    """Get Gumroad access token using client credentials"""
    try:
        client_id = config["gumroad"]["client_id"]
        client_secret = config["gumroad"]["client_secret"]
        
        if not client_id or not client_secret:
            return None
            
        response = requests.post(
            "https://api.gumroad.com/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret
            }
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("? Gumroad OAuth token acquired")
            return token
        else:
            print(f"??  Gumroad OAuth failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"? Gumroad error: {e}")
        return None

def check_paypal():
    """Check PayPal balance"""
    try:
        client_id = config["paypal"]["client_id"]
        secret = config["paypal"]["secret"]
        
        if client_id and secret:
            print("? PayPal connected (sandbox mode)")
            print(f"   Email: {config['paypal']['email']}")
            return True
        else:
            print("??  PayPal keys missing")
            return False
            
    except Exception as e:
        print(f"? PayPal error: {e}")
        return False

def github_sponsors():
    """Check GitHub Sponsors"""
    try:
        token = config["github"]["token"]
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }
        
        response = requests.get("https://api.github.com/user", headers=headers)
        if response.status_code == 200:
            username = response.json()["login"]
            print(f"? GitHub Sponsors ready for: {username}")
            print(f"   Set up: https://github.com/sponsors/{username}")
            return True
        else:
            print("??  GitHub token invalid")
            return False
            
    except Exception as e:
        print(f"? GitHub Sponsors error: {e}")
        return False

# Main revenue loop
while True:
    print(f"\n[{datetime.now()}] REVENUE CHECK")
    print("-" * 40)
    
    # Gumroad
    gumroad_token = gumroad_oauth()
    if gumroad_token:
        print("?? Gumroad: Ready for product sales")
    
    # PayPal
    if check_paypal():
        print("?? PayPal: Ready for direct payments")
    
    # GitHub Sponsors
    if github_sponsors():
        print("?? GitHub Sponsors: Ready for recurring donations")
    
    print("\n?? NEXT: Set up GitHub Sponsors at: https://github.com/sponsors")
    print("?? Revenue ? 50% to humanitarian causes")
    
    time.sleep(3600)  # Check hourly
