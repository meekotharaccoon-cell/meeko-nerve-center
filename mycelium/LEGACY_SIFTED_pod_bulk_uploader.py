#!/usr/bin/env python3
"""
POD Bulk Uploader 2026 - Local LLM API Edition
Uses HTTP requests to localhost:8000/ask - No browser automation
"""

import os
import time
import random
import json
import csv
import logging
import requests
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pod_uploader_api_2026.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Design:
    filepath: str
    title: str
    tags: str
    description: str
    niche: str
    status: str = "pending"
    uploaded_at: Optional[str] = None
    platform: Optional[str] = None
    error: Optional[str] = None


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
        
    def ask(self, prompt: str, context: Optional[Dict] = None, timeout: int = 300) -> Dict[str, Any]:
        """
        Send prompt to local LLM API
        
        Returns dict with:
        - success: bool
        - response: str (LLM output)
        - error: str (if failed)
        """
        payload = {
            "prompt": prompt,
            "context": context or {}
        }
        
        try:
            logger.info(f"Sending request to {self.ask_endpoint}")
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
            
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to {self.ask_endpoint}. Is the server running?",
                "response": None
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timed out. LLM may be overloaded.",
                "response": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }


class PODUploaderAPI2026:
    def __init__(self, platform: str = 'redbubble', api_base_url: str = "http://localhost:8000"):
        self.platform = platform.lower()
        self.llm = LocalLLMClient(api_base_url)
        self.uploaded_count = 0
        self.failed_count = 0
        self.session_start = datetime.now()
        self.designs_log: List[Dict] = []
        self.api_available = self._check_api()
        
        # Platform configurations
        self.configs = {
            'redbubble': {
                'name': 'RedBubble',
                'upload_url': 'https://www.redbubble.com/portfolio/images/new',
                'login_url': 'https://www.redbubble.com/auth/login',
                'steps': ['login', 'upload_file', 'fill_details', 'enable_products', 'save']
            },
            'teepublic': {
                'name': 'TeePublic', 
                'upload_url': 'https://www.teepublic.com/design/quick-create',
                'login_url': 'https://www.teepublic.com/login',
                'steps': ['login', 'upload_file', 'fill_details', 'save']
            },
            'society6': {
                'name': 'Society6',
                'upload_url': 'https://society6.com/upload',
                'login_url': 'https://society6.com/login',
                'steps': ['login', 'upload_file', 'fill_details', 'enable_products', 'save']
            }
        }
        
        self.current_config = self.configs.get(self.platform)
        if not self.current_config:
            raise ValueError(f"Platform {platform} not supported")

    def _check_api(self) -> bool:
        """Check if local LLM API is running"""
        try:
            # Try a simple health check or short prompt
            result = self.llm.ask("Hello", timeout=5)
            if result["success"]:
                logger.info("✅ Local LLM API connected")
                return True
            else:
                logger.warning(f"⚠️ API check: {result['error']}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Cannot reach LLM API: {e}")
            return False

    def generate_metadata(self, filepath: str) -> Design:
        """Auto-generate title, tags, description from filename"""
        filename = Path(filepath).stem
        words = filename.replace('_', ' ').replace('-', ' ').split()
        
        # Determine niche
        niche_keywords = {
            'vintage': ['vintage', 'retro', 'classic', 'old school', 'nostalgic', 'antique'],
            'nature': ['nature', 'forest', 'mountain', 'ocean', 'wildlife', 'outdoor', 'hiking'],
            'funny': ['funny', 'humor', 'joke', 'sarcastic', 'meme', 'witty', 'comedy'],
            'abstract': ['abstract', 'geometric', 'pattern', 'modern', 'minimalist', 'boho'],
            'typography': ['text', 'quote', 'saying', 'typography', 'lettering', 'font'],
            'pop_culture': ['gaming', 'anime', 'movie', 'tv', 'music', 'band', 'game'],
            'animals': ['dog', 'cat', 'pet', 'animal', 'puppy', 'kitten', 'wildlife'],
            'sports': ['sports', 'football', 'basketball', 'soccer', 'fitness', 'gym']
        }
        
        detected_niche = 'abstract'
        filename_lower = filename.lower()
        for niche, keywords in niche_keywords.items():
            if any(k in filename_lower for k in keywords):
                detected_niche = niche
                break
        
        # Use LLM to generate better metadata if available
        if self.api_available:
            return self._generate_metadata_with_llm(filepath, filename, detected_niche)
        else:
            return self._generate_metadata_basic(filepath, filename, detected_niche)

    def _generate_metadata_basic(self, filepath: str, filename: str, niche: str) -> Design:
        """Basic metadata generation without LLM"""
        title_templates = [
            f"{filename.title()} - Premium 2026 Design",
            f"Stunning {filename.title()} Art Print",
            f"{filename.title()} - Modern 2026 Collection",
            f"Unique {filename.title()} Design",
            f"{filename.title()} - Trending Style 2026"
        ]
        
        tag_pools = {
            'vintage': ['vintage', 'retro', 'classic', 'nostalgic', '80s', '90s', 'throwback'],
            'nature': ['nature', 'outdoors', 'wildlife', 'forest', 'mountain', 'eco', 'green'],
            'funny': ['funny', 'humor', 'sarcastic', 'meme', 'joke', 'witty', 'gift'],
            'abstract': ['abstract', 'geometric', 'modern', 'minimalist', 'pattern', 'art'],
            'typography': ['typography', 'quote', 'inspirational', 'lettering', 'text'],
            'pop_culture': ['gaming', 'gamer', 'anime', 'geek', 'fandom', 'pop culture'],
            'animals': ['animal', 'pet', 'cute', 'dog', 'cat', 'wildlife', 'nature'],
            'sports': ['sports', 'fitness', 'gym', 'athletic', 'workout', 'team']
        }
        
        base_tags = tag_pools.get(niche, tag_pools['abstract'])
        extra_tags = ['trending 2026', 'best seller', 'popular', 'gift idea', 'unique design']
        all_tags = random.sample(base_tags, min(5, len(base_tags))) + random.sample(extra_tags, 3)
        
        descriptions = [
            f"Premium {filename.lower()} design created in 2026. Perfect for gifts or personal use. High quality printing on 50+ products.",
            f"Trending 2026 {filename.lower()} artwork. Modern style meets quality craftsmanship. Available on apparel, home decor, and accessories.",
            f"Unique {filename.lower()} design from independent artist. 2026 collection. Support small business while getting amazing products."
        ]
        
        return Design(
            filepath=filepath,
            title=random.choice(title_templates),
            tags=', '.join(all_tags),
            description=random.choice(descriptions),
            niche=niche
        )

    def _generate_metadata_with_llm(self, filepath: str, filename: str, niche: str) -> Design:
        """Use local LLM to generate optimized metadata"""
        prompt = f"""Generate POD (Print on Demand) metadata for an image file.

Filename: {filename}
Detected niche: {niche}

Generate:
1. A catchy title (max 80 chars)
2. 10-15 relevant tags, comma-separated
3. A compelling description (2-3 sentences)

Format exactly as:
TITLE: [title]
TAGS: [tag1, tag2, tag3...]
DESC: [description]

Make it SEO-friendly for 2026. Appeal to buyers looking for {niche} designs."""

        result = self.llm.ask(prompt, timeout=30)
        
        if result["success"]:
            try:
                text = result["response"]
                lines = text.strip().split('\n')
                
                title = filename.title()
                tags = f"{niche}, trending 2026, best seller"
                desc = f"Premium {filename.lower()} design from 2026."
                
                for line in lines:
                    if line.startswith('TITLE:'):
                        title = line.replace('TITLE:', '').strip()
                    elif line.startswith('TAGS:'):
                        tags = line.replace('TAGS:', '').strip()
                    elif line.startswith('DESC:'):
                        desc = line.replace('DESC:', '').strip()
                
                return Design(
                    filepath=filepath,
                    title=title[:80],
                    tags=tags,
                    description=desc[:200],
                    niche=niche
                )
            except Exception as e:
                logger.warning(f"LLM parse error: {e}, using basic")
                return self._generate_metadata_basic(filepath, filename, niche)
        else:
            return self._generate_metadata_basic(filepath, filename, niche)

    def create_upload_instructions(self, design: Design) -> str:
        """Create detailed instructions for manual upload or LLM guidance"""
        instructions = f"""
PLATFORM: {self.current_config['name']}
UPLOAD URL: {self.current_config['upload_url']}

FILE: {os.path.abspath(design.filepath)}
TITLE: {design.title}
TAGS: {design.tags}
DESCRIPTION: {design.description}

STEPS:
1. Go to {self.current_config['upload_url']}
2. Click "Upload" or drag file: {os.path.basename(design.filepath)}
3. Wait for image processing
4. Enter Title: {design.title}
5. Enter Tags: {design.tags}
6. Enter Description: {design.description}
7. Enable ALL available products (t-shirts, stickers, mugs, etc.)
8. Set markup to 20% if adjustable
9. Click Save/Publish
10. Wait for confirmation

CONFIRMATION: Look for "Success" message or check your portfolio
"""
        return instructions

    def process_with_llm(self, design: Design) -> bool:
        """Ask LLM to guide or automate the upload process conceptually"""
        if not self.api_available:
            return False
            
        instructions = self.create_upload_instructions(design)
        
        prompt = f"""You are helping upload a design to {self.current_config['name']}.

{instructions}

The user will perform these steps manually. Provide:
1. Any tips for this specific platform
2. Common mistakes to avoid
3. Expected time per step
4. How to verify success

Keep response under 200 words, actionable and specific."""

        result = self.llm.ask(prompt, timeout=60)
        
        if result["success"]:
            logger.info(f"LLM guidance for {design.title}:")
            logger.info(result["response"][:300] + "...")
            return True
        else:
            logger.error(f"LLM failed: {result['error']}")
            return False

    def save_to_csv(self, designs: List[Design], filename: Optional[str] = None) -> Path:
        """Export designs to CSV for manual upload"""
        if not filename:
            filename = f"upload_queue_{self.platform}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        filepath = Path(filename)
        
        fieldnames = ['filepath', 'title', 'tags', 'description', 'niche', 
                     'platform', 'status', 'uploaded_at', 'error', 'instructions']
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for design in designs:
                row = asdict(design)
                row['platform'] = self.platform
                row['instructions'] = self.create_upload_instructions(design)
                writer.writerow(row)
        
        logger.info(f"📄 CSV saved: {filepath.absolute()}")
        return filepath

    def save_to_json(self, designs: List[Design], filename: Optional[str] = None) -> Path:
        """Export designs to JSON with full instructions"""
        if not filename:
            filename = f"upload_queue_{self.platform}_{datetime.now().strftime('%Y%m%d')}.json"
        
        filepath = Path(filename)
        
        data = {
            'platform': self.platform,
            'created': datetime.now().isoformat(),
            'api_available': self.api_available,
            'designs': []
        }
        
        for design in designs:
            design_dict = asdict(design)
            design_dict['instructions'] = self.create_upload_instructions(design)
            data['designs'].append(design_dict)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"📄 JSON saved: {filepath.absolute()}")
        return filepath

    def bulk_process(self, 
                    folder_path: str, 
                    limit: Optional[int] = None,
                    file_types: tuple = ('.png', '.jpg', '.jpeg', '.webp')) -> List[Design]:
        """Process all designs and generate upload packages"""
        folder = Path(folder_path)
        files = [f for f in folder.iterdir() if f.suffix.lower() in file_types]
        
        if not files:
            logger.error(f"No image files found in {folder_path}")
            return []
        
        if limit:
            files = files[:limit]
        
        logger.info(f"🚀 Processing {len(files)} designs for {self.current_config['name']}")
        logger.info(f"API Status: {'✅ Connected' if self.api_available else '❌ Offline (basic mode)'}")
        
        designs = []
        
        for i, filepath in enumerate(files, 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing {i}/{len(files)}: {filepath.name}")
            
            # Generate metadata
            design = self.generate_metadata(str(filepath))
            design.platform = self.platform
            
            # Get LLM enhancement if available
            if self.api_available:
                self.process_with_llm(design)
                time.sleep(1)  # Be nice to local API
            
            designs.append(design)
            logger.info(f"✅ Ready: {design.title[:60]}...")
            logger.info(f"   Niche: {design.niche}")
            logger.info(f"   Tags: {design.tags[:60]}...")
        
        return designs

    def run(self, 
           folder_path: str = './designs',
           limit: Optional[int] = None,
           export_format: str = 'both'):
        """
        Main execution
        
        export_format: 'csv', 'json', or 'both'
        """
        print(f"\n{'='*60}")
        print(f"🎨 POD Bulk Uploader 2026 - API Edition")
        print(f"Platform: {self.current_config['name']}")
        print(f"LLM API: {self.llm.base_url}")
        print(f"{'='*60}\n")
        
        # Process designs
        designs = self.bulk_process(folder_path, limit)
        
        if not designs:
            print("❌ No designs processed")
            return
        
        # Export
        files_created = []
        
        if export_format in ('csv', 'both'):
            csv_path = self.save_to_csv(designs)
            files_created.append(csv_path)
        
        if export_format in ('json', 'both'):
            json_path = self.save_to_json(designs)
            files_created.append(json_path)
        
        # Summary
        print(f"\n{'='*60}")
        print("✅ PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Designs processed: {len(designs)}")
        print(f"Files created:")
        for f in files_created:
            print(f"  📄 {f}")
        print(f"\nNext steps:")
        print(f"1. Open the CSV in Excel/Google Sheets")
        print(f"2. Go to {self.current_config['upload_url']}")
        print(f"3. Follow the instructions column for each design")
        print(f"4. Mark status as 'uploaded' when done")
        print(f"\nOr use the JSON file with a custom uploader script")

    def cross_platform_export(self, 
                             folder_path: str, 
                             platforms: List[str],
                             limit_per_platform: Optional[int] = None):
        """Export for multiple platforms at once"""
        # Generate designs once
        folder = Path(folder_path)
        files = []
        for ext in ('*.png', '*.jpg', '*.jpeg', '*.webp'):
            files.extend(folder.glob(ext))
        
        if limit_per_platform:
            files = files[:limit_per_platform]
        
        logger.info(f"Generating metadata for {len(files)} designs...")
        
        # Create base designs
        base_designs = []
        for filepath in files:
            # Use basic generation for speed
            filename = filepath.stem
            niche = 'abstract'
            design = self._generate_metadata_basic(str(filepath), filename, niche)
            base_designs.append(design)
        
        # Export for each platform
        for platform in platforms:
            print(f"\n{'='*60}")
            print(f"Exporting for: {platform.upper()}")
            print(f"{'='*60}")
            
            self.platform = platform
            self.current_config = self.configs[platform]
            
            # Update platform in designs
            platform_designs = []
            for d in base_designs:
                new_d = Design(**asdict(d))
                new_d.platform = platform
                platform_designs.append(new_d)
            
            # Save files
            csv_path = self.save_to_csv(platform_designs, 
                                       f"upload_queue_{platform}_2026.csv")
            json_path = self.save_to_json(platform_designs,
                                         f"upload_queue_{platform}_2026.json")
            
            print(f"✅ {platform}: CSV + JSON created")


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='POD Bulk Uploader 2026 - API Edition')
    parser.add_argument('--platform', default='redbubble', 
                       choices=['redbubble', 'teepublic', 'society6'])
    parser.add_argument('--folder', default='./designs', help='Designs folder')
    parser.add_argument('--limit', type=int, default=None, help='Max designs to process')
    parser.add_argument('--api-url', default='http://localhost:8000', help='LLM API URL')
    parser.add_argument('--format', default='both', choices=['csv', 'json', 'both'])
    parser.add_argument('--multi', action='store_true', help='Export for all platforms')
    
    args = parser.parse_args()
    
    uploader = PODUploaderAPI2026(args.platform, args.api_url)
    
    if args.multi:
        uploader.cross_platform_export(
            args.folder,
            ['redbubble', 'teepublic', 'society6'],
            args.limit
        )
    else:
        uploader.run(args.folder, args.limit, args.format)


if __name__ == "__main__":
    main()