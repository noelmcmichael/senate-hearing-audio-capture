#!/usr/bin/env python3
"""
Enhanced Senate Hearing Audio Capture with Hybrid Support

Main entry point supporting both ISVP (Senate) and YouTube (House) streams
with intelligent platform detection and fallback capabilities.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import json
import logging

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from extractors.extraction_orchestrator import ExtractionOrchestrator, analyze_congressional_url
from converters.hybrid_converter import HybridConverter


def setup_logging(log_dir: Path) -> logging.Logger:
    """Set up logging configuration."""
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"capture_hybrid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Extract audio from congressional hearings (Senate ISVP + YouTube)'
    )
    parser.add_argument(
        '--url',
        required=True,
        help='URL of the congressional hearing page'
    )
    parser.add_argument(
        '--output',
        default='./output',
        help='Output directory for audio files (default: ./output)'
    )
    parser.add_argument(
        '--format',
        choices=['wav', 'mp3', 'flac'],
        default='mp3',
        help='Output audio format (default: mp3)'
    )
    parser.add_argument(
        '--quality',
        choices=['low', 'medium', 'high'],
        default='medium',
        help='Audio quality (default: medium)'
    )
    parser.add_argument(
        '--platform',
        choices=['auto', 'isvp', 'youtube'],
        default='auto',
        help='Preferred extraction platform (default: auto)'
    )
    parser.add_argument(
        '--duration-limit',
        type=int,
        help='Maximum duration to capture in seconds'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (for ISVP)'
    )
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze the URL without extracting audio'
    )
    
    args = parser.parse_args()
    
    # Setup paths
    output_dir = Path(args.output)
    log_dir = Path('logs')
    
    # Setup logging
    logger = setup_logging(log_dir)
    
    logger.info(f"🎯 Starting hybrid audio capture for: {args.url}")
    logger.info(f"📁 Output directory: {output_dir}")
    logger.info(f"🎵 Format: {args.format}, Quality: {args.quality}")
    logger.info(f"🔧 Platform preference: {args.platform}")
    
    try:
        # Step 1: Analyze the URL
        logger.info("🔍 Analyzing URL...")
        analysis = analyze_congressional_url(args.url)
        
        platform_info = analysis['platform_detection']
        strategy = analysis['extraction_strategy']
        
        logger.info(f"📊 Platform Analysis:")
        logger.info(f"   Platform: {platform_info['detected_platform']}")
        logger.info(f"   Congressional Type: {platform_info['congressional_type']}")
        logger.info(f"   Confidence: {platform_info['confidence']}%")
        logger.info(f"   Recommended Extractor: {platform_info['recommended_extractor']}")
        logger.info(f"   Available Extractors: {platform_info['available_extractors']}")
        
        logger.info(f"🎯 Extraction Strategy:")
        logger.info(f"   Primary Extractor: {strategy['primary_extractor']}")
        logger.info(f"   Extraction Order: {strategy['extraction_order']}")
        logger.info(f"   Expected Success Rate: {strategy['expected_success_rate']}%")
        for note in strategy['notes']:
            logger.info(f"   📝 {note}")
        
        # If analyze-only mode, stop here
        if args.analyze_only:
            print(f"\n📋 URL Analysis Complete")
            print(f"Platform: {platform_info['detected_platform']}")
            print(f"Recommended: {platform_info['recommended_extractor']}")
            print(f"Confidence: {platform_info['confidence']}%")
            return 0
        
        # Step 2: Initialize orchestrator
        orchestrator = ExtractionOrchestrator()
        
        # Step 3: Extract streams
        logger.info("📡 Extracting stream information...")
        
        prefer_platform = None if args.platform == 'auto' else args.platform
        streams, extractor_used = orchestrator.extract_streams(args.url, prefer_platform)
        
        if not streams:
            logger.error("❌ No streams found")
            return 1
        
        logger.info(f"✅ Found {len(streams)} stream(s) using {extractor_used} extractor")
        for i, stream in enumerate(streams, 1):
            logger.info(f"   Stream {i}: {stream.format_type} - {stream.title}")
            logger.info(f"   Committee: {stream.metadata.get('committee', 'Unknown')}")
            logger.info(f"   Source: {stream.metadata.get('source', 'Unknown')}")
        
        # Step 4: Initialize hybrid converter
        try:
            converter = HybridConverter(
                output_format=args.format,
                audio_quality=args.quality
            )
            
            capabilities = converter.test_conversion_capabilities()
            logger.info(f"🔧 Converter capabilities: {capabilities}")
            
            if not capabilities.get('ffmpeg_available') and extractor_used == 'isvp':
                logger.error("❌ FFmpeg required for ISVP streams but not available")
                return 1
            
        except RuntimeError as e:
            logger.error(f"❌ Failed to initialize converter: {e}")
            return 1
        
        # Step 5: Convert streams
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []
        
        for i, stream in enumerate(streams, 1):
            logger.info(f"🎵 Converting stream {i}/{len(streams)}: {stream.title}")
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in stream.title if c.isalnum() or c in ' -_').strip()
            safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
            
            filename = f"{safe_title}_{timestamp}.{args.format}"
            output_path = output_dir / filename
            
            # Convert stream
            result = converter.convert_stream(
                stream=stream,
                output_path=output_path,
                duration_limit=args.duration_limit
            )
            
            if result.success:
                logger.info(f"   ✅ Success: {output_path}")
                logger.info(f"   📏 Size: {result.file_size_bytes / (1024**2):.1f} MB")
                if result.duration_seconds:
                    logger.info(f"   ⏱️  Duration: {result.duration_seconds / 60:.1f} minutes")
            else:
                logger.error(f"   ❌ Failed: {result.error_message}")
            
            results.append({
                'stream': {
                    'title': stream.title,
                    'url': stream.url,
                    'format_type': stream.format_type,
                    'metadata': stream.metadata
                },
                'result': {
                    'success': result.success,
                    'output_path': str(result.output_path) if result.output_path else None,
                    'duration_seconds': result.duration_seconds,
                    'file_size_bytes': result.file_size_bytes,
                    'error_message': result.error_message,
                    'metadata': result.metadata
                }
            })
        
        # Step 6: Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = output_dir / f"results_hybrid_{timestamp}.json"
        
        full_results = {
            'timestamp': timestamp,
            'url': args.url,
            'platform_analysis': analysis,
            'extractor_used': extractor_used,
            'conversion_settings': {
                'format': args.format,
                'quality': args.quality,
                'duration_limit': args.duration_limit
            },
            'streams': results
        }
        
        with open(results_file, 'w') as f:
            json.dump(full_results, f, indent=2)
        
        logger.info(f"💾 Results saved: {results_file}")
        
        # Summary
        successful_conversions = sum(1 for r in results if r['result']['success'])
        total_streams = len(results)
        
        logger.info(f"📊 Conversion Summary:")
        logger.info(f"   Total streams: {total_streams}")
        logger.info(f"   Successful: {successful_conversions}")
        logger.info(f"   Failed: {total_streams - successful_conversions}")
        
        if successful_conversions > 0:
            total_size = sum(r['result']['file_size_bytes'] or 0 for r in results if r['result']['success'])
            total_duration = sum(r['result']['duration_seconds'] or 0 for r in results if r['result']['success'])
            
            logger.info(f"   Total size: {total_size / (1024**2):.1f} MB")
            logger.info(f"   Total duration: {total_duration / 60:.1f} minutes")
        
        return 0 if successful_conversions > 0 else 1
        
    except KeyboardInterrupt:
        logger.info("🛑 Capture interrupted by user")
        return 1
    except Exception as e:
        logger.exception(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())