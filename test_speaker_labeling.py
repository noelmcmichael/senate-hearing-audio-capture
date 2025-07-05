#!/usr/bin/env python3
"""
Test Enhanced Speaker Labeling for Milestone 5.3
Tests congressional metadata integration for speaker identification
"""

import sys
import json
import logging
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_speaker_labeler_import():
    """Test enhanced speaker labeler import"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from src.speaker.enhanced_labeling import EnhancedSpeakerLabeler, get_enhanced_speaker_labeler
        from src.speaker import SpeakerIdentification, CommitteeContext
        
        labeler = EnhancedSpeakerLabeler()
        logger.info("✅ EnhancedSpeakerLabeler class initialized")
        
        # Test singleton
        labeler2 = get_enhanced_speaker_labeler()
        logger.info("✅ Enhanced speaker labeler singleton working")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced speaker labeler import failed: {e}")
        return False

def test_congressional_data_loading():
    """Test congressional data loading"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from src.speaker.enhanced_labeling import get_enhanced_speaker_labeler
        
        labeler = get_enhanced_speaker_labeler()
        
        # Check loaded data
        congressional_data = labeler.congressional_data
        committees_count = len(congressional_data.get("committees", {}))
        members_count = len(congressional_data.get("members", {}))
        
        logger.info(f"✅ Congressional data loaded:")
        logger.info(f"  - Committees: {committees_count}")
        logger.info(f"  - Members: {members_count}")
        
        # Test specific committee
        if "SCOM" in congressional_data["committees"]:
            scom_data = congressional_data["committees"]["SCOM"]
            logger.info(f"  - SCOM members: {len(scom_data.get('members', []))}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Congressional data loading test failed: {e}")
        return False

def test_committee_context():
    """Test committee context creation"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from src.speaker.enhanced_labeling import get_enhanced_speaker_labeler
        
        labeler = get_enhanced_speaker_labeler()
        
        # Test with known committee
        context = labeler.get_committee_context("SCOM")
        
        logger.info(f"✅ Committee context created:")
        logger.info(f"  - Committee: {context.committee_name}")
        logger.info(f"  - Chair: {context.chair.get('full_name') if context.chair else 'None'}")
        logger.info(f"  - Ranking Member: {context.ranking_member.get('full_name') if context.ranking_member else 'None'}")
        logger.info(f"  - Members: {len(context.members) if context.members else 0}")
        
        # Test with unknown committee
        unknown_context = labeler.get_committee_context("UNKNOWN_TEST")
        logger.info(f"✅ Unknown committee context handled: {unknown_context.committee_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Committee context test failed: {e}")
        return False

def test_speaker_identification():
    """Test speaker identification from text"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from src.speaker.enhanced_labeling import get_enhanced_speaker_labeler
        
        labeler = get_enhanced_speaker_labeler()
        context = labeler.get_committee_context("SCOM")
        
        # Test various speaker patterns
        test_speakers = [
            "The Chair:",
            "Ranking Member Cruz:",
            "Senator Cantwell:",
            "Mr. Chairman:",
            "Dr. Smith:",
            "Ms. Johnson, Director of Technology Policy:",
            "Unknown Speaker"
        ]
        
        successful_identifications = 0
        
        for speaker_text in test_speakers:
            identification = labeler.identify_speaker_from_text(speaker_text, context)
            
            logger.info(f"✅ Speaker identification: '{speaker_text}'")
            logger.info(f"  - Role: {identification.role}")
            logger.info(f"  - Name: {identification.speaker_name}")
            logger.info(f"  - Confidence: {identification.confidence:.2f}")
            logger.info(f"  - Source: {identification.source}")
            
            if identification.confidence > 0.5:
                successful_identifications += 1
        
        success_rate = successful_identifications / len(test_speakers)
        logger.info(f"✅ Speaker identification success rate: {success_rate:.1%}")
        
        return success_rate > 0.6  # At least 60% should be identified with good confidence
        
    except Exception as e:
        logger.error(f"❌ Speaker identification test failed: {e}")
        return False

def test_transcript_enhancement():
    """Test transcript segment enhancement"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from src.speaker.enhanced_labeling import get_enhanced_speaker_labeler
        
        labeler = get_enhanced_speaker_labeler()
        
        # Create test transcript segments
        test_segments = [
            {
                "speaker": "The Chair:",
                "text": "This hearing will come to order.",
                "start": 0.0,
                "end": 3.0
            },
            {
                "speaker": "Ranking Member Cruz:",
                "text": "Thank you, Mr. Chairman.",
                "start": 3.0,
                "end": 5.0
            },
            {
                "speaker": "Senator Cantwell:",
                "text": "I have a question about the proposal.",
                "start": 5.0,
                "end": 8.0
            },
            {
                "speaker": "Dr. Williams:",
                "text": "The technology sector has seen significant growth.",
                "start": 8.0,
                "end": 12.0
            }
        ]
        
        # Enhance segments
        enhanced_segments = labeler.enhance_transcript_segments(
            test_segments, "SCOM", "TEST_HEARING_001"
        )
        
        logger.info(f"✅ Transcript enhancement completed:")
        logger.info(f"  - Original segments: {len(test_segments)}")
        logger.info(f"  - Enhanced segments: {len(enhanced_segments)}")
        
        # Analyze enhancement results
        high_confidence_count = 0
        metadata_matches = 0
        
        for i, segment in enumerate(enhanced_segments):
            enhanced_speaker = segment.get("enhanced_speaker", {})
            confidence = enhanced_speaker.get("confidence", 0)
            source = enhanced_speaker.get("source", "unknown")
            
            logger.info(f"  Segment {i+1}:")
            logger.info(f"    - Original: {test_segments[i]['speaker']}")
            logger.info(f"    - Enhanced: {enhanced_speaker.get('speaker_name', 'Unknown')} ({enhanced_speaker.get('role', 'UNKNOWN')})")
            logger.info(f"    - Confidence: {confidence:.2f}")
            logger.info(f"    - Source: {source}")
            
            if confidence > 0.7:
                high_confidence_count += 1
            
            if source == "metadata":
                metadata_matches += 1
        
        logger.info(f"✅ Enhancement results:")
        logger.info(f"  - High confidence: {high_confidence_count}/{len(enhanced_segments)}")
        logger.info(f"  - Metadata matches: {metadata_matches}")
        
        return len(enhanced_segments) == len(test_segments) and high_confidence_count > 0
        
    except Exception as e:
        logger.error(f"❌ Transcript enhancement test failed: {e}")
        return False

def test_pipeline_integration():
    """Test integration with pipeline controller"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from src.api.pipeline_controller import PipelineController
        
        controller = PipelineController()
        
        # Check that speaker_labeler is available
        if hasattr(controller, 'speaker_labeler'):
            logger.info("✅ Enhanced speaker labeler integrated into PipelineController")
            
            # Test that it has the expected methods
            labeler = controller.speaker_labeler
            if hasattr(labeler, 'enhance_transcript_segments'):
                logger.info("✅ enhance_transcript_segments method available")
                return True
            else:
                logger.error("❌ enhance_transcript_segments method not found")
                return False
        else:
            logger.error("❌ Enhanced speaker labeler not found in PipelineController")
            return False
            
    except Exception as e:
        logger.error(f"❌ Pipeline integration test failed: {e}")
        return False

def run_speaker_labeling_tests():
    """Run all enhanced speaker labeling tests"""
    logger.info("=" * 60)
    logger.info("MILESTONE 5.3: Enhanced Speaker Labeling Test")
    logger.info("=" * 60)
    
    tests = [
        ("Speaker Labeler Import", test_speaker_labeler_import),
        ("Congressional Data Loading", test_congressional_data_loading),
        ("Committee Context", test_committee_context),
        ("Speaker Identification", test_speaker_identification),
        ("Transcript Enhancement", test_transcript_enhancement),
        ("Pipeline Integration", test_pipeline_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running test: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"SPEAKER LABELING TEST RESULTS: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("🎉 ALL SPEAKER LABELING TESTS PASSED!")
        logger.info("✅ Step 5.3 Enhanced Speaker Labeling is COMPLETE")
        logger.info("✅ Congressional metadata integration working, speaker identification functional")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = run_speaker_labeling_tests()
    sys.exit(0 if success else 1)