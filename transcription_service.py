#!/usr/bin/env python3
"""
Enhanced transcription service for Senate hearing audio processing.
Supports both small files and chunked processing for large files.
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

from audio_analyzer import AudioAnalyzer
from audio_chunker import AudioChunker, ChunkingResult, AudioChunk

class EnhancedTranscriptionService:
    """Enhanced service for handling audio transcription with chunking support."""
    
    def __init__(self, db_path=None):
        """Initialize the enhanced transcription service."""
        self.db_path = db_path or Path(__file__).parent / 'data' / 'demo_enhanced_ui.db'
        self.output_dir = Path(__file__).parent / 'output' / 'demo_transcription'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.analyzer = AudioAnalyzer()
        self.chunker = AudioChunker()
        
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
            
            # If not found, check environment variable as fallback
            env_key = os.environ.get('OPENAI_API_KEY')
            if env_key:
                return env_key
                
            return None
        except Exception as e:
            return None
    
    def transcribe_hearing(self, hearing_id, progress_callback=None):
        """Transcribe audio for a specific hearing with chunking support."""
        if not self.api_key:
            raise Exception("OpenAI API key not found. Please set it in Memex settings.")
        
        # Find audio file for this hearing
        audio_file = self._find_audio_file(hearing_id)
        if not audio_file:
            raise Exception(f"No audio file found for hearing {hearing_id}")
        
        # Get hearing details
        hearing_info = self._get_hearing_info(hearing_id)
        
        if progress_callback:
            progress_callback("analyzing", 0, "Analyzing audio file...")
        
        # Analyze audio file to determine processing approach
        analysis = self.analyzer.analyze_file(audio_file)
        
        # Choose processing method based on file size
        if analysis.needs_chunking:
            print(f"🔧 Large file detected ({analysis.file_size_mb:.2f}MB), using chunked processing")
            transcript_data = self._transcribe_with_chunking(audio_file, hearing_info, analysis, progress_callback)
        else:
            print(f"📁 Small file ({analysis.file_size_mb:.2f}MB), using direct processing")
            transcript_data = self._transcribe_direct(audio_file, hearing_info, progress_callback)
        
        # Save transcript to file
        transcript_file = self.output_dir / f'hearing_{hearing_id}_transcript.json'
        with open(transcript_file, 'w') as f:
            json.dump(transcript_data, f, indent=2)
        
        # Update database with transcript
        self._update_database_transcript(hearing_id, transcript_data)
        
        if progress_callback:
            progress_callback("completed", 100, "Transcription completed successfully")
        
        return transcript_data
    
    def _transcribe_with_chunking(self, audio_file: Path, hearing_info: Dict, analysis, progress_callback=None) -> Dict[str, Any]:
        """Transcribe large audio file using chunking approach."""
        
        if progress_callback:
            progress_callback("chunking", 5, f"Creating {analysis.estimated_chunks} audio chunks...")
        
        # Create chunks
        chunking_result = self.chunker.chunk_audio_file(audio_file, hearing_id=str(hearing_info['id']))
        
        try:
            # Validate chunks
            if not self.chunker.validate_chunks(chunking_result):
                raise Exception("Chunk validation failed")
            
            if progress_callback:
                progress_callback("chunking", 10, f"Created {len(chunking_result.chunks)} chunks successfully")
            
            # Process each chunk
            all_segments = []
            total_chunks = len(chunking_result.chunks)
            base_progress = 10
            chunk_progress_range = 80  # 10% to 90% for chunk processing
            
            for i, chunk in enumerate(chunking_result.chunks):
                chunk_start_progress = base_progress + (i * chunk_progress_range // total_chunks)
                chunk_end_progress = base_progress + ((i + 1) * chunk_progress_range // total_chunks)
                
                if progress_callback:
                    progress_callback("processing", chunk_start_progress, 
                                    f"Processing chunk {i+1}/{total_chunks} ({chunk.file_size_mb:.1f}MB)...")
                
                # Transcribe chunk with retries
                chunk_segments = self._transcribe_chunk_with_retries(chunk, hearing_info, i)
                
                # Adjust timestamps for chunk position in original audio
                adjusted_segments = self._adjust_chunk_timestamps(chunk_segments, chunk)
                
                all_segments.extend(adjusted_segments)
                
                if progress_callback:
                    progress_callback("processing", chunk_end_progress, 
                                    f"Completed chunk {i+1}/{total_chunks}")
                
                # Small delay between API calls
                if i < total_chunks - 1:  # Don't delay after last chunk
                    time.sleep(self.api_delay)
            
            if progress_callback:
                progress_callback("merging", 90, "Merging chunk transcripts...")
            
            # Merge segments and handle overlaps
            merged_segments = self._merge_overlapping_segments(all_segments)
            
            # Create final transcript
            full_text = " ".join([segment['text'].strip() for segment in merged_segments])
            
            transcript_data = {
                'hearing_id': hearing_info['id'],
                'hearing_title': hearing_info['hearing_title'],
                'committee_code': hearing_info['committee_code'],
                'hearing_date': hearing_info['hearing_date'],
                'transcription': {
                    'text': full_text,
                    'segments': merged_segments,
                    'language': 'en',
                    'duration': analysis.duration_seconds
                },
                'metadata': {
                    'transcription_timestamp': datetime.now().isoformat(),
                    'source': 'openai_whisper_chunked',
                    'model': 'whisper-1',
                    'audio_file': str(audio_file),
                    'total_chunks': total_chunks,
                    'chunking_info': chunking_result.to_dict()
                }
            }
            
            return transcript_data
            
        finally:
            # Always clean up chunks
            if progress_callback:
                progress_callback("cleanup", 95, "Cleaning up temporary files...")
            self.chunker.cleanup_chunks(chunking_result)
    
    def _transcribe_chunk_with_retries(self, chunk: AudioChunk, hearing_info: Dict, chunk_index: int) -> List[Dict]:
        """Transcribe a single chunk with retry logic."""
        
        for attempt in range(self.max_retries):
            try:
                return self._transcribe_single_chunk(chunk, hearing_info, chunk_index)
            
            except Exception as e:
                print(f"⚠️  Chunk {chunk_index} attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    print(f"🔄 Retrying chunk {chunk_index} in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"❌ Chunk {chunk_index} failed after {self.max_retries} attempts")
                    raise Exception(f"Failed to transcribe chunk {chunk_index} after {self.max_retries} attempts: {e}")
    
    def _transcribe_single_chunk(self, chunk: AudioChunk, hearing_info: Dict, chunk_index: int) -> List[Dict]:
        """Transcribe a single audio chunk using OpenAI Whisper API."""
        
        url = "https://api.openai.com/v1/audio/transcriptions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare audio file for upload
        with open(chunk.file_path, 'rb') as f:
            files = {
                'file': (chunk.file_path.name, f, 'audio/mpeg'),
                'model': (None, 'whisper-1'),
                'response_format': (None, 'verbose_json'),
                'timestamp_granularities[]': (None, 'segment')
            }
            
            # Add prompt for better transcription
            prompt = f"This is chunk {chunk_index + 1} of a US Senate hearing: {hearing_info.get('hearing_title', 'Senate Hearing')}"
            files['prompt'] = (None, prompt)
            
            response = requests.post(url, headers=headers, files=files, timeout=300)  # 5 minute timeout
        
        if response.status_code != 200:
            raise Exception(f"Whisper API error: {response.status_code} - {response.text}")
        
        whisper_result = response.json()
        
        # Convert segments to our format
        segments = []
        for segment in whisper_result.get('segments', []):
            segments.append({
                'start': segment.get('start', 0),
                'end': segment.get('end', 0),
                'text': segment.get('text', ''),
                'speaker': 'Unknown',  # Default speaker
                'confidence': 1.0,
                'chunk_index': chunk_index,
                'review_metadata': {
                    'needs_review': False,
                    'has_correction': False,
                    'reviewer': None,
                    'review_timestamp': None
                }
            })
        
        print(f"✅ Chunk {chunk_index}: {len(segments)} segments, {whisper_result.get('duration', 0):.1f}s")
        return segments
    
    def _adjust_chunk_timestamps(self, segments: List[Dict], chunk: AudioChunk) -> List[Dict]:
        """Adjust segment timestamps to reflect position in original audio."""
        
        adjusted_segments = []
        
        for segment in segments:
            # Adjust timestamps by adding chunk start time
            adjusted_segment = segment.copy()
            adjusted_segment['start'] = segment['start'] + chunk.start_time
            adjusted_segment['end'] = segment['end'] + chunk.start_time
            
            adjusted_segments.append(adjusted_segment)
        
        return adjusted_segments
    
    def _merge_overlapping_segments(self, all_segments: List[Dict]) -> List[Dict]:
        """Merge overlapping segments from different chunks."""
        
        if not all_segments:
            return []
        
        # Sort segments by start time
        sorted_segments = sorted(all_segments, key=lambda x: x['start'])
        
        merged_segments = []
        overlap_threshold = 25.0  # 25 seconds (less than 30s overlap to account for processing differences)
        
        for segment in sorted_segments:
            # Check if this segment overlaps with the last merged segment
            if (merged_segments and 
                segment['start'] < merged_segments[-1]['end'] and
                segment['start'] > merged_segments[-1]['end'] - overlap_threshold):
                
                # This is likely an overlapping segment, skip it
                # (keep the earlier segment which is likely more complete)
                continue
            
            merged_segments.append(segment)
        
        # Renumber segments
        for i, segment in enumerate(merged_segments):
            segment['segment_id'] = i
        
        return merged_segments
    
    def _transcribe_direct(self, audio_file: Path, hearing_info: Dict, progress_callback=None) -> Dict[str, Any]:
        """Transcribe small audio file directly (existing method)."""
        
        if progress_callback:
            progress_callback("processing", 20, "Processing audio with Whisper API...")
        
        url = "https://api.openai.com/v1/audio/transcriptions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare audio file for upload
        with open(audio_file, 'rb') as f:
            files = {
                'file': (audio_file.name, f, 'audio/mpeg'),
                'model': (None, 'whisper-1'),
                'response_format': (None, 'verbose_json'),
                'timestamp_granularities[]': (None, 'segment')
            }
            
            # Add prompt for better transcription
            prompt = f"This is a transcript of a US Senate hearing: {hearing_info.get('hearing_title', 'Senate Hearing')}"
            files['prompt'] = (None, prompt)
            
            if progress_callback:
                progress_callback("processing", 50, "Sending to OpenAI Whisper API...")
            
            response = requests.post(url, headers=headers, files=files, timeout=300)
        
        if response.status_code != 200:
            raise Exception(f"Whisper API error: {response.status_code} - {response.text}")
        
        whisper_result = response.json()
        
        if progress_callback:
            progress_callback("processing", 80, "Processing Whisper API response...")
        
        # Convert to our format
        transcript_data = {
            'hearing_id': hearing_info['id'],
            'hearing_title': hearing_info['hearing_title'],
            'committee_code': hearing_info['committee_code'],
            'hearing_date': hearing_info['hearing_date'],
            'transcription': {
                'text': whisper_result.get('text', ''),
                'segments': [],
                'language': whisper_result.get('language', 'en'),
                'duration': whisper_result.get('duration', 0)
            },
            'metadata': {
                'transcription_timestamp': datetime.now().isoformat(),
                'source': 'openai_whisper_direct',
                'model': 'whisper-1',
                'audio_file': str(audio_file)
            }
        }
        
        # Process segments
        for segment in whisper_result.get('segments', []):
            transcript_data['transcription']['segments'].append({
                'start': segment.get('start', 0),
                'end': segment.get('end', 0),
                'text': segment.get('text', ''),
                'speaker': 'Unknown',  # Default speaker
                'confidence': 1.0,
                'review_metadata': {
                    'needs_review': False,
                    'has_correction': False,
                    'reviewer': None,
                    'review_timestamp': None
                }
            })
        
        return transcript_data
    
    def _find_audio_file(self, hearing_id):
        """Find audio file for a hearing."""
        base_dir = Path(__file__).parent / 'output'
        
        # Search patterns for audio files
        patterns = [
            f'hearing_{hearing_id}/*.mp3',
            f'hearing_{hearing_id}/*.wav',
            f'hearing_{hearing_id}/*.m4a',
            f'real_audio/hearing_{hearing_id}/*.mp3',
            f'real_audio/hearing_{hearing_id}/*.wav',
            f'preprocessed_audio/hearing_{hearing_id}/*.mp3',
            f'preprocessed_audio/hearing_{hearing_id}/*.wav',
        ]
        
        for pattern in patterns:
            matches = list(base_dir.glob(pattern))
            if matches:
                return matches[0]
        
        # If no specific hearing files, use the latest real audio file as demo
        real_audio_files = list((base_dir / 'real_audio').glob('*.mp3'))
        if real_audio_files:
            return real_audio_files[0]
        
        return None
    
    def _get_hearing_info(self, hearing_id):
        """Get hearing information from database."""
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
    
    def _update_database_transcript(self, hearing_id, transcript_data):
        """Update database with transcript content."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store full transcript text in database
        full_text = transcript_data['transcription']['text']
        
        cursor.execute('''
            UPDATE hearings_unified 
            SET full_text_content = ?
            WHERE id = ?
        ''', (full_text, hearing_id))
        
        conn.commit()
        conn.close()

def main():
    """Test the enhanced transcription service with chunked processing."""
    service = EnhancedTranscriptionService()
    
    # Test with a hearing that has 'captured' status
    conn = sqlite3.connect(service.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, hearing_title FROM hearings_unified WHERE processing_stage = 'captured' LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        hearing_id, title = result
        print(f"🎵 Testing enhanced transcription for hearing {hearing_id}: {title}")
        
        # Progress callback function
        def progress_callback(stage, percent, message):
            print(f"📊 {stage.upper()}: {percent}% - {message}")
        
        try:
            transcript = service.transcribe_hearing(hearing_id, progress_callback=progress_callback)
            
            print(f"\n✅ Enhanced transcription successful!")
            print(f"📊 Results:")
            print(f"   Segments: {len(transcript['transcription']['segments'])}")
            print(f"   Duration: {transcript['transcription']['duration']:.1f} seconds")
            print(f"   Text length: {len(transcript['transcription']['text'])} characters")
            print(f"   Source: {transcript['metadata']['source']}")
            
            if 'chunking_info' in transcript['metadata']:
                chunking = transcript['metadata']['chunking_info']
                print(f"   Chunks processed: {chunking['total_chunks']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Enhanced transcription failed: {e}")
            return False
    else:
        print("No hearings with 'captured' status found for testing")
        return False

if __name__ == "__main__":
    main()