#!/usr/bin/env python3
"""
Discover Real Senate Hearings
Find actual, accessible Senate hearings for processing
"""

import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup

class HearingDiscoverer:
    def __init__(self):
        self.discovered_hearings = []
        
    def discover_commerce_hearings(self):
        """Discover hearings from Commerce Committee"""
        
        print("🔍 Discovering Commerce Committee hearings...")
        
        try:
            # Commerce Committee hearings page
            url = "https://www.commerce.senate.gov/hearings"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for hearing links
                hearing_links = soup.find_all('a', href=True)
                
                commerce_hearings = []
                for link in hearing_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # Filter for hearing pages
                    if ('/hearings/' in href or '/hearing/' in href) and len(text) > 20:
                        full_url = href if href.startswith('http') else f"https://www.commerce.senate.gov{href}"
                        
                        hearing = {
                            'title': text,
                            'url': full_url,
                            'committee': 'Commerce, Science, and Transportation',
                            'source': 'commerce.senate.gov'
                        }
                        commerce_hearings.append(hearing)
                
                print(f"   Found {len(commerce_hearings)} potential hearings")
                return commerce_hearings[:3]  # Return first 3
                
        except Exception as e:
            print(f"   Error discovering commerce hearings: {e}")
            return []
    
    def discover_judiciary_hearings(self):
        """Discover hearings from Judiciary Committee"""
        
        print("🔍 Discovering Judiciary Committee hearings...")
        
        try:
            url = "https://www.judiciary.senate.gov/committee-activity/hearings"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                hearing_links = soup.find_all('a', href=True)
                
                judiciary_hearings = []
                for link in hearing_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    if ('/hearings/' in href or '/hearing/' in href) and len(text) > 20:
                        full_url = href if href.startswith('http') else f"https://www.judiciary.senate.gov{href}"
                        
                        hearing = {
                            'title': text,
                            'url': full_url,
                            'committee': 'Judiciary',
                            'source': 'judiciary.senate.gov'
                        }
                        judiciary_hearings.append(hearing)
                
                print(f"   Found {len(judiciary_hearings)} potential hearings")
                return judiciary_hearings[:2]  # Return first 2
                
        except Exception as e:
            print(f"   Error discovering judiciary hearings: {e}")
            return []
    
    def test_hearing_accessibility(self, hearing):
        """Test if a discovered hearing is accessible"""
        
        try:
            response = requests.get(hearing['url'], timeout=10)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Look for media indicators
                media_keywords = [
                    'video', 'audio', 'stream', 'isvp', 'player', 
                    'webcast', 'recording', 'media', 'live'
                ]
                
                media_score = sum(1 for keyword in media_keywords if keyword in content)
                
                hearing['accessible'] = True
                hearing['media_score'] = media_score
                hearing['likely_has_media'] = media_score >= 2
                
                return True
            else:
                hearing['accessible'] = False
                hearing['error'] = f"HTTP {response.status_code}"
                return False
                
        except Exception as e:
            hearing['accessible'] = False
            hearing['error'] = str(e)
            return False
    
    def discover_and_validate_hearings(self):
        """Discover and validate real hearings"""
        
        print("🚀 Discovering Real Senate Hearings")
        print("=" * 50)
        
        all_hearings = []
        
        # Discover from multiple committees
        all_hearings.extend(self.discover_commerce_hearings())
        all_hearings.extend(self.discover_judiciary_hearings())
        
        print(f"\n📊 Total discovered: {len(all_hearings)} hearings")
        
        # Test accessibility
        print("\n🔍 Testing hearing accessibility...")
        accessible_hearings = []
        
        for i, hearing in enumerate(all_hearings, 1):
            print(f"   {i}/{len(all_hearings)}: {hearing['title'][:50]}...")
            
            if self.test_hearing_accessibility(hearing):
                accessible_hearings.append(hearing)
                media_status = "✅ Likely has media" if hearing.get('likely_has_media') else "⚠️ Media unclear"
                print(f"      ✅ Accessible - {media_status}")
            else:
                error = hearing.get('error', 'Unknown error')
                print(f"      ❌ Not accessible - {error}")
        
        print(f"\n✅ Accessible hearings: {len(accessible_hearings)}")
        
        # Create target list for processing
        target_hearings = []
        for hearing in accessible_hearings:
            target = {
                'id': self.create_hearing_id(hearing['title']),
                'title': hearing['title'],
                'committee': hearing['committee'],
                'url': hearing['url'],
                'source': hearing['source'],
                'media_score': hearing.get('media_score', 0),
                'likely_has_media': hearing.get('likely_has_media', False)
            }
            target_hearings.append(target)
        
        self.discovered_hearings = target_hearings
        self.generate_discovery_report()
        
        return target_hearings
    
    def create_hearing_id(self, title):
        """Create a hearing ID from title"""
        # Clean title and create ID
        import re
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
        words = clean_title.lower().split()
        return '-'.join(words[:4]) + f"-{datetime.now().strftime('%Y')}"
    
    def generate_discovery_report(self):
        """Generate discovery report"""
        
        print("\n" + "=" * 50)
        print("📊 HEARING DISCOVERY REPORT")
        print("=" * 50)
        
        total = len(self.discovered_hearings)
        with_media = sum(1 for h in self.discovered_hearings if h.get('likely_has_media'))
        
        print(f"🎯 Total Accessible Hearings: {total}")
        print(f"📺 Likely Have Media: {with_media}")
        
        if total > 0:
            print("\n📋 Discovered Hearings:")
            for i, hearing in enumerate(self.discovered_hearings, 1):
                media_icon = "📺" if hearing.get('likely_has_media') else "📄"
                print(f"{i}. {media_icon} {hearing['title']}")
                print(f"   Committee: {hearing['committee']}")
                print(f"   URL: {hearing['url']}")
                print(f"   Media Score: {hearing.get('media_score', 0)}/8")
                print()
        
        return total > 0

def main():
    discoverer = HearingDiscoverer()
    
    try:
        hearings = discoverer.discover_and_validate_hearings()
        
        if hearings:
            print("✅ Ready to process real hearings!")
            
            # Save discovered hearings for processing
            output_file = "discovered_hearings.json"
            with open(output_file, 'w') as f:
                json.dump(hearings, f, indent=2)
            print(f"💾 Saved hearings to {output_file}")
        else:
            print("❌ No accessible hearings found")
            
    except KeyboardInterrupt:
        print("\n⚠️ Discovery interrupted")
    except Exception as e:
        print(f"\n❌ Discovery failed: {e}")

if __name__ == "__main__":
    main()