#!/usr/bin/env python3
"""
GAZA ROSE - REVENUE CYCLE REFLECTION ENGINE
Based on MUSE "事后诸葛亮" (after-the-fact复盘) mechanism [citation:1]

After every revenue cycle, this:
    1. Analyzes what worked/didn't work
    2. Extracts successful patterns
    3. Updates strategy recommendations
    4. Improves future revenue generation
"""

import os
import json
import time
import sqlite3
import numpy as np
from datetime import datetime
from typing import Dict, List, Any

class RevenueReflectionEngine:
    """
    Reflects on every revenue cycle to continuously improve.
    """
    
    def __init__(self, memory):
        self.memory = memory
        self.reflection_count = 0
        self.optimizations_applied = 0
        
    def analyze_revenue_cycle(self, cycle_data: Dict) -> Dict:
        """
        Deep analysis of a revenue cycle:
            - Revenue by agent generation
            - Spawn timing efficiency
            - PCRF allocation timing
            - Self-healing events
            - Bottlenecks
        """
        analysis = {
            "total_revenue": cycle_data.get("total_revenue", 0),
            "agents_active": cycle_data.get("agents_active", 0),
            "new_agents": cycle_data.get("new_agents", 0),
            "pcrf_sent": cycle_data.get("pcrf_sent", 0),
            "reinvested": cycle_data.get("reinvested", 0),
            "healing_events": cycle_data.get("healing_events", []),
            "revenue_by_generation": {},
            "efficiency_metrics": {},
            "bottlenecks": [],
            "optimizations": []
        }
        
        # Revenue by generation
        if "agents" in cycle_data:
            for agent in cycle_data["agents"]:
                gen = agent.get("generation", 0)
                rev = agent.get("revenue", 0)
                if gen not in analysis["revenue_by_generation"]:
                    analysis["revenue_by_generation"][gen] = []
                analysis["revenue_by_generation"][gen].append(rev)
        
        # Calculate efficiency metrics
        if analysis["agents_active"] > 0:
            analysis["efficiency_metrics"]["revenue_per_agent"] = (
                analysis["total_revenue"] / analysis["agents_active"]
            )
            analysis["efficiency_metrics"]["pcrf_per_agent"] = (
                analysis["pcrf_sent"] / analysis["agents_active"]
            )
            analysis["efficiency_metrics"]["spawn_efficiency"] = (
                analysis["new_agents"] / analysis["agents_active"]
            )
        
        # Identify bottlenecks
        if analysis.get("efficiency_metrics", {}).get("revenue_per_agent", 0) < 5:
            analysis["bottlenecks"].append("Low revenue per agent - consider increasing spawn rate")
        
        if analysis.get("healing_events", []):
            analysis["bottlenecks"].append(f"{len(analysis['healing_events'])} healing events - system instability")
        
        # Generate optimization suggestions
        if analysis["revenue_by_generation"]:
            # Find best performing generation
            avg_by_gen = {
                gen: np.mean(revs) for gen, revs in analysis["revenue_by_generation"].items()
            }
            best_gen = max(avg_by_gen, key=avg_by_gen.get)
            
            if best_gen > 0:
                analysis["optimizations"].append({
                    "type": "generation_focus",
                    "suggestion": f"Generation {best_gen} performs best - spawn more from this lineage",
                    "expected_improvement": avg_by_gen[best_gen] / np.mean(list(avg_by_gen.values()))
                })
        
        return analysis
    
    def reflect_and_optimize(self, cycle_data: Dict) -> Dict:
        """
        Complete reflection cycle:
            1. Analyze performance
            2. Store successful patterns
            3. Update optimal parameters
            4. Return optimizations
        """
        self.reflection_count += 1
        print(f"\n     REVENUE REFLECTION #{self.reflection_count}")
        
        # 1. Analyze
        analysis = self.analyze_revenue_cycle(cycle_data)
        print(f"      Revenue: ${analysis['total_revenue']:.2f}")
        print(f"      Agents: {analysis['agents_active']} (+{analysis['new_agents']})")
        print(f"      PCRF: ${analysis['pcrf_sent']:.2f}")
        
        # 2. Store successful patterns
        if analysis["total_revenue"] > 50:  # Significant revenue threshold
            # Store spawn strategy if it worked
            if analysis["new_agents"] > 0:
                self.memory.store_strategic_success(
                    strategy_type="spawn_rate",
                    parameters={"rate": analysis["new_agents"] / max(1, analysis["agents_active"])},
                    revenue=analysis["total_revenue"],
                    roi=analysis["total_revenue"] / max(1, analysis["agents_active"])
                )
            
            # Store agent performance
            if "agents" in cycle_data:
                for agent in cycle_data["agents"]:
                    self.memory.store_agent_performance(agent)
            
            # Update revenue patterns
            self.memory.update_revenue_pattern(analysis["total_revenue"])
        
        # 3. Store healing patterns
        for heal in analysis.get("healing_events", []):
            self.memory.store_healing_event(
                error_type=heal.get("error", "unknown"),
                fix=heal.get("fix", "restart"),
                success=heal.get("success", True),
                time_to_fix=heal.get("time", 0),
                revenue_saved=heal.get("revenue_saved", 0)
            )
        
        # 4. Store swarm performance
        if analysis["agents_active"] > 0:
            self.memory.store_swarm_performance(
                swarm_size=analysis["agents_active"],
                generations=len(analysis["revenue_by_generation"]),
                total_revenue=analysis["total_revenue"],
                per_agent_revenue=analysis.get("efficiency_metrics", {}).get("revenue_per_agent", 0)
            )
        
        # 5. Generate optimization recommendations
        recommendations = {
            "spawn_rate": self._optimize_spawn_rate(analysis),
            "timing": self._optimize_timing(analysis),
            "healing": self._optimize_healing(analysis),
            "allocation": self._optimize_allocation(analysis)
        }
        
        if any(recommendations.values()):
            self.optimizations_applied += 1
        
        return {
            "analysis": analysis,
            "recommendations": recommendations,
            "memory_stats": self.memory.get_stats()
        }
    
    def _optimize_spawn_rate(self, analysis: Dict) -> Dict:
        """Optimize agent spawn rate based on performance"""
        current_rate = analysis.get("efficiency_metrics", {}).get("spawn_efficiency", 0.3)
        
        # Get best historical rate
        best_strategy = self.memory.get_best_strategy("spawn_rate")
        if best_strategy:
            best_rate = best_strategy["parameters"].get("rate", 0.3)
            
            # Adjust toward best rate
            if best_rate > current_rate:
                return {
                    "action": "increase_spawn_rate",
                    "from": current_rate,
                    "to": min(0.8, current_rate + 0.05),
                    "reason": f"Best historical rate: {best_rate}"
                }
            elif best_rate < current_rate:
                return {
                    "action": "decrease_spawn_rate",
                    "from": current_rate,
                    "to": max(0.1, current_rate - 0.05),
                    "reason": f"Best historical rate: {best_rate}"
                }
        
        return {}
    
    def _optimize_timing(self, analysis: Dict) -> Dict:
        """Optimize revenue timing"""
        optimal = self.memory.get_optimal_timing()
        current_hour = datetime.now().hour
        
        if current_hour not in optimal["best_hours"]:
            next_best = min(optimal["best_hours"], key=lambda h: abs(h - current_hour))
            return {
                "action": "adjust_cycle_frequency",
                "current_hour": current_hour,
                "target_hour": next_best,
                "reason": f"Peak revenue at hours {optimal['best_hours']}"
            }
        
        return {}
    
    def _optimize_healing(self, analysis: Dict) -> Dict:
        """Optimize self-healing strategies"""
        for heal in analysis.get("healing_events", []):
            error = heal.get("error", "unknown")
            best_fix = self.memory.get_best_fix_for_error(error)
            
            if best_fix and best_fix != heal.get("fix", ""):
                return {
                    "action": "update_healing_protocol",
                    "error": error,
                    "old_fix": heal.get("fix", ""),
                    "new_fix": best_fix,
                    "reason": "Better fix found in memory"
                }
        
        return {}
    
    def _optimize_allocation(self, analysis: Dict) -> Dict:
        """Optimize 70% PCRF allocation"""
        pcrf_percent = (analysis["pcrf_sent"] / max(1, analysis["total_revenue"])) * 100
        
        if abs(pcrf_percent - 70) > 5:  # More than 5% off target
            return {
                "action": "rebalance_allocation",
                "current": pcrf_percent,
                "target": 70,
                "adjustment": "increase_pcrf" if pcrf_percent < 70 else "decrease_pcrf",
                "reason": "Maintaining 70% PCRF target"
            }
        
        return {}

if __name__ == "__main__":
    print(f" Revenue Reflection Engine ready")
