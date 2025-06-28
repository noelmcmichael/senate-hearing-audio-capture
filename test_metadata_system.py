#!/usr/bin/env python3
"""
Phase 3 Metadata System Test Suite

Tests the congressional metadata foundation layer for speaker identification
and transcript enrichment capabilities.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from models.metadata_loader import MetadataLoader
from models.committee_member import CommitteeMember
from models.hearing_witness import HearingWitness
from models.hearing import Hearing


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


def test_committee_member_model():
    """Test CommitteeMember model functionality."""
    print("\n🧪 Testing CommitteeMember Model")
    result = TestResult()
    
    # Test creation and serialization
    member = CommitteeMember(
        member_id="SEN_TEST",
        full_name="Test Senator",
        title="Senator",
        party="D",
        state="TX",
        chamber="Senate",
        committee="Commerce",
        role="Chair",
        aliases=["Chair Test", "Sen. Test"]
    )
    
    # Test serialization/deserialization
    json_str = member.to_json()
    member_restored = CommitteeMember.from_json(json_str)
    result.add_test(
        "Member JSON serialization",
        member.member_id == member_restored.member_id,
        "JSON round-trip failed"
    )
    
    # Test name matching
    result.add_test(
        "Member name matching - full name",
        member.matches_name("Test Senator"),
        "Should match full name"
    )
    
    result.add_test(
        "Member name matching - alias",
        member.matches_name("Chair Test"),
        "Should match alias"
    )
    
    result.add_test(
        "Member name matching - partial",
        member.matches_name("Sen. Test"),
        "Should match partial alias"
    )
    
    result.add_test(
        "Member name matching - negative",
        not member.matches_name("Random Name"),
        "Should not match unrelated name"
    )
    
    # Test display name
    display_name = member.get_display_name()
    result.add_test(
        "Member display name format",
        "Chair Test Senator (D-TX)" in display_name,
        f"Unexpected display format: {display_name}"
    )
    
    print(f"   {result.summary()}")
    return result


def test_hearing_witness_model():
    """Test HearingWitness model functionality."""
    print("\n🧪 Testing HearingWitness Model")
    result = TestResult()
    
    # Test creation
    witness = HearingWitness(
        witness_id="WTN_TEST",
        full_name="Dr. Test Witness",
        title="Chief Scientist",
        organization="Test Corp",
        hearing_title="Test Hearing",
        committee="Senate Commerce",
        hearing_date="2025-06-10",
        aliases=["Dr. Witness", "Test Witness"]
    )
    
    # Test serialization
    json_str = witness.to_json()
    witness_restored = HearingWitness.from_json(json_str)
    result.add_test(
        "Witness JSON serialization",
        witness.witness_id == witness_restored.witness_id,
        "JSON round-trip failed"
    )
    
    # Test name matching
    result.add_test(
        "Witness name matching - full name",
        witness.matches_name("Dr. Test Witness"),
        "Should match full name"
    )
    
    result.add_test(
        "Witness name matching - alias",
        witness.matches_name("Dr. Witness"),
        "Should match alias"
    )
    
    # Test display names
    display_name = witness.get_display_name()
    result.add_test(
        "Witness display name format",
        "Dr. Test Witness, Chief Scientist, Test Corp" == display_name,
        f"Unexpected display format: {display_name}"
    )
    
    short_name = witness.get_short_display_name()
    result.add_test(
        "Witness short display name",
        "Dr. Test Witness (Test Corp)" == short_name,
        f"Unexpected short format: {short_name}"
    )
    
    print(f"   {result.summary()}")
    return result


def test_hearing_model():
    """Test Hearing model functionality."""
    print("\n🧪 Testing Hearing Model")
    result = TestResult()
    
    # Test creation
    hearing = Hearing(
        hearing_id="TEST-2025-06-10-SAMPLE",
        title="Test Hearing",
        committee="Senate Commerce",
        date="2025-06-10",
        members_present=["SEN_TEST1", "SEN_TEST2"],
        witnesses=["WTN_TEST1"]
    )
    
    # Test serialization
    json_str = hearing.to_json()
    hearing_restored = Hearing.from_json(json_str)
    result.add_test(
        "Hearing JSON serialization",
        hearing.hearing_id == hearing_restored.hearing_id,
        "JSON round-trip failed"
    )
    
    # Test status management
    hearing.update_status("captured")
    result.add_test(
        "Hearing status update",
        hearing.status == "captured",
        "Status update failed"
    )
    
    # Test invalid status
    try:
        hearing.update_status("invalid_status")
        result.add_test("Hearing invalid status", False, "Should reject invalid status")
    except ValueError:
        result.add_test("Hearing invalid status", True)
    
    # Test participant addition
    hearing.add_participant("SEN_TEST3", "member")
    result.add_test(
        "Add hearing member",
        "SEN_TEST3" in hearing.members_present,
        "Member not added"
    )
    
    hearing.add_participant("WTN_TEST2", "witness")
    result.add_test(
        "Add hearing witness",
        "WTN_TEST2" in hearing.witnesses,
        "Witness not added"
    )
    
    # Test file safe ID
    file_safe_id = hearing.get_file_safe_id()
    result.add_test(
        "File safe ID generation",
        "/" not in file_safe_id and " " not in file_safe_id,
        f"File safe ID contains invalid chars: {file_safe_id}"
    )
    
    print(f"   {result.summary()}")
    return result


def test_metadata_loader():
    """Test MetadataLoader functionality."""
    print("\n🧪 Testing MetadataLoader")
    result = TestResult()
    
    # Initialize loader
    loader = MetadataLoader()
    
    # Test committee loading
    commerce_members = loader.load_committee_members("Commerce")
    result.add_test(
        "Load Commerce committee members",
        len(commerce_members) > 0,
        f"Expected members, got {len(commerce_members)}"
    )
    
    # Test specific member loading
    cantwell = loader.load_member("SEN_CANTWELL")
    result.add_test(
        "Load specific member (Cantwell)",
        cantwell is not None and cantwell.full_name == "Maria Cantwell",
        "Failed to load Sen. Cantwell"
    )
    
    # Test member not found
    nonexistent = loader.load_member("SEN_NONEXISTENT")
    result.add_test(
        "Handle nonexistent member",
        nonexistent is None,
        "Should return None for nonexistent member"
    )
    
    # Test House committee loading
    house_members = loader.load_committee_members("House Judiciary")
    result.add_test(
        "Load House Judiciary committee members",
        len(house_members) > 0,
        f"Expected House members, got {len(house_members)}"
    )
    
    # Test hearing loading
    hearing = loader.load_hearing("SCOM-2025-06-10-AI-OVERSIGHT")
    result.add_test(
        "Load sample hearing",
        hearing is not None and hearing.title.startswith("Oversight of Artificial Intelligence"),
        "Failed to load sample hearing"
    )
    
    # Test witness loading
    if hearing:
        witnesses = loader.load_hearing_witnesses(hearing.hearing_id)
        result.add_test(
            "Load hearing witnesses",
            len(witnesses) > 0,
            f"Expected witnesses, got {len(witnesses)}"
        )
    
    # Test speaker search
    speaker = loader.find_speaker_by_name("Chair Cantwell")
    result.add_test(
        "Find speaker by name",
        speaker is not None and hasattr(speaker, 'member_id'),
        "Failed to find speaker by name"
    )
    
    # Test committee roster
    roster = loader.get_committee_roster("Commerce")
    result.add_test(
        "Get committee roster",
        len(roster) > 0 and any("Cantwell" in name for name in roster.keys()),
        "Failed to generate committee roster"
    )
    
    print(f"   {result.summary()}")
    return result


def test_speaker_identification():
    """Test speaker identification scenarios."""
    print("\n🧪 Testing Speaker Identification")
    result = TestResult()
    
    loader = MetadataLoader()
    
    # Test various name formats for identification
    test_cases = [
        ("Chair Cantwell", "SEN_CANTWELL"),
        ("Sen. Cruz", "SEN_CRUZ"),
        ("Ms. Klobuchar", "SEN_KLOBUCHAR"),
        ("The Chair", "SEN_CANTWELL"),
        ("Ranking Member Cruz", "SEN_CRUZ")
    ]
    
    for name, expected_id in test_cases:
        speaker = loader.find_speaker_by_name(name)
        if speaker and hasattr(speaker, 'member_id'):
            result.add_test(
                f"Identify '{name}'",
                speaker.member_id == expected_id,
                f"Expected {expected_id}, got {speaker.member_id}"
            )
        else:
            result.add_test(
                f"Identify '{name}'",
                False,
                "Speaker not found"
            )
    
    # Test witness identification
    witness = loader.find_speaker_by_name("Dr. Williams", "SCOM-2025-06-10-AI-OVERSIGHT")
    result.add_test(
        "Identify witness in hearing context",
        witness is not None and hasattr(witness, 'witness_id'),
        "Failed to identify witness in hearing context"
    )
    
    print(f"   {result.summary()}")
    return result


def test_integration_workflow():
    """Test complete integration workflow."""
    print("\n🧪 Testing Integration Workflow")
    result = TestResult()
    
    loader = MetadataLoader()
    
    # Load a hearing with all context
    hearing = loader.load_hearing("SCOM-2025-06-10-AI-OVERSIGHT")
    
    if hearing:
        # Get all members present
        members_present = []
        for member_id in hearing.members_present:
            member = loader.load_member(member_id)
            if member:
                members_present.append(member)
        
        result.add_test(
            "Load all hearing members",
            len(members_present) == len(hearing.members_present),
            f"Expected {len(hearing.members_present)}, got {len(members_present)}"
        )
        
        # Get all witnesses
        witnesses = loader.load_hearing_witnesses(hearing.hearing_id)
        result.add_test(
            "Load all hearing witnesses",
            len(witnesses) == len(hearing.witnesses),
            f"Expected {len(hearing.witnesses)}, got {len(witnesses)}"
        )
        
        # Test complete context availability
        total_speakers = len(members_present) + len(witnesses)
        result.add_test(
            "Complete speaker context",
            total_speakers > 0,
            f"Expected speakers, got {total_speakers}"
        )
        
        # Simulate transcript enrichment scenario
        sample_names = ["Chair Cantwell", "Commissioner Rodriguez", "Dr. Williams"]
        identified_count = 0
        
        for name in sample_names:
            speaker = loader.find_speaker_by_name(name, hearing.hearing_id)
            if speaker:
                identified_count += 1
        
        result.add_test(
            "Transcript enrichment simulation",
            identified_count == len(sample_names),
            f"Identified {identified_count}/{len(sample_names)} speakers"
        )
    else:
        result.add_test("Load sample hearing", False, "Could not load hearing for integration test")
    
    print(f"   {result.summary()}")
    return result


def main():
    """Run all metadata system tests."""
    print("🚀 Phase 3 Metadata System Test Suite")
    print("=" * 50)
    
    # Configure logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run all test suites
    results = []
    results.append(test_committee_member_model())
    results.append(test_hearing_witness_model())
    results.append(test_hearing_model())
    results.append(test_metadata_loader())
    results.append(test_speaker_identification())
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
    
    print("\n🎯 METADATA SYSTEM STATUS")
    if success_rate >= 95:
        print("✅ Foundation layer ready for transcription integration")
    elif success_rate >= 80:
        print("⚠️  Foundation layer mostly functional, minor issues to address")
    else:
        print("❌ Foundation layer needs significant work before transcription")
    
    print("\n📋 NEXT STEPS")
    print("• Add more committee rosters as needed")
    print("• Populate witness data from actual hearings")
    print("• Integrate with transcription workflow")
    print("• Enhance dashboard with metadata filtering")
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())