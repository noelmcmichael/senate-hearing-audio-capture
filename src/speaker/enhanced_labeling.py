"""
Enhanced Speaker Labeling for Milestone 5.3
Integrates congressional metadata for accurate speaker identification
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SpeakerIdentification:
    """Speaker identification result"""
    speaker_id: str
    speaker_name: str
    role: str  # CHAIR, RANKING_MEMBER, MEMBER, WITNESS, STAFF
    party: Optional[str] = None
    state: Optional[str] = None
    title: Optional[str] = None
    organization: Optional[str] = None
    confidence: float = 0.0
    source: str = "unknown"  # metadata, pattern, context

@dataclass
class CommitteeContext:
    """Committee context for speaker identification"""
    committee_code: str
    committee_name: str
    chair: Optional[Dict[str, Any]] = None
    ranking_member: Optional[Dict[str, Any]] = None
    members: List[Dict[str, Any]] = None
    witnesses: List[Dict[str, Any]] = None

class EnhancedSpeakerLabeler:
    """Enhanced speaker labeling with congressional metadata integration"""
    
    def __init__(self):
        """Initialize enhanced speaker labeler"""
        self.congressional_data = self._load_congressional_data()
        self.speaker_patterns = self._compile_speaker_patterns()
        self.context_cache = {}
        
    def _load_congressional_data(self) -> Dict[str, Any]:
        """Load congressional metadata"""
        try:
            # Load committee data
            data_dir = Path("data")
            congressional_data = {
                "committees": {},
                "members": {},
                "patterns": {}
            }
            
            # Load committee files
            committees_dir = data_dir / "committees"
            if committees_dir.exists():
                for committee_file in committees_dir.glob("*.json"):
                    try:
                        with open(committee_file, 'r') as f:
                            committee_data = json.load(f)
                        committee_code = committee_file.stem.upper()
                        congressional_data["committees"][committee_code] = committee_data
                        logger.info(f"Loaded committee data: {committee_code}")
                    except Exception as e:
                        logger.error(f"Error loading committee file {committee_file}: {e}")
            
            # Create member lookup
            for committee_code, committee_data in congressional_data["committees"].items():
                if "members" in committee_data:
                    for member in committee_data["members"]:
                        member_id = member.get("member_id", member.get("bioguide_id", ""))
                        if member_id:
                            congressional_data["members"][member_id] = member
                            # Add committee context
                            member["committee_code"] = committee_code
            
            logger.info(f"Loaded congressional data: {len(congressional_data['committees'])} committees, "
                       f"{len(congressional_data['members'])} members")
            
            return congressional_data
            
        except Exception as e:
            logger.error(f"Error loading congressional data: {e}")
            return {"committees": {}, "members": {}, "patterns": {}}
    
    def _compile_speaker_patterns(self) -> List[Dict[str, Any]]:
        """Compile speaker identification patterns"""
        patterns = [
            # Chair patterns
            {
                "pattern": r"^(Chair|Chairman|Chairwoman|The Chair|The Chairman|The Chairwoman)\s*[:\.]?\s*(.*)$",
                "role": "CHAIR",
                "confidence": 0.95
            },
            {
                "pattern": r"^(Mr\.|Ms\.|Mrs\.)\s+(Chair|Chairman|Chairwoman)\s*[:\.]?\s*(.*)$",
                "role": "CHAIR",
                "confidence": 0.90
            },
            
            # Ranking Member patterns
            {
                "pattern": r"^(Ranking Member|The Ranking Member)\s+(.*?)\s*[:\.]?\s*(.*)$",
                "role": "RANKING_MEMBER",
                "confidence": 0.95
            },
            {
                "pattern": r"^(Mr\.|Ms\.|Mrs\.)\s+(.*?),?\s+(Ranking Member)\s*[:\.]?\s*(.*)$",
                "role": "RANKING_MEMBER",
                "confidence": 0.90
            },
            
            # Senator patterns
            {
                "pattern": r"^(Senator|Sen\.)\s+(.*?)\s*[:\.]?\s*(.*)$",
                "role": "MEMBER",
                "confidence": 0.85
            },
            
            # Representative patterns
            {
                "pattern": r"^(Representative|Rep\.)\s+(.*?)\s*[:\.]?\s*(.*)$",
                "role": "MEMBER",
                "confidence": 0.85
            },
            
            # Witness patterns
            {
                "pattern": r"^(Dr\.|Professor|Prof\.)\s+(.*?)\s*[:\.]?\s*(.*)$",
                "role": "WITNESS",
                "confidence": 0.75
            },
            {
                "pattern": r"^(Mr\.|Ms\.|Mrs\.)\s+(.*?),?\s+(.*?)\s*[:\.]?\s*(.*)$",
                "role": "WITNESS",
                "confidence": 0.70
            },
            
            # Generic patterns
            {
                "pattern": r"^(.*?):\s*(.*)$",
                "role": "UNKNOWN",
                "confidence": 0.50
            }
        ]
        
        # Compile regex patterns
        for pattern_info in patterns:
            pattern_info["regex"] = re.compile(pattern_info["pattern"], re.IGNORECASE)
        
        return patterns
    
    def get_committee_context(self, committee_code: str, hearing_id: Optional[str] = None) -> CommitteeContext:
        """Get committee context for speaker identification"""
        try:
            if committee_code in self.context_cache:
                return self.context_cache[committee_code]
            
            committee_data = self.congressional_data["committees"].get(committee_code.upper(), {})
            
            if not committee_data:
                logger.warning(f"No committee data found for {committee_code}")
                return CommitteeContext(
                    committee_code=committee_code,
                    committee_name=f"Unknown Committee ({committee_code})",
                    members=[]
                )
            
            # Extract committee leadership
            chair = None
            ranking_member = None
            members = []
            
            if "members" in committee_data:
                for member in committee_data["members"]:
                    role = member.get("role", "").lower()
                    if "chair" in role and "ranking" not in role:
                        chair = member
                    elif "ranking" in role:
                        ranking_member = member
                    else:
                        members.append(member)
            
            context = CommitteeContext(
                committee_code=committee_code,
                committee_name=committee_data.get("committee_name", f"Committee {committee_code}"),
                chair=chair,
                ranking_member=ranking_member,
                members=members,
                witnesses=[]  # Would be loaded from hearing-specific data
            )
            
            self.context_cache[committee_code] = context
            return context
            
        except Exception as e:
            logger.error(f"Error getting committee context for {committee_code}: {e}")
            return CommitteeContext(
                committee_code=committee_code,
                committee_name=f"Committee {committee_code}",
                members=[]
            )
    
    def identify_speaker_from_text(self, speaker_text: str, committee_context: CommitteeContext) -> SpeakerIdentification:
        """Identify speaker from text using patterns and metadata"""
        try:
            if not speaker_text or not speaker_text.strip():
                return SpeakerIdentification(
                    speaker_id="UNKNOWN",
                    speaker_name="Unknown Speaker",
                    role="UNKNOWN",
                    confidence=0.0,
                    source="empty_text"
                )
            
            speaker_text = speaker_text.strip()
            
            # Try pattern matching
            for pattern_info in self.speaker_patterns:
                match = pattern_info["regex"].match(speaker_text)
                if match:
                    groups = match.groups()
                    role = pattern_info["role"]
                    confidence = pattern_info["confidence"]
                    
                    # Extract name from match
                    name = self._extract_name_from_groups(groups, pattern_info["pattern"])
                    
                    # Try to match with committee metadata
                    if name and committee_context:
                        metadata_match = self._match_with_committee_metadata(
                            name, role, committee_context
                        )
                        if metadata_match:
                            metadata_match.confidence = max(metadata_match.confidence, confidence)
                            metadata_match.source = "metadata_pattern"
                            return metadata_match
                    
                    # Return pattern-based identification
                    return SpeakerIdentification(
                        speaker_id=self._generate_speaker_id(name, role),
                        speaker_name=name or "Unknown",
                        role=role,
                        confidence=confidence,
                        source="pattern"
                    )
            
            # Fallback: try direct metadata matching
            if committee_context:
                metadata_match = self._match_with_committee_metadata(
                    speaker_text, "UNKNOWN", committee_context
                )
                if metadata_match:
                    return metadata_match
            
            # Ultimate fallback
            return SpeakerIdentification(
                speaker_id="UNKNOWN",
                speaker_name=speaker_text,
                role="UNKNOWN",
                confidence=0.1,
                source="fallback"
            )
            
        except Exception as e:
            logger.error(f"Error identifying speaker from text '{speaker_text}': {e}")
            return SpeakerIdentification(
                speaker_id="ERROR",
                speaker_name=speaker_text,
                role="UNKNOWN",
                confidence=0.0,
                source="error"
            )
    
    def _extract_name_from_groups(self, groups: Tuple, pattern: str) -> Optional[str]:
        """Extract name from regex groups"""
        try:
            # Simple heuristic: find the group that looks most like a name
            for group in groups:
                if group and len(group) > 1 and not group.lower() in [
                    "chair", "chairman", "chairwoman", "ranking", "member", 
                    "senator", "sen.", "representative", "rep.", "mr.", "ms.", "mrs.", "dr."
                ]:
                    return group.strip()
            return None
        except Exception:
            return None
    
    def _match_with_committee_metadata(self, name: str, role_hint: str, 
                                     committee_context: CommitteeContext) -> Optional[SpeakerIdentification]:
        """Match speaker with committee metadata"""
        try:
            if not name:
                return None
            
            name_lower = name.lower()
            
            # Check chair
            if committee_context.chair and role_hint in ["CHAIR", "UNKNOWN"]:
                chair_name = committee_context.chair.get("full_name", "").lower()
                if self._name_similarity(name_lower, chair_name) > 0.7:
                    return SpeakerIdentification(
                        speaker_id=committee_context.chair.get("member_id", "CHAIR"),
                        speaker_name=committee_context.chair.get("full_name", name),
                        role="CHAIR",
                        party=committee_context.chair.get("party"),
                        state=committee_context.chair.get("state"),
                        title="Chair",
                        confidence=0.90,
                        source="metadata"
                    )
            
            # Check ranking member
            if committee_context.ranking_member and role_hint in ["RANKING_MEMBER", "UNKNOWN"]:
                ranking_name = committee_context.ranking_member.get("full_name", "").lower()
                if self._name_similarity(name_lower, ranking_name) > 0.7:
                    return SpeakerIdentification(
                        speaker_id=committee_context.ranking_member.get("member_id", "RANKING"),
                        speaker_name=committee_context.ranking_member.get("full_name", name),
                        role="RANKING_MEMBER",
                        party=committee_context.ranking_member.get("party"),
                        state=committee_context.ranking_member.get("state"),
                        title="Ranking Member",
                        confidence=0.90,
                        source="metadata"
                    )
            
            # Check members
            if committee_context.members:
                for member in committee_context.members:
                    member_name = member.get("full_name", "").lower()
                    if self._name_similarity(name_lower, member_name) > 0.7:
                        return SpeakerIdentification(
                            speaker_id=member.get("member_id", f"MEMBER_{member_name}"),
                            speaker_name=member.get("full_name", name),
                            role="MEMBER",
                            party=member.get("party"),
                            state=member.get("state"),
                            title=member.get("title", "Member"),
                            confidence=0.85,
                            source="metadata"
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"Error matching with committee metadata: {e}")
            return None
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity score"""
        try:
            if not name1 or not name2:
                return 0.0
            
            # Simple similarity based on common words
            words1 = set(name1.lower().split())
            words2 = set(name2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception:
            return 0.0
    
    def _generate_speaker_id(self, name: Optional[str], role: str) -> str:
        """Generate speaker ID"""
        if name:
            # Create ID from name
            clean_name = re.sub(r'[^\w\s]', '', name).strip()
            return f"{role}_{clean_name.replace(' ', '_').upper()}"
        else:
            return f"{role}_UNKNOWN"
    
    def enhance_transcript_segments(self, transcript_segments: List[Dict[str, Any]], 
                                  committee_code: str, hearing_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Enhance transcript segments with speaker identification"""
        try:
            logger.info(f"Enhancing {len(transcript_segments)} transcript segments for {committee_code}")
            
            # Get committee context
            committee_context = self.get_committee_context(committee_code, hearing_id)
            
            enhanced_segments = []
            
            for i, segment in enumerate(transcript_segments):
                try:
                    # Extract speaker text (various possible fields)
                    speaker_text = (
                        segment.get("speaker", "") or 
                        segment.get("speaker_text", "") or
                        segment.get("text", "")[:50] or  # Use first part of text as fallback
                        ""
                    )
                    
                    # Identify speaker
                    speaker_id = self.identify_speaker_from_text(speaker_text, committee_context)
                    
                    # Create enhanced segment
                    enhanced_segment = segment.copy()
                    enhanced_segment.update({
                        "enhanced_speaker": {
                            "speaker_id": speaker_id.speaker_id,
                            "speaker_name": speaker_id.speaker_name,
                            "role": speaker_id.role,
                            "party": speaker_id.party,
                            "state": speaker_id.state,
                            "title": speaker_id.title,
                            "organization": speaker_id.organization,
                            "confidence": speaker_id.confidence,
                            "source": speaker_id.source
                        },
                        "committee_context": {
                            "committee_code": committee_context.committee_code,
                            "committee_name": committee_context.committee_name
                        }
                    })
                    
                    enhanced_segments.append(enhanced_segment)
                    
                except Exception as e:
                    logger.error(f"Error enhancing segment {i}: {e}")
                    # Keep original segment if enhancement fails
                    enhanced_segments.append(segment)
            
            logger.info(f"Enhanced {len(enhanced_segments)} segments successfully")
            return enhanced_segments
            
        except Exception as e:
            logger.error(f"Error enhancing transcript segments: {e}")
            return transcript_segments  # Return original if enhancement fails

# Global labeler instance
_enhanced_speaker_labeler = None

def get_enhanced_speaker_labeler() -> EnhancedSpeakerLabeler:
    """Get enhanced speaker labeler singleton"""
    global _enhanced_speaker_labeler
    if _enhanced_speaker_labeler is None:
        _enhanced_speaker_labeler = EnhancedSpeakerLabeler()
    return _enhanced_speaker_labeler