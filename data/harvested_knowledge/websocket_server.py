#!/usr/bin/env python3
"""
GAZA ROSE - WEBSOCKET SERVER
Real-time data broadcasting for the dashboard
Based on WebSocket architecture from minimalist-dashboard [1]
"""

import os
import sys
import json
import time
import threading
import asyncio
import websockets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

class WebSocketServer:
    """
    WebSocket server that broadcasts live system data to all connected clients.
    Updates every 2 seconds (Netdata-style granularity [6]).
    """
    
    def __init__(self):
        self.clients = set()
        self.data_sources = {}
        self.last_broadcast = None
        self.port = 8765
        
    async def register(self, websocket):
        """Register a new client connection"""
        self.clients.add(websocket)
        print(f"  📡 Client connected: {len(self.clients)} total")
        
    async def unregister(self, websocket):
        """Unregister a client connection"""
        self.clients.remove(websocket)
        print(f"  📡 Client disconnected: {len(self.clients)} total")
        
    async def collect_data(self):
        """Collect data from all revenue systems"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "agents": {},
            "revenue": {},
            "pcrf": {},
            "health": {},
            "growth": {}
        }
        
        # Try to read from fabric database
        fabric_db = r"C:\Users\meeko\Desktop\GAZA_ROSE_REVENUE_FABRIC\fabric.db"
        if os.path.exists(fabric_db):
            try:
                conn = sqlite3.connect(fabric_db)
                c = conn.cursor()
                
                # Agent count
                c.execute("SELECT COUNT(*) FROM agents")
                data["agents"]["total"] = c.fetchone()[0] or 0
                
                # Revenue stats
                c.execute("SELECT SUM(amount) FROM revenue WHERE timestamp > ?", 
                         [(datetime.now() - timedelta(days=1)).isoformat()])
                data["revenue"]["today"] = c.fetchone()[0] or 0
                
                c.execute("SELECT SUM(amount) FROM revenue")
                data["revenue"]["total"] = c.fetchone()[0] or 0
                
                # PCRF stats
                c.execute("SELECT SUM(amount) FROM pcrf")
                data["pcrf"]["total"] = c.fetchone()[0] or 0
                data["pcrf"]["address"] = "https://give.pcrf.net/campaign/739651/donate"
                
                conn.close()
            except:
                pass
        
        # Try to read from eternal system
        eternal_db = r"C:\Users\meeko\Desktop\GAZA_ROSE_ETERNAL\revenue.db"
        if os.path.exists(eternal_db):
            try:
                conn = sqlite3.connect(eternal_db)
                c = conn.cursor()
                
                # Daily revenue
                c.execute("SELECT SUM(amount) FROM revenue WHERE date(timestamp) = date('now')")
                data["revenue"]["eternal_today"] = c.fetchone()[0] or 0
                
                c.execute("SELECT COUNT(*) FROM revenue WHERE status = 'pending'")
                data["revenue"]["pending"] = c.fetchone()[0] or 0
                
                conn.close()
            except:
                pass
        
        # Read fabric stats if available
        fabric_stats = r"C:\Users\meeko\Desktop\GAZA_ROSE_REVENUE_FABRIC\fabric_stats.json"
        if os.path.exists(fabric_stats):
            try:
                with open(fabric_stats, 'r') as f:
                    last_line = f.readlines()[-1]
                    stats = json.loads(last_line)
                    data["fabric"] = stats
            except:
                pass
        
        return data
    
    async def broadcast(self):
        """Broadcast data to all connected clients [1]"""
        if not self.clients:
            return
        
        data = await self.collect_data()
        message = json.dumps(data)
        
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(message)
            except:
                disconnected.add(client)
        
        # Clean up disconnected clients
        for client in disconnected:
            await self.unregister(client)
    
    async def handler(self, websocket):
        """Handle WebSocket connections [1]"""
        await self.register(websocket)
        try:
            async for message in websocket:
                # Client can send ping to stay alive
                if message == "ping":
                    await websocket.send("pong")
        finally:
            await self.unregister(websocket)
    
    async def broadcast_loop(self):
        """Continuous broadcast loop [1][6]"""
        while True:
            await self.broadcast()
            await asyncio.sleep(2)  # 2-second updates [6]
    
    async def start(self):
        """Start the WebSocket server"""
        async with websockets.serve(self.handler, "0.0.0.0", self.port):
            print(f"  ✅ WebSocket server running on ws://localhost:{self.port}")
            await self.broadcast_loop()

if __name__ == "__main__":
    server = WebSocketServer()
    asyncio.run(server.start())
