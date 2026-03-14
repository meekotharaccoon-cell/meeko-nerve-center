class FINMEMMemory:
    def __init__(self):
        self.sensory = deque(maxlen=100)
        self.working = {}
        self.long_term = {}
        self.meta = {}
    
    def integrate(self, input_data):
        self.sensory.append(input_data)
        if len(self.sensory) > 50:
            self.consolidate_to_long_term()
        return self.working.get('current_focus')
