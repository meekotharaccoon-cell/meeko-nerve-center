"""
Mesh network management and orchestration.
"""
import asyncio
from typing import Dict, List, Any, Optional
from .mesh_node import MeshNode
from .coordinator import CoordinatorNode


class MeshNetwork:
    """Manages the entire mesh network of nodes."""
    
    def __init__(self):
        self.nodes: Dict[str, MeshNode] = {}
        self.coordinator: Optional[CoordinatorNode] = None
        self.network_topology: Dict[str, List[str]] = {}
    
    async def add_node(self, node: MeshNode) -> str:
        """Add a node to the mesh network."""
        self.nodes[node.info.node_id] = node
        await node.start()
        
        # Connect to existing nodes
        if len(self.nodes) > 1:
            await self._connect_to_mesh(node)
        
        print(f"Added node {node.info.node_id} to mesh network")
        return node.info.node_id
    
    async def add_coordinator(self, coordinator: CoordinatorNode) -> str:
        """Add a coordinator node to the network."""
        self.coordinator = coordinator
        await self.add_node(coordinator)
        print(f"Coordinator {coordinator.info.node_id} added to network")
        return coordinator.info.node_id
    
    async def _connect_to_mesh(self, new_node: MeshNode):
        """Connect a new node to existing mesh nodes."""
        for existing_node in self.nodes.values():
            if existing_node.info.node_id != new_node.info.node_id:
                try:
                    await new_node.connect_to_peer(f"localhost:{existing_node.port}")
                    await existing_node.connect_to_peer(f"localhost:{new_node.port}")
                except Exception as e:
                    print(f"Failed to connect nodes: {e}")
    
    async def remove_node(self, node_id: str):
        """Remove a node from the mesh network."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            await node.stop()
            del self.nodes[node_id]
            print(f"Removed node {node_id} from mesh network")
    
    async def start_distributed_reasoning(self, problem: str, context: Dict[str, Any] = None) -> str:
        """Start a distributed reasoning task."""
        if not self.coordinator:
            raise ValueError("No coordinator available for distributed reasoning")
        
        task_id = await self.coordinator.distribute_reasoning_task(problem, context)
        print(f"Started distributed reasoning task {task_id}")
        return task_id
    
    async def get_reasoning_result(self, task_id: str, timeout: float = 30.0) -> Dict[str, Any]:
        """Get the result of a distributed reasoning task."""
        if not self.coordinator:
            raise ValueError("No coordinator available")
        
        return await self.coordinator.collect_reasoning_results(task_id, timeout)
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get the current status of the mesh network."""
        return {
            "total_nodes": len(self.nodes),
            "coordinator_active": self.coordinator is not None,
            "nodes": {
                node_id: node.get_status() 
                for node_id, node in self.nodes.items()
            },
            "topology": self._analyze_topology()
        }
    
    def _analyze_topology(self) -> Dict[str, Any]:
        """Analyze the network topology."""
        total_connections = sum(len(node.peers) for node in self.nodes.values())
        avg_connections = total_connections / len(self.nodes) if self.nodes else 0
        
        return {
            "total_connections": total_connections,
            "average_connections_per_node": avg_connections,
            "network_density": avg_connections / max(1, len(self.nodes) - 1)
        }
    
    async def simulate_node_failure(self, node_id: str):
        """Simulate a node failure for testing self-healing."""
        if node_id in self.nodes:
            print(f"Simulating failure of node {node_id}")
            await self.remove_node(node_id)
            
            # Trigger self-healing by reconnecting remaining nodes
            await self._heal_network()
    
    async def _heal_network(self):
        """Attempt to heal network connections after node failure."""
        print("Initiating network self-healing...")
        
        # Reconnect isolated nodes
        for node in self.nodes.values():
            if len(node.peers) < 2 and len(self.nodes) > 2:
                # Find nodes to connect to
                for other_node in self.nodes.values():
                    if (other_node.info.node_id != node.info.node_id and 
                        other_node.info.node_id not in node.peers):
                        try:
                            await node.connect_to_peer(f"localhost:{other_node.port}")
                            break
                        except Exception as e:
                            print(f"Healing connection failed: {e}")
        
        print("Network self-healing completed")
    
    async def shutdown(self):
        """Shutdown the entire mesh network."""
        print("Shutting down mesh network...")
        
        # Stop all nodes
        for node in self.nodes.values():
            await node.stop()
        
        self.nodes.clear()
        self.coordinator = None
        print("Mesh network shutdown complete")