#!/usr/bin/env python3
"""
House Committee Configuration for YouTube-based extraction

Configuration and discovery system for House of Representatives committees 
that use YouTube for streaming hearings.
"""

import re
from typing import Dict, List, Optional
from datetime import datetime


# House Committees with YouTube streaming capabilities
HOUSE_COMMITTEES = {
    'House Judiciary': {
        'full_name': 'House Committee on the Judiciary',
        'youtube_channel': 'https://www.youtube.com/channel/UCVvv3JRCVQAl6ovogDum4hA',
        'website': 'https://judiciary.house.gov',
        'stream_type': 'youtube',
        'description': 'Constitutional freedoms, civil liberties, law enforcement oversight',
        'priority': 1,
        'keywords': ['judiciary', 'judicial', 'constitutional', 'civil liberties'],
        'active': True
    },
    'House Financial Services': {
        'full_name': 'House Committee on Financial Services',
        'youtube_channel': 'https://www.youtube.com/channel/UCiGw0gRK-daU7Xv4oDMr9Hg',
        'website': 'https://financialservices.house.gov',
        'stream_type': 'youtube',
        'description': 'Banking, securities, insurance, housing policy',
        'priority': 2,
        'keywords': ['financial services', 'banking', 'securities', 'housing'],
        'active': True
    },
    'House Oversight': {
        'full_name': 'House Committee on Oversight and Accountability',
        'youtube_channel': None,  # May use different streaming
        'website': 'https://oversight.house.gov',
        'stream_type': 'mixed',
        'description': 'Government oversight, waste, fraud, and abuse investigation',
        'priority': 3,
        'keywords': ['oversight', 'accountability', 'government reform'],
        'active': True
    },
    'House Energy and Commerce': {
        'full_name': 'House Committee on Energy and Commerce',
        'youtube_channel': None,  # Channel to be discovered
        'website': 'https://energycommerce.house.gov',
        'stream_type': 'mixed',
        'description': 'Energy policy, telecommunications, healthcare, consumer protection',
        'priority': 4,
        'keywords': ['energy', 'commerce', 'telecommunications', 'healthcare'],
        'active': True
    },
    'House Appropriations': {
        'full_name': 'House Committee on Appropriations',
        'youtube_channel': None,
        'website': 'https://appropriations.house.gov',
        'stream_type': 'mixed',
        'description': 'Federal spending and budget appropriations',
        'priority': 5,
        'keywords': ['appropriations', 'budget', 'spending'],
        'active': True
    },
    'House Armed Services': {
        'full_name': 'House Committee on Armed Services',
        'youtube_channel': None,
        'website': 'https://armedservices.house.gov',
        'stream_type': 'mixed',
        'description': 'Defense policy, military affairs, national security',
        'priority': 6,
        'keywords': ['armed services', 'defense', 'military', 'national security'],
        'active': True
    },
    'House Foreign Affairs': {
        'full_name': 'House Committee on Foreign Affairs',
        'youtube_channel': None,
        'website': 'https://foreignaffairs.house.gov',
        'stream_type': 'mixed',
        'description': 'Foreign policy, international relations, diplomacy',
        'priority': 7,
        'keywords': ['foreign affairs', 'international', 'diplomacy'],
        'active': True
    },
    'House Intelligence': {
        'full_name': 'House Permanent Select Committee on Intelligence',
        'youtube_channel': None,
        'website': 'https://intelligence.house.gov',
        'stream_type': 'mixed',
        'description': 'Intelligence oversight, national security',
        'priority': 8,
        'keywords': ['intelligence', 'national security', 'surveillance'],
        'active': True
    },
    'House Education and Workforce': {
        'full_name': 'House Committee on Education and the Workforce',
        'youtube_channel': None,
        'website': 'https://edworkforce.house.gov',
        'stream_type': 'mixed',
        'description': 'Education policy, workforce development, labor relations',
        'priority': 9,
        'keywords': ['education', 'workforce', 'labor'],
        'active': True
    },
    'House Homeland Security': {
        'full_name': 'House Committee on Homeland Security',
        'youtube_channel': None,
        'website': 'https://homeland.house.gov',
        'stream_type': 'mixed',
        'description': 'Homeland security, border security, cybersecurity',
        'priority': 10,
        'keywords': ['homeland security', 'border', 'cybersecurity'],
        'active': True
    }
}


class HouseCommitteeResolver:
    """Resolves House committee information and YouTube channels."""
    
    @staticmethod
    def identify_house_committee(url: str) -> Optional[str]:
        """Identify House committee from URL."""
        url_lower = url.lower()
        
        # Check for direct committee website matches
        for committee_name, config in HOUSE_COMMITTEES.items():
            website = config['website'].replace('https://', '').replace('http://', '')
            if website in url_lower:
                return committee_name
        
        # Check for YouTube channel matches
        for committee_name, config in HOUSE_COMMITTEES.items():
            if config.get('youtube_channel') and config['youtube_channel'] in url:
                return committee_name
        
        # Check for keyword matches in URL
        for committee_name, config in HOUSE_COMMITTEES.items():
            for keyword in config['keywords']:
                if keyword.replace(' ', '') in url_lower:
                    return committee_name
        
        return None
    
    @staticmethod
    def get_committee_config(committee_name: str) -> Optional[Dict]:
        """Get configuration for a specific House committee."""
        return HOUSE_COMMITTEES.get(committee_name)
    
    @staticmethod
    def get_youtube_committees() -> List[str]:
        """Get committees with known YouTube channels."""
        return [
            name for name, config in HOUSE_COMMITTEES.items()
            if config.get('youtube_channel') and config.get('active', True)
        ]
    
    @staticmethod
    def get_priority_committees() -> List[str]:
        """Get House committees sorted by priority."""
        sorted_committees = sorted(
            HOUSE_COMMITTEES.items(),
            key=lambda x: x[1].get('priority', 999)
        )
        return [name for name, config in sorted_committees if config.get('active', True)]
    
    @staticmethod
    def detect_congressional_chamber(url: str) -> str:
        """Detect if URL is House or Senate related."""
        url_lower = url.lower()
        
        if any(domain in url_lower for domain in ['house.gov', 'congress.gov']):
            return 'house'
        elif 'senate.gov' in url_lower:
            return 'senate'
        elif 'youtube.com' in url_lower:
            # Try to determine from content
            committee = HouseCommitteeResolver.identify_house_committee(url)
            if committee:
                return 'house'
        
        return 'unknown'
    
    @staticmethod
    def get_committee_youtube_info(committee_name: str) -> Optional[Dict]:
        """Get YouTube-specific information for a committee."""
        config = HOUSE_COMMITTEES.get(committee_name)
        if not config:
            return None
        
        return {
            'committee': committee_name,
            'full_name': config['full_name'],
            'youtube_channel': config.get('youtube_channel'),
            'has_youtube': bool(config.get('youtube_channel')),
            'stream_type': config.get('stream_type'),
            'keywords': config.get('keywords', [])
        }
    
    @staticmethod
    def search_committees_by_keyword(keyword: str) -> List[str]:
        """Search committees by keyword."""
        keyword_lower = keyword.lower()
        matching_committees = []
        
        for committee_name, config in HOUSE_COMMITTEES.items():
            # Check in committee name
            if keyword_lower in committee_name.lower():
                matching_committees.append(committee_name)
                continue
            
            # Check in full name
            if keyword_lower in config['full_name'].lower():
                matching_committees.append(committee_name)
                continue
            
            # Check in keywords
            if any(keyword_lower in kw.lower() for kw in config.get('keywords', [])):
                matching_committees.append(committee_name)
                continue
            
            # Check in description
            if keyword_lower in config.get('description', '').lower():
                matching_committees.append(committee_name)
        
        return matching_committees


def get_house_committee_summary() -> Dict:
    """Get summary of House committee streaming capabilities."""
    total_committees = len(HOUSE_COMMITTEES)
    youtube_committees = len([c for c in HOUSE_COMMITTEES.values() if c.get('youtube_channel')])
    active_committees = len([c for c in HOUSE_COMMITTEES.values() if c.get('active', True)])
    
    return {
        'total_committees': total_committees,
        'youtube_committees': youtube_committees,
        'active_committees': active_committees,
        'youtube_coverage_percentage': round((youtube_committees / total_committees) * 100, 1),
        'committees_with_youtube': [
            name for name, config in HOUSE_COMMITTEES.items() 
            if config.get('youtube_channel')
        ],
        'priority_committees': HouseCommitteeResolver.get_priority_committees()[:5]
    }


def discover_youtube_capabilities() -> Dict:
    """Discover YouTube streaming capabilities across House committees."""
    summary = get_house_committee_summary()
    
    capabilities = {
        'summary': summary,
        'youtube_ready': [],
        'needs_discovery': [],
        'mixed_streaming': []
    }
    
    for committee_name, config in HOUSE_COMMITTEES.items():
        if not config.get('active', True):
            continue
        
        committee_info = {
            'name': committee_name,
            'full_name': config['full_name'],
            'priority': config.get('priority'),
            'youtube_channel': config.get('youtube_channel'),
            'stream_type': config.get('stream_type')
        }
        
        if config.get('youtube_channel'):
            capabilities['youtube_ready'].append(committee_info)
        elif config.get('stream_type') == 'mixed':
            capabilities['mixed_streaming'].append(committee_info)
        else:
            capabilities['needs_discovery'].append(committee_info)
    
    return capabilities


if __name__ == "__main__":
    # Test the House committee resolver
    resolver = HouseCommitteeResolver()
    
    print("🏛️ HOUSE COMMITTEE CONFIGURATION")
    print("=" * 50)
    
    summary = get_house_committee_summary()
    print(f"Total House Committees: {summary['total_committees']}")
    print(f"YouTube Committees: {summary['youtube_committees']}")
    print(f"YouTube Coverage: {summary['youtube_coverage_percentage']}%")
    
    print(f"\n✅ Committees with YouTube Channels:")
    for committee in summary['committees_with_youtube']:
        config = HOUSE_COMMITTEES[committee]
        print(f"  • {committee}")
        print(f"    Channel: {config['youtube_channel']}")
        print(f"    Priority: {config['priority']}")
    
    print(f"\n🎯 Priority Committees:")
    for i, committee in enumerate(summary['priority_committees'], 1):
        config = HOUSE_COMMITTEES[committee]
        status = "🎬" if config.get('youtube_channel') else "📺"
        print(f"  {i}. {status} {committee}")
    
    # Test URL recognition
    print(f"\n🧪 URL Recognition Test:")
    test_urls = [
        'https://judiciary.house.gov/hearing',
        'https://financialservices.house.gov/videos',
        'https://www.youtube.com/channel/UCVvv3JRCVQAl6ovogDum4hA',
        'https://oversight.house.gov/hearing'
    ]
    
    for url in test_urls:
        identified = resolver.identify_house_committee(url)
        chamber = resolver.detect_congressional_chamber(url)
        print(f"  {url[:50]}... → {identified} ({chamber})")
    
    print(f"\n📊 YouTube Capabilities Discovery:")
    capabilities = discover_youtube_capabilities()
    print(f"  YouTube Ready: {len(capabilities['youtube_ready'])}")
    print(f"  Mixed Streaming: {len(capabilities['mixed_streaming'])}")
    print(f"  Needs Discovery: {len(capabilities['needs_discovery'])}")