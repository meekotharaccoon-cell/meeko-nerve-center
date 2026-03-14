#!/usr/bin/env python3
"""
GAZA ROSE - REVENUE INTELLIGENCE MEMORY CORE
Based on MUSE framework [citation:1]

Stores and learns from:
    - Which revenue strategies work best
    - Optimal agent spawning patterns
    - Best times for revenue generation
    - Self-healing success patterns
    - PCRF allocation efficiency
"""

import os
import json
import sqlite3
import hashlib
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class RevenueIntelligenceMemory:
    """
    The brain of your revenue system. Remembers everything that worked.
    """
    
    def __init__(self):
        self.db_path = "revenue_intelligence.db"
        self._init_database()
        print("     Revenue Intelligence Memory initialized")
        
    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Strategic Memory - What strategies generated most revenue
        c.execute('''CREATE TABLE IF NOT EXISTS strategic_revenue
                    (id TEXT PRIMARY KEY,
                     strategy_type TEXT,  -- 'spawn_rate', 'allocation', 'timing', 'swarm_size'
                     parameters TEXT,
                     revenue_generated REAL,
                     roi REAL,
                     timestamp TIMESTAMP,
                     success_score REAL,
                     context TEXT)''')
        
        # Agent Performance Memory - Which agents perform best
        c.execute('''CREATE TABLE IF NOT EXISTS agent_performance
                    (id TEXT PRIMARY KEY,
                     agent_id TEXT,
                     generation INTEGER,
                     parent_id TEXT,
                     total_revenue REAL,
                     pcrf_contributed REAL,
                     children_spawned INTEGER,
                     lifespan_hours REAL,
                     efficiency_score REAL,
                     last_active TIMESTAMP)''')
        
        # Revenue Pattern Memory - When revenue peaks
        c.execute('''CREATE TABLE IF NOT EXISTS revenue_patterns
                    (id TEXT PRIMARY KEY,
                     hour_of_day INTEGER,
                     day_of_week INTEGER,
                     avg_revenue REAL,
                     peak_revenue REAL,
                     samples INTEGER,
                     confidence REAL)''')
        
        # Self-Healing Memory - What fixes work best
        c.execute('''CREATE TABLE IF NOT EXISTS healing_memory
                    (id TEXT PRIMARY KEY,
                     error_type TEXT,
                     fix_applied TEXT,
                     success BOOLEAN,
                     time_to_fix REAL,
                     revenue_saved REAL,
                     timestamp TIMESTAMP)''')
        
        # Allocation Efficiency - 70% PCRF optimization
        c.execute('''CREATE TABLE IF NOT EXISTS allocation_efficiency
                    (id TEXT PRIMARY KEY,
                     allocation_ratio REAL,  -- Should always be 70%, but tracking
                     revenue_before REAL,
                     revenue_after REAL,
                     pcrf_sent REAL,
                     efficiency_score REAL,
                     timestamp TIMESTAMP)''')
        
        # Swarm Intelligence - How agents work together
        c.execute('''CREATE TABLE IF NOT EXISTS swarm_intelligence
                    (id TEXT PRIMARY KEY,
                     swarm_size INTEGER,
                     generations INTEGER,
                     total_revenue REAL,
                     per_agent_revenue REAL,
                     synergy_score REAL,
                     timestamp TIMESTAMP)''')
        
        conn.commit()
        conn.close()
    
    def store_strategic_success(self, strategy_type: str, parameters: Dict, 
                                revenue: float, roi: float) -> str:
        """Store a successful revenue strategy"""
        mem_id = hashlib.sha256(f"{strategy_type}{datetime.now()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO strategic_revenue 
                    (id, strategy_type, parameters, revenue_generated, roi, timestamp, success_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (mem_id, strategy_type, json.dumps(parameters), revenue, roi,
                  datetime.now().isoformat(), revenue * roi))
        conn.commit()
        conn.close()
        
        print(f"       Strategic success stored: {strategy_type} (${revenue:.2f})")
        return mem_id
    
    def store_agent_performance(self, agent_data: Dict) -> str:
        """Store performance metrics for an agent"""
        mem_id = hashlib.sha256(f"{agent_data['agent_id']}{datetime.now()}".encode()).hexdigest()[:16]
        
        # Calculate efficiency score
        efficiency = (agent_data.get('total_revenue', 0) * 
                     (1 + agent_data.get('children_spawned', 0) * 0.1) /
                     max(1, agent_data.get('lifespan_hours', 1)))
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO agent_performance 
                    (id, agent_id, generation, parent_id, total_revenue, pcrf_contributed,
                     children_spawned, lifespan_hours, efficiency_score, last_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (mem_id, agent_data.get('agent_id'), agent_data.get('generation', 0),
                  agent_data.get('parent_id', ''), agent_data.get('total_revenue', 0),
                  agent_data.get('pcrf_contributed', 0), agent_data.get('children_spawned', 0),
                  agent_data.get('lifespan_hours', 0), efficiency,
                  datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return mem_id
    
    def update_revenue_pattern(self, revenue: float):
        """Update revenue patterns based on time of day"""
        now = datetime.now()
        hour = now.hour
        day = now.weekday()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Check if pattern exists
        c.execute('''SELECT avg_revenue, peak_revenue, samples 
                    FROM revenue_patterns 
                    WHERE hour_of_day = ? AND day_of_week = ?''', (hour, day))
        existing = c.fetchone()
        
        if existing:
            # Update existing
            avg_rev = (existing[0] * existing[2] + revenue) / (existing[2] + 1)
            peak_rev = max(existing[1], revenue)
            samples = existing[2] + 1
            confidence = min(1.0, samples / 100)  # Confidence increases with samples
            
            c.execute('''UPDATE revenue_patterns 
                        SET avg_revenue = ?, peak_revenue = ?, samples = ?, confidence = ?
                        WHERE hour_of_day = ? AND day_of_week = ?''',
                     (avg_rev, peak_rev, samples, confidence, hour, day))
        else:
            # Insert new
            mem_id = hashlib.sha256(f"{hour}{day}".encode()).hexdigest()[:16]
            c.execute('''INSERT INTO revenue_patterns 
                        (id, hour_of_day, day_of_week, avg_revenue, peak_revenue, samples, confidence)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (mem_id, hour, day, revenue, revenue, 1, 0.1))
        
        conn.commit()
        conn.close()
    
    def store_healing_event(self, error_type: str, fix: str, success: bool, 
                           time_to_fix: float, revenue_saved: float) -> str:
        """Store self-healing success/failure for learning"""
        mem_id = hashlib.sha256(f"{error_type}{datetime.now()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO healing_memory 
                    (id, error_type, fix_applied, success, time_to_fix, revenue_saved, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (mem_id, error_type, fix, success, time_to_fix, revenue_saved,
                  datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return mem_id
    
    def store_swarm_performance(self, swarm_size: int, generations: int, 
                               total_revenue: float, per_agent_revenue: float) -> str:
        """Store swarm performance metrics"""
        mem_id = hashlib.sha256(f"swarm_{datetime.now()}".encode()).hexdigest()[:16]
        
        # Calculate synergy score (how much more each agent earns in swarm vs alone)
        baseline = 10.0  # Expected revenue per agent alone
        synergy = per_agent_revenue / baseline if baseline > 0 else 1.0
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO swarm_intelligence 
                    (id, swarm_size, generations, total_revenue, per_agent_revenue, synergy_score, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (mem_id, swarm_size, generations, total_revenue, per_agent_revenue, synergy,
                  datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return mem_id
    
    # =========================================================================
    # INTELLIGENT RETRIEVAL - Get best practices
    # =========================================================================
    
    def get_best_strategy(self, strategy_type: str) -> Optional[Dict]:
        """Get the highest-performing strategy of a given type"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT parameters, revenue_generated, roi 
                    FROM strategic_revenue 
                    WHERE strategy_type = ?
                    ORDER BY revenue_generated * roi DESC
                    LIMIT 1''', (strategy_type,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                "parameters": json.loads(row[0]),
                "revenue": row[1],
                "roi": row[2]
            }
        return None
    
    def get_best_spawn_rate(self) -> float:
        """Get optimal agent spawn rate from historical data"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT parameters FROM strategic_revenue 
                    WHERE strategy_type = 'spawn_rate'
                    ORDER BY revenue_generated DESC
                    LIMIT 1''')
        row = c.fetchone()
        conn.close()
        
        if row:
            params = json.loads(row[0])
            return params.get('rate', 0.3)
        return 0.3  # Default
    
    def get_optimal_timing(self) -> Dict:
        """Get best times for revenue generation"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT hour_of_day, avg_revenue 
                    FROM revenue_patterns 
                    WHERE confidence > 0.5
                    ORDER BY avg_revenue DESC
                    LIMIT 3''')
        rows = c.fetchall()
        conn.close()
        
        if rows:
            return {
                "best_hours": [r[0] for r in rows],
                "avg_revenues": [r[1] for r in rows]
            }
        return {"best_hours": list(range(24)), "avg_revenues": [10] * 24}
    
    def get_best_fix_for_error(self, error_type: str) -> Optional[str]:
        """Get most successful fix for a given error type"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT fix_applied, success, revenue_saved 
                    FROM healing_memory 
                    WHERE error_type = ?
                    ORDER BY success DESC, revenue_saved DESC
                    LIMIT 1''', (error_type,))
        row = c.fetchone()
        conn.close()
        
        if row and row[1]:  # If successful
            return row[0]
        return None
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        stats = {}
        tables = ['strategic_revenue', 'agent_performance', 'revenue_patterns', 
                  'healing_memory', 'swarm_intelligence']
        
        for table in tables:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = c.fetchone()[0]
        
        conn.close()
        return stats

if __name__ == "__main__":
    memory = RevenueIntelligenceMemory()
    print(f" Revenue Intelligence Memory active")
