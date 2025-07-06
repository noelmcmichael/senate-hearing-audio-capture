#!/usr/bin/env python3
"""
Enhanced async transcription service with parallel processing capabilities.
Implements concurrent chunk processing with rate limiting and resource optimization.
"""

import os
import json
import sqlite3
import requests
import asyncio
import aiohttp
import time
import random
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import keyring
import logging

from audio_analyzer import AudioAnalyzer
from audio_chunker import AudioChunker, ChunkingResult, AudioChunk
from progress_tracker import progress_tracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TokenBucket:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, capacity: int = 20, refill_rate: float = 20/60):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens per second refill rate
        """
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
        
    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens with async waiting."""
        async with self.lock:
            while True:
                now = time.time()
                # Refill tokens based on time elapsed
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, 
                                 self.tokens + elapsed * self.refill_rate)
                self.last_refill = now
                
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    break
                    
                # Wait for token availability
                wait_time = (tokens - self.tokens) / self.refill_rate
                await asyncio.sleep(min(wait_time, 1.0))

class ParallelProgressTracker:
    """Enhanced progress tracker for parallel processing."""
    
    def __init__(self, hearing_id: int):
        """Initialize parallel progress tracker."""
        self.hearing_id = hearing_id
        self.chunk_states = {}
        self.processing_start_times = {}
        self.chunk_velocities = {}
        self.start_time = time.time()
        self.lock = asyncio.Lock()
        
        # Stage weights for overall progress calculation
        self.stage_weights = {
            'analyzing': 0.10,
            'chunking': 0.15,
            'processing': 0.70,
            'merging': 0.15,
            'cleanup': 0.05
        }
        
    async def start_chunk_processing(self, chunk_index: int):
        """Mark chunk processing as started."""
        async with self.lock:
            self.processing_start_times[chunk_index] = time.time()
            self.chunk_states[chunk_index] = {
                'state': 'processing',
                'timestamp': time.time(),
                'progress': 0
            }
            await self._update_overall_progress()
            
    async def update_chunk_progress(self, chunk_index: int, progress: float):
        """Update progress for a specific chunk."""
        async with self.lock:
            if chunk_index in self.chunk_states:
                self.chunk_states[chunk_index].update({
                    'progress': progress,
                    'timestamp': time.time()
                })
                await self._update_overall_progress()
                
    async def complete_chunk(self, chunk_index: int, result: Any = None):
        """Mark chunk as completed."""
        async with self.lock:
            start_time = self.processing_start_times.get(chunk_index)
            if start_time:
                duration = time.time() - start_time
                self.chunk_velocities[chunk_index] = duration
                
            self.chunk_states[chunk_index] = {
                'state': 'completed',
                'timestamp': time.time(),
                'progress': 100,
                'result': result
            }
            await self._update_overall_progress()
            
    async def fail_chunk(self, chunk_index: int, error: str):
        """Mark chunk as failed."""
        async with self.lock:
            self.chunk_states[chunk_index] = {
                'state': 'failed',
                'timestamp': time.time(),
                'progress': 0,
                'error': error
            }
            await self._update_overall_progress()
            
    async def _update_overall_progress(self):
        """Calculate and update overall progress."""
        if not self.chunk_states:
            return
            
        total_chunks = len(self.chunk_states)
        completed = sum(1 for state in self.chunk_states.values() 
                       if state['state'] == 'completed')
        processing = sum(1 for state in self.chunk_states.values() 
                        if state['state'] == 'processing')
        failed = sum(1 for state in self.chunk_states.values() 
                    if state['state'] == 'failed')
                    
        # Calculate progress considering partial completion of processing chunks
        processing_progress = sum(
            state.get('progress', 0) / 100 
            for state in self.chunk_states.values() 
            if state['state'] == 'processing'
        )
        
        # Overall progress calculation
        progress = (completed + processing_progress) / total_chunks * 100
        
        # Calculate estimated time remaining
        eta = self._calculate_eta(completed, processing, total_chunks)
        
        # Update progress tracker
        chunk_progress = {
            'current_chunk': processing,
            'total_chunks': total_chunks,
            'completed_chunks': completed,
            'failed_chunks': failed,
            'chunk_progress': int(progress)
        }
        
        progress_tracker.update_progress(
            hearing_id=self.hearing_id,
            stage='processing',
            overall_progress=int(progress),
            message=f"Processing chunk {completed + processing} of {total_chunks}",
            chunk_progress=chunk_progress,
            estimated_time_remaining=eta
        )
        
    def _calculate_eta(self, completed: int, processing: int, total_chunks: int) -> Optional[int]:
        """Calculate estimated time remaining."""
        if not self.chunk_velocities:
            return None
            
        # Average processing time per chunk
        avg_time = sum(self.chunk_velocities.values()) / len(self.chunk_velocities)
        
        # Remaining chunks
        remaining = total_chunks - completed
        
        # Adjust for parallel processing
        concurrent_factor = min(3, remaining)  # Max 3 concurrent
        estimated_seconds = (remaining * avg_time) / concurrent_factor
        
        return int(estimated_seconds)

class IntelligentRetryManager:
    """Advanced retry logic with pattern recognition."""
    
    def __init__(self):
        """Initialize retry manager."""
        self.retry_patterns = {
            'rate_limit': {'max_retries': 5, 'base_delay': 60},
            'network_error': {'max_retries': 3, 'base_delay': 5},
            'api_error': {'max_retries': 2, 'base_delay': 10},
            'chunk_corruption': {'max_retries': 1, 'base_delay': 0}
        }
        self.error_history = defaultdict(list)
        
    async def retry_with_intelligence(self, operation, chunk_index: int, error: Exception):
        """Intelligent retry based on error patterns."""
        error_type = self._classify_error(error)
        retry_config = self.retry_patterns.get(error_type, 
                                             self.retry_patterns['api_error'])
        
        # Check retry history
        history_key = f"{chunk_index}:{error_type}"
        retry_count = len(self.error_history[history_key])
        
        if retry_count >= retry_config['max_retries']:
            raise Exception(
                f"Max retries exceeded for chunk {chunk_index}: {error}"
            )
            
        # Calculate delay with jitter
        delay = retry_config['base_delay'] * (2 ** retry_count)
        jitter = random.uniform(0.1, 0.3) * delay
        total_delay = delay + jitter
        
        # Record attempt
        self.error_history[history_key].append({
            'timestamp': time.time(),
            'error': str(error),
            'delay': total_delay
        })
        
        logger.info(f"Retrying chunk {chunk_index} after {total_delay:.1f}s delay")
        
        # Wait and retry
        await asyncio.sleep(total_delay)
        return await operation()
        
    def _classify_error(self, error: Exception) -> str:
        """Classify error type for appropriate retry strategy."""
        error_str = str(error).lower()
        
        if 'rate limit' in error_str or '429' in error_str:
            return 'rate_limit'
        elif 'network' in error_str or 'timeout' in error_str:
            return 'network_error'
        elif 'chunk' in error_str or 'corruption' in error_str:
            return 'chunk_corruption'
        else:
            return 'api_error'

class ResourcePool:
    """Efficient resource pooling for audio processing."""
    
    def __init__(self, max_temp_dirs: int = 5):
        """Initialize resource pool."""
        self.temp_dir_pool = []
        self.max_temp_dirs = max_temp_dirs
        self.temp_dir_counter = 0
        
    async def get_temp_directory(self) -> Path:
        """Get or create temporary directory from pool."""
        if self.temp_dir_pool:
            temp_dir = self.temp_dir_pool.pop()
        else:
            temp_dir = self._create_temp_directory()
        
        return temp_dir
        
    async def return_temp_directory(self, temp_dir: Path):
        """Return cleaned temporary directory to pool."""
        try:
            # Clean directory contents
            for item in temp_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
                    
            # Return to pool if under limit
            if len(self.temp_dir_pool) < self.max_temp_dirs:
                self.temp_dir_pool.append(temp_dir)
            else:
                shutil.rmtree(temp_dir)
                
        except Exception as e:
            logger.warning(f"Error cleaning temp directory {temp_dir}: {e}")
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
                
    def _create_temp_directory(self) -> Path:
        """Create new temporary directory."""
        self.temp_dir_counter += 1
        temp_dir = Path(f"/tmp/audio_processing_{os.getpid()}_{self.temp_dir_counter}")
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

class EnhancedAsyncTranscriptionService:
    """Enhanced transcription service with parallel processing capabilities."""
    
    def __init__(self, db_path=None, max_concurrent_chunks: int = 3):
        """
        Initialize the enhanced async transcription service.
        
        Args:
            db_path: Database path for storing transcription metadata
            max_concurrent_chunks: Maximum chunks to process concurrently
        """
        self.db_path = db_path or Path(__file__).parent / 'data' / 'demo_enhanced_ui.db'
        self.output_dir = Path(__file__).parent / 'output' / 'demo_transcription'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.analyzer = AudioAnalyzer()
        self.chunker = AudioChunker()
        
        # Parallel processing configuration
        self.max_concurrent_chunks = max_concurrent_chunks
        self.chunk_semaphore = asyncio.Semaphore(max_concurrent_chunks)
        self.rate_limiter = TokenBucket(capacity=20, refill_rate=20/60)
        
        # Resource management
        self.resource_pool = ResourcePool()
        self.retry_manager = IntelligentRetryManager()
        
        # Get OpenAI API key from keyring
        self.api_key = self._get_openai_key()
        
        # Configuration
        self.max_file_size_mb = 20  # 5MB buffer under OpenAI's 25MB limit
        
    def _get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key from keyring storage."""
        try:
            # Try different case variations
            for key_name in ['OpenAI Key', 'OPENAI_API_KEY', 'openai_api_key', 'OpenAI_API_KEY']:
                try:
                    key = keyring.get_password('memex', key_name)
                    if key:
                        return key
                except Exception:
                    continue
            
            logger.warning("OpenAI API key not found in keyring")
            return None
            
        except Exception as e:
            logger.error(f"Error accessing keyring: {e}")
            return None
    
    async def transcribe_audio_parallel(self, audio_path: str, hearing_id: int) -> Dict[str, Any]:
        """
        Transcribe audio with parallel processing for large files.
        
        Args:
            audio_path: Path to audio file
            hearing_id: Hearing ID for progress tracking
            
        Returns:
            Transcription result with metadata
        """
        logger.info(f"Starting parallel transcription for hearing {hearing_id}")
        
        # Initialize progress tracking
        progress_tracker.start_operation(hearing_id, 'transcription')
        parallel_tracker = ParallelProgressTracker(hearing_id)
        
        try:
            # Step 1: Analyze audio
            progress_tracker.update_progress(
                hearing_id, 'analyzing', 5, 'Analyzing audio file...'
            )
            
            audio_info = self.analyzer.analyze_audio(audio_path)
            logger.info(f"Audio analysis: {audio_info.duration_seconds}s, {audio_info.file_size_mb}MB")
            
            # Step 2: Determine processing approach
            if audio_info.file_size_mb <= self.max_file_size_mb:
                # Direct processing for small files
                logger.info("File is small enough for direct processing")
                return await self._transcribe_direct(audio_path, hearing_id)
            else:
                # Chunked processing for large files
                logger.info("File requires chunked processing")
                return await self._transcribe_chunked_parallel(
                    audio_path, hearing_id, audio_info, parallel_tracker
                )
                
        except Exception as e:
            logger.error(f"Transcription failed for hearing {hearing_id}: {e}")
            progress_tracker.complete_operation(hearing_id, False, str(e))
            raise
    
    async def _transcribe_direct(self, audio_path: str, hearing_id: int) -> Dict[str, Any]:
        """Direct transcription for small files."""
        progress_tracker.update_progress(
            hearing_id, 'processing', 50, 'Transcribing audio...'
        )
        
        result = await self._call_whisper_api(audio_path)
        
        # Save transcript
        transcript_path = self.output_dir / f"hearing_{hearing_id}_transcript.json"
        with open(transcript_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        progress_tracker.complete_operation(hearing_id, True)
        
        return {
            'transcript_path': str(transcript_path),
            'segments_count': len(result.get('segments', [])),
            'processing_method': 'direct'
        }
    
    async def _transcribe_chunked_parallel(
        self, 
        audio_path: str, 
        hearing_id: int, 
        audio_info, 
        parallel_tracker: ParallelProgressTracker
    ) -> Dict[str, Any]:
        """Parallel chunked transcription for large files."""
        
        # Step 1: Create chunks
        progress_tracker.update_progress(
            hearing_id, 'chunking', 15, 'Creating audio chunks...'
        )
        
        temp_dir = await self.resource_pool.get_temp_directory()
        try:
            chunking_result = self.chunker.chunk_audio(audio_path, str(temp_dir))
            logger.info(f"Created {len(chunking_result.chunks)} chunks")
            
            # Step 2: Process chunks in parallel
            progress_tracker.update_progress(
                hearing_id, 'processing', 20, 'Starting parallel chunk processing...',
                chunk_progress={
                    'current_chunk': 0,
                    'total_chunks': len(chunking_result.chunks),
                    'completed_chunks': 0,
                    'failed_chunks': 0,
                    'chunk_progress': 0
                }
            )
            
            # Process chunks concurrently
            tasks = []
            for i, chunk in enumerate(chunking_result.chunks):
                task = self._process_chunk_with_limits(
                    chunk, i, len(chunking_result.chunks), parallel_tracker
                )
                tasks.append(task)
            
            # Execute with controlled concurrency
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for failures
            failures = [r for r in results if isinstance(r, Exception)]
            if failures:
                raise Exception(f"Failed to process {len(failures)} chunks: {failures[0]}")
            
            # Step 3: Merge results
            progress_tracker.update_progress(
                hearing_id, 'merging', 85, 'Merging chunk transcripts...'
            )
            
            merged_transcript = self._merge_chunk_results(results, chunking_result)
            
            # Step 4: Save final transcript
            transcript_path = self.output_dir / f"hearing_{hearing_id}_transcript.json"
            with open(transcript_path, 'w') as f:
                json.dump(merged_transcript, f, indent=2)
            
            # Step 5: Cleanup
            progress_tracker.update_progress(
                hearing_id, 'cleanup', 95, 'Cleaning up temporary files...'
            )
            
            progress_tracker.complete_operation(hearing_id, True)
            
            return {
                'transcript_path': str(transcript_path),
                'segments_count': len(merged_transcript.get('segments', [])),
                'processing_method': 'chunked_parallel',
                'chunks_processed': len(results),
                'total_duration': merged_transcript.get('duration', 0)
            }
            
        finally:
            await self.resource_pool.return_temp_directory(temp_dir)
    
    async def _process_chunk_with_limits(
        self, 
        chunk: AudioChunk, 
        chunk_index: int, 
        total_chunks: int,
        parallel_tracker: ParallelProgressTracker
    ) -> Dict[str, Any]:
        """Process single chunk with rate limiting and error isolation."""
        
        async with self.chunk_semaphore:  # Limit concurrency
            await parallel_tracker.start_chunk_processing(chunk_index)
            
            try:
                # Acquire rate limit token
                await self.rate_limiter.acquire()
                
                # Process chunk with retry logic
                async def process_operation():
                    result = await self._call_whisper_api(chunk.file_path)
                    await parallel_tracker.update_chunk_progress(chunk_index, 100)
                    return result
                
                try:
                    result = await process_operation()
                except Exception as e:
                    # Retry with intelligent backoff
                    result = await self.retry_manager.retry_with_intelligence(
                        process_operation, chunk_index, e
                    )
                
                await parallel_tracker.complete_chunk(chunk_index, result)
                
                logger.info(f"Completed chunk {chunk_index + 1}/{total_chunks}")
                return result
                
            except Exception as e:
                logger.error(f"Failed to process chunk {chunk_index}: {e}")
                await parallel_tracker.fail_chunk(chunk_index, str(e))
                raise
    
    async def _call_whisper_api(self, audio_path: str) -> Dict[str, Any]:
        """Call OpenAI Whisper API with async HTTP client."""
        if not self.api_key:
            raise Exception("OpenAI API key not available")
        
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        
        # Prepare file data
        with open(audio_path, 'rb') as audio_file:
            files = {
                'file': audio_file,
                'model': (None, 'whisper-1')
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/audio/transcriptions',
                    headers=headers,
                    data=files
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"API call failed: {response.status} - {error_text}")
    
    def _merge_chunk_results(self, results: List[Dict], chunking_result: ChunkingResult) -> Dict[str, Any]:
        """Merge chunk transcription results into final transcript."""
        merged_segments = []
        total_duration = 0
        
        for i, (result, chunk) in enumerate(zip(results, chunking_result.chunks)):
            if 'segments' in result:
                for segment in result['segments']:
                    # Adjust timestamps for chunk offset
                    adjusted_segment = segment.copy()
                    adjusted_segment['start'] = segment['start'] + chunk.start_time
                    adjusted_segment['end'] = segment['end'] + chunk.start_time
                    
                    merged_segments.append(adjusted_segment)
                    total_duration = max(total_duration, adjusted_segment['end'])
        
        # Sort segments by start time
        merged_segments.sort(key=lambda x: x['start'])
        
        return {
            'text': ' '.join([seg['text'] for seg in merged_segments]),
            'segments': merged_segments,
            'duration': total_duration,
            'language': results[0].get('language', 'en') if results else 'en',
            'processing_metadata': {
                'chunks_processed': len(results),
                'total_chunks': len(chunking_result.chunks),
                'processing_method': 'parallel_chunked',
                'processed_at': datetime.now().isoformat()
            }
        }

# Global instance
enhanced_async_service = EnhancedAsyncTranscriptionService()

async def transcribe_hearing_async(audio_path: str, hearing_id: int) -> Dict[str, Any]:
    """
    Async wrapper for transcribing hearing audio.
    
    Args:
        audio_path: Path to audio file
        hearing_id: Hearing ID for progress tracking
        
    Returns:
        Transcription result with metadata
    """
    return await enhanced_async_service.transcribe_audio_parallel(audio_path, hearing_id)

if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Example usage
        service = EnhancedAsyncTranscriptionService()
        
        # Test with a sample audio file
        audio_path = "path/to/your/audio.wav"
        hearing_id = 999
        
        try:
            result = await service.transcribe_audio_parallel(audio_path, hearing_id)
            print(f"Transcription completed: {result}")
        except Exception as e:
            print(f"Transcription failed: {e}")
    
    # Uncomment to run example
    # asyncio.run(main())