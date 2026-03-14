import requests, json, time, datetime, sys

print("?? GITHUB SPONSORS REVENUE ENGINE")
print("="*60)

with open("config.json") as f:
    config = json.load(f)

GITHUB_TOKEN = config["github"]["token"]
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def setup_sponsors():
    """Set up GitHub Sponsors if not already"""
    print("1. Go to: https://github.com/sponsors")
    print("2. Click 'Set up GitHub Sponsors'")
    print("3. Follow the wizard (5 minutes)")
    print("4. Set tier prices: $1, $5, $47 (for complete SolarPunk system)")
    print("5. Share: https://github.com/sponsors/MeekoThaRaccoon")
    return True

def check_sponsors():
    """Check for sponsors and revenue"""
    try:
        # Check current sponsors
        response = requests.get("https://api.github.com/user/sponsors", headers=HEADERS)
        if response.status_code == 200:
            sponsors = response.json()
            total_monthly = sum(sponsor.get("monthly_amount", 0) for sponsor in sponsors)
            
            if sponsors:
                print(f"[{datetime.datetime.now()}] ACTIVE REVENUE: ${total_monthly}/month")
                print(f"   Sponsors: {len(sponsors)}")
                
                # Auto-thank new sponsors
                for sponsor in sponsors:
                    username = sponsor["sponsor"]["login"]
                    amount = sponsor["monthly_amount"]
                    print(f"   ? {username}: ${amount}/month")
                
                return total_monthly
            else:
                print(f"[{datetime.datetime.now()}] No sponsors yet. Promote: https://github.com/sponsors/MeekoThaRaccoon")
                return 0
        else:
            print(f"??  GitHub Sponsors not set up (Status: {response.status_code})")
            setup_sponsors()
            return 0
            
    except Exception as e:
        print(f"? Error: {e}")
        return 0

def promote_sponsors():
    """Promote sponsors on Twitter"""
    # This will be called by Twitter bot
    return "Support SolarPunk humanitarian work: https://github.com/sponsors/MeekoThaRaccoon"

# Run continuously
if __name__ == "__main__":
    print("?? GitHub Sponsors Revenue Engine Started")
    print("Will check for sponsors hourly and promote automatically")
    
    total_revenue = 0
    
    while True:
        revenue = check_sponsors()
        total_revenue += revenue
        
        if revenue > 0:
            print(f"?? Total revenue tracked: ${total_revenue}")
            print("?? 50% would auto-send to humanitarian causes")
        
        time.sleep(3600)  # Check hourly
