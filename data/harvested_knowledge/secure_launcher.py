#!/usr/bin/env python3
"""
GAZA ROSE - SECURE LAUNCHER
Keys are entered each session and NEVER stored on disk
"""

import os
import sys
import getpass
import platform
from datetime import datetime

def secure_launch():
    """Launch system with secure key entry"""
    
    print("\n" + "="*60)
    print("   GAZA ROSE - SECURE SYSTEM LAUNCH")
    print("="*60)
    print("\n Your keys will be used ONLY in this session")
    print("   They will NEVER be stored on disk\n")
    
    # Collect keys securely (getpass hides input)
    polygon_key = getpass.getpass("Polygon private key (64 hex chars): ").strip()
    openai_key = getpass.getpass("OpenAI API key (sk-...): ").strip()
    
    # Validate format
    if len(polygon_key) != 64 or not all(c in '0123456789abcdefABCDEF' for c in polygon_key):
        print("\n Invalid Polygon key format")
        sys.exit(1)
    
    if not openai_key.startswith('sk-') or len(openai_key) < 20:
        print("\n Invalid OpenAI key format")
        sys.exit(1)
    
    # Set environment variables (memory only)
    os.environ['POLYGON_PRIVATE_KEY'] = polygon_key
    os.environ['OPENAI_API_KEY'] = openai_key
    os.environ['PCRF_ADDRESS'] = '"https://give.pcrf.net/campaign/739651/donate"'
    os.environ['PCRF_ALLOCATION'] = '70'
    
    print("\n Keys validated. Starting system...\n")
    
    # Import and start system
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from gaza_rose_complete import GazaRoseKnowledgeBase
        knowledge = GazaRoseKnowledgeBase()
        
        print(f" Gaza Rose System v{knowledge.version}")
        print(f" Components: {knowledge.get_component_count()}")
        print(f" PCRF: {knowledge.pcrf_address} (70%)")
        print("\n System running...\n")
        
        # Keep running
        while True:
            # In real implementation, this would run the revenue loop
            # For now, just show it's alive
            print(f"    {datetime.now().strftime('%H:%M:%S')} - System active", end='\r')
            
    except KeyboardInterrupt:
        print("\n\n System stopped")
        print(" Keys cleared from memory")
    except Exception as e:
        print(f"\n Error: {e}")
    finally:
        # Clear sensitive data
        polygon_key = None
        openai_key = None
        os.environ.pop('POLYGON_PRIVATE_KEY', None)
        os.environ.pop('OPENAI_API_KEY', None)

if __name__ == "__main__":
    secure_launch()
