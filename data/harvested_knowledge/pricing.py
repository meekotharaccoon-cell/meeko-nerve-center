class CompetingPricingEngine:
    def __init__(self):
        self.agents = {
            'margin': MarginMaximizerAgent(),
            'volume': VolumeOptimizerAgent(),
            'loyalty': CustomerLoyaltyAgent(),
            'competitive': CompetitiveAgent()
        }
    
    def determine_price(self, product):
        recommendations = {}
        for name, agent in self.agents.items():
            recommendations[name] = agent.propose_price(product)
        return self.coordinate(recommendations)
