import sys
import os
sys.path.insert(0, os.getenv("SITE_ROOT"))
sys.path.insert(0, os.getenv("AGENT_PATH"))

import asyncio
import json
import ssl
import websockets

WATCH_PATH = "/comm/mailman-1/incoming"
PORT = 9443  # 🔐 Standard for secure WSS stream
SEEN = set()

CERT_PATH = "certs/server.crt"
KEY_PATH = "certs/server.key"

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile=CERT_PATH, keyfile=KEY_PATH)

async def stream_logs(websocket):
    print(f"[WSS] Client connected: {websocket.remote_address}")
    try:
        while True:
            for fname in sorted(os.listdir(WATCH_PATH)):
                if not fname.endswith(".json") and not fname.endswith(".msg"):
                    continue
                if fname in SEEN:
                    continue

                path = os.path.join(WATCH_PATH, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        try:
                            msg = json.loads(content)
                        except:
                            msg = {"msg": content, "raw": True}

                        await websocket.send(json.dumps(msg))
                        SEEN.add(fname)
                        print(f"[WSS] Sent: {fname}")
                except Exception as e:
                    print(f"[ERROR] Failed to read {fname}: {e}")
            await asyncio.sleep(1)
    except websockets.exceptions.ConnectionClosed:
        print(f"[DISCONNECT] {websocket.remote_address} disconnected.")

async def main():
    print(f"[WSS] Stream live at wss://localhost:{PORT}")
    async with websockets.serve(stream_logs, "0.0.0.0", PORT, ssl=ssl_context):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[WSS] Shutdown requested.")
