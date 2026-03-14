class SaaStrPlaybook:
    def __init__(self):
        self.agents = {
            'sdr': ArtisanAgent(response_rate=0.07),
            'bdr': QualifiedAgent(deal_size=85000),
            'advisor': DelphiAgent(conversations=139000),
            'collateral': GammaAgent(creation_time=10),
            'revops': MomentumAgent(auto_transcribe=True),
            'reviewer': ReplitAgent(cost_savings=180000)
        }
