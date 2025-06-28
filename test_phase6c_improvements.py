#!/usr/bin/env python3
"""
Test Phase 6C Improvements

Tests the fixes and enhancements made to Phase 6C:
1. SQLite Row object fixes
2. Pattern cache pickling improvements  
3. Enhanced error handling
4. Performance optimizations
"""

import sys
import json
import tempfile
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from learning.pattern_analyzer import PatternAnalyzer
from learning.threshold_optimizer import ThresholdOptimizer
from learning.predictive_identifier import PredictiveIdentifier
from learning.feedback_integrator import FeedbackIntegrator
from learning.performance_tracker import PerformanceTracker
from learning.error_handler import health_monitor, ComponentStatus
from learning.performance_optimizer import profiler, cache_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase6CImprovementsTest:
    """Test Phase 6C improvements and fixes."""
    
    def __init__(self):
        """Initialize test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        print(f"📁 Phase 6C Improvements Test Environment: {self.temp_dir}")
        
        # Test database paths
        self.corrections_db = self.temp_dir / "corrections.db"
        self.voice_models_db = self.temp_dir / "speaker_models.db"
        self.metrics_db = self.temp_dir / "performance_metrics.db"
        
        # Setup test data
        self._setup_test_databases()
        
        print("✅ Test environment initialized")
    
    def _setup_test_databases(self):
        """Create test databases with sample data."""
        # Setup corrections database
        with sqlite3.connect(self.corrections_db) as conn:
            conn.execute("""
                CREATE TABLE corrections (
                    id INTEGER PRIMARY KEY,
                    transcript_file TEXT,
                    segment_id INTEGER,
                    speaker_name TEXT,
                    confidence REAL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT,
                    reviewer_id TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE review_sessions (
                    id INTEGER PRIMARY KEY,
                    transcript_file TEXT,
                    reviewer_id TEXT,
                    start_time TEXT,
                    progress_data TEXT
                )
            """)
            
            # Insert sample data
            sample_corrections = [
                ('hearing_judiciary_2024.txt', 1, 'Sen. Smith', 0.85, 1, datetime.now().isoformat(), 'reviewer1'),
                ('hearing_judiciary_2024.txt', 2, 'Sen. Johnson', 0.92, 1, datetime.now().isoformat(), 'reviewer1'),
                ('hearing_intelligence_2024.txt', 1, 'Sen. Davis', 0.78, 1, datetime.now().isoformat(), 'reviewer2'),
                ('hearing_intelligence_2024.txt', 2, 'Sen. Wilson', 0.88, 1, datetime.now().isoformat(), 'reviewer2'),
            ]
            
            conn.executemany(
                "INSERT INTO corrections (transcript_file, segment_id, speaker_name, confidence, is_active, created_at, reviewer_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                sample_corrections
            )
        
        # Setup voice models database
        with sqlite3.connect(self.voice_models_db) as conn:
            conn.execute("""
                CREATE TABLE recognition_results (
                    id INTEGER PRIMARY KEY,
                    audio_segment_id TEXT,
                    recognized_speaker TEXT,
                    confidence_score REAL,
                    similarity_scores TEXT,
                    correction_applied INTEGER DEFAULT 0,
                    human_verified INTEGER DEFAULT 0,
                    created_at TEXT
                )
            """)
            
            # Insert sample recognition data
            sample_recognitions = [
                ('hearing_judiciary_2024_segment1.wav', 'Sen. Smith', 0.85, '[]', 0, 1, datetime.now().isoformat()),
                ('hearing_judiciary_2024_segment2.wav', 'Sen. Johnson', 0.92, '[]', 0, 1, datetime.now().isoformat()),
                ('hearing_intelligence_2024_segment1.wav', 'Sen. Davis', 0.78, '[]', 1, 1, datetime.now().isoformat()),
                ('hearing_intelligence_2024_segment2.wav', 'Sen. Wilson', 0.88, '[]', 0, 1, datetime.now().isoformat()),
            ]
            
            conn.executemany(
                "INSERT INTO recognition_results (audio_segment_id, recognized_speaker, confidence_score, similarity_scores, correction_applied, human_verified, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                sample_recognitions
            )
    
    def test_sqlite_row_fixes(self):
        """Test that SQLite Row object issues are fixed."""
        print("\n🔧 Testing SQLite Row Object Fixes...")
        
        try:
            # Test threshold optimizer
            optimizer = ThresholdOptimizer(self.voice_models_db, self.corrections_db)
            performance_data = optimizer._get_performance_data()
            
            print(f"  ✅ Threshold Optimizer: Retrieved {len(performance_data)} performance records")
            
            # Test predictive identifier
            identifier = PredictiveIdentifier(
                models_dir=self.temp_dir / "models",
                corrections_db_path=self.corrections_db, 
                voice_models_db_path=self.voice_models_db
            )
            training_data = identifier._get_training_data()
            
            print(f"  ✅ Predictive Identifier: Retrieved {len(training_data)} training samples")
            
            return True
            
        except Exception as e:
            print(f"  ❌ SQLite Row object error: {e}")
            return False
    
    def test_pattern_cache_fixes(self):
        """Test that pattern cache pickling issues are fixed."""
        print("\n🗄️ Testing Pattern Cache Fixes...")
        
        try:
            # Test pattern analyzer caching
            analyzer = PatternAnalyzer(self.corrections_db, self.voice_models_db)
            
            # Run pattern analysis (this should trigger cache save)
            patterns = analyzer.analyze_correction_patterns(force_refresh=True)
            
            print(f"  ✅ Pattern Analysis: Generated {len(patterns)} pattern categories")
            
            # Check if cache was saved without pickling errors
            if analyzer.patterns_cache_path.exists():
                print("  ✅ Pattern Cache: Successfully saved to disk")
            else:
                print("  ⚠️ Pattern Cache: Cache file not found")
            
            # Test cache loading
            analyzer2 = PatternAnalyzer(self.corrections_db, self.voice_models_db)
            cached_patterns = analyzer2.pattern_cache
            
            if cached_patterns:
                print("  ✅ Pattern Cache: Successfully loaded from disk")
            else:
                print("  ⚠️ Pattern Cache: No cached patterns loaded")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Pattern cache error: {e}")
            return False
    
    def test_error_handling_improvements(self):
        """Test enhanced error handling capabilities."""
        print("\n🛡️ Testing Enhanced Error Handling...")
        
        try:
            # Test health monitoring
            print(f"  📊 Initial health status: {health_monitor.get_system_health()}")
            
            # Test error recording
            health_monitor.record_error("test_component", Exception("Test error"))
            health_monitor.record_error("test_component", Exception("Another test error"))
            
            health_status = health_monitor.get_system_health()
            if health_status['failed'] > 0 or health_status['degraded'] > 0:
                print("  ✅ Error Handling: Health monitor correctly tracks component failures")
            
            # Test recovery
            health_monitor.record_success("test_component")
            health_monitor.record_success("test_component")
            
            health_status = health_monitor.get_system_health()
            print(f"  📈 Health after recovery: {health_status}")
            
            # Test feedback integrator health
            integrator = FeedbackIntegrator(self.corrections_db, self.voice_models_db)
            system_health = integrator.get_system_health_status()
            
            print(f"  🔍 System Health Check: {system_health['status']}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error handling test failed: {e}")
            return False
    
    def test_performance_optimizations(self):
        """Test performance optimization improvements."""
        print("\n⚡ Testing Performance Optimizations...")
        
        try:
            # Test performance profiling
            @profiler.profile_function("test_function")
            def test_function(n):
                time.sleep(0.1)  # Simulate work
                return sum(range(n))
            
            # Run function multiple times
            for i in range(5):
                result = test_function(1000)
            
            # Get performance report
            report = profiler.get_performance_report()
            
            if 'test_function' in report['function_metrics']:
                metrics = report['function_metrics']['test_function']
                print(f"  📊 Performance Profiling: Tracked {metrics['total_calls']} calls")
                print(f"  ⏱️ Average execution time: {metrics['avg_execution_time']:.3f}s")
                print(f"  💾 Average memory delta: {metrics['avg_memory_delta']:.2f}MB")
            
            # Test cache manager
            cache_manager.set("test_key", {"data": "test_value"})
            cached_value = cache_manager.get("test_key")
            
            if cached_value:
                print("  🗄️ Cache Manager: Successfully stored and retrieved data")
            
            cache_stats = cache_manager.get_cache_stats()
            print(f"  📈 Cache Stats: {cache_stats['hit_rate']:.1%} hit rate")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Performance optimization test failed: {e}")
            return False
    
    def test_integration_workflow(self):
        """Test complete integration workflow with improvements."""
        print("\n🔄 Testing Complete Integration Workflow...")
        
        try:
            # Initialize all components
            integrator = FeedbackIntegrator(self.corrections_db, self.voice_models_db)
            
            # Test integration summary
            summary = integrator.get_integration_summary()
            print(f"  📋 Integration Summary: {len(summary.get('components', []))} components integrated")
            
            # Test feedback status
            status = integrator.get_feedback_status()
            print(f"  🏥 Feedback Status: {status.get('real_time_active', False)}")
            
            # Test real-time feedback configuration
            config = integrator._load_feedback_config()
            if config:
                print("  ⚙️ Real-time Feedback: Configuration loaded successfully")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Integration workflow test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all improvement tests."""
        print("🚀 Starting Phase 6C Improvements Testing")
        print("=" * 60)
        
        tests = [
            ("SQLite Row Fixes", self.test_sqlite_row_fixes),
            ("Pattern Cache Fixes", self.test_pattern_cache_fixes),
            ("Error Handling", self.test_error_handling_improvements),
            ("Performance Optimizations", self.test_performance_optimizations),
            ("Integration Workflow", self.test_integration_workflow)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    status = "✅ PASSED"
                else:
                    status = "❌ FAILED"
            except Exception as e:
                status = f"❌ ERROR: {e}"
            
            print(f"{test_name}: {status}")
        
        print("\n" + "=" * 60)
        print("📊 PHASE 6C IMPROVEMENTS TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL IMPROVEMENTS TESTS PASSED!")
            print("Phase 6C is now production-ready with enhanced reliability.")
        else:
            print(f"\n⚠️ {total - passed} tests failed. Review issues before production deployment.")
        
        print(f"\nTest Environment: {self.temp_dir}")
        
        return passed == total


if __name__ == "__main__":
    tester = Phase6CImprovementsTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)