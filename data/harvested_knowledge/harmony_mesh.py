"""
Harmony protocol extension for mesh communication.
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class HarmonyMessage:
    """Harmony protocol message structure."""
    message_id: str
    sender_id: str
    recipient_id: Optional[str]
    message_type: str
    payload: Dict[str, Any]
    timestamp: float
    harmony_version: str = "1.0"


class HarmonyMeshProtocol:
    """Extended Harmony protocol for mesh networking."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.message_handlers: Dict[str, callable] = {}
        self.message_history: List[HarmonyMessage] = []
        self.routing_table: Dict[str, str] = {}  # node_id -> connection_address
    
    def register_handler(self, message_type: str, handler: callable):
        """Register a message handler for a specific message type."""
        self.message_handlers[message_type] = handler
    
    async def send_message(self, recipient_id: str, message_type: str, payload: Dict[str, Any], 
                          connection_manager) -> bool:
        """Send a Harmony message to another node."""
        message = HarmonyMessage(
            message_id=f"msg_{len(self.message_history)}",
            sender_id=self.node_id,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload,
            timestamp=asyncio.get_event_loop().time()
        )
        
        self.message_history.append(message)
        
        try:
            # Route message through mesh network
            if recipient_id in connection_manager.connections:
                conn = connection_manager.connections[recipient_id]
                harmony_data = {
                    "protocol": "harmony_mesh",
                    "message": asdict(message)
                }
                await conn.send(json.dumps(harmony_data))
                return True
            else:
                # Try to route through other nodes
                return await self._route_message(message, connection_manager)
        except Exception as e:
            print(f"Failed to send Harmony message: {e}")
            return False
    
    async def _route_message(self, message: HarmonyMessage, connection_manager) -> bool:
        """Route message through intermediate nodes."""
        # Simple flooding approach for now
        routed_message = {
            "protocol": "harmony_mesh",
            "message": asdict(message),
            "route_request": True
        }
        
        for conn in connection_manager.connections.values():
            try:
                await conn.send(json.dumps(routed_message))
            except Exception:
                continue
        
        return True
    
    async def handle_incoming_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming Harmony protocol messages."""
        if data.get("protocol") != "harmony_mesh":
            return {"error": "Not a Harmony message"}
        
        message_data = data["message"]
        message = HarmonyMessage(**message_data)
        
        # Check if message is for this node
        if message.recipient_id and message.recipient_id != self.node_id:
            # Forward message if it's a route request
            if data.get("route_request"):
                return {"type": "forward", "message": "Message forwarded"}
            return {"error": "Message not for this node"}
        
        # Process message
        if message.message_type in self.message_handlers:
            handler = self.message_handlers[message.message_type]
            result = await handler(message.payload)
            
            # Send response
            response = HarmonyMessage(
                message_id=f"resp_{message.message_id}",
                sender_id=self.node_id,
                recipient_id=message.sender_id,
                message_type=f"{message.message_type}_response",
                payload=result,
                timestamp=asyncio.get_event_loop().time()
            )
            
            return {"type": "harmony_response", "message": asdict(response)}
        
        return {"error": f"No handler for message type: {message.message_type}"}
    
    def create_reasoning_request(self, problem: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a Harmony-formatted reasoning request."""
        return {
            "problem_statement": problem,
            "context": context or {},
            "reasoning_type": "distributed_chain_of_thought",
            "requested_capabilities": ["analysis", "synthesis", "validation"],
            "priority": "normal",
            "timeout": 30.0
        }
    
    def create_reasoning_response(self, request_id: str, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Harmony-formatted reasoning response."""
        return {
            "request_id": request_id,
            "solution": solution,
            "confidence": solution.get("confidence", 0.0),
            "reasoning_steps": solution.get("reasoning_chain", []),
            "processing_time": solution.get("total_processing_time", 0.0),
            "nodes_involved": solution.get("nodes_involved", 1)
        }
    
    def create_node_announcement(self, capabilities: List[str], status: str) -> Dict[str, Any]:
        """Create a node announcement message."""
        return {
            "node_id": self.node_id,
            "capabilities": capabilities,
            "status": status,
            "protocol_version": "harmony_mesh_1.0",
            "available_for_reasoning": status == "idle"
        }
    
    def get_message_stats(self) -> Dict[str, Any]:
        """Get statistics about message handling."""
        if not self.message_history:
            return {"total_messages": 0}
        
        message_types = {}
        for msg in self.message_history:
            message_types[msg.message_type] = message_types.get(msg.message_type, 0) + 1
        
        return {
            "total_messages": len(self.message_history),
            "message_types": message_types,
            "average_message_size": sum(len(json.dumps(asdict(msg))) for msg in self.message_history) / len(self.message_history),
            "recent_activity": len([msg for msg in self.message_history if asyncio.get_event_loop().time() - msg.timestamp < 60])
        }