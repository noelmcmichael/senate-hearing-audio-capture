#!/usr/bin/env python3
"""
Comprehensive Hearing Discovery Engine
Discovers hearings across all Senate committees with ISVP detection
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import time
from datetime import datetime, date
import logging
from dataclasses import dataclass, asdict
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Hearing:
    """Hearing data structure"""
    hearing_id: str
    title: str
    committee_code: str
    committee_name: str
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    hearing_type: Optional[str] = None  # "hearing", "markup", "executive_session"
    url: Optional[str] = None
    isvp_url: Optional[str] = None
    youtube_url: Optional[str] = None
    transcript_url: Optional[str] = None
    audio_available: Optional[bool] = None
    video_available: Optional[bool] = None
    isvp_compatible: Optional[bool] = None
    duration_estimate: Optional[int] = None  # minutes
    witness_count: Optional[int] = None
    witnesses: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    status: Optional[str] = None  # "scheduled", "in_progress", "completed", "cancelled"
    discovery_source: Optional[str] = None
    discovery_date: Optional[str] = None
    processing_priority: Optional[int] = None  # 1-10, 10 being highest
    quality_score: Optional[float] = None  # 0-1, readiness assessment

class HearingDiscoveryEngine:
    """Comprehensive hearing discovery system"""
    
    def __init__(self, committee_file: str = "data/committees/committee_structure_refined.json",
                 output_dir: str = "data/hearings"):
        self.committee_file = Path(committee_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load committee structure
        self.committees = self._load_committees()
        
        # Date range for discovery
        self.date_range = {
            "start": "2025-01-01",
            "end": "2025-12-31"
        }
        
        # Hearing sources
        self.hearing_sources = {
            "committee_websites": True,
            "congress_api": True,
            "senate_calendar": True
        }
        
        # ISVP detection patterns
        self.isvp_patterns = [
            r'isvp',
            r'in-house streaming',
            r'live\.senate\.gov',
            r'senate\.gov/isvp',
            r'streaming video player',
            r'watch live'
        ]
        
        # Quality assessment criteria
        self.quality_criteria = {
            "has_date": 2,
            "has_time": 1,
            "has_title": 2,
            "has_witnesses": 2,
            "has_isvp": 5,
            "has_youtube": 3,
            "recent_date": 2,
            "duration_reasonable": 2
        }
        
        self.discovered_hearings: Dict[str, Hearing] = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Senate Hearing Discovery System (Research/Academic)'
        })
    
    def _load_committees(self) -> Dict:
        """Load committee structure"""
        if not self.committee_file.exists():
            logger.error(f"Committee file not found: {self.committee_file}")
            return {}
        
        try:
            with open(self.committee_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load committees: {e}")
            return {}
    
    def discover_hearings_from_committee(self, committee_code: str, committee_data: Dict) -> List[Hearing]:
        """Discover hearings from a specific committee website"""
        logger.info(f"Discovering hearings from {committee_data.get('name', committee_code)}")
        
        hearings = []
        
        website_url = committee_data.get("website_url")
        if not website_url:
            logger.debug(f"No website URL for {committee_code}")
            return hearings
        
        try:
            # Get committee main page
            response = self.session.get(website_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for hearing-related links
            hearing_links = self._find_hearing_links(soup, website_url)
            
            # Extract hearing information
            for link_info in hearing_links:
                try:
                    hearing = self._extract_hearing_info(link_info, committee_code, committee_data)
                    if hearing:
                        hearings.append(hearing)
                except Exception as e:
                    logger.debug(f"Failed to extract hearing info from {link_info.get('url', '')}: {e}")
            
            logger.info(f"Found {len(hearings)} hearings from {committee_data.get('name', committee_code)}")
            
        except Exception as e:
            logger.warning(f"Failed to discover hearings from {committee_code}: {e}")
        
        return hearings
    
    def _find_hearing_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Find hearing-related links on committee website"""
        hearing_links = []
        
        # Common hearing link patterns
        hearing_patterns = [
            r'hearing',
            r'markup',
            r'executive session',
            r'committee meeting',
            r'oversight',
            r'field hearing'
        ]
        
        # Look for links with hearing-related text
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            # Check if link text contains hearing patterns
            if any(pattern in text.lower() for pattern in hearing_patterns):
                full_url = urljoin(base_url, href)
                
                # Extract date from link text if possible
                date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
                extracted_date = date_match.group(1) if date_match else None
                
                # Check for recent dates (2025)
                if extracted_date and '2025' in extracted_date:
                    hearing_links.append({
                        'url': full_url,
                        'text': text,
                        'date': extracted_date
                    })
                elif not extracted_date and len(text) > 10:
                    # Include links without dates if they have substantial text
                    hearing_links.append({
                        'url': full_url,
                        'text': text,
                        'date': None
                    })
        
        # Look for dedicated hearing sections
        hearing_sections = soup.find_all(['div', 'section'], class_=re.compile(r'hearing|event|meeting', re.I))
        
        for section in hearing_sections:
            section_links = section.find_all('a', href=True)
            for link in section_links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                if len(text) > 10:
                    full_url = urljoin(base_url, href)
                    
                    # Extract date from link text
                    date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
                    extracted_date = date_match.group(1) if date_match else None
                    
                    hearing_links.append({
                        'url': full_url,
                        'text': text,
                        'date': extracted_date
                    })
        
        # Remove duplicates
        unique_links = []
        seen_urls = set()
        for link in hearing_links:
            if link['url'] not in seen_urls:
                unique_links.append(link)
                seen_urls.add(link['url'])
        
        return unique_links
    
    def _extract_hearing_info(self, link_info: Dict, committee_code: str, committee_data: Dict) -> Optional[Hearing]:
        """Extract detailed hearing information from link"""
        hearing_url = link_info['url']
        
        try:
            response = self.session.get(hearing_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Generate hearing ID
            hearing_id = self._generate_hearing_id(committee_code, link_info['text'], link_info.get('date'))
            
            # Extract title
            title = self._extract_title(soup, link_info['text'])
            
            # Extract date and time
            date_str, time_str = self._extract_date_time(soup, link_info.get('date'))
            
            # Extract location
            location = self._extract_location(soup)
            
            # Extract hearing type
            hearing_type = self._extract_hearing_type(soup, link_info['text'])
            
            # Detect ISVP compatibility
            isvp_url, isvp_compatible = self._detect_isvp(soup, hearing_url)
            
            # Detect YouTube availability
            youtube_url = self._detect_youtube(soup)
            
            # Extract witnesses
            witnesses = self._extract_witnesses(soup)
            
            # Extract topics
            topics = self._extract_topics(soup, title)
            
            # Determine status
            status = self._determine_status(date_str, soup)
            
            # Create hearing object
            hearing = Hearing(
                hearing_id=hearing_id,
                title=title,
                committee_code=committee_code,
                committee_name=committee_data.get('name', ''),
                date=date_str,
                time=time_str,
                location=location,
                hearing_type=hearing_type,
                url=hearing_url,
                isvp_url=isvp_url,
                youtube_url=youtube_url,
                audio_available=bool(isvp_url or youtube_url),
                video_available=bool(isvp_url or youtube_url),
                isvp_compatible=isvp_compatible,
                witness_count=len(witnesses) if witnesses else None,
                witnesses=witnesses,
                topics=topics,
                status=status,
                discovery_source=f"{committee_code} website",
                discovery_date=datetime.now().isoformat()
            )
            
            # Calculate quality score
            hearing.quality_score = self._calculate_quality_score(hearing)
            
            # Calculate processing priority
            hearing.processing_priority = self._calculate_processing_priority(hearing)
            
            return hearing
            
        except Exception as e:
            logger.debug(f"Failed to extract hearing info from {hearing_url}: {e}")
            return None
    
    def _generate_hearing_id(self, committee_code: str, title: str, date: Optional[str]) -> str:
        """Generate unique hearing ID"""
        # Create hash from committee, title, and date
        content = f"{committee_code}_{title}_{date or 'unknown'}"
        hash_obj = hashlib.md5(content.encode())
        hash_hex = hash_obj.hexdigest()[:8]
        
        return f"{committee_code}_{hash_hex}"
    
    def _extract_title(self, soup: BeautifulSoup, fallback_text: str) -> str:
        """Extract hearing title"""
        # Look for title patterns
        title_selectors = [
            'h1',
            'h2',
            '.hearing-title',
            '.event-title',
            '.page-title',
            'title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if len(title) > 10 and len(title) < 200:
                    return title
        
        # Clean up fallback text
        cleaned = re.sub(r'[^\w\s,.-]', '', fallback_text)
        return cleaned[:150] if len(cleaned) > 150 else cleaned
    
    def _extract_date_time(self, soup: BeautifulSoup, fallback_date: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Extract hearing date and time"""
        # Look for date patterns in text
        page_text = soup.get_text()
        
        # Date patterns
        date_patterns = [
            r'(\w+\s+\d{1,2},\s+\d{4})',  # "January 15, 2025"
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # "1/15/2025"
            r'(\d{4}-\d{2}-\d{2})',  # "2025-01-15"
        ]
        
        # Time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*[AP]M)',  # "10:00 AM"
            r'(\d{1,2}:\d{2})'  # "10:00"
        ]
        
        extracted_date = None
        extracted_time = None
        
        # Extract date
        for pattern in date_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                extracted_date = match.group(1)
                break
        
        # Extract time
        for pattern in time_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                extracted_time = match.group(1)
                break
        
        # Use fallback date if no date found
        if not extracted_date and fallback_date:
            extracted_date = fallback_date
        
        return extracted_date, extracted_time
    
    def _extract_location(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract hearing location"""
        page_text = soup.get_text()
        
        # Location patterns
        location_patterns = [
            r'Room\s+(\w+\s*\d+)',
            r'(\w+\s+Room\s+\d+)',
            r'Location:\s*([^\n]+)',
            r'Committee Room\s+(\w+)',
            r'Hart\s+(\d+)',
            r'Dirksen\s+(\d+)',
            r'Russell\s+(\d+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_hearing_type(self, soup: BeautifulSoup, title: str) -> str:
        """Extract hearing type"""
        content = f"{soup.get_text()} {title}".lower()
        
        if 'markup' in content:
            return 'markup'
        elif 'executive session' in content:
            return 'executive_session'
        elif 'oversight' in content:
            return 'oversight'
        elif 'field hearing' in content:
            return 'field_hearing'
        else:
            return 'hearing'
    
    def _detect_isvp(self, soup: BeautifulSoup, url: str) -> Tuple[Optional[str], bool]:
        """Detect ISVP streaming availability"""
        page_content = soup.get_text().lower()
        page_html = str(soup).lower()
        
        # Check for ISVP patterns
        isvp_found = any(re.search(pattern, page_content + page_html, re.IGNORECASE) 
                        for pattern in self.isvp_patterns)
        
        isvp_url = None
        
        if isvp_found:
            # Look for ISVP URL
            isvp_links = soup.find_all('a', href=re.compile(r'isvp|live\.senate\.gov', re.IGNORECASE))
            if isvp_links:
                isvp_url = isvp_links[0].get('href')
        
        return isvp_url, isvp_found
    
    def _detect_youtube(self, soup: BeautifulSoup) -> Optional[str]:
        """Detect YouTube availability"""
        # Look for YouTube links
        youtube_links = soup.find_all('a', href=re.compile(r'youtube\.com|youtu\.be', re.IGNORECASE))
        
        if youtube_links:
            return youtube_links[0].get('href')
        
        # Look for embedded YouTube videos
        youtube_embeds = soup.find_all('iframe', src=re.compile(r'youtube\.com', re.IGNORECASE))
        
        if youtube_embeds:
            return youtube_embeds[0].get('src')
        
        return None
    
    def _extract_witnesses(self, soup: BeautifulSoup) -> List[str]:
        """Extract witness list"""
        witnesses = []
        
        # Look for witness sections
        witness_sections = soup.find_all(['div', 'section'], 
                                       class_=re.compile(r'witness|panel|speaker', re.I))
        
        for section in witness_sections:
            # Extract names from section
            names = re.findall(r'([A-Z][a-z]+\s+[A-Z][a-z]+)', section.get_text())
            witnesses.extend(names)
        
        # Look for witness patterns in text
        page_text = soup.get_text()
        witness_patterns = [
            r'Witness:\s*([^\n]+)',
            r'Witnesses:\s*([^\n]+)',
            r'Panel:\s*([^\n]+)'
        ]
        
        for pattern in witness_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                # Split by commas and clean
                names = [name.strip() for name in match.split(',')]
                witnesses.extend(names)
        
        # Remove duplicates and clean
        unique_witnesses = []
        seen = set()
        for witness in witnesses:
            clean_witness = re.sub(r'[^\w\s,.-]', '', witness).strip()
            if clean_witness and len(clean_witness) > 5 and clean_witness not in seen:
                unique_witnesses.append(clean_witness)
                seen.add(clean_witness)
        
        return unique_witnesses[:10]  # Limit to 10 witnesses
    
    def _extract_topics(self, soup: BeautifulSoup, title: str) -> List[str]:
        """Extract hearing topics"""
        # Extract keywords from title
        title_words = re.findall(r'\b[A-Z][a-z]+\b', title)
        
        # Common policy topics
        policy_topics = [
            'healthcare', 'education', 'defense', 'finance', 'banking',
            'environment', 'energy', 'transportation', 'agriculture',
            'technology', 'cybersecurity', 'immigration', 'trade',
            'judiciary', 'oversight', 'appropriations', 'budget'
        ]
        
        page_text = soup.get_text().lower()
        found_topics = []
        
        for topic in policy_topics:
            if topic in page_text:
                found_topics.append(topic.title())
        
        # Combine title words and policy topics
        all_topics = title_words + found_topics
        
        # Remove duplicates
        unique_topics = []
        seen = set()
        for topic in all_topics:
            if topic.lower() not in seen and len(topic) > 3:
                unique_topics.append(topic)
                seen.add(topic.lower())
        
        return unique_topics[:5]  # Limit to 5 topics
    
    def _determine_status(self, date_str: Optional[str], soup: BeautifulSoup) -> str:
        """Determine hearing status"""
        if not date_str:
            return "unknown"
        
        # Parse date
        try:
            # Simple date parsing
            if '2025' in date_str:
                current_date = datetime.now().date()
                # For simplicity, assume all 2025 dates are future
                return "scheduled"
            else:
                return "completed"
        except:
            return "unknown"
    
    def _calculate_quality_score(self, hearing: Hearing) -> float:
        """Calculate hearing quality score for processing readiness"""
        score = 0
        max_score = sum(self.quality_criteria.values())
        
        # Check criteria
        if hearing.date:
            score += self.quality_criteria["has_date"]
        if hearing.time:
            score += self.quality_criteria["has_time"]
        if hearing.title and len(hearing.title) > 10:
            score += self.quality_criteria["has_title"]
        if hearing.witnesses:
            score += self.quality_criteria["has_witnesses"]
        if hearing.isvp_compatible:
            score += self.quality_criteria["has_isvp"]
        if hearing.youtube_url:
            score += self.quality_criteria["has_youtube"]
        if hearing.date and '2025' in hearing.date:
            score += self.quality_criteria["recent_date"]
        
        return min(1.0, score / max_score)
    
    def _calculate_processing_priority(self, hearing: Hearing) -> int:
        """Calculate processing priority (1-10)"""
        priority = 1
        
        # ISVP compatibility is high priority
        if hearing.isvp_compatible:
            priority += 5
        
        # Recent dates are higher priority
        if hearing.date and '2025' in hearing.date:
            priority += 2
        
        # Hearings with witnesses are higher priority
        if hearing.witnesses:
            priority += 1
        
        # Quality score boost
        if hearing.quality_score and hearing.quality_score > 0.7:
            priority += 1
        
        return min(10, priority)
    
    def discover_all_hearings(self, committee_filter: List[str] = None) -> Dict[str, Hearing]:
        """Discover hearings from all committees"""
        logger.info("Starting comprehensive hearing discovery...")
        
        all_hearings = {}
        committees = self.committees.get("committees", {})
        
        # Filter committees if specified
        if committee_filter:
            committees = {k: v for k, v in committees.items() if k in committee_filter}
        
        # Discover hearings from each committee
        for committee_code, committee_data in committees.items():
            if committee_data.get("type") == "committee":  # Skip subcommittees
                try:
                    hearings = self.discover_hearings_from_committee(committee_code, committee_data)
                    
                    for hearing in hearings:
                        all_hearings[hearing.hearing_id] = hearing
                    
                    # Rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Failed to discover hearings from {committee_code}: {e}")
        
        self.discovered_hearings = all_hearings
        logger.info(f"Total hearings discovered: {len(all_hearings)}")
        
        return all_hearings
    
    def save_hearing_catalog(self, output_file: str = "hearing_catalog.json"):
        """Save discovered hearing catalog"""
        output_path = self.output_dir / output_file
        
        # Convert to serializable format
        catalog_data = {
            "discovery_info": {
                "discovery_date": datetime.now().isoformat(),
                "total_hearings": len(self.discovered_hearings),
                "date_range": self.date_range,
                "committees_scanned": len(self.committees.get("committees", {})),
                "isvp_compatible_hearings": len([h for h in self.discovered_hearings.values() 
                                               if h.isvp_compatible]),
                "high_priority_hearings": len([h for h in self.discovered_hearings.values() 
                                             if h.processing_priority and h.processing_priority >= 7])
            },
            "hearings": {hearing_id: asdict(hearing) for hearing_id, hearing in self.discovered_hearings.items()}
        }
        
        with open(output_path, 'w') as f:
            json.dump(catalog_data, f, indent=2)
        
        logger.info(f"Hearing catalog saved to {output_path}")
        return output_path
    
    def generate_discovery_summary(self):
        """Generate summary of discovered hearings"""
        hearings = self.discovered_hearings
        
        summary = {
            "total_hearings": len(hearings),
            "by_committee": {},
            "by_status": {},
            "by_type": {},
            "isvp_compatible": 0,
            "high_priority": 0,
            "avg_quality_score": 0
        }
        
        total_quality = 0
        
        for hearing in hearings.values():
            # Count by committee
            committee = hearing.committee_code
            summary["by_committee"][committee] = summary["by_committee"].get(committee, 0) + 1
            
            # Count by status
            status = hearing.status or "unknown"
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # Count by type
            h_type = hearing.hearing_type or "unknown"
            summary["by_type"][h_type] = summary["by_type"].get(h_type, 0) + 1
            
            # Count ISVP compatible
            if hearing.isvp_compatible:
                summary["isvp_compatible"] += 1
            
            # Count high priority
            if hearing.processing_priority and hearing.processing_priority >= 7:
                summary["high_priority"] += 1
            
            # Sum quality scores
            if hearing.quality_score:
                total_quality += hearing.quality_score
        
        # Calculate average quality score
        if hearings:
            summary["avg_quality_score"] = total_quality / len(hearings)
        
        return summary

def main():
    """Main hearing discovery function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Discover Senate Committee Hearings")
    parser.add_argument("--committees", nargs="+", help="Specific committees to scan")
    parser.add_argument("--output", default="data/hearings", help="Output directory")
    parser.add_argument("--date-range", default="2025-01-01:2025-12-31", help="Date range (start:end)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize discovery engine
    discovery = HearingDiscoveryEngine(output_dir=args.output)
    
    # Set date range
    start_date, end_date = args.date_range.split(':')
    discovery.date_range = {"start": start_date, "end": end_date}
    
    # Discover hearings
    hearings = discovery.discover_all_hearings(args.committees)
    
    # Save catalog
    output_file = discovery.save_hearing_catalog()
    
    # Generate summary
    summary = discovery.generate_discovery_summary()
    
    print("\n" + "="*60)
    print("HEARING DISCOVERY COMPLETE")
    print("="*60)
    print(f"Total Hearings: {summary['total_hearings']}")
    print(f"ISVP Compatible: {summary['isvp_compatible']}")
    print(f"High Priority: {summary['high_priority']}")
    print(f"Average Quality Score: {summary['avg_quality_score']:.2f}")
    print("\nBy Committee:")
    for committee, count in list(summary['by_committee'].items())[:5]:
        print(f"  {committee}: {count}")
    print("\nBy Status:")
    for status, count in summary['by_status'].items():
        print(f"  {status}: {count}")
    print(f"\nCatalog saved to: {output_file}")
    print("="*60)

if __name__ == "__main__":
    main()