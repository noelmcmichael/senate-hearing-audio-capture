"""
Transcription Service for Cloud Platform
Integrates existing transcription logic with cloud infrastructure
"""

import os
import asyncio
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

# Cloud storage imports
from google.cloud import storage

# Import existing transcription logic
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Conditional imports to avoid startup errors
try:
    from transcription.whisper_transcriber import WhisperTranscriber
    from enrichment.transcript_enricher import TranscriptEnricher
    TRANSCRIPTION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import transcription dependencies: {e}")
    TRANSCRIPTION_AVAILABLE = False
    # Create placeholder classes for now
    class WhisperTranscriber:
        def transcribe_file(self, *args, **kwargs):
            raise Exception("Whisper transcriber not available in API-only mode")
    
    class TranscriptEnricher:
        def enrich_transcript(self, *args, **kwargs):
            raise Exception("Transcript enricher not available in API-only mode")

logger = logging.getLogger(__name__)

class CloudTranscriptionService:
    """Service for transcribing audio files stored in cloud storage"""
    
    def __init__(self):
        self.storage_client = storage.Client()
        self.audio_bucket_name = os.environ.get('AUDIO_BUCKET', 'senate-hearing-capture-audio-files-development')
        self.temp_dir = Path(tempfile.gettempdir()) / 'senate_transcription'
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize transcription components
        self.whisper_transcriber = WhisperTranscriber()
        self.transcript_enricher = TranscriptEnricher()
    
    async def transcribe_hearing(self, hearing_id: str, transcription_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Transcribe audio file from cloud storage
        
        Args:
            hearing_id: Unique identifier for the hearing
            transcription_options: Optional transcription configuration
            
        Returns:
            Dictionary with transcription results
        """
        
        logger.info(f"Starting transcription for hearing {hearing_id}")
        
        # Default transcription options
        options = {
            'model': 'base',
            'language': 'en',
            'enhance_speakers': True,
            'congressional_enrichment': True
        }
        if transcription_options:
            options.update(transcription_options)
        
        try:
            # Step 1: Download audio from cloud storage
            local_audio_file = await self._download_audio_file(hearing_id)
            
            # Step 2: Transcribe with Whisper
            transcript_result = await self._transcribe_audio(local_audio_file, options)
            
            # Step 3: Enhance with congressional metadata (if enabled)
            if options.get('congressional_enrichment', True):
                enhanced_result = await self._enhance_transcript(hearing_id, transcript_result, options)
            else:
                enhanced_result = transcript_result
            
            # Step 4: Store transcript in database/storage
            storage_result = await self._store_transcript(hearing_id, enhanced_result)
            
            # Step 5: Clean up local files
            await self._cleanup_local_files(local_audio_file)
            
            # Step 6: Return comprehensive result
            result = {
                'hearing_id': hearing_id,
                'status': 'completed',
                'transcription_time': datetime.now().isoformat(),
                'transcript': enhanced_result,
                'options_used': options,
                'storage': storage_result,
                'metrics': {
                    'duration': enhanced_result.get('duration', 0),
                    'segments': len(enhanced_result.get('segments', [])),
                    'words': enhanced_result.get('word_count', 0),
                    'speakers_identified': len(enhanced_result.get('speakers', [])),
                    'confidence_avg': enhanced_result.get('confidence_avg', 0)
                }
            }
            
            logger.info(f"Transcription completed successfully for hearing {hearing_id}")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed for hearing {hearing_id}: {str(e)}")
            raise TranscriptionException(f"Transcription failed: {str(e)}")
    
    async def _download_audio_file(self, hearing_id: str) -> Path:
        """Download audio file from cloud storage to local temp directory"""
        
        logger.info(f"Downloading audio file for hearing {hearing_id}")
        
        try:
            # Get storage info
            bucket = self.storage_client.bucket(self.audio_bucket_name)
            blobs = list(bucket.list_blobs(prefix=f"hearings/{hearing_id}/"))
            
            if not blobs:
                raise TranscriptionException(f"No audio file found for hearing {hearing_id}")
            
            # Get the most recent audio file
            latest_blob = max(blobs, key=lambda b: b.time_created)
            
            # Create local file path
            local_file = self.temp_dir / f"{hearing_id}_{latest_blob.name.split('/')[-1]}"
            
            # Download file
            latest_blob.download_to_filename(local_file)
            
            logger.info(f"Downloaded {latest_blob.size} bytes to {local_file}")
            return local_file
            
        except Exception as e:
            logger.error(f"Failed to download audio file for hearing {hearing_id}: {e}")
            raise TranscriptionException(f"Audio download failed: {str(e)}")
    
    async def _transcribe_audio(self, audio_file: Path, options: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio using Whisper"""
        
        logger.info(f"Transcribing audio file {audio_file}")
        
        try:
            # Configure Whisper transcriber
            model_size = options.get('model', 'base')
            language = options.get('language', 'en')
            
            # Transcribe (run in thread to avoid blocking)
            result = await asyncio.to_thread(
                self.whisper_transcriber.transcribe_file,
                str(audio_file),
                model_size=model_size,
                language=language
            )
            
            logger.info(f"Transcription completed: {len(result.get('segments', []))} segments")
            return result
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise TranscriptionException(f"Whisper transcription failed: {str(e)}")
    
    async def _enhance_transcript(self, hearing_id: str, transcript: Dict[str, Any], 
                                options: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance transcript with congressional metadata and speaker identification"""
        
        logger.info(f"Enhancing transcript for hearing {hearing_id}")
        
        try:
            # Run enhancement in thread
            enhanced = await asyncio.to_thread(
                self.transcript_enricher.enrich_transcript,
                transcript,
                hearing_id
            )
            
            logger.info(f"Transcript enhancement completed")
            return enhanced
            
        except Exception as e:
            logger.warning(f"Transcript enhancement failed: {e}")
            # Return original transcript if enhancement fails
            return transcript
    
    async def _store_transcript(self, hearing_id: str, transcript: Dict[str, Any]) -> Dict[str, Any]:
        """Store transcript in database and/or cloud storage"""
        
        logger.info(f"Storing transcript for hearing {hearing_id}")
        
        try:
            # For now, we'll store as JSON in cloud storage
            # Later this could be enhanced to store in database
            
            bucket = self.storage_client.bucket(self.audio_bucket_name)
            
            # Create transcript object name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            object_name = f"transcripts/{hearing_id}/{timestamp}_transcript.json"
            
            # Create blob and upload transcript
            blob = bucket.blob(object_name)
            
            # Set metadata
            metadata = {
                'hearing_id': hearing_id,
                'transcribed_at': datetime.now().isoformat(),
                'transcript_version': '1.0',
                'source': 'cloud_platform'
            }
            blob.metadata = metadata
            
            # Upload transcript as JSON
            transcript_json = json.dumps(transcript, indent=2, ensure_ascii=False)
            blob.upload_from_string(transcript_json, content_type='application/json')
            
            result = {
                'cloud_path': f"gs://{self.audio_bucket_name}/{object_name}",
                'object_name': object_name,
                'size': blob.size,
                'metadata': metadata
            }
            
            logger.info(f"Transcript stored: {result['cloud_path']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to store transcript: {e}")
            raise TranscriptionException(f"Transcript storage failed: {str(e)}")
    
    async def _cleanup_local_files(self, local_file: Path):
        """Clean up temporary local files"""
        try:
            if local_file.exists():
                local_file.unlink()
                logger.debug(f"Cleaned up local file: {local_file}")
        except Exception as e:
            logger.warning(f"Failed to cleanup local file {local_file}: {e}")
    
    async def get_transcript_info(self, hearing_id: str) -> Optional[Dict[str, Any]]:
        """Get transcript information for a hearing"""
        
        try:
            bucket = self.storage_client.bucket(self.audio_bucket_name)
            
            # List transcript objects for this hearing
            blobs = list(bucket.list_blobs(prefix=f"transcripts/{hearing_id}/"))
            
            if not blobs:
                return None
            
            # Get the most recent transcript
            latest_blob = max(blobs, key=lambda b: b.time_created)
            
            return {
                'hearing_id': hearing_id,
                'cloud_path': f"gs://{self.audio_bucket_name}/{latest_blob.name}",
                'size': latest_blob.size,
                'created_at': latest_blob.time_created.isoformat(),
                'metadata': latest_blob.metadata or {},
                'object_name': latest_blob.name
            }
            
        except Exception as e:
            logger.error(f"Error getting transcript info for hearing {hearing_id}: {e}")
            return None
    
    async def get_transcript_content(self, hearing_id: str) -> Optional[Dict[str, Any]]:
        """Get actual transcript content for a hearing"""
        
        try:
            transcript_info = await self.get_transcript_info(hearing_id)
            
            if not transcript_info:
                return None
            
            # Download and parse transcript content
            bucket = self.storage_client.bucket(self.audio_bucket_name)
            blob = bucket.blob(transcript_info['object_name'])
            
            # Download content
            content = blob.download_as_text()
            transcript = json.loads(content)
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error getting transcript content for hearing {hearing_id}: {e}")
            return None

class TranscriptionException(Exception):
    """Custom exception for transcription-related errors"""
    pass

# Global service instance
_transcription_service = None

def get_transcription_service() -> CloudTranscriptionService:
    """Get singleton transcription service instance"""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = CloudTranscriptionService()
    return _transcription_service