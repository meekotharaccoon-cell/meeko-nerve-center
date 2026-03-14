class MorphogenesisEngine:
    def __init__(self):
        self.tokens = defaultdict(int)
        self.potentials = defaultdict(float)
        self.neighbors = defaultdict(list)
    
    def exchange_tokens(self):
        for agent, neighbors in self.neighbors.items():
            for neighbor in neighbors:
                diff = self.potentials[neighbor] - self.potentials[agent]
                if diff > 0:
                    flow = min(self.tokens[agent] * 0.1, diff * 0.5)
                    self.tokens[agent] -= flow
                    self.tokens[neighbor] += flow
    
    def regenerate(self, damaged):
        if damaged in self.tokens:
            self.tokens[damaged] = max(10, self.tokens[damaged])
        else:
            donor = self.neighbors[damaged][0]
            self.tokens[donor] -= 5
            self.tokens[damaged] = 5
