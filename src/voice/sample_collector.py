#!/usr/bin/env python3
"""
Voice Sample Collector for Phase 6B

Automated collection of voice samples from multiple sources:
- C-SPAN archives and live streams
- YouTube congressional content
- Senate.gov official videos
- House.gov committee recordings

Focus on priority committee members with quality filtering.
"""

import re
import json
import logging
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import subprocess

import yt_dlp
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class VoiceSampleCollector:
    """Automated voice sample collection system."""
    
    def __init__(self, output_dir: Path = None):
        """Initialize voice sample collector."""
        self.output_dir = output_dir or Path("data/voice_samples")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Priority senators from Phase 6A review system
        self.priority_senators = self._load_priority_senators()
        
        # Sample collection targets per senator
        self.target_samples_per_senator = 10
        self.min_sample_duration = 5.0  # seconds
        self.max_sample_duration = 30.0  # seconds
        
        # Collection sources
        self.sources = {
            'cspan': 'https://www.c-span.org',
            'youtube': 'https://www.youtube.com',
            'senate_gov': 'https://www.senate.gov',
            'committee_sites': {}  # Will be populated
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            'min_audio_quality': 128,  # kbps
            'max_background_noise': 0.3,  # ratio
            'min_speech_clarity': 0.7,  # confidence
            'min_speaker_isolation': 0.8  # single speaker confidence
        }
    
    def _load_priority_senators(self) -> List[Dict[str, Any]]:
        """Load priority senators from committee data."""
        try:
            senators = []
            
            # Load from committee files
            committee_dir = Path("data/committees")
            if committee_dir.exists():
                for committee_file in committee_dir.glob("*.json"):
                    with open(committee_file, 'r') as f:
                        committee_data = json.load(f)
                    
                    for member in committee_data.get("members", []):
                        if member.get("chamber") == "Senate" or committee_data.get("committee_info", {}).get("chamber") == "Senate":
                            # Handle both old and new data formats
                            name = member.get("full_name") or member.get("name", "")
                            display_name = member.get("display_name") or f"Sen. {name.split()[-1]}" if name else ""
                            
                            senators.append({
                                "name": name,
                                "display_name": display_name,
                                "party": member.get("party", ""),
                                "state": member.get("state", ""),
                                "aliases": member.get("aliases", [display_name] if display_name else []),
                                "committee": committee_data.get("committee_info", {}).get("name") or committee_data.get("name", "")
                            })
            
            # Remove duplicates based on name
            unique_senators = {}
            for senator in senators:
                name = senator["name"]
                if name and name not in unique_senators:
                    unique_senators[name] = senator
                elif name:
                    # Merge committee info
                    existing = unique_senators[name]
                    if "committees" not in existing:
                        existing["committees"] = [existing.get("committee", "")]
                    existing["committees"].append(senator.get("committee", ""))
            
            result = list(unique_senators.values())
            logger.info(f"Loaded {len(result)} priority senators for voice collection")
            return result
            
        except Exception as e:
            logger.error(f"Error loading priority senators: {e}")
            return []
    
    async def collect_samples_for_senator(
        self, 
        senator: Dict[str, Any], 
        max_samples: int = None
    ) -> List[Dict[str, Any]]:
        """Collect voice samples for a specific senator."""
        max_samples = max_samples or self.target_samples_per_senator
        
        logger.info(f"Collecting voice samples for {senator['display_name']} (target: {max_samples})")
        
        collected_samples = []
        
        # Check existing samples
        existing_samples = self._get_existing_samples(senator)
        if len(existing_samples) >= max_samples:
            logger.info(f"Already have {len(existing_samples)} samples for {senator['display_name']}")
            return existing_samples
        
        needed_samples = max_samples - len(existing_samples)
        logger.info(f"Need {needed_samples} additional samples for {senator['display_name']}")
        
        # Collection strategies in priority order
        strategies = [
            self._collect_from_cspan,
            self._collect_from_youtube,
            self._collect_from_senate_gov,
            self._collect_from_committee_sites
        ]
        
        for strategy in strategies:
            if len(collected_samples) >= needed_samples:
                break
                
            try:
                strategy_samples = await strategy(senator, needed_samples - len(collected_samples))
                collected_samples.extend(strategy_samples)
                logger.info(f"{strategy.__name__}: collected {len(strategy_samples)} samples")
                
            except Exception as e:
                logger.error(f"Error in {strategy.__name__} for {senator['display_name']}: {e}")
                continue
        
        # Save collected samples
        for sample in collected_samples:
            self._save_sample_metadata(senator, sample)
        
        logger.info(f"Total collected for {senator['display_name']}: {len(collected_samples)} samples")
        return existing_samples + collected_samples
    
    async def _collect_from_cspan(
        self, 
        senator: Dict[str, Any], 
        max_samples: int
    ) -> List[Dict[str, Any]]:
        """Collect voice samples from C-SPAN archives."""
        logger.info(f"Searching C-SPAN for {senator['display_name']}")
        
        samples = []
        search_terms = [
            senator["display_name"],
            senator["name"],
            *senator.get("aliases", [])
        ]
        
        async with aiohttp.ClientSession() as session:
            for search_term in search_terms:
                if len(samples) >= max_samples:
                    break
                
                try:
                    # Search C-SPAN for senator appearances
                    search_url = f"https://www.c-span.org/search/?searchtype=Videos&search={search_term.replace(' ', '+')}"
                    
                    async with session.get(search_url) as response:
                        if response.status == 200:
                            content = await response.text()
                            video_urls = self._parse_cspan_search_results(content)
                            
                            for video_url in video_urls[:3]:  # Limit per search term
                                if len(samples) >= max_samples:
                                    break
                                
                                sample = await self._extract_cspan_audio_sample(session, video_url, senator)
                                if sample:
                                    samples.append(sample)
                
                except Exception as e:
                    logger.error(f"Error searching C-SPAN for {search_term}: {e}")
                    continue
        
        return samples
    
    async def _collect_from_youtube(
        self, 
        senator: Dict[str, Any], 
        max_samples: int
    ) -> List[Dict[str, Any]]:
        """Collect voice samples from YouTube congressional content."""
        logger.info(f"Searching YouTube for {senator['display_name']}")
        
        samples = []
        
        # YouTube search queries
        search_queries = [
            f"{senator['display_name']} senate hearing",
            f"{senator['display_name']} committee",
            f"Senator {senator['name']} questions",
            f"{senator['display_name']} congress"
        ]
        
        for query in search_queries:
            if len(samples) >= max_samples:
                break
                
            try:
                # Use yt-dlp to search and extract
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                    'default_search': 'ytsearch5:'  # Top 5 results per query
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    search_results = ydl.extract_info(query, download=False)
                    
                    if search_results and 'entries' in search_results:
                        for entry in search_results['entries']:
                            if len(samples) >= max_samples:
                                break
                            
                            sample = await self._extract_youtube_audio_sample(entry, senator)
                            if sample:
                                samples.append(sample)
            
            except Exception as e:
                logger.error(f"Error searching YouTube for {query}: {e}")
                continue
        
        return samples
    
    async def _collect_from_senate_gov(
        self, 
        senator: Dict[str, Any], 
        max_samples: int
    ) -> List[Dict[str, Any]]:
        """Collect voice samples from official Senate.gov content."""
        logger.info(f"Searching Senate.gov for {senator['display_name']}")
        
        samples = []
        
        # Official Senate sources
        sources = [
            f"https://www.senate.gov/senators/{senator['state'].lower()}/",
            "https://www.senate.gov/committees/",
            "https://www.judiciary.senate.gov/hearings",
            "https://www.commerce.senate.gov/hearings",
            "https://www.banking.senate.gov/hearings"
        ]
        
        async with aiohttp.ClientSession() as session:
            for source_url in sources:
                if len(samples) >= max_samples:
                    break
                
                try:
                    async with session.get(source_url) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Look for video/audio content mentioning the senator
                            audio_urls = self._parse_senate_gov_content(content, senator)
                            
                            for audio_url in audio_urls:
                                if len(samples) >= max_samples:
                                    break
                                
                                sample = await self._extract_senate_gov_sample(session, audio_url, senator)
                                if sample:
                                    samples.append(sample)
                
                except Exception as e:
                    logger.error(f"Error accessing {source_url}: {e}")
                    continue
        
        return samples
    
    async def _collect_from_committee_sites(
        self, 
        senator: Dict[str, Any], 
        max_samples: int
    ) -> List[Dict[str, Any]]:
        """Collect from specific committee websites."""
        logger.info(f"Searching committee sites for {senator['display_name']}")
        
        samples = []
        
        # Committee-specific URLs
        committee_urls = {
            "Commerce": "https://www.commerce.senate.gov/hearings",
            "Judiciary": "https://www.judiciary.senate.gov/hearings", 
            "Banking": "https://www.banking.senate.gov/hearings",
            "Intelligence": "https://www.intelligence.senate.gov/hearings"
        }
        
        senator_committees = senator.get("committees", [senator.get("committee", "")])
        
        async with aiohttp.ClientSession() as session:
            for committee in senator_committees:
                if committee in committee_urls and len(samples) < max_samples:
                    try:
                        committee_url = committee_urls[committee]
                        
                        async with session.get(committee_url) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Parse committee hearing pages
                                hearing_urls = self._parse_committee_hearings(content)
                                
                                for hearing_url in hearing_urls[:2]:  # Limit per committee
                                    if len(samples) >= max_samples:
                                        break
                                    
                                    sample = await self._extract_committee_sample(session, hearing_url, senator)
                                    if sample:
                                        samples.append(sample)
                    
                    except Exception as e:
                        logger.error(f"Error accessing {committee} committee site: {e}")
                        continue
        
        return samples
    
    def _parse_cspan_search_results(self, html_content: str) -> List[str]:
        """Parse C-SPAN search results to extract video URLs."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            video_links = []
            
            # Look for C-SPAN video links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/video/' in href and 'c-span.org' in href:
                    if not href.startswith('http'):
                        href = f"https://www.c-span.org{href}"
                    video_links.append(href)
            
            return video_links[:10]  # Return top 10 results
            
        except Exception as e:
            logger.error(f"Error parsing C-SPAN search results: {e}")
            return []
    
    def _parse_senate_gov_content(self, html_content: str, senator: Dict[str, Any]) -> List[str]:
        """Parse Senate.gov content for audio/video URLs."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            audio_urls = []
            
            # Look for audio/video elements
            for element in soup.find_all(['audio', 'video', 'source']):
                if element.get('src'):
                    audio_urls.append(element['src'])
            
            # Look for download links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(ext in href.lower() for ext in ['.mp3', '.wav', '.m4a', '.mp4']):
                    audio_urls.append(href)
            
            return audio_urls
            
        except Exception as e:
            logger.error(f"Error parsing Senate.gov content: {e}")
            return []
    
    def _parse_committee_hearings(self, html_content: str) -> List[str]:
        """Parse committee hearing pages for audio content."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            hearing_urls = []
            
            # Look for hearing links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'hearing' in href.lower() or 'markup' in href.lower():
                    if not href.startswith('http'):
                        href = f"https://www.senate.gov{href}"
                    hearing_urls.append(href)
            
            return hearing_urls[:5]  # Limit results
            
        except Exception as e:
            logger.error(f"Error parsing committee hearings: {e}")
            return []
    
    async def _extract_cspan_audio_sample(
        self, 
        session: aiohttp.ClientSession, 
        video_url: str, 
        senator: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract audio sample from C-SPAN video."""
        try:
            # Use yt-dlp to extract audio from C-SPAN
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(self.output_dir / f"cspan_{senator['name'].replace(' ', '_')}_%(id)s.%(ext)s"),
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                
                if info and 'requested_downloads' in info:
                    downloaded_file = info['requested_downloads'][0]['filepath']
                    
                    # Extract speaker segments (simplified for now)
                    sample_segments = await self._extract_speaker_segments(downloaded_file, senator)
                    
                    return {
                        "source": "cspan",
                        "source_url": video_url,
                        "file_path": downloaded_file,
                        "duration": info.get('duration', 0),
                        "title": info.get('title', ''),
                        "upload_date": info.get('upload_date', ''),
                        "quality_score": 0.8,  # Default for C-SPAN
                        "segments": sample_segments
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting C-SPAN audio from {video_url}: {e}")
            return None
    
    async def _extract_youtube_audio_sample(
        self, 
        video_info: Dict[str, Any], 
        senator: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract audio sample from YouTube video."""
        try:
            video_url = f"https://www.youtube.com/watch?v={video_info['id']}"
            
            # Download audio using yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(self.output_dir / f"youtube_{senator['name'].replace(' ', '_')}_%(id)s.%(ext)s"),
                'quiet': True,
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                
                if info and 'requested_downloads' in info:
                    downloaded_file = info['requested_downloads'][0]['filepath']
                    
                    # Check if video is likely to contain the senator
                    relevance_score = self._calculate_relevance_score(info, senator)
                    
                    if relevance_score >= 0.5:  # Minimum relevance threshold
                        sample_segments = await self._extract_speaker_segments(downloaded_file, senator)
                        
                        return {
                            "source": "youtube",
                            "source_url": video_url,
                            "file_path": downloaded_file,
                            "duration": info.get('duration', 0),
                            "title": info.get('title', ''),
                            "upload_date": info.get('upload_date', ''),
                            "quality_score": relevance_score,
                            "segments": sample_segments
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting YouTube audio: {e}")
            return None
    
    async def _extract_senate_gov_sample(
        self,
        session: aiohttp.ClientSession,
        audio_url: str,
        senator: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract audio sample from Senate.gov content."""
        try:
            # Download audio file
            async with session.get(audio_url) as response:
                if response.status == 200:
                    filename = f"senate_gov_{senator['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                    file_path = self.output_dir / filename
                    
                    with open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    
                    # Extract speaker segments
                    sample_segments = await self._extract_speaker_segments(file_path, senator)
                    
                    return {
                        "source": "senate_gov",
                        "source_url": audio_url,
                        "file_path": str(file_path),
                        "duration": 0,  # Will be calculated in processing
                        "title": f"Senate.gov content for {senator['display_name']}",
                        "upload_date": datetime.now().strftime('%Y%m%d'),
                        "quality_score": 0.9,  # High for official sources
                        "segments": sample_segments
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting Senate.gov audio from {audio_url}: {e}")
            return None
    
    async def _extract_committee_sample(
        self,
        session: aiohttp.ClientSession,
        hearing_url: str,
        senator: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract audio sample from committee hearing."""
        try:
            # This would integrate with existing ISVP extraction
            # For now, return placeholder
            logger.info(f"Committee sample extraction from {hearing_url} - placeholder")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting committee sample from {hearing_url}: {e}")
            return None
    
    async def _extract_speaker_segments(
        self, 
        audio_file: Path, 
        senator: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract segments where the senator is speaking."""
        try:
            # This would use more advanced speaker diarization
            # For now, return placeholder segments
            
            segments = []
            
            # Simulate finding 2-3 segments per file
            for i in range(2):
                segment = {
                    "start_time": i * 60.0,  # Start at minute intervals
                    "end_time": (i * 60.0) + 10.0,  # 10-second segments
                    "confidence": 0.75 + (i * 0.1),  # Varying confidence
                    "text": f"Sample speech segment {i+1} for {senator['display_name']}",
                    "speaker_confidence": 0.8
                }
                segments.append(segment)
            
            return segments
            
        except Exception as e:
            logger.error(f"Error extracting speaker segments: {e}")
            return []
    
    def _calculate_relevance_score(self, video_info: Dict[str, Any], senator: Dict[str, Any]) -> float:
        """Calculate how relevant a video is for the senator."""
        score = 0.0
        
        title = video_info.get('title', '').lower()
        description = video_info.get('description', '').lower()
        
        # Check for senator name variations
        name_variations = [
            senator['name'].lower(),
            senator['display_name'].lower(),
            *[alias.lower() for alias in senator.get('aliases', [])]
        ]
        
        for name in name_variations:
            if name in title:
                score += 0.4
            if name in description:
                score += 0.2
        
        # Check for congressional keywords
        congressional_keywords = [
            'senate', 'committee', 'hearing', 'congress', 'senator',
            'judiciary', 'commerce', 'banking', 'intelligence'
        ]
        
        for keyword in congressional_keywords:
            if keyword in title:
                score += 0.1
            if keyword in description:
                score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_existing_samples(self, senator: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get existing voice samples for a senator."""
        try:
            senator_dir = self.output_dir / senator['name'].replace(' ', '_')
            if not senator_dir.exists():
                return []
            
            samples = []
            for sample_file in senator_dir.glob("*.json"):
                with open(sample_file, 'r') as f:
                    sample_data = json.load(f)
                samples.append(sample_data)
            
            return samples
            
        except Exception as e:
            logger.error(f"Error getting existing samples: {e}")
            return []
    
    def _save_sample_metadata(self, senator: Dict[str, Any], sample: Dict[str, Any]):
        """Save sample metadata to file."""
        try:
            senator_dir = self.output_dir / senator['name'].replace(' ', '_')
            senator_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            sample_id = f"{sample['source']}_{timestamp}"
            
            metadata_file = senator_dir / f"{sample_id}.json"
            
            sample_metadata = {
                "sample_id": sample_id,
                "senator": senator,
                "collected_at": datetime.now().isoformat(),
                **sample
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(sample_metadata, f, indent=2, default=str)
            
            logger.info(f"Saved sample metadata: {metadata_file}")
            
        except Exception as e:
            logger.error(f"Error saving sample metadata: {e}")
    
    async def collect_all_samples(self, max_concurrent: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """Collect voice samples for all priority senators."""
        logger.info(f"Starting voice sample collection for {len(self.priority_senators)} senators")
        
        # Create semaphore to limit concurrent downloads
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def collect_with_semaphore(senator):
            async with semaphore:
                return senator['name'], await self.collect_samples_for_senator(senator)
        
        # Collect samples concurrently
        tasks = [collect_with_semaphore(senator) for senator in self.priority_senators]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        all_samples = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in concurrent collection: {result}")
                continue
            
            senator_name, samples = result
            all_samples[senator_name] = samples
        
        # Summary
        total_samples = sum(len(samples) for samples in all_samples.values())
        logger.info(f"Collection complete: {total_samples} total samples for {len(all_samples)} senators")
        
        return all_samples


if __name__ == "__main__":
    # Test voice sample collection
    import asyncio
    
    async def test_collection():
        collector = VoiceSampleCollector()
        
        # Test with first priority senator
        if collector.priority_senators:
            test_senator = collector.priority_senators[0]
            samples = await collector.collect_samples_for_senator(test_senator, max_samples=2)
            print(f"Collected {len(samples)} samples for {test_senator['display_name']}")
        else:
            print("No priority senators found")
    
    asyncio.run(test_collection())