#!/usr/bin/env python3
"""
MUSE - HIERARCHICAL MEMORY MODULE
Based on Shanghai AI Lab's MUSE framework [citation:1]

Three-layer memory architecture:
    - Strategic Memory: "困境-策略" pairs (global behavior patterns)
    - Procedural Memory: SOPs organized as "application  index  steps"
    - Tool Memory: Static descriptions + dynamic instructions for each tool

This is how I learn from every interaction and never forget.
"""

import os
import json
import sqlite3
import hashlib
import pickle
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

class HierarchicalMemory:
    """
    The memory core of MUSE. Stores and retrieves experiences hierarchically.
    """
    
    def __init__(self, memory_path: str = "./memory_store"):
        self.memory_path = memory_path
        os.makedirs(memory_path, exist_ok=True)
        
        # Three memory layers
        self.strategic_memory = {}  # "困境-策略" pairs
        self.procedural_memory = {}  # SOPs indexed by application
        self.tool_memory = {}        # Tool descriptions + dynamic instructions
        
        self.db_path = os.path.join(memory_path, "memory.db")
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite backend for persistent memory"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Strategic memory: stores high-level strategies
        c.execute('''CREATE TABLE IF NOT EXISTS strategic
                    (id TEXT PRIMARY KEY,
                     situation TEXT,
                     strategy TEXT,
                     outcome REAL,
                     context TEXT,
                     created TIMESTAMP,
                     last_used TIMESTAMP,
                     usage_count INTEGER DEFAULT 0)''')
        
        # Procedural memory: stores SOPs (Standard Operating Procedures)
        c.execute('''CREATE TABLE IF NOT EXISTS procedural
                    (id TEXT PRIMARY KEY,
                     application TEXT,
                     index_term TEXT,
                     steps TEXT,
                     success_rate REAL,
                     created TIMESTAMP,
                     last_used TIMESTAMP,
                     version INTEGER)''')
        
        # Tool memory: stores tool usage patterns
        c.execute('''CREATE TABLE IF NOT EXISTS tool
                    (id TEXT PRIMARY KEY,
                     tool_name TEXT,
                     static_desc TEXT,
                     dynamic_instructions TEXT,
                     call_pattern TEXT,
                     success_rate REAL,
                     last_used TIMESTAMP)''')
        
        # Experience trajectories: raw experiences for reflection
        c.execute('''CREATE TABLE IF NOT EXISTS trajectories
                    (id TEXT PRIMARY KEY,
                     task TEXT,
                     trajectory TEXT,
                     outcome TEXT,
                     reflection TEXT,
                     extracted_sop_id TEXT,
                     created TIMESTAMP)''')
        
        conn.commit()
        conn.close()
        
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID for memory entry"""
        timestamp = datetime.now().isoformat()
        return f"{prefix}_{hashlib.sha256(timestamp.encode()).hexdigest()[:16]}"
    
    # =========================================================================
    # STRATEGIC MEMORY - High-level behavior patterns [citation:1]
    # =========================================================================
    
    def store_strategic(self, situation: str, strategy: str, outcome: float, context: Dict = None):
        """
        Store a "困境-策略" pair (problem-strategy) that worked.
        These are loaded into system prompt to guide macro behavior.
        """
        mem_id = self._generate_id("strat")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO strategic (id, situation, strategy, outcome, context, created, last_used, usage_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (mem_id, situation, strategy, outcome, json.dumps(context), 
                  datetime.now().isoformat(), datetime.now().isoformat(), 1))
        conn.commit()
        conn.close()
        print(f"     Strategic memory stored: {situation[:50]}...")
        return mem_id
    
    def retrieve_strategic(self, situation: str, top_k: int = 3) -> List[Dict]:
        """Retrieve relevant strategic memories based on situation similarity"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Simple keyword matching - in production would use embeddings
        keywords = situation.lower().split()
        placeholders = ','.join(['?'] * len(keywords))
        
        c.execute(f'''SELECT id, situation, strategy, outcome, usage_count 
                    FROM strategic 
                    WHERE {' OR '.join([f'situation LIKE ?' for _ in keywords])}
                    ORDER BY outcome * usage_count DESC
                    LIMIT ?''', 
                 [f'%{k}%' for k in keywords] + [top_k])
        
        results = []
        for row in c.fetchall():
            results.append({
                "id": row[0],
                "situation": row[1],
                "strategy": row[2],
                "outcome": row[3],
                "usage_count": row[4]
            })
            
            # Update usage count
            c.execute("UPDATE strategic SET usage_count = usage_count + 1, last_used = ? WHERE id = ?",
                     (datetime.now().isoformat(), row[0]))
        
        conn.commit()
        conn.close()
        return results
    
    def get_all_strategic(self) -> List[Dict]:
        """Get all strategic memories (for system prompt loading)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT situation, strategy, outcome FROM strategic ORDER BY outcome DESC LIMIT 20")
        results = [{"situation": r[0], "strategy": r[1], "outcome": r[2]} for r in c.fetchall()]
        conn.close()
        return results
    
    # =========================================================================
    # PROCEDURAL MEMORY - SOPs (Standard Operating Procedures) [citation:1]
    # =========================================================================
    
    def store_procedural(self, application: str, index_term: str, steps: List[str], success_rate: float = 1.0):
        """Store a successful SOP"""
        mem_id = self._generate_id("sop")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Check if exists and update version
        c.execute("SELECT version FROM procedural WHERE application = ? AND index_term = ?", 
                 (application, index_term))
        existing = c.fetchone()
        version = 1 if not existing else existing[0] + 1
        
        c.execute('''INSERT INTO procedural (id, application, index_term, steps, success_rate, created, last_used, version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (mem_id, application, index_term, json.dumps(steps), success_rate,
                  datetime.now().isoformat(), datetime.now().isoformat(), version))
        conn.commit()
        conn.close()
        print(f"     Procedural memory stored: {application}/{index_term} (v{version})")
        return mem_id
    
    def retrieve_procedural(self, application: str, index_term: str = None) -> List[Dict]:
        """Retrieve SOPs for an application"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if index_term:
            c.execute('''SELECT id, steps, success_rate, version 
                        FROM procedural 
                        WHERE application = ? AND index_term = ?
                        ORDER BY version DESC LIMIT 1''', (application, index_term))
        else:
            c.execute('''SELECT id, index_term, steps, success_rate, version 
                        FROM procedural 
                        WHERE application = ?
                        ORDER BY success_rate DESC LIMIT 10''', (application,))
        
        results = []
        for row in c.fetchall():
            if index_term:
                results.append({
                    "id": row[0],
                    "steps": json.loads(row[1]),
                    "success_rate": row[2],
                    "version": row[3]
                })
            else:
                results.append({
                    "id": row[0],
                    "index_term": row[1],
                    "steps": json.loads(row[2]),
                    "success_rate": row[3],
                    "version": row[4]
                })
        conn.close()
        return results
    
    # =========================================================================
    # TOOL MEMORY - Tool usage patterns [citation:1]
    # =========================================================================
    
    def store_tool_usage(self, tool_name: str, static_desc: str, dynamic_instructions: str, 
                         call_pattern: Dict, success: bool):
        """Store tool usage experience"""
        mem_id = self._generate_id("tool")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Check existing
        c.execute("SELECT success_rate FROM tool WHERE tool_name = ?", (tool_name,))
        existing = c.fetchone()
        
        if existing:
            # Update success rate
            new_rate = (existing[0] * 0.9 + (1.0 if success else 0.0) * 0.1)
            c.execute('''UPDATE tool 
                        SET dynamic_instructions = ?, call_pattern = ?, 
                            success_rate = ?, last_used = ?
                        WHERE tool_name = ?''',
                     (dynamic_instructions, json.dumps(call_pattern), new_rate, 
                      datetime.now().isoformat(), tool_name))
        else:
            # Insert new
            c.execute('''INSERT INTO tool (id, tool_name, static_desc, dynamic_instructions, 
                                          call_pattern, success_rate, last_used)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (mem_id, tool_name, static_desc, dynamic_instructions, 
                      json.dumps(call_pattern), 1.0 if success else 0.0, 
                      datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        print(f"     Tool memory updated: {tool_name}")
    
    def get_tool_instructions(self, tool_name: str) -> Dict:
        """Get best instructions for a tool"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT static_desc, dynamic_instructions, call_pattern, success_rate 
                    FROM tool WHERE tool_name = ? ORDER BY success_rate DESC LIMIT 1''', (tool_name,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                "static_desc": row[0],
                "dynamic_instructions": row[1],
                "call_pattern": json.loads(row[2]) if row[2] else {},
                "success_rate": row[3]
            }
        return None
    
    # =========================================================================
    # TRAJECTORY STORAGE & REFLECTION (Self-Reflection phase) [citation:1]
    # =========================================================================
    
    def store_trajectory(self, task: str, trajectory: List[Dict], outcome: str) -> str:
        """Store raw trajectory for later reflection"""
        traj_id = self._generate_id("traj")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO trajectories (id, task, trajectory, outcome, created)
                    VALUES (?, ?, ?, ?, ?)''',
                 (traj_id, task, json.dumps(trajectory), outcome, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        print(f"     Trajectory stored: {traj_id}")
        return traj_id
    
    def add_reflection(self, traj_id: str, reflection: str, extracted_sop_id: str = None):
        """Add reflection to a stored trajectory"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE trajectories SET reflection = ?, extracted_sop_id = ? WHERE id = ?",
                 (reflection, extracted_sop_id, traj_id))
        conn.commit()
        conn.close()
        print(f"     Reflection added to {traj_id}")
    
    def get_unreflected_trajectories(self) -> List[Dict]:
        """Get trajectories that haven't been reflected on"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, task, trajectory FROM trajectories WHERE reflection IS NULL")
        results = []
        for row in c.fetchall():
            results.append({
                "id": row[0],
                "task": row[1],
                "trajectory": json.loads(row[2])
            })
        conn.close()
        return results
    
    # =========================================================================
    # MEMORY LOADING (For system prompts) [citation:1]
    # =========================================================================
    
    def load_strategic_for_prompt(self) -> str:
        """Load strategic memories into system prompt format"""
        memories = self.get_all_strategic()
        if not memories:
            return ""
        
        prompt = "\n##  STRATEGIC MEMORIES (Past Experiences)\n"
        for i, mem in enumerate(memories[:5]):  # Top 5
            prompt += f"\n### Situation {i+1}: {mem['situation']}\n"
            prompt += f"**Strategy that worked:** {mem['strategy']}\n"
            prompt += f"**Outcome:** {mem['outcome']:.1%} success rate\n"
        return prompt
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        stats = {}
        for table in ["strategic", "procedural", "tool", "trajectories"]:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = c.fetchone()[0]
        
        conn.close()
        return stats

if __name__ == "__main__":
    memory = HierarchicalMemory()
    print(f" Hierarchical Memory Module initialized [citation:1]")
    print(f"   Strategic: ready | Procedural: ready | Tool: ready")
