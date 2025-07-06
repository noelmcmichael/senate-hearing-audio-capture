#!/usr/bin/env python3
"""
Integration layer for async transcription service with existing system.
Provides backward compatibility while enabling parallel processing.
"""

import asyncio
import threading
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from enhanced_async_transcription_service import enhanced_async_service
from enhanced_transcription_service import EnhancedTranscriptionService

logger = logging.getLogger(__name__)

class AsyncTranscriptionIntegrator:
    """Integrates async transcription service with existing synchronous APIs."""
    
    def __init__(self):
        """Initialize the integration layer."""
        self.async_service = enhanced_async_service
        self.sync_service = EnhancedTranscriptionService()  # Fallback
        self.executor = None
        
    def start_async_support(self):
        """Start async support for transcription operations."""
        # Create event loop for async operations in separate thread
        if not self.executor:
            self.executor = AsyncExecutor()
            self.executor.start()
    
    def stop_async_support(self):
        """Stop async support and cleanup resources."""
        if self.executor:
            self.executor.stop()
            self.executor = None
    
    def transcribe_audio_sync(self, audio_path: str, hearing_id: int, use_parallel: bool = True) -> Dict[str, Any]:
        """
        Synchronous wrapper for audio transcription with optional parallel processing.
        
        Args:
            audio_path: Path to audio file
            hearing_id: Hearing ID for progress tracking
            use_parallel: Whether to use parallel processing for large files
            
        Returns:
            Transcription result with metadata
        """
        if use_parallel and self.executor:
            try:
                # Use async parallel processing
                logger.info(f"Using parallel processing for hearing {hearing_id}")
                return self.executor.run_async(
                    self.async_service.transcribe_audio_parallel(audio_path, hearing_id)
                )
            except Exception as e:
                logger.warning(f"Parallel processing failed, falling back to sync: {e}")
                # Fall back to synchronous processing
                return self.sync_service.transcribe_audio(audio_path, hearing_id)
        else:
            # Use synchronous processing
            logger.info(f"Using synchronous processing for hearing {hearing_id}")
            return self.sync_service.transcribe_audio(audio_path, hearing_id)
    
    async def transcribe_audio_async(self, audio_path: str, hearing_id: int) -> Dict[str, Any]:
        """
        Async interface for audio transcription.
        
        Args:
            audio_path: Path to audio file
            hearing_id: Hearing ID for progress tracking
            
        Returns:
            Transcription result with metadata
        """
        return await self.async_service.transcribe_audio_parallel(audio_path, hearing_id)

class AsyncExecutor:
    """Manages async event loop in separate thread for integration."""
    
    def __init__(self):
        """Initialize async executor."""
        self.loop = None
        self.thread = None
        self.running = False
        
    def start(self):
        """Start the async event loop in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            
            # Wait for loop to be ready
            while self.loop is None:
                import time
                time.sleep(0.01)
    
    def stop(self):
        """Stop the async event loop and cleanup."""
        if self.running:
            self.running = False
            if self.loop and not self.loop.is_closed():
                asyncio.run_coroutine_threadsafe(self._shutdown(), self.loop)
            if self.thread:
                self.thread.join(timeout=5.0)
    
    def _run_loop(self):
        """Run the event loop in the thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()
    
    async def _shutdown(self):
        """Shutdown the event loop gracefully."""
        # Cancel all running tasks
        tasks = [task for task in asyncio.all_tasks(self.loop) if not task.done()]
        if tasks:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop the loop
        self.loop.stop()
    
    def run_async(self, coro):
        """Run async coroutine from sync context."""
        if not self.loop or not self.running:
            raise RuntimeError("Async executor not running")
        
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()  # This will block until complete

# Global integrator instance
transcription_integrator = AsyncTranscriptionIntegrator()

def initialize_parallel_processing():
    """Initialize parallel processing capabilities."""
    try:
        transcription_integrator.start_async_support()
        logger.info("Parallel processing capabilities initialized")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize parallel processing: {e}")
        return False

def shutdown_parallel_processing():
    """Shutdown parallel processing capabilities."""
    try:
        transcription_integrator.stop_async_support()
        logger.info("Parallel processing capabilities shutdown")
    except Exception as e:
        logger.error(f"Error during parallel processing shutdown: {e}")

def transcribe_audio_with_optimization(
    audio_path: str, 
    hearing_id: int, 
    prefer_parallel: bool = True
) -> Dict[str, Any]:
    """
    Transcribe audio with automatic optimization selection.
    
    Args:
        audio_path: Path to audio file
        hearing_id: Hearing ID for progress tracking
        prefer_parallel: Whether to prefer parallel processing
        
    Returns:
        Transcription result with metadata
    """
    # Check file size to determine optimal approach
    file_size_mb = Path(audio_path).stat().st_size / (1024 * 1024)
    
    # Use parallel processing for files > 20MB if available
    use_parallel = prefer_parallel and file_size_mb > 20
    
    logger.info(f"Transcribing {file_size_mb:.1f}MB file, parallel={use_parallel}")
    
    return transcription_integrator.transcribe_audio_sync(
        audio_path, hearing_id, use_parallel
    )

if __name__ == "__main__":
    # Example usage and testing
    import time
    
    def test_integration():
        """Test the integration layer."""
        print("Testing async transcription integration...")
        
        # Initialize
        initialize_parallel_processing()
        
        try:
            # Test with mock data (would need real audio file)
            # result = transcribe_audio_with_optimization("test.wav", 999)
            # print(f"Result: {result}")
            
            print("Integration layer ready for use")
            
        finally:
            # Cleanup
            shutdown_parallel_processing()
    
    # Uncomment to run test
    # test_integration()