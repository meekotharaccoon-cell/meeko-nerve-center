cd C:\Users\meeko\Downloads\autonomous_income_system

# Create the SIMPLEST working version - NO emojis, NO syntax errors, NO bullshit
@'
import requests
import json
import time
from datetime import datetime

print("="*50)
print("HUMANITARIAN REVENUE ENGINE - RUNNING")
print("="*50)

# Your Amazon tag - WORKING
AMAZON_TAG = "autonomoushum-20"
API_URL = "http://localhost:8000/ask"

# Topics that make money
TOPICS = [
    "best office chair",
    "best standing desk",
    "best wireless mouse",
    "best mechanical keyboard",
    "best monitor",
    "best laptop",
    "best headphones"
]

cycle = 0
while True:
    cycle += 1
    print(f"\n--- CYCLE {cycle} ---")
    print(f"Time: {datetime.now()}")
    
    # Pick a topic
    topic = TOPICS[cycle % len(TOPICS)]
    print(f"Topic: {topic}")
    
    # Generate article
    try:
        r = requests.post(API_URL, json={
            "question": f"Write a 300-word review of the best {topic} 2026. Include affiliate tag {AMAZON_TAG}"
        }, timeout=30)
        article = r.json().get("answer", "")
        
        # Save it
        filename = f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(article)
        print(f"Saved: {filename}")
    except:
        print("API not ready - start main.py")
    
    # Wait 1 hour
    print("Sleeping 1 hour...")
    time.sleep(3600)
'@ | Out-File -FilePath "engine_simple.py" -Encoding UTF8

Write-Host "✅ DONE - RUN THIS:" -ForegroundColor Green
Write-Host "python engine_simple.py" -ForegroundColor Yellow