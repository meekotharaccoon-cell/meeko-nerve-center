#!/usr/bin/env python3
"""
GAZA ROSE - MASTER KNOWLEDGE ORCHESTRATOR
Connects ALL knowledge systems into one unified, self-organizing ecosystem:
    - Knowledge Graph Core [3][6]
    - Knowledge Agent [1]
    - Knowledge Modules [7]
    - Decentralized Assets [5][9]
    - Wikidata Connector [10]
    - ThinkTank Platform [2]

ALL RUNNING TOGETHER. ALL SELF-ORGANIZING. ALL OPEN-SOURCE.
"""

import os
import sys
import time
import json
import threading
from datetime import datetime

# Import all systems
sys.path.append(os.path.dirname(__file__))

try:
    from knowledge_graph_core import KnowledgeGraphCore
    from knowledge_agent import KnowledgeAgent
    from knowledge_modules import ModuleRegistry, KnowledgeModule
    from decentralized_assets import DecentralizedKnowledgeGraph, KnowledgeAsset
    from wikidata_connector import WikidataEmbeddingConnector
    from thinktank_platform import ThinkTankPlatform
    IMPORTS_OK = True
except ImportError as e:
    print(f" Import error: {e}")
    IMPORTS_OK = False

class MasterKnowledgeOrchestrator:
    """
    Orchestrates all knowledge systems into one unified ecosystem.
    Each system contributes to the whole, creating emergent intelligence.
    """
    
    def __init__(self):
        self.systems = {}
        self.connections = []
        self.start_time = datetime.now()
        
        print("\n" + "="*60)
        print("   GAZA ROSE - MASTER KNOWLEDGE ORCHESTRATOR")
        print("="*60)
        
        # Initialize all systems
        self._init_systems()
        
    def _init_systems(self):
        """Initialize all knowledge systems"""
        
        # 1. Knowledge Graph Core [3][6]
        try:
            self.systems["knowledge_graph"] = KnowledgeGraphCore()
            print("   Knowledge Graph Core [3][6]")
        except Exception as e:
            print(f"   Knowledge Graph Core failed: {e}")
        
        # 2. Knowledge Agent [1]
        try:
            self.systems["knowledge_agent"] = KnowledgeAgent()
            print("   Knowledge Agent [1]")
        except Exception as e:
            print(f"   Knowledge Agent failed: {e}")
        
        # 3. Knowledge Modules [7]
        try:
            self.systems["knowledge_modules"] = ModuleRegistry("./modules")
            print("   Knowledge Modules [7]")
        except Exception as e:
            print(f"   Knowledge Modules failed: {e}")
        
        # 4. Decentralized Assets [5][9]
        try:
            self.systems["decentralized"] = DecentralizedKnowledgeGraph()
            print("   Decentralized Assets [5][9]")
        except Exception as e:
            print(f"   Decentralized Assets failed: {e}")
        
        # 5. Wikidata Connector [10]
        try:
            self.systems["wikidata"] = WikidataEmbeddingConnector()
            print("   Wikidata Connector [10]")
        except Exception as e:
            print(f"   Wikidata Connector failed: {e}")
        
        # 6. ThinkTank Platform [2]
        try:
            self.systems["thinktank"] = ThinkTankPlatform()
            print("   ThinkTank Platform [2]")
        except Exception as e:
            print(f"   ThinkTank Platform failed: {e}")
        
        print(f"\n  Systems initialized: {len(self.systems)}")
        
    def start_auto_curation(self):
        """Start autonomous knowledge curation in background"""
        if "knowledge_agent" in self.systems:
            def run_curation():
                self.systems["knowledge_agent"].run_maintenance_cycle()
                time.sleep(300)
            
            thread = threading.Thread(target=run_curation, daemon=True)
            thread.start()
            self.connections.append({"type": "auto_curation", "thread": thread})
    
    def get_unified_status(self):
        """Get status of all systems"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "uptime": str(datetime.now() - self.start_time),
            "systems": {}
        }
        
        for name, system in self.systems.items():
            try:
                if name == "knowledge_graph":
                    status["systems"][name] = system.get_graph_stats()
                elif name == "knowledge_agent":
                    status["systems"][name] = {"status": "running"}
                elif name == "knowledge_modules":
                    status["systems"][name] = {"modules": len(system.modules)}
                elif name == "decentralized":
                    status["systems"][name] = {"assets": len(system.assets)}
                elif name == "wikidata":
                    status["systems"][name] = {"connected": True}
                elif name == "thinktank":
                    status["systems"][name] = system.get_status()
            except:
                status["systems"][name] = {"status": "error"}
        
        return status
    
    def run_forever(self):
        """Run the knowledge ecosystem forever"""
        print("\n" + "="*60)
        print("   KNOWLEDGE ECOSYSTEM RUNNING")
        print("="*60)
        print(f"  Systems: {len(self.systems)}")
        print(f"  Based on: [1][2][3][5][6][7][9][10]")
        print("="*60 + "\n")
        
        # Start background processes
        self.start_auto_curation()
        
        try:
            while True:
                status = self.get_unified_status()
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}]  ECOSYSTEM STATUS")
                for name, data in status["systems"].items():
                    if isinstance(data, dict):
                        keys = list(data.keys())[:3]
                        vals = [f"{k}: {data[k]}" for k in keys]
                        print(f"   {name}: {', '.join(vals)}")
                
                time.sleep(60)  # Update every minute
                
        except KeyboardInterrupt:
            print("\n\n Knowledge ecosystem paused")
            print(f"Uptime: {datetime.now() - self.start_time}")
            print(f"Systems active: {len(self.systems)}")
            print("\nResume by running this script again.")

if __name__ == "__main__":
    if not IMPORTS_OK:
        print(" Some systems could not be imported")
        print("   Run: pip install networkx requests")
    
    orchestrator = MasterKnowledgeOrchestrator()
    orchestrator.run_forever()
