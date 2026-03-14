class NetworkEffectsAmplifier:
    def calculate_multiplier(self, connections):
        # Metcalfe's Law: value  n
        return connections * math.log(connections + 1) / 10
