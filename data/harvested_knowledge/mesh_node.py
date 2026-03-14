"""
Enhanced mesh node with networking capabilities.
"""
import asyncio
import json
import websockets
from typing import Dict, Any, Set, Optional
from .node import Node, NodeStatus


class MeshNode(Node):
    """Enhanced node with mesh networking capabilities."""
    
    def __init__(self, node_id: Optional[str] = None, port: int = 8765, model_size: str = "20b"):
        capabilities = [f"gpt-oss-{model_size}", "mesh-networking", "distributed-reasoning"]
        super().__init__(node_id, capabilities)
        self.port = port
        self.model_size = model_size
        self.peers: Set[str] = set()
        self.server = None
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
    
    async def start(self):
        """Start the mesh node with networking."""
        await super().start()
        self.server = await websockets.serve(self._handle_connection, "localhost", self.port)
        print(f"MeshNode {self.info.node_id} listening on port {self.port}")
    
    async def stop(self):
        """Stop the mesh node."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        for conn in self.connections.values():
            await conn.close()
        await super().stop()
    
    async def _handle_connection(self, websocket, path):
        """Handle incoming WebSocket connections."""
        try:
            async for message in websocket:
                data = json.loads(message)
                response = await self._process_message(data)
                await websocket.send(json.dumps(response))
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def _process_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming mesh messages."""
        msg_type = data.get("type")
        
        if msg_type == "ping":
            return {"type": "pong", "node_id": self.info.node_id}
        
        elif msg_type == "task":
            result = await self.process_task(data["task_id"], data["payload"])
            return {"type": "task_result", **result}
        
        elif msg_type == "join_mesh":
            self.peers.add(data["node_id"])
            return {"type": "welcome", "node_id": self.info.node_id, "peers": list(self.peers)}
        
        return {"type": "error", "message": "Unknown message type"}
    
    async def connect_to_peer(self, peer_address: str):
        """Connect to another mesh node."""
        try:
            uri = f"ws://{peer_address}"
            websocket = await websockets.connect(uri)
            
            # Send join message
            join_msg = {"type": "join_mesh", "node_id": self.info.node_id}
            await websocket.send(json.dumps(join_msg))
            
            response = await websocket.recv()
            data = json.loads(response)
            
            if data["type"] == "welcome":
                self.peers.update(data["peers"])
                self.connections[data["node_id"]] = websocket
                print(f"Connected to peer {data['node_id']}")
            
        except Exception as e:
            print(f"Failed to connect to peer {peer_address}: {e}")
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected peers."""
        if not self.connections:
            return
        
        message_str = json.dumps(message)
        await asyncio.gather(
            *[conn.send(message_str) for conn in self.connections.values()],
            return_exceptions=True
        )