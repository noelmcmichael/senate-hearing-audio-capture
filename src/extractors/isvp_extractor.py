"""ISVP (In-House Streaming Video Player) stream extractor with multi-committee support."""

import re
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin

# Add src to path for committee_config import
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.base_extractor import BaseExtractor, StreamInfo
from utils.page_inspector import PageInspector
from committee_config import CommitteeResolver, SENATE_COMMITTEES


class ISVPExtractor(BaseExtractor):
    """Enhanced ISVP extractor supporting multiple Senate committees."""
    
    def __init__(self):
        """Initialize with committee resolver."""
        self.committee_resolver = CommitteeResolver()
    
    def can_extract(self, url: str) -> bool:
        """Check if this extractor can handle the given URL."""
        # Check if URL matches any known Senate committee
        committee = self.committee_resolver.identify_committee(url)
        if committee:
            config = self.committee_resolver.get_committee_config(committee)
            return config and config.get('isvp_compatible', False)
        
        # Fallback to domain checking for general senate.gov URLs
        senate_domains = [
            'senate.gov',
            'commerce.senate.gov',
            'judiciary.senate.gov',
            'intelligence.senate.gov',
            'banking.senate.gov'
        ]
        
        return any(domain in url.lower() for domain in senate_domains)
    
    def extract_streams(self, url: str) -> List[StreamInfo]:
        """Extract ISVP stream information from the given URL with multi-committee support."""
        streams = []
        
        # Identify committee for enhanced metadata
        committee = self.committee_resolver.identify_committee(url)
        committee_config = self.committee_resolver.get_committee_config(committee) if committee else None
        
        try:
            with PageInspector(headless=True, timeout=15000) as inspector:
                analysis = inspector.analyze_page(url)
            
            # Look for HLS streams in network requests
            for request in analysis.get('network_requests', []):
                if request['url'].endswith('.m3u8'):
                    stream = StreamInfo(
                        url=request['url'],
                        format_type='hls',
                        title=self._extract_title_from_url(url, committee),
                        metadata={
                            'source': 'network_request',
                            'referer': url,
                            'user_agent': request.get('headers', {}).get('user-agent', ''),
                            'original_page': url,
                            'committee': committee,
                            'committee_description': committee_config.get('description') if committee_config else None,
                            'stream_type': self._identify_stream_type(request['url'])
                        }
                    )
                    streams.append(stream)
            
            # Look for streams in ISVP player analysis
            for player in analysis.get('players_found', []):
                if player.get('type') == 'isvp':
                    potential_streams = player.get('potential_streams', [])
                    for stream_url in potential_streams:
                        if stream_url.endswith('.m3u8') or 'hls' in stream_url.lower():
                            stream = StreamInfo(
                                url=stream_url,
                                format_type='hls',
                                title=self._extract_title_from_url(url, committee),
                                metadata={
                                    'source': 'dom_analysis',
                                    'referer': url,
                                    'original_page': url,
                                    'committee': committee,
                                    'committee_description': committee_config.get('description') if committee_config else None,
                                    'stream_type': self._identify_stream_type(stream_url)
                                }
                            )
                            streams.append(stream)
            
            # If no streams found via page inspection, try constructing URLs
            if not streams and committee and committee_config and committee_config.get('isvp_compatible'):
                constructed_streams = self._try_construct_stream_urls(url, committee)
                streams.extend(constructed_streams)
            
            # Remove duplicates
            seen_urls = set()
            unique_streams = []
            for stream in streams:
                if stream.url not in seen_urls:
                    seen_urls.add(stream.url)
                    unique_streams.append(stream)
            
            return unique_streams
            
        except Exception as e:
            # Log error but don't fail completely
            print(f"Error extracting ISVP streams for {committee or 'unknown committee'}: {e}")
            return []
    
    def get_priority(self) -> int:
        """Get the priority of this extractor."""
        return 10  # High priority for Senate pages
    
    def _identify_stream_type(self, stream_url: str) -> str:
        """Identify whether stream is live or archive."""
        if 'msl3archive' in stream_url:
            return 'archive'
        elif 'media-srs' in stream_url:
            return 'live'
        else:
            return 'unknown'
    
    def _try_construct_stream_urls(self, url: str, committee: str) -> List[StreamInfo]:
        """Try to construct stream URLs when page inspection fails."""
        streams = []
        
        try:
            # Extract date from URL
            date_str = self.committee_resolver.extract_date_from_url(url)
            if not date_str:
                return streams
            
            # Construct potential stream URLs
            potential_urls = self.committee_resolver.construct_stream_urls(committee, date_str)
            
            for stream_url in potential_urls:
                stream = StreamInfo(
                    url=stream_url,
                    format_type='hls',
                    title=self._extract_title_from_url(url, committee),
                    metadata={
                        'source': 'constructed',
                        'referer': url,
                        'original_page': url,
                        'committee': committee,
                        'stream_type': self._identify_stream_type(stream_url),
                        'constructed_date': date_str
                    }
                )
                streams.append(stream)
            
            return streams
            
        except Exception as e:
            print(f"Error constructing stream URLs for {committee}: {e}")
            return []
    
    def _extract_title_from_url(self, url: str, committee: Optional[str] = None) -> Optional[str]:
        """Extract a reasonable title from the URL with committee context."""
        try:
            # Start with committee name if available
            title_parts = []
            if committee:
                committee_config = self.committee_resolver.get_committee_config(committee)
                if committee_config:
                    title_parts.append(f"{committee} Committee")
            
            # Extract from URL path
            path_parts = url.split('/')
            
            # Look for date-like patterns and descriptive parts
            for part in path_parts:
                if re.match(r'\d{4}', part):  # Year
                    title_parts.append(part)
                elif re.match(r'\d{1,2}', part):  # Month/day
                    title_parts.append(part)
                elif part.replace('-', '').replace('_', '').isalnum() and len(part) > 3:
                    # Descriptive part
                    title_parts.append(part.replace('-', ' ').replace('_', ' ').title())
            
            if title_parts:
                return ' - '.join(title_parts)
            
            return f"{committee} Committee Hearing" if committee else "Senate Hearing"
            
        except Exception:
            return f"{committee} Committee Hearing" if committee else "Senate Hearing"