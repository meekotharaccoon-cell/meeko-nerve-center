"""
Coordinator node for managing distributed reasoning tasks.
"""
import asyncio
import uuid
import json
from typing import Dict, Any, List, Optional
from .mesh_node import MeshNode


class CoordinatorNode(MeshNode):
    """Coordinator node that manages distributed reasoning tasks."""
    
    def __init__(self, node_id: Optional[str] = None, port: int = 8766):
        super().__init__(node_id, port, model_size="120b")
        self.active_reasoning_tasks: Dict[str, Dict[str, Any]] = {}
        self.node_capabilities: Dict[str, List[str]] = {}
    
    async def start(self):
        """Start the coordinator node."""
        await super().start()
        print(f"CoordinatorNode {self.info.node_id} ready to coordinate reasoning tasks")
    
    async def distribute_reasoning_task(self, problem: str, context: Dict[str, Any] = None) -> str:
        """Distribute a complex reasoning task across the mesh."""
        task_id = str(uuid.uuid4())
        
        # Break down the problem into subtasks
        subtasks = await self._decompose_problem(problem, context or {})
        
        # Create reasoning task
        reasoning_task = {
            "task_id": task_id,
            "problem": problem,
            "context": context,
            "subtasks": subtasks,
            "status": "active",
            "results": {},
            "start_time": asyncio.get_event_loop().time()
        }
        
        self.active_reasoning_tasks[task_id] = reasoning_task
        
        # Distribute subtasks to available nodes
        await self._distribute_subtasks(task_id, subtasks)
        
        return task_id
    
    async def _decompose_problem(self, problem: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose a complex problem into smaller subtasks."""
        # Simulate problem decomposition using gpt-oss-120b
        await asyncio.sleep(0.2)  # Simulate processing time
        
        subtasks = [
            {
                "subtask_id": str(uuid.uuid4()),
                "type": "analysis",
                "description": f"Analyze aspect 1 of: {problem[:50]}...",
                "priority": 1
            },
            {
                "subtask_id": str(uuid.uuid4()),
                "type": "synthesis", 
                "description": f"Synthesize findings for: {problem[:50]}...",
                "priority": 2
            },
            {
                "subtask_id": str(uuid.uuid4()),
                "type": "validation",
                "description": f"Validate solution for: {problem[:50]}...",
                "priority": 3
            }
        ]
        
        return subtasks
    
    async def _distribute_subtasks(self, task_id: str, subtasks: List[Dict[str, Any]]):
        """Distribute subtasks to available mesh nodes."""
        if not self.connections:
            print("No peer nodes available for task distribution")
            return
        
        # Simple round-robin distribution
        peer_nodes = list(self.connections.keys())
        
        for i, subtask in enumerate(subtasks):
            if peer_nodes:
                target_node = peer_nodes[i % len(peer_nodes)]
                
                message = {
                    "type": "reasoning_subtask",
                    "task_id": task_id,
                    "subtask": subtask,
                    "coordinator_id": self.info.node_id
                }
                
                try:
                    conn = self.connections[target_node]
                    await conn.send(json.dumps(message))
                    print(f"Distributed subtask {subtask['subtask_id']} to node {target_node}")
                except Exception as e:
                    print(f"Failed to distribute subtask to {target_node}: {e}")
    
    async def collect_reasoning_results(self, task_id: str, timeout: float = 30.0) -> Dict[str, Any]:
        """Collect and synthesize results from distributed reasoning."""
        if task_id not in self.active_reasoning_tasks:
            return {"error": "Task not found"}
        
        task = self.active_reasoning_tasks[task_id]
        start_time = asyncio.get_event_loop().time()
        
        # Wait for results with timeout
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            if len(task["results"]) >= len(task["subtasks"]):
                break
            await asyncio.sleep(0.1)
        
        # Synthesize final result
        final_result = await self._synthesize_results(task)
        task["status"] = "completed"
        task["final_result"] = final_result
        
        return final_result
    
    async def _synthesize_results(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize results from all subtasks into final answer."""
        # Simulate synthesis using gpt-oss-120b
        await asyncio.sleep(0.3)
        
        return {
            "problem": task["problem"],
            "solution": f"Synthesized solution based on {len(task['results'])} distributed analyses",
            "confidence": 0.85,
            "reasoning_path": [result.get("reasoning", "") for result in task["results"].values()],
            "nodes_involved": len(task["results"])
        }
    
    async def _process_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process coordinator-specific messages."""
        msg_type = data.get("type")
        
        if msg_type == "subtask_result":
            task_id = data["task_id"]
            subtask_id = data["subtask_id"]
            result = data["result"]
            
            if task_id in self.active_reasoning_tasks:
                self.active_reasoning_tasks[task_id]["results"][subtask_id] = result
                return {"type": "ack", "message": "Result received"}
        
        # Fall back to parent message processing
        return await super()._process_message(data)