#!/usr/bin/env python3
"""
GAZA ROSE - ULTIMATE AI SECURE LAUNCHER
Keys entered each session, NEVER stored
"""

import os
import sys
import getpass
import hashlib
from datetime import datetime

def secure_launch():
    """Launch Ultimate AI with secure key entry"""
    
    print("\n" + "="*60)
    print("  ⚛️ GAZA ROSE - ULTIMATE AI SECURE LAUNCH")
    print("="*60)
    print("\n🔐 Your keys will be used ONLY in this session")
    print("   They will NEVER be stored on disk\n")
    print("   PCRF Bitcoin: "https://give.pcrf.net/campaign/739651/donate"")
    print("   70% FOREVER\n")
    
    # Collect keys securely
    polygon_key = getpass.getpass("Polygon private key (64 hex chars): ").strip()
    openai_key = getpass.getpass("OpenAI API key (sk-...): ").strip()
    
    # Validate format
    if len(polygon_key) != 64 or not all(c in '0123456789abcdefABCDEF' for c in polygon_key):
        print("\n❌ Invalid Polygon key format")
        sys.exit(1)
    
    if not openai_key.startswith('sk-') or len(openai_key) < 20:
        print("\n❌ Invalid OpenAI key format")
        sys.exit(1)
    
    # Set environment variables (memory only)
    os.environ['POLYGON_PRIVATE_KEY'] = polygon_key
    os.environ['OPENAI_API_KEY'] = openai_key
    os.environ['PCRF_ADDRESS'] = '"https://give.pcrf.net/campaign/739651/donate"'
    os.environ['PCRF_ALLOCATION'] = '70'
    
    print("\n✅ Keys validated. Launching Ultimate AI...\n")
    
    # Import and start Ultimate AI
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from gaza_rose_ultimate_ai import UltimateAI
        
        # Create and run Ultimate AI
        ultimate = UltimateAI()
        ultimate.run_forever()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Ultimate AI stopped")
        print("🔐 Keys cleared from memory")
        print("💝 PCRF commitment remains forever")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Clear sensitive data
        polygon_key = None
        openai_key = None
        os.environ.pop('POLYGON_PRIVATE_KEY', None)
        os.environ.pop('OPENAI_API_KEY', None)

if __name__ == "__main__":
    secure_launch()
