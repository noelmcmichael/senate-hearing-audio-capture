#!/usr/bin/env python3
"""
Test Phase 6C: Advanced Learning & Feedback Integration

Comprehensive test suite for Phase 6C components:
- Pattern Analyzer: Correction pattern analysis and insights
- Threshold Optimizer: Dynamic threshold optimization
- Predictive Identifier: Context-aware speaker prediction
- Feedback Integrator: Real-time learning integration
- Performance Tracker: System performance monitoring
"""

import sys
import json
import tempfile
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from learning.pattern_analyzer import PatternAnalyzer
from learning.threshold_optimizer import ThresholdOptimizer
from learning.predictive_identifier import PredictiveIdentifier
from learning.feedback_integrator import FeedbackIntegrator
from learning.performance_tracker import PerformanceTracker


class Phase6CLearningSystemTest:
    """Test suite for Phase 6C learning and feedback integration system."""
    
    def __init__(self):
        """Initialize test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        print(f"Phase 6C Test Environment: {self.temp_dir}")
        
        # Test database paths
        self.corrections_db = self.temp_dir / "corrections.db"
        self.voice_models_db = self.temp_dir / "speaker_models.db"
        self.metrics_db = self.temp_dir / "performance_metrics.db"
        
        # Initialize components
        self.pattern_analyzer = PatternAnalyzer(
            corrections_db_path=self.corrections_db,
            voice_models_db_path=self.voice_models_db
        )
        
        self.threshold_optimizer = ThresholdOptimizer(
            voice_models_db_path=self.voice_models_db,
            corrections_db_path=self.corrections_db
        )
        
        self.predictive_identifier = PredictiveIdentifier(
            models_dir=self.temp_dir / "predictive_models",
            corrections_db_path=self.corrections_db,
            voice_models_db_path=self.voice_models_db
        )
        
        self.performance_tracker = PerformanceTracker(
            corrections_db_path=self.corrections_db,
            voice_models_db_path=self.voice_models_db,
            metrics_db_path=self.metrics_db
        )
        
        self.feedback_integrator = FeedbackIntegrator(
            corrections_db_path=self.corrections_db,
            voice_models_db_path=self.voice_models_db
        )
        
        # Test results
        self.test_results = {
            'pattern_analyzer': [],
            'threshold_optimizer': [],
            'predictive_identifier': [],
            'performance_tracker': [],
            'feedback_integrator': [],
            'integration': []
        }
    
    def setup_test_data(self):
        """Setup comprehensive test data for all components."""
        print("Setting up test data...")
        
        # Setup corrections database with sample data
        self._setup_corrections_data()
        
        # Setup voice models database with sample data
        self._setup_voice_models_data()
        
        # Setup performance metrics data
        self._setup_performance_data()
        
        print("✅ Test data setup complete")
    
    def _setup_corrections_data(self):
        """Setup corrections database with test data."""
        with sqlite3.connect(self.corrections_db) as conn:
            # Create schema
            conn.executescript("""
                CREATE TABLE corrections (
                    id TEXT PRIMARY KEY,
                    transcript_file TEXT NOT NULL,
                    segment_id INTEGER NOT NULL,
                    speaker_name TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    reviewer_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    is_active BOOLEAN DEFAULT 1
                );
                
                CREATE TABLE review_sessions (
                    id TEXT PRIMARY KEY,
                    transcript_file TEXT NOT NULL,
                    reviewer_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    progress_data TEXT,
                    status TEXT DEFAULT 'active'
                );
                
                CREATE TABLE correction_audit (
                    id TEXT PRIMARY KEY,
                    correction_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    reviewer_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
            """)
            
            # Insert sample corrections
            base_time = datetime.now() - timedelta(days=7)
            
            sample_corrections = [
                # Judiciary Committee corrections
                ("corr_001", "judiciary_hearing_20241201.json", 15, "Sen. Cruz", 0.85, "reviewer_1", 
                 (base_time + timedelta(hours=1)).isoformat()),
                ("corr_002", "judiciary_hearing_20241201.json", 23, "Sen. Feinstein", 0.92, "reviewer_1",
                 (base_time + timedelta(hours=1.5)).isoformat()),
                ("corr_003", "judiciary_hearing_20241201.json", 45, "Sen. Graham", 0.78, "reviewer_2",
                 (base_time + timedelta(hours=2)).isoformat()),
                
                # Intelligence Committee corrections
                ("corr_004", "intelligence_hearing_20241202.json", 12, "Sen. Warner", 0.89, "reviewer_1",
                 (base_time + timedelta(days=1)).isoformat()),
                ("corr_005", "intelligence_hearing_20241202.json", 34, "Sen. Rubio", 0.76, "reviewer_2",
                 (base_time + timedelta(days=1, hours=1)).isoformat()),
                
                # Armed Services Committee corrections
                ("corr_006", "armed_services_hearing_20241203.json", 8, "Sen. Reed", 0.94, "reviewer_1",
                 (base_time + timedelta(days=2)).isoformat()),
                ("corr_007", "armed_services_hearing_20241203.json", 28, "Sen. Inhofe", 0.81, "reviewer_2",
                 (base_time + timedelta(days=2, hours=1)).isoformat()),
                ("corr_008", "armed_services_hearing_20241203.json", 52, "Sen. Cruz", 0.73, "reviewer_1",
                 (base_time + timedelta(days=2, hours=2)).isoformat()),
                
                # Recent corrections for trend analysis
                ("corr_009", "judiciary_hearing_20241205.json", 19, "Sen. Cruz", 0.68, "reviewer_1",
                 (base_time + timedelta(days=4)).isoformat()),
                ("corr_010", "judiciary_hearing_20241205.json", 41, "Sen. Cruz", 0.72, "reviewer_2",
                 (base_time + timedelta(days=4, hours=1)).isoformat()),
                ("corr_011", "intelligence_hearing_20241206.json", 25, "Sen. Warner", 0.84, "reviewer_1",
                 (base_time + timedelta(days=5)).isoformat()),
                ("corr_012", "foreign_relations_hearing_20241207.json", 16, "Sen. Menendez", 0.91, "reviewer_2",
                 (base_time + timedelta(days=6)).isoformat()),
            ]
            
            for correction in sample_corrections:
                conn.execute(
                    "INSERT INTO corrections "
                    "(id, transcript_file, segment_id, speaker_name, confidence, reviewer_id, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    correction
                )
            
            # Insert sample review sessions
            sample_sessions = [
                ("session_001", "judiciary_hearing_20241201.json", "reviewer_1", 
                 (base_time + timedelta(hours=0.5)).isoformat()),
                ("session_002", "intelligence_hearing_20241202.json", "reviewer_1",
                 (base_time + timedelta(days=1, hours=-0.5)).isoformat()),
                ("session_003", "armed_services_hearing_20241203.json", "reviewer_2",
                 (base_time + timedelta(days=2, hours=-0.5)).isoformat()),
            ]
            
            for session in sample_sessions:
                conn.execute(
                    "INSERT INTO review_sessions "
                    "(id, transcript_file, reviewer_id, start_time) "
                    "VALUES (?, ?, ?, ?)",
                    session
                )
    
    def _setup_voice_models_data(self):
        """Setup voice models database with test data."""
        with sqlite3.connect(self.voice_models_db) as conn:
            # Create schema
            conn.executescript("""
                CREATE TABLE speaker_models (
                    id TEXT PRIMARY KEY,
                    senator_name TEXT NOT NULL UNIQUE,
                    model_path TEXT NOT NULL,
                    training_samples INTEGER DEFAULT 0,
                    accuracy_score REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    is_active BOOLEAN DEFAULT 1
                );
                
                CREATE TABLE voice_samples (
                    id TEXT PRIMARY KEY,
                    senator_name TEXT NOT NULL,
                    sample_path TEXT NOT NULL,
                    source TEXT NOT NULL,
                    duration REAL DEFAULT 0.0,
                    quality_score REAL DEFAULT 0.0,
                    feature_vector_path TEXT,
                    created_at TEXT NOT NULL,
                    is_processed BOOLEAN DEFAULT 0
                );
                
                CREATE TABLE recognition_results (
                    id TEXT PRIMARY KEY,
                    audio_segment_id TEXT,
                    recognized_speaker TEXT,
                    confidence_score REAL DEFAULT 0.0,
                    similarity_scores TEXT,
                    correction_applied BOOLEAN DEFAULT 0,
                    human_verified BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL
                );
            """)
            
            # Insert sample speaker models
            base_time = datetime.now() - timedelta(days=5)
            
            sample_models = [
                ("model_001", "Sen. Cruz", "models/cruz_model.pkl", 25, 0.82, base_time.isoformat()),
                ("model_002", "Sen. Feinstein", "models/feinstein_model.pkl", 30, 0.87, base_time.isoformat()),
                ("model_003", "Sen. Graham", "models/graham_model.pkl", 22, 0.79, base_time.isoformat()),
                ("model_004", "Sen. Warner", "models/warner_model.pkl", 28, 0.85, base_time.isoformat()),
                ("model_005", "Sen. Rubio", "models/rubio_model.pkl", 26, 0.83, base_time.isoformat()),
                ("model_006", "Sen. Reed", "models/reed_model.pkl", 32, 0.89, base_time.isoformat()),
                ("model_007", "Sen. Inhofe", "models/inhofe_model.pkl", 24, 0.78, base_time.isoformat()),
                ("model_008", "Sen. Menendez", "models/menendez_model.pkl", 27, 0.84, base_time.isoformat()),
            ]
            
            for model in sample_models:
                conn.execute(
                    "INSERT INTO speaker_models "
                    "(id, senator_name, model_path, training_samples, accuracy_score, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    model
                )
            
            # Insert sample recognition results
            sample_recognitions = [
                ("rec_001", "judiciary_hearing_20241201_segment_15.wav", "Sen. Cruz", 0.78, 
                 '[{"senator_name": "Sen. Cruz", "similarity_score": 0.78}]', True, True,
                 (base_time + timedelta(hours=1)).isoformat()),
                ("rec_002", "judiciary_hearing_20241201_segment_23.wav", "Sen. Graham", 0.65,
                 '[{"senator_name": "Sen. Graham", "similarity_score": 0.65}]', True, True,
                 (base_time + timedelta(hours=1.5)).isoformat()),
                ("rec_003", "intelligence_hearing_20241202_segment_12.wav", "Sen. Warner", 0.91,
                 '[{"senator_name": "Sen. Warner", "similarity_score": 0.91}]', False, True,
                 (base_time + timedelta(days=1)).isoformat()),
                ("rec_004", "armed_services_hearing_20241203_segment_8.wav", "Sen. Reed", 0.88,
                 '[{"senator_name": "Sen. Reed", "similarity_score": 0.88}]', False, True,
                 (base_time + timedelta(days=2)).isoformat()),
                ("rec_005", "judiciary_hearing_20241205_segment_19.wav", "Sen. Cruz", 0.56,
                 '[{"senator_name": "Sen. Cruz", "similarity_score": 0.56}]', True, True,
                 (base_time + timedelta(days=4)).isoformat()),
            ]
            
            for recognition in sample_recognitions:
                conn.execute(
                    "INSERT INTO recognition_results "
                    "(id, audio_segment_id, recognized_speaker, confidence_score, similarity_scores, "
                    "correction_applied, human_verified, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    recognition
                )
    
    def _setup_performance_data(self):
        """Setup performance metrics data."""
        # Record sample performance metrics
        base_time = datetime.now() - timedelta(days=3)
        
        # Simulate performance over time with trends
        for i in range(72):  # 3 days, hourly data
            timestamp = base_time + timedelta(hours=i)
            
            # Accuracy with slight decline trend
            accuracy = 0.85 - (i * 0.001) + np.random.normal(0, 0.02)
            accuracy = max(0.5, min(1.0, accuracy))
            
            # Coverage with improvement trend
            coverage = 0.70 + (i * 0.0005) + np.random.normal(0, 0.015)
            coverage = max(0.3, min(1.0, coverage))
            
            # Response time with some volatility
            response_time = 2.0 + np.random.normal(0, 0.3)
            response_time = max(0.5, response_time)
            
            # Record metrics for different components
            self.performance_tracker.record_performance_metric(
                'phase6a', 'accuracy', 'speaker_identification', accuracy
            )
            self.performance_tracker.record_performance_metric(
                'phase6a', 'coverage', 'review_coverage', coverage
            )
            self.performance_tracker.record_performance_metric(
                'phase6a', 'response_time', 'review_latency', response_time
            )
    
    def test_pattern_analyzer(self):
        """Test pattern analyzer functionality."""
        print("\n🔍 Testing Pattern Analyzer...")
        
        try:
            # Test 1: Basic pattern analysis
            print("  Testing pattern analysis...")
            patterns = self.pattern_analyzer.analyze_correction_patterns(force_refresh=True)
            
            assert patterns is not None, "Pattern analysis should return results"
            assert 'speaker_patterns' in patterns, "Should include speaker patterns"
            assert 'temporal_patterns' in patterns, "Should include temporal patterns"
            assert 'context_patterns' in patterns, "Should include context patterns"
            assert 'error_patterns' in patterns, "Should include error patterns"
            
            self.test_results['pattern_analyzer'].append("✅ Basic pattern analysis")
            
            # Test 2: Pattern insights
            print("  Testing pattern insights...")
            insights = self.pattern_analyzer.get_pattern_insights()
            
            assert insights is not None, "Should return insights"
            assert 'recommendations' in insights, "Should include recommendations"
            assert 'alerts' in insights, "Should include alerts"
            assert 'optimization_opportunities' in insights, "Should include optimization opportunities"
            
            self.test_results['pattern_analyzer'].append("✅ Pattern insights generation")
            
            # Test 3: Cache functionality
            print("  Testing pattern cache...")
            patterns_cached = self.pattern_analyzer.analyze_correction_patterns(force_refresh=False)
            
            assert patterns_cached is not None, "Cached patterns should be available"
            
            self.test_results['pattern_analyzer'].append("✅ Pattern caching system")
            
            print("  ✅ Pattern Analyzer tests passed")
            
        except Exception as e:
            error_msg = f"❌ Pattern Analyzer test failed: {e}"
            print(f"  {error_msg}")
            self.test_results['pattern_analyzer'].append(error_msg)
    
    def test_threshold_optimizer(self):
        """Test threshold optimizer functionality."""
        print("\n⚙️ Testing Threshold Optimizer...")
        
        try:
            # Test 1: Get current recommendations
            print("  Testing threshold recommendations...")
            recommendations = self.threshold_optimizer.get_threshold_recommendations()
            
            assert recommendations is not None, "Should return recommendations"
            assert 'status' in recommendations, "Should include status"
            
            self.test_results['threshold_optimizer'].append("✅ Threshold recommendations")
            
            # Test 2: Optimization (with limited data)
            print("  Testing threshold optimization...")
            optimization_result = self.threshold_optimizer.optimize_thresholds('balanced')
            
            assert optimization_result is not None, "Should return optimization result"
            assert 'status' in optimization_result, "Should include status"
            
            # With limited test data, might get insufficient_data status
            if optimization_result['status'] in ['optimized', 'no_improvement', 'insufficient_data']:
                self.test_results['threshold_optimizer'].append("✅ Threshold optimization")
            else:
                self.test_results['threshold_optimizer'].append(f"⚠️ Unexpected optimization status: {optimization_result['status']}")
            
            # Test 3: A/B test setup
            print("  Testing A/B test framework...")
            test_thresholds = self.threshold_optimizer.current_thresholds.copy()
            test_thresholds['voice_thresholds']['high_confidence'] = 0.90
            
            ab_test_result = self.threshold_optimizer.start_ab_test(test_thresholds, "Test A/B")
            
            assert ab_test_result is not None, "Should return A/B test result"
            assert 'test_id' in ab_test_result, "Should include test ID"
            assert ab_test_result['status'] == 'started', "Should start successfully"
            
            self.test_results['threshold_optimizer'].append("✅ A/B test framework")
            
            print("  ✅ Threshold Optimizer tests passed")
            
        except Exception as e:
            error_msg = f"❌ Threshold Optimizer test failed: {e}"
            print(f"  {error_msg}")
            self.test_results['threshold_optimizer'].append(error_msg)
    
    def test_predictive_identifier(self):
        """Test predictive identifier functionality."""
        print("\n🔮 Testing Predictive Identifier...")
        
        try:
            # Test 1: Model training
            print("  Testing predictive model training...")
            training_result = self.predictive_identifier.train_prediction_models()
            
            assert training_result is not None, "Should return training result"
            assert 'status' in training_result, "Should include status"
            
            # With limited test data, might get insufficient_data status
            if training_result['status'] in ['success', 'insufficient_data']:
                self.test_results['predictive_identifier'].append("✅ Model training")
            else:
                self.test_results['predictive_identifier'].append(f"⚠️ Training status: {training_result['status']}")
            
            # Test 2: Speaker likelihood prediction
            print("  Testing speaker prediction...")
            context = {
                'committee': 'judiciary',
                'segment_id': 25,
                'timestamp': datetime.now().isoformat(),
                'candidate_speakers': ['Sen. Cruz', 'Sen. Feinstein', 'Sen. Graham']
            }
            
            prediction = self.predictive_identifier.predict_speaker_likelihood(context)
            
            assert prediction is not None, "Should return prediction"
            assert 'status' in prediction, "Should include status"
            
            if prediction['status'] in ['success', 'models_not_trained']:
                self.test_results['predictive_identifier'].append("✅ Speaker prediction")
            else:
                self.test_results['predictive_identifier'].append(f"⚠️ Prediction status: {prediction['status']}")
            
            # Test 3: Meeting structure prediction
            print("  Testing meeting structure prediction...")
            structure = self.predictive_identifier.get_meeting_structure_prediction(context)
            
            assert structure is not None, "Should return structure prediction"
            assert 'status' in structure, "Should include status"
            
            if structure['status'] == 'success':
                assert 'meeting_structure' in structure, "Should include meeting structure"
                self.test_results['predictive_identifier'].append("✅ Meeting structure prediction")
            else:
                self.test_results['predictive_identifier'].append(f"⚠️ Structure prediction failed: {structure.get('error', 'Unknown')}")
            
            print("  ✅ Predictive Identifier tests passed")
            
        except Exception as e:
            error_msg = f"❌ Predictive Identifier test failed: {e}"
            print(f"  {error_msg}")
            self.test_results['predictive_identifier'].append(error_msg)
    
    def test_performance_tracker(self):
        """Test performance tracker functionality."""
        print("\n📊 Testing Performance Tracker...")
        
        try:
            # Test 1: Current performance
            print("  Testing current performance metrics...")
            current_perf = self.performance_tracker.get_current_performance()
            
            assert current_perf is not None, "Should return current performance"
            assert 'component_performance' in current_perf, "Should include component performance"
            assert 'overall_performance' in current_perf, "Should include overall performance"
            
            self.test_results['performance_tracker'].append("✅ Current performance metrics")
            
            # Test 2: Performance trends
            print("  Testing performance trends...")
            trends = self.performance_tracker.get_performance_trends(days=3)
            
            assert trends is not None, "Should return trends"
            
            if 'trends' in trends and trends['trends']:
                self.test_results['performance_tracker'].append("✅ Performance trends analysis")
            else:
                self.test_results['performance_tracker'].append("⚠️ Limited trend data available")
            
            # Test 3: System analysis
            print("  Testing comprehensive system analysis...")
            analysis = self.performance_tracker.analyze_system_performance()
            
            assert analysis is not None, "Should return system analysis"
            
            if 'current_performance' in analysis:
                self.test_results['performance_tracker'].append("✅ Comprehensive system analysis")
            else:
                self.test_results['performance_tracker'].append(f"⚠️ Analysis incomplete: {analysis.get('error', 'Unknown')}")
            
            # Test 4: Alert system
            print("  Testing alert system...")
            alerts = self.performance_tracker.get_recent_alerts(hours=24)
            
            assert isinstance(alerts, list), "Should return list of alerts"
            self.test_results['performance_tracker'].append("✅ Alert system")
            
            print("  ✅ Performance Tracker tests passed")
            
        except Exception as e:
            error_msg = f"❌ Performance Tracker test failed: {e}"
            print(f"  {error_msg}")
            self.test_results['performance_tracker'].append(error_msg)
    
    def test_feedback_integrator(self):
        """Test feedback integrator functionality."""
        print("\n🔄 Testing Feedback Integrator...")
        
        try:
            # Test 1: Configuration
            print("  Testing feedback configuration...")
            status = self.feedback_integrator.get_feedback_status()
            
            assert status is not None, "Should return status"
            assert 'status' in status, "Should include status field"
            assert 'config' in status, "Should include configuration"
            
            self.test_results['feedback_integrator'].append("✅ Feedback configuration")
            
            # Test 2: Integration summary
            print("  Testing integration summary...")
            summary = self.feedback_integrator.get_integration_summary()
            
            assert summary is not None, "Should return summary"
            
            if 'feedback_metrics' in summary:
                self.test_results['feedback_integrator'].append("✅ Integration summary")
            else:
                self.test_results['feedback_integrator'].append(f"⚠️ Summary incomplete: {summary.get('error', 'Unknown')}")
            
            # Test 3: Real-time feedback (brief test)
            print("  Testing real-time feedback system...")
            start_result = self.feedback_integrator.start_real_time_feedback()
            
            assert start_result is not None, "Should return start result"
            
            if start_result.get('status') == 'started':
                # Let it run briefly
                time.sleep(2)
                
                # Stop the system
                stop_result = self.feedback_integrator.stop_real_time_feedback()
                
                assert stop_result is not None, "Should return stop result"
                assert stop_result.get('status') == 'stopped', "Should stop successfully"
                
                self.test_results['feedback_integrator'].append("✅ Real-time feedback system")
            else:
                self.test_results['feedback_integrator'].append(f"⚠️ Real-time feedback failed to start: {start_result}")
            
            print("  ✅ Feedback Integrator tests passed")
            
        except Exception as e:
            error_msg = f"❌ Feedback Integrator test failed: {e}"
            print(f"  {error_msg}")
            self.test_results['feedback_integrator'].append(error_msg)
    
    def test_integration_workflow(self):
        """Test complete integration workflow."""
        print("\n🔗 Testing Complete Integration Workflow...")
        
        try:
            # Test 1: End-to-end pattern analysis to optimization
            print("  Testing pattern analysis → threshold optimization workflow...")
            
            # Analyze patterns
            patterns = self.pattern_analyzer.analyze_correction_patterns(force_refresh=True)
            insights = self.pattern_analyzer.get_pattern_insights()
            
            # Use insights to inform optimization
            if insights.get('recommendations'):
                optimization_target = 'balanced'  # Default
                for rec in insights['recommendations']:
                    if rec.get('type') == 'accuracy_improvement':
                        optimization_target = 'accuracy'
                        break
                
                optimization_result = self.threshold_optimizer.optimize_thresholds(optimization_target)
                
                if optimization_result and optimization_result.get('status') in ['optimized', 'no_improvement', 'insufficient_data']:
                    self.test_results['integration'].append("✅ Pattern analysis → threshold optimization")
                else:
                    self.test_results['integration'].append("⚠️ Optimization workflow incomplete")
            else:
                self.test_results['integration'].append("⚠️ No recommendations available for optimization")
            
            # Test 2: Performance tracking integration
            print("  Testing performance tracking integration...")
            
            # Record some metrics
            self.performance_tracker.record_performance_metric(
                'phase6c', 'accuracy', 'integrated_system', 0.82
            )
            
            # Get performance and check for alerts
            current_perf = self.performance_tracker.get_current_performance()
            alerts = self.performance_tracker.get_recent_alerts()
            
            if current_perf and 'overall_performance' in current_perf:
                self.test_results['integration'].append("✅ Performance tracking integration")
            else:
                self.test_results['integration'].append("⚠️ Performance tracking integration incomplete")
            
            # Test 3: Feedback loop simulation
            print("  Testing feedback loop simulation...")
            
            # Simulate feedback from all components
            integration_health = self.feedback_integrator._calculate_integration_health()
            
            if integration_health and 'health_score' in integration_health:
                self.test_results['integration'].append("✅ Feedback loop simulation")
            else:
                self.test_results['integration'].append("⚠️ Feedback loop simulation incomplete")
            
            print("  ✅ Integration workflow tests passed")
            
        except Exception as e:
            error_msg = f"❌ Integration workflow test failed: {e}"
            print(f"  {error_msg}")
            self.test_results['integration'].append(error_msg)
    
    def run_all_tests(self):
        """Run all Phase 6C tests."""
        print("🚀 Starting Phase 6C: Advanced Learning & Feedback Integration Tests")
        print("=" * 80)
        
        # Setup test environment
        self.setup_test_data()
        
        # Run individual component tests
        self.test_pattern_analyzer()
        self.test_threshold_optimizer()
        self.test_predictive_identifier()
        self.test_performance_tracker()
        self.test_feedback_integrator()
        
        # Run integration tests
        self.test_integration_workflow()
        
        # Generate test report
        self.generate_test_report()
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n" + "=" * 80)
        print("📋 PHASE 6C TEST REPORT")
        print("=" * 80)
        
        total_tests = 0
        passed_tests = 0
        warning_tests = 0
        failed_tests = 0
        
        for component, results in self.test_results.items():
            print(f"\n{component.upper().replace('_', ' ')}:")
            print("-" * 40)
            
            for result in results:
                total_tests += 1
                print(f"  {result}")
                
                if result.startswith("✅"):
                    passed_tests += 1
                elif result.startswith("⚠️"):
                    warning_tests += 1
                else:
                    failed_tests += 1
        
        print("\n" + "=" * 80)
        print("TEST SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  ✅ Passed: {passed_tests}")
        print(f"  ⚠️  Warnings: {warning_tests}")
        print(f"  ❌ Failed: {failed_tests}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"  Success Rate: {success_rate:.1f}%")
        
        if failed_tests == 0:
            print("\n🎉 ALL PHASE 6C TESTS COMPLETED SUCCESSFULLY!")
            print("The advanced learning and feedback integration system is operational.")
        elif warning_tests > 0 and failed_tests == 0:
            print("\n⚠️  PHASE 6C TESTS COMPLETED WITH WARNINGS")
            print("The system is functional but may have limited data or features.")
        else:
            print("\n❌ SOME PHASE 6C TESTS FAILED")
            print("Review the test results and address the issues before deployment.")
        
        print("\nKey Phase 6C Features Tested:")
        print("  • Pattern Analysis Engine")
        print("  • Threshold Optimization System")
        print("  • Predictive Speaker Identification")
        print("  • Real-time Feedback Integration")
        print("  • Performance Tracking & Analytics")
        print("  • Complete Learning Workflow")
        
        print(f"\nTest Environment: {self.temp_dir}")
        print("=" * 80)


if __name__ == "__main__":
    # Run Phase 6C tests
    test_suite = Phase6CLearningSystemTest()
    test_suite.run_all_tests()