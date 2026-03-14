# GAZA ROSE - UNIVERSAL SWARM DIRECTIVE
# This blueprint defines how all your systems connect and collaborate
# Based on multi-agent architecture research [citation:2][citation:3][citation:5]

from matrixswarm.agent import Agent
from matrixswarm.directive import Directive
import os

class GazaRoseUniversalDirective(Directive):
    """
    Master directive that orchestrates every system on Meeko's desktop.
    Agents communicate via files, resurrect each other, and self-heal [citation:9].
    """
    
    def build(self):
        # ==============================================
        # ROOT AGENT - The Orchestrator [citation:7][citation:8]
        # ==============================================
        root = self.create_agent(
            name="Orchestrator",
            agent_type="coordinator",
            config={
                "model": "deepseek-r1:8b",  # Local reasoning model [citation:7]
                "role": "principal_synthesizer",
                "description": "Coordinates all swarm activities"
            }
        )
        
        # ==============================================
        # DISCOVERED AGENTS - Auto-registered from your system
        # ==============================================
        # Ultimate Pipeline - Pipeline Orchestrator
        AGENT_8 = self.create_agent(
            name="Ultimate Pipeline",
            agent_type="worker",
            executable=r"C:\Users\meeko\Desktop\GAZA_ROSE_PIPELINE",
            command="python orchestrator.py",
            parent=root,
            config={
                "description": "Pipeline Orchestrator",
                "watchdog": True,  # Auto-resurrect if dies [citation:9]
                "communication": "file-based"
            }
        )
                 # Continuation Protocol - Universal Connector
        AGENT_5 = self.create_agent(
            name="Continuation Protocol",
            agent_type="worker",
            executable=r"C:\Users\meeko\Desktop\GAZA_ROSE_CONTINUATION",
            command="python universal_connector.py",
            parent=root,
            config={
                "description": "Universal Connector",
                "watchdog": True,  # Auto-resurrect if dies [citation:9]
                "communication": "file-based"
            }
        )
                 # Watchdog - Self-Healing Watcher
        AGENT_7 = self.create_agent(
            name="Watchdog",
            agent_type="worker",
            executable=r"C:\Users\meeko\Desktop\GAZA_ROSE_WATCHDOG",
            command="python self_healing_watcher.py",
            parent=root,
            config={
                "description": "Self-Healing Watcher",
                "watchdog": True,  # Auto-resurrect if dies [citation:9]
                "communication": "file-based"
            }
        )
                 # Verification Suite - System Verifier
        AGENT_4 = self.create_agent(
            name="Verification Suite",
            agent_type="worker",
            executable=r"C:\Users\meeko\Desktop\GAZA_ROSE_VERIFICATION",
            command="python master_verifier.py",
            parent=root,
            config={
                "description": "System Verifier",
                "watchdog": True,  # Auto-resurrect if dies [citation:9]
                "communication": "file-based"
            }
        )
                 # AutoGPT - Autonomous GPT Agent
        AGENT_1 = self.create_agent(
            name="AutoGPT",
            agent_type="worker",
            executable=r"C:\Users\meeko\autogpt",
            command="python -m autogpt --agent gaza_rose_agent",
            parent=root,
            config={
                "description": "Autonomous GPT Agent",
                "watchdog": True,  # Auto-resurrect if dies [citation:9]
                "communication": "file-based"
            }
        )
                 # Knowledge Base - Knowledge Broadcaster
        AGENT_6 = self.create_agent(
            name="Knowledge Base",
            agent_type="worker",
            executable=r"C:\Users\meeko\Desktop\GAZA_ROSE_KNOWLEDGE",
            command="python broadcast_knowledge.py",
            parent=root,
            config={
                "description": "Knowledge Broadcaster",
                "watchdog": True,  # Auto-resurrect if dies [citation:9]
                "communication": "file-based"
            }
        )
                 # Self-Healing Ecosystem - Meta Healer
        AGENT_3 = self.create_agent(
            name="Self-Healing Ecosystem",
            agent_type="worker",
            executable=r"C:\Users\meeko\Desktop\GAZA_ROSE_SELF_HEALING_ECOSYSTEM",
            command="python meta_healer.py",
            parent=root,
            config={
                "description": "Meta Healer",
                "watchdog": True,  # Auto-resurrect if dies [citation:9]
                "communication": "file-based"
            }
        )
                 # Force Bot - Trading Bot
        AGENT_2 = self.create_agent(
            name="Force Bot",
            agent_type="worker",
            executable=r"C:\Users\meeko\Desktop\GAZA_ROSE_FORCE_BOT",
            command="node index.js",
            parent=root,
            config={
                "description": "Trading Bot",
                "watchdog": True,  # Auto-resurrect if dies [citation:9]
                "communication": "file-based"
            }
        )
        
        # ==============================================
        # SPECIALIZED SWARM ROLES [citation:2][citation:5][citation:7]
        # ==============================================
        critical_thinker = self.create_agent(
            name="CriticalThinker",
            agent_type="validator",
            model="phi4-mini",  # Lightweight validator [citation:7]
            parent=root,
            config={
                "role": "fact_validator",
                "description": "Validates all agent outputs"
            }
        )
        
        quality_auditor = self.create_agent(
            name="QualityAuditor",
            agent_type="auditor",
            model="phi4-mini",  # Output assessor [citation:7]
            parent=root,
            config={
                "role": "quality_auditor",
                "description": "Assesses output quality"
            }
        )
        
        domain_expert = self.create_agent(
            name="DomainExpert",
            agent_type="specialist",
            model="qwen3:8b",  # Domain analysis [citation:7]
            parent=root,
            config={
                "role": "domain_specialist",
                "description": "Expert analysis on all tasks"
            }
        )
        
        # ==============================================
        # SWARM RULES - How agents interact [citation:3][citation:10]
        # ==============================================
        self.add_rule("orchestrator_to_all", root, "broadcast", "coordinate")
        self.add_rule("critical_review", critical_thinker, "audit", "all")
        self.add_rule("quality_check", quality_auditor, "assess", "all")
        self.add_rule("domain_insight", domain_expert, "analyze", "all")
        
        # Self-healing rules: agents monitor each other [citation:9]
        self.add_watchdog(root, "all", interval=30)  # Check every 30 seconds
        
        return root

# ==============================================
# SWARM INITIALIZATION
# ==============================================
directive = GazaRoseUniversalDirective()
__all__ = ['directive']
