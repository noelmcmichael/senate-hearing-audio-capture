"""
Hearing model for congressional hearing metadata.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json
from datetime import datetime


@dataclass
class Hearing:
    """
    Represents a congressional hearing with associated metadata.
    
    Central record linking audio, transcripts, and participants.
    """
    hearing_id: str                   # Unique identifier (e.g., "SCOM-2025-06-10-DIGITAL-OVERSIGHT")
    title: str                        # Official hearing title
    committee: str                    # Committee holding the hearing
    date: str                         # Date in YYYY-MM-DD format
    members_present: List[str] = field(default_factory=list)  # Member IDs present
    witnesses: List[str] = field(default_factory=list)        # Witness IDs testifying
    subcommittee: Optional[str] = None        # Subcommittee if applicable
    video_url: Optional[str] = None           # Original video/stream URL
    audio_file: Optional[str] = None          # Path to extracted audio
    transcript_file: Optional[str] = None     # Path to transcript
    summary: Optional[str] = None             # Brief hearing summary
    topics: List[str] = field(default_factory=list)  # Main topics discussed
    duration_minutes: Optional[int] = None    # Hearing duration
    status: str = "scheduled"                 # scheduled, captured, transcribed, analyzed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'hearing_id': self.hearing_id,
            'title': self.title,
            'committee': self.committee,
            'subcommittee': self.subcommittee,
            'date': self.date,
            'members_present': self.members_present,
            'witnesses': self.witnesses,
            'video_url': self.video_url,
            'audio_file': self.audio_file,
            'transcript_file': self.transcript_file,
            'summary': self.summary,
            'topics': self.topics,
            'duration_minutes': self.duration_minutes,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Hearing':
        """Create instance from dictionary."""
        return cls(
            hearing_id=data['hearing_id'],
            title=data['title'],
            committee=data['committee'],
            date=data['date'],
            subcommittee=data.get('subcommittee'),
            members_present=data.get('members_present', []),
            witnesses=data.get('witnesses', []),
            video_url=data.get('video_url'),
            audio_file=data.get('audio_file'),
            transcript_file=data.get('transcript_file'),
            summary=data.get('summary'),
            topics=data.get('topics', []),
            duration_minutes=data.get('duration_minutes'),
            status=data.get('status', 'scheduled')
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Hearing':
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def get_file_safe_id(self) -> str:
        """Get filesystem-safe version of hearing ID."""
        return self.hearing_id.replace('/', '-').replace(' ', '_')
    
    def is_completed(self) -> bool:
        """Check if hearing has been fully processed."""
        return self.status in ['transcribed', 'analyzed'] and self.audio_file is not None
    
    def get_output_directory(self) -> str:
        """Get directory path for this hearing's files."""
        return f"output/{self.get_file_safe_id()}"
    
    def update_status(self, new_status: str) -> None:
        """Update hearing status with validation."""
        valid_statuses = ['scheduled', 'captured', 'transcribed', 'analyzed', 'failed']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")
        self.status = new_status
    
    def add_participant(self, participant_id: str, participant_type: str) -> None:
        """Add a member or witness to the hearing."""
        if participant_type == 'member' and participant_id not in self.members_present:
            self.members_present.append(participant_id)
        elif participant_type == 'witness' and participant_id not in self.witnesses:
            self.witnesses.append(participant_id)
    
    def get_display_title(self) -> str:
        """Get formatted title for display."""
        committee_short = self.committee.replace('Senate ', '').replace('House ', '')
        return f"{committee_short}: {self.title}"