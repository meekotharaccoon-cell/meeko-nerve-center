#!/usr/bin/env python3
"""
Quick test script for NeuroMesh functionality.
"""
import asyncio
import sys
from neuromesh import MeshNetwork, MeshNode, CoordinatorNode


async def test_basic_functionality():
    """Test basic NeuroMesh functionality."""
    print("🧪 Testing NeuroMesh Basic Functionality")
    print("=" * 40)
    
    try:
        # Create network
        network = MeshNetwork()
        print("✅ Created mesh network")
        
        # Add coordinator
        coordinator = CoordinatorNode(port=8766)
        await network.add_coordinator(coordinator)
        print("✅ Added coordinator node")
        
        # Add edge node
        edge_node = MeshNode(port=8767, model_size="20b")
        await network.add_node(edge_node)
        print("✅ Added edge node")
        
        # Test network status
        status = network.get_network_status()
        print(f"✅ Network status: {status['total_nodes']} nodes")
        
        # Test distributed reasoning
        task_id = await network.start_distributed_reasoning(
            "What is the capital of France?",
            {"domain": "geography"}
        )
        print(f"✅ Started reasoning task: {task_id[:8]}...")
        
        # Get result
        result = await network.get_reasoning_result(task_id, timeout=10.0)
        print(f"✅ Got reasoning result: {result['solution'][:50]}...")
        
        # Cleanup
        await network.shutdown()
        print("✅ Network shutdown complete")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def main():
    """Run tests."""
    success = await test_basic_functionality()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())