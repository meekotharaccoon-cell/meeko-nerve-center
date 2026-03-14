class IndirectIncentiveEngine:
    def calculate_incentive(self, contribution, network_activity):
        base = self.params['base_reward'] * contribution
        network_bonus = self.params['network_multiplier'] * network_activity
        return base + network_bonus
