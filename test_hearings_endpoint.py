#!/usr/bin/env python3
"""
Test the hearings endpoint with proper routing
"""

import requests
import json
from datetime import datetime

def test_hearings_api():
    """Test various hearings API endpoints"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print("🔍 TESTING HEARINGS API ENDPOINTS")
    print("=" * 60)
    
    # Test different hearing endpoint variations
    endpoints = [
        "/api/hearings",
        "/api/hearings/",
        "/hearings",
        "/api/hearings/list",
        "/api/hearings/all"
    ]
    
    for endpoint in endpoints:
        print(f"\n📋 Testing: {endpoint}")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"Status: {response.status_code}")
            content_type = response.headers.get('content-type', '')
            print(f"Content-Type: {content_type}")
            
            if 'application/json' in content_type:
                try:
                    data = response.json()
                    print(f"✅ JSON Response: {len(data) if isinstance(data, list) else 'Not a list'}")
                    if isinstance(data, list) and len(data) > 0:
                        print(f"First hearing: {data[0]}")
                    elif isinstance(data, dict):
                        print(f"Response data: {data}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
            else:
                print(f"❌ Non-JSON response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    # Test individual hearing access
    print(f"\n📋 Testing: Committee-specific hearings")
    committees = ["SCOM", "SSCI", "SSJU"]
    
    for committee in committees:
        try:
            response = requests.get(f"{base_url}/api/committees/{committee}/hearings", timeout=10)
            print(f"{committee}: Status {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  ✅ {committee} hearings: {len(data) if isinstance(data, list) else 'Not a list'}")
                except:
                    print(f"  ❌ {committee} response not JSON")
        except Exception as e:
            print(f"  ❌ {committee} failed: {e}")

def test_frontend_api():
    """Test the frontend to see what it's actually calling"""
    
    print("\n🌐 TESTING FRONTEND API CALLS")
    print("=" * 60)
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    # Check if there's an API docs endpoint
    try:
        response = requests.get(f"{base_url}/api/docs", timeout=10)
        print(f"API Docs: {response.status_code}")
        if response.status_code == 200:
            print("✅ API documentation available")
    except Exception as e:
        print(f"❌ API docs failed: {e}")
    
    # Check direct database status
    try:
        response = requests.get(f"{base_url}/admin/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Database status: {data}")
    except Exception as e:
        print(f"❌ Database status failed: {e}")

def main():
    """Main function"""
    
    print(f"🔍 COMPREHENSIVE HEARINGS API TESTING")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    test_hearings_api()
    test_frontend_api()
    
    print("\n🎯 ANALYSIS")
    print("=" * 60)
    print("The system has 6 hearings but the API routing may be incorrect.")
    print("The /api/hearings endpoint returns HTML instead of JSON.")
    print("This suggests the API routes are not properly configured.")
    print("Next: Check the React app and see what's actually displayed.")

if __name__ == "__main__":
    main()