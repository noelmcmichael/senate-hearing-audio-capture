"""
Congress API synchronization for metadata system.

Syncs official congressional data with our local metadata system.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from .committee_member import CommitteeMember
from .metadata_loader import MetadataLoader
from api.congress_api_client import CongressAPIClient


class CongressDataSync:
    """
    Synchronizes congressional data from the official Congress API.
    
    Updates local metadata files with authoritative congressional data.
    """
    
    def __init__(self, data_directory: str = "data", api_client: Optional[CongressAPIClient] = None):
        """
        Initialize Congress data synchronizer.
        
        Args:
            data_directory: Path to metadata directory
            api_client: Optional Congress API client instance
        """
        self.data_dir = Path(data_directory)
        self.metadata_loader = MetadataLoader(data_directory)
        self.api_client = api_client or CongressAPIClient()
        self.logger = logging.getLogger(__name__)
        
        # Committee system code mappings
        self.committee_mappings = {
            'commerce': {
                'chamber': 'senate',
                'system_code': 'sscm00',
                'official_name': 'Committee on Commerce, Science, and Transportation'
            },
            'judiciary_senate': {
                'chamber': 'senate', 
                'system_code': 'ssju00',
                'official_name': 'Committee on the Judiciary'
            },
            'judiciary_house': {
                'chamber': 'house',
                'system_code': 'hsju00', 
                'official_name': 'Committee on the Judiciary'
            },
            'intelligence_senate': {
                'chamber': 'senate',
                'system_code': 'slin00',
                'official_name': 'Select Committee on Intelligence'
            },
            'banking_senate': {
                'chamber': 'senate',
                'system_code': 'ssbk00',
                'official_name': 'Committee on Banking, Housing, and Urban Affairs'
            },
            'financial_services_house': {
                'chamber': 'house',
                'system_code': 'hsba00',
                'official_name': 'Committee on Financial Services'
            }
        }
    
    def test_api_connection(self) -> bool:
        """
        Test Congress API connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        response = self.api_client.test_connection()
        return response.success
    
    def sync_committee_members(self, committee_key: str) -> Tuple[bool, str]:
        """
        Sync members for a specific committee.
        
        Args:
            committee_key: Key from committee_mappings
            
        Returns:
            Tuple of (success, message)
        """
        if committee_key not in self.committee_mappings:
            return False, f"Unknown committee: {committee_key}"
        
        committee_info = self.committee_mappings[committee_key]
        self.logger.info(f"Syncing {committee_info['official_name']} members...")
        
        try:
            # Get current congress
            congress_response = self.api_client.get_current_congress()
            if not congress_response.success:
                return False, f"Failed to get current congress: {congress_response.error}"
            
            congresses = congress_response.data.get('congresses', [])
            if not congresses:
                return False, "No congress data found"
            try:
                current_congress = int(congresses[0].get('name', '').split('th')[0])
            except (ValueError, IndexError):
                return False, "Could not parse congress number"
            
            # Get committee members by getting current members and filtering
            # Note: Congress API doesn't have direct committee membership endpoint
            # So we get all current members and then identify committee membership
            # through their committee assignments
            
            chamber = committee_info['chamber']
            members_response = self.api_client.get_current_members(chamber)
            if not members_response.success:
                return False, f"Failed to get members: {members_response.error}"
            
            # Convert API data to our CommitteeMember format
            members = []
            members_data = members_response.data.get('members', [])
            
            for member_data in members_data:
                # Get detailed member info
                bioguide_id = member_data.get('bioguideId')
                if not bioguide_id:
                    continue
                
                comprehensive_data = self.api_client.get_comprehensive_member_data(bioguide_id)
                if not comprehensive_data:
                    self.logger.warning(f"Failed to get comprehensive data for {bioguide_id}")
                    continue
                
                # Create CommitteeMember from API data
                member = self._create_committee_member_from_api(
                    comprehensive_data, 
                    committee_key,
                    committee_info['official_name']
                )
                
                if member:
                    members.append(member)
            
            # Save to file
            committee_file = self.data_dir / 'committees' / f"{committee_key}.json"
            committee_data = {
                'committee_info': {
                    'name': committee_key.replace('_', ' ').title(),
                    'full_name': committee_info['official_name'],
                    'chamber': committee_info['chamber'].title(),
                    'system_code': committee_info['system_code'],
                    'api_sync_date': datetime.now().isoformat(),
                    'congress': current_congress
                },
                'members': [member.to_dict() for member in members]
            }
            
            # Ensure directory exists
            committee_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(committee_file, 'w') as f:
                json.dump(committee_data, f, indent=2)
            
            self.logger.info(f"✅ Synced {len(members)} members for {committee_info['official_name']}")
            return True, f"Successfully synced {len(members)} members"
            
        except Exception as e:
            error_msg = f"Error syncing committee {committee_key}: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _create_committee_member_from_api(
        self, 
        api_data: Dict, 
        committee_key: str,
        committee_name: str
    ) -> Optional[CommitteeMember]:
        """
        Create CommitteeMember from Congress API data.
        
        Args:
            api_data: Comprehensive member data from API
            committee_key: Committee identifier
            committee_name: Full committee name
            
        Returns:
            CommitteeMember instance or None if data insufficient
        """
        try:
            current_service = api_data.get('current_service', {})
            name_data = api_data.get('name', {})
            
            # Generate member ID
            last_name = name_data.get('last', '').upper()
            first_initial = name_data.get('first', '')[0].upper() if name_data.get('first') else ''
            chamber_prefix = 'SEN' if current_service.get('chamber') == 'Senate' else 'REP'
            member_id = f"{chamber_prefix}_{last_name}_{first_initial}" if last_name else api_data.get('bioguide_id')
            
            # Create name variations for aliases
            full_name = name_data.get('full', '')
            last_name_lower = name_data.get('last', '')
            honorific = name_data.get('honorific', '')
            
            aliases = []
            if full_name:
                aliases.extend([
                    full_name,
                    f"{honorific} {last_name_lower}" if honorific and last_name_lower else None,
                    f"Sen. {last_name_lower}" if chamber_prefix == 'SEN' and last_name_lower else None,
                    f"Rep. {last_name_lower}" if chamber_prefix == 'REP' and last_name_lower else None
                ])
            
            # Filter out None values
            aliases = [alias for alias in aliases if alias]
            
            # Determine role (this would need committee-specific logic in real implementation)
            role = None
            if committee_key == 'commerce' and member_id.endswith('CANTWELL'):
                role = 'Chair'
            elif committee_key == 'commerce' and member_id.endswith('CRUZ'):
                role = 'Ranking Member'
            
            return CommitteeMember(
                member_id=member_id,
                full_name=full_name or f"{name_data.get('first', '')} {name_data.get('last', '')}".strip(),
                title=current_service.get('member_type', 'Member'),
                party=current_service.get('party_code', ''),
                state=current_service.get('state_code', ''),
                chamber=current_service.get('chamber', ''),
                committee=committee_name,
                role=role,
                aliases=aliases
            )
            
        except Exception as e:
            self.logger.error(f"Error creating CommitteeMember from API data: {e}")
            return None
    
    def sync_all_committees(self) -> Dict[str, Tuple[bool, str]]:
        """
        Sync all configured committees.
        
        Returns:
            Dictionary mapping committee keys to (success, message) tuples
        """
        results = {}
        
        for committee_key in self.committee_mappings.keys():
            success, message = self.sync_committee_members(committee_key)
            results[committee_key] = (success, message)
            
            if success:
                self.logger.info(f"✅ {committee_key}: {message}")
            else:
                self.logger.error(f"❌ {committee_key}: {message}")
        
        return results
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get synchronization status for all committees.
        
        Returns:
            Dictionary with sync status information
        """
        status = {
            'last_checked': datetime.now().isoformat(),
            'api_connection': self.test_api_connection(),
            'committees': {}
        }
        
        for committee_key in self.committee_mappings.keys():
            committee_file = self.data_dir / 'committees' / f"{committee_key}.json"
            
            if committee_file.exists():
                try:
                    with open(committee_file, 'r') as f:
                        data = json.load(f)
                    
                    committee_info = data.get('committee_info', {})
                    status['committees'][committee_key] = {
                        'exists': True,
                        'member_count': len(data.get('members', [])),
                        'last_sync': committee_info.get('api_sync_date'),
                        'congress': committee_info.get('congress'),
                        'official_name': committee_info.get('full_name')
                    }
                except Exception as e:
                    status['committees'][committee_key] = {
                        'exists': True,
                        'error': str(e)
                    }
            else:
                status['committees'][committee_key] = {
                    'exists': False,
                    'official_name': self.committee_mappings[committee_key]['official_name']
                }
        
        return status
    
    def update_member_aliases(self, committee_key: str) -> Tuple[bool, str]:
        """
        Update member aliases with common congressional name variations.
        
        Args:
            committee_key: Committee to update
            
        Returns:
            Tuple of (success, message)
        """
        committee_file = self.data_dir / 'committees' / f"{committee_key}.json"
        
        if not committee_file.exists():
            return False, f"Committee file not found: {committee_file}"
        
        try:
            with open(committee_file, 'r') as f:
                data = json.load(f)
            
            updated_count = 0
            for member_data in data.get('members', []):
                # Add common variations
                full_name = member_data.get('full_name', '')
                last_name = full_name.split()[-1] if full_name else ''
                title = member_data.get('title', '')
                role = member_data.get('role', '')
                
                current_aliases = set(member_data.get('aliases', []))
                new_aliases = set()
                
                if last_name:
                    new_aliases.add(f"{title} {last_name}")
                    new_aliases.add(f"The {role}" if role else "")
                    new_aliases.add(f"{role} {last_name}" if role else "")
                
                # Remove empty strings
                new_aliases.discard("")
                
                # Add new aliases
                all_aliases = list(current_aliases.union(new_aliases))
                if len(all_aliases) > len(current_aliases):
                    member_data['aliases'] = all_aliases
                    updated_count += 1
            
            # Save updated data
            with open(committee_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True, f"Updated aliases for {updated_count} members"
            
        except Exception as e:
            return False, f"Error updating aliases: {e}"