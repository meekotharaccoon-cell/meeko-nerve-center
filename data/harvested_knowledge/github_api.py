class GitHubAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = 'https://api.github.com'
        self.headers = {'Authorization': f'token {token}'}
    
    def create_repo(self, name, description, public=True):
        data = {
            'name': name,
            'description': description,
            'private': not public,
            'auto_init': True,
            'gitignore_template': 'Python'
        }
        response = requests.post(f'{self.base_url}/user/repos', 
                                 json=data, headers=self.headers)
        return response.json()
    
    def get_rate_limit(self):
        response = requests.get(f'{self.base_url}/rate_limit', headers=self.headers)
        return response.json()['resources']['core']
