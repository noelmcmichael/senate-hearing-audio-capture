#!/usr/bin/env python3
"""
Priority Committee Sync Utility

Syncs priority Senate committees with the Congress.gov API, focusing on
ISVP-compatible committees first for comprehensive coverage.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from models.congress_sync import CongressDataSync
from api.congress_api_client import CongressAPIClient


def setup_logging():
    """Set up logging for the sync process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/committee_sync.log', mode='a')
        ]
    )


def sync_priority_committees():
    """Sync priority committees in order."""
    print("🏛️ PRIORITY COMMITTEE SYNC")
    print("=" * 50)
    
    # Initialize sync system
    try:
        sync_system = CongressDataSync()
        print("✅ Congress data sync system initialized")
    except Exception as e:
        print(f"❌ Failed to initialize sync system: {e}")
        return False
    
    # Test API connection
    print("\n🔗 Testing Congress API connection...")
    if not sync_system.test_api_connection():
        print("❌ API connection failed. Check your API key.")
        return False
    print("✅ API connection successful")
    
    # Get priority committees
    priority_committees = sync_system.get_priority_committees(isvp_only=True)
    print(f"\n🎯 Priority ISVP-Compatible Committees ({len(priority_committees)}):")
    for i, committee_key in enumerate(priority_committees, 1):
        committee_info = sync_system.committee_mappings[committee_key]
        print(f"  {i}. {committee_info['official_name']}")
    
    # Sync priority committees
    print(f"\n🔄 Syncing {len(priority_committees)} priority committees...")
    results = sync_system.sync_priority_committees(isvp_only=True)
    
    # Report results
    print(f"\n📊 SYNC RESULTS")
    print("-" * 30)
    
    successful = 0
    failed = 0
    
    for committee_key, (success, message) in results.items():
        committee_info = sync_system.committee_mappings[committee_key]
        status = "✅" if success else "❌"
        print(f"{status} {committee_info['official_name']}")
        print(f"   {message}")
        
        if success:
            successful += 1
        else:
            failed += 1
    
    print(f"\n📈 SUMMARY")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(successful/(successful+failed)*100):.1f}%" if (successful+failed) > 0 else "N/A")
    
    return successful > 0


def show_sync_status():
    """Show current sync status for all committees."""
    print("\n📋 CURRENT SYNC STATUS")
    print("=" * 50)
    
    try:
        sync_system = CongressDataSync()
        status = sync_system.get_sync_status()
        
        print(f"API Connection: {'✅' if status['api_connection'] else '❌'}")
        print(f"Last Checked: {status['last_checked']}")
        
        print(f"\n📊 Committee Status:")
        for committee_key, committee_status in status['committees'].items():
            committee_info = sync_system.committee_mappings.get(committee_key, {})
            official_name = committee_status.get('official_name', committee_info.get('official_name', 'Unknown'))
            
            if committee_status.get('exists'):
                if 'error' in committee_status:
                    print(f"  ❌ {official_name}")
                    print(f"     Error: {committee_status['error']}")
                else:
                    member_count = committee_status.get('member_count', 0)
                    last_sync = committee_status.get('last_sync', 'Never')
                    congress = committee_status.get('congress', 'Unknown')
                    print(f"  ✅ {official_name}")
                    print(f"     Members: {member_count}, Last Sync: {last_sync[:19]}, Congress: {congress}")
            else:
                print(f"  ⭕ {official_name}")
                print(f"     Not synced")
        
    except Exception as e:
        print(f"❌ Error checking sync status: {e}")


def main():
    """Main sync process."""
    setup_logging()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--status':
        show_sync_status()
        return
    
    print("Starting priority committee sync process...")
    
    # Show current status first
    show_sync_status()
    
    # Ask for confirmation
    print(f"\n⚠️  This will sync committee data with the Congress.gov API.")
    print(f"Existing committee files will be updated with official data.")
    
    response = input("\nProceed with sync? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Sync cancelled.")
        return
    
    # Perform sync
    success = sync_priority_committees()
    
    if success:
        print(f"\n✅ Priority committee sync completed successfully!")
        print(f"Run with --status to see updated sync status.")
    else:
        print(f"\n❌ Priority committee sync failed or had issues.")
        print(f"Check the logs for more details.")


if __name__ == "__main__":
    main()