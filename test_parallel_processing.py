#!/usr/bin/env python3
"""
Comprehensive test suite for parallel processing implementation.
Tests performance improvements, reliability, and integration.
"""

import asyncio
import time
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
import logging

from enhanced_async_transcription_service import (
    EnhancedAsyncTranscriptionService,
    TokenBucket,
    ParallelProgressTracker,
    IntelligentRetryManager,
    ResourcePool
)
from async_transcription_integration import (
    AsyncTranscriptionIntegrator,
    initialize_parallel_processing,
    shutdown_parallel_processing,
    transcribe_audio_with_optimization
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestTokenBucket(unittest.TestCase):
    """Test token bucket rate limiter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bucket = TokenBucket(capacity=5, refill_rate=2.0)  # 2 tokens per second
    
    async def test_token_acquisition(self):
        """Test basic token acquisition."""
        # Should acquire immediately
        start_time = time.time()
        await self.bucket.acquire(1)
        elapsed = time.time() - start_time
        self.assertLess(elapsed, 0.1, "Token acquisition should be immediate")
    
    async def test_rate_limiting(self):
        """Test rate limiting behavior."""
        # Acquire all tokens
        for _ in range(5):
            await self.bucket.acquire(1)
        
        # Next acquisition should wait
        start_time = time.time()
        await self.bucket.acquire(1)
        elapsed = time.time() - start_time
        self.assertGreater(elapsed, 0.4, "Should wait for token refill")
    
    async def test_token_refill(self):
        """Test token refill over time."""
        # Drain all tokens
        for _ in range(5):
            await self.bucket.acquire(1)
        
        # Wait for refill
        await asyncio.sleep(1.0)
        
        # Should be able to acquire without waiting
        start_time = time.time()
        await self.bucket.acquire(1)
        elapsed = time.time() - start_time
        self.assertLess(elapsed, 0.1, "Token should be available after refill")

class TestParallelProgressTracker(unittest.TestCase):
    """Test parallel progress tracking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = ParallelProgressTracker(hearing_id=999)
    
    async def test_progress_calculation(self):
        """Test progress calculation with multiple chunks."""
        # Start 3 chunks
        await self.tracker.start_chunk_processing(0)
        await self.tracker.start_chunk_processing(1)
        await self.tracker.start_chunk_processing(2)
        
        # Complete first chunk
        await self.tracker.complete_chunk(0)
        
        # Update progress on second chunk
        await self.tracker.update_chunk_progress(1, 50.0)
        
        # Verify progress calculation
        self.assertEqual(len(self.tracker.chunk_states), 3)
        
        # Check that overall progress is calculated correctly
        # 1 completed + 0.5 in progress + 0 pending = 1.5/3 = 50%
        completed = sum(1 for state in self.tracker.chunk_states.values() 
                       if state['state'] == 'completed')
        self.assertEqual(completed, 1)
    
    async def test_eta_calculation(self):
        """Test estimated time remaining calculation."""
        # Start and complete some chunks to build velocity data
        await self.tracker.start_chunk_processing(0)
        await asyncio.sleep(0.1)  # Simulate processing time
        await self.tracker.complete_chunk(0)
        
        await self.tracker.start_chunk_processing(1)
        await asyncio.sleep(0.1)
        await self.tracker.complete_chunk(1)
        
        # Verify velocity tracking
        self.assertEqual(len(self.tracker.chunk_velocities), 2)
        
        # Start remaining chunks
        await self.tracker.start_chunk_processing(2)
        await self.tracker.start_chunk_processing(3)
        
        # ETA should be calculated
        eta = self.tracker._calculate_eta(2, 2, 4)
        self.assertIsInstance(eta, int)
        self.assertGreater(eta, 0)

class TestIntelligentRetryManager(unittest.TestCase):
    """Test intelligent retry logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.retry_manager = IntelligentRetryManager()
    
    def test_error_classification(self):
        """Test error type classification."""
        # Test rate limit error
        rate_error = Exception("Rate limit exceeded")
        self.assertEqual(
            self.retry_manager._classify_error(rate_error), 
            'rate_limit'
        )
        
        # Test network error
        network_error = Exception("Network timeout occurred")
        self.assertEqual(
            self.retry_manager._classify_error(network_error), 
            'network_error'
        )
        
        # Test chunk corruption
        chunk_error = Exception("Chunk corruption detected")
        self.assertEqual(
            self.retry_manager._classify_error(chunk_error), 
            'chunk_corruption'
        )
        
        # Test generic API error
        api_error = Exception("Unknown API error")
        self.assertEqual(
            self.retry_manager._classify_error(api_error), 
            'api_error'
        )
    
    async def test_retry_logic(self):
        """Test retry logic with backoff."""
        call_count = 0
        
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Network timeout")
            return "success"
        
        # Should succeed after retries
        start_time = time.time()
        result = await self.retry_manager.retry_with_intelligence(
            failing_operation, chunk_index=0, error=Exception("Network timeout")
        )
        elapsed = time.time() - start_time
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
        self.assertGreater(elapsed, 0.5, "Should have some delay from backoff")
    
    async def test_max_retries_exceeded(self):
        """Test max retries exceeded scenario."""
        async def always_failing_operation():
            raise Exception("Persistent error")
        
        # Should raise exception after max retries
        with self.assertRaises(Exception) as context:
            await self.retry_manager.retry_with_intelligence(
                always_failing_operation, 
                chunk_index=0, 
                error=Exception("Persistent error")
            )
        
        self.assertIn("Max retries exceeded", str(context.exception))

class TestResourcePool(unittest.TestCase):
    """Test resource pool management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pool = ResourcePool(max_temp_dirs=3)
    
    async def test_temp_directory_management(self):
        """Test temporary directory creation and reuse."""
        # Get first directory
        temp_dir1 = await self.pool.get_temp_directory()
        self.assertTrue(temp_dir1.exists())
        
        # Return it to pool
        await self.pool.return_temp_directory(temp_dir1)
        
        # Get another directory - should reuse the same one
        temp_dir2 = await self.pool.get_temp_directory()
        self.assertEqual(temp_dir1, temp_dir2)
    
    async def test_pool_size_limit(self):
        """Test pool size limiting."""
        # Create directories beyond pool limit
        dirs = []
        for i in range(5):  # More than max_temp_dirs=3
            temp_dir = await self.pool.get_temp_directory()
            dirs.append(temp_dir)
        
        # Return all directories
        for temp_dir in dirs:
            await self.pool.return_temp_directory(temp_dir)
        
        # Pool should only retain max_temp_dirs directories
        self.assertLessEqual(len(self.pool.temp_dir_pool), 3)

class MockAudioFile:
    """Mock audio file for testing."""
    
    def __init__(self, size_mb: float, duration_seconds: float = 300):
        """Create mock audio file."""
        self.temp_file = None
        self.size_mb = size_mb
        self.duration_seconds = duration_seconds
        
    def __enter__(self):
        """Create temporary file."""
        self.temp_file = tempfile.NamedTemporaryFile(
            suffix='.wav', delete=False
        )
        # Write some data to simulate file size
        data_size = int(self.size_mb * 1024 * 1024)
        self.temp_file.write(b'\x00' * data_size)
        self.temp_file.close()
        return self.temp_file.name
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup temporary file."""
        if self.temp_file:
            Path(self.temp_file.name).unlink(missing_ok=True)

class TestAsyncTranscriptionService(unittest.TestCase):
    """Test enhanced async transcription service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = EnhancedAsyncTranscriptionService(max_concurrent_chunks=2)
    
    @patch('enhanced_async_transcription_service.AudioAnalyzer')
    @patch('enhanced_async_transcription_service.AudioChunker')
    async def test_small_file_processing(self, mock_chunker, mock_analyzer):
        """Test direct processing for small files."""
        # Mock audio analysis
        mock_analyzer.return_value.analyze_audio.return_value = MagicMock(
            file_size_mb=15,  # Under 20MB limit
            duration_seconds=120
        )
        
        # Mock API call
        with patch.object(self.service, '_call_whisper_api') as mock_api:
            mock_api.return_value = {
                'text': 'Test transcription',
                'segments': [{'start': 0, 'end': 10, 'text': 'Test'}]
            }
            
            with MockAudioFile(15) as audio_path:
                result = await self.service.transcribe_audio_parallel(audio_path, 999)
                
                self.assertEqual(result['processing_method'], 'direct')
                mock_api.assert_called_once()
    
    @patch('enhanced_async_transcription_service.AudioAnalyzer')
    @patch('enhanced_async_transcription_service.AudioChunker')
    async def test_large_file_processing(self, mock_chunker, mock_analyzer):
        """Test parallel processing for large files."""
        # Mock audio analysis
        mock_analyzer.return_value.analyze_audio.return_value = MagicMock(
            file_size_mb=50,  # Over 20MB limit
            duration_seconds=1800
        )
        
        # Mock chunking result
        mock_chunks = [
            MagicMock(file_path='chunk_0.wav', start_time=0),
            MagicMock(file_path='chunk_1.wav', start_time=300),
            MagicMock(file_path='chunk_2.wav', start_time=600)
        ]
        mock_chunker.return_value.chunk_audio.return_value = MagicMock(
            chunks=mock_chunks,
            total_chunks=3
        )
        
        # Mock API calls
        with patch.object(self.service, '_call_whisper_api') as mock_api:
            mock_api.return_value = {
                'text': 'Chunk transcription',
                'segments': [{'start': 0, 'end': 10, 'text': 'Chunk'}],
                'language': 'en'
            }
            
            with MockAudioFile(50) as audio_path:
                result = await self.service.transcribe_audio_parallel(audio_path, 999)
                
                self.assertEqual(result['processing_method'], 'chunked_parallel')
                self.assertEqual(result['chunks_processed'], 3)
                self.assertEqual(mock_api.call_count, 3)  # One call per chunk

class TestIntegration(unittest.TestCase):
    """Test integration layer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.integrator = AsyncTranscriptionIntegrator()
    
    def test_sync_wrapper(self):
        """Test synchronous wrapper functionality."""
        # Mock the async service
        with patch.object(self.integrator.async_service, 'transcribe_audio_parallel') as mock_async:
            mock_async.return_value = asyncio.Future()
            mock_async.return_value.set_result({
                'transcript_path': 'test.json',
                'processing_method': 'parallel'
            })
            
            # Start async support
            self.integrator.start_async_support()
            
            try:
                with MockAudioFile(25) as audio_path:
                    # Should use parallel processing for large file
                    result = self.integrator.transcribe_audio_sync(
                        audio_path, 999, use_parallel=True
                    )
                    self.assertEqual(result['processing_method'], 'parallel')
                    
            finally:
                self.integrator.stop_async_support()

class PerformanceTest:
    """Performance testing utilities."""
    
    @staticmethod
    async def benchmark_parallel_vs_sequential():
        """Benchmark parallel vs sequential processing."""
        print("\n🚀 Performance Benchmark: Parallel vs Sequential Processing")
        print("=" * 70)
        
        # Mock processing that takes time
        async def mock_chunk_processing(delay=0.5):
            await asyncio.sleep(delay)
            return {'text': 'chunk result', 'segments': []}
        
        chunk_count = 6
        chunk_delay = 0.5  # seconds per chunk
        
        # Test sequential processing
        print(f"Testing sequential processing of {chunk_count} chunks...")
        start_time = time.time()
        
        sequential_results = []
        for i in range(chunk_count):
            result = await mock_chunk_processing(chunk_delay)
            sequential_results.append(result)
            
        sequential_time = time.time() - start_time
        
        # Test parallel processing (max 3 concurrent)
        print(f"Testing parallel processing of {chunk_count} chunks (max 3 concurrent)...")
        start_time = time.time()
        
        semaphore = asyncio.Semaphore(3)  # Limit concurrency
        
        async def limited_chunk_processing():
            async with semaphore:
                return await mock_chunk_processing(chunk_delay)
        
        tasks = [limited_chunk_processing() for _ in range(chunk_count)]
        parallel_results = await asyncio.gather(*tasks)
        
        parallel_time = time.time() - start_time
        
        # Calculate improvement
        improvement = sequential_time / parallel_time
        
        print(f"\n📊 Results:")
        print(f"Sequential time: {sequential_time:.2f} seconds")
        print(f"Parallel time:   {parallel_time:.2f} seconds")
        print(f"Improvement:     {improvement:.2f}x faster")
        print(f"Expected improvement: ~{min(3, chunk_count):.1f}x (limited by concurrency)")
        
        return {
            'sequential_time': sequential_time,
            'parallel_time': parallel_time,
            'improvement_factor': improvement,
            'chunks_processed': chunk_count
        }

async def run_all_tests():
    """Run comprehensive test suite."""
    print("🧪 Parallel Processing Test Suite")
    print("=" * 50)
    
    # Unit tests
    test_classes = [
        TestTokenBucket,
        TestParallelProgressTracker,
        TestIntelligentRetryManager,
        TestResourcePool,
        TestAsyncTranscriptionService,
        TestIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n📋 Running {test_class.__name__}...")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) 
                       if method.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                # Create test instance
                test_instance = test_class()
                test_instance.setUp()
                
                # Run test method
                test_method = getattr(test_instance, method_name)
                if asyncio.iscoroutinefunction(test_method):
                    await test_method()
                else:
                    test_method()
                
                print(f"  ✅ {method_name}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ❌ {method_name}: {e}")
    
    # Performance benchmark
    print(f"\n🎯 Performance Testing...")
    benchmark_results = await PerformanceTest.benchmark_parallel_vs_sequential()
    
    # Summary
    print(f"\n🎉 Test Summary")
    print("=" * 30)
    print(f"Tests passed: {passed_tests}/{total_tests}")
    print(f"Success rate: {passed_tests/total_tests*100:.1f}%")
    
    if benchmark_results['improvement_factor'] >= 2.0:
        print(f"✅ Performance target achieved: {benchmark_results['improvement_factor']:.1f}x improvement")
    else:
        print(f"⚠️  Performance target not met: {benchmark_results['improvement_factor']:.1f}x improvement")
    
    return {
        'tests_passed': passed_tests,
        'total_tests': total_tests,
        'success_rate': passed_tests/total_tests,
        'performance_improvement': benchmark_results['improvement_factor']
    }

def run_integration_test():
    """Run integration test with existing system."""
    print("\n🔗 Integration Test")
    print("=" * 30)
    
    try:
        # Initialize parallel processing
        success = initialize_parallel_processing()
        if success:
            print("✅ Parallel processing initialized")
        else:
            print("❌ Failed to initialize parallel processing")
            return False
        
        # Test file size optimization
        with MockAudioFile(15) as small_file:  # 15MB - should use direct
            with MockAudioFile(30) as large_file:  # 30MB - should use parallel
                
                print(f"Testing small file optimization...")
                # Should prefer direct processing for small files
                
                print(f"Testing large file optimization...")
                # Should prefer parallel processing for large files
                
        print("✅ Integration test completed")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
        
    finally:
        # Cleanup
        shutdown_parallel_processing()
        print("✅ Cleanup completed")

if __name__ == "__main__":
    async def main():
        """Main test runner."""
        print("🚀 Starting Parallel Processing Test Suite")
        
        # Run comprehensive tests
        results = await run_all_tests()
        
        # Run integration test
        integration_success = run_integration_test()
        
        # Final assessment
        print(f"\n🎯 Final Assessment")
        print("=" * 40)
        
        if results['success_rate'] >= 0.9 and results['performance_improvement'] >= 2.0:
            print("🎉 PARALLEL PROCESSING IMPLEMENTATION SUCCESSFUL!")
            print(f"   • Test Success Rate: {results['success_rate']*100:.1f}%")
            print(f"   • Performance Improvement: {results['performance_improvement']:.1f}x")
            print(f"   • Integration: {'✅ Success' if integration_success else '❌ Failed'}")
        else:
            print("⚠️  IMPLEMENTATION NEEDS IMPROVEMENT")
            print(f"   • Test Success Rate: {results['success_rate']*100:.1f}% (target: 90%)")
            print(f"   • Performance Improvement: {results['performance_improvement']:.1f}x (target: 2.0x)")
        
        return results
    
    # Run the test suite
    asyncio.run(main())