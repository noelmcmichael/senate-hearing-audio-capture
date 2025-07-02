#!/usr/bin/env python3
"""
Quick integration test to verify what's actually working
"""
import requests
import json

def test_backend_endpoints():
    """Test key backend endpoints"""
    base_url = "http://localhost:8001"
    
    print("🧪 Testing Backend Integration")
    print("=" * 50)
    
    # Test 1: API Health
    try:
        response = requests.get(f"{base_url}/api")
        if response.status_code == 200:
            print("✅ API Health: WORKING")
            data = response.json()
            print(f"   Version: {data.get('version', 'Unknown')}")
        else:
            print(f"❌ API Health: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ API Health: ERROR - {e}")
    
    # Test 2: Committee Data
    try:
        response = requests.get(f"{base_url}/api/committees")
        if response.status_code == 200:
            committees = response.json()
            print(f"✅ Committees: WORKING ({len(committees)} committees)")
        else:
            print(f"❌ Committees: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Committees: ERROR - {e}")
    
    # Test 3: Sample Hearing Data
    try:
        response = requests.get(f"{base_url}/api/committees/SCOM/hearings")
        if response.status_code == 200:
            data = response.json()
            hearings = data.get('hearings', [])
            if hearings:
                sample = hearings[0]
                print(f"✅ Hearing Data: WORKING ({len(hearings)} SCOM hearings)")
                print(f"   Sample: {sample.get('hearing_title', 'No title')[:50]}...")
                print(f"   Stage: {sample.get('processing_stage', 'Unknown')}")
                print(f"   Status: {sample.get('status', 'Unknown')}")
                return sample['id']  # Return for further testing
            else:
                print("⚠️  Hearing Data: NO HEARINGS FOUND")
        else:
            print(f"❌ Hearing Data: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Hearing Data: ERROR - {e}")
    
    return None

def test_hearing_details(hearing_id):
    """Test hearing details endpoint"""
    if not hearing_id:
        return
        
    base_url = "http://localhost:8001"
    
    try:
        response = requests.get(f"{base_url}/api/hearings/{hearing_id}")
        if response.status_code == 200:
            hearing = response.json()
            print(f"✅ Hearing Details: WORKING")
            print(f"   Title: {hearing.get('hearing_title', 'No title')}")
            print(f"   Pipeline Stage: {hearing.get('processing_stage', 'Unknown')}")
            print(f"   Has Streams: {hearing.get('has_streams', False)}")
            print(f"   Capture Readiness: {hearing.get('capture_readiness', {}).get('score', 'Unknown')}")
        else:
            print(f"❌ Hearing Details: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Hearing Details: ERROR - {e}")

def test_capture_endpoint(hearing_id):
    """Test capture functionality"""
    if not hearing_id:
        return
        
    base_url = "http://localhost:8001"
    
    try:
        payload = {
            "hearing_id": str(hearing_id),
            "priority": 1,
            "capture_options": {"quality": "high", "format": "wav"}
        }
        
        # Note: This endpoint requires user_id parameter
        response = requests.post(
            f"{base_url}/api/hearings/{hearing_id}/capture?user_id=test_user",
            json=payload
        )
        
        if response.status_code in [200, 201]:
            print("✅ Capture Endpoint: WORKING")
            print(f"   Response: {response.json()}")
        elif response.status_code == 422:
            print("⚠️  Capture Endpoint: VALIDATION ERROR (expected)")
            print(f"   Details: {response.json()}")
        else:
            print(f"❌ Capture Endpoint: FAILED ({response.status_code})")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Capture Endpoint: ERROR - {e}")

def main():
    print("🎯 Senate Hearing Audio Capture - Integration Test")
    print("=" * 60)
    
    # Test backend
    hearing_id = test_backend_endpoints()
    
    print("\n" + "=" * 50)
    
    # Test specific hearing
    if hearing_id:
        test_hearing_details(hearing_id)
        print()
        test_capture_endpoint(hearing_id)
    
    print("\n" + "=" * 50)
    print("Integration test complete!")

if __name__ == "__main__":
    main()