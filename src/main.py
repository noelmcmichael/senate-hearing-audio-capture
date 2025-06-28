#!/usr/bin/env python3
"""
Senate Hearing Audio Capture Agent - Main Entry Point

This script orchestrates the extraction of audio from Senate hearing streams.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import json
import logging

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from extractors.isvp_extractor import ISVPExtractor
from converters.ffmpeg_converter import FFmpegConverter, ConversionResult
from utils.page_inspector import PageInspector


def setup_logging(log_dir: Path) -> logging.Logger:
    """Set up logging configuration."""
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
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
        description='Extract audio from Senate hearing streams'
    )
    parser.add_argument(
        '--url',
        required=True,
        help='URL of the Senate hearing page'
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
        default='high',
        help='Audio quality (default: high)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    
    args = parser.parse_args()
    
    # Setup paths
    output_dir = Path(args.output)
    log_dir = Path('logs')
    
    # Setup logging
    logger = setup_logging(log_dir)
    
    logger.info(f"Starting audio capture for: {args.url}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Format: {args.format}, Quality: {args.quality}")
    
    try:
        # Initialize extractor
        extractor = ISVPExtractor()
        
        if not extractor.can_extract(args.url):
            logger.error(f"Extractor cannot handle URL: {args.url}")
            return 1
        
        # Extract streams
        logger.info("Extracting stream information...")
        streams = extractor.extract_streams(args.url)
        
        if not streams:
            logger.error("No streams found on the page")
            return 1
        
        logger.info(f"Found {len(streams)} stream(s)")
        for i, stream in enumerate(streams, 1):
            logger.info(f"  Stream {i}: {stream.format_type} - {stream.url}")
        
        # Initialize converter
        try:
            converter = FFmpegConverter(
                output_format=args.format,
                audio_quality=args.quality
            )
            logger.info(f"FFmpeg converter initialized: {converter.get_info()}")
        except RuntimeError as e:
            logger.error(f"Failed to initialize converter: {e}")
            return 1
        
        # Convert each stream
        results = []
        for i, stream in enumerate(streams, 1):
            logger.info(f"Converting stream {i}/{len(streams)}: {stream.url}")
            
            # Generate output filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"senate_hearing_{timestamp}_stream{i}.{args.format}"
            output_path = output_dir / filename
            
            # Convert
            result = converter.convert_stream(stream, output_path)
            results.append({
                'stream': stream,
                'result': result
            })
            
            if result.success:
                logger.info(f"✅ Success: {output_path}")
                logger.info(f"   Duration: {result.duration_seconds:.1f}s")
                logger.info(f"   Size: {result.file_size_bytes / 1024 / 1024:.1f} MB")
            else:
                logger.error(f"❌ Failed: {result.error_message}")
        
        # Summary
        successful = sum(1 for r in results if r['result'].success)
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"   Total streams: {len(streams)}")
        logger.info(f"   Successful: {successful}")
        logger.info(f"   Failed: {len(streams) - successful}")
        
        # Save detailed results
        results_file = output_dir / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_results(results, results_file)
        logger.info(f"   Results saved: {results_file}")
        
        return 0 if successful > 0 else 1
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


def save_results(results, output_file: Path):
    """Save conversion results to JSON file."""
    output_file.parent.mkdir(exist_ok=True)
    
    # Convert results to serializable format
    serializable_results = []
    for item in results:
        stream = item['stream']
        result = item['result']
        
        serializable_results.append({
            'stream': {
                'url': stream.url,
                'format_type': stream.format_type,
                'quality': stream.quality,
                'duration': stream.duration,
                'title': stream.title,
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
    
    with open(output_file, 'w') as f:
        json.dump(serializable_results, f, indent=2)


if __name__ == "__main__":
    sys.exit(main())