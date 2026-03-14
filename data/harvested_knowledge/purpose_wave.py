class PurposeWaveFunction:
    def __init__(self):
        self.pcrf_address = '"https://give.pcrf.net/campaign/739651/donate"'
        self.allocation = 0.7
        self.harmonics = {
            'primary': {'frequency': 1.0, 'description': 'PCRF aid'},
            'secondary': {'frequency': 0.5, 'description': 'Sustainability'},
            'tertiary': {'frequency': 0.25, 'description': 'Knowledge'}
        }
    
    def resonate_with_purpose(self, operation):
        pcrf_resonance = 1.0 if operation.get('bitcoin_address') == self.pcrf_address else 0.0
        humanitarian_resonance = 1.0 if operation.get('humanitarian_purpose') else 0.0
        return pcrf_resonance * 0.7 + humanitarian_resonance * 0.3
