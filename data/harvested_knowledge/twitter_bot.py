import tweepy, json, time, random
from datetime import datetime

class SolarPunkTwitterBot:
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            config = json.load(f)["twitter"]
        
        self.client = tweepy.Client(
            consumer_key=config["api_key"],
            consumer_secret=config["api_secret"],
            access_token=config["access_token"],
            access_token_secret=config["access_secret"],
            bearer_token=config["bearer_token"]
        )
        
        self.auth = tweepy.OAuth1UserHandler(
            config["api_key"],
            config["api_secret"],
            config["access_token"],
            config["access_secret"]
        )
        self.api = tweepy.API(self.auth)
        
        print("🐦 SolarPunk Twitter Bot Started")
    
    def post_tweet(self):
        tweets = [
            "🚀 SolarPunk autonomous system update: Self-optimizing across 30 GitHub repositories. #OpenSource #Automation",
            "🌍 Regenerative finance in action: Open-source systems creating humanitarian impact. #SolarPunk #EthicalTech",
            "📈 Decentralized networks are more resilient. Our autonomous system demonstrates this daily. #Decentralization",
            "💻 Just pushed new community governance features. Open-source development creates better systems. #GitHub",
            "🤖 Autonomous systems don't sleep, don't get tired, and continuously improve. The future of technology. #AI"
        ]
        
        try:
            tweet = random.choice(tweets)
            self.client.create_tweet(text=tweet)
            print(f"[{datetime.now()}] Tweeted: {tweet[:60]}...")
        except Exception as e:
            print(f"Tweet failed: {e}")
    
    def run(self):
        while True:
            self.post_tweet()
            time.sleep(14400)  # 4 hours

if __name__ == "__main__":
    bot = SolarPunkTwitterBot()
    bot.run()
