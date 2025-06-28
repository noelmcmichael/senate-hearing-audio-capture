#!/usr/bin/env python3
"""
Phase 5: Complete Transcription Pipeline

Demonstrates the complete workflow:
Audio Capture → Whisper Transcription → Speaker Identification → Context Enrichment
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from transcription.whisper_transcriber import WhisperTranscriber
from models.metadata_loader import MetadataLoader
from enrichment.transcript_enricher import TranscriptEnricher


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Reduce whisper logging noise
    logging.getLogger('whisper').setLevel(logging.WARNING)


def find_audio_files(directory: Path) -> list:
    """Find audio files in directory."""
    audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
    audio_files = []
    
    for ext in audio_extensions:
        audio_files.extend(directory.glob(f"*{ext}"))
        audio_files.extend(directory.glob(f"**/*{ext}"))
    
    return sorted(audio_files)


def main():
    """Run the complete transcription pipeline."""
    parser = argparse.ArgumentParser(
        description="Complete transcription pipeline for congressional hearings"
    )
    
    parser.add_argument(
        '--audio', 
        type=str, 
        help='Path to audio file or directory containing audio files'
    )
    
    parser.add_argument(
        '--hearing-id', 
        type=str, 
        help='Hearing ID for congressional metadata context'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        default='./output/transcriptions',
        help='Output directory for transcription results'
    )
    
    parser.add_argument(
        '--model', 
        type=str, 
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        default='base',
        help='Whisper model size (default: base)'
    )
    
    parser.add_argument(
        '--batch', 
        action='store_true',
        help='Process all audio files in directory (batch mode)'
    )
    
    parser.add_argument(
        '--demo', 
        action='store_true',
        help='Run demonstration with sample data'
    )
    
    parser.add_argument(
        '--test-system', 
        action='store_true',
        help='Test system components without processing audio'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Phase 5: Complete Transcription Pipeline")
    logger.info("=" * 50)
    
    # Test system components
    if args.test_system:
        test_system_components()
        return
    
    # Demo mode
    if args.demo:
        run_demo()
        return
    
    # Validate arguments
    if not args.audio:
        logger.error("❌ --audio argument required (or use --demo/--test-system)")
        sys.exit(1)
    
    audio_path = Path(args.audio)
    if not audio_path.exists():
        logger.error(f"❌ Audio path not found: {audio_path}")
        sys.exit(1)
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize transcriber
    logger.info(f"🔧 Initializing Whisper transcriber (model: {args.model})...")
    transcriber = WhisperTranscriber(model_size=args.model)
    
    try:
        if audio_path.is_file():
            # Single file processing
            logger.info(f"📄 Processing single file: {audio_path}")
            result = transcriber.transcribe_with_enrichment(
                audio_path, 
                hearing_id=args.hearing_id,
                output_dir=output_dir
            )
            
            logger.info("✅ Transcription pipeline completed successfully")
            display_results_summary(result)
            
        elif audio_path.is_dir() and args.batch:
            # Batch processing
            logger.info(f"📁 Processing directory: {audio_path}")
            audio_files = find_audio_files(audio_path)
            
            if not audio_files:
                logger.error(f"❌ No audio files found in: {audio_path}")
                sys.exit(1)
            
            logger.info(f"📋 Found {len(audio_files)} audio files")
            results = transcriber.batch_transcribe(audio_files, output_dir)
            
            logger.info("✅ Batch transcription completed")
            display_batch_summary(results)
            
        else:
            logger.error("❌ Invalid arguments. Use --batch for directory processing.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def test_system_components():
    """Test all system components without processing audio."""
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 Testing system components...")
    
    # Test 1: Metadata loader
    logger.info("1️⃣  Testing metadata loader...")
    try:
        metadata_loader = MetadataLoader()
        committees = ['commerce', 'intelligence', 'banking', 'judiciary_senate']
        
        for committee in committees:
            members = metadata_loader.load_committee_members(committee)
            logger.info(f"   ✅ {committee}: {len(members)} members loaded")
        
    except Exception as e:
        logger.error(f"   ❌ Metadata loader failed: {e}")
        return False
    
    # Test 2: Transcript enricher  
    logger.info("2️⃣  Testing transcript enricher...")
    try:
        enricher = TranscriptEnricher()
        test_text = "Chair Cantwell: The committee will come to order."
        speaker = enricher.identify_speaker("Chair Cantwell")
        
        if speaker and speaker.get('speaker_id'):
            logger.info(f"   ✅ Speaker identification: {speaker['display_name']}")
        else:
            logger.info("   ⚠️  Speaker not identified (expected if metadata not synced)")
        
    except Exception as e:
        logger.error(f"   ❌ Transcript enricher failed: {e}")
        return False
    
    # Test 3: Whisper transcriber initialization
    logger.info("3️⃣  Testing Whisper transcriber...")
    try:
        transcriber = WhisperTranscriber(model_size="tiny")  # Use smallest model for testing
        # Don't load model yet, just test initialization
        logger.info(f"   ✅ Transcriber initialized (model: {transcriber.model_size})")
        
    except Exception as e:
        logger.error(f"   ❌ Transcriber initialization failed: {e}")
        return False
    
    logger.info("✅ All system components operational")
    return True


def run_demo():
    """Run demonstration with sample data."""
    logger = logging.getLogger(__name__)
    
    logger.info("🎭 Running demonstration mode...")
    
    # Check if we have any sample audio files
    output_dir = Path('./output')
    audio_files = []
    
    if output_dir.exists():
        audio_files = find_audio_files(output_dir)
    
    if audio_files:
        logger.info(f"📁 Found {len(audio_files)} audio files in output directory")
        
        # Use the first audio file for demo
        demo_audio = audio_files[0]
        logger.info(f"🎵 Using demo audio: {demo_audio}")
        
        # Run transcription pipeline
        transcriber = WhisperTranscriber(model_size="base")
        result = transcriber.transcribe_with_enrichment(
            demo_audio,
            hearing_id="DEMO-HEARING",
            output_dir=Path('./output/demo_transcription')
        )
        
        display_results_summary(result)
        
    else:
        logger.info("📝 No audio files found - demonstrating system components...")
        
        # Test system components instead
        if test_system_components():
            logger.info("🎊 Demo completed - system ready for transcription")
        else:
            logger.error("❌ Demo failed - check system configuration")


def display_results_summary(result: dict):
    """Display transcription results summary."""
    logger = logging.getLogger(__name__)
    
    summary = result.get('summary', {})
    transcription = result.get('transcription', {})
    enrichment = result.get('enrichment', {})
    
    logger.info("\n📊 TRANSCRIPTION RESULTS")
    logger.info("=" * 30)
    logger.info(f"Audio Duration: {summary.get('audio_duration', 0):.1f}s")
    logger.info(f"Confidence: {summary.get('transcription_confidence', 'unknown')}")
    logger.info(f"Speakers Identified: {summary.get('identified_speakers', 0)}")
    logger.info(f"Total Segments: {summary.get('total_segments', 0)}")
    
    # Show quality metrics
    quality = transcription.get('transcription', {}).get('quality_metrics', {})
    if quality:
        logger.info(f"High Confidence Segments: {quality.get('metrics', {}).get('high_confidence_segments', 0)}")
        logger.info(f"Potential Speaker Changes: {quality.get('metrics', {}).get('potential_speaker_changes', 0)}")
    
    # Show first few segments
    segments = enrichment.get('segments', [])[:3]
    if segments:
        logger.info("\n📝 SAMPLE SEGMENTS")
        logger.info("-" * 20)
        for i, segment in enumerate(segments, 1):
            speaker = segment.get('speaker')
            if speaker:
                speaker_name = speaker.get('display_name', 'Unknown')
            else:
                speaker_name = 'Unknown'
            content = segment.get('content', '')[:100]
            logger.info(f"{i}. {speaker_name}: {content}...")
    
    if 'output_file' in result:
        logger.info(f"\n💾 Full results saved: {result['output_file']}")


def display_batch_summary(results: list):
    """Display batch processing summary."""
    logger = logging.getLogger(__name__)
    
    successful = [r for r in results if r.get('summary', {}).get('pipeline_complete', False)]
    failed = [r for r in results if 'error' in r]
    
    logger.info("\n📊 BATCH PROCESSING SUMMARY")
    logger.info("=" * 35)
    logger.info(f"Total Files: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        total_duration = sum(r.get('summary', {}).get('audio_duration', 0) for r in successful)
        total_speakers = sum(r.get('summary', {}).get('identified_speakers', 0) for r in successful)
        
        logger.info(f"Total Audio Duration: {total_duration:.1f}s")
        logger.info(f"Total Speakers Identified: {total_speakers}")
    
    if failed:
        logger.info("\n❌ FAILED FILES:")
        for result in failed:
            logger.info(f"   {Path(result['audio_file']).name}: {result['error']}")


if __name__ == "__main__":
    main()