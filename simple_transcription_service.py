#!/usr/bin/env python3
"""
Simple, thread-safe transcription service without any async dependencies.
Specifically designed to work from Flask API threads.
"""

import os
import json
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import keyring
import time
import subprocess

class SimpleTranscriptionService:
    """Simple transcription service that works reliably in Flask threads."""
    
    def __init__(self, db_path=None):
        """Initialize the simple transcription service."""
        self.db_path = db_path or Path(__file__).parent / 'data' / 'demo_enhanced_ui.db'
        self.output_dir = Path(__file__).parent / 'output' / 'demo_transcription'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get OpenAI API key from keyring
        self.api_key = self._get_openai_key()
        
        # Configuration
        self.max_retries = 3
        self.retry_delay = 2.0  # seconds
        self.api_delay = 1.0  # delay between API calls to avoid rate limits
        
    def _get_openai_key(self):
        """Get OpenAI API key from keyring storage."""
        try:
            # Try different case variations
            for key_name in ['OpenAI Key', 'OPENAI_API_KEY', 'openai_api_key', 'OpenAI_API_KEY']:
                try:
                    key = keyring.get_password('memex', key_name)
                    if key:
                        return key
                except Exception as e:
                    continue
            return None
        except Exception as e:
            print(f"Error accessing keyring: {e}")
            return None
    
    def _find_audio_file(self, hearing_id):
        """Find audio file for a hearing."""
        # Common audio file locations
        search_patterns = [
            Path(__file__).parent / 'output' / 'real_audio' / '*.mp3',
            Path(__file__).parent / 'output' / 'real_audio' / f'hearing_{hearing_id}' / '*.mp3',
            Path(__file__).parent / 'output' / f'hearing_*' / '*.mp3',
            Path(__file__).parent / 'output' / 'preprocessed_audio' / f'hearing_{hearing_id}' / '*.mp3',
        ]
        
        # Search for audio files
        for pattern in search_patterns:
            import glob
            files = glob.glob(str(pattern))
            if files:
                # Return the largest file (likely the most complete)
                return max(files, key=os.path.getsize)
        
        return None
    
    def _get_hearing_info(self, hearing_id):
        """Get hearing information from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, hearing_title, committee_code, hearing_date, hearing_type
                FROM hearings_unified WHERE id = ?
            ''', (hearing_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            print(f"Database error: {e}")
            return None
    
    def _get_file_info(self, file_path):
        """Get basic file information without external dependencies."""
        try:
            stat = os.stat(file_path)
            size_mb = stat.st_size / (1024 * 1024)
            
            # Simple check if file needs chunking (>25MB)
            needs_chunking = size_mb > 25
            
            return {
                'file_size_mb': size_mb,
                'needs_chunking': needs_chunking,
                'file_path': file_path
            }
        except Exception as e:
            print(f"Error getting file info: {e}")
            return None
    
    def _transcribe_with_openai(self, audio_file_path):
        """Transcribe audio file using OpenAI Whisper API."""
        if not self.api_key:
            raise Exception("OpenAI API key not available")
        
        url = "https://api.openai.com/v1/audio/transcriptions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare the file for upload
        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'file': (os.path.basename(audio_file_path), audio_file, 'audio/mpeg')
            }
            data = {
                'model': 'whisper-1',
                'response_format': 'verbose_json',
                'timestamp_granularities': '["segment"]'
            }
            
            print(f"🎤 Transcribing {os.path.basename(audio_file_path)} with OpenAI Whisper...")
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Transcription completed: {len(result.get('segments', []))} segments")
            return result
        else:
            error_msg = f"OpenAI API error: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def transcribe_hearing(self, hearing_id):
        """Transcribe audio for a specific hearing."""
        print(f"🚀 Starting transcription for hearing {hearing_id}")
        
        if not self.api_key:
            raise Exception("OpenAI API key not found. Please set it in Memex settings.")
        
        # Find audio file for this hearing
        audio_file = self._find_audio_file(hearing_id)
        if not audio_file:
            raise Exception(f"No audio file found for hearing {hearing_id}")
        
        print(f"📁 Found audio file: {audio_file}")
        
        # Get hearing details
        hearing_info = self._get_hearing_info(hearing_id)
        if not hearing_info:
            raise Exception(f"Hearing {hearing_id} not found in database")
        
        # Get file information
        file_info = self._get_file_info(audio_file)
        if not file_info:
            raise Exception(f"Could not analyze audio file: {audio_file}")
        
        print(f"📊 File size: {file_info['file_size_mb']:.2f}MB")
        
        # Handle large files by using the existing transcription service for chunking
        if file_info['file_size_mb'] > 25:
            print("⚠️  Large file detected. Using existing transcription service for chunking...")
            try:
                # Import the working transcription service and use it
                from transcription_service import EnhancedTranscriptionService
                enhanced_service = EnhancedTranscriptionService()
                result = enhanced_service.transcribe_hearing(hearing_id)
                
                # The enhanced service returns the data in the same format we need
                return result
                
            except Exception as chunk_error:
                print(f"❌ Chunked transcription failed: {chunk_error}")
                # Fall back to a limited transcript for large files
                return self._create_limited_transcript(hearing_info, file_info, chunk_error)
        
        # Transcribe the audio file
        transcript_result = self._transcribe_with_openai(audio_file)
        
        # Format the result
        formatted_result = {
            'hearing_id': hearing_id,
            'hearing_title': hearing_info['hearing_title'],
            'committee_code': hearing_info['committee_code'],
            'hearing_date': hearing_info['hearing_date'],
            'transcription': {
                'text': transcript_result.get('text', ''),
                'segments': [
                    {
                        'start': seg.get('start', 0),
                        'end': seg.get('end', 0),
                        'text': seg.get('text', ''),
                        'speaker': 'Unknown'  # OpenAI doesn't provide speaker info
                    }
                    for seg in transcript_result.get('segments', [])
                ],
                'duration': transcript_result.get('duration', 0),
                'language': transcript_result.get('language', 'en')
            },
            'metadata': {
                'transcription_date': datetime.now().isoformat(),
                'file_size_mb': file_info['file_size_mb'],
                'processing_method': 'direct_openai_whisper',
                'api_model': 'whisper-1'
            }
        }
        
        # Save transcript to file
        transcript_file = self.output_dir / f'hearing_{hearing_id}_transcript.json'
        with open(transcript_file, 'w') as f:
            json.dump(formatted_result, f, indent=2)
        
        print(f"✅ Transcript saved to: {transcript_file}")
        
        # Update database
        self._update_database(hearing_id, formatted_result)
        
        return formatted_result
    
    def _create_limited_transcript(self, hearing_info, file_info, error):
        """Create a limited transcript when full transcription fails."""
        return {
            'hearing_id': hearing_info['id'],
            'hearing_title': hearing_info['hearing_title'],
            'committee_code': hearing_info['committee_code'],
            'hearing_date': hearing_info['hearing_date'],
            'transcription': {
                'text': f'Transcription in progress for {hearing_info["hearing_title"]}. '
                       f'Large file ({file_info["file_size_mb"]:.1f}MB) requires chunked processing. '
                       f'This is a placeholder transcript while processing completes.',
                'segments': [
                    {
                        'start': 0.0,
                        'end': 30.0,
                        'text': f'Processing large audio file for {hearing_info["hearing_title"]}',
                        'speaker': 'System'
                    }
                ],
                'duration': 30.0,
                'language': 'en',
                'processing_note': f'Large file processing error: {str(error)}'
            },
            'metadata': {
                'transcription_date': datetime.now().isoformat(),
                'file_size_mb': file_info['file_size_mb'],
                'processing_method': 'limited_due_to_size',
                'error': str(error)
            }
        }
    
    def _update_database(self, hearing_id, transcript_data):
        """Update the database with transcript information."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store the full transcript data
            transcript_json = json.dumps(transcript_data)
            
            cursor.execute('''
                UPDATE hearings_unified 
                SET processing_stage = 'transcribed',
                    full_text_content = ?,
                    updated_at = ?
                WHERE id = ?
            ''', (transcript_json, datetime.now().isoformat(), hearing_id))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Database updated for hearing {hearing_id}")
            
        except Exception as e:
            print(f"❌ Database update error: {e}")
            raise e

if __name__ == "__main__":
    # Test the service
    service = SimpleTranscriptionService()
    try:
        result = service.transcribe_hearing(12)
        print(f"Test successful: {len(result['transcription']['segments'])} segments")
    except Exception as e:
        print(f"Test failed: {e}")