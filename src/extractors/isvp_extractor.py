"""ISVP (In-House Streaming Video Player) stream extractor."""

import re
from typing import List, Optional
from urllib.parse import urljoin

from extractors.base_extractor import BaseExtractor, StreamInfo
from utils.page_inspector import PageInspector


class ISVPExtractor(BaseExtractor):
    """Extractor for Senate ISVP streams."""
    
    def can_extract(self, url: str) -> bool:
        """Check if this extractor can handle the given URL."""
        senate_domains = [
            'senate.gov',
            'commerce.senate.gov',
            'judiciary.senate.gov',
            'finance.senate.gov',
            'banking.senate.gov'
        ]
        
        return any(domain in url.lower() for domain in senate_domains)
    
    def extract_streams(self, url: str) -> List[StreamInfo]:
        """Extract ISVP stream information from the given URL."""
        streams = []
        
        try:
            with PageInspector(headless=True) as inspector:
                analysis = inspector.analyze_page(url)
            
            # Look for HLS streams in network requests
            for request in analysis.get('network_requests', []):
                if request['url'].endswith('.m3u8'):
                    stream = StreamInfo(
                        url=request['url'],
                        format_type='hls',
                        title=self._extract_title_from_url(url),
                        metadata={
                            'source': 'network_request',
                            'referer': url,
                            'user_agent': request.get('headers', {}).get('user-agent', ''),
                            'original_page': url
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
                                title=self._extract_title_from_url(url),
                                metadata={
                                    'source': 'dom_analysis',
                                    'referer': url,
                                    'original_page': url
                                }
                            )
                            streams.append(stream)
            
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
            print(f"Error extracting ISVP streams: {e}")
            return []
    
    def get_priority(self) -> int:
        """Get the priority of this extractor."""
        return 10  # High priority for Senate pages
    
    def _extract_title_from_url(self, url: str) -> Optional[str]:
        """Extract a reasonable title from the URL."""
        try:
            # Extract from URL path
            path_parts = url.split('/')
            
            # Look for date-like patterns and descriptive parts
            title_parts = []
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
            
            return "Senate Hearing"
            
        except Exception:
            return "Senate Hearing"