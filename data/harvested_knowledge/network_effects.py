"""
GAZA ROSE - NETWORK EFFECTS AMPLIFIER
Based on Indirect Incentive Strategies research [citation:2][citation:5]

Key insight: Network effects create exponential growth when agents
incentivize each other through indirect mechanisms
"""

import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import sqlite3
import math

class NetworkEffectsAmplifier:
    """
    Amplifies revenue through network effects [citation:2]
    """
    
    def __init__(self):
        self.db_path = "network_effects.db"
        self._init_database()
        
    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Agent network graph
        c.execute('''CREATE TABLE IF NOT EXISTS agent_network
                    (agent_id TEXT,
                     connected_agent TEXT,
                     connection_strength REAL,
                     revenue_multiplier REAL,
                     last_interaction TIMESTAMP,
                     PRIMARY KEY (agent_id, connected_agent))''')
        
        # Indirect incentives [citation:2]
        c.execute('''CREATE TABLE IF NOT EXISTS indirect_incentives
                    (id TEXT PRIMARY KEY,
                     source_agent TEXT,
                     target_agent TEXT,
                     incentive_type TEXT,
                     magnitude REAL,
                     network_multiplier REAL,
                     timestamp TIMESTAMP)''')
        
        # Network effect measurements
        c.execute('''CREATE TABLE IF NOT EXISTS network_metrics
                    (id TEXT PRIMARY KEY,
                     network_size INTEGER,
                     connection_density REAL,
                     average_multiplier REAL,
                     total_revenue REAL,
                     timestamp TIMESTAMP)''')
        
        conn.commit()
        conn.close()
    
    def calculate_network_multiplier(self, agent_id: str) -> float:
        """
        Calculate network effect multiplier for an agent [citation:2]
        Based on Metcalfe's Law: value  n
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get agent's network size
        c.execute('''SELECT COUNT(*) FROM agent_network 
                    WHERE agent_id = ? OR connected_agent = ?''', (agent_id, agent_id))
        connections = c.fetchone()[0]
        
        # Get average connection strength
        c.execute('''SELECT AVG(connection_strength) FROM agent_network 
                    WHERE agent_id = ? OR connected_agent = ?''', (agent_id, agent_id))
        avg_strength = c.fetchone()[0] or 1.0
        
        conn.close()
        
        # Network effect multiplier = n * log(n) * avg_strength [citation:2]
        if connections > 0:
            multiplier = connections * math.log(connections + 1) * avg_strength / 10
            return max(1.0, multiplier)
        return 1.0
    
    def create_indirect_incentive(self, source: str, target: str, incentive_type: str, magnitude: float):
        """
        Create indirect incentive between agents [citation:2][citation:5]
        Indirect mechanisms can match direct mechanism performance
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Calculate network multiplier
        multiplier = self.calculate_network_multiplier(target)
        
        # Store incentive
        incentive_id = f"inc_{datetime.now().timestamp()}"
        c.execute('''INSERT INTO indirect_incentives 
                    (id, source_agent, target_agent, incentive_type, magnitude, network_multiplier, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (incentive_id, source, target, incentive_type, magnitude, multiplier,
                  datetime.now().isoformat()))
        
        # Update or create network connection
        c.execute('''INSERT OR REPLACE INTO agent_network 
                    (agent_id, connected_agent, connection_strength, revenue_multiplier, last_interaction)
                    VALUES (?, ?, ?, ?, ?)''',
                 (source, target, 
                  (magnitude * multiplier) / 100,  # Connection strength based on incentive
                  multiplier,
                  datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return {
            "incentive_id": incentive_id,
            "effective_magnitude": magnitude * multiplier,
            "network_multiplier": multiplier
        }
    
    def optimize_network_topology(self) -> Dict:
        """
        Optimize agent connections for maximum network effects [citation:2]
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get all agents and their current connections
        c.execute('''SELECT agent_id, COUNT(*) as conn_count 
                    FROM (SELECT agent_id FROM agent_network
                          UNION ALL
                          SELECT connected_agent FROM agent_network)
                    GROUP BY agent_id''')
        agents = c.fetchall()
        
        if len(agents) < 2:
            conn.close()
            return {"status": "insufficient_agents", "recommendations": []}
        
        # Calculate optimal connections (dense enough for effects, sparse enough for efficiency)
        optimal_density = min(0.3, 10 / len(agents))  # 30% max, but scale with size
        
        # Generate recommendations
        recommendations = []
        for agent_id, current_conns in agents:
            target_conns = int(len(agents) * optimal_density)
            if current_conns < target_conns:
                recommendations.append({
                    "agent": agent_id,
                    "action": "increase_connections",
                    "from": current_conns,
                    "to": target_conns,
                    "expected_multiplier_gain": math.log(target_conns) - math.log(current_conns + 1)
                })
        
        conn.close()
        
        return {
            "network_size": len(agents),
            "optimal_density": optimal_density,
            "recommendations": recommendations,
            "potential_improvement": sum(r["expected_multiplier_gain"] for r in recommendations)
        }
    
    def measure_network_effects(self) -> Dict:
        """
        Measure current network effect contribution [citation:2]
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get all agents and calculate their multipliers
        c.execute('''SELECT DISTINCT agent_id FROM agent_network
                    UNION
                    SELECT DISTINCT connected_agent FROM agent_network''')
        agents = [a[0] for a in c.fetchall()]
        
        if not agents:
            conn.close()
            return {"network_multiplier": 1.0, "contribution": 0}
        
        multipliers = []
        for agent in agents:
            multiplier = self.calculate_network_multiplier(agent)
            multipliers.append(multiplier)
        
        # Calculate network metrics
        avg_multiplier = np.mean(multipliers)
        max_multiplier = max(multipliers)
        
        # Connection density
        c.execute('''SELECT COUNT(*) FROM agent_network''')
        total_connections = c.fetchone()[0]
        possible_connections = len(agents) * (len(agents) - 1) / 2
        density = total_connections / possible_connections if possible_connections > 0 else 0
        
        # Store metrics
        c.execute('''INSERT INTO network_metrics 
                    (id, network_size, connection_density, average_multiplier, total_revenue, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (f"metric_{datetime.now().timestamp()}", len(agents), density,
                  avg_multiplier, 0, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return {
            "network_size": len(agents),
            "connection_density": density,
            "average_multiplier": avg_multiplier,
            "max_multiplier": max_multiplier,
            "total_effect": avg_multiplier * len(agents)
        }
    
    def amplify_revenue(self, base_revenue: float) -> float:
        """
        Apply network effects to amplify revenue [citation:2]
        """
        metrics = self.measure_network_effects()
        network_multiplier = metrics.get("average_multiplier", 1.0)
        
        # Revenue = base_revenue * network_multiplier [citation:2]
        amplified = base_revenue * network_multiplier
        
        # Additional boost from network effects theory [citation:5]
        if metrics["connection_density"] > 0.3:
            amplified *= 1.2  # Dense networks get extra boost
        
        return amplified
    
    def get_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        stats = {}
        for table in ["agent_network", "indirect_incentives", "network_metrics"]:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = c.fetchone()[0]
        conn.close()
        return stats

if __name__ == "__main__":
    network = NetworkEffectsAmplifier()
    print(f" Network Effects Amplifier active [exponential growth potential]")
