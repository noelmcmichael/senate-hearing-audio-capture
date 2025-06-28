#!/usr/bin/env python3
"""
Committee Expansion Verification Test

Tests the expanded Congress.gov API integration across all priority committees.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from models.metadata_loader import MetadataLoader
from models.congress_sync import CongressDataSync
from enrichment.transcript_enricher import TranscriptEnricher


def test_committee_expansion():
    """Test expanded committee coverage and functionality."""
    print("🏛️ COMMITTEE EXPANSION VERIFICATION")
    print("=" * 60)
    
    # Initialize systems
    loader = MetadataLoader()
    sync_system = CongressDataSync()
    enricher = TranscriptEnricher(loader)
    
    # Test expanded committee coverage
    print("\n📊 COMMITTEE COVERAGE ANALYSIS")
    print("-" * 40)
    
    priority_committees = sync_system.get_priority_committees(isvp_only=True)
    total_members = 0
    successful_committees = 0
    
    for committee_key in priority_committees:
        committee_info = sync_system.committee_mappings[committee_key]
        try:
            members = loader.load_committee_members(committee_key)
            if members:
                print(f"✅ {committee_info['official_name']}")
                print(f"   🔗 System Code: {committee_info['system_code']}")
                print(f"   👥 Members: {len(members)}")
                print(f"   🎯 Priority: {committee_info['priority']}")
                total_members += len(members)
                successful_committees += 1
            else:
                print(f"❌ {committee_info['official_name']}: No members loaded")
        except Exception as e:
            print(f"❌ {committee_info['official_name']}: Error - {e}")
    
    print(f"\n📈 COVERAGE SUMMARY")
    print(f"Successful Committees: {successful_committees}/{len(priority_committees)}")
    print(f"Total Members: {total_members}")
    print(f"Average Members per Committee: {total_members/successful_committees:.1f}" if successful_committees > 0 else "N/A")
    
    # Test speaker identification across committees
    print(f"\n🧪 CROSS-COMMITTEE SPEAKER IDENTIFICATION")
    print("-" * 40)
    
    test_cases = [
        ("Sen. Hawley", "Should identify Josh Hawley"),
        ("Senator Sheehy", "Should identify Tim Sheehy"),
        ("Sen. Lujan", "Should identify Ben Ray Luján"),
        ("Chairman", "Should identify as Chairman"),
        ("Ranking Member", "Should identify role"),
        ("Sen. Warren", "Should identify if present"),
        ("Sen. Cruz", "Should identify if present"),
        ("Unknown Speaker", "Should not identify")
    ]
    
    identified_count = 0
    for speaker, description in test_cases:
        identified = enricher.identify_speaker(speaker)
        if identified:
            display_name = identified.get('display_name', 'Unknown')
            print(f"✅ '{speaker}' → {display_name}")
            identified_count += 1
        else:
            print(f"❌ '{speaker}' → Not identified")
    
    identification_rate = (identified_count / len(test_cases)) * 100
    print(f"\nSpeaker Identification Rate: {identification_rate:.1f}% ({identified_count}/{len(test_cases)})")
    
    # Test data quality
    print(f"\n🔍 DATA QUALITY ANALYSIS")
    print("-" * 40)
    
    quality_issues = 0
    total_checks = 0
    
    for committee_key in priority_committees:
        committee_info = sync_system.committee_mappings[committee_key]
        try:
            members = loader.load_committee_members(committee_key)
            if not members:
                continue
                
            print(f"\n{committee_info['official_name']}:")
            
            # Check data completeness
            for member in members[:3]:  # Check first 3 members
                total_checks += 1
                issues = []
                
                if not member.full_name or member.full_name == 'Unknown':
                    issues.append("Missing name")
                if not member.party:
                    issues.append("Missing party")
                if not member.state:
                    issues.append("Missing state")
                if not member.aliases or len(member.aliases) < 2:
                    issues.append("Insufficient aliases")
                
                if issues:
                    quality_issues += len(issues)
                    print(f"  ⚠️  {member.full_name}: {', '.join(issues)}")
                else:
                    print(f"  ✅ {member.full_name}: Complete data")
                    
        except Exception as e:
            print(f"  ❌ Error checking {committee_key}: {e}")
    
    data_quality = ((total_checks * 4 - quality_issues) / (total_checks * 4)) * 100 if total_checks > 0 else 0
    print(f"\nData Quality Score: {data_quality:.1f}%")
    
    # Test API sync status
    print(f"\n📡 API SYNC STATUS")
    print("-" * 40)
    
    sync_status = sync_system.get_sync_status()
    api_connection = sync_status.get('api_connection', False)
    
    print(f"API Connection: {'✅ Active' if api_connection else '❌ Failed'}")
    
    synced_committees = 0
    for committee_key, committee_status in sync_status.get('committees', {}).items():
        if committee_status.get('exists') and not committee_status.get('error'):
            synced_committees += 1
    
    print(f"Synced Committees: {synced_committees}/{len(sync_status.get('committees', {}))}")
    
    # Overall assessment
    print(f"\n🎯 EXPANSION SUCCESS ASSESSMENT")
    print("=" * 60)
    
    success_criteria = [
        (successful_committees >= 4, f"✅ All 4 priority committees synced" if successful_committees >= 4 else f"❌ Only {successful_committees}/4 committees synced"),
        (total_members >= 80, f"✅ Sufficient member coverage ({total_members} members)" if total_members >= 80 else f"❌ Insufficient members ({total_members} < 80)"),
        (identification_rate >= 60, f"✅ Good speaker identification ({identification_rate:.1f}%)" if identification_rate >= 60 else f"❌ Poor speaker identification ({identification_rate:.1f}%)"),
        (data_quality >= 80, f"✅ High data quality ({data_quality:.1f}%)" if data_quality >= 80 else f"❌ Low data quality ({data_quality:.1f}%)"),
        (api_connection, "✅ API connection working" if api_connection else "❌ API connection failed")
    ]
    
    passed_criteria = sum(1 for passed, _ in success_criteria if passed)
    
    for passed, message in success_criteria:
        print(message)
    
    overall_success = passed_criteria >= 4
    print(f"\n{'🎉 COMMITTEE EXPANSION SUCCESSFUL!' if overall_success else '⚠️  COMMITTEE EXPANSION NEEDS ATTENTION'}")
    print(f"Success Rate: {(passed_criteria/len(success_criteria)*100):.1f}% ({passed_criteria}/{len(success_criteria)} criteria met)")
    
    return overall_success


if __name__ == "__main__":
    success = test_committee_expansion()
    exit(0 if success else 1)