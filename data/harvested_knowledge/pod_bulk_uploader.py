import os
import time
import random
import json
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pod_uploader_2026.log'),
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


class PODUploader2026:
    def __init__(self, platform: str = 'redbubble'):
        self.platform = platform.lower()
        self.driver: Optional[webdriver.Chrome] = None
        self.uploaded_count = 0
        self.failed_count = 0
        self.session_start = datetime.now()
        
        # Platform configurations
        self.configs = {
            'redbubble': {
                'name': 'RedBubble',
                'login_url': 'https://www.redbubble.com/auth/login',
                'upload_url': 'https://www.redbubble.com/portfolio/images/new',
                'success_url': '/portfolio/images/',
                'file_input': (By.CSS_SELECTOR, 'input[type="file"]'),
                'title_input': (By.ID, 'work_title'),
                'tags_input': (By.CSS_SELECTOR, 'input[placeholder*="tag"]'),
                'description_input': (By.ID, 'work_description'),
                'save_button': (By.CSS_SELECTOR, 'button[type="submit"]'),
                'mature_checkbox': (By.ID, 'work_is_mature'),
                'products_grid': (By.CLASS_NAME, 'products-grid'),
                'delay_range': (35, 90)  # Conservative for 2026
            },
            'teepublic': {
                'name': 'TeePublic',
                'login_url': 'https://www.teepublic.com/login',
                'upload_url': 'https://www.teepublic.com/design/quick-create',
                'success_url': '/design/',
                'file_input': (By.ID, 'design_file'),
                'title_input': (By.ID, 'design_title'),
                'tags_input': (By.ID, 'design_tags'),
                'description_input': (By.ID, 'design_description'),
                'save_button': (By.CSS_SELECTOR, '.submit-design'),
                'delay_range': (25, 75)
            },
            'society6': {
                'name': 'Society6',
                'login_url': 'https://society6.com/login',
                'upload_url': 'https://society6.com/upload',
                'success_url': '/product/',
                'file_input': (By.CSS_SELECTOR, 'input[type="file"]'),
                'title_input': (By.NAME, 'title'),
                'tags_input': (By.NAME, 'tags'),
                'description_input': (By.NAME, 'description'),
                'save_button': (By.CSS_SELECTOR, '.save-button'),
                'delay_range': (40, 100)
            }
        }
        
        self.current_config = self.configs.get(self.platform)
        if not self.current_config:
            raise ValueError(f"Platform {platform} not supported. Use: redbubble, teepublic, society6")

    def setup_driver(self, headless: bool = False, proxy: Optional[str] = None):
        """Initialize Chrome with anti-detection measures"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Anti-detection settings (2026 updated)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--start-maximized')
        
        # Random user agent (2026 Chrome versions)
        chrome_version = random.choice([120, 121, 122, 123])
        user_agent = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36'
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        # Proxy support
        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')
        
        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute CDP commands to prevent detection
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    window.chrome = { runtime: {} };
                '''
            })
            
            self.driver.set_page_load_timeout(30)
            logger.info(f"Driver initialized for {self.current_config['name']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            raise

    def random_delay(self, action_type: str = 'medium'):
        """Human-like delays"""
        if action_type == 'short':
            delay = random.uniform(1.5, 4.0)
        elif action_type == 'medium':
            delay = random.uniform(4.0, 8.0)
        elif action_type == 'long':
            delay = random.uniform(self.current_config['delay_range'][0], 
                                 self.current_config['delay_range'][1])
        else:
            delay = random.uniform(2.0, 5.0)
        
        logger.info(f"Waiting {delay:.1f}s...")
        time.sleep(delay)

    def human_typing(self, element, text: str):
        """Simulate human typing with mistakes and corrections"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.25))
        
        # Occasionally pause mid-typing
        if random.random() < 0.1:
            time.sleep(random.uniform(0.5, 1.5))

    def auto_login(self, email: str, password: str):
        """Automated login with human-like behavior"""
        logger.info(f"Navigating to {self.current_config['name']} login...")
        self.driver.get(self.current_config['login_url'])
        self.random_delay('medium')
        
        try:
            # Find and fill email
            email_selectors = [
                (By.ID, 'email'),
                (By.NAME, 'email'),
                (By.NAME, 'username'),
                (By.CSS_SELECTOR, 'input[type="email"]'),
                (By.CSS_SELECTOR, 'input[name="login[email]"]')
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(selector)
                    )
                    break
                except:
                    continue
            
            if not email_field:
                raise Exception("Could not find email field")
            
            email_field.click()
            self.random_delay('short')
            self.human_typing(email_field, email)
            self.random_delay('short')
            
            # Find and fill password
            password_selectors = [
                (By.ID, 'password'),
                (By.NAME, 'password'),
                (By.CSS_SELECTOR, 'input[type="password"]')
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(*selector)
                    break
                except:
                    continue
            
            if not password_field:
                raise Exception("Could not find password field")
            
            password_field.click()
            self.random_delay('short')
            self.human_typing(password_field, password)
            self.random_delay('short')
            
            # Submit
            submit_selectors = [
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.CSS_SELECTOR, 'input[type="submit"]'),
                (By.CLASS_NAME, 'login-button')
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = self.driver.find_element(*selector)
                    submit_btn.click()
                    break
                except:
                    continue
            
            self.random_delay('long')
            
            # Check for success
            if 'login' not in self.driver.current_url.lower():
                logger.info("Login successful")
                return True
            else:
                logger.error("Login may have failed - still on login page")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def generate_metadata(self, filepath: str) -> Design:
        """Auto-generate title, tags, description from filename"""
        filename = Path(filepath).stem
        words = filename.replace('_', ' ').replace('-', ' ').split()
        
        # Determine niche from filename
        niche_keywords = {
            'vintage': ['vintage', 'retro', 'classic', 'old school', 'nostalgic'],
            'nature': ['nature', 'forest', 'mountain', 'ocean', 'wildlife', 'outdoor'],
            'funny': ['funny', 'humor', 'joke', 'sarcastic', 'meme', 'witty'],
            'abstract': ['abstract', 'geometric', 'pattern', 'modern', 'minimalist'],
            'typography': ['text', 'quote', 'saying', 'typography', 'lettering'],
            'pop_culture': ['gaming', 'anime', 'movie', 'tv', 'music', 'band']
        }
        
        detected_niche = 'abstract'
        for niche, keywords in niche_keywords.items():
            if any(k in filename.lower() for k in keywords):
                detected_niche = niche
                break
        
        # Title templates
        title_templates = [
            f"{filename.title()} - Premium 2026 Design",
            f"Stunning {filename.title()} Art",
            f"{filename.title()} - Modern Aesthetic 2026",
            f"Unique {filename.title()} Design Collection",
            f"{filename.title()} - Trending 2026"
        ]
        
        title = random.choice(title_templates)
        
        # Tag pools by niche
        tag_pools = {
            'vintage': ['vintage', 'retro', 'classic', 'nostalgic', 'throwback', 'old school', 'antique', 'timeless', '80s', '90s'],
            'nature': ['nature', 'outdoors', 'wildlife', 'forest', 'mountain', 'hiking', 'adventure', 'eco', 'green', 'organic'],
            'funny': ['funny', 'humor', 'sarcastic', 'meme', 'joke', 'witty', 'clever', 'laugh', 'comedy', 'gift idea'],
            'abstract': ['abstract', 'geometric', 'modern', 'minimalist', 'pattern', 'design', 'art', 'contemporary', 'creative', 'boho'],
            'typography': ['typography', 'quote', 'inspirational', 'motivational', 'text art', 'lettering', 'saying', 'phrase'],
            'pop_culture': ['gaming', 'gamer', 'anime', 'geek', 'nerd', 'fandom', 'cosplay', 'pop culture', 'entertainment']
        }
        
        base_tags = tag_pools.get(detected_niche, tag_pools['abstract'])
        extra_tags = ['trending 2026', 'best seller', 'popular', 'gift', 'unique', 'stylish', 'cool']
        
        all_tags = random.sample(base_tags, 5) + random.sample(extra_tags, 3)
        tags = ', '.join(all_tags)
        
        # Description
        descriptions = [
            f"High-quality {filename.lower()} design perfect for any occasion. Created in 2026. Available on multiple products including t-shirts, stickers, phone cases, and more. Great gift idea!",
            f"Trending 2026 {filename.lower()} artwork. Modern, stylish design that stands out. Premium quality printing on all products. Support independent artists!",
            f"Unique {filename.lower()} design from 2026. Perfect for expressing your personal style. Available on 50+ products. Fast shipping worldwide."
        ]
        
        description = random.choice(descriptions)
        
        return Design(
            filepath=filepath,
            title=title,
            tags=tags,
            description=description,
            niche=detected_niche
        )

    def upload_design(self, design: Design, enable_all_products: bool = True) -> bool:
        """Upload single design to current platform"""
        logger.info(f"Uploading: {Path(design.filepath).name}")
        
        try:
            # Navigate to upload page
            self.driver.get(self.current_config['upload_url'])
            self.random_delay('medium')
            
            # Upload file
            try:
                file_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located(self.current_config['file_input'])
                )
                file_input.send_keys(os.path.abspath(design.filepath))
                logger.info("File sent to input")
            except Exception as e:
                logger.error(f"Could not find file input: {e}")
                return False
            
            # Wait for upload processing
            self.random_delay('long')
            
            # Fill title
            try:
                title_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(self.current_config['title_input'])
                )
                title_field.clear()
                self.human_typing(title_field, design.title)
                logger.info(f"Title entered: {design.title[:50]}...")
            except Exception as e:
                logger.warning(f"Title input issue: {e}")
            
            self.random_delay('short')
            
            # Fill tags
            try:
                tags_field = self.driver.find_element(*self.current_config['tags_input'])
                self.human_typing(tags_field, design.tags)
                logger.info(f"Tags entered: {len(design.tags)} chars")
            except Exception as e:
                logger.warning(f"Tags input issue: {e}")
            
            self.random_delay('short')
            
            # Fill description
            try:
                desc_field = self.driver.find_element(*self.current_config['description_input'])
                self.human_typing(desc_field, design.description)
            except Exception as e:
                logger.warning(f"Description input issue: {e}")
            
            # Platform-specific additional steps
            if self.platform == 'redbubble' and enable_all_products:
                self._enable_all_redbubble_products()
            
            self.random_delay('medium')
            
            # Save/submit
            try:
                save_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(self.current_config['save_button'])
                )
                save_btn.click()
                logger.info("Save button clicked")
            except Exception as e:
                logger.error(f"Could not click save: {e}")
                return False
            
            # Wait for success
            self.random_delay('long')
            
            # Verify success
            if self.current_config['success_url'] in self.driver.current_url:
                self.uploaded_count += 1
                logger.info(f"✅ SUCCESS: {design.title[:40]}...")
                return True
            else:
                # Check for error messages
                try:
                    error_elements = self.driver.find_elements(By.CLASS_NAME, 'error')
                    if error_elements:
                        logger.error(f"Upload error: {error_elements[0].text}")
                except:
                    pass
                return False
                
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            self.failed_count += 1
            return False

    def _enable_all_redbubble_products(self):
        """Enable all product types on RedBubble"""
        try:
            # Scroll to products section
            products_section = self.driver.find_element(By.CLASS_NAME, 'products-grid')
            self.driver.execute_script("arguments[0].scrollIntoView();", products_section)
            self.random_delay('short')
            
            # Find and check all product checkboxes
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, '.product-checkbox input')
            enabled = 0
            for checkbox in checkboxes:
                if not checkbox.is_selected():
                    try:
                        checkbox.click()
                        enabled += 1
                        time.sleep(0.2)
                    except:
                        continue
            
            logger.info(f"Enabled {enabled} products")
            
            # Set default markup (20%)
            try:
                markup_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="number"]')
                for inp in markup_inputs[:3]:  # First few markup fields
                    inp.clear()
                    inp.send_keys('20')
                    time.sleep(0.1)
            except:
                pass
                
        except Exception as e:
            logger.warning(f"Could not enable all products: {e}")

    def bulk_upload(self, 
                   folder_path: str, 
                   limit: Optional[int] = None,
                   file_types: tuple = ('.png', '.jpg', '.jpeg')):
        """Upload all designs in folder"""
        folder = Path(folder_path)
        files = [f for f in folder.iterdir() if f.suffix.lower() in file_types]
        
        if not files:
            logger.error(f"No image files found in {folder_path}")
            return
        
        if limit:
            files = files[:limit]
        
        logger.info(f"🚀 Starting bulk upload of {len(files)} designs to {self.current_config['name']}")
        logger.info(f"Session started: {self.session_start}")
        
        for i, filepath in enumerate(files, 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing {i}/{len(files)}: {filepath.name}")
            
            # Generate metadata
            design = self.generate_metadata(str(filepath))
            logger.info(f"Title: {design.title}")
            logger.info(f"Niche: {design.niche}")
            
            # Upload
            success = self.upload_design(design)
            
            if i < len(files):
                # Random delay between uploads (critical for anti-detection)
                delay = random.randint(*self.current_config['delay_range'])
                logger.info(f"Next upload in {delay} seconds...")
                time.sleep(delay)
        
        # Summary
        logger.info(f"\n{'='*50}")
        logger.info("UPLOAD SESSION COMPLETE")
        logger.info(f"Total: {len(files)}")
        logger.info(f"Successful: {self.uploaded_count}")
        logger.info(f"Failed: {self.failed_count}")
        logger.info(f"Duration: {datetime.now() - self.session_start}")

    def cross_platform_upload(self, 
                             folder_path: str, 
                             platforms: List[str],
                             credentials: Dict[str, tuple]):
        """Upload to multiple platforms sequentially"""
        for platform in platforms:
            logger.info(f"\n{'='*60}")
            logger.info(f"SWITCHING TO {platform.upper()}")
            logger.info(f"{'='*60}")
            
            # Reset counters
            self.uploaded_count = 0
            self.failed_count = 0
            
            # Reinitialize driver for clean session
            if self.driver:
                self.driver.quit()
                time.sleep(5)
            
            self.platform = platform
            self.current_config = self.configs[platform]
            self.setup_driver()
            
            # Login
            if platform in credentials:
                email, password = credentials[platform]
                if not self.auto_login(email, password):
                    logger.error(f"Skipping {platform} due to login failure")
                    continue
            else:
                input(f"🔑 Manual login required for {platform}. Press Enter when logged in...")
            
            # Upload
            self.bulk_upload(folder_path)
            
            # Cooldown between platforms
            if platform != platforms[-1]:
                cooldown = random.randint(60, 180)
                logger.info(f"Platform cooldown: {cooldown}s")
                time.sleep(cooldown)

    def save_session_log(self):
        """Save upload session details"""
        log_data = {
            'session_date': self.session_start.isoformat(),
            'platform': self.platform,
            'uploaded': self.uploaded_count,
            'failed': self.failed_count,
            'user_agent': self.driver.execute_script("return navigator.userAgent;") if self.driver else None
        }
        
        with open(f'upload_session_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(log_data, f, indent=2)

    def quit(self):
        """Clean shutdown"""
        if self.driver:
            self.save_session_log()
            self.driver.quit()
            logger.info("Driver closed")


def main():
    """Example usage"""
    print("🎨 POD Bulk Uploader 2026")
    print("=" * 50)
    
    # Single platform example
    uploader = PODUploader2026('redbubble')
    uploader.setup_driver(headless=False)
    
    # Manual login first time (safer)
    print("\n1. Browser will open to RedBubble login")
    print("2. Login manually")
    print("3. Return here and press Enter")
    input("\nPress Enter after logging in...")
    
    # Upload
    uploader.bulk_upload(
        folder_path='./designs',
        limit=10  # Start small for testing
    )
    
    uploader.quit()
    
    print("\n✅ Upload complete!")
    print("Check pod_uploader_2026.log for details")


if __name__ == "__main__":
    main()