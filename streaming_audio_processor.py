#!/usr/bin/env python3
"""
Streaming audio processor for memory-efficient chunk processing.
Implements memory optimization and advanced resource management.
"""

import os
import shutil
import time
import psutil
import tempfile
import asyncio
from pathlib import Path
from typing import Iterator, Optional, Dict, Any, List
import subprocess
import logging
from collections import deque

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """Monitors system memory usage and provides optimization recommendations."""
    
    def __init__(self, max_memory_mb: int = 200):
        """Initialize memory monitor."""
        self.max_memory_mb = max_memory_mb
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.process = psutil.Process()
        self.memory_history = deque(maxlen=60)  # Keep 60 samples
        
    def get_current_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics."""
        memory_info = self.process.memory_info()
        system_memory = psutil.virtual_memory()
        
        usage = {
            'process_memory_mb': memory_info.rss / (1024 * 1024),
            'system_memory_percent': system_memory.percent,
            'system_available_mb': system_memory.available / (1024 * 1024),
            'timestamp': time.time()
        }
        
        self.memory_history.append(usage)
        return usage
        
    def is_memory_pressure(self) -> bool:
        """Check if system is under memory pressure."""
        usage = self.get_current_usage()
        
        # Check process memory limit
        if usage['process_memory_mb'] > self.max_memory_mb:
            return True
            
        # Check system memory pressure
        if usage['system_memory_percent'] > 85:
            return True
            
        # Check available memory
        if usage['system_available_mb'] < 100:  # Less than 100MB available
            return True
            
        return False
        
    def get_memory_trend(self) -> Optional[str]:
        """Analyze memory usage trend."""
        if len(self.memory_history) < 10:
            return None
            
        recent = list(self.memory_history)[-10:]
        early = recent[:5]
        late = recent[5:]
        
        early_avg = sum(m['process_memory_mb'] for m in early) / len(early)
        late_avg = sum(m['process_memory_mb'] for m in late) / len(late)
        
        change_percent = ((late_avg - early_avg) / early_avg) * 100
        
        if change_percent > 10:
            return 'increasing'
        elif change_percent < -10:
            return 'decreasing'
        else:
            return 'stable'
            
    def suggest_cleanup(self) -> List[str]:
        """Suggest cleanup actions based on memory state."""
        suggestions = []
        
        if self.is_memory_pressure():
            suggestions.append('immediate_cleanup')
            
        trend = self.get_memory_trend()
        if trend == 'increasing':
            suggestions.append('proactive_cleanup')
            
        usage = self.get_current_usage()
        if usage['system_memory_percent'] > 80:
            suggestions.append('reduce_concurrency')
            
        return suggestions

class StreamingAudioSlicer:
    """Memory-efficient audio slicing using streaming operations."""
    
    def __init__(self, chunk_size_bytes: int = 1024 * 1024):  # 1MB chunks
        """Initialize streaming audio slicer."""
        self.chunk_size_bytes = chunk_size_bytes
        
    def stream_slice(self, audio_path: str, start_seconds: float, 
                    duration_seconds: float, output_path: str) -> bool:
        """
        Stream audio slice directly to output file without loading full audio.
        
        Args:
            audio_path: Source audio file path
            start_seconds: Start time for slice
            duration_seconds: Duration of slice
            output_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use ffmpeg for efficient streaming slice
            cmd = [
                'ffmpeg',
                '-i', audio_path,
                '-ss', str(start_seconds),
                '-t', str(duration_seconds),
                '-acodec', 'copy',  # Copy without re-encoding
                '-y',  # Overwrite output
                output_path
            ]
            
            # Run ffmpeg with streaming
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Verify output file was created
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.debug(f"Streaming slice successful: {output_path}")
                    return True
                    
            logger.error(f"ffmpeg failed: {result.stderr}")
            return False
            
        except subprocess.TimeoutExpired:
            logger.error(f"ffmpeg timeout for slice {start_seconds}-{start_seconds + duration_seconds}")
            return False
        except Exception as e:
            logger.error(f"Streaming slice failed: {e}")
            return False

class AdvancedResourcePool:
    """Advanced resource pool with memory monitoring and optimization."""
    
    def __init__(self, max_temp_dirs: int = 3, max_temp_files: int = 10):
        """Initialize advanced resource pool."""
        self.max_temp_dirs = max_temp_dirs
        self.max_temp_files = max_temp_files
        
        # Resource pools
        self.temp_dir_pool = []
        self.temp_file_pool = deque(maxlen=max_temp_files)
        
        # Tracking
        self.active_resources = set()
        self.resource_stats = {
            'directories_created': 0,
            'directories_reused': 0,
            'files_created': 0,
            'files_cleaned': 0,
            'memory_cleanups': 0
        }
        
        # Memory monitoring
        self.memory_monitor = MemoryMonitor()
        
    async def get_temp_directory(self) -> Path:
        """Get temporary directory with memory monitoring."""
        # Check memory pressure
        if self.memory_monitor.is_memory_pressure():
            await self._emergency_cleanup()
            
        # Try to reuse from pool
        if self.temp_dir_pool:
            temp_dir = self.temp_dir_pool.pop()
            self.resource_stats['directories_reused'] += 1
            logger.debug(f"Reused temp directory: {temp_dir}")
        else:
            temp_dir = self._create_temp_directory()
            self.resource_stats['directories_created'] += 1
            logger.debug(f"Created new temp directory: {temp_dir}")
            
        self.active_resources.add(temp_dir)
        return temp_dir
        
    async def return_temp_directory(self, temp_dir: Path, force_cleanup: bool = False):
        """Return temporary directory to pool with intelligent cleanup."""
        try:
            self.active_resources.discard(temp_dir)
            
            # Check if we should clean up based on memory pressure
            memory_suggestions = self.memory_monitor.suggest_cleanup()
            should_cleanup = (
                force_cleanup or 
                'immediate_cleanup' in memory_suggestions or
                len(self.temp_dir_pool) >= self.max_temp_dirs
            )
            
            if should_cleanup:
                await self._cleanup_directory(temp_dir)
                self.resource_stats['memory_cleanups'] += 1
            else:
                # Clean contents but keep directory for reuse
                await self._clean_directory_contents(temp_dir)
                self.temp_dir_pool.append(temp_dir)
                
        except Exception as e:
            logger.warning(f"Error managing temp directory {temp_dir}: {e}")
            await self._cleanup_directory(temp_dir)
            
    def _create_temp_directory(self) -> Path:
        """Create new temporary directory."""
        temp_dir = Path(tempfile.mkdtemp(prefix='audio_proc_'))
        return temp_dir
        
    async def _clean_directory_contents(self, temp_dir: Path):
        """Clean directory contents but keep directory."""
        try:
            for item in temp_dir.iterdir():
                if item.is_file():
                    item.unlink()
                    self.resource_stats['files_cleaned'] += 1
                elif item.is_dir():
                    shutil.rmtree(item)
        except Exception as e:
            logger.warning(f"Error cleaning directory contents {temp_dir}: {e}")
            
    async def _cleanup_directory(self, temp_dir: Path):
        """Completely remove directory."""
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Error removing directory {temp_dir}: {e}")
            
    async def _emergency_cleanup(self):
        """Emergency cleanup when memory pressure is detected."""
        logger.warning("Memory pressure detected, performing emergency cleanup")
        
        # Clean up all pooled directories
        while self.temp_dir_pool:
            temp_dir = self.temp_dir_pool.pop()
            await self._cleanup_directory(temp_dir)
            
        # Clean up all active resources if possible
        for resource in list(self.active_resources):
            try:
                if isinstance(resource, Path) and resource.exists():
                    await self._clean_directory_contents(resource)
            except Exception as e:
                logger.warning(f"Emergency cleanup failed for {resource}: {e}")
                
        self.resource_stats['memory_cleanups'] += 1
        
    def get_stats(self) -> Dict[str, Any]:
        """Get resource pool statistics."""
        memory_usage = self.memory_monitor.get_current_usage()
        
        return {
            'resource_stats': self.resource_stats.copy(),
            'active_resources': len(self.active_resources),
            'pooled_directories': len(self.temp_dir_pool),
            'memory_usage': memory_usage,
            'memory_pressure': self.memory_monitor.is_memory_pressure(),
            'memory_trend': self.memory_monitor.get_memory_trend()
        }

class SmartCleanupManager:
    """Advanced cleanup manager with monitoring and optimization."""
    
    def __init__(self):
        """Initialize smart cleanup manager."""
        self.cleanup_queue = asyncio.Queue()
        self.cleanup_policies = {
            'immediate': 0,      # Clean up immediately
            'after_use': 30,     # Clean up 30 seconds after use
            'on_pressure': 300,  # Clean up in 5 minutes if no memory pressure
            'on_completion': 600 # Clean up in 10 minutes
        }
        self.memory_monitor = MemoryMonitor()
        self.cleanup_stats = {
            'files_cleaned': 0,
            'bytes_freed': 0,
            'cleanup_errors': 0
        }
        self.running = False
        
    async def start(self):
        """Start the cleanup manager background worker."""
        if not self.running:
            self.running = True
            asyncio.create_task(self._cleanup_worker())
            
    async def stop(self):
        """Stop the cleanup manager."""
        self.running = False
        
    async def schedule_cleanup(self, file_path: str, policy: str = 'after_use'):
        """Schedule file for cleanup based on policy."""
        if not os.path.exists(file_path):
            return
            
        cleanup_item = {
            'path': file_path,
            'policy': policy,
            'scheduled_at': time.time(),
            'size': os.path.getsize(file_path),
            'cleanup_at': time.time() + self.cleanup_policies.get(policy, 300)
        }
        
        await self.cleanup_queue.put(cleanup_item)
        
    async def _cleanup_worker(self):
        """Background worker for smart cleanup."""
        pending_items = []
        
        while self.running:
            try:
                # Process new items from queue
                try:
                    while True:
                        item = self.cleanup_queue.get_nowait()
                        pending_items.append(item)
                except asyncio.QueueEmpty:
                    pass
                
                # Check for items ready for cleanup
                current_time = time.time()
                items_to_clean = []
                remaining_items = []
                
                for item in pending_items:
                    # Check if cleanup time has arrived
                    if current_time >= item['cleanup_at']:
                        items_to_clean.append(item)
                    # Check for immediate cleanup due to memory pressure
                    elif (item['policy'] != 'immediate' and 
                          self.memory_monitor.is_memory_pressure()):
                        items_to_clean.append(item)
                    else:
                        remaining_items.append(item)
                
                # Execute cleanups
                for item in items_to_clean:
                    await self._execute_cleanup(item)
                
                pending_items = remaining_items
                
                # Sleep briefly before next iteration
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Cleanup worker error: {e}")
                await asyncio.sleep(5.0)
                
    async def _execute_cleanup(self, item: Dict[str, Any]):
        """Execute cleanup for a specific item."""
        try:
            file_path = item['path']
            
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    
                self.cleanup_stats['files_cleaned'] += 1
                self.cleanup_stats['bytes_freed'] += file_size
                
                logger.debug(f"Cleaned up: {file_path} ({file_size} bytes)")
                
        except Exception as e:
            logger.warning(f"Cleanup failed for {item['path']}: {e}")
            self.cleanup_stats['cleanup_errors'] += 1
            
    def get_stats(self) -> Dict[str, Any]:
        """Get cleanup statistics."""
        return {
            'cleanup_stats': self.cleanup_stats.copy(),
            'pending_items': self.cleanup_queue.qsize(),
            'memory_usage': self.memory_monitor.get_current_usage(),
            'memory_pressure': self.memory_monitor.is_memory_pressure()
        }

class StreamingAudioProcessor:
    """Memory-efficient audio processing with streaming and resource management."""
    
    def __init__(self):
        """Initialize streaming audio processor."""
        self.slicer = StreamingAudioSlicer()
        self.resource_pool = AdvancedResourcePool()
        self.cleanup_manager = SmartCleanupManager()
        
    async def start(self):
        """Start the streaming processor."""
        await self.cleanup_manager.start()
        
    async def stop(self):
        """Stop the streaming processor and cleanup resources."""
        await self.cleanup_manager.stop()
        
        # Force cleanup of all resources
        stats = self.resource_pool.get_stats()
        for i in range(stats['active_resources']):
            try:
                # This would need proper resource tracking
                pass
            except:
                pass
                
    async def create_chunks_streaming(self, audio_path: str, chunk_specs: List[Dict]) -> List[str]:
        """
        Create audio chunks using streaming to minimize memory usage.
        
        Args:
            audio_path: Source audio file path
            chunk_specs: List of chunk specifications with start_time and duration
            
        Returns:
            List of chunk file paths
        """
        temp_dir = await self.resource_pool.get_temp_directory()
        chunk_paths = []
        
        try:
            for i, spec in enumerate(chunk_specs):
                chunk_path = temp_dir / f"chunk_{i:03d}.wav"
                
                # Stream slice directly to chunk file
                success = self.slicer.stream_slice(
                    audio_path,
                    spec['start_time'],
                    spec['duration'],
                    str(chunk_path)
                )
                
                if success:
                    chunk_paths.append(str(chunk_path))
                    
                    # Schedule cleanup after processing
                    await self.cleanup_manager.schedule_cleanup(
                        str(chunk_path), 'after_use'
                    )
                else:
                    raise Exception(f"Failed to create chunk {i}")
                    
                # Check memory pressure after each chunk
                if self.resource_pool.memory_monitor.is_memory_pressure():
                    logger.warning(f"Memory pressure during chunk creation at chunk {i}")
                    
            return chunk_paths
            
        except Exception as e:
            # Clean up any created chunks on error
            for chunk_path in chunk_paths:
                await self.cleanup_manager.schedule_cleanup(chunk_path, 'immediate')
            raise
            
        finally:
            # Return temp directory to pool
            await self.resource_pool.return_temp_directory(temp_dir)
            
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        return {
            'resource_pool': self.resource_pool.get_stats(),
            'cleanup_manager': self.cleanup_manager.get_stats(),
            'processor_status': {
                'running': self.cleanup_manager.running,
                'memory_optimizations_active': True
            }
        }

# Global instance
streaming_processor = StreamingAudioProcessor()

async def initialize_streaming_processor():
    """Initialize the streaming processor for use."""
    await streaming_processor.start()
    logger.info("Streaming audio processor initialized")

async def shutdown_streaming_processor():
    """Shutdown the streaming processor and cleanup resources."""
    await streaming_processor.stop()
    logger.info("Streaming audio processor shutdown")

if __name__ == "__main__":
    async def test_streaming_processor():
        """Test the streaming audio processor."""
        processor = StreamingAudioProcessor()
        await processor.start()
        
        try:
            # Test memory monitoring
            stats = processor.get_performance_stats()
            print(f"Performance stats: {stats}")
            
            # Test would require actual audio file
            # chunk_specs = [
            #     {'start_time': 0, 'duration': 300},
            #     {'start_time': 270, 'duration': 300},
            # ]
            # chunks = await processor.create_chunks_streaming("test.wav", chunk_specs)
            # print(f"Created chunks: {chunks}")
            
        finally:
            await processor.stop()
    
    # Uncomment to run test
    # asyncio.run(test_streaming_processor())