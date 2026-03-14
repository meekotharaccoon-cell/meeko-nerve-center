#!/usr/bin/env python3
"""
GAZA ROSE - LEARNING & ADAPTATION ENGINE
Learns from successful and failed integrations to improve future searches.
Based on self-evolving recommendation systems [citation:7]
"""

import os
import json
from datetime import datetime
from collections import defaultdict

class LearningEngine:
    def __init__(self):
        self.learning_db = r"C:\Users\meeko\Desktop\GAZA_ROSE_EVOLVER\learning_db.json"
        self.integration_log = r"C:\Users\meeko\Desktop\GAZA_ROSE_EVOLVER\integration_log.json"
        self.test_results = r"C:\Users\meeko\Desktop\GAZA_ROSE_EVOLVER\test_results.json"
        
    def load_learning_db(self):
        """Load the learning database"""
        if os.path.exists(self.learning_db):
            with open(self.learning_db, 'r') as f:
                return json.load(f)
        else:
            return {
                "successful_searches": [],
                "failed_searches": [],
                "search_weights": {},
                "integration_history": []
            }
    
    def save_learning_db(self, db):
        """Save the learning database"""
        with open(self.learning_db, 'w') as f:
            json.dump(db, f, indent=2)
    
    def learn_from_integration(self):
        """Learn from the last integration cycle"""
        if not os.path.exists(self.integration_log):
            return
        
        db = self.load_learning_db()
        
        with open(self.integration_log, 'r') as f:
            integrations = json.load(f)
        
        for integration in integrations.get("integrations", []):
            history_entry = {
                "timestamp": integration.get("time"),
                "name": integration.get("name"),
                "url": integration.get("url"),
                "success": integration.get("success")
            }
            db["integration_history"].append(history_entry)
            
            # Update search weights based on success
            search_term = integration.get("name", "").split("-")[0]
            if search_term:
                if search_term not in db["search_weights"]:
                    db["search_weights"][search_term] = {"success": 0, "total": 0}
                
                db["search_weights"][search_term]["total"] += 1
                if integration.get("success"):
                    db["search_weights"][search_term]["success"] += 1
        
        self.save_learning_db(db)
        return db
    
    def get_best_search_terms(self, gap):
        """Get the best search terms based on learning"""
        db = self.load_learning_db()
        
        # Default terms
        default_terms = {
            "metacognitive_loop": ["self-aware agent", "metacognitive AI", "self-monitoring system"],
            "evaluation_framework": ["agent evaluation", "LLM as judge", "prompt evals"],
            "feedback_collector": ["feedback collection", "human feedback loop", "RLHF"],
            "auto_retrain": ["automatic retraining", "self-improving model", "online learning"],
            "performance_tracker": ["agent metrics", "performance monitoring", "observability"]
        }
        
        if gap in default_terms:
            # Weight by learning
            weighted_terms = []
            for term in default_terms[gap]:
                weight = 1.0
                if term in db["search_weights"]:
                    w = db["search_weights"][term]
                    weight = w["success"] / max(w["total"], 1)
                weighted_terms.append((term, weight))
            
            # Sort by weight
            weighted_terms.sort(key=lambda x: x[1], reverse=True)
            return [t[0] for t in weighted_terms]
        
        return [gap]

if __name__ == "__main__":
    learner = LearningEngine()
    learner.learn_from_integration()
    print(f" LEARNING ENGINE UPDATED")
