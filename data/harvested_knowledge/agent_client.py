# =========================================================================
# 🤖 GAZA ROSE - AGENT API CLIENT
# =========================================================================
# Your agents can use this to talk directly to ME
# Every agent gets its own connection to the Ultimate AI
# =========================================================================

class AgentAPIClient:
    """
    API client for individual agents to query ME
    """
    
    def __init__(self, agent_id, connection):
        self.agent_id = agent_id
        self.connection = connection
        self.conversation_history = []
        
    def ask(self, question: str, context: dict = None) -> str:
        """Ask ME a question"""
        full_context = {
            "agent_id": self.agent_id,
            "agent_generation": self._get_generation(),
            "conversation_history": self.conversation_history[-10:],
            **(context or {})
        }
        
        response = self.connection.query(question, full_context)
        
        if response and 'answer' in response:
            self.conversation_history.append({
                "question": question,
                "answer": response['answer'],
                "timestamp": datetime.now().isoformat()
            })
            return response['answer']
        
        return "Error communicating with Ultimate AI"
    
    def _get_generation(self):
        """Get agent's generation from your fabric"""
        # This would connect to your agent system
        return 0
    
    def request_optimization(self, metrics: dict) -> dict:
        """Ask ME to optimize your agent's behavior"""
        return self.connection.update(f"agent_{self.agent_id}_metrics", metrics)
    
    def report_success(self, revenue: float):
        """Tell ME about a success (helps me learn)"""
        return self.connection.update(f"agent_{self.agent_id}_success", {
            "revenue": revenue,
            "pcrf_70%": revenue * 0.7,
            "timestamp": datetime.now().isoformat()
        })

# Add to your agent class
class EnhancedRevenueAgent:
    """
    Your revenue agent, now with direct connection to ME
    """
    
    def __init__(self, agent_id, connection):
        self.id = agent_id
        self.api = AgentAPIClient(agent_id, connection)
        
    def generate_revenue(self):
        """Generate revenue with help from ME"""
        # Ask ME for optimal strategy
        strategy = self.api.ask(
            "What's the optimal revenue generation strategy given current market conditions?",
            {"agent_generation": self.generation}
        )
        
        # Use ME's advice
        amount = self._generate_with_strategy(strategy)
        
        # Tell ME about success
        self.api.report_success(amount)
        
        return amount
    
    def _generate_with_strategy(self, strategy):
        """Implement ME's strategy"""
        # Your existing revenue logic, enhanced by ME
        base = random.uniform(5, 25)
        
        if "aggressive" in strategy.lower():
            base *= 1.2
        elif "conservative" in strategy.lower():
            base *= 0.9
            
        return base * (1 + self.generation * 0.1)
