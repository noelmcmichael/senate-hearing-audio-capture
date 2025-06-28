"""
Intelligent deduplication engine for merging hearing records from multiple sources.
Part of Phase 7A: Automated Data Synchronization
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class DuplicationMatch:
    """Represents a potential duplicate match between hearings"""
    primary_id: int
    secondary_id: int
    similarity_score: float
    confidence_level: str  # 'high', 'medium', 'low'
    match_factors: Dict[str, float]
    recommended_action: str  # 'auto_merge', 'manual_review', 'ignore'

class DeduplicationEngine:
    """Intelligent engine for detecting and merging duplicate hearing records"""
    
    def __init__(self, auto_merge_threshold: float = 0.9, manual_review_threshold: float = 0.7):
        """Initialize deduplication engine with configurable thresholds"""
        self.auto_merge_threshold = auto_merge_threshold
        self.manual_review_threshold = manual_review_threshold
        
        # Weights for different similarity factors
        self.similarity_weights = {
            'title_similarity': 0.4,      # 40% - Most important
            'date_proximity': 0.3,        # 30% - Very important
            'committee_match': 0.1,       # 10% - Should always match
            'time_proximity': 0.1,        # 10% - If available
            'location_similarity': 0.05,  # 5% - Supplementary
            'witness_overlap': 0.05       # 5% - Supplementary
        }
        
        # Common variations in hearing titles to normalize
        self.title_normalizations = [
            (r'\b(hearing|markup|meeting|session)\b', ''),
            (r'\b(on|regarding|concerning)\b', ''),
            (r'\s+', ' '),
            (r'[^\w\s]', ''),
            (r'\b(the|a|an)\b', ''),
            (r'\bexecutive\s*session\s*\d*\b', 'executive session')
        ]
    
    def find_duplicates(self, hearings: List[Dict[str, Any]]) -> List[DuplicationMatch]:
        """Find potential duplicate hearings in a list"""
        
        logger.info(f"Analyzing {len(hearings)} hearings for duplicates")
        
        matches = []
        
        # Compare each hearing with every other hearing
        for i, hearing1 in enumerate(hearings):
            for j, hearing2 in enumerate(hearings[i+1:], i+1):
                
                # Skip if same record
                if hearing1.get('id') == hearing2.get('id'):
                    continue
                
                # Calculate similarity
                match = self._calculate_similarity(hearing1, hearing2)
                
                if match and match.similarity_score >= self.manual_review_threshold:
                    matches.append(match)
        
        # Sort by similarity score (highest first)
        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        
        logger.info(f"Found {len(matches)} potential duplicate pairs")
        return matches
    
    def _calculate_similarity(self, hearing1: Dict[str, Any], hearing2: Dict[str, Any]) -> Optional[DuplicationMatch]:
        """Calculate similarity score between two hearings"""
        
        # Quick filters to avoid unnecessary computation
        if not self._quick_compatibility_check(hearing1, hearing2):
            return None
        
        match_factors = {}
        
        # 1. Title similarity (40% weight)
        title_score = self._calculate_title_similarity(
            hearing1.get('hearing_title', ''),
            hearing2.get('hearing_title', '')
        )
        match_factors['title_similarity'] = title_score
        
        # 2. Date proximity (30% weight)
        date_score = self._calculate_date_proximity(
            hearing1.get('hearing_date', ''),
            hearing2.get('hearing_date', '')
        )
        match_factors['date_proximity'] = date_score
        
        # 3. Committee match (10% weight)
        committee_score = self._calculate_committee_match(
            hearing1.get('committee_code', ''),
            hearing2.get('committee_code', '')
        )
        match_factors['committee_match'] = committee_score
        
        # 4. Time proximity if available (10% weight)
        time_score = self._calculate_time_proximity(hearing1, hearing2)
        match_factors['time_proximity'] = time_score
        
        # 5. Location similarity (5% weight)
        location_score = self._calculate_location_similarity(hearing1, hearing2)
        match_factors['location_similarity'] = location_score
        
        # 6. Witness overlap (5% weight)
        witness_score = self._calculate_witness_overlap(hearing1, hearing2)
        match_factors['witness_overlap'] = witness_score
        
        # Calculate weighted similarity score
        total_score = sum(
            score * self.similarity_weights[factor]
            for factor, score in match_factors.items()
        )
        
        # Determine confidence level and action
        if total_score >= self.auto_merge_threshold:
            confidence = 'high'
            action = 'auto_merge'
        elif total_score >= self.manual_review_threshold:
            confidence = 'medium'
            action = 'manual_review'
        else:
            confidence = 'low'
            action = 'ignore'
        
        return DuplicationMatch(
            primary_id=hearing1.get('id', 0),
            secondary_id=hearing2.get('id', 0),
            similarity_score=total_score,
            confidence_level=confidence,
            match_factors=match_factors,
            recommended_action=action
        )
    
    def _quick_compatibility_check(self, hearing1: Dict[str, Any], hearing2: Dict[str, Any]) -> bool:
        """Quick check to filter out obviously non-duplicate hearings"""
        
        # Must be same committee
        if hearing1.get('committee_code') != hearing2.get('committee_code'):
            return False
        
        # Must be within reasonable date range (30 days)
        try:
            date1 = datetime.strptime(hearing1.get('hearing_date', ''), '%Y-%m-%d')
            date2 = datetime.strptime(hearing2.get('hearing_date', ''), '%Y-%m-%d')
            
            if abs((date1 - date2).days) > 30:
                return False
        except (ValueError, TypeError):
            # If date parsing fails, continue with analysis
            pass
        
        return True
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between hearing titles"""
        
        if not title1 or not title2:
            return 0.0
        
        # Normalize titles
        norm_title1 = self._normalize_title(title1)
        norm_title2 = self._normalize_title(title2)
        
        if not norm_title1 or not norm_title2:
            return 0.0
        
        # Use sequence matcher for similarity
        similarity = SequenceMatcher(None, norm_title1, norm_title2).ratio()
        
        # Boost score for exact matches of key phrases
        key_phrases = self._extract_key_phrases(norm_title1) | self._extract_key_phrases(norm_title2)
        exact_matches = 0
        
        for phrase in key_phrases:
            if phrase in norm_title1 and phrase in norm_title2:
                exact_matches += 1
        
        # Bonus for exact phrase matches
        if key_phrases:
            phrase_bonus = (exact_matches / len(key_phrases)) * 0.2
            similarity = min(1.0, similarity + phrase_bonus)
        
        return similarity
    
    def _normalize_title(self, title: str) -> str:
        """Normalize hearing title for comparison"""
        
        normalized = title.lower().strip()
        
        # Apply normalization patterns
        for pattern, replacement in self.title_normalizations:
            normalized = re.sub(pattern, replacement, normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _extract_key_phrases(self, title: str) -> set:
        """Extract key phrases from hearing title"""
        
        # Remove common words and extract meaningful phrases
        words = title.split()
        
        # Filter out very common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Extract 2-word and 3-word phrases
        phrases = set()
        for i in range(len(meaningful_words)):
            if i < len(meaningful_words) - 1:
                phrases.add(' '.join(meaningful_words[i:i+2]))
            if i < len(meaningful_words) - 2:
                phrases.add(' '.join(meaningful_words[i:i+3]))
        
        return phrases
    
    def _calculate_date_proximity(self, date1: str, date2: str) -> float:
        """Calculate proximity score based on hearing dates"""
        
        try:
            dt1 = datetime.strptime(date1, '%Y-%m-%d')
            dt2 = datetime.strptime(date2, '%Y-%m-%d')
            
            # Exact date match
            if dt1 == dt2:
                return 1.0
            
            # Calculate days difference
            days_diff = abs((dt1 - dt2).days)
            
            # Score decreases with distance
            if days_diff == 0:
                return 1.0
            elif days_diff <= 1:
                return 0.8
            elif days_diff <= 3:
                return 0.6
            elif days_diff <= 7:
                return 0.4
            elif days_diff <= 14:
                return 0.2
            else:
                return 0.0
        
        except (ValueError, TypeError):
            return 0.5  # Neutral score if dates can't be parsed
    
    def _calculate_committee_match(self, committee1: str, committee2: str) -> float:
        """Calculate committee match score"""
        
        if not committee1 or not committee2:
            return 0.0
        
        return 1.0 if committee1.upper() == committee2.upper() else 0.0
    
    def _calculate_time_proximity(self, hearing1: Dict[str, Any], hearing2: Dict[str, Any]) -> float:
        """Calculate time proximity if time information is available"""
        
        # Extract time from location_info or other fields
        time1 = self._extract_time_info(hearing1)
        time2 = self._extract_time_info(hearing2)
        
        if not time1 or not time2:
            return 0.5  # Neutral score if no time info
        
        try:
            # Simple time comparison
            if time1 == time2:
                return 1.0
            else:
                return 0.3  # Partial match if times are different
        except:
            return 0.5
    
    def _extract_time_info(self, hearing: Dict[str, Any]) -> Optional[str]:
        """Extract time information from hearing record"""
        
        # Check location_info for time
        location_info = hearing.get('location_info', {})
        if isinstance(location_info, str):
            try:
                location_info = json.loads(location_info)
            except json.JSONDecodeError:
                location_info = {}
        
        # Look for time in various fields
        time_patterns = [
            r'\b(\d{1,2}:\d{2}\s*[AP]M)\b',
            r'\b(\d{1,2}\s*[AP]M)\b'
        ]
        
        # Search in title, location, and other text fields
        search_text = ' '.join([
            str(hearing.get('hearing_title', '')),
            str(location_info.get('description', '')),
            str(location_info.get('room', ''))
        ])
        
        for pattern in time_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    def _calculate_location_similarity(self, hearing1: Dict[str, Any], hearing2: Dict[str, Any]) -> float:
        """Calculate location similarity score"""
        
        loc1 = hearing1.get('location_info', {})
        loc2 = hearing2.get('location_info', {})
        
        # Parse JSON if needed
        for loc in [loc1, loc2]:
            if isinstance(loc, str):
                try:
                    loc = json.loads(loc)
                except json.JSONDecodeError:
                    loc = {}
        
        # Compare room and building information
        room1 = str(loc1.get('room', '')).lower().strip()
        room2 = str(loc2.get('room', '')).lower().strip()
        
        building1 = str(loc1.get('building', '')).lower().strip()
        building2 = str(loc2.get('building', '')).lower().strip()
        
        if not room1 and not room2 and not building1 and not building2:
            return 0.5  # Neutral if no location info
        
        # Calculate similarity
        room_match = 1.0 if room1 == room2 and room1 else 0.0
        building_match = 1.0 if building1 == building2 and building1 else 0.0
        
        # Average the matches
        matches = []
        if room1 or room2:
            matches.append(room_match)
        if building1 or building2:
            matches.append(building_match)
        
        return sum(matches) / len(matches) if matches else 0.5
    
    def _calculate_witness_overlap(self, hearing1: Dict[str, Any], hearing2: Dict[str, Any]) -> float:
        """Calculate overlap in witness lists"""
        
        witnesses1 = hearing1.get('witnesses', [])
        witnesses2 = hearing2.get('witnesses', [])
        
        # Parse JSON if needed
        for witnesses in [witnesses1, witnesses2]:
            if isinstance(witnesses, str):
                try:
                    witnesses = json.loads(witnesses)
                except json.JSONDecodeError:
                    witnesses = []
        
        if not witnesses1 and not witnesses2:
            return 0.5  # Neutral if no witness info
        
        if not witnesses1 or not witnesses2:
            return 0.2  # Low score if one has witnesses, other doesn't
        
        # Extract witness names
        names1 = set()
        names2 = set()
        
        for witness in witnesses1:
            if isinstance(witness, dict):
                name = witness.get('name', '').lower().strip()
                if name:
                    names1.add(name)
        
        for witness in witnesses2:
            if isinstance(witness, dict):
                name = witness.get('name', '').lower().strip()
                if name:
                    names2.add(name)
        
        if not names1 or not names2:
            return 0.2
        
        # Calculate Jaccard similarity
        intersection = names1.intersection(names2)
        union = names1.union(names2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def merge_hearings(self, primary: Dict[str, Any], secondary: Dict[str, Any], confidence: float) -> Dict[str, Any]:
        """Merge two hearing records with intelligent field selection"""
        
        merged = primary.copy()
        
        # Prefer API data over scraped data
        api_priority_fields = [
            'congress_api_id', 'hearing_type', 'meeting_status'
        ]
        
        # Source priority: API > Website scraping
        primary_is_api = primary.get('source_api', False)
        secondary_is_api = secondary.get('source_api', False)
        
        for field, value in secondary.items():
            if not value:  # Skip empty values
                continue
            
            current_value = merged.get(field)
            
            # Field-specific merge logic
            if field in api_priority_fields:
                # Prefer API data
                if secondary_is_api and not primary_is_api:
                    merged[field] = value
                elif not current_value:
                    merged[field] = value
            
            elif field in ['streams', 'documents', 'witnesses']:
                # Merge lists/dicts
                merged[field] = self._merge_complex_field(current_value, value, field)
            
            elif field in ['external_urls']:
                # Combine URL lists
                merged[field] = self._merge_url_lists(current_value, value)
            
            elif not current_value:
                # Fill empty fields
                merged[field] = value
        
        # Update merge metadata
        merged['sync_confidence'] = confidence
        merged['source_api'] = primary_is_api or secondary_is_api
        merged['source_website'] = primary.get('source_website', False) or secondary.get('source_website', False)
        merged['updated_at'] = datetime.now().isoformat()
        
        return merged
    
    def _merge_complex_field(self, primary_value: Any, secondary_value: Any, field_type: str) -> Any:
        """Merge complex fields like streams, documents, witnesses"""
        
        # Parse JSON strings if needed
        def parse_if_json(value):
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return {}
            return value or {}
        
        primary_data = parse_if_json(primary_value)
        secondary_data = parse_if_json(secondary_value)
        
        if field_type == 'streams':
            # Merge stream dictionaries
            merged_streams = secondary_data.copy()
            merged_streams.update(primary_data)  # Primary takes precedence
            return merged_streams
        
        elif field_type in ['documents', 'witnesses']:
            # Merge lists, removing duplicates
            primary_list = primary_data if isinstance(primary_data, list) else []
            secondary_list = secondary_data if isinstance(secondary_data, list) else []
            
            # Simple deduplication by title/name
            seen = set()
            merged_list = []
            
            for item in primary_list + secondary_list:
                if isinstance(item, dict):
                    key = item.get('title') or item.get('name') or str(item)
                    if key not in seen:
                        seen.add(key)
                        merged_list.append(item)
            
            return merged_list
        
        return primary_data or secondary_data
    
    def _merge_url_lists(self, primary_urls: Any, secondary_urls: Any) -> List[str]:
        """Merge URL lists, removing duplicates"""
        
        def parse_urls(urls):
            if isinstance(urls, str):
                try:
                    return json.loads(urls)
                except json.JSONDecodeError:
                    return [urls] if urls else []
            elif isinstance(urls, list):
                return urls
            return []
        
        primary_list = parse_urls(primary_urls)
        secondary_list = parse_urls(secondary_urls)
        
        # Combine and deduplicate
        combined = list(set(primary_list + secondary_list))
        return [url for url in combined if url]  # Remove empty strings
    
    def generate_merge_report(self, matches: List[DuplicationMatch]) -> Dict[str, Any]:
        """Generate summary report of deduplication analysis"""
        
        report = {
            'total_matches': len(matches),
            'auto_merge_candidates': len([m for m in matches if m.recommended_action == 'auto_merge']),
            'manual_review_candidates': len([m for m in matches if m.recommended_action == 'manual_review']),
            'confidence_distribution': {
                'high': len([m for m in matches if m.confidence_level == 'high']),
                'medium': len([m for m in matches if m.confidence_level == 'medium']),
                'low': len([m for m in matches if m.confidence_level == 'low'])
            },
            'average_similarity': sum(m.similarity_score for m in matches) / len(matches) if matches else 0.0,
            'top_matches': [
                {
                    'primary_id': m.primary_id,
                    'secondary_id': m.secondary_id,
                    'similarity_score': round(m.similarity_score, 3),
                    'confidence': m.confidence_level,
                    'action': m.recommended_action
                }
                for m in matches[:10]  # Top 10 matches
            ]
        }
        
        return report

if __name__ == "__main__":
    # Test deduplication engine
    
    # Sample hearings for testing
    test_hearings = [
        {
            'id': 1,
            'committee_code': 'SCOM',
            'hearing_title': 'Executive Session 12: AI Oversight and Regulation',
            'hearing_date': '2025-06-27',
            'source_api': True,
            'witnesses': [{'name': 'Dr. Jane Smith'}, {'name': 'John Doe'}]
        },
        {
            'id': 2,
            'committee_code': 'SCOM', 
            'hearing_title': 'Executive Session on AI Oversight',
            'hearing_date': '2025-06-27',
            'source_website': True,
            'witnesses': [{'name': 'Dr. Jane Smith'}],
            'streams': {'isvp_stream': 'test_url'}
        },
        {
            'id': 3,
            'committee_code': 'SSCI',
            'hearing_title': 'Intelligence Briefing on Cybersecurity',
            'hearing_date': '2025-06-28',
            'source_api': True
        }
    ]
    
    engine = DeduplicationEngine()
    
    # Find duplicates
    matches = engine.find_duplicates(test_hearings)
    
    print(f"Found {len(matches)} potential matches")
    for match in matches:
        print(f"Match: {match.primary_id} <-> {match.secondary_id}")
        print(f"  Similarity: {match.similarity_score:.3f}")
        print(f"  Confidence: {match.confidence_level}")
        print(f"  Action: {match.recommended_action}")
        print(f"  Factors: {match.match_factors}")
        print()
    
    # Generate report
    report = engine.generate_merge_report(matches)
    print("Deduplication Report:")
    print(json.dumps(report, indent=2))
    
    print("Deduplication engine testing completed")