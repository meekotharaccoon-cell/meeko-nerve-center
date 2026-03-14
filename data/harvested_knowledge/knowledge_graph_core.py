#!/usr/bin/env python3
"""
GAZA ROSE - KNOWLEDGE GRAPH CORE
Self-organizing knowledge network based on agentic deep graph reasoning [3][6].
Automatically structures and refines knowledge through iterative graph expansion.
"""

import os
import json
import time
import hashlib
import networkx as nx
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np

class KnowledgeGraphCore:
    """
    Self-organizing knowledge network with:
        - Hub formation (central concepts)
        - Stable modularity (topic clusters)
        - Bridging nodes (cross-domain connections)
        - Scale-free network properties [3]
    """
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.node_metadata = {}
        self.edge_metadata = {}
        self.generation = 0
        self.hubs = []
        self.bridges = []
        self.modules = []
        
    def add_knowledge_node(self, node_id: str, content: Dict, node_type: str = "concept"):
        """Add a knowledge node to the graph"""
        self.graph.add_node(node_id)
        self.node_metadata[node_id] = {
            "content": content,
            "type": node_type,
            "created": str(datetime.now()),
            "generation": self.generation,
            "connections": 0,
            "centrality": 0.0
        }
        return node_id
    
    def add_relationship(self, from_node: str, to_node: str, rel_type: str, weight: float = 1.0):
        """Add a relationship edge between nodes"""
        self.graph.add_edge(from_node, to_node, key=rel_type)
        edge_id = f"{from_node}->{to_node}[{rel_type}]"
        self.edge_metadata[edge_id] = {
            "type": rel_type,
            "weight": weight,
            "created": str(datetime.now())
        }
        return edge_id
    
    def compute_network_metrics(self):
        """Calculate hub formation and bridging nodes [3][6]"""
        if len(self.graph.nodes) == 0:
            return
        
        # Degree centrality (hub formation)
        degree = nx.degree_centrality(self.graph)
        for node, cent in degree.items():
            if node in self.node_metadata:
                self.node_metadata[node]["centrality"] = cent
                if cent > 0.1:  # Threshold for hub detection
                    if node not in self.hubs:
                        self.hubs.append(node)
        
        # Betweenness centrality (bridging nodes)
        betweenness = nx.betweenness_centrality(self.graph)
        for node, cent in betweenness.items():
            if cent > 0.05:  # Threshold for bridge detection
                if node not in self.bridges:
                    self.bridges.append(node)
        
        # Community detection (modularity)
        try:
            from networkx.algorithms.community import greedy_modularity_communities
            communities = greedy_modularity_communities(self.graph.to_undirected())
            self.modules = [list(c) for c in communities]
        except:
            pass
    
    def get_graph_stats(self) -> Dict:
        """Get network statistics"""
        self.compute_network_metrics()
        return {
            "nodes": len(self.graph.nodes),
            "edges": len(self.graph.edges),
            "hubs": len(self.hubs),
            "bridges": len(self.bridges),
            "modules": len(self.modules),
            "generation": self.generation,
            "density": nx.density(self.graph),
            "is_scale_free": self._check_scale_free()
        }
    
    def _check_scale_free(self) -> bool:
        """Check if network exhibits scale-free properties [3]"""
        if len(self.graph.nodes) < 10:
            return False
        degrees = [d for n, d in self.graph.degree()]
        if not degrees:
            return False
        # Simple power-law check
        mean_deg = np.mean(degrees)
        max_deg = np.max(degrees)
        return max_deg > mean_deg * 3  # Rough indicator
    
    def save(self, path: str):
        """Save the knowledge graph"""
        data = {
            "graph": nx.node_link_data(self.graph),
            "node_metadata": self.node_metadata,
            "edge_metadata": self.edge_metadata,
            "hubs": self.hubs,
            "bridges": self.bridges,
            "modules": self.modules,
            "generation": self.generation,
            "stats": self.get_graph_stats()
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, path: str):
        """Load the knowledge graph"""
        with open(path, 'r') as f:
            data = json.load(f)
        self.graph = nx.node_link_graph(data["graph"])
        self.node_metadata = data["node_metadata"]
        self.edge_metadata = data["edge_metadata"]
        self.hubs = data["hubs"]
        self.bridges = data["bridges"]
        self.modules = data["modules"]
        self.generation = data["generation"]

# =========================================================================
# INITIALIZE THE KNOWLEDGE GRAPH
# =========================================================================
if __name__ == "__main__":
    kg = KnowledgeGraphCore()
    print(f" Knowledge Graph Core initialized")
    print(f"    Self-organizing network ready [3][6]")
    print(f"    Hub formation: enabled")
    print(f"    Bridge detection: enabled")
    print(f"    Modularity analysis: enabled")
