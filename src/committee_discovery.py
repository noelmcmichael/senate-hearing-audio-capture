#!/usr/bin/env python3
"""
Senate Committee Discovery and Analysis

Identifies other Senate committees that might use ISVP streaming and
tests their page structures for compatibility with our extraction system.
"""

import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import urljoin

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.page_inspector import PageInspector

# Major Senate Committees with their base URLs
SENATE_COMMITTEES = {
    'Commerce': {
        'base_url': 'https://www.commerce.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Commerce, Science, and Transportation',
        'tested': True,
        'isvp_compatible': True
    },
    'Judiciary': {
        'base_url': 'https://www.judiciary.senate.gov',
        'hearings_path': '/committee-activity/hearings',
        'description': 'Judiciary',
        'tested': False,
        'isvp_compatible': None
    },
    'Finance': {
        'base_url': 'https://www.finance.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Finance',
        'tested': False,
        'isvp_compatible': None
    },
    'Banking': {
        'base_url': 'https://www.banking.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Banking, Housing, and Urban Affairs',
        'tested': False,
        'isvp_compatible': None
    },
    'Armed Services': {
        'base_url': 'https://www.armed-services.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Armed Services',
        'tested': False,
        'isvp_compatible': None
    },
    'HELP': {
        'base_url': 'https://www.help.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Health, Education, Labor and Pensions',
        'tested': False,
        'isvp_compatible': None
    },
    'Foreign Relations': {
        'base_url': 'https://www.foreign.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Foreign Relations',
        'tested': False,
        'isvp_compatible': None
    },
    'Homeland Security': {
        'base_url': 'https://www.hsgac.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Homeland Security and Governmental Affairs',
        'tested': False,
        'isvp_compatible': None
    },
    'Intelligence': {
        'base_url': 'https://www.intelligence.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Intelligence',
        'tested': False,
        'isvp_compatible': None
    },
    'Environment': {
        'base_url': 'https://www.epw.senate.gov',
        'hearings_path': '/public/index.cfm/hearings',
        'description': 'Environment and Public Works',
        'tested': False,
        'isvp_compatible': None
    }
}


class CommitteeDiscovery:
    """Discovers and analyzes Senate committee hearing pages."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 SenateHearingBot/1.0'
        })
    
    def analyze_committee(self, committee_name: str, committee_info: dict) -> dict:
        """Analyze a single committee for ISVP compatibility."""
        print(f"\n🔍 ANALYZING COMMITTEE: {committee_name}")
        print(f"   Description: {committee_info['description']}")
        print(f"   Base URL: {committee_info['base_url']}")
        
        analysis = {
            'committee': committee_name,
            'base_url': committee_info['base_url'],
            'description': committee_info['description'],
            'accessible': False,
            'hearings_found': 0,
            'recent_hearings': [],
            'isvp_compatible': False,
            'sample_analysis': None,
            'error': None
        }
        
        try:
            # Check if hearings page is accessible
            hearings_url = committee_info['base_url'] + committee_info['hearings_path']
            print(f"   Checking: {hearings_url}")
            
            response = self.session.get(hearings_url, timeout=10)
            
            if response.status_code != 200:
                print(f"   ❌ Hearings page not accessible: HTTP {response.status_code}")
                analysis['error'] = f"HTTP {response.status_code}"
                return analysis
            
            analysis['accessible'] = True
            print(f"   ✅ Hearings page accessible")
            
            # Parse hearings page
            recent_hearings = self._extract_recent_hearings(response.text, committee_info['base_url'])
            analysis['recent_hearings'] = recent_hearings
            analysis['hearings_found'] = len(recent_hearings)
            
            print(f"   📋 Found {len(recent_hearings)} recent hearings")
            
            # Test a sample hearing for ISVP compatibility
            if recent_hearings:
                sample_hearing = recent_hearings[0]
                print(f"   🧪 Testing sample: {sample_hearing['title'][:50]}...")
                
                sample_analysis = self._analyze_hearing_page(sample_hearing['url'])
                analysis['sample_analysis'] = sample_analysis
                
                # Check for ISVP compatibility
                if sample_analysis and not sample_analysis.get('error'):
                    has_isvp = any(
                        req['url'].endswith('.m3u8') and 'senate' in req['url'].lower()
                        for req in sample_analysis.get('network_requests', [])
                    )
                    analysis['isvp_compatible'] = has_isvp
                    
                    if has_isvp:
                        print(f"   ✅ ISVP streams detected!")
                    else:
                        print(f"   ⚠️  No ISVP streams found")
                else:
                    print(f"   ❌ Error analyzing sample hearing")
            
            return analysis
            
        except requests.Timeout:
            print(f"   ⏰ Timeout accessing hearings page")
            analysis['error'] = 'timeout'
            return analysis
        except Exception as e:
            print(f"   ❌ Error: {e}")
            analysis['error'] = str(e)
            return analysis
    
    def _extract_recent_hearings(self, html_content: str, base_url: str) -> list:
        """Extract recent hearing URLs from committee hearings page."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            hearings = []
            
            # Look for common patterns in Senate committee pages
            # Pattern 1: Links to hearing pages
            hearing_links = soup.find_all('a', href=True)
            
            for link in hearing_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Skip if it's not a hearing link
                if not text or len(text) < 10:
                    continue
                
                # Look for date patterns or hearing-like text
                if any(keyword in text.lower() for keyword in ['hearing', 'session', 'markup', 'nomination']):
                    full_url = urljoin(base_url, href)
                    
                    # Avoid duplicates and non-hearing pages
                    if not any(h['url'] == full_url for h in hearings):
                        hearings.append({
                            'title': text[:100],  # Truncate long titles
                            'url': full_url
                        })
                
                # Limit to recent hearings
                if len(hearings) >= 5:
                    break
            
            return hearings
            
        except Exception as e:
            print(f"Error extracting hearings: {e}")
            return []
    
    def _analyze_hearing_page(self, url: str) -> dict:
        """Analyze a single hearing page for ISVP content."""
        try:
            with PageInspector(headless=True, timeout=10000) as inspector:
                analysis = inspector.analyze_page(url)
                return analysis
        except Exception as e:
            return {'error': str(e)}
    
    def discover_all_committees(self) -> dict:
        """Analyze all committees for ISVP compatibility."""
        print("🏛️ SENATE COMMITTEE DISCOVERY")
        print("=" * 60)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'committees_analyzed': 0,
            'committees_accessible': 0,
            'committees_isvp_compatible': 0,
            'committee_results': {}
        }
        
        for committee_name, committee_info in SENATE_COMMITTEES.items():
            if committee_info.get('tested', False) and committee_name == 'Commerce':
                print(f"\n⏭️  SKIPPING: {committee_name} (already tested)")
                continue
                
            analysis = self.analyze_committee(committee_name, committee_info)
            results['committee_results'][committee_name] = analysis
            
            results['committees_analyzed'] += 1
            if analysis['accessible']:
                results['committees_accessible'] += 1
            if analysis['isvp_compatible']:
                results['committees_isvp_compatible'] += 1
        
        # Summary
        print(f"\n📊 DISCOVERY SUMMARY")
        print("=" * 40)
        print(f"   Committees analyzed: {results['committees_analyzed']}")
        print(f"   Committees accessible: {results['committees_accessible']}")
        print(f"   ISVP compatible: {results['committees_isvp_compatible']}")
        
        # Compatible committees
        compatible = [
            name for name, result in results['committee_results'].items()
            if result['isvp_compatible']
        ]
        if compatible:
            print(f"\n✅ ISVP Compatible Committees:")
            for committee in compatible:
                print(f"   • {committee}")
        
        return results


def main():
    discovery = CommitteeDiscovery()
    results = discovery.discover_all_committees()
    
    # Save results
    output_file = Path('output') / f'committee_discovery_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved: {output_file}")
    
    # Recommendations
    print(f"\n🎯 RECOMMENDATIONS:")
    compatible_count = results['committees_isvp_compatible']
    
    if compatible_count >= 3:
        print("✅ Excellent! Multiple committees support ISVP - ready for multi-committee deployment")
    elif compatible_count >= 1:
        print("🟡 Some committees support ISVP - can expand gradually")
    else:
        print("❌ Limited ISVP support - may need alternative extraction strategies")


if __name__ == "__main__":
    main()