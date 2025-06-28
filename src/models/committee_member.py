"""
Committee member model for congressional hearing metadata.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json


@dataclass
class CommitteeMember:
    """
    Represents a member of a congressional committee.
    
    Used for speaker identification and transcript enrichment.
    """
    member_id: str                    # Unique identifier (e.g., "SEN_CANTWELL")
    full_name: str                    # Full legal name
    title: str                        # Official title (Senator, Representative, etc.)
    party: str                        # Party affiliation (D, R, I)
    state: str                        # State abbreviation (WA, TX, etc.)
    chamber: str                      # Senate or House
    committee: str                    # Primary committee name
    subcommittee: Optional[str] = None  # Subcommittee if applicable
    role: Optional[str] = None        # Chair, Ranking Member, etc.
    aliases: List[str] = field(default_factory=list)  # Common name variations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'member_id': self.member_id,
            'full_name': self.full_name,
            'title': self.title,
            'party': self.party,
            'state': self.state,
            'chamber': self.chamber,
            'committee': self.committee,
            'subcommittee': self.subcommittee,
            'role': self.role,
            'aliases': self.aliases
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommitteeMember':
        """Create instance from dictionary."""
        return cls(
            member_id=data['member_id'],
            full_name=data['full_name'],
            title=data['title'],
            party=data['party'],
            state=data['state'],
            chamber=data['chamber'],
            committee=data['committee'],
            subcommittee=data.get('subcommittee'),
            role=data.get('role'),
            aliases=data.get('aliases', [])
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CommitteeMember':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def matches_name(self, name: str) -> bool:
        """
        Check if a name string matches this member.
        
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
        if self.role:
            return f"{self.role} {self.full_name} ({self.party}-{self.state})"
        else:
            return f"{self.title} {self.full_name} ({self.party}-{self.state})"