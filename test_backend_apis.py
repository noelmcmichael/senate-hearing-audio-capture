#!/usr/bin/env python3
"""
Test backend APIs directly to diagnose frontend issues.
"""
import requests
import json
import time
from datetime import datetime

# Production service URL
BASE_URL = "https://senate-hearing-processor-518203250893.us-central1.run.app"

def test_endpoint(endpoint, method="GET", expected_status=200, description=""):
    """Test a single endpoint and return results."""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testing {method} {endpoint}")
    print(f"   Description: {description}")
    print(f"   URL: {url}")
    
    try:
        start_time = time.time()
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, timeout=30)
        
        duration = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Duration: {duration:.2f}s")
        
        if response.status_code == expected_status:
            print("   ✅ SUCCESS")
            
            # Try to parse JSON response
            try:
                data = response.json()
                if isinstance(data, dict):
                    print(f"   Response keys: {list(data.keys())}")
                    if 'count' in data:
                        print(f"   Count: {data['count']}")
                elif isinstance(data, list):
                    print(f"   Response: List with {len(data)} items")
                return True, data
            except:
                print(f"   Response: Non-JSON ({len(response.text)} chars)")
                return True, response.text
        else:
            print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False, None
            
    except Exception as e:
        print(f"   ❌ ERROR - {str(e)}")
        return False, None

def main():
    """Run comprehensive backend API tests."""
    print("="*60)
    print("🚀 BACKEND API VALIDATION TEST")
    print("="*60)
    print(f"Testing service at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test critical endpoints
    endpoints = [
        ("/health", "GET", 200, "Health check endpoint"),
        ("/admin/status", "GET", 200, "Admin status endpoint"),
        ("/api/committees", "GET", 200, "List committees"),
        ("/api/hearings/discover", "POST", 200, "Discover hearings"),
        ("/", "GET", 200, "Frontend root"),
        ("/admin", "GET", 200, "Admin page"),
    ]
    
    results = []
    
    for endpoint, method, expected_status, description in endpoints:
        success, data = test_endpoint(endpoint, method, expected_status, description)
        results.append({
            'endpoint': endpoint,
            'success': success,
            'data': data
        })
        
        # Small delay between requests
        time.sleep(0.5)
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    # Show specific issues
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for test in failed_tests:
            print(f"   - {test['endpoint']}")
    
    # Check if we have committee data
    committee_result = next((r for r in results if r['endpoint'] == '/api/committees'), None)
    if committee_result and committee_result['success']:
        committees = committee_result['data']
        if isinstance(committees, list):
            print(f"\n📋 COMMITTEE DATA:")
            print(f"   Found {len(committees)} committees")
            for committee in committees[:3]:  # Show first 3
                if isinstance(committee, dict):
                    print(f"   - {committee.get('code', 'N/A')}: {committee.get('name', 'N/A')}")
    
    print("\n🔍 NEXT STEPS:")
    if successful_tests == total_tests:
        print("   ✅ All backend APIs working - investigate frontend issues")
    else:
        print("   ❌ Backend API issues detected - fix backend first")
    
    return successful_tests == total_tests

if __name__ == "__main__":
    main()