class RoxSwarm:
    def __init__(self):
        self.knowledge_graph = UnifiedKnowledgeGraph()
        self.swarms = {
            'research': ResearchSwarm(),
            'outreach': OutreachSwarm(),
            'opportunity': OpportunitySwarm(),
            'proposal': ProposalSwarm()
        }
    
    def process_request(self, request):
        plan = self.decompose_request(request)
        results = {}
        for step in plan:
            results[step.id] = self.swarms[step.type].execute(step)
        return self.synthesize(results)
