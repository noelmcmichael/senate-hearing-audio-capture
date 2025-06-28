#!/usr/bin/env python3
"""
Congress API Integration Test Suite

Tests the integration with the official Congress.gov API for authoritative
congressional data synchronization.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from api.congress_api_client import CongressAPIClient
from models.congress_sync import CongressDataSync


class TestResult:
    """Simple test result tracker."""
    
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.failures = []
    
    def add_test(self, test_name: str, passed: bool, message: str = ""):
        """Add a test result."""
        self.total += 1
        if passed:
            self.passed += 1
            print(f"✅ {test_name}")
        else:
            self.failed += 1
            self.failures.append(f"{test_name}: {message}")
            print(f"❌ {test_name}: {message}")
    
    def summary(self) -> str:
        """Get test summary."""
        success_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        return f"Tests: {self.passed}/{self.total} passed ({success_rate:.1f}%)"


def test_api_client():
    """Test Congress API client functionality."""
    print("\n🧪 Testing Congress API Client")
    result = TestResult()
    
    try:
        # Initialize client
        client = CongressAPIClient()
        
        # Test connection
        connection_test = client.test_connection()
        result.add_test(
            "API connection",
            connection_test.success,
            connection_test.error if not connection_test.success else ""
        )
        
        if not connection_test.success:
            print("   ⚠️  Skipping remaining tests due to connection failure")
            print(f"   {result.summary()}")
            return result
        
        # Test current congress
        congress_response = client.get_current_congress()
        result.add_test(
            "Get current congress",
            congress_response.success,
            congress_response.error if not congress_response.success else ""
        )
        
        if congress_response.success:
            congresses = congress_response.data.get('congresses', [])
            congress_name = congresses[0].get('name') if congresses else 'Unknown'
            print(f"   📊 Current Congress: {congress_name}")
        
        # Test get current members
        members_response = client.get_current_members(chamber='senate', limit=10)
        result.add_test(
            "Get current Senate members",
            members_response.success,
            members_response.error if not members_response.success else ""
        )
        
        if members_response.success:
            member_count = len(members_response.data.get('members', []))
            print(f"   👥 Retrieved {member_count} Senate members")
        
        # Test member details (try Cantwell)
        cantwell_response = client.get_member_details('C000127')
        result.add_test(
            "Get member details (Cantwell)",
            cantwell_response.success,
            cantwell_response.error if not cantwell_response.success else ""
        )
        
        if cantwell_response.success:
            member = cantwell_response.data.get('member', {})
            name = member.get('directOrderName', 'Unknown')
            print(f"   🔍 Member details: {name}")
        
        # Test committees
        committees_response = client.get_committees(limit=10)
        result.add_test(
            "Get committees",
            committees_response.success,
            committees_response.error if not committees_response.success else ""
        )
        
        if committees_response.success:
            committee_count = len(committees_response.data.get('committees', []))
            print(f"   🏛️  Retrieved {committee_count} committees")
        
        # Test comprehensive member data
        comprehensive_data = client.get_comprehensive_member_data('C000127')
        result.add_test(
            "Get comprehensive member data",
            comprehensive_data is not None,
            "Failed to get comprehensive data" if comprehensive_data is None else ""
        )
        
        if comprehensive_data:
            print(f"   📋 Comprehensive data includes: {list(comprehensive_data.keys())}")
    
    except Exception as e:
        result.add_test("API client initialization", False, str(e))
    
    print(f"   {result.summary()}")
    return result


def test_congress_sync():
    """Test Congress data synchronization."""
    print("\n🧪 Testing Congress Data Sync")
    result = TestResult()
    
    try:
        # Initialize sync
        sync = CongressDataSync()
        
        # Test API connection through sync
        connection_ok = sync.test_api_connection()
        result.add_test(
            "Sync API connection",
            connection_ok,
            "Failed to connect to Congress API" if not connection_ok else ""
        )
        
        if not connection_ok:
            print("   ⚠️  Skipping sync tests due to connection failure")
            print(f"   {result.summary()}")
            return result
        
        # Test sync status
        status = sync.get_sync_status()
        result.add_test(
            "Get sync status",
            status is not None and 'committees' in status,
            "Failed to get sync status" if status is None else ""
        )
        
        if status:
            print(f"   📊 API connection: {status['api_connection']}")
            print(f"   📊 Configured committees: {len(status['committees'])}")
        
        # Test single committee sync (Commerce)
        print("   🔄 Testing committee sync (Commerce)...")
        success, message = sync.sync_committee_members('commerce')
        result.add_test(
            "Sync Commerce committee",
            success,
            message
        )
        
        if success:
            # Verify the sync created data
            committee_file = Path('data/committees/commerce.json')
            result.add_test(
                "Commerce committee file created",
                committee_file.exists(),
                "Committee file not found after sync"
            )
            
            if committee_file.exists():
                import json
                with open(committee_file, 'r') as f:
                    data = json.load(f)
                
                member_count = len(data.get('members', []))
                api_sync_date = data.get('committee_info', {}).get('api_sync_date')
                
                result.add_test(
                    "Commerce committee has members",
                    member_count > 0,
                    f"Expected members, got {member_count}"
                )
                
                result.add_test(
                    "Sync metadata present",
                    api_sync_date is not None,
                    "Missing API sync timestamp"
                )
                
                print(f"   👥 Synced {member_count} Commerce committee members")
                print(f"   🕒 Last sync: {api_sync_date}")
        
        # Test alias update
        alias_success, alias_message = sync.update_member_aliases('commerce')
        result.add_test(
            "Update member aliases",
            alias_success,
            alias_message
        )
    
    except Exception as e:
        result.add_test("Congress sync initialization", False, str(e))
    
    print(f"   {result.summary()}")
    return result


def test_integration_workflow():
    """Test complete integration workflow."""
    print("\n🧪 Testing Integration Workflow")
    result = TestResult()
    
    try:
        # Test loading synced data through MetadataLoader
        from models.metadata_loader import MetadataLoader
        
        loader = MetadataLoader()
        
        # Load synced Commerce committee
        commerce_members = loader.load_committee_members('commerce')
        result.add_test(
            "Load synced Commerce members",
            len(commerce_members) > 0,
            f"Expected members, got {len(commerce_members)}"
        )
        
        if commerce_members:
            print(f"   👥 Loaded {len(commerce_members)} Commerce members")
            
            # Test speaker identification with synced data
            cantwell = loader.find_speaker_by_name("Chair Cantwell")
            result.add_test(
                "Identify Chair Cantwell (synced data)",
                cantwell is not None and hasattr(cantwell, 'member_id'),
                "Failed to identify Chair Cantwell from synced data"
            )
            
            if cantwell:
                print(f"   🔍 Identified: {cantwell.get_display_name()}")
        
        # Test that API-synced data works with transcript enrichment
        from enrichment.transcript_enricher import TranscriptEnricher
        
        enricher = TranscriptEnricher(loader)
        
        # Test speaker identification
        test_cases = [
            "Chair Cantwell",
            "Sen. Cruz",  
            "Ms. Klobuchar"
        ]
        
        identified_count = 0
        for name in test_cases:
            speaker = enricher.identify_speaker(name)
            if speaker and speaker.get('speaker_id'):
                identified_count += 1
        
        result.add_test(
            "Speaker identification with synced data",
            identified_count > 0,
            f"Identified {identified_count}/{len(test_cases)} speakers"
        )
        
        print(f"   🎯 Speaker identification: {identified_count}/{len(test_cases)} successful")
    
    except Exception as e:
        result.add_test("Integration workflow", False, str(e))
    
    print(f"   {result.summary()}")
    return result


def main():
    """Run all Congress API integration tests."""
    print("🚀 Congress API Integration Test Suite")
    print("=" * 50)
    
    # Configure logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run all test suites
    results = []
    results.append(test_api_client())
    results.append(test_congress_sync())
    results.append(test_integration_workflow())
    
    # Calculate overall results
    total_tests = sum(r.total for r in results)
    total_passed = sum(r.passed for r in results)
    total_failed = sum(r.failed for r in results)
    
    print("\n" + "=" * 50)
    print("📊 OVERALL RESULTS")
    print("=" * 50)
    
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if total_failed > 0:
        print("\n❌ FAILURES:")
        for result in results:
            for failure in result.failures:
                print(f"   • {failure}")
    
    print("\n🎯 CONGRESS API INTEGRATION STATUS")
    if success_rate >= 95:
        print("✅ Congress API integration fully operational")
    elif success_rate >= 80:
        print("⚠️  Congress API integration mostly functional, minor issues")
    else:
        print("❌ Congress API integration needs work")
    
    print("\n📋 NEXT STEPS")
    if success_rate >= 80:
        print("• Sync additional committees")
        print("• Set up automated daily sync")
        print("• Enhance committee role detection")
        print("• Add witness data from hearings API")
    else:
        print("• Verify API key and network connectivity")
        print("• Check API rate limits and quotas")
        print("• Review error logs for specific issues")
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())