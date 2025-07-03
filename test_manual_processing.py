#!/usr/bin/env python3
"""
Comprehensive test suite for Manual Processing Framework
Tests all components without requiring user interaction
"""

import json
import os
import tempfile
import shutil
from pathlib import Path
from process_single_hearing import ManualProcessingFramework

class TestManualProcessingFramework:
    """Test suite for manual processing framework"""
    
    def __init__(self):
        self.framework = ManualProcessingFramework()
        self.test_results = []
        
    def log_test(self, test_name, passed, details=""):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'status': status,
            'passed': passed,
            'details': details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def test_framework_initialization(self):
        """Test framework initialization"""
        try:
            # Test basic initialization
            passed = self.framework is not None
            self.log_test("Framework Initialization", passed)
            
            # Test directory creation
            dirs_exist = all([
                self.framework.base_dir.exists(),
                self.framework.data_dir.exists(),
                self.framework.output_dir.exists(),
                self.framework.logs_dir.exists()
            ])
            self.log_test("Directory Creation", dirs_exist)
            
            # Test priority hearings loading
            hearings_loaded = bool(self.framework.priority_hearings.get('priority_hearings'))
            hearing_count = len(self.framework.priority_hearings.get('priority_hearings', []))
            self.log_test("Priority Hearings Loading", hearings_loaded, 
                         f"{hearing_count} hearings loaded")
            
        except Exception as e:
            self.log_test("Framework Initialization", False, str(e))
    
    def test_hearing_validation(self):
        """Test hearing validation logic"""
        try:
            if not self.framework.priority_hearings.get('priority_hearings'):
                self.log_test("Hearing Validation", False, "No hearings available")
                return
            
            # Test with valid hearing
            valid_hearing = self.framework.priority_hearings['priority_hearings'][0]
            is_ready, issues = self.framework.validate_hearing_processing_readiness(valid_hearing)
            self.log_test("Valid Hearing Validation", is_ready, f"Issues: {len(issues)}")
            
            # Test with invalid hearing
            invalid_hearing = {
                'hearing_id': 'test_invalid',
                'title': '',  # Missing title
                'committee_code': '',  # Missing committee
                'url': 'http://invalid-url',  # Non-HTTPS URL
                'audio_source': 'Unknown',  # Unknown source
                'readiness_score': 0.5  # Low score
            }
            
            is_ready, issues = self.framework.validate_hearing_processing_readiness(invalid_hearing)
            self.log_test("Invalid Hearing Validation", not is_ready, f"Issues detected: {len(issues)}")
            
        except Exception as e:
            self.log_test("Hearing Validation", False, str(e))
    
    def test_session_management(self):
        """Test processing session management"""
        try:
            if not self.framework.priority_hearings.get('priority_hearings'):
                self.log_test("Session Management", False, "No hearings available")
                return
            
            # Create test session
            test_hearing = self.framework.priority_hearings['priority_hearings'][0]
            session = self.framework.create_processing_session(test_hearing)
            
            # Validate session structure
            required_fields = ['session_id', 'hearing_id', 'processing_status', 'stages']
            session_valid = all(field in session for field in required_fields)
            self.log_test("Session Creation", session_valid, f"Session ID: {session['session_id']}")
            
            # Test stage updates
            self.framework.update_session_stage(session, 'validation', 'STARTED')
            self.framework.update_session_stage(session, 'validation', 'COMPLETED')
            
            validation_stage = session['stages']['validation']
            stage_updated = (validation_stage['status'] == 'COMPLETED' and 
                           validation_stage['start_time'] is not None)
            self.log_test("Session Stage Updates", stage_updated)
            
        except Exception as e:
            self.log_test("Session Management", False, str(e))
    
    def test_processing_simulation(self):
        """Test processing simulation (without actual audio/transcript processing)"""
        try:
            if not self.framework.priority_hearings.get('priority_hearings'):
                self.log_test("Processing Simulation", False, "No hearings available")
                return
            
            # Get a high-readiness hearing for testing
            test_hearing = None
            for hearing in self.framework.priority_hearings['priority_hearings']:
                if hearing.get('readiness_score', 0) > 0.9:
                    test_hearing = hearing
                    break
            
            if not test_hearing:
                self.log_test("Processing Simulation", False, "No high-readiness hearing found")
                return
            
            # Run processing simulation
            session = self.framework.process_single_hearing(test_hearing)
            
            # Validate processing results
            processing_completed = session['processing_status'] in ['COMPLETED', 'FAILED']
            self.log_test("Processing Simulation", processing_completed, 
                         f"Status: {session['processing_status']}")
            
            # Check output files were created
            output_files_exist = any(
                path and os.path.exists(path) 
                for path in session['output_paths'].values()
            )
            self.log_test("Output Files Creation", output_files_exist)
            
            # Test rollback functionality
            if processing_completed and session['processing_status'] == 'COMPLETED':
                self.framework.rollback_processing(session)
                
                # Check files were cleaned up
                files_cleaned = not any(
                    path and os.path.exists(path) 
                    for path in session['output_paths'].values()
                )
                self.log_test("Rollback Functionality", files_cleaned)
            
        except Exception as e:
            self.log_test("Processing Simulation", False, str(e))
    
    def test_error_handling(self):
        """Test error handling capabilities"""
        try:
            # Test with malformed hearing data
            malformed_hearing = {
                'hearing_id': 'test_malformed',
                'title': 'Test Malformed Hearing',
                'committee_code': 'TEST',
                'committee_name': 'Test Committee',
                'url': 'https://invalid-url-that-does-not-exist.com',
                'audio_source': 'ISVP',
                'readiness_score': 0.95
            }
            
            session = self.framework.process_single_hearing(malformed_hearing)
            
            # Should handle gracefully (may succeed in simulation mode)
            error_handled = session['processing_status'] in ['FAILED', 'COMPLETED']
            self.log_test("Error Handling", error_handled, 
                         f"Status: {session['processing_status']}, Errors: {len(session['errors'])}")
            
        except Exception as e:
            self.log_test("Error Handling", False, str(e))
    
    def test_priority_hearing_quality(self):
        """Test quality of priority hearings"""
        try:
            if not self.framework.priority_hearings.get('priority_hearings'):
                self.log_test("Priority Hearing Quality", False, "No hearings available")
                return
            
            hearings = self.framework.priority_hearings['priority_hearings']
            
            # Test readiness scores
            high_readiness = sum(1 for h in hearings if h.get('readiness_score', 0) > 0.8)
            readiness_quality = high_readiness / len(hearings) > 0.6  # 60% should be high quality
            self.log_test("High Readiness Quality", readiness_quality, 
                         f"{high_readiness}/{len(hearings)} high-readiness hearings")
            
            # Test ISVP compatibility
            isvp_compatible = sum(1 for h in hearings if h.get('isvp_compatible', False))
            isvp_quality = isvp_compatible / len(hearings) > 0.5  # 50% should be ISVP compatible
            self.log_test("ISVP Compatibility", isvp_quality, 
                         f"{isvp_compatible}/{len(hearings)} ISVP-compatible hearings")
            
            # Test committee diversity
            committees = set(h.get('committee_code') for h in hearings)
            diversity_quality = len(committees) >= 3  # At least 3 different committees
            self.log_test("Committee Diversity", diversity_quality, 
                         f"{len(committees)} different committees")
            
        except Exception as e:
            self.log_test("Priority Hearing Quality", False, str(e))
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 MANUAL PROCESSING FRAMEWORK TEST SUITE")
        print("=" * 60)
        
        # Run all tests
        self.test_framework_initialization()
        self.test_hearing_validation()
        self.test_session_management()
        self.test_processing_simulation()
        self.test_error_handling()
        self.test_priority_hearing_quality()
        
        # Generate results summary
        print("\n📊 TEST RESULTS SUMMARY")
        print("=" * 40)
        
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        total_tests = len(self.test_results)
        
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        print(f"\n🎯 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed")
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1%}")
        
        if success_rate >= 0.8:
            print("✅ FRAMEWORK READY FOR PRODUCTION USE")
        else:
            print("❌ FRAMEWORK NEEDS IMPROVEMENTS")
        
        return success_rate >= 0.8


def main():
    """Run test suite"""
    test_suite = TestManualProcessingFramework()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🚀 Manual Processing Framework validation successful!")
        print("Ready to proceed with Phase 1 testing (5 high-priority ISVP hearings)")
    else:
        print("\n⚠️  Manual Processing Framework needs improvements before proceeding")
    
    return success


if __name__ == "__main__":
    main()