"""YouTube stream extractor using yt-dlp for House committee hearings and fallback scenarios."""

import re
import sys
import yt_dlp
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.base_extractor import BaseExtractor, StreamInfo


class YouTubeExtractor(BaseExtractor):
    """Extractor for YouTube streams, primarily for House committee hearings."""
    
    def __init__(self):
        """Initialize YouTube extractor with yt-dlp configuration."""
        self.yt_dlp_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'format': 'bestaudio/best',  # Prefer audio-only streams
            'noplaylist': True,
        }
    
    def can_extract(self, url: str) -> bool:
        """Check if this extractor can handle the given URL."""
        youtube_domains = [
            'youtube.com',
            'youtu.be',
            'm.youtube.com',
            'www.youtube.com'
        ]
        
        parsed_url = urlparse(url.lower())
        domain = parsed_url.netloc.replace('www.', '')
        
        return any(domain.endswith(yt_domain) for yt_domain in youtube_domains)
    
    def extract_streams(self, url: str) -> List[StreamInfo]:
        """Extract YouTube stream information from the given URL."""
        streams = []
        
        try:
            with yt_dlp.YoutubeDL(self.yt_dlp_opts) as ydl:
                # Extract info without downloading
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return streams
                
                # Handle playlists
                if 'entries' in info:
                    # For playlists, process each entry
                    for entry in info['entries']:
                        if entry:
                            stream = self._create_stream_from_info(entry, url)
                            if stream:
                                streams.append(stream)
                else:
                    # Single video
                    stream = self._create_stream_from_info(info, url)
                    if stream:
                        streams.append(stream)
                
                return streams
                
        except Exception as e:
            print(f"Error extracting YouTube streams: {e}")
            return []
    
    def _create_stream_from_info(self, info: Dict[str, Any], original_url: str) -> Optional[StreamInfo]:
        """Create a StreamInfo object from yt-dlp info."""
        try:
            # Determine the best audio format
            formats = info.get('formats', [])
            best_audio_url = None
            best_audio_format = None
            
            # Look for audio-only formats first
            audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
            if audio_formats:
                # Sort by quality (bitrate)
                audio_formats.sort(key=lambda x: x.get('abr', 0) or 0, reverse=True)
                best_format = audio_formats[0]
                best_audio_url = best_format.get('url')
                best_audio_format = 'audio'
            else:
                # Fall back to video formats with audio
                video_formats = [f for f in formats if f.get('acodec') != 'none']
                if video_formats:
                    # Sort by quality
                    video_formats.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)
                    best_format = video_formats[0]
                    best_audio_url = best_format.get('url')
                    best_audio_format = 'video'
            
            if not best_audio_url:
                return None
            
            # Extract metadata
            title = info.get('title', 'YouTube Video')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', '')
            upload_date = info.get('upload_date', '')
            video_id = info.get('id', '')
            
            # Determine if this is a congressional hearing
            is_congressional = self._is_congressional_content(title, uploader, info)
            
            # Extract committee information
            committee_info = self._extract_committee_info(title, uploader, info)
            
            stream = StreamInfo(
                url=best_audio_url,
                format_type='youtube',
                title=title,
                metadata={
                    'source': 'youtube',
                    'video_id': video_id,
                    'duration_seconds': duration,
                    'uploader': uploader,
                    'upload_date': upload_date,
                    'original_page': original_url,
                    'youtube_url': info.get('webpage_url', original_url),
                    'format_type': best_audio_format,
                    'is_congressional': is_congressional,
                    'committee': committee_info.get('committee'),
                    'committee_type': committee_info.get('type'),  # 'house' or 'senate'
                    'is_live': info.get('is_live', False),
                    'view_count': info.get('view_count', 0),
                    'description': info.get('description', '')[:500] if info.get('description') else ''
                }
            )
            
            return stream
            
        except Exception as e:
            print(f"Error creating stream from YouTube info: {e}")
            return None
    
    def _is_congressional_content(self, title: str, uploader: str, info: Dict[str, Any]) -> bool:
        """Determine if this is congressional hearing content."""
        congressional_keywords = [
            'committee', 'hearing', 'congress', 'house', 'senate',
            'subcommittee', 'markup', 'oversight', 'testimony',
            'judiciary', 'financial services', 'appropriations',
            'armed services', 'foreign affairs', 'homeland security'
        ]
        
        # Check title
        title_lower = title.lower()
        if any(keyword in title_lower for keyword in congressional_keywords):
            return True
        
        # Check uploader
        uploader_lower = uploader.lower()
        if any(keyword in uploader_lower for keyword in congressional_keywords):
            return True
        
        # Check description
        description = info.get('description', '').lower()
        if any(keyword in description for keyword in congressional_keywords):
            return True
        
        return False
    
    def _extract_committee_info(self, title: str, uploader: str, info: Dict[str, Any]) -> Dict[str, str]:
        """Extract committee information from video metadata."""
        # House committee patterns
        house_committees = {
            'judiciary': 'House Judiciary Committee',
            'financial services': 'House Financial Services Committee',
            'oversight': 'House Oversight Committee',
            'appropriations': 'House Appropriations Committee',
            'armed services': 'House Armed Services Committee',
            'foreign affairs': 'House Foreign Affairs Committee',
            'homeland security': 'House Homeland Security Committee',
            'education': 'House Education and the Workforce Committee',
            'energy': 'House Energy and Commerce Committee',
            'intelligence': 'House Intelligence Committee',
            'natural resources': 'House Natural Resources Committee',
            'science': 'House Science, Space, and Technology Committee',
            'small business': 'House Small Business Committee',
            'transportation': 'House Transportation and Infrastructure Committee',
            'veterans': 'House Veterans\' Affairs Committee',
            'ways and means': 'House Ways and Means Committee'
        }
        
        # Senate committee patterns (for potential YouTube fallback)
        senate_committees = {
            'commerce': 'Senate Commerce Committee',
            'judiciary': 'Senate Judiciary Committee',
            'banking': 'Senate Banking Committee',
            'intelligence': 'Senate Intelligence Committee',
            'finance': 'Senate Finance Committee'
        }
        
        text_to_check = f"{title} {uploader} {info.get('description', '')}".lower()
        
        # Check for House committees
        for pattern, committee_name in house_committees.items():
            if pattern in text_to_check:
                return {'committee': committee_name, 'type': 'house'}
        
        # Check for Senate committees
        for pattern, committee_name in senate_committees.items():
            if pattern in text_to_check:
                return {'committee': committee_name, 'type': 'senate'}
        
        # Determine chamber based on keywords
        if 'house' in text_to_check:
            return {'committee': 'Unknown House Committee', 'type': 'house'}
        elif 'senate' in text_to_check:
            return {'committee': 'Unknown Senate Committee', 'type': 'senate'}
        
        return {'committee': None, 'type': None}
    
    def get_priority(self) -> int:
        """Get the priority of this extractor."""
        return 5  # Lower priority than ISVP extractor
    
    def get_available_formats(self, url: str) -> List[Dict[str, Any]]:
        """Get available formats for a YouTube URL."""
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and 'formats' in info:
                    return info['formats']
        except Exception as e:
            print(f"Error getting YouTube formats: {e}")
        
        return []
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def is_live_stream(self, url: str) -> bool:
        """Check if the YouTube URL is a live stream."""
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('is_live', False) if info else False
        except:
            return False