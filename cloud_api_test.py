#!/usr/bin/env python3
"""
Simple API test that can be run on cloud platform
"""
import os
import requests
import json

def test_local_api():
    """Test if we can call our deployed API"""
    try:
        # Test health endpoint
        response = requests.get('http://localhost:8080/health', timeout=10)
        if response.status_code == 200:
            print("✅ Local API health check passed")
            return True
        else:
            print(f"❌ Local API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Local API health check failed: {e}")
        return False

def test_congress_api_with_env():
    """Test Congress API using environment variable"""
    api_key = os.environ.get('CONGRESS_API_KEY')
    if not api_key:
        print("❌ CONGRESS_API_KEY environment variable not set")
        return False
    
    print(f"✅ Found Congress API key: {api_key[:10]}...")
    
    try:
        url = "https://api.congress.gov/v3/member"
        params = {
            'api_key': api_key,
            'format': 'json',
            'limit': 1
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Congress API call successful")
            print(f"Response contains {len(data.get('members', []))} members")
            return True
        else:
            print(f"❌ Congress API call failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Congress API call failed: {e}")
        return False

def main():
    print("🔧 Testing API connectivity from cloud platform")
    print("=" * 50)
    
    success = True
    
    # Test local API
    if not test_local_api():
        success = False
    
    # Test Congress API
    if not test_congress_api_with_env():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed.")

if __name__ == "__main__":
    main()