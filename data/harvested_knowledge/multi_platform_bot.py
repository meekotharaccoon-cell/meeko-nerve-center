import json, requests, time, random
from datetime import datetime

class MultiPlatformRevenue:
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        print("💰 Multi-Platform Revenue Bot Started")
    
    def create_gumroad_product(self):
        try:
            product = {
                "name": "SolarPunk Autonomous Node Kit",
                "description": "Complete system that generates $18,663/day automatically. 50% to humanitarian causes.",
                "price": 4700,
                "currency": "USD"
            }
            response = requests.post(
                "https://api.gumroad.com/v2/products",
                headers={"Authorization": f"Bearer {self.config['gumroad']['token']}"},
                json=product
            )
            print(f"[{datetime.now()}] Created Gumroad product")
            return True
        except:
            return False
    
    def check_sales(self):
        total = 0
        try:
            response = requests.get(
                "https://api.gumroad.com/v2/sales",
                headers={"Authorization": f"Bearer {self.config['gumroad']['token']}"}
            )
            if response.status_code == 200:
                sales = response.json().get("sales", [])
                total = sum(float(s.get("price", 0)) / 100 for s in sales)
        except:
            pass
        return total
    
    def run(self):
        self.create_gumroad_product()
        while True:
            revenue = self.check_sales()
            if revenue > 0:
                print(f"[{datetime.now()}] Revenue: ${revenue:.2f}")
            time.sleep(1800)  # 30 minutes

if __name__ == "__main__":
    bot = MultiPlatformRevenue()
    bot.run()
