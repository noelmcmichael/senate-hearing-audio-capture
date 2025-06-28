"""
Extraction Orchestrator - Intelligent Platform Detection and Stream Extraction

Manages multiple extractors (ISVP, YouTube) and automatically selects the best 
approach based on URL patterns and content detection.
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.base_extractor import BaseExtractor, StreamInfo
from extractors.isvp_extractor import ISVPExtractor
from extractors.youtube_extractor import YouTubeExtractor
from committee_config import CommitteeResolver
from house_committee_config import HouseCommitteeResolver


class ExtractionOrchestrator:
    """Orchestrates multiple extractors for comprehensive congressional hearing coverage."""
    
    def __init__(self):
        """Initialize with all available extractors."""
        self.extractors = [
            ISVPExtractor(),    # Priority 1: Senate ISVP streams
            YouTubeExtractor()  # Priority 2: YouTube fallback (House committees, etc.)
        ]
        
        # Initialize resolvers for enhanced detection
        self.senate_resolver = CommitteeResolver()
        self.house_resolver = HouseCommitteeResolver()
        
        # Sort by priority (higher priority first)
        self.extractors.sort(key=lambda x: x.get_priority(), reverse=True)
    
    def extract_streams(self, url: str, prefer_platform: Optional[str] = None) -> Tuple[List[StreamInfo], str]:
        """
        Extract streams using the best available extractor.
        
        Args:
            url: The URL to extract from
            prefer_platform: Optional platform preference ('isvp', 'youtube')
            
        Returns:
            Tuple of (streams, extractor_used)
        """
        # If platform preference is specified, try that first
        if prefer_platform:
            preferred_extractor = self._get_extractor_by_type(prefer_platform)
            if preferred_extractor and preferred_extractor.can_extract(url):
                streams = preferred_extractor.extract_streams(url)
                if streams:
                    return streams, prefer_platform
        
        # Try extractors in priority order
        for extractor in self.extractors:
            if extractor.can_extract(url):
                print(f"🔧 Using {extractor.__class__.__name__} for {url[:50]}...")
                
                try:
                    streams = extractor.extract_streams(url)
                    if streams:
                        extractor_type = self._get_extractor_type(extractor)
                        return streams, extractor_type
                except Exception as e:
                    print(f"   ❌ {extractor.__class__.__name__} failed: {e}")
                    continue
        
        return [], 'none'
    
    def detect_platform(self, url: str) -> Dict[str, Any]:
        """
        Detect the platform and provide detailed analysis.
        
        Returns:
            Dictionary with platform information and capabilities
        """
        parsed_url = urlparse(url.lower())
        domain = parsed_url.netloc.replace('www.', '')
        
        platform_info = {
            'url': url,
            'domain': domain,
            'detected_platform': 'unknown',
            'congressional_type': 'unknown',
            'recommended_extractor': 'none',
            'available_extractors': [],
            'confidence': 0
        }
        
        # Check each extractor
        for extractor in self.extractors:
            if extractor.can_extract(url):
                extractor_type = self._get_extractor_type(extractor)
                platform_info['available_extractors'].append(extractor_type)
        
        # Enhanced platform detection with committee-specific analysis
        if 'senate.gov' in domain:
            # Check if it's a supported Senate committee
            senate_committee = self.senate_resolver.identify_committee(url)
            senate_config = self.senate_resolver.get_committee_config(senate_committee) if senate_committee else None
            
            if senate_config and senate_config.get('isvp_compatible'):
                platform_info.update({
                    'detected_platform': 'senate_isvp',
                    'congressional_type': 'senate',
                    'recommended_extractor': 'isvp',
                    'confidence': 95,
                    'committee': senate_committee,
                    'committee_info': senate_config.get('description')
                })
            else:
                platform_info.update({
                    'detected_platform': 'senate_unknown',
                    'congressional_type': 'senate',
                    'recommended_extractor': 'youtube',  # Fallback
                    'confidence': 50,
                    'committee': senate_committee
                })
                
        elif any(yt_domain in domain for yt_domain in ['youtube.com', 'youtu.be']):
            # Enhanced YouTube detection with House committee recognition
            house_committee = self.house_resolver.identify_house_committee(url)
            
            if house_committee:
                house_config = self.house_resolver.get_committee_config(house_committee)
                platform_info.update({
                    'detected_platform': 'house_youtube',
                    'congressional_type': 'house',
                    'recommended_extractor': 'youtube',
                    'confidence': 95,
                    'committee': house_committee,
                    'committee_info': house_config.get('description') if house_config else None
                })
            else:
                platform_info.update({
                    'detected_platform': 'youtube',
                    'congressional_type': self._detect_congressional_type_from_url(url),
                    'recommended_extractor': 'youtube',
                    'confidence': 90
                })
                
        elif 'house.gov' in domain:
            # House committee website detection
            house_committee = self.house_resolver.identify_house_committee(url)
            house_config = self.house_resolver.get_committee_config(house_committee) if house_committee else None
            
            platform_info.update({
                'detected_platform': 'house_website',
                'congressional_type': 'house',
                'recommended_extractor': 'youtube',  # House primarily uses YouTube
                'confidence': 80,
                'committee': house_committee,
                'committee_info': house_config.get('description') if house_config else None
            })
        
        return platform_info
    
    def get_extraction_strategy(self, url: str) -> Dict[str, Any]:
        """
        Get recommended extraction strategy for a URL.
        
        Returns:
            Strategy information including primary and fallback options
        """
        platform_info = self.detect_platform(url)
        
        strategy = {
            'primary_extractor': platform_info['recommended_extractor'],
            'fallback_extractors': [],
            'extraction_order': [],
            'expected_success_rate': 0,
            'notes': []
        }
        
        # Define extraction order based on platform
        if platform_info['detected_platform'] == 'senate_isvp':
            strategy.update({
                'extraction_order': ['isvp'],
                'expected_success_rate': 95,
                'notes': ['Senate ISVP streams have high reliability']
            })
        elif platform_info['detected_platform'] == 'youtube':
            strategy.update({
                'extraction_order': ['youtube'],
                'expected_success_rate': 85,
                'notes': ['YouTube streams may require format selection']
            })
        elif platform_info['congressional_type'] == 'house':
            strategy.update({
                'extraction_order': ['youtube', 'isvp'],
                'fallback_extractors': ['isvp'],
                'expected_success_rate': 75,
                'notes': ['House committees primarily use YouTube', 'ISVP fallback available']
            })
        else:
            strategy.update({
                'extraction_order': ['youtube', 'isvp'],
                'fallback_extractors': ['isvp'],
                'expected_success_rate': 50,
                'notes': ['Unknown platform - trying all extractors']
            })
        
        return strategy
    
    def _get_extractor_by_type(self, extractor_type: str) -> Optional[BaseExtractor]:
        """Get extractor instance by type name."""
        type_mapping = {
            'isvp': ISVPExtractor,
            'youtube': YouTubeExtractor
        }
        
        target_class = type_mapping.get(extractor_type.lower())
        if target_class:
            for extractor in self.extractors:
                if isinstance(extractor, target_class):
                    return extractor
        
        return None
    
    def _get_extractor_type(self, extractor: BaseExtractor) -> str:
        """Get the type name for an extractor instance."""
        if isinstance(extractor, ISVPExtractor):
            return 'isvp'
        elif isinstance(extractor, YouTubeExtractor):
            return 'youtube'
        else:
            return 'unknown'
    
    def _detect_congressional_type_from_url(self, url: str) -> str:
        """Detect if URL is related to House or Senate."""
        url_lower = url.lower()
        
        if 'senate' in url_lower:
            return 'senate'
        elif 'house' in url_lower:
            return 'house'
        else:
            return 'unknown'
    
    def test_all_extractors(self, url: str) -> Dict[str, Any]:
        """
        Test all extractors against a URL for debugging.
        
        Returns:
            Detailed results from each extractor
        """
        results = {
            'url': url,
            'platform_detection': self.detect_platform(url),
            'extractor_results': {}
        }
        
        for extractor in self.extractors:
            extractor_type = self._get_extractor_type(extractor)
            extractor_result = {
                'can_extract': False,
                'streams_found': 0,
                'streams': [],
                'error': None,
                'priority': extractor.get_priority()
            }
            
            try:
                extractor_result['can_extract'] = extractor.can_extract(url)
                
                if extractor_result['can_extract']:
                    streams = extractor.extract_streams(url)
                    extractor_result['streams_found'] = len(streams)
                    extractor_result['streams'] = [
                        {
                            'title': stream.title,
                            'url': stream.url[:80] + '...' if len(stream.url) > 80 else stream.url,
                            'format_type': stream.format_type,
                            'metadata_keys': list(stream.metadata.keys())
                        }
                        for stream in streams
                    ]
                
            except Exception as e:
                extractor_result['error'] = str(e)
            
            results['extractor_results'][extractor_type] = extractor_result
        
        return results
    
    def get_supported_platforms(self) -> List[Dict[str, Any]]:
        """Get information about all supported platforms."""
        platforms = []
        
        for extractor in self.extractors:
            extractor_type = self._get_extractor_type(extractor)
            
            if extractor_type == 'isvp':
                platforms.append({
                    'name': 'Senate ISVP',
                    'type': 'isvp',
                    'description': 'US Senate In-House Streaming Video Player',
                    'supported_committees': 4,
                    'priority': extractor.get_priority(),
                    'reliability': 'High',
                    'use_cases': ['Senate committee hearings', 'Live and archive streams']
                })
            elif extractor_type == 'youtube':
                platforms.append({
                    'name': 'YouTube',
                    'type': 'youtube',
                    'description': 'YouTube streaming platform',
                    'supported_committees': 'Multiple House committees',
                    'priority': extractor.get_priority(),
                    'reliability': 'Medium-High',
                    'use_cases': ['House committee hearings', 'Congressional channel content', 'Fallback for Senate']
                })
        
        return platforms


# Convenience functions for easy usage
def extract_congressional_audio(url: str, prefer_platform: Optional[str] = None) -> Tuple[List[StreamInfo], str]:
    """
    Convenience function to extract audio from congressional hearings.
    
    Args:
        url: URL to extract from
        prefer_platform: Optional platform preference
    
    Returns:
        Tuple of (streams, extractor_used)
    """
    orchestrator = ExtractionOrchestrator()
    return orchestrator.extract_streams(url, prefer_platform)


def analyze_congressional_url(url: str) -> Dict[str, Any]:
    """
    Convenience function to analyze a congressional URL.
    
    Args:
        url: URL to analyze
    
    Returns:
        Analysis results including platform detection and extraction strategy
    """
    orchestrator = ExtractionOrchestrator()
    
    return {
        'platform_detection': orchestrator.detect_platform(url),
        'extraction_strategy': orchestrator.get_extraction_strategy(url),
        'supported_platforms': orchestrator.get_supported_platforms()
    }