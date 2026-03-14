class RevenueAgent:
    def __init__(self, agent_id, generation=0):
        self.id = agent_id
        self.generation = generation
        self.revenue = 0
        self.children = []
    
    def generate_revenue(self):
        amount = random.uniform(5, 25) * (1 + self.generation * 0.1)
        self.revenue += amount
        return amount
    
    def allocate(self, amount):
        pcrf = amount * 0.7
        reinvest = amount * 0.3
        return pcrf, reinvest
