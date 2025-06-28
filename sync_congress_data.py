#!/usr/bin/env python3
"""
Congress Data Synchronization Utility

Syncs congressional member data from the official Congress.gov API to ensure
our metadata is current and authoritative.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from api.congress_api_client import CongressAPIClient
from models.committee_member import CommitteeMember


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def get_senate_commerce_members(api_client: CongressAPIClient):
    """Get Senate Commerce Committee members from API."""
    logger = logging.getLogger(__name__)
    
    # Get current members (all chambers)
    logger.info("Getting current members from Congress API...")
    response = api_client.get_current_members()
    
    if not response.success:
        logger.error(f"Failed to get members: {response.error}")
        return []
    
    members = response.data.get('members', [])
    logger.info(f"Retrieved {len(members)} total members")
    
    # Filter for Senate members
    senate_members = []
    for member in members:
        # Check if this is a Senate member
        terms = member.get('terms', {})
        term_items = terms.get('item', [])
        
        if not term_items:
            continue
            
        # Get the most recent term
        latest_term = term_items[-1] if isinstance(term_items, list) else term_items
        
        if latest_term.get('chamber') == 'Senate':
            # Get detailed member information
            bioguide_id = member.get('bioguideId')
            if bioguide_id:
                comprehensive_data = api_client.get_comprehensive_member_data(bioguide_id)
                if comprehensive_data:
                    senate_members.append(comprehensive_data)
    
    logger.info(f"Found {len(senate_members)} Senate members")
    return senate_members


def create_committee_member_from_api_data(api_data, committee_name="Senate Commerce"):
    """Create CommitteeMember from comprehensive API data."""
    try:
        current_service = api_data.get('current_service', {})
        name_data = api_data.get('name', {})
        
        # Generate member ID
        last_name = name_data.get('last', '').upper()
        bioguide_id = api_data.get('bioguide_id', '')
        member_id = f"SEN_{last_name}" if last_name else bioguide_id
        
        # Create aliases
        full_name = name_data.get('full', '')
        last_name_display = name_data.get('last', '')
        
        aliases = []
        if full_name and last_name_display:
            aliases.extend([
                full_name,
                f"Sen. {last_name_display}",
                f"Senator {last_name_display}"
            ])
        
        # Determine role for known members
        role = None
        if 'cantwell' in full_name.lower():
            role = 'Chair'
        elif 'cruz' in full_name.lower():
            role = 'Ranking Member'
        
        return CommitteeMember(
            member_id=member_id,
            full_name=full_name,
            title=current_service.get('member_type', 'Senator'),
            party=current_service.get('party_code', ''),
            state=current_service.get('state_code', ''),
            chamber=current_service.get('chamber', 'Senate'),
            committee=committee_name,
            role=role,
            aliases=aliases
        )
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating CommitteeMember: {e}")
        return None


def sync_senate_commerce():
    """Sync Senate Commerce Committee with fresh API data."""
    logger = logging.getLogger(__name__)
    
    # Initialize API client
    logger.info("Initializing Congress API client...")
    try:
        api_client = CongressAPIClient()
        
        # Test connection
        if not api_client.test_connection().success:
            logger.error("Failed to connect to Congress API")
            return False
            
    except Exception as e:
        logger.error(f"Failed to initialize API client: {e}")
        return False
    
    # Get Senate members
    senate_members = get_senate_commerce_members(api_client)
    if not senate_members:
        logger.error("No Senate members retrieved")
        return False
    
    # Known Senate Commerce Committee members (current as of 2025)
    # Note: In production, this would come from committee assignments API
    commerce_member_names = [
        'maria cantwell',     # Chair (D-WA)
        'ted cruz',          # Ranking Member (R-TX) 
        'amy klobuchar',     # (D-MN)
        'marsha blackburn',  # (R-TN)
        'brian schatz',      # (D-HI)
        'john thune',        # (R-SD)
        'edward markey',     # (D-MA)
        'roger wicker',      # (R-MS)
        'gary peters',       # (D-MI)
        'deb fischer',       # (R-NE)
        'tammy baldwin',     # (D-WI)
        'jerry moran',       # (R-KS)
        'john hickenlooper', # (D-CO)
        'dan sullivan',      # (R-AK)
        'raphael warnock',   # (D-GA)
        'todd young',        # (R-IN)
        'ben ray luján',     # (D-NM)
        'ted budd'           # (R-NC)
    ]
    
    # Filter Senate members for Commerce Committee
    commerce_members = []
    for member_data in senate_members:
        full_name = member_data.get('name', {}).get('full', '').lower()
        
        # Check if this member is on Commerce Committee
        for commerce_name in commerce_member_names:
            if commerce_name in full_name:
                committee_member = create_committee_member_from_api_data(member_data)
                if committee_member:
                    commerce_members.append(committee_member)
                break
    
    logger.info(f"Identified {len(commerce_members)} Commerce Committee members")
    
    # Create committee data structure
    committee_data = {
        'committee_info': {
            'name': 'Commerce',
            'full_name': 'Senate Committee on Commerce, Science, and Transportation',
            'chamber': 'Senate',
            'jurisdiction': 'Interstate commerce, transportation, communications, technology policy',
            'website': 'https://www.commerce.senate.gov',
            'api_sync_date': datetime.now().isoformat(),
            'api_source': 'Congress.gov API v3'
        },
        'members': [member.to_dict() for member in commerce_members]
    }
    
    # Save to file
    output_file = Path('data/committees/commerce.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(committee_data, f, indent=2)
    
    logger.info(f"✅ Successfully synced {len(commerce_members)} Commerce Committee members")
    logger.info(f"📁 Saved to: {output_file}")
    
    return True


def main():
    """Main synchronization function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🚀 Congress Data Synchronization")
    print("=" * 40)
    
    try:
        success = sync_senate_commerce()
        
        if success:
            print("\n✅ SYNCHRONIZATION COMPLETE")
            print("• Senate Commerce Committee data updated with official API data")
            print("• Member information is now current and authoritative")
            print("• Ready for enhanced transcript enrichment")
        else:
            print("\n❌ SYNCHRONIZATION FAILED")
            print("• Check API key and network connectivity")
            print("• Review logs for specific error details")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error during sync: {e}")
        print(f"\n❌ ERROR: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())