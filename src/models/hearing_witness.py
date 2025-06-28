"""
Hearing witness model for congressional hearing metadata.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json


@dataclass
class HearingWitness:
    """
    Represents a witness testifying at a congressional hearing.
    
    Used for speaker identification and transcript enrichment.
    """
    witness_id: str                   # Unique identifier (e.g., "WTN_JANE_SMITH_FTC")
    full_name: str                    # Full legal name
    title: str                        # Professional title
    organization: str                 # Affiliated organization
    hearing_title: str                # Title of the hearing
    committee: str                    # Committee holding the hearing
    hearing_date: str                 # Date in YYYY-MM-DD format
    aliases: List[str] = field(default_factory=list)  # Common name variations
    source_url: Optional[str] = None  # URL to hearing announcement/witness list
    bio: Optional[str] = None         # Brief biographical information
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'witness_id': self.witness_id,
            'full_name': self.full_name,
            'title': self.title,
            'organization': self.organization,
            'hearing_title': self.hearing_title,
            'committee': self.committee,
            'hearing_date': self.hearing_date,
            'aliases': self.aliases,
            'source_url': self.source_url,
            'bio': self.bio
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HearingWitness':
        """Create instance from dictionary."""
        return cls(
            witness_id=data['witness_id'],
            full_name=data['full_name'],
            title=data['title'],
            organization=data['organization'],
            hearing_title=data['hearing_title'],
            committee=data['committee'],
            hearing_date=data['hearing_date'],
            aliases=data.get('aliases', []),
            source_url=data.get('source_url'),
            bio=data.get('bio')
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'HearingWitness':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def matches_name(self, name: str) -> bool:
        """
        Check if a name string matches this witness.
        
        Useful for speaker identification in transcripts.
        """
        name_lower = name.lower()
        
        # Check full name
        if self.full_name.lower() in name_lower or name_lower in self.full_name.lower():
            return True
            
        # Check aliases
        for alias in self.aliases:
            if alias.lower() in name_lower or name_lower in alias.lower():
                return True
                
        return False
    
    def get_display_name(self) -> str:
        """Get formatted display name for transcripts."""
        return f"{self.full_name}, {self.title}, {self.organization}"
    
    def get_short_display_name(self) -> str:
        """Get short display name for compact contexts."""
        return f"{self.full_name} ({self.organization})"