"""
CrewAI -> UltimateAI Master Bridge
Connects the CrewAI multi-agent system directly into the master knowledge base
"""
import sys
import os
import json
from datetime import datetime

# Add mycelium_env to path
sys.path.insert(0, r'C:\Users\meeko\Desktop\mycelium_env\Lib\site-packages')

from crewai import Agent, Task, Crew, LLM

# Connect to master knowledge base
knowledge_path = r'C:\Users\meeko\Desktop\UltimateAI_Master\knowledge'
os.makedirs(knowledge_path, exist_ok=True)

llm = LLM(model='ollama/mistral', base_url='http://localhost:11434')

researcher = Agent(
    role='System Researcher',
    goal='Analyze the UltimateAI Master system and identify the single best next evolution',
    backstory='Expert at analyzing self-evolving AI systems and finding growth opportunities',
    llm=llm,
    verbose=True
)

builder = Agent(
    role='System Builder',
    goal='Write exact executable code to implement the next evolution',
    backstory='You write Python and PowerShell that works first time',
    llm=llm,
    verbose=True
)

research_task = Task(
    description='''The UltimateAI Master v15 has: self-healing, evolution cycles, Gaza Rose revenue 
    with 70% to PCRF, subsystem manager, GitHub integration, knowledge base, scheduler, backup recovery.
    It just evolved to v15.0.1. What single addition makes it most powerful next?''',
    agent=researcher,
    expected_output='Specific recommendation with clear reasoning'
)

build_task = Task(
    description='Write the exact Python code and any pip install commands to implement the recommendation',
    agent=builder,
    expected_output='Ready to run code and commands'
)

crew = Crew(agents=[researcher, builder], tasks=[research_task, build_task], verbose=True)
result = crew.kickoff()

# Save directly to master knowledge base
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
knowledge_file = os.path.join(knowledge_path, f'crew_evolution_{timestamp}.json')

knowledge_entry = {
    'timestamp': timestamp,
    'source': 'CrewAI_Bridge',
    'type': 'evolution_recommendation',
    'content': str(result)
}

with open(knowledge_file, 'w') as f:
    json.dump(knowledge_entry, f, indent=2)

print(f'\n=== SAVED TO MASTER KNOWLEDGE BASE ===')
print(f'File: {knowledge_file}')
print(f'\n=== CREW RECOMMENDATION ===')
print(result)
