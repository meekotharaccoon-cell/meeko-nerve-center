class FederatedLearningLayer:
    def __init__(self):
        self.local_models = {}
        self.global_model = None
    
    def aggregate(self, sample_ratio=0.3):
        selected = random.sample(list(self.local_models.keys()), 
                                 int(len(self.local_models) * sample_ratio))
        for key in self.global_model:
            self.global_model[key] = sum(
                self.local_models[a]['weights'][key] for a in selected
            ) / len(selected)
        for agent in self.local_models:
            if random.random() < 0.5:
                self.local_models[agent]['weights'] = self.global_model.copy()
