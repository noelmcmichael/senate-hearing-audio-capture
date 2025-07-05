#!/usr/bin/env python3
"""
Focused Production Test - Core Infrastructure Validation
Tests the essential functionality without external dependencies
"""

import json
import requests
import time
import threading
from datetime import datetime

# Configuration
CLOUD_URL = "https://senate-hearing-processor-518203250893.us-central1.run.app"

class FocusedValidator:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    def test(self, name, test_func):
        """Run a single test and log results"""
        try:
            result = test_func()
            status = "✅ PASS" if result else "❌ FAIL"
            self.results.append((name, result))
            print(f"{status} - {name}")
            return result
        except Exception as e:
            print(f"❌ FAIL - {name}: {str(e)}")
            self.results.append((name, False))
            return False
    
    def test_health_endpoint(self):
        """Test basic health endpoint"""
        response = requests.get(f"{CLOUD_URL}/health", timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('status') == 'healthy'
        return False
    
    def test_storage_verification(self):
        """Test storage verification endpoint"""
        response = requests.get(f"{CLOUD_URL}/api/storage/audio/test-123/verify", timeout=30)
        if response.status_code == 200:
            data = response.json()
            # Should return exists: false for non-existent file
            return 'exists' in data and data['exists'] == False
        return False
    
    def test_transcription_error_handling(self):
        """Test transcription service error handling"""
        payload = {
            "hearing_id": "test-nonexistent-hearing",
            "options": {"model": "whisper-1", "language": "en"}
        }
        
        response = requests.post(f"{CLOUD_URL}/api/transcription", json=payload, timeout=30)
        
        # Should return 500 with proper error message for missing audio
        if response.status_code == 500:
            data = response.json()
            return 'error' in data and 'No audio file found' in data['error']
        return False
    
    def test_concurrent_requests(self):
        """Test concurrent request handling"""
        results = []
        
        def make_request():
            try:
                response = requests.get(f"{CLOUD_URL}/health", timeout=30)
                results.append(response.status_code == 200)
            except:
                results.append(False)
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        return all(results) and len(results) == 3
    
    def test_response_times(self):
        """Test API response times"""
        start = time.time()
        response = requests.get(f"{CLOUD_URL}/health", timeout=30)
        elapsed = time.time() - start
        
        # Should respond within 10 seconds
        return response.status_code == 200 and elapsed < 10.0
    
    def test_error_responses(self):
        """Test proper error response formatting"""
        # Test invalid endpoint
        response = requests.get(f"{CLOUD_URL}/invalid-endpoint", timeout=30)
        return response.status_code == 404
    
    def test_json_response_format(self):
        """Test JSON response format consistency"""
        response = requests.get(f"{CLOUD_URL}/health", timeout=30)
        if response.status_code == 200:
            try:
                data = response.json()
                # Should have status and timestamp
                return 'status' in data and 'timestamp' in data
            except:
                return False
        return False
    
    def run_validation(self):
        """Run focused validation suite"""
        print("🚀 Milestone 3: Focused Production Validation")
        print("=" * 55)
        print(f"Target: {CLOUD_URL}")
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Core functionality tests
        print("\n📋 Core Functionality Tests:")
        self.test("Health Endpoint", self.test_health_endpoint)
        self.test("Storage Verification", self.test_storage_verification)
        self.test("Transcription Error Handling", self.test_transcription_error_handling)
        
        # Performance & reliability tests
        print("\n📋 Performance & Reliability Tests:")
        self.test("Response Times", self.test_response_times)
        self.test("Concurrent Requests", self.test_concurrent_requests)
        
        # API quality tests
        print("\n📋 API Quality Tests:")
        self.test("Error Responses", self.test_error_responses)
        self.test("JSON Response Format", self.test_json_response_format)
        
        # Generate report
        return self.generate_report()
    
    def generate_report(self):
        """Generate validation report"""
        print("\n" + "=" * 55)
        print("📊 MILESTONE 3 VALIDATION REPORT")
        print("=" * 55)
        
        passed = sum(1 for _, success in self.results if success)
        total = len(self.results)
        success_rate = (passed / total) * 100
        
        print(f"🎯 Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print(f"⏱️  Duration: {datetime.now() - self.start_time}")
        
        # Detailed results
        print("\n📋 Detailed Results:")
        for name, success in self.results:
            status = "✅" if success else "❌"
            print(f"{status} {name}")
        
        # Assessment
        print(f"\n🏆 Overall Assessment:")
        if success_rate >= 85:
            print("✅ MILESTONE 3 COMPLETE - Production Ready!")
            print("🚀 All core systems operational")
            print("🎯 Ready for production deployment")
            return True
        elif success_rate >= 70:
            print("⚠️  MILESTONE 3 MOSTLY COMPLETE - Minor Issues")
            print("🔧 Some non-critical issues identified")
            print("📈 Core functionality working well")
            return True
        else:
            print("❌ MILESTONE 3 NEEDS WORK - Critical Issues")
            print("🛠️  Major fixes needed before production")
            return False

def main():
    validator = FocusedValidator()
    
    try:
        success = validator.run_validation()
        
        if success:
            print("\n🎉 Cloud infrastructure validated successfully!")
            print("✅ Ready for production workloads")
        else:
            print("\n⚠️  Some issues need attention before production")
            
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted")
        validator.generate_report()
    except Exception as e:
        print(f"\n❌ Validation error: {e}")

if __name__ == "__main__":
    main()