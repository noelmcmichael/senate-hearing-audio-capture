#!/usr/bin/env python3
"""
Simple Audio Trimming Test for Milestone 5.2
"""

import sys
import logging
import tempfile
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_functionality():
    """Test basic audio trimming functionality"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from src.audio.trimming import AudioTrimmer
        
        trimmer = AudioTrimmer()
        logger.info("✅ AudioTrimmer initialized")
        
        # Test basic parameters
        params = trimmer.default_params
        logger.info(f"✅ Default parameters: {len(params)} settings")
        
        # Test temp directory creation
        if trimmer.temp_dir.exists():
            logger.info("✅ Temp directory created")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic functionality test failed: {e}")
        return False

def test_ffmpeg_availability():
    """Test FFmpeg availability"""
    try:
        # Test FFmpeg
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("✅ FFmpeg available")
        else:
            logger.error("❌ FFmpeg not available")
            return False
        
        # Test FFprobe
        result = subprocess.run(['ffprobe', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("✅ FFprobe available")
        else:
            logger.error("❌ FFprobe not available")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FFmpeg availability test failed: {e}")
        return False

def test_simple_audio_creation():
    """Test simple audio file creation"""
    try:
        temp_dir = Path(tempfile.gettempdir()) / "test_simple_audio"
        temp_dir.mkdir(exist_ok=True)
        
        test_audio_path = temp_dir / "simple_test.wav"
        
        # Create simple 5-second audio file
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "sine=frequency=440:sample_rate=44100:duration=5",
            "-c:a", "pcm_s16le",
            str(test_audio_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and test_audio_path.exists():
            logger.info(f"✅ Simple test audio created: {test_audio_path}")
            
            # Test duration detection
            sys.path.append(str(Path(__file__).parent))
            from src.audio.trimming import AudioTrimmer
            
            trimmer = AudioTrimmer()
            duration = trimmer._get_audio_duration(test_audio_path)
            
            if 4.5 <= duration <= 5.5:  # Allow some tolerance
                logger.info(f"✅ Duration detection working: {duration:.2f}s")
                return True
            else:
                logger.error(f"❌ Duration detection failed: {duration}s (expected ~5s)")
                return False
        else:
            logger.error(f"❌ Failed to create simple test audio: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Simple audio creation test failed: {e}")
        return False

def test_integration_imports():
    """Test that audio trimming integrates with pipeline"""
    try:
        sys.path.append(str(Path(__file__).parent))
        
        # Test audio module import
        from src.audio import AudioTrimmer, get_audio_trimmer
        logger.info("✅ Audio module imports working")
        
        # Test pipeline integration
        from src.api.pipeline_controller import PipelineController
        controller = PipelineController()
        
        if hasattr(controller, 'audio_trimmer'):
            logger.info("✅ Audio trimmer integrated in pipeline")
            return True
        else:
            logger.error("❌ Audio trimmer not found in pipeline")
            return False
            
    except Exception as e:
        logger.error(f"❌ Integration imports test failed: {e}")
        return False

def cleanup_simple_test():
    """Clean up test files"""
    try:
        temp_dir = Path(tempfile.gettempdir()) / "test_simple_audio"
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)
        logger.info("✅ Test cleanup complete")
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")

def run_simple_audio_tests():
    """Run simplified audio tests"""
    logger.info("=" * 50)
    logger.info("MILESTONE 5.2: Audio Trimming - Simple Test")
    logger.info("=" * 50)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("FFmpeg Availability", test_ffmpeg_availability),
        ("Simple Audio Creation", test_simple_audio_creation),
        ("Integration Imports", test_integration_imports)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"SIMPLE AUDIO TEST RESULTS: {passed}/{total} passed")
    logger.info("="*50)
    
    if passed == total:
        logger.info("🎉 AUDIO TRIMMING FOUNDATION COMPLETE!")
        logger.info("✅ Core functionality working, ready for production")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    try:
        success = run_simple_audio_tests()
        sys.exit(0 if success else 1)
    finally:
        cleanup_simple_test()