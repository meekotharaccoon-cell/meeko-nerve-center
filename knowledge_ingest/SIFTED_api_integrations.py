#!/usr/bin/env python3
"""
API INTEGRATIONS FOR FULL AUTONOMY
Connects to all services automatically
"""

import os
import json
import requests
from typing import Dict, List, Optional

class VercelAPI:
    """Vercel deployment automation"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.vercel.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def deploy(self, project_id: str, files: Dict[str, str]) -> Dict:
        """Deploy files to Vercel"""
        url = f"{self.base_url}/v13/deployments"
        
        payload = {
            "name": "autonomous-site",
            "project": project_id,
            "files": files,
            "target": "production"
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def get_deployments(self, project_id: str) -> List[Dict]:
        """Get deployment history"""
        url = f"{self.base_url}/v6/deployments"
        params = {"projectId": project_id}
        
        response = requests.get(url, headers=self.headers, params=params)
        return response.json().get("deployments", [])

class NetlifyAPI:
    """Netlify deployment automation"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.netlify.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def deploy(self, site_id: str, files: Dict[str, str]) -> Dict:
        """Deploy files to Netlify"""
        url = f"{self.base_url}/sites/{site_id}/deploys"
        
        payload = {"files": files}
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()

class BeehiivAPI:
    """Beehiiv email automation"""
    
    def __init__(self, api_key: str, publication_id: str):
        self.api_key = api_key
        self.publication_id = publication_id
        self.base_url = "https://api.beehiiv.com/v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_post(self, title: str, content: str, status: str = "draft") -> Dict:
        """Create newsletter post"""
        url = f"{self.base_url}/publications/{self.publication_id}/posts"
        
        payload = {
            "title": title,
            "content": content,
            "status": status
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def schedule_post(self, post_id: str, publish_at: str) -> Dict:
        """Schedule post for later"""
        url = f"{self.base_url}/publications/{self.publication_id}/posts/{post_id}"
        
        payload = {
            "status": "scheduled",
            "publish_at": publish_at
        }
        
        response = requests.patch(url, headers=self.headers, json=payload)
        return response.json()
    
    def get_subscribers(self) -> List[Dict]:
        """Get subscriber list"""
        url = f"{self.base_url}/publications/{self.publication_id}/subscriptions"
        
        response = requests.get(url, headers=self.headers)
        return response.json().get("data", [])

class BufferAPI:
    """Buffer social media automation"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.bufferapp.com/1"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def get_profiles(self) -> List[Dict]:
        """Get connected social profiles"""
        url = f"{self.base_url}/profiles.json"
        
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def create_update(self, profile_ids: List[str], text: str, 
                      scheduled_at: Optional[str] = None) -> Dict:
        """Schedule social media post"""
        url = f"{self.base_url}/updates/create.json"
        
        payload = {
            "profile_ids": profile_ids,
            "text": text
        }
        
        if scheduled_at:
            payload["scheduled_at"] = scheduled_at
        
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def schedule_posts(self, posts: List[Dict]) -> List[Dict]:
        """Schedule multiple posts"""
        profiles = self.get_profiles()
        profile_ids = [p["id"] for p in profiles]
        
        results = []
        for post in posts:
            result = self.create_update(
                profile_ids=profile_ids,
                text=post["text"],
                scheduled_at=post.get("scheduled_at")
            )
            results.append(result)
        
        return results

class AmazonPAAPI:
    """Amazon Product Advertising API"""
    
    def __init__(self, access_key: str, secret_key: str, partner_tag: str, 
                 region: str = "us-east-1"):
        self.access_key = access_key
        self.secret_key = secret_key
        self.partner_tag = partner_tag
        self.region = region
        self.base_url = f"https://webservices.amazon.com/paapi5"
    
    def search_items(self, keywords: str, search_index: str = "All") -> Dict:
        """Search for products"""
        # This requires AWS Signature V4 authentication
        # Implementation would use boto3 or custom signing
        pass
    
    def get_items(self, asins: List[str]) -> Dict:
        """Get product details by ASIN"""
        pass
    
    def generate_link(self, asin: str) -> str:
        """Generate affiliate link"""
        return f"https://www.amazon.com/dp/{asin}?tag={self.partner_tag}"

class GoogleAnalyticsAPI:
    """Google Analytics 4 automation"""
    
    def __init__(self, service_account_file: str, property_id: str):
        from google.analytics.data import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import RunReportRequest
        
        self.client = BetaAnalyticsDataClient.from_service_account_file(
            service_account_file
        )
        self.property_id = property_id
    
    def get_traffic_report(self, start_date: str, end_date: str) -> Dict:
        """Get website traffic report"""
        from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
        
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="screenPageViews"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration")
            ]
        )
        
        response = self.client.run_report(request)
        
        return {
            "sessions": response.rows[0].metric_values[0].value,
            "users": response.rows[0].metric_values[1].value,
            "pageviews": response.rows[0].metric_values[2].value,
            "bounce_rate": response.rows[0].metric_values[3].value,
            "avg_session": response.rows[0].metric_values[4].value
        }

class NamecheapAPI:
    """Namecheap domain automation"""
    
    def __init__(self, api_key: str, username: str, client_ip: str):
        self.api_key = api_key
        self.username = username
        self.client_ip = client_ip
        self.base_url = "https://api.namecheap.com/xml.response"
    
    def get_domains(self) -> List[Dict]:
        """Get list of domains"""
        params = {
            "ApiUser": self.username,
            "ApiKey": self.api_key,
            "UserName": self.username,
            "Command": "namecheap.domains.getList",
            "ClientIp": self.client_ip
        }
        
        response = requests.get(self.base_url, params=params)
        # Parse XML response
        return []
    
    def set_dns(self, domain: str, records: List[Dict]) -> bool:
        """Set DNS records"""
        # Implementation for setting DNS
        pass

class CloudflareAPI:
    """Cloudflare automation"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def get_zones(self) -> List[Dict]:
        """Get DNS zones"""
        url = f"{self.base_url}/zones"
        
        response = requests.get(url, headers=self.headers)
        return response.json().get("result", [])
    
    def create_dns_record(self, zone_id: str, record_type: str, 
                          name: str, content: str) -> Dict:
        """Create DNS record"""
        url = f"{self.base_url}/zones/{zone_id}/dns_records"
        
        payload = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": 1  # Auto
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()

# Unified API Manager
class APIManager:
    """Manage all API connections"""
    
    def __init__(self, config_file: str = "deployment_config.json"):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.apis = {}
    
    def get_vercel(self) -> VercelAPI:
        """Get Vercel API instance"""
        if 'vercel' not in self.apis:
            token = self.config['hosting']['token']
            self.apis['vercel'] = VercelAPI(token)
        return self.apis['vercel']
    
    def get_beehiiv(self) -> BeehiivAPI:
        """Get Beehiiv API instance"""
        if 'beehiiv' not in self.apis:
            api_key = self.config['email']['api_key']
            pub_id = self.config['email']['publication_id']
            self.apis['beehiiv'] = BeehiivAPI(api_key, pub_id)
        return self.apis['beehiiv']
    
    def get_buffer(self) -> BufferAPI:
        """Get Buffer API instance"""
        if 'buffer' not in self.apis:
            token = self.config['social']['buffer']['access_token']
            self.apis['buffer'] = BufferAPI(token)
        return self.apis['buffer']
    
    def get_cloudflare(self) -> CloudflareAPI:
        """Get Cloudflare API instance"""
        if 'cloudflare' not in self.apis:
            # Cloudflare token would be in config
            token = self.config.get('domain', {}).get('cloudflare_token', '')
            self.apis['cloudflare'] = CloudflareAPI(token)
        return self.apis['cloudflare']
    
    def test_all_connections(self) -> Dict[str, bool]:
        """Test all API connections"""
        results = {}
        
        # Test each API
        try:
            vercel = self.get_vercel()
            vercel.get_deployments("test")
            results['vercel'] = True
        except Exception as e:
            results['vercel'] = False
            print(f"Vercel API error: {e}")
        
        try:
            beehiiv = self.get_beehiiv()
            beehiiv.get_subscribers()
            results['beehiiv'] = True
        except Exception as e:
            results['beehiiv'] = False
            print(f"Beehiiv API error: {e}")
        
        try:
            buffer = self.get_buffer()
            buffer.get_profiles()
            results['buffer'] = True
        except Exception as e:
            results['buffer'] = False
            print(f"Buffer API error: {e}")
        
        return results

# Usage example
if __name__ == "__main__":
    # Test all APIs
    manager = APIManager()
    results = manager.test_all_connections()
    
    print("\nAPI Connection Test Results:")
    print("=" * 40)
    for api, status in results.items():
        symbol = "✅" if status else "❌"
        print(f"{symbol} {api}: {'Connected' if status else 'Failed'}")
