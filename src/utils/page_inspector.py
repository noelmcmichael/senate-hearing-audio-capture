"""Web page analysis utilities for identifying media players and stream sources."""

from typing import Dict, List, Optional, Tuple
import re
import json
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import requests
from bs4 import BeautifulSoup


class PageInspector:
    """Analyzes web pages to identify embedded media players and extract stream URLs."""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """Initialize the page inspector.
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Page load timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self._playwright = None
        self._browser = None
        self._context = None
    
    def __enter__(self):
        """Context manager entry."""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 SenateHearingBot/1.0 (+mailto:contact@example.com)"
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
    
    def analyze_page(self, url: str) -> Dict:
        """Analyze a web page for embedded media players.
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        if not self._context:
            raise RuntimeError("PageInspector must be used as context manager")
        
        page = self._context.new_page()
        analysis = {
            'url': url,
            'players_found': [],
            'network_requests': [],
            'javascript_variables': {},
            'dom_elements': []
        }
        
        # Track network requests
        def handle_request(request):
            if any(ext in request.url.lower() for ext in ['.m3u8', '.mp4', '.webm', '.ts']):
                analysis['network_requests'].append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'resource_type': request.resource_type
                })
        
        page.on("request", handle_request)
        
        try:
            # Load the page
            page.goto(url, timeout=self.timeout)
            page.wait_for_load_state("networkidle", timeout=10000)
            
            # Look for ISVP player
            isvp_analysis = self._analyze_isvp_player(page)
            if isvp_analysis:
                analysis['players_found'].append(isvp_analysis)
            
            # Look for YouTube embeds
            youtube_analysis = self._analyze_youtube_embeds(page)
            if youtube_analysis:
                analysis['players_found'].extend(youtube_analysis)
            
            # Extract JavaScript variables that might contain stream URLs
            js_vars = self._extract_javascript_variables(page)
            analysis['javascript_variables'] = js_vars
            
            # Look for relevant DOM elements
            dom_elements = self._extract_media_elements(page)
            analysis['dom_elements'] = dom_elements
            
        except Exception as e:
            analysis['error'] = str(e)
        finally:
            page.close()
        
        return analysis
    
    def _analyze_isvp_player(self, page: Page) -> Optional[Dict]:
        """Analyze ISVP player implementation on the page."""
        try:
            # Look for ISVP-specific elements
            isvp_elements = page.query_selector_all('[class*="isvp"], [id*="isvp"], [data-*="isvp"]')
            
            if not isvp_elements:
                # Check for generic video containers that might be ISVP
                video_containers = page.query_selector_all('div[class*="video"], div[id*="video"], div[class*="player"]')
                if not video_containers:
                    return None
                isvp_elements = video_containers
            
            player_info = {
                'type': 'isvp',
                'elements': [],
                'potential_streams': []
            }
            
            for element in isvp_elements[:5]:  # Limit to first 5 elements
                try:
                    element_info = {
                        'tag': element.evaluate('el => el.tagName.toLowerCase()'),
                        'id': element.get_attribute('id'),
                        'class': element.get_attribute('class'),
                        'data_attributes': {}
                    }
                    
                    # Extract data attributes
                    attributes = element.evaluate('el => Array.from(el.attributes).map(attr => [attr.name, attr.value])')
                    for name, value in attributes:
                        if name.startswith('data-'):
                            element_info['data_attributes'][name] = value
                    
                    player_info['elements'].append(element_info)
                except Exception as e:
                    player_info['elements'].append({'error': str(e)})
            
            # Look for stream URLs in page source
            page_content = page.content()
            stream_urls = self._extract_stream_urls_from_content(page_content)
            player_info['potential_streams'] = stream_urls
            
            return player_info
            
        except Exception as e:
            return {'type': 'isvp', 'error': str(e)}
    
    def _analyze_youtube_embeds(self, page: Page) -> List[Dict]:
        """Analyze YouTube embeds on the page."""
        try:
            youtube_iframes = page.query_selector_all('iframe[src*="youtube"]')
            embeds = []
            
            for iframe in youtube_iframes:
                src = iframe.get_attribute('src')
                video_id = self._extract_youtube_video_id(src)
                
                embed_info = {
                    'type': 'youtube',
                    'src': src,
                    'video_id': video_id,
                    'width': iframe.get_attribute('width'),
                    'height': iframe.get_attribute('height')
                }
                embeds.append(embed_info)
            
            return embeds
            
        except Exception as e:
            return [{'type': 'youtube', 'error': str(e)}]
    
    def _extract_javascript_variables(self, page: Page) -> Dict:
        """Extract JavaScript variables that might contain stream information."""
        try:
            # Common variable names that might contain streaming info
            var_names = [
                'videoUrl', 'streamUrl', 'manifestUrl', 'playlistUrl',
                'isvpConfig', 'playerConfig', 'videoConfig', 'streamConfig'
            ]
            
            js_vars = {}
            for var_name in var_names:
                try:
                    value = page.evaluate(f'window.{var_name}')
                    if value:
                        js_vars[var_name] = value
                except:
                    continue
            
            return js_vars
            
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_media_elements(self, page: Page) -> List[Dict]:
        """Extract relevant media elements from the DOM."""
        try:
            elements = []
            
            # Video elements
            video_elements = page.query_selector_all('video')
            for video in video_elements:
                element_info = {
                    'type': 'video',
                    'src': video.get_attribute('src'),
                    'poster': video.get_attribute('poster'),
                    'controls': video.get_attribute('controls') is not None,
                    'autoplay': video.get_attribute('autoplay') is not None
                }
                elements.append(element_info)
            
            # Source elements within video tags
            source_elements = page.query_selector_all('video source')
            for source in source_elements:
                element_info = {
                    'type': 'source',
                    'src': source.get_attribute('src'),
                    'type': source.get_attribute('type')
                }
                elements.append(element_info)
            
            return elements
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def _extract_stream_urls_from_content(self, content: str) -> List[str]:
        """Extract potential stream URLs from page content."""
        urls = []
        
        # Common streaming URL patterns
        patterns = [
            r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*',
            r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*',
            r'https?://[^\s"\'<>]+/playlist\.m3u8[^\s"\'<>]*',
            r'https?://[^\s"\'<>]+/manifest[^\s"\'<>]*',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            urls.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
    
    def _extract_youtube_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None