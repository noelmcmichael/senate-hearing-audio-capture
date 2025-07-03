#!/usr/bin/env python3
"""
Production test suite for Senate Hearing Audio Capture
Tests production deployment health, functionality, and performance
"""

import asyncio
import argparse
import json
import sys
import time
import httpx
from typing import Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urljoin

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    duration: float
    details: Optional[Dict] = None

class ProductionTestSuite:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.results: List[TestResult] = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    def add_result(self, name: str, passed: bool, message: str, duration: float, details: Optional[Dict] = None):
        """Add a test result"""
        self.results.append(TestResult(name, passed, message, duration, details))
        
    async def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        print(f"Running {test_name}...")
        start_time = time.time()
        
        try:
            result = await test_func()
            duration = time.time() - start_time
            
            if isinstance(result, dict):
                self.add_result(test_name, True, result.get('message', 'Passed'), duration, result.get('details'))
            else:
                self.add_result(test_name, True, "Passed", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(test_name, False, str(e), duration)
            
    async def test_health_endpoint(self):
        """Test the health endpoint"""
        response = await self.client.get(f"{self.base_url}/health")
        if response.status_code == 200:
            data = response.json()
            return {
                'message': 'Health check passed',
                'details': data
            }
        else:
            raise Exception(f"Health check failed with status {response.status_code}")
            
    async def test_api_documentation(self):
        """Test API documentation endpoint"""
        response = await self.client.get(f"{self.base_url}/docs")
        if response.status_code == 200:
            return {'message': 'API documentation accessible'}
        else:
            raise Exception(f"API documentation failed with status {response.status_code}")
            
    async def test_hearing_list_endpoint(self):
        """Test hearing list endpoint"""
        response = await self.client.get(f"{self.base_url}/api/hearings")
        if response.status_code == 200:
            data = response.json()
            return {
                'message': f'Hearing list returned {len(data)} hearings',
                'details': {'hearing_count': len(data)}
            }
        else:
            raise Exception(f"Hearing list failed with status {response.status_code}")
            
    async def test_committee_list_endpoint(self):
        """Test committee list endpoint"""
        response = await self.client.get(f"{self.base_url}/api/committees")
        if response.status_code == 200:
            data = response.json()
            return {
                'message': f'Committee list returned {len(data)} committees',
                'details': {'committee_count': len(data)}
            }
        else:
            raise Exception(f"Committee list failed with status {response.status_code}")
            
    async def test_system_info_endpoint(self):
        """Test system info endpoint"""
        response = await self.client.get(f"{self.base_url}/api/system/info")
        if response.status_code == 200:
            data = response.json()
            return {
                'message': 'System info retrieved successfully',
                'details': data
            }
        else:
            raise Exception(f"System info failed with status {response.status_code}")
            
    async def test_processing_capability(self):
        """Test basic processing capability"""
        # Test with a sample hearing processing request
        test_payload = {
            "hearing_id": "test-hearing-1",
            "dry_run": True
        }
        
        response = await self.client.post(f"{self.base_url}/api/process/hearing", json=test_payload)
        if response.status_code in [200, 202]:
            data = response.json()
            return {
                'message': 'Processing capability test passed',
                'details': data
            }
        else:
            raise Exception(f"Processing test failed with status {response.status_code}")
            
    async def test_database_connectivity(self):
        """Test database connectivity"""
        response = await self.client.get(f"{self.base_url}/api/system/health/database")
        if response.status_code == 200:
            data = response.json()
            return {
                'message': 'Database connectivity verified',
                'details': data
            }
        else:
            raise Exception(f"Database connectivity failed with status {response.status_code}")
            
    async def test_redis_connectivity(self):
        """Test Redis connectivity"""
        response = await self.client.get(f"{self.base_url}/api/system/health/redis")
        if response.status_code == 200:
            data = response.json()
            return {
                'message': 'Redis connectivity verified',
                'details': data
            }
        else:
            raise Exception(f"Redis connectivity failed with status {response.status_code}")
            
    async def test_authentication_security(self):
        """Test authentication and security"""
        # Test that sensitive endpoints require authentication
        sensitive_endpoints = [
            '/api/admin/system',
            '/api/admin/users',
            '/api/system/logs'
        ]
        
        authenticated_count = 0
        for endpoint in sensitive_endpoints:
            response = await self.client.get(f"{self.base_url}{endpoint}")
            if response.status_code in [401, 403]:
                authenticated_count += 1
                
        if authenticated_count == len(sensitive_endpoints):
            return {
                'message': 'Authentication security verified',
                'details': {'protected_endpoints': authenticated_count}
            }
        else:
            raise Exception(f"Security issue: {len(sensitive_endpoints) - authenticated_count} endpoints not protected")
            
    async def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        # Test response times for key endpoints
        endpoints = [
            '/health',
            '/api/hearings',
            '/api/committees'
        ]
        
        response_times = {}
        for endpoint in endpoints:
            start_time = time.time()
            response = await self.client.get(f"{self.base_url}{endpoint}")
            duration = time.time() - start_time
            response_times[endpoint] = duration
            
            if response.status_code != 200:
                raise Exception(f"Performance test failed for {endpoint}")
                
        avg_response_time = sum(response_times.values()) / len(response_times)
        
        if avg_response_time < 2.0:  # Less than 2 seconds average
            return {
                'message': f'Performance benchmark passed (avg: {avg_response_time:.2f}s)',
                'details': {'response_times': response_times, 'average': avg_response_time}
            }
        else:
            raise Exception(f"Performance benchmark failed: avg response time {avg_response_time:.2f}s")
            
    async def test_error_handling(self):
        """Test error handling"""
        # Test various error scenarios
        test_cases = [
            ('/api/hearings/nonexistent', 404),
            ('/api/process/hearing', 400),  # Missing required fields
            ('/api/invalid-endpoint', 404)
        ]
        
        passed_cases = 0
        for endpoint, expected_status in test_cases:
            response = await self.client.get(f"{self.base_url}{endpoint}")
            if response.status_code == expected_status:
                passed_cases += 1
                
        if passed_cases == len(test_cases):
            return {
                'message': 'Error handling test passed',
                'details': {'test_cases_passed': passed_cases}
            }
        else:
            raise Exception(f"Error handling test failed: {passed_cases}/{len(test_cases)} cases passed")
            
    async def run_all_tests(self):
        """Run all production tests"""
        print(f"Starting production test suite for {self.base_url}")
        print("=" * 60)
        
        # Core functionality tests
        await self.run_test("Health Endpoint", self.test_health_endpoint)
        await self.run_test("API Documentation", self.test_api_documentation)
        await self.run_test("Hearing List", self.test_hearing_list_endpoint)
        await self.run_test("Committee List", self.test_committee_list_endpoint)
        await self.run_test("System Info", self.test_system_info_endpoint)
        
        # Processing capability
        await self.run_test("Processing Capability", self.test_processing_capability)
        
        # Infrastructure tests
        await self.run_test("Database Connectivity", self.test_database_connectivity)
        await self.run_test("Redis Connectivity", self.test_redis_connectivity)
        
        # Security tests
        await self.run_test("Authentication Security", self.test_authentication_security)
        
        # Performance tests
        await self.run_test("Performance Benchmarks", self.test_performance_benchmarks)
        
        # Error handling
        await self.run_test("Error Handling", self.test_error_handling)
        
        return self.generate_report()
        
    def generate_report(self):
        """Generate test report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("PRODUCTION TEST RESULTS")
        print("=" * 60)
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} {result.name} ({result.duration:.2f}s)")
            if not result.passed:
                print(f"    Error: {result.message}")
            elif result.details:
                print(f"    Details: {result.message}")
                
        print("\n" + "=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ PRODUCTION TESTS FAILED")
            return False
        else:
            print("\n✅ ALL PRODUCTION TESTS PASSED")
            return True

async def main():
    parser = argparse.ArgumentParser(description='Production Test Suite for Senate Hearing Audio Capture')
    parser.add_argument('--url', required=True, help='Base URL of the deployed application')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    parser.add_argument('--output', help='Output file for test results (JSON format)')
    
    args = parser.parse_args()
    
    async with ProductionTestSuite(args.url, args.timeout) as test_suite:
        success = await test_suite.run_all_tests()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump([{
                    'name': r.name,
                    'passed': r.passed,
                    'message': r.message,
                    'duration': r.duration,
                    'details': r.details
                } for r in test_suite.results], f, indent=2)
                
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())