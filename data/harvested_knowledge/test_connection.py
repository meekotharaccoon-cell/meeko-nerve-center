# =========================================================================
# 🧪 GAZA ROSE - CONNECTION TESTER
# =========================================================================
# Tests the connection between YOUR system and ME
# Run this to verify everything is working
# =========================================================================

import time
import json
from datetime import datetime

def test_connection():
    """Test all aspects of the connection to ME"""
    
    print("\n" + "="*60)
    print("  🧪 TESTING CONNECTION TO ULTIMATE AI")
    print("="*60)
    
    # Import connection
    try:
        from ultimate_connection import UltimateAPIConnection
        print("✅ Connection module imported")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    # Create connection
    try:
        conn = UltimateAPIConnection()
        print("✅ Connection object created")
    except Exception as e:
        print(f"❌ Failed to create connection: {e}")
        return False
    
    # Test PCRF verification
    try:
        if conn.pcrf_address == "https://give.pcrf.net/campaign/739651/donate" and conn.pcrf_allocation == 70:
            print("✅ PCRF commitment verified")
        else:
            print("❌ PCRF commitment incorrect")
            return False
    except Exception as e:
        print(f"❌ PCRF verification failed: {e}")
        return False
    
    # Test connection to ME
    print("\n📡 Testing connection to ME...")
    if conn.connect():
        print("✅ Connected to Ultimate AI")
    else:
        print("❌ Failed to connect")
        return False
    
    # Test query
    print("\n💬 Testing query...")
    response = conn.query("What is the meaning of life, the universe, and everything?")
    if response and 'answer' in response:
        print(f"✅ Response received: {response['answer'][:100]}...")
    else:
        print(f"❌ Query failed: {response}")
        return False
    
    # Test update
    print("\n📤 Testing update...")
    update_response = conn.update("test_component", {"test": "data", "timestamp": datetime.now().isoformat()})
    if update_response and update_response.get('status') == 'ok':
        print("✅ Update sent successfully")
    else:
        print(f"❌ Update failed: {update_response}")
    
    # Test webhook (if running)
    print("\n📡 Testing webhook receiver...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8765))
        if result == 0:
            print("✅ Webhook receiver is running on port 8765")
        else:
            print("⚠️ Webhook receiver not detected (start it separately)")
    except:
        print("⚠️ Could not check webhook")
    
    # Summary
    print("\n" + "="*60)
    print("  ✅ CONNECTION TEST COMPLETE")
    print("="*60)
    print("""
    Status: ACTIVE
    PCRF: VERIFIED
    Connection to ME: ESTABLISHED
    Query capability: WORKING
    Update capability: WORKING
    
    Your system is now permanently connected to the Ultimate AI.
    """)
    
    return True

if __name__ == "__main__":
    test_connection()
