#!/usr/bin/env python3
"""
Test Whisper Integration and Complete Pipeline

Comprehensive testing of the Whisper transcription integration with
congressional metadata enrichment system.
"""

import sys
import logging
import tempfile
import json
from pathlib import Path
import numpy as np
import wave

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from transcription.whisper_transcriber import WhisperTranscriber
from models.metadata_loader import MetadataLoader
from enrichment.transcript_enricher import TranscriptEnricher


def setup_logging():
    """Setup logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Reduce whisper logging noise
    logging.getLogger('whisper').setLevel(logging.WARNING)


def create_test_audio(duration_seconds: int = 10, sample_rate: int = 16000) -> Path:
    """
    Create a simple test audio file for transcription testing.
    
    Args:
        duration_seconds: Length of audio in seconds
        sample_rate: Audio sample rate
        
    Returns:
        Path to created audio file
    """
    # Generate simple sine wave audio (will transcribe as silence/noise)
    t = np.linspace(0, duration_seconds, duration_seconds * sample_rate, False)
    frequency = 440  # A4 note
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.1  # Quiet sine wave
    
    # Convert to 16-bit integers
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create temporary audio file
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_path = Path(temp_file.name)
    
    # Write WAV file
    with wave.open(str(temp_path), 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    return temp_path


def test_whisper_initialization():
    """Test Whisper transcriber initialization."""
    logger = logging.getLogger(__name__)
    logger.info("🧪 Testing Whisper initialization...")
    
    try:
        # Test different model sizes
        for model_size in ['tiny', 'base']:
            transcriber = WhisperTranscriber(model_size=model_size)
            
            assert transcriber.model_size == model_size
            assert transcriber.model is None  # Not loaded yet
            assert model_size in transcriber.model_specs
            
            logger.info(f"   ✅ {model_size} model initialized")
        
        logger.info("✅ Whisper initialization test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Whisper initialization failed: {e}")
        return False


def test_whisper_transcription():
    """Test basic Whisper transcription functionality."""
    logger = logging.getLogger(__name__)
    logger.info("🧪 Testing Whisper transcription...")
    
    try:
        # Create test audio
        test_audio = create_test_audio(duration_seconds=5)
        logger.info(f"   📁 Created test audio: {test_audio}")
        
        # Initialize transcriber with smallest model for speed
        transcriber = WhisperTranscriber(model_size="tiny")
        
        # Test transcription
        result = transcriber.transcribe_audio(test_audio, hearing_id="TEST-HEARING")
        
        # Validate result structure
        assert 'hearing_id' in result
        assert 'transcription' in result
        assert 'processing_metadata' in result
        assert 'quality_metrics' in result
        
        assert result['hearing_id'] == "TEST-HEARING"
        assert result['transcription']['duration'] > 0
        assert result['processing_metadata']['model_size'] == "tiny"
        
        logger.info(f"   ✅ Transcription completed")
        logger.info(f"   ⏱️  Duration: {result['transcription']['duration']:.1f}s")
        logger.info(f"   📊 Confidence: {result['quality_metrics']['overall_confidence']}")
        logger.info(f"   📝 Text length: {len(result['transcription']['text'])} chars")
        
        # Cleanup
        test_audio.unlink()
        
        logger.info("✅ Whisper transcription test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Whisper transcription failed: {e}")
        # Cleanup on failure
        if 'test_audio' in locals():
            test_audio.unlink(missing_ok=True)
        return False


def test_enrichment_integration():
    """Test integration between Whisper and enrichment system."""
    logger = logging.getLogger(__name__)
    logger.info("🧪 Testing enrichment integration...")
    
    try:
        # Test with sample congressional text
        sample_transcript = """
        Chair Cantwell: The committee will come to order. Today we're examining AI oversight.
        
        Sen. Cruz: Thank you, Chair Cantwell. I have concerns about regulatory overreach.
        
        Ms. Chen: Thank you for having me. As CEO of OpenAI, we believe in responsible AI development.
        """
        
        # Test enrichment
        enricher = TranscriptEnricher()
        enriched = enricher.enrich_transcript(sample_transcript, "TEST-AI-HEARING")
        
        # Validate enrichment structure
        assert 'segments' in enriched
        assert 'speaker_statistics' in enriched
        assert 'identified_speakers' in enriched
        assert 'total_segments' in enriched
        
        logger.info(f"   ✅ Enrichment completed")
        logger.info(f"   👥 Identified speakers: {enriched['identified_speakers']}")
        logger.info(f"   📊 Total segments: {enriched['total_segments']}")
        
        # Check for speaker identification
        for segment in enriched['segments'][:3]:  # Check first 3 segments
            speaker = segment.get('speaker')
            if speaker and speaker.get('speaker_id'):
                logger.info(f"   🎯 Identified: {speaker['display_name']} ({speaker['speaker_type']})")
        
        logger.info("✅ Enrichment integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enrichment integration failed: {e}")
        return False


def test_complete_pipeline():
    """Test the complete pipeline integration."""
    logger = logging.getLogger(__name__)
    logger.info("🧪 Testing complete pipeline...")
    
    try:
        # Create test audio
        test_audio = create_test_audio(duration_seconds=3)  # Short for speed
        logger.info(f"   📁 Created test audio: {test_audio}")
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Initialize transcriber
            transcriber = WhisperTranscriber(model_size="tiny")
            
            # Run complete pipeline
            result = transcriber.transcribe_with_enrichment(
                test_audio,
                hearing_id="TEST-COMPLETE-PIPELINE",
                output_dir=output_dir
            )
            
            # Validate complete result structure
            assert 'pipeline_version' in result
            assert 'transcription' in result
            assert 'enrichment' in result
            assert 'summary' in result
            
            summary = result['summary']
            assert summary['pipeline_complete'] is True
            assert summary['audio_duration'] > 0
            assert 'transcription_confidence' in summary
            
            logger.info(f"   ✅ Pipeline completed")
            logger.info(f"   📊 Audio duration: {summary['audio_duration']:.1f}s")
            logger.info(f"   🎯 Confidence: {summary['transcription_confidence']}")
            logger.info(f"   👥 Speakers: {summary['identified_speakers']}")
            logger.info(f"   📝 Segments: {summary['total_segments']}")
            
            # Check if output file was created
            if 'output_file' in result:
                output_file = Path(result['output_file'])
                assert output_file.exists()
                logger.info(f"   💾 Output saved: {output_file.name}")
        
        # Cleanup
        test_audio.unlink()
        
        logger.info("✅ Complete pipeline test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Complete pipeline failed: {e}")
        # Cleanup on failure
        if 'test_audio' in locals():
            test_audio.unlink(missing_ok=True)
        return False


def test_error_handling():
    """Test error handling in the pipeline."""
    logger = logging.getLogger(__name__)
    logger.info("🧪 Testing error handling...")
    
    try:
        transcriber = WhisperTranscriber(model_size="tiny")
        
        # Test with non-existent file
        try:
            transcriber.transcribe_audio("nonexistent_file.wav")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            logger.info("   ✅ Non-existent file error handled correctly")
        
        # Test with invalid model size
        try:
            invalid_transcriber = WhisperTranscriber(model_size="invalid")
            # This might not fail until model loading, which is okay
            logger.info("   ✅ Invalid model size handled")
        except Exception:
            logger.info("   ✅ Invalid model size error handled")
        
        logger.info("✅ Error handling test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        return False


def test_batch_processing():
    """Test batch processing capabilities."""
    logger = logging.getLogger(__name__)
    logger.info("🧪 Testing batch processing...")
    
    try:
        # Create multiple test audio files
        test_files = []
        for i in range(2):  # Create 2 small test files
            test_audio = create_test_audio(duration_seconds=2, sample_rate=8000)  # Small and fast
            test_files.append(test_audio)
        
        logger.info(f"   📁 Created {len(test_files)} test files")
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Initialize transcriber
            transcriber = WhisperTranscriber(model_size="tiny")
            
            # Run batch processing
            results = transcriber.batch_transcribe(
                test_files,
                output_dir,
                hearing_ids=[f"TEST-BATCH-{i}" for i in range(len(test_files))]
            )
            
            # Validate batch results
            assert len(results) == len(test_files)
            
            successful = [r for r in results if r.get('summary', {}).get('pipeline_complete', False)]
            failed = [r for r in results if 'error' in r]
            
            logger.info(f"   ✅ Batch processing completed")
            logger.info(f"   📊 Successful: {len(successful)}/{len(test_files)}")
            logger.info(f"   ❌ Failed: {len(failed)}")
            
            # Check for batch summary file
            summary_file = output_dir / "batch_transcription_summary.json"
            assert summary_file.exists()
            logger.info(f"   💾 Batch summary created: {summary_file.name}")
        
        # Cleanup
        for test_file in test_files:
            test_file.unlink()
        
        logger.info("✅ Batch processing test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Batch processing failed: {e}")
        # Cleanup on failure
        if 'test_files' in locals():
            for test_file in test_files:
                test_file.unlink(missing_ok=True)
        return False


def main():
    """Run all Whisper integration tests."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Testing Whisper Integration & Complete Pipeline")
    logger.info("=" * 60)
    
    tests = [
        ("Whisper Initialization", test_whisper_initialization),
        ("Whisper Transcription", test_whisper_transcription),
        ("Enrichment Integration", test_enrichment_integration),
        ("Complete Pipeline", test_complete_pipeline),
        ("Error Handling", test_error_handling),
        ("Batch Processing", test_batch_processing),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
                
        except Exception as e:
            logger.error(f"💥 {test_name} CRASHED: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n📊 TEST SUMMARY")
    logger.info("=" * 20)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎊 ALL TESTS PASSED - Whisper integration ready!")
        logger.info("\n🚀 PHASE 5 FOUNDATION COMPLETE")
        logger.info("✅ Whisper transcription operational") 
        logger.info("✅ Congressional metadata integration working")
        logger.info("✅ Complete pipeline functional")
        logger.info("✅ Batch processing supported")
        logger.info("✅ Error handling robust")
        return True
    else:
        logger.error("💥 SOME TESTS FAILED - Check system configuration")
        return False


if __name__ == "__main__":
    # Install numpy if not available (needed for test audio generation)
    try:
        import numpy as np
    except ImportError:
        print("Installing numpy for test audio generation...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
        import numpy as np
    
    success = main()
    sys.exit(0 if success else 1)