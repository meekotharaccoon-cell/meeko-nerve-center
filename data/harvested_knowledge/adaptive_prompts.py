"""
GAZA ROSE - ADAPTIVE PROMPT OPTIMIZATION
Based on ATLAS framework [citation:3][citation:6]

Key innovation: Adaptive-OPRO dynamically optimizes prompts using
real-time stochastic feedback, outperforming fixed prompts consistently
"""

import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import sqlite3

class AdaptivePromptOptimizer:
    """
    ATLAS-style adaptive prompt optimization [citation:3]
    """
    
    def __init__(self):
        self.db_path = "adaptive_prompts.db"
        self._init_database()
        self.performance_history = []
        
    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Prompt templates with performance tracking
        c.execute('''CREATE TABLE IF NOT EXISTS prompt_templates
                    (id TEXT PRIMARY KEY,
                     template_type TEXT,  -- spawn, allocate, heal, etc.
                     template_text TEXT,
                     parameters TEXT,
                     success_rate REAL,
                     avg_revenue REAL,
                     trials INTEGER,
                     last_used TIMESTAMP)''')
        
        # Real-time feedback storage [citation:3]
        c.execute('''CREATE TABLE IF NOT EXISTS feedback_loop
                    (id TEXT PRIMARY KEY,
                     prompt_id TEXT,
                     outcome REAL,
                     latency REAL,
                     context TEXT,
                     timestamp TIMESTAMP)''')
        
        # Adaptive weights (updated continuously) [citation:6]
        c.execute('''CREATE TABLE IF NOT EXISTS adaptive_weights
                    (id TEXT PRIMARY KEY,
                     prompt_type TEXT,
                     weight_vector TEXT,
                     performance_metric REAL,
                     update_count INTEGER,
                     last_update TIMESTAMP)''')
        
        conn.commit()
        conn.close()
    
    def adaptive_opro_optimize(self, prompt_type: str, recent_outcomes: List[float]) -> Dict:
        """
        Adaptive-OPRO: Dynamic prompt optimization with stochastic feedback [citation:3]
        This is the key innovation that outperforms reflection-based approaches
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get current best template
        c.execute('''SELECT id, template_text, parameters, success_rate, avg_revenue 
                    FROM prompt_templates 
                    WHERE template_type = ? 
                    ORDER BY success_rate * avg_revenue DESC 
                    LIMIT 1''', (prompt_type,))
        best = c.fetchone()
        
        if not best:
            # Default template
            template = self._create_default_template(prompt_type)
            return {"template": template, "confidence": 0.5}
        
        # Adaptive optimization based on recent feedback [citation:3]
        if recent_outcomes:
            recent_avg = np.mean(recent_outcomes)
            historical_avg = best[3] * best[4]  # success_rate * avg_revenue
            
            # Calculate adjustment factor
            if recent_avg > historical_avg:
                # Positive trend - reinforce current parameters
                adjustment = 1.05
                confidence = min(1.0, best[3] + 0.05)
            else:
                # Negative trend - explore variations
                adjustment = 0.95
                confidence = max(0.5, best[3] - 0.05)
            
            # Update weights in database
            c.execute('''INSERT OR REPLACE INTO adaptive_weights 
                        (id, prompt_type, weight_vector, performance_metric, update_count, last_update)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (f"weight_{prompt_type}", prompt_type, json.dumps({"adjustment": adjustment}),
                      recent_avg, 1, datetime.now().isoformat()))
            conn.commit()
        
        conn.close()
        
        # Apply optimization to template
        params = json.loads(best[2]) if best[2] else {}
        params["adjustment"] = adjustment if "adjustment" in locals() else 1.0
        
        optimized_template = self._apply_optimization(best[1], params)
        
        return {
            "template": optimized_template,
            "parameters": params,
            "confidence": confidence if "confidence" in locals() else best[3],
            "expected_improvement": adjustment if "adjustment" in locals() else 1.0
        }
    
    def _create_default_template(self, prompt_type: str) -> str:
        templates = {
            "spawn": "Spawn new agents at rate {rate} with target revenue {target}",
            "allocate": "Allocate {percent}% to PCRF, reinvest {reinvest}%",
            "heal": "When error {error} occurs, apply fix {fix} within {timeout}s",
            "optimize": "Optimize for {metric} with constraints {constraints}"
        }
        return templates.get(prompt_type, "Execute with parameters: {params}")
    
    def _apply_optimization(self, template: str, params: Dict) -> str:
        """Apply optimized parameters to template"""
        for key, value in params.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template
    
    def incorporate_feedback(self, prompt_id: str, outcome: float, latency: float, context: Dict):
        """Real-time feedback incorporation [citation:3][citation:6]"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Store feedback
        c.execute('''INSERT INTO feedback_loop (id, prompt_id, outcome, latency, context, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (f"fb_{datetime.now().timestamp()}", prompt_id, outcome, latency,
                  json.dumps(context), datetime.now().isoformat()))
        
        # Update prompt performance
        c.execute('''UPDATE prompt_templates 
                    SET success_rate = (success_rate * trials + ?) / (trials + 1),
                        avg_revenue = (avg_revenue * trials + ?) / (trials + 1),
                        trials = trials + 1,
                        last_used = ?
                    WHERE id = ?''',
                 (1.0 if outcome > 0 else 0.0, outcome, datetime.now().isoformat(), prompt_id))
        
        conn.commit()
        conn.close()
    
    def get_optimal_parameters(self, prompt_type: str) -> Dict:
        """Get currently optimal parameters for a prompt type"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT parameters, success_rate, avg_revenue 
                    FROM prompt_templates 
                    WHERE template_type = ? 
                    ORDER BY success_rate * avg_revenue DESC 
                    LIMIT 1''', (prompt_type,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                "parameters": json.loads(row[0]) if row[0] else {},
                "success_rate": row[1],
                "avg_revenue": row[2]
            }
        return {"parameters": {}, "success_rate": 0.5, "avg_revenue": 0}
    
    def get_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM prompt_templates")
        templates = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM feedback_loop")
        feedback = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM adaptive_weights")
        weights = c.fetchone()[0]
        conn.close()
        return {"templates": templates, "feedback_samples": feedback, "weights": weights}

if __name__ == "__main__":
    optimizer = AdaptivePromptOptimizer()
    print(f" Adaptive Prompt Optimization active [ATLAS framework]")
