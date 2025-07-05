#!/usr/bin/env python3
"""
Fix API response parsing issues and test endpoints
"""

import requests
import json
from datetime import datetime

def test_api_endpoints():
    """Test API endpoints with better error handling"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print("🔧 TESTING API ENDPOINTS WITH DETAILED RESPONSES")
    print("=" * 60)
    
    # Test committees endpoint
    print("\n📋 TESTING COMMITTEES ENDPOINT")
    try:
        response = requests.get(f"{base_url}/api/committees", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Raw Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ JSON parsed successfully")
                print(f"Type: {type(data)}")
                print(f"Content: {data}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test hearings endpoint  
    print("\n📋 TESTING HEARINGS ENDPOINT")
    try:
        response = requests.get(f"{base_url}/api/hearings", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Raw Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ JSON parsed successfully")
                print(f"Type: {type(data)}")
                print(f"Count: {len(data) if isinstance(data, list) else 'Not a list'}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test discovery endpoint
    print("\n🔍 TESTING DISCOVERY ENDPOINT")
    try:
        response = requests.post(f"{base_url}/api/hearings/discover", 
                               json={"committee_codes": ["SCOM"]},
                               timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Raw Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ JSON parsed successfully")
                print(f"Discovery result: {data}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test admin bootstrap
    print("\n🏗️ TESTING ADMIN BOOTSTRAP")
    try:
        response = requests.post(f"{base_url}/admin/bootstrap", timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Raw Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Bootstrap result: {data}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")

def main():
    """Main function"""
    
    print(f"🔧 API ENDPOINT TESTING AND DEBUGGING")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    test_api_endpoints()
    
    print("\n🎯 NEXT STEPS")
    print("=" * 60)
    print("1. Fix any API response format issues")
    print("2. Run bootstrap to populate initial data")
    print("3. Test discovery service")
    print("4. Proceed with hearing discovery")

if __name__ == "__main__":
    main()