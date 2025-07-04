"""
Audio Capture Service for Cloud Platform
Integrates existing capture logic with cloud infrastructure
"""

import os
import asyncio
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import json

# Cloud storage imports
from google.cloud import storage

# Import existing capture logic
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize logger
logger = logging.getLogger(__name__)

# Conditional imports to avoid startup errors
try:
    from extractors.isvp_extractor import ISVPExtractor
    from converters.ffmpeg_converter import FFmpegConverter
    from utils.page_inspector import PageInspector
    from extractors.base_extractor import StreamInfo
except ImportError as e:
    logger.warning(f"Could not import capture dependencies: {e}")
    # Create placeholder classes for now
    class ISVPExtractor:
        def extract_streams(self, *args, **kwargs):
            raise Exception("ISVP extractor not available")
    
    class FFmpegConverter:
        def __init__(self, *args, **kwargs):
            pass
        def convert_stream(self, *args, **kwargs):
            raise Exception("FFmpeg converter not available")
    
    class PageInspector:
        def analyze_page(self, *args, **kwargs):
            raise Exception("Page inspector not available")
    
    class StreamInfo:
        def __init__(self, *args, **kwargs):
            self.url = ""
            raise Exception("StreamInfo not available")

class CloudCaptureService:
    """Service for capturing audio and storing in cloud infrastructure"""
    
    def __init__(self):
        self.storage_client = storage.Client()
        self.audio_bucket_name = os.environ.get('AUDIO_BUCKET', 'senate-hearing-capture-audio-files-development')
        self.temp_dir = Path(tempfile.gettempdir()) / 'senate_capture'
        self.temp_dir.mkdir(exist_ok=True)
    
    async def capture_hearing_audio(self, hearing_id: str, hearing_url: str, 
                                  capture_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Capture audio from hearing URL and store in cloud storage
        
        Args:
            hearing_id: Unique identifier for the hearing
            hearing_url: URL of the hearing page
            capture_options: Optional capture configuration
            
        Returns:
            Dictionary with capture results and storage information
        """
        
        logger.info(f"Starting audio capture for hearing {hearing_id}")
        
        # Default capture options
        options = {
            'format': 'wav',
            'quality': 'high',
            'timeout': 3600,
            'headless': True
        }
        if capture_options:
            options.update(capture_options)
        
        try:
            # Step 1: Analyze the hearing page
            capture_result = await self._execute_capture(hearing_id, hearing_url, options)
            
            # Step 2: Upload to cloud storage
            storage_result = await self._upload_to_storage(hearing_id, capture_result['local_file'])
            
            # Step 3: Clean up local files
            await self._cleanup_local_files(capture_result['local_file'])
            
            # Step 4: Return comprehensive result
            result = {
                'hearing_id': hearing_id,
                'status': 'completed',
                'capture_time': datetime.now().isoformat(),
                'audio_file': storage_result['cloud_path'],
                'file_size': storage_result['file_size'],
                'duration': capture_result.get('duration', 0),
                'quality': options['format'],
                'streams_found': capture_result.get('streams_found', 0),
                'extraction_method': capture_result.get('method', 'ISVP'),
                'cloud_storage': {
                    'bucket': self.audio_bucket_name,
                    'object_name': storage_result['object_name'],
                    'public_url': storage_result.get('public_url'),
                    'metadata': storage_result.get('metadata', {})
                }
            }
            
            logger.info(f"Audio capture completed successfully for hearing {hearing_id}")
            return result
            
        except Exception as e:
            logger.error(f"Audio capture failed for hearing {hearing_id}: {str(e)}")
            raise CaptureException(f"Capture failed: {str(e)}")
    
    def _analyze_page_with_context(self, hearing_url: str) -> Dict:
        """Analyze page using proper context manager"""
        with PageInspector(headless=True) as inspector:
            return inspector.analyze_page(hearing_url)
    
    async def _execute_capture(self, hearing_id: str, hearing_url: str, 
                             options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual audio capture using existing logic"""
        
        logger.info(f"Executing capture for {hearing_id} from {hearing_url}")
        
        # Create temporary output file
        output_file = self.temp_dir / f"{hearing_id}.{options['format']}"
        
        try:
            # Step 1: Inspect the page to find ISVP player
            page_info = await asyncio.to_thread(self._analyze_page_with_context, hearing_url)
            
            if not page_info.get('has_isvp_player', False):
                raise CaptureException("No ISVP player found on hearing page")
            
            # Step 2: Extract stream URL using ISVP extractor
            extractor = ISVPExtractor()
            stream_infos = await asyncio.to_thread(
                extractor.extract_streams, 
                hearing_url
            )
            
            if not stream_infos:
                raise CaptureException("No stream URLs found")
            
            logger.info(f"Found {len(stream_infos)} stream URLs")
            
            # Step 3: Convert audio using FFmpeg
            converter = FFmpegConverter(
                output_format=options['format'],
                audio_quality=options['quality']
            )
            
            # Use the first (highest quality) stream
            primary_stream = stream_infos[0]
            
            conversion_result = await asyncio.to_thread(
                converter.convert_stream,
                primary_stream,
                output_file
            )
            
            if not conversion_result.success:
                raise CaptureException(f"Audio conversion failed: {conversion_result.error}")
            
            # Get file information
            file_size = output_file.stat().st_size if output_file.exists() else 0
            
            result = {
                'local_file': output_file,
                'streams_found': len(stream_infos),
                'method': 'ISVP',
                'duration': conversion_result.duration_seconds,
                'file_size': file_size,
                'stream_url': primary_stream.url
            }
            
            logger.info(f"Capture execution completed: {file_size} bytes, {conversion_result.duration}s")
            return result
            
        except Exception as e:
            # Cleanup on failure
            if output_file.exists():
                output_file.unlink()
            raise CaptureException(f"Capture execution failed: {str(e)}")
    
    async def _upload_to_storage(self, hearing_id: str, local_file: Path) -> Dict[str, Any]:
        """Upload captured audio to Google Cloud Storage"""
        
        logger.info(f"Uploading {local_file} to cloud storage")
        
        try:
            # Get storage bucket
            bucket = self.storage_client.bucket(self.audio_bucket_name)
            
            # Create object name with timestamp for uniqueness
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            object_name = f"hearings/{hearing_id}/{timestamp}_{local_file.name}"
            
            # Create blob and upload
            blob = bucket.blob(object_name)
            
            # Set metadata
            metadata = {
                'hearing_id': hearing_id,
                'captured_at': datetime.now().isoformat(),
                'original_filename': local_file.name,
                'capture_source': 'cloud_platform'
            }
            blob.metadata = metadata
            
            # Upload file
            with open(local_file, 'rb') as file_obj:
                blob.upload_from_file(file_obj)
            
            # Get file information
            blob.reload()  # Refresh to get updated information
            
            result = {
                'cloud_path': f"gs://{self.audio_bucket_name}/{object_name}",
                'object_name': object_name,
                'file_size': blob.size,
                'metadata': metadata,
                'upload_time': datetime.now().isoformat()
            }
            
            logger.info(f"Upload completed: {result['cloud_path']} ({blob.size} bytes)")
            return result
            
        except Exception as e:
            logger.error(f"Upload to cloud storage failed: {str(e)}")
            raise CaptureException(f"Storage upload failed: {str(e)}")
    
    async def _cleanup_local_files(self, local_file: Path):
        """Clean up temporary local files"""
        try:
            if local_file.exists():
                local_file.unlink()
                logger.debug(f"Cleaned up local file: {local_file}")
        except Exception as e:
            logger.warning(f"Failed to cleanup local file {local_file}: {e}")
    
    async def get_storage_info(self, hearing_id: str) -> Optional[Dict[str, Any]]:
        """Get storage information for a hearing's audio file"""
        
        try:
            bucket = self.storage_client.bucket(self.audio_bucket_name)
            
            # List objects with hearing_id prefix
            blobs = list(bucket.list_blobs(prefix=f"hearings/{hearing_id}/"))
            
            if not blobs:
                return None
            
            # Get the most recent blob (latest capture)
            latest_blob = max(blobs, key=lambda b: b.time_created)
            
            return {
                'hearing_id': hearing_id,
                'cloud_path': f"gs://{self.audio_bucket_name}/{latest_blob.name}",
                'file_size': latest_blob.size,
                'created_at': latest_blob.time_created.isoformat(),
                'metadata': latest_blob.metadata or {},
                'object_name': latest_blob.name
            }
            
        except Exception as e:
            logger.error(f"Error getting storage info for hearing {hearing_id}: {e}")
            return None
    
    async def verify_audio_file(self, hearing_id: str) -> Dict[str, Any]:
        """Verify that audio file exists and is accessible"""
        
        storage_info = await self.get_storage_info(hearing_id)
        
        if not storage_info:
            return {
                'exists': False,
                'error': 'Audio file not found in storage'
            }
        
        try:
            # Try to access the blob to verify it exists and is readable
            bucket = self.storage_client.bucket(self.audio_bucket_name)
            blob = bucket.blob(storage_info['object_name'])
            
            # Check if blob exists
            if not blob.exists():
                return {
                    'exists': False,
                    'error': 'Audio file reference exists but file is missing'
                }
            
            # Get additional information
            blob.reload()
            
            return {
                'exists': True,
                'size': blob.size,
                'created_at': blob.time_created.isoformat(),
                'content_type': blob.content_type,
                'cloud_path': storage_info['cloud_path'],
                'metadata': blob.metadata or {}
            }
            
        except Exception as e:
            return {
                'exists': False,
                'error': f'Error verifying audio file: {str(e)}'
            }

class CaptureException(Exception):
    """Custom exception for capture-related errors"""
    pass

# Global service instance
_capture_service = None

def get_capture_service() -> CloudCaptureService:
    """Get singleton capture service instance"""
    global _capture_service
    if _capture_service is None:
        _capture_service = CloudCaptureService()
    return _capture_service