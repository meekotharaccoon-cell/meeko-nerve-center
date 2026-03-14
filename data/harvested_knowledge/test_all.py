import json, tweepy, requests, sys
from datetime import datetime

print("🎯 SOLARPUNK QUICK TEST")
print("="*60)

try:
    with open("config.json", 'r') as f:
        config = json.load(f)
    
    print("✅ Config loaded")
    
    # Test Twitter
    if config.get("twitter", {}).get("api_key"):
        print("\n🔑 Testing Twitter API...")
        try:
            auth = tweepy.OAuth1UserHandler(
                config["twitter"]["api_key"],
                config["twitter"]["api_secret"],
                config["twitter"]["access_token"],
                config["twitter"]["access_secret"]
            )
            api = tweepy.API(auth)
            user = api.verify_credentials()
            print(f"  ✅ Twitter: @{user.screen_name}")
        except Exception as e:
            print(f"  ❌ Twitter failed: {e}")
    
    # Test GitHub
    if config.get("github", {}).get("token"):
        print("\n🐙 Testing GitHub API...")
        try:
            response = requests.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {config['github']['token']}"}
            )
            if response.status_code == 200:
                print(f"  ✅ GitHub: {response.json().get('login')}")
            else:
                print(f"  ❌ GitHub failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ GitHub failed: {e}")
    
    # Test Gumroad
    if config.get("gumroad", {}).get("token"):
        print("\n💰 Testing Gumroad API...")
        try:
            response = requests.get(
                "https://api.gumroad.com/v2/user",
                headers={"Authorization": f"Bearer {config['gumroad']['token']}"}
            )
            if response.status_code == 200:
                print("  ✅ Gumroad: Connected")
            else:
                print(f"  ❌ Gumroad failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Gumroad failed: {e}")
    
    print("\n" + "="*60)
    print("✅ BASIC TESTS COMPLETE")
    print("\nIf any tests failed, check your tokens in config.json")
    print("Then run: python deploy_all.py")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    print("Check config.json exists and is valid JSON")
