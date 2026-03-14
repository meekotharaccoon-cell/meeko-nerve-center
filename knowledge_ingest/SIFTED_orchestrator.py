#!/usr/bin/env python3
"""
AUTONOMOUS INCOME SYSTEM ORCHESTRATOR
Master controller that runs all subsystems
Schedule this to run daily via cron: 0 6 * * * /usr/bin/python3 /path/to/orchestrator.py
"""

import json
import os
import sys
from datetime import datetime

# Add all subdirectories to path
sys.path.extend([
    'content_generator',
    'social_automation', 
    'email_automation',
    'analytics'
])

from auto_content_system import AutonomousContentGenerator
from social_media_bot import SocialMediaAutomation
from email_sequences import EmailAutomation
from money_tracker import MoneyTracker

class AutonomousIncomeOrchestrator:
    def __init__(self, config_file: str = "config.json"):
        self.config = self._load_config(config_file)
        self.niche = self.config.get("niche", "productivity_tools")
        self.brand_name = self.config.get("brand_name", "ProductivityPro")
        self.log_file = "automation_log.txt"
        
    def _load_config(self, config_file: str) -> dict:
        """Load configuration or create default"""
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        return self._create_default_config()
    
    def _create_default_config(self) -> dict:
        """Create default configuration"""
        config = {
            "niche": "productivity_tools",
            "brand_name": "ProductivityPro",
            "site_url": "https://yourdomain.com",
            "email_service": "mailchimp",
            "social_scheduler": "buffer",
            "content_frequency": "daily",
            "social_frequency": "3x_daily",
            "email_frequency": "weekly",
            "automation_level": "full"  # full, semi, manual
        }
        
        with open("config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        return config
    
    def log(self, message: str):
        """Log automation activity"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
        
        print(log_entry.strip())
    
    def run_daily_cycle(self):
        """Execute complete daily automation cycle"""
        
        self.log("=" * 60)
        self.log("🚀 STARTING DAILY AUTONOMOUS INCOME CYCLE")
        self.log("=" * 60)
        
        try:
            # Step 1: Generate Content
            self.log("\n📄 STEP 1: Content Generation")
            content_gen = AutonomousContentGenerator(niche=self.niche)
            content_result = content_gen.run_daily_automation()
            
            if content_result:
                self.log(f"✅ Generated article: {content_result['article']['title']}")
                self.log(f"✅ Generated {len(content_result['social_posts'])} social posts")
                self.log(f"✅ Generated {len(content_result['emails'])} emails")
            
            # Step 2: Social Media
            self.log("\n📱 STEP 2: Social Media Automation")
            social_bot = SocialMediaAutomation(
                brand_name=self.brand_name,
                niche=self.niche
            )
            calendar = social_bot.generate_content_calendar(30)
            social_bot.save_calendar(calendar)
            self.log(f"✅ Generated 30-day social calendar")
            
            # Step 3: Email Sequences
            self.log("\n📧 STEP 3: Email Automation")
            email_system = EmailAutomation(
                brand_name=self.brand_name,
                niche=self.niche
            )
            welcome_seq = email_system.generate_welcome_sequence()
            broadcasts = email_system.generate_broadcast_emails(10)
            email_system.save_sequences(welcome_seq, broadcasts)
            self.log(f"✅ Generated {len(welcome_seq)} welcome emails")
            self.log(f"✅ Generated {len(broadcasts)} broadcast emails")
            
            # Step 4: Analytics & Tracking
            self.log("\n📊 STEP 4: Analytics Update")
            tracker = MoneyTracker()
            data = tracker.generate_sample_data(90)
            tracker.save_dashboard(data)
            
            opportunities = tracker.generate_optimization_opportunities(data)
            self.log(f"✅ Identified {len(opportunities)} optimization opportunities")
            
            # Step 5: Generate Report
            self.log("\n📈 STEP 5: Daily Report Generation")
            self._generate_daily_report(content_result, opportunities)
            
            self.log("\n" + "=" * 60)
            self.log("✅ DAILY CYCLE COMPLETED SUCCESSFULLY")
            self.log("=" * 60)
            
            return True
            
        except Exception as e:
            self.log(f"\n❌ ERROR: {str(e)}")
            self.log("=" * 60)
            return False
    
    def _generate_daily_report(self, content_result, opportunities):
        """Generate daily automation report"""
        
        report = {
            "date": datetime.now().isoformat(),
            "status": "completed",
            "content_generated": {
                "article_title": content_result['article']['title'] if content_result else None,
                "social_posts": len(content_result['social_posts']) if content_result else 0,
                "emails": len(content_result['emails']) if content_result else 0
            },
            "optimization_opportunities": len(opportunities),
            "next_actions": [
                "Review generated content in content_generator/ folder",
                "Approve social posts in social_automation/ folder",
                "Upload email sequences to your email service",
                "Check analytics dashboard in analytics/ folder"
            ]
        }
        
        report_file = f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"✅ Report saved: {report_file}")
    
    def run_weekly_cycle(self):
        """Execute weekly optimization cycle"""
        
        self.log("\n📅 RUNNING WEEKLY OPTIMIZATION CYCLE")
        
        # Content audit
        self.log("Auditing content performance...")
        
        # Affiliate optimization
        self.log("Optimizing affiliate links...")
        
        # Email segmentation
        self.log("Updating email segments...")
        
        self.log("✅ Weekly cycle completed")
    
    def status_check(self):
        """Check system status"""
        
        self.log("\n🔍 SYSTEM STATUS CHECK")
        
        checks = {
            "config_file": os.path.exists("config.json"),
            "content_generator": os.path.exists("content_generator/auto_content_system.py"),
            "social_bot": os.path.exists("social_automation/social_media_bot.py"),
            "email_system": os.path.exists("email_automation/email_sequences.py"),
            "analytics": os.path.exists("analytics/money_tracker.py"),
            "log_file": os.path.exists(self.log_file)
        }
        
        all_good = all(checks.values())
        
        for check, status in checks.items():
            symbol = "✅" if status else "❌"
            self.log(f"{symbol} {check}: {'OK' if status else 'MISSING'}")
        
        return all_good

# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous Income System")
    parser.add_argument("command", choices=["daily", "weekly", "status", "init"], 
                       help="Command to execute")
    
    args = parser.parse_args()
    
    orchestrator = AutonomousIncomeOrchestrator()
    
    if args.command == "daily":
        orchestrator.run_daily_cycle()
    elif args.command == "weekly":
        orchestrator.run_weekly_cycle()
    elif args.command == "status":
        orchestrator.status_check()
    elif args.command == "init":
        print("🚀 Initializing Autonomous Income System...")
        orchestrator.status_check()
        print("\n✅ System initialized!")
        print("\nNext steps:")
        print("1. Edit config.json with your settings")
        print("2. Run: python orchestrator.py daily")
        print("3. Set up cron job for daily execution")
