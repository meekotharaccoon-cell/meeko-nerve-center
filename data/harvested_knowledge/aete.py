class AETEEngine:
    def __init__(self):
        self.agents = {
            'maia': MarketAudienceInsightAgent(),
            'csca': ContentStrategyAgent(),
            'mcga': MultiPlatformContentAgent(),
            'paaa': PerformanceAttributionAgent()
        }
        self.q_table = {}
    
    def run_campaign(self, product):
        insights = self.agents['maia'].analyze(product)
        strategy = self.agents['csca'].select_action(insights)
        content = self.agents['mcga'].generate(strategy)
        performance = self.deploy(content)
        roi = self.agents['paaa'].calculate(performance)
        self.update_q_table(insights, strategy, roi)
        return {'roi': roi, 'strategy': strategy}
