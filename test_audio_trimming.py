#!/usr/bin/env python3
"""
Test Audio Trimming for Milestone 5.2
Tests the audio trimming functionality with silence detection
"""

import sys
import os
import logging
import tempfile
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_audio():
    """Create a test audio file with silence at the beginning"""
    try:
        # Create a test audio file using FFmpeg
        # 5 seconds silence + 10 seconds tone + 2 seconds silence
        temp_dir = Path(tempfile.gettempdir()) / "test_audio_trimming"
        temp_dir.mkdir(exist_ok=True)
        
        test_audio_path = temp_dir / "test_hearing_audio.wav"
        
        # Generate test audio: 5s silence + 10s 440Hz tone + 2s silence
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "anullsrc=channel_layout=stereo:sample_rate=44100:d=5",
            "-f", "lavfi", 
            "-i", "sine=frequency=440:sample_rate=44100:duration=10",
            "-f", "lavfi",
            "-i", "anullsrc=channel_layout=stereo:sample_rate=44100:d=2",
            "-filter_complex", "[0:0][1:0][2:0]concat=n=3:v=0:a=1",
            "-c:a", "pcm_s16le",
            str(test_audio_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and test_audio_path.exists():
            logger.info(f"✅ Test audio created: {test_audio_path} ({test_audio_path.stat().st_size} bytes)")
            return test_audio_path
        else:
            logger.error(f"❌ Failed to create test audio: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Test audio creation failed: {e}")
        return None

def test_audio_trimmer_import():
    """Test AudioTrimmer import and initialization"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from src.audio.trimming import AudioTrimmer, get_audio_trimmer
        
        # Test class initialization
        trimmer = AudioTrimmer()
        logger.info("✅ AudioTrimmer class initialized")
        
        # Test singleton
        trimmer2 = get_audio_trimmer()
        logger.info("✅ AudioTrimmer singleton working")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ AudioTrimmer import failed: {e}")
        return False

def test_silence_detection():
    """Test silence detection functionality"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from src.audio.trimming import get_audio_trimmer
        
        # Create test audio
        test_audio_path = create_test_audio()
        if not test_audio_path:
            return False
        
        trimmer = get_audio_trimmer()
        
        # Run silence detection
        silence_analysis = trimmer.detect_silence_boundaries(test_audio_path)
        
        logger.info(f"✅ Silence detection completed:")
        logger.info(f"  - Duration: {silence_analysis['duration']:.1f}s")
        logger.info(f"  - Silence segments: {silence_analysis['silence_count']}")
        logger.info(f"  - Total silence: {silence_analysis['total_silence_duration']:.1f}s")
        logger.info(f"  - Recommended trim start: {silence_analysis['recommended_trim_start']:.1f}s")
        logger.info(f"  - Quality score: {silence_analysis['quality_score']:.1f}")
        
        # Validate results
        if silence_analysis["duration"] > 15 and silence_analysis["silence_count"] > 0:
            logger.info("✅ Silence detection results are reasonable")
            return True
        else:
            logger.error("❌ Silence detection results seem incorrect")
            return False
            
    except Exception as e:
        logger.error(f"❌ Silence detection test failed: {e}")
        return False

def test_audio_trimming():
    """Test audio trimming functionality"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from src.audio.trimming import get_audio_trimmer
        
        # Create test audio
        test_audio_path = create_test_audio()
        if not test_audio_path:
            return False
        
        trimmer = get_audio_trimmer()
        
        # Run trimming
        output_path = test_audio_path.parent / "test_hearing_audio_trimmed.mp3"
        trim_result = trimmer.trim_audio(test_audio_path, output_path, trim_start=5.0)
        
        logger.info(f"✅ Audio trimming completed:")
        logger.info(f"  - Original duration: {trim_result['original_duration']:.1f}s")
        logger.info(f"  - New duration: {trim_result['new_duration']:.1f}s")
        logger.info(f"  - Trimmed seconds: {trim_result['trimmed_seconds']:.1f}s")
        logger.info(f"  - Quality improvement: {trim_result['quality_improvement']:.1f}%")
        logger.info(f"  - File size reduction: {trim_result['file_size_reduction']:.1f}%")
        
        # Validate output file
        if output_path.exists() and trim_result["new_duration"] < trim_result["original_duration"]:
            logger.info("✅ Audio trimming results are valid")
            return True
        else:
            logger.error("❌ Audio trimming results invalid")
            return False
            
    except Exception as e:
        logger.error(f"❌ Audio trimming test failed: {e}")
        return False

def test_smart_trimming():
    """Test smart trimming with automatic detection"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from src.audio.trimming import get_audio_trimmer
        
        # Create test audio
        test_audio_path = create_test_audio()
        if not test_audio_path:
            return False
        
        trimmer = get_audio_trimmer()
        
        # Run smart trimming
        output_path = test_audio_path.parent / "test_hearing_audio_smart_trimmed.mp3"
        smart_result = trimmer.smart_trim(test_audio_path, output_path)
        
        analysis = smart_result["analysis"]
        trimming = smart_result["trimming"]
        optimization = smart_result["optimization"]
        
        logger.info(f"✅ Smart trimming completed:")
        logger.info(f"  Analysis - Silence segments: {analysis['silence_count']}")
        logger.info(f"  Analysis - Quality score: {analysis['quality_score']:.1f}")
        logger.info(f"  Trimming - Duration change: {trimming['original_duration']:.1f}s → {trimming['new_duration']:.1f}s")
        logger.info(f"  Optimization - Content improvement: {optimization['content_improvement']:.1f}%")
        logger.info(f"  Optimization - Transcription quality: +{optimization['transcription_quality_improvement']:.1f}%")
        
        # Validate smart trimming
        if (output_path.exists() and 
            trimming["new_duration"] < trimming["original_duration"] and
            optimization["content_improvement"] > 0):
            logger.info("✅ Smart trimming results are excellent")
            return True
        else:
            logger.error("❌ Smart trimming results invalid")
            return False
            
    except Exception as e:
        logger.error(f"❌ Smart trimming test failed: {e}")
        return False

def test_pipeline_integration():
    """Test integration with pipeline controller"""
    try:
        # Test that trimming can be imported in pipeline
        sys.path.append(str(Path(__file__).parent))
        from src.api.pipeline_controller import PipelineController
        
        controller = PipelineController()
        
        # Check that audio_trimmer is available
        if hasattr(controller, 'audio_trimmer'):
            logger.info("✅ AudioTrimmer integrated into PipelineController")
            return True
        else:
            logger.error("❌ AudioTrimmer not found in PipelineController")
            return False
            
    except Exception as e:
        logger.error(f"❌ Pipeline integration test failed: {e}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    try:
        temp_dir = Path(tempfile.gettempdir()) / "test_audio_trimming"
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)
        
        trimmer_temp_dir = Path(tempfile.gettempdir()) / "senate_audio_trimming"
        if trimmer_temp_dir.exists():
            import shutil
            shutil.rmtree(trimmer_temp_dir)
        
        logger.info("✅ Test files cleaned up")
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")

def run_audio_trimming_tests():
    """Run all audio trimming tests"""
    logger.info("=" * 60)
    logger.info("MILESTONE 5.2: Audio Trimming Implementation Test")
    logger.info("=" * 60)
    
    tests = [
        ("AudioTrimmer Import", test_audio_trimmer_import),
        ("Silence Detection", test_silence_detection),
        ("Audio Trimming", test_audio_trimming),
        ("Smart Trimming", test_smart_trimming),
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
    logger.info(f"AUDIO TRIMMING TEST RESULTS: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("🎉 ALL AUDIO TRIMMING TESTS PASSED!")
        logger.info("✅ Step 5.2 Audio Trimming Implementation is COMPLETE")
        logger.info("✅ Silence detection working, trimming functional, pipeline integrated")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    try:
        success = run_audio_trimming_tests()
        sys.exit(0 if success else 1)
    finally:
        cleanup_test_files()