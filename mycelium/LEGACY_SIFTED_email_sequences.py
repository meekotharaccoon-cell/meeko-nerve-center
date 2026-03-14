#!/usr/bin/env python3
"""
AUTONOMOUS EMAIL MARKETING SYSTEM
Generates complete email sequences, nurtures, and broadcasts
Integrates with Mailchimp, ConvertKit, or ActiveCampaign
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict

class EmailAutomation:
    def __init__(self, brand_name: str, niche: str):
        self.brand_name = brand_name
        self.niche = niche
        
    def generate_welcome_sequence(self) -> List[Dict]:
        """Generate 7-email welcome sequence"""
        
        sequence = [
            {
                "email_number": 1,
                "delay": "immediate",
                "subject": "Welcome to {brand_name} - Here's your free guide",
                "preview_text": "The productivity system that changed everything...",
                "content_type": "value_delivery",
                "body_template": """
                <h1>Welcome to the community!</h1>
                <p>Hi {{first_name}},</p>
                <p>Thanks for joining {brand_name}. I'm excited to help you transform your productivity.</p>
                <p><strong>Here's your promised guide:</strong> <a href="[DOWNLOAD_LINK]">Download the Productivity Toolkit</a></p>
                <p>Over the next week, I'll share:</p>
                <ul>
                    <li>The exact system I use to manage 5 projects simultaneously</li>
                    <li>Automation scripts that save 10+ hours/week</li>
                    <li>My favorite tools (most are free)</li>
                </ul>
                <p>Talk soon,<br>{brand_name} Team</p>
                """,
                "cta": "Download Your Free Guide",
                "affiliate_links": []
            },
            {
                "email_number": 2,
                "delay": "1_day",
                "subject": "The $5,000 mistake most people make",
                "preview_text": "I made this mistake for 3 years before figuring it out...",
                "content_type": "story",
                "body_template": """
                <p>Hi {{first_name}},</p>
                <p>Three years ago, I was working 80-hour weeks and barely making ends meet.</p>
                <p>I thought the answer was to work harder. Buy more tools. Learn more skills.</p>
                <p><strong>I was wrong.</strong></p>
                <p>The breakthrough came when I realized I was solving the wrong problem.</p>
                <p>I didn't need to do MORE. I needed to do LESS, but better.</p>
                <p>Specifically, I needed to:</p>
                <ol>
                    <li>Eliminate 80% of my tasks (Pareto Principle)</li>
                    <li>Automate everything repetitive</li>
                    <li>Focus only on high-leverage activities</li>
                </ol>
                <p>The result? I cut my work hours by 60% while doubling my income.</p>
                <p>Tomorrow, I'll show you exactly how to identify your high-leverage activities.</p>
                <p>Stay productive,<br>{brand_name}</p>
                """,
                "cta": None,
                "affiliate_links": []
            },
            {
                "email_number": 3,
                "delay": "2_days",
                "subject": "Step 1: The 80/20 Audit (takes 15 minutes)",
                "preview_text": "This exercise will change how you work forever...",
                "content_type": "actionable",
                "body_template": """
                <p>Hi {{first_name}},</p>
                <p>Yesterday I told you about my $5,000 mistake.</p>
                <p>Today, let's fix it with a simple 15-minute exercise:</p>
                <h3>The 80/20 Audit</h3>
                <p><strong>Step 1:</strong> List everything you did last week</p>
                <p><strong>Step 2:</strong> Mark which tasks produced results</p>
                <p><strong>Step 3:</strong> Circle the top 20% that drove 80% of results</p>
                <p><strong>Step 4:</strong> Eliminate, delegate, or automate the rest</p>
                <p>I created a template to make this easier:</p>
                <p><a href="[TEMPLATE_LINK]">Get the 80/20 Audit Template</a></p>
                <p>Tomorrow: How to automate the remaining tasks.</p>
                <p>Best,<br>{brand_name}</p>
                """,
                "cta": "Get the Template",
                "affiliate_links": ["notion_template", "airtable_template"]
            },
            {
                "email_number": 4,
                "delay": "2_days",
                "subject": "This tool saves me 10 hours every week",
                "preview_text": "And it costs less than a coffee per month...",
                "content_type": "product_recommendation",
                "body_template": """
                <p>Hi {{first_name}},</p>
                <p>After doing your 80/20 audit, you probably identified tasks you do repeatedly.</p>
                <p>Those are perfect candidates for automation.</p>
                <p>My favorite automation tool? <strong>Make.com</strong> (formerly Integromat).</p>
                <p>Here's what I automate with it:</p>
                <ul>
                    <li>Social media posting (saves 5 hrs/week)</li>
                    <li>Email sorting and responses (saves 3 hrs/week)</li>
                    <li>Data entry and reporting (saves 2 hrs/week)</li>
                </ul>
                <p><strong>Total time saved: 10+ hours per week</strong></p>
                <p>Cost: $9/month</p>
                <p>ROI: About 1000x</p>
                <p>I wrote a complete setup guide here:</p>
                <p><a href="[MAKE_GUIDE_LINK]">Read: Make.com Setup Guide</a></p>
                <p>Tomorrow: The final piece of the puzzle.</p>
                <p>Cheers,<br>{brand_name}</p>
                """,
                "cta": "Read the Guide",
                "affiliate_links": ["make_dot_com"]
            },
            {
                "email_number": 5,
                "delay": "2_days",
                "subject": "The 'One Thing' principle (email 5 of 7)",
                "preview_text": "What if you could only do ONE thing today?",
                "content_type": "philosophy",
                "body_template": """
                <p>Hi {{first_name}},</p>
                <p>Quick question:</p>
                <p><strong>If you could only accomplish ONE thing today, what would make everything else easier or irrelevant?</strong></p>
                <p>This is the "One Thing" principle from Gary Keller's book.</p>
                <p>Here's how I apply it:</p>
                <ol>
                    <li>Every morning, I identify my ONE thing</li>
                    <li>I block 3 hours for deep work on it</li>
                    <li>Everything else waits until it's done</li>
                </ol>
                <p>The result? I make progress on what actually matters, every single day.</p>
                <p>Try it tomorrow morning. Pick your ONE thing tonight.</p>
                <p>Tomorrow, I'll share my complete daily productivity system.</p>
                <p>Stay focused,<br>{brand_name}</p>
                """,
                "cta": None,
                "affiliate_links": []
            },
            {
                "email_number": 6,
                "delay": "2_days",
                "subject": "My complete daily productivity system",
                "preview_text": "The exact schedule I follow every day...",
                "content_type": "system_reveal",
                "body_template": """
                <p>Hi {{first_name}},</p>
                <p>You've learned about the 80/20 rule, automation, and the One Thing principle.</p>
                <p>Today, I'll show you how I combine them into a daily system:</p>
                <h3>My Daily Schedule</h3>
                <p><strong>6:00 AM - 6:30 AM:</strong> Morning routine (no phone)</p>
                <p><strong>6:30 AM - 9:30 AM:</strong> Deep work on ONE thing</p>
                <p><strong>9:30 AM - 10:00 AM:</strong> Break + light exercise</p>
                <p><strong>10:00 AM - 12:00 PM:</strong> Important meetings/calls</p>
                <p><strong>12:00 PM - 1:00 PM:</strong> Lunch + reading</p>
                <p><strong>1:00 PM - 3:00 PM:</strong> Administrative tasks (email, etc.)</p>
                <p><strong>3:00 PM onwards:</strong> Flexible time / learning</p>
                <p>The key? <strong>Protect your morning at all costs.</strong></p>
                <p>That's when your brain is fresh and creative.</p>
                <p>Want the complete system as a Notion template?</p>
                <p><a href="[NOTION_TEMPLATE_LINK]">Get the Daily System Template</a></p>
                <p>One more email coming tomorrow...</p>
                <p>Best,<br>{brand_name}</p>
                """,
                "cta": "Get the Template",
                "affiliate_links": ["notion_template"]
            },
            {
                "email_number": 7,
                "delay": "2_days",
                "subject": "Your next step (and a special offer)",
                "preview_text": "Thank you for being part of the community...",
                "content_type": "transition",
                "body_template": """
                <p>Hi {{first_name}},</p>
                <p>Over the past week, you've learned:</p>
                <ul>
                    <li>✅ How to identify your high-leverage activities</li>
                    <li>✅ How to automate repetitive tasks</li>
                    <li>✅ How to focus on what matters most</li>
                    <li>✅ My complete daily productivity system</li>
                </ul>
                <p>Now it's time to implement.</p>
                <p><strong>Your next step:</strong> Choose ONE tactic from this series and implement it this week.</p>
                <p>Just one. Don't try to do everything at once.</p>
                <p>And if you want to go deeper...</p>
                <h3>Special Offer for New Subscribers</h3>
                <p>I'm opening 5 spots for 1-on-1 productivity consulting.</p>
                <p>We'll audit your workflow, identify automation opportunities, and build a custom system for you.</p>
                <p>Normally $500. For you: $197 (limited to first 5 replies).</p>
                <p><a href="[CONSULTING_LINK]">Book Your Session</a></p>
                <p>Either way, keep implementing what you've learned.</p>
                <p>To your success,<br>{brand_name}</p>
                <p>P.S. - Hit reply and let me know which tactic you're implementing first. I read every email.</p>
                """,
                "cta": "Book Your Session",
                "affiliate_links": ["consulting_service"]
            }
        ]
        
        # Fill in brand name
        for email in sequence:
            email["subject"] = email["subject"].format(brand_name=self.brand_name)
            email["body_template"] = email["body_template"].format(brand_name=self.brand_name)
        
        return sequence
    
    def generate_broadcast_emails(self, count: int = 10) -> List[Dict]:
        """Generate broadcast email ideas"""
        
        broadcast_types = [
            {
                "subject": "New review: Best {product} for {audience}",
                "type": "new_content",
                "frequency": "weekly"
            },
            {
                "subject": "This week's top picks (curated for you)",
                "type": "curated",
                "frequency": "weekly"
            },
            {
                "subject": "⚡ Flash sale: {product} 40% off",
                "type": "promotional",
                "frequency": "as_needed"
            },
            {
                "subject": "Reader question: {question}",
                "type": "engagement",
                "frequency": "bi_weekly"
            },
            {
                "subject": "My {niche} toolkit (updated for 2026)",
                "type": "resource",
                "frequency": "monthly"
            }
        ]
        
        broadcasts = []
        for i in range(count):
            template = random.choice(broadcast_types)
            broadcast = {
                "id": i + 1,
                "subject": template["subject"].format(
                    product=random.choice(["project management tool", "automation software"]),
                    audience=random.choice(["freelancers", "remote workers"]),
                    question=random.choice(["What tool should I start with?", "How do I automate email?"]),
                    niche=self.niche
                ),
                "type": template["type"],
                "send_date": (datetime.now() + timedelta(days=i*7)).strftime("%Y-%m-%d"),
                "status": "draft"
            }
            broadcasts.append(broadcast)
        
        return broadcasts
    
    def generate_segmentation_rules(self) -> Dict:
        """Generate email segmentation rules for personalization"""
        
        return {
            "segments": [
                {
                    "name": "New Subscribers",
                    "criteria": "subscribed < 7 days",
                    "sequence": "welcome_sequence",
                    "email_frequency": "daily"
                },
                {
                    "name": "Engaged Readers",
                    "criteria": "opened last 3 emails",
                    "sequence": "value_focused",
                    "email_frequency": "3x_week"
                },
                {
                    "name": "Clickers",
                    "criteria": "clicked affiliate link in last 7 days",
                    "sequence": "buyer_intent",
                    "email_frequency": "2x_week"
                },
                {
                    "name": "Inactive",
                    "criteria": "no opens in 30 days",
                    "sequence": "re_engagement",
                    "email_frequency": "weekly"
                },
                {
                    "name": "VIP",
                    "criteria": "purchased or high engagement",
                    "sequence": "exclusive_content",
                    "email_frequency": "2x_week"
                }
            ],
            "automation_triggers": [
                {
                    "trigger": "clicked affiliate link",
                    "action": "add to 'buyer_intent' segment",
                    "delay": "immediate"
                },
                {
                    "trigger": "visited pricing page",
                    "action": "send comparison email",
                    "delay": "1_hour"
                },
                {
                    "trigger": "no open in 14 days",
                    "action": "send re-engagement email",
                    "delay": "immediate"
                }
            ]
        }
    
    def export_to_mailchimp_format(self, sequence: List[Dict]) -> List[Dict]:
        """Export sequence to Mailchimp automation format"""
        
        mailchimp_emails = []
        
        for email in sequence:
            mailchimp_emails.append({
                "subject_line": email["subject"],
                "preview_text": email["preview_text"],
                "from_name": self.brand_name,
                "from_email": f"hello@{self.brand_name.lower().replace(' ', '')}.com",
                "html_content": email["body_template"],
                "delay": email["delay"],
                "trigger": "signup" if email["email_number"] == 1 else "previous_email_sent"
            })
        
        return mailchimp_emails
    
    def save_sequences(self, sequence: List[Dict], broadcasts: List[Dict]):
        """Save all email sequences to files"""
        import os
        
        output_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Save welcome sequence
        welcome_file = f"{output_dir}/welcome_sequence.json"
        with open(welcome_file, 'w') as f:
            json.dump(sequence, f, indent=2)
        
        # Save broadcasts
        broadcast_file = f"{output_dir}/broadcast_emails.json"
        with open(broadcast_file, 'w') as f:
            json.dump(broadcasts, f, indent=2)
        
        # Save segmentation rules
        segmentation = self.generate_segmentation_rules()
        segmentation_file = f"{output_dir}/segmentation_rules.json"
        with open(segmentation_file, 'w') as f:
            json.dump(segmentation, f, indent=2)
        
        # Export Mailchimp format
        mailchimp_format = self.export_to_mailchimp_format(sequence)
        mailchimp_file = f"{output_dir}/mailchimp_import.json"
        with open(mailchimp_file, 'w') as f:
            json.dump(mailchimp_format, f, indent=2)
        
        print(f"✅ Welcome sequence saved: {welcome_file}")
        print(f"✅ Broadcast emails saved: {broadcast_file}")
        print(f"✅ Segmentation rules saved: {segmentation_file}")
        print(f"✅ Mailchimp format saved: {mailchimp_file}")

# Usage
if __name__ == "__main__":
    email_system = EmailAutomation(
        brand_name="ProductivityPro",
        niche="productivity"
    )
    
    # Generate sequences
    welcome_sequence = email_system.generate_welcome_sequence()
    broadcast_emails = email_system.generate_broadcast_emails(10)
    
    # Save everything
    email_system.save_sequences(welcome_sequence, broadcast_emails)
    
    print(f"\n📧 Generated {len(welcome_sequence)} welcome emails")
    print(f"📧 Generated {len(broadcast_emails)} broadcast emails")
    print("\n🎯 Segmentation strategy:")
    for segment in email_system.generate_segmentation_rules()["segments"]:
        print(f"  - {segment['name']}: {segment['email_frequency']} emails")
