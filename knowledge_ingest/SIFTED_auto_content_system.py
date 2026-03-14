#!/usr/bin/env python3
"""
AUTONOMOUS CONTENT GENERATION SYSTEM
Generates SEO-optimized articles, social posts, and emails automatically
Run this daily via cron job or scheduler
"""

import json
import random
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import os

class AutonomousContentGenerator:
    def __init__(self, niche: str, api_key: str = None):
        self.niche = niche
        self.api_key = api_key
        self.content_calendar = []
        
    def generate_article_ideas(self, count: int = 30) -> List[Dict]:
        """Generate 30 days of article ideas autonomously"""
        
        templates = [
            "Best {product} for {audience} in 2026",
            "{product} vs {competitor}: Complete Comparison",
            "How to {action} with {product} (Step-by-Step)",
            "{number} {product} Hacks That Will Save You {benefit}",
            "Why {audience} Are Switching to {product}",
            "{product} Review: Is It Worth It?",
            "The Ultimate Guide to {topic} for Beginners",
            "{number} Mistakes to Avoid When Buying {product}",
            "How I {achievement} Using Only {product}",
            "{product} Buying Guide: What Experts Don't Tell You"
        ]
        
        # Niche-specific variables (auto-populated based on niche)
        niche_data = self._get_niche_data()
        
        ideas = []
        for i in range(count):
            template = random.choice(templates)
            idea = {
                "title": template.format(**self._fill_template_vars(niche_data)),
                "keyword": self._extract_keyword(template, niche_data),
                "type": "review" if "best" in template.lower() else "guide",
                "publish_date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                "status": "pending"
            }
            ideas.append(idea)
            
        self.content_calendar = ideas
        return ideas
    
    def _get_niche_data(self) -> Dict:
        """Auto-configure based on selected niche"""
        niches = {
            "productivity_tools": {
                "product": ["Notion", "Asana", "ClickUp", "Trello", "Monday.com"],
                "audience": ["freelancers", "remote workers", "small teams", "solopreneurs"],
                "action": ["organize your life", "manage projects", "track habits", "automate workflows"],
                "topic": ["project management", "time blocking", "habit tracking", "goal setting"],
                "achievement": ["doubled my productivity", "organized my entire business", "eliminated 10 hours of busywork"],
                "benefit": ["10 hours/week", "$1000/month", "your sanity"],
                "competitor": ["Notion vs Asana", "ClickUp vs Monday", "Trello vs Asana"],
                "number": ["7", "10", "15", "21"]
            },
            "home_fitness": {
                "product": ["resistance bands", "adjustable dumbbells", "pull-up bar", "yoga mat", "kettlebell"],
                "audience": ["busy professionals", "apartment dwellers", "beginners", "people over 40"],
                "action": ["build muscle at home", "lose weight without gym", "get ripped", "stay consistent"],
                "topic": ["home workouts", "strength training", "HIIT", "flexibility"],
                "achievement": ["lost 30 pounds", "built visible muscle", "eliminated back pain"],
                "benefit": ["hundreds on gym fees", "2 hours/day", "your excuses"],
                "competitor": ["Bowflex vs PowerBlock", "TRX vs resistance bands"],
                "number": ["5", "8", "12", "20"]
            },
            "smart_home": {
                "product": ["smart thermostat", "video doorbell", "smart lights", "security camera", "smart lock"],
                "audience": ["homeowners", "renters", "tech beginners", "security-conscious families"],
                "action": ["automate your home", "save on energy bills", "secure your property", "control everything remotely"],
                "topic": ["home automation", "energy efficiency", "home security", "IoT setup"],
                "achievement": ["cut energy bills by 40%", "never worry about security", "automated my entire house"],
                "benefit": ["$500/year", "peace of mind", "hours of manual work"],
                "competitor": ["Nest vs Ecobee", "Ring vs Arlo", "Philips Hue vs LIFX"],
                "number": ["6", "9", "14", "18"]
            }
        }
        return niches.get(self.niche, niches["productivity_tools"])
    
    def _fill_template_vars(self, data: Dict) -> Dict:
        """Randomly select values for template variables"""
        return {k: random.choice(v) if isinstance(v, list) else v for k, v in data.items()}
    
    def _extract_keyword(self, template: str, data: Dict) -> str:
        """Extract target keyword from template"""
        filled = self._fill_template_vars(data)
        # Simplified keyword extraction
        return filled.get("product", "product review").lower()
    
    def generate_full_article(self, idea: Dict) -> Dict:
        """Generate complete SEO-optimized article"""
        
        article_structure = {
            "title": idea["title"],
            "meta_description": f"Discover everything about {idea['keyword']} in this comprehensive guide. Expert reviews, comparisons, and buying advice.",
            "word_count_target": 2000,
            "sections": [
                {"heading": "Introduction", "word_count": 200, "content_type": "hook_problem_solution"},
                {"heading": "Quick Summary (TL;DR)", "word_count": 150, "content_type": "bullet_summary"},
                {"heading": f"What is {idea['keyword'].title()}?", "word_count": 300, "content_type": "explanation"},
                {"heading": f"Top 5 {idea['keyword'].title()} Options Compared", "word_count": 600, "content_type": "product_comparison"},
                {"heading": "Key Features to Look For", "word_count": 300, "content_type": "buying_guide"},
                {"heading": "Pros and Cons", "word_count": 200, "content_type": "pros_cons"},
                {"heading": "Who Should Buy This?", "word_count": 150, "content_type": "target_audience"},
                {"heading": "Final Verdict", "word_count": 100, "content_type": "conclusion"}
            ],
            "affiliate_links": self._generate_affiliate_links(idea["keyword"]),
            "images_needed": ["hero_image", "product_comparison_chart", "feature_infographic"],
            "publish_date": idea["publish_date"]
        }
        
        return article_structure
    
    def _generate_affiliate_links(self, keyword: str) -> List[Dict]:
        """Generate affiliate link placeholders"""
        return [
            {"platform": "amazon", "product": f"Best {keyword.title()}", "link": f"[AMAZON_LINK_{keyword.upper()}]"},
            {"platform": "shareasale", "product": f"Premium {keyword.title()}", "link": f"[SHAREASALE_LINK_{keyword.upper()}]"}
        ]
    
    def generate_social_posts(self, article: Dict) -> List[Dict]:
        """Generate social media posts from article"""
        posts = [
            {
                "platform": "twitter",
                "content": f"🧵 Thread: {article['title']}\n\nI spent 20 hours researching so you don't have to.\n\nHere are the key findings:\n\n[1/5] 🧵",
                "post_time": "09:00",
                "hashtags": ["#ProductReview", "#BuyingGuide", f"#{self.niche.replace('_', '')}"]
            },
            {
                "platform": "linkedin",
                "content": f"Just published: {article['title']}\n\nAfter testing 15+ options, here's what actually works (and what doesn't).\n\nFull breakdown in comments 👇",
                "post_time": "12:00",
                "hashtags": ["#Productivity", "#TechReview", "#Recommendations"]
            },
            {
                "platform": "pinterest",
                "content": f"{article['title']} - Save this guide!",
                "image_type": "infographic",
                "post_time": "19:00"
            }
        ]
        return posts
    
    def generate_email_sequence(self, article: Dict) -> List[Dict]:
        """Generate email nurture sequence"""
        emails = [
            {
                "subject": f"Your {article['title']} guide is ready",
                "send_delay": "immediate",
                "content_type": "value_delivery",
                "cta": "Read the full guide"
            },
            {
                "subject": "Did you see this comparison?",
                "send_delay": "2_days",
                "content_type": "follow_up",
                "cta": "See the comparison"
            },
            {
                "subject": f"Last chance: Best {article['title']} deals",
                "send_delay": "5_days",
                "content_type": "urgency",
                "cta": "Get the deal"
            }
        ]
        return emails
    
    def run_daily_automation(self):
        """Main automation loop - call this daily"""
        print(f"🤖 Starting autonomous content generation for: {self.niche}")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Generate ideas if none exist
        if not self.content_calendar:
            self.generate_article_ideas(30)
            print(f"📅 Generated 30 article ideas")
        
        # Find today's article
        today = datetime.now().strftime("%Y-%m-%d")
        today_idea = next((idea for idea in self.content_calendar if idea["publish_date"] == today), None)
        
        if today_idea:
            print(f"📝 Generating article: {today_idea['title']}")
            article = self.generate_full_article(today_idea)
            social_posts = self.generate_social_posts(article)
            emails = self.generate_email_sequence(article)
            
            output = {
                "article": article,
                "social_posts": social_posts,
                "emails": emails,
                "generated_at": datetime.now().isoformat()
            }
            
            # Save to file
            import os
            output_dir = os.path.dirname(os.path.abspath(__file__))
            filename = f"{output_dir}/output_{today}.json"
            with open(filename, 'w') as f:
                json.dump(output, f, indent=2)
            
            print(f"✅ Content saved to: {filename}")
            return output
        else:
            print("ℹ️ No article scheduled for today")
            return None

# Usage
if __name__ == "__main__":
    # Initialize with your chosen niche
    generator = AutonomousContentGenerator(niche="productivity_tools")
    generator.run_daily_automation()
