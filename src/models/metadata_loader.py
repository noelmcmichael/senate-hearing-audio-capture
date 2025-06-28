"""
Metadata loader for congressional hearing context data.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

from .committee_member import CommitteeMember
from .hearing_witness import HearingWitness
from .hearing import Hearing


class MetadataLoader:
    """
    Loads and manages congressional metadata for transcript enrichment.
    
    Provides centralized access to committee members, witnesses, and hearing data.
    """
    
    def __init__(self, data_directory: str = "data"):
        """
        Initialize metadata loader.
        
        Args:
            data_directory: Path to directory containing metadata files
        """
        self.data_dir = Path(data_directory)
        self.logger = logging.getLogger(__name__)
        
        # Cache for loaded data
        self._members_cache: Dict[str, CommitteeMember] = {}
        self._witnesses_cache: Dict[str, HearingWitness] = {}
        self._hearings_cache: Dict[str, Hearing] = {}
        self._committee_members_cache: Dict[str, List[CommitteeMember]] = {}
        
        # Ensure data directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure all required data directories exist."""
        for subdir in ['committees', 'members', 'witnesses', 'hearings']:
            (self.data_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    def load_committee_members(self, committee_name: str) -> List[CommitteeMember]:
        """
        Load all members for a specific committee.
        
        Args:
            committee_name: Name of the committee (e.g., "Commerce", "Judiciary")
            
        Returns:
            List of committee members
        """
        if committee_name in self._committee_members_cache:
            return self._committee_members_cache[committee_name]
        
        # Try multiple file name variations
        possible_filenames = [
            committee_name.lower().replace(' ', '_'),
            committee_name.lower().replace(' ', ''),
            committee_name.lower()
        ]
        
        committee_file = None
        for filename in possible_filenames:
            test_file = self.data_dir / 'committees' / f"{filename}.json"
            if test_file.exists():
                committee_file = test_file
                break
        
        if committee_file is None:
            self.logger.warning(f"Committee file not found for: {committee_name} (tried: {possible_filenames})")
            return []
        
        try:
            with open(committee_file, 'r') as f:
                data = json.load(f)
            
            members = []
            for member_data in data.get('members', []):
                member = CommitteeMember.from_dict(member_data)
                members.append(member)
                # Cache individual member
                self._members_cache[member.member_id] = member
            
            self._committee_members_cache[committee_name] = members
            return members
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Error loading committee {committee_name}: {e}")
            return []
    
    def load_member(self, member_id: str) -> Optional[CommitteeMember]:
        """
        Load a specific committee member by ID.
        
        Args:
            member_id: Unique member identifier
            
        Returns:
            Committee member or None if not found
        """
        if member_id in self._members_cache:
            return self._members_cache[member_id]
        
        # Try to find member in all committee files
        for committee_file in (self.data_dir / 'committees').glob('*.json'):
            try:
                with open(committee_file, 'r') as f:
                    data = json.load(f)
                
                for member_data in data.get('members', []):
                    if member_data.get('member_id') == member_id:
                        member = CommitteeMember.from_dict(member_data)
                        self._members_cache[member_id] = member
                        return member
                        
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.error(f"Error loading committee file {committee_file}: {e}")
                continue
        
        return None
    
    def load_hearing_witnesses(self, hearing_id: str) -> List[HearingWitness]:
        """
        Load all witnesses for a specific hearing.
        
        Args:
            hearing_id: Unique hearing identifier
            
        Returns:
            List of hearing witnesses
        """
        witness_file = self.data_dir / 'hearings' / hearing_id / 'witnesses.json'
        
        if not witness_file.exists():
            self.logger.warning(f"Witness file not found: {witness_file}")
            return []
        
        try:
            with open(witness_file, 'r') as f:
                data = json.load(f)
            
            witnesses = []
            for witness_data in data.get('witnesses', []):
                witness = HearingWitness.from_dict(witness_data)
                witnesses.append(witness)
                # Cache individual witness
                self._witnesses_cache[witness.witness_id] = witness
            
            return witnesses
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Error loading witnesses for hearing {hearing_id}: {e}")
            return []
    
    def load_hearing(self, hearing_id: str) -> Optional[Hearing]:
        """
        Load a specific hearing by ID.
        
        Args:
            hearing_id: Unique hearing identifier
            
        Returns:
            Hearing object or None if not found
        """
        if hearing_id in self._hearings_cache:
            return self._hearings_cache[hearing_id]
        
        hearing_file = self.data_dir / 'hearings' / hearing_id / 'metadata.json'
        
        if not hearing_file.exists():
            self.logger.warning(f"Hearing file not found: {hearing_file}")
            return None
        
        try:
            with open(hearing_file, 'r') as f:
                data = json.load(f)
            
            hearing = Hearing.from_dict(data)
            self._hearings_cache[hearing_id] = hearing
            return hearing
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Error loading hearing {hearing_id}: {e}")
            return None
    
    def find_speaker_by_name(self, name: str, hearing_id: Optional[str] = None) -> Optional[Union[CommitteeMember, HearingWitness]]:
        """
        Find a speaker (member or witness) by name.
        
        Args:
            name: Name to search for
            hearing_id: Optional hearing ID to limit search scope
            
        Returns:
            Matching committee member or witness, or None
        """
        # If hearing_id provided, search within that hearing's context first
        if hearing_id:
            hearing = self.load_hearing(hearing_id)
            if hearing:
                # Search members present at hearing
                for member_id in hearing.members_present:
                    member = self.load_member(member_id)
                    if member and member.matches_name(name):
                        return member
                
                # Search witnesses at hearing
                witnesses = self.load_hearing_witnesses(hearing_id)
                for witness in witnesses:
                    if witness.matches_name(name):
                        return witness
        
        # Ensure we have loaded committee data for global search
        if not self._members_cache:
            # Load known committees to populate cache
            for committee in ['Commerce', 'House Judiciary']:
                self.load_committee_members(committee)
        
        # Search all cached members and witnesses
        for member in self._members_cache.values():
            if member.matches_name(name):
                return member
        
        for witness in self._witnesses_cache.values():
            if witness.matches_name(name):
                return witness
        
        return None
    
    def save_hearing(self, hearing: Hearing) -> None:
        """
        Save hearing metadata to file.
        
        Args:
            hearing: Hearing object to save
        """
        hearing_dir = self.data_dir / 'hearings' / hearing.hearing_id
        hearing_dir.mkdir(parents=True, exist_ok=True)
        
        hearing_file = hearing_dir / 'metadata.json'
        
        try:
            with open(hearing_file, 'w') as f:
                f.write(hearing.to_json())
            
            # Update cache
            self._hearings_cache[hearing.hearing_id] = hearing
            self.logger.info(f"Saved hearing metadata: {hearing.hearing_id}")
            
        except Exception as e:
            self.logger.error(f"Error saving hearing {hearing.hearing_id}: {e}")
            raise
    
    def get_committee_roster(self, committee_name: str) -> Dict[str, str]:
        """
        Get a simple name-to-ID mapping for a committee.
        
        Args:
            committee_name: Name of the committee
            
        Returns:
            Dictionary mapping display names to member IDs
        """
        members = self.load_committee_members(committee_name)
        return {member.get_display_name(): member.member_id for member in members}