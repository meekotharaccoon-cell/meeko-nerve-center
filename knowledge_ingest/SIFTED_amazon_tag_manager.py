#!/usr/bin/env python3
"""
Amazon Associates Tag Manager 2026
Creates and manages multiple tracking tags (autonomoushum-21 through autonomoushum-50)
Uses local LLM API for automation guidance
"""

import os
import json
import re
import random
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, quote

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('amazon_tags_2026.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LocalLLMClient:
    """Client for local LLM API at localhost:8000"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ask_endpoint = urljoin(base_url, "/ask")
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def ask(self, prompt: str, context: Optional[Dict] = None, timeout: int = 60) -> Dict:
        """Send prompt to local LLM API"""
        payload = {
            "prompt": prompt,
            "context": context or {}
        }
        
        try:
            response = self.session.post(
                self.ask_endpoint,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            return {
                "success": True,
                "response": data.get("response", data.get("answer", str(data))),
                "raw": data
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }


@dataclass
class AmazonTag:
    id: str
    store_id: str  # autonomoushum-20, autonomoushum-21, etc.
    created_date: Optional[str] = None
    status: str = "pending"  # pending, active, rejected
    website: Optional[str] = None
    tag_type: str = "content"  # content, mobile, redirect
    
    def full_tag(self) -> str:
        return self.store_id


class AmazonTagManager2026:
    def __init__(self, 
                 base_tag: str = "autonomoushum",
                 start_num: int = 21,
                 end_num: int = 50,
                 api_url: str = "http://localhost:8000"):
        self.base_tag = base_tag
        self.start_num = start_num
        self.end_num = end_num
        self.llm = LocalLLMClient(api_url)
        self.tags: List[AmazonTag] = []
        self.existing_tags: Set[str] = set()
        self.tags_file = Path("amazon_tags.json")
        self.associates_central_url = "https://affiliate-program.amazon.com/home/account/tag/manage"
        
        # Load existing tags if any
        self._load_existing()
        
    def _load_existing(self):
        """Load existing tags from JSON"""
        if self.tags_file.exists():
            try:
                with open(self.tags_file, 'r') as f:
                    data = json.load(f)
                    for tag_data in data.get('tags', []):
                        tag = AmazonTag(**tag_data)
                        self.tags.append(tag)
                        self.existing_tags.add(tag.store_id)
                logger.info(f"Loaded {len(self.tags)} existing tags")
            except Exception as e:
                logger.error(f"Error loading tags: {e}")

    def generate_tag_list(self) -> List[str]:
        """Generate list of tag IDs to create (autonomoushum-21 through autonomoushum-50)"""
        return [f"{self.base_tag}-{i}" for i in range(self.start_num, self.end_num + 1)]

    def create_tag_instructions(self, tag_id: str) -> str:
        """Generate step-by-step instructions for creating a tag manually"""
        instructions = f"""
AMAZON ASSOCIATES TAG CREATION - {tag_id}
========================================

URL: https://affiliate-program.amazon.com/home/account/tag/manage

STEPS:
1. Log in to Amazon Associates Central
2. Navigate to: Account Settings > Manage Your Tracking IDs
   (Direct: https://affiliate-program.amazon.com/home/account/tag/manage)
3. Click "Add Tracking ID" or "Create new tracking ID"
4. Enter Tracking ID: {tag_id}
5. Select Type: "Content" (for websites/blogs)
6. Website: Enter your main website URL (e.g., https://autonomoushum.com)
7. Click "Create" or "Submit"
8. Wait for confirmation (usually instant, sometimes 24-48 hours)
9. Note the status: Active = ready to use, Pending = wait for approval

VERIFICATION:
- Tag should appear in your tracking ID list
- Status should show "Active" or "Pending"
- Full tag format: {tag_id}-20 (the -20 is auto-appended by Amazon)

NEXT TAG: After creating {tag_id}, proceed to next in sequence.
"""
        return instructions

    def get_llm_guidance(self, tag_id: str, step: str = "general") -> str:
        """Get LLM guidance for tag creation"""
        prompt = f"""You are an Amazon Associates expert helping create tracking ID {tag_id}.

Current step: {step}

Provide specific guidance for:
1. Navigating Amazon Associates Central in 2026
2. Any recent UI changes or requirements
3. Common rejection reasons and how to avoid them
4. Best practices for tracking ID naming

Keep under 150 words, actionable."""
        
        result = self.llm.ask(prompt, timeout=30)
        if result["success"]:
            return result["response"]
        return "LLM guidance unavailable. Follow standard Amazon Associates procedures."

    def create_tags_batch(self, interactive: bool = True):
        """Generate creation workflow for all tags 21-50"""
        tag_list = self.generate_tag_list()
        new_tags = [t for t in tag_list if t not in self.existing_tags]
        
        if not new_tags:
            logger.info("All tags already exist in database")
            return
        
        logger.info(f"Creating {len(new_tags)} new tags ({new_tags[0]} to {new_tags[-1]})")
        
        created_tags = []
        
        for i, tag_id in enumerate(new_tags, 1):
            print(f"\n{'='*60}")
            print(f"TAG {i}/{len(new_tags)}: {tag_id}")
            print(f"{'='*60}")
            
            # Generate instructions
            instructions = self.create_tag_instructions(tag_id)
            print(instructions)
            
            # Get LLM tips
            tips = self.get_llm_guidance(tag_id, "creation")
            print(f"\n💡 LLM Tips:\n{tips}\n")
            
            if interactive:
                # Wait for user confirmation
                status = input(f"Status for {tag_id} (active/pending/failed/skip): ").strip().lower()
                
                if status == "skip":
                    continue
                elif status in ("active", "pending", "failed"):
                    tag = AmazonTag(
                        id=f"tag_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}",
                        store_id=tag_id,
                        created_date=datetime.now().isoformat(),
                        status=status,
                        website="https://autonomoushum.com",
                        tag_type="content"
                    )
                    created_tags.append(tag)
                    self.tags.append(tag)
                    self.existing_tags.add(tag_id)
                    
                    # Save after each creation
                    self.save_tags()
                    
                    if i < len(new_tags):
                        cont = input("\nContinue to next tag? (y/n): ").strip().lower()
                        if cont != 'y':
                            break
                else:
                    logger.warning(f"Invalid status '{status}', skipping {tag_id}")
            else:
                # Non-interactive: just create placeholder
                tag = AmazonTag(
                    id=f"tag_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}",
                    store_id=tag_id,
                    created_date=datetime.now().isoformat(),
                    status="pending",
                    website="https://autonomoushum.com",
                    tag_type="content"
                )
                created_tags.append(tag)
                self.tags.append(tag)
        
        logger.info(f"Created {len(created_tags)} tags")
        return created_tags

    def save_tags(self):
        """Save all tags to JSON"""
        data = {
            "base_tag": self.base_tag,
            "created": datetime.now().isoformat(),
            "total_tags": len(self.tags),
            "active_tags": len([t for t in self.tags if t.status == "active"]),
            "tags": [asdict(t) for t in self.tags]
        }
        
        with open(self.tags_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved {len(self.tags)} tags to {self.tags_file}")

    def get_active_tags(self) -> List[str]:
        """Return list of active tag store_ids"""
        return [t.store_id for t in self.tags if t.status == "active"]

    def get_random_tag(self) -> str:
        """Get random active tag for rotation"""
        active = self.get_active_tags()
        if not active:
            return f"{self.base_tag}-20"  # Fallback to original
        return random.choice(active)

    def update_content_tags(self, content_dir: str = "./articles", dry_run: bool = True):
        """Update all content files to use rotating tags"""
        content_path = Path(content_dir)
        if not content_path.exists():
            logger.error(f"Content directory not found: {content_dir}")
            return
        
        # Find all markdown/HTML files
        files = list(content_path.glob("*.md")) + list(content_path.glob("*.html"))
        
        if not files:
            logger.warning(f"No content files found in {content_dir}")
            return
        
        active_tags = self.get_active_tags()
        if len(active_tags) < 2:
            logger.warning("Not enough active tags for rotation (need 2+)")
            return
        
        logger.info(f"Updating {len(files)} files with tag rotation...")
        
        updates = []
        
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                new_content = content
                
                # Find all Amazon links with tags
                # Pattern: tag=XXXX-20 or tag=autonomoushum-XX
                pattern = r'tag=autonomoushum-\d{2}'
                matches = list(re.finditer(pattern, content))
                
                if not matches:
                    continue
                
                # Replace each tag with a random active one
                replacements = []
                for match in reversed(matches):  # Reverse to preserve positions
                    old_tag = match.group()
                    new_tag = f"tag={self.get_random_tag()}"
                    
                    if old_tag != new_tag:
                        new_content = new_content[:match.start()] + new_tag + new_content[match.end():]
                        replacements.append(f"{old_tag} -> {new_tag}")
                
                if new_content != original_content:
                    update_info = {
                        'file': str(filepath),
                        'replacements': replacements,
                        'old_preview': original_content[:200],
                        'new_preview': new_content[:200]
                    }
                    updates.append(update_info)
                    
                    if not dry_run:
                        # Backup original
                        backup_path = filepath.with_suffix(filepath.suffix + '.backup')
                        with open(backup_path, 'w', encoding='utf-8') as f:
                            f.write(original_content)
                        
                        # Write updated
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        logger.info(f"Updated: {filepath.name}")
                    else:
                        logger.info(f"[DRY RUN] Would update: {filepath.name}")
                        for r in replacements:
                            logger.info(f"  {r}")
                
            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")
        
        # Save update log
        log_file = f"tag_updates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump({
                'dry_run': dry_run,
                'files_processed': len(files),
                'files_updated': len(updates),
                'updates': updates
            }, f, indent=2)
        
        logger.info(f"\nSummary:")
        logger.info(f"Files processed: {len(files)}")
        logger.info(f"Files with updates: {len(updates)}")
        logger.info(f"Log saved: {log_file}")
        
        if dry_run:
            logger.info("\nThis was a DRY RUN. No files were modified.")
            logger.info("Run with dry_run=False to apply changes.")

    def generate_tag_rotation_script(self) -> str:
        """Generate Python script for dynamic tag rotation in new content"""
        active_tags = self.get_active_tags()
        
        script = f'''#!/usr/bin/env python3
"""
Dynamic Amazon Tag Rotator
Auto-inserts rotating tags into new content
Generated: {datetime.now().isoformat()}
"""

import random

# Active tags (auto-generated from amazon_tags.json)
ACTIVE_TAGS = {active_tags}

def get_tag() -> str:
    """Get random active Amazon Associates tag"""
    return random.choice(ACTIVE_TAGS)

def make_link(asin: str, tag: str = None) -> str:
    """Generate Amazon affiliate link with rotating tag"""
    if not tag:
        tag = get_tag()
    return f"https://www.amazon.com/dp/{{asin}}/?tag={{tag}}"

# Example usage:
# from tag_rotator import get_tag, make_link
# link = make_link("B0EXAMPLE123")
# print(link)  # Uses random tag from your pool
'''
        return script

    def export_tag_rotator(self, filename: str = "tag_rotator.py"):
        """Export rotation script"""
        script = self.generate_tag_rotation_script()
        with open(filename, 'w') as f:
            f.write(script)
        logger.info(f"Exported tag rotator to {filename}")

    def generate_report(self) -> Dict:
        """Generate status report"""
        total = len(self.tags)
        active = len([t for t in self.tags if t.status == "active"])
        pending = len([t for t in self.tags if t.status == "pending"])
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "base_tag": self.base_tag,
            "target_range": f"{self.base_tag}-{self.start_num} to {self.base_tag}-{self.end_num}",
            "summary": {
                "total_tags": total,
                "active": active,
                "pending": pending,
                "needed": 50 - 20 - total  # 50 max - existing (20) - created
            },
            "tags": [asdict(t) for t in self.tags],
            "next_steps": [
                f"Create remaining {30 - total} tags via Associates Central",
                "Update content files with tag rotation",
                "Monitor tag performance in Amazon reports"
            ]
        }
        
        report_file = f"tag_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved: {report_file}")
        return report

    def batch_create_workflow(self):
        """Complete workflow for creating tags 21-50"""
        print(f"\n{'='*70}")
        print(f"AMAZON ASSOCIATES TAG MANAGER 2026")
        print(f"Creating tags: {self.base_tag}-{self.start_num} through {self.base_tag}-{self.end_num}")
        print(f"{'='*70}\n")
        
        # Check existing
        existing = [t for t in self.tags if t.store_id >= f"{self.base_tag}-{self.start_num}"]
        print(f"Found {len(existing)} tags already in database")
        
        # Generate creation workflow
        print(f"\nStep 1: Create {30 - len(existing)} new tracking IDs")
        self.create_tags_batch(interactive=True)
        
        # Save
        self.save_tags()
        
        # Export rotator
        print(f"\nStep 2: Exporting tag rotation utilities...")
        self.export_tag_rotator()
        
        # Report
        print(f"\nStep 3: Generating report...")
        report = self.generate_report()
        
        print(f"\n{'='*70}")
        print("WORKFLOW COMPLETE")
        print(f"{'='*70}")
        print(f"Active tags: {report['summary']['active']}")
        print(f"Pending: {report['summary']['pending']}")
        print(f"Files created:")
        print(f"  - {self.tags_file} (tag database)")
        print(f"  - tag_rotator.py (rotation script)")
        print(f"  - tag_report_*.json (status report)")
        print(f"\nNext: Run update_content_tags() to rotate existing content")


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Amazon Associates Tag Manager 2026')
    parser.add_argument('--create', action='store_true', help='Interactive tag creation workflow')
    parser.add_argument('--update-content', action='store_true', help='Update content with rotating tags')
    parser.add_argument('--content-dir', default='./articles', help='Content directory')
    parser.add_argument('--apply', action='store_true', help='Apply updates (not dry run)')
    parser.add_argument('--report', action='store_true', help='Generate status report')
    parser.add_argument('--api-url', default='http://localhost:8000', help='LLM API URL')
    
    args = parser.parse_args()
    
    manager = AmazonTagManager2026(api_url=args.api_url)
    
    if args.create:
        manager.batch_create_workflow()
    elif args.update_content:
        manager.update_content_tags(args.content_dir, dry_run=not args.apply)
    elif args.report:
        manager.generate_report()
    else:
        # Default: show status
        print(f"\nAmazon Tag Manager Status")
        print(f"Existing tags: {len(manager.tags)}")
        print(f"Active: {len(manager.get_active_tags())}")
        print(f"\nRun with --create to start tag creation workflow")
        print(f"Run with --update-content to rotate tags in articles")


if __name__ == "__main__":
    main()