"""
Committee website scraper for real-time hearing discovery and media stream extraction.
Part of Phase 7A: Automated Data Synchronization
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

@dataclass
class ScrapedHearing:
    """Hearing record from committee website scraping"""
    committee_source_id: str
    committee_code: str
    hearing_title: str
    hearing_date: str
    source_url: str
    streams: Dict[str, str]
    documents: List[Dict[str, Any]]
    witnesses: List[Dict[str, Any]]
    status: str
    raw_html: str

class CommitteeWebsiteScraper:
    """Scraper for committee websites to find real-time hearing updates"""
    
    def __init__(self):
        """Initialize committee website scraper"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Senate-Hearing-Research-Tool/1.0 (+https://example.com/contact)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Committee-specific configuration
        self.committee_configs = {
            'SCOM': {
                'base_url': 'https://www.commerce.senate.gov',
                'hearings_path': '/public/index.cfm/hearings',
                'meeting_types': ['hearings', 'markup', 'meetings'],
                'date_format': '%B %d, %Y',
                'selectors': {
                    'hearing_links': 'a[href*="/hearings/"]',
                    'title': 'h1, .hearing-title, .event-title',
                    'date': '.date, .hearing-date, time',
                    'streams': 'iframe[src*="isvp"], iframe[src*="youtube"], video, audio',
                    'documents': 'a[href$=".pdf"], a[href*="document"]',
                    'witnesses': '.witness, .testimony, .participant'
                }
            },
            'SSCI': {
                'base_url': 'https://www.intelligence.senate.gov',
                'hearings_path': '/hearings',
                'meeting_types': ['hearings', 'open-hearings'],
                'date_format': '%m/%d/%Y',
                'selectors': {
                    'hearing_links': 'a[href*="/hearings/"]',
                    'title': 'h1, .page-title',
                    'date': '.date, .event-date',
                    'streams': 'iframe[src*="isvp"], iframe[src*="youtube"]',
                    'documents': 'a[href$=".pdf"]',
                    'witnesses': '.witness-name, .participant'
                }
            },
            'SBAN': {
                'base_url': 'https://www.banking.senate.gov',
                'hearings_path': '/hearings',
                'meeting_types': ['hearings', 'markups'],
                'date_format': '%B %d, %Y',
                'selectors': {
                    'hearing_links': 'a[href*="/hearings/"]',
                    'title': 'h1, .hearing-title',
                    'date': '.date, .hearing-date',
                    'streams': 'iframe[src*="isvp"]',
                    'documents': 'a[href$=".pdf"]',
                    'witnesses': '.witness, .testimony'
                }
            },
            'SSJU': {
                'base_url': 'https://www.judiciary.senate.gov',
                'hearings_path': '/meetings',
                'meeting_types': ['hearings', 'markups', 'meetings'],
                'date_format': '%B %d, %Y at %I:%M %p',
                'selectors': {
                    'hearing_links': 'a[href*="/meetings/"]',
                    'title': 'h1, .meeting-title',
                    'date': '.date, .meeting-date, time',
                    'streams': 'iframe[src*="isvp"], iframe[src*="youtube"]',
                    'documents': 'a[href$=".pdf"], a[href*="testimony"]',
                    'witnesses': '.witness, .participant, .testimony'
                }
            },
            'HJUD': {
                'base_url': 'https://judiciary.house.gov',
                'hearings_path': '/calendar',
                'meeting_types': ['hearings', 'markups'],
                'date_format': '%m/%d/%Y',
                'selectors': {
                    'hearing_links': 'a[href*="/hearing"], a[href*="/markup"]',
                    'title': 'h1, .event-title',
                    'date': '.date, .event-date',
                    'streams': 'iframe[src*="youtube"], iframe[src*="livestream"]',
                    'documents': 'a[href$=".pdf"]',
                    'witnesses': '.witness, .member'
                }
            }
        }
    
    def scrape_committee_hearings(self, committee_code: str, days_back: int = 7) -> List[ScrapedHearing]:
        """Scrape hearings for a specific committee"""
        
        if committee_code not in self.committee_configs:
            logger.warning(f"No scraper configuration for committee {committee_code}")
            return []
        
        config = self.committee_configs[committee_code]
        logger.info(f"Scraping hearings for {committee_code}")
        
        try:
            # Get hearings list page
            hearings_url = urljoin(config['base_url'], config['hearings_path'])
            response = self._make_request(hearings_url)
            
            if not response:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find hearing links
            hearing_links = self._extract_hearing_links(soup, config)
            logger.info(f"Found {len(hearing_links)} potential hearing links for {committee_code}")
            
            # Process each hearing page
            hearings = []
            for link_url in hearing_links[:20]:  # Limit to recent 20 to avoid overload
                try:
                    hearing = self._scrape_hearing_page(link_url, committee_code, config)
                    if hearing and self._is_recent_hearing(hearing.hearing_date, days_back):
                        hearings.append(hearing)
                    
                    # Respectful delay between requests
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error scraping hearing {link_url}: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(hearings)} recent hearings for {committee_code}")
            return hearings
        
        except Exception as e:
            logger.error(f"Error scraping committee {committee_code}: {e}")
            return []
    
    def _make_request(self, url: str, retries: int = 3) -> Optional[requests.Response]:
        """Make HTTP request with retry logic"""
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {url} (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All retries failed for {url}")
                    return None
        
        return None
    
    def _extract_hearing_links(self, soup: BeautifulSoup, config: Dict[str, Any]) -> List[str]:
        """Extract hearing page links from committee hearings list"""
        
        links = []
        selectors = config['selectors']
        base_url = config['base_url']
        
        # Find hearing links using committee-specific selectors
        hearing_elements = soup.select(selectors['hearing_links'])
        
        for element in hearing_elements:
            href = element.get('href', '')
            if href:
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    full_url = urljoin(base_url, href)
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                
                links.append(full_url)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(links))
    
    def _scrape_hearing_page(self, url: str, committee_code: str, config: Dict[str, Any]) -> Optional[ScrapedHearing]:
        """Scrape individual hearing page for detailed information"""
        
        response = self._make_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        selectors = config['selectors']
        
        try:
            # Extract hearing title
            title_element = soup.select_one(selectors['title'])
            title = title_element.get_text(strip=True) if title_element else 'Untitled Hearing'
            
            # Extract hearing date
            date_element = soup.select_one(selectors['date'])
            date_text = date_element.get_text(strip=True) if date_element else ''
            hearing_date = self._parse_hearing_date(date_text, config['date_format'])
            
            # Extract streams (ISVP, YouTube, etc.)
            streams = self._extract_media_streams(soup, selectors['streams'], config['base_url'])
            
            # Extract documents
            documents = self._extract_documents(soup, selectors['documents'], config['base_url'])
            
            # Extract witnesses
            witnesses = self._extract_witnesses(soup, selectors['witnesses'])
            
            # Generate unique identifier
            source_id = self._generate_source_id(url, title, hearing_date)
            
            return ScrapedHearing(
                committee_source_id=source_id,
                committee_code=committee_code,
                hearing_title=title,
                hearing_date=hearing_date,
                source_url=url,
                streams=streams,
                documents=documents,
                witnesses=witnesses,
                status='discovered',
                raw_html=response.text[:10000]  # Store first 10KB for debugging
            )
        
        except Exception as e:
            logger.error(f"Error parsing hearing page {url}: {e}")
            return None
    
    def _parse_hearing_date(self, date_text: str, date_format: str) -> str:
        """Parse hearing date from various text formats"""
        
        if not date_text:
            return datetime.now().strftime('%Y-%m-%d')
        
        # Clean up date text
        date_text = re.sub(r'\s+', ' ', date_text.strip())
        
        # Common date patterns to try
        date_patterns = [
            '%B %d, %Y',  # January 15, 2025
            '%b %d, %Y',   # Jan 15, 2025
            '%m/%d/%Y',    # 01/15/2025
            '%Y-%m-%d',    # 2025-01-15
            '%B %d, %Y at %I:%M %p',  # January 15, 2025 at 2:30 PM
            '%b %d, %Y at %I:%M %p'   # Jan 15, 2025 at 2:30 PM
        ]
        
        # Try specified format first
        if date_format:
            date_patterns.insert(0, date_format)
        
        for pattern in date_patterns:
            try:
                parsed_date = datetime.strptime(date_text, pattern)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Extract date using regex if parsing fails
        date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_text)
        if date_match:
            month, day, year = date_match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Return current date as fallback
        logger.warning(f"Could not parse date: {date_text}")
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_media_streams(self, soup: BeautifulSoup, stream_selector: str, base_url: str) -> Dict[str, str]:
        """Extract media stream URLs (ISVP, YouTube, etc.)"""
        
        streams = {}
        
        # Find all stream elements
        stream_elements = soup.select(stream_selector)
        
        for element in stream_elements:
            src = element.get('src', '')
            if not src:
                continue
            
            # Convert relative URLs to absolute
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(base_url, src)
            
            # Categorize stream type
            if 'isvp' in src.lower():
                streams['isvp_stream'] = src
            elif 'youtube' in src.lower():
                streams['youtube_stream'] = src
            elif element.name == 'video':
                streams['video_stream'] = src
            elif element.name == 'audio':
                streams['audio_stream'] = src
            else:
                streams['unknown_stream'] = src
        
        return streams
    
    def _extract_documents(self, soup: BeautifulSoup, doc_selector: str, base_url: str) -> List[Dict[str, Any]]:
        """Extract document links and information"""
        
        documents = []
        doc_elements = soup.select(doc_selector)
        
        for element in doc_elements:
            href = element.get('href', '')
            if not href:
                continue
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = urljoin(base_url, href)
            
            doc_info = {
                'title': element.get_text(strip=True),
                'url': href,
                'type': 'pdf' if href.endswith('.pdf') else 'document'
            }
            
            documents.append(doc_info)
        
        return documents
    
    def _extract_witnesses(self, soup: BeautifulSoup, witness_selector: str) -> List[Dict[str, Any]]:
        """Extract witness information"""
        
        witnesses = []
        witness_elements = soup.select(witness_selector)
        
        for element in witness_elements:
            witness_text = element.get_text(strip=True)
            if witness_text:
                # Try to parse name and title
                lines = [line.strip() for line in witness_text.split('\n') if line.strip()]
                
                witness_info = {
                    'name': lines[0] if lines else witness_text,
                    'title': lines[1] if len(lines) > 1 else '',
                    'organization': lines[2] if len(lines) > 2 else '',
                    'raw_text': witness_text
                }
                
                witnesses.append(witness_info)
        
        return witnesses
    
    def _generate_source_id(self, url: str, title: str, date: str) -> str:
        """Generate unique source identifier for hearing"""
        
        # Extract path from URL for uniqueness
        parsed = urlparse(url)
        path_hash = hash(parsed.path) % 100000
        
        # Create readable ID
        date_clean = date.replace('-', '')
        title_clean = re.sub(r'[^a-zA-Z0-9]', '', title)[:20]
        
        return f"{date_clean}_{title_clean}_{path_hash}"
    
    def _is_recent_hearing(self, hearing_date: str, days_back: int) -> bool:
        """Check if hearing is within the specified time range"""
        
        try:
            hearing_dt = datetime.strptime(hearing_date, '%Y-%m-%d')
            cutoff_date = datetime.now() - timedelta(days=days_back)
            future_cutoff = datetime.now() + timedelta(days=30)  # Include future hearings
            
            return cutoff_date <= hearing_dt <= future_cutoff
        except ValueError:
            # If date parsing fails, include the hearing
            return True
    
    def scrape_all_committees(self, committee_codes: List[str] = None, days_back: int = 7) -> Dict[str, List[ScrapedHearing]]:
        """Scrape hearings for multiple committees concurrently"""
        
        if committee_codes is None:
            committee_codes = list(self.committee_configs.keys())
        
        results = {}
        
        # Use thread pool for concurrent scraping
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_committee = {
                executor.submit(self.scrape_committee_hearings, code, days_back): code
                for code in committee_codes
            }
            
            for future in as_completed(future_to_committee):
                committee_code = future_to_committee[future]
                try:
                    hearings = future.result()
                    results[committee_code] = hearings
                except Exception as e:
                    logger.error(f"Error scraping {committee_code}: {e}")
                    results[committee_code] = []
        
        return results
    
    def validate_committee_access(self, committee_code: str) -> bool:
        """Validate access to committee website"""
        
        if committee_code not in self.committee_configs:
            return False
        
        config = self.committee_configs[committee_code]
        test_url = urljoin(config['base_url'], config['hearings_path'])
        
        response = self._make_request(test_url)
        return response is not None and response.status_code == 200

if __name__ == "__main__":
    # Test committee scraper
    scraper = CommitteeWebsiteScraper()
    
    # Test single committee
    print("Testing Commerce Committee scraper...")
    commerce_hearings = scraper.scrape_committee_hearings('SCOM', days_back=30)
    print(f"Found {len(commerce_hearings)} Commerce hearings")
    
    if commerce_hearings:
        sample = commerce_hearings[0]
        print(f"Sample: {sample.hearing_title}")
        print(f"Date: {sample.hearing_date}")
        print(f"Streams: {list(sample.streams.keys())}")
        print(f"Documents: {len(sample.documents)}")
    
    # Test committee access validation
    for committee in ['SCOM', 'SSCI', 'SBAN']:
        accessible = scraper.validate_committee_access(committee)
        print(f"{committee} accessible: {accessible}")
    
    print("Committee scraper testing completed")