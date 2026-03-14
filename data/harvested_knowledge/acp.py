class ACPProtocol:
    def __init__(self):
        self.services = {}
        self.transactions = []
    
    def register_service(self, service):
        self.services[service.id] = service
        return service.id
