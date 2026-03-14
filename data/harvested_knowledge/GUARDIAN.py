#!/usr/bin/env python3
"""
GAZA ROSE - AUTONOMOUS GUARDIAN
Location: Your Desktop (FIXED)
"""

import time
import json
import os
from datetime import datetime

# Configuration
BITCOIN_ADDRESS = "bc1ppmp8e7n8zlxzuafllpdjpdaxmfrrvr46r4jylg6pf38433m4f0ssjeqpah"
AMAZON_TAG = "autonomoushum-20"
ARTIST = "Meeko"

print(f"\n Guardian initialized at {datetime.now()}")
print(f" Artist: {ARTIST}")
print(f" Bitcoin: {BITCOIN_ADDRESS}")
print(f" Amazon: {AMAZON_TAG}")
print(f"\n Guardian entering eternal loop...")
print(f"   Press Ctrl+C to stop (tube will restart)\n")

heartbeat = 0
while True:
    try:
        heartbeat += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Count artworks
        gallery_path = os.path.expanduser("~/Desktop/GAZA_ROSE_GALLERY/art")
        art_count = 0
        if os.path.exists(gallery_path):
            art_count = len([f for f in os.listdir(gallery_path) if f.endswith(('.png', '.jpg', '.jpeg'))])
        
        print(f"[{timestamp}]   Tube active - Generation {heartbeat} - {art_count} artworks")
        print(f"     Bitcoin: {BITCOIN_ADDRESS[:20]}...")
        print(f"      Amazon: {AMAZON_TAG}")
        print()
        
        time.sleep(60)
        
    except KeyboardInterrupt:
        print(f"\n Guardian paused at {datetime.now()}")
        print("   Tube remains intact. Restart to resume.\n")
        break
    except Exception as e:
        print(f"   Error: {e}")
        time.sleep(10)
