#!/usr/bin/env python3
"""
Senate Committee Configuration for Multi-Committee ISVP Support

Updated with confirmed compatibility and stream patterns for all priority committees.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional

# Enhanced Senate Committee Configuration with ISVP stream patterns
SENATE_COMMITTEES = {
    'Commerce': {
        'base_url': 'https://www.commerce.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Commerce, Science, and Transportation',
        'isvp_compatible': True,
        'stream_id': '2036779',
        'url_pattern': 'commerce',
        'archive_pattern': 'commerce',
        'tested': True,
        'priority': 1
    },
    'Intelligence': {
        'base_url': 'https://www.intelligence.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Intelligence',
        'isvp_compatible': True,
        'stream_id': '2036790',
        'url_pattern': 'intel',
        'archive_pattern': 'intelligence',
        'tested': True,
        'priority': 2
    },
    'Banking': {
        'base_url': 'https://www.banking.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Banking, Housing, and Urban Affairs',
        'isvp_compatible': True,
        'stream_id': '2036799',
        'url_pattern': 'banking',
        'archive_pattern': 'banking',
        'tested': True,
        'priority': 3
    },
    'Judiciary': {
        'base_url': 'https://www.judiciary.senate.gov',
        'hearings_path': '/committee-activity/hearings',
        'description': 'Judiciary',
        'isvp_compatible': True,
        'stream_id': '2036788',
        'url_pattern': 'judiciary',
        'archive_pattern': 'judiciary',
        'tested': True,
        'priority': 4
    },
    'Finance': {
        'base_url': 'https://www.finance.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Finance',
        'isvp_compatible': False,  # Not yet tested
        'stream_id': None,
        'url_pattern': None,
        'archive_pattern': None,
        'tested': False,
        'priority': 5
    },
    'Armed Services': {
        'base_url': 'https://www.armed-services.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Armed Services',
        'isvp_compatible': False,  # Not yet tested
        'stream_id': None,
        'url_pattern': None,
        'archive_pattern': None,
        'tested': False,
        'priority': 6
    },
    'HELP': {
        'base_url': 'https://www.help.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Health, Education, Labor and Pensions',
        'isvp_compatible': False,  # Not yet tested
        'stream_id': None,
        'url_pattern': None,
        'archive_pattern': None,
        'tested': False,
        'priority': 7
    },
    'Foreign Relations': {
        'base_url': 'https://www.foreign.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Foreign Relations',
        'isvp_compatible': False,  # Not yet tested
        'stream_id': None,
        'url_pattern': None,
        'archive_pattern': None,
        'tested': False,
        'priority': 8
    },
    'Homeland Security': {
        'base_url': 'https://www.hsgac.senate.gov',
        'hearings_path': '/hearings',
        'description': 'Homeland Security and Governmental Affairs',
        'isvp_compatible': False,  # Not yet tested
        'stream_id': None,
        'url_pattern': None,
        'archive_pattern': None,
        'tested': False,
        'priority': 9
    },
    'Environment': {
        'base_url': 'https://www.epw.senate.gov',
        'hearings_path': '/public/index.cfm/hearings',
        'description': 'Environment and Public Works',
        'isvp_compatible': False,  # Not yet tested
        'stream_id': None,
        'url_pattern': None,
        'archive_pattern': None,
        'tested': False,
        'priority': 10
    }
}

# ISVP Stream URL Templates
ISVP_STREAM_TEMPLATES = {
    'live': 'https://www-senate-gov-media-srs.akamaized.net/hls/live/{stream_id}/{pattern}/{pattern}{date}/master.m3u8',
    'archive': 'https://www-senate-gov-msl3archive.akamaized.net/{archive_pattern}/{pattern}{date}_1/master.m3u8'
}


class CommitteeResolver:
    """Resolves committee information from URLs and provides stream patterns."""
    
    @staticmethod
    def identify_committee(url: str) -> Optional[str]:
        """Identify committee from URL."""
        url_lower = url.lower()
        
        for committee_name, config in SENATE_COMMITTEES.items():
            base_domain = config['base_url'].replace('https://', '').replace('http://', '')
            if base_domain in url_lower:
                return committee_name
        
        return None
    
    @staticmethod
    def get_committee_config(committee_name: str) -> Optional[Dict]:
        """Get configuration for a specific committee."""
        return SENATE_COMMITTEES.get(committee_name)
    
    @staticmethod
    def get_isvp_compatible_committees() -> List[str]:
        """Get list of ISVP-compatible committees."""
        return [
            name for name, config in SENATE_COMMITTEES.items()
            if config.get('isvp_compatible', False)
        ]
    
    @staticmethod
    def extract_date_from_url(url: str) -> Optional[str]:
        """Extract date pattern from URL for stream URL construction."""
        # Look for date patterns in URL
        # Format: MMDDYY
        date_patterns = [
            r'/(\d{2})(\d{2})(\d{2})/',  # /062625/
            r'/(\d{2})/(\d{2})/(\d{4})/',  # /06/26/2025/
            r'(\d{2})-(\d{2})-(\d{4})',  # 06-26-2025
            r'(\d{2})_(\d{2})_(\d{4})',  # 06_26_2025
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, url)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    if len(groups[2]) == 4:  # Full year
                        month, day, year = groups[0], groups[1], groups[2][-2:]
                        return f"{month}{day}{year}"
                    else:  # Already MMDDYY format
                        return f"{groups[0]}{groups[1]}{groups[2]}"
        
        return None
    
    @staticmethod
    def construct_stream_urls(committee_name: str, date_str: str) -> List[str]:
        """Construct potential ISVP stream URLs for a committee and date."""
        config = SENATE_COMMITTEES.get(committee_name)
        if not config or not config.get('isvp_compatible'):
            return []
        
        urls = []
        
        # Live stream URL
        live_url = ISVP_STREAM_TEMPLATES['live'].format(
            stream_id=config['stream_id'],
            pattern=config['url_pattern'],
            date=date_str
        )
        urls.append(live_url)
        
        # Archive stream URL
        archive_url = ISVP_STREAM_TEMPLATES['archive'].format(
            archive_pattern=config['archive_pattern'],
            pattern=config['url_pattern'],
            date=date_str
        )
        urls.append(archive_url)
        
        return urls
    
    @staticmethod
    def get_priority_committees() -> List[str]:
        """Get committees sorted by priority."""
        sorted_committees = sorted(
            SENATE_COMMITTEES.items(),
            key=lambda x: x[1].get('priority', 999)
        )
        return [name for name, config in sorted_committees if config.get('isvp_compatible')]


def get_committee_summary() -> Dict:
    """Get summary of committee compatibility status."""
    total_committees = len(SENATE_COMMITTEES)
    isvp_compatible = sum(1 for config in SENATE_COMMITTEES.values() if config.get('isvp_compatible'))
    tested = sum(1 for config in SENATE_COMMITTEES.values() if config.get('tested'))
    
    return {
        'total_committees': total_committees,
        'isvp_compatible': isvp_compatible,
        'tested': tested,
        'coverage_percentage': round((isvp_compatible / total_committees) * 100, 1),
        'compatible_committees': [
            name for name, config in SENATE_COMMITTEES.items() 
            if config.get('isvp_compatible')
        ]
    }


if __name__ == "__main__":
    # Test the committee resolver
    resolver = CommitteeResolver()
    
    print("🏛️ SENATE COMMITTEE CONFIGURATION")
    print("=" * 50)
    
    summary = get_committee_summary()
    print(f"Total Committees: {summary['total_committees']}")
    print(f"ISVP Compatible: {summary['isvp_compatible']}")
    print(f"Coverage: {summary['coverage_percentage']}%")
    
    print(f"\n✅ Compatible Committees:")
    for committee in summary['compatible_committees']:
        config = SENATE_COMMITTEES[committee]
        print(f"  • {committee} ({config['description']})")
    
    print(f"\n🎯 Priority Order:")
    for committee in resolver.get_priority_committees():
        print(f"  {SENATE_COMMITTEES[committee]['priority']}. {committee}")