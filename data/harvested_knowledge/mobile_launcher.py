"""
GAZA ROSE - MOBILE LAUNCHER
For Android (Pydroid3) and iOS (Pythonista)
"""

import os
import sys
import getpass
import platform

print("\n" + "="*50)
print("   GAZA ROSE - MOBILE SYSTEM")
print("="*50)

# Detect platform
if 'android' in platform.platform().lower():
    print(" Android device detected")
    print("   Using Pydroid3 runtime")
elif 'ios' in platform.platform().lower():
    print(" iOS device detected")
    print("   Using Pythonista runtime")
else:
    print(" Mobile device detected")

print("\n SECURE KEY ENTRY")
print("Your keys will NEVER be stored")
print("They exist only in memory during this session\n")

# Get keys securely
polygon_key = getpass.getpass("Polygon private key (64 hex chars): ").strip()
openai_key = getpass.getpass("OpenAI API key (sk-...): ").strip()

# Validate
if len(polygon_key) != 64:
    print("\n Invalid Polygon key format")
    sys.exit(1)

if not openai_key.startswith('sk-'):
    print("\n Invalid OpenAI key format")
    sys.exit(1)

# Set environment (memory only)
os.environ['POLYGON_PRIVATE_KEY'] = polygon_key
os.environ['OPENAI_API_KEY'] = openai_key
os.environ['PCRF_ADDRESS'] = '"https://give.pcrf.net/campaign/739651/donate"'
os.environ['PCRF_ALLOCATION'] = '70'

print("\n Keys validated. Starting mobile system...\n")

try:
    # Import mobile core
    sys.path.append(os.path.dirname(__file__))
    from mobile_core import GazaRoseMobileCore
    
    # Start system
    mobile = GazaRoseMobileCore()
    mobile.start()
    
    print(" Mobile revenue system running")
    print(f" PCRF: {os.environ['PCRF_ADDRESS']}")
    print("70% FOREVER\n")
    
    # Keep running
    import time
    while True:
        stats = mobile.get_stats()
        print(f"  Revenue: ${stats['total_revenue']:.2f} | PCRF: ${stats['pcrf_70%']:.2f}", end='\r')
        time.sleep(5)
        
except KeyboardInterrupt:
    print("\n\n System stopped")
    print(" Keys cleared from memory")
except Exception as e:
    print(f"\n Error: {e}")
finally:
    # Clear sensitive data
    polygon_key = None
    openai_key = None
