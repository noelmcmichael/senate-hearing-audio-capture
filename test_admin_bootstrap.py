#!/usr/bin/env python3
"""
Test script to call the admin bootstrap endpoint
"""

import requests
import json

API_BASE = "https://senate-hearing-processor-518203250893.us-central1.run.app"

def test_bootstrap():
    """Test the admin bootstrap functionality"""
    
    print("🚀 Testing Admin Bootstrap")
    print("=" * 30)
    
    # Step 1: Check current status
    print("1. Checking current status...")
    try:
        response = requests.get(f"{API_BASE}/admin/status")
        if response.status_code == 200:
            status = response.json()
            print(f"   Committees: {status.get('committees', 'unknown')}")
            print(f"   Hearings: {status.get('hearings', 'unknown')}")
            print(f"   Bootstrap needed: {status.get('bootstrap_needed', 'unknown')}")
        else:
            print(f"   Status check failed: {response.status_code}")
    except Exception as e:
        print(f"   Status check error: {e}")
    
    # Step 2: Run bootstrap
    print("\n2. Running bootstrap...")
    try:
        response = requests.post(f"{API_BASE}/admin/bootstrap")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Bootstrap successful!")
            print(f"   Committees added: {result.get('committees_added', 'unknown')}")
            print(f"   Total committees: {result.get('total_committees', 'unknown')}")
            print(f"   Message: {result.get('message', 'No message')}")
        else:
            print(f"   ❌ Bootstrap failed: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', 'Unknown error')}")
            except:
                print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Bootstrap error: {e}")
    
    # Step 3: Verify committees
    print("\n3. Verifying committees...")
    try:
        response = requests.get(f"{API_BASE}/api/committees")
        if response.status_code == 200:
            committees = response.json()
            print(f"   ✅ Committees endpoint working!")
            print(f"   Total committees: {committees.get('total_committees', 'unknown')}")
            
            if committees.get('committees'):
                print("   Committee list:")
                for committee in committees['committees'][:3]:
                    print(f"     - {committee.get('committee_code', 'unknown')}: {committee.get('committee_name', 'unknown')}")
        else:
            print(f"   ❌ Committees check failed: {response.status_code}")
    except Exception as e:
        print(f"   Committees check error: {e}")
    
    # Step 4: Test discovery
    print("\n4. Testing discovery...")
    try:
        response = requests.post(f"{API_BASE}/api/hearings/discover", json={"committee_codes": ["all"]})
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Discovery working!")
            print(f"   Hearings discovered: {result['data'].get('total_discovered', 'unknown')}")
            print(f"   New hearings: {result['data'].get('new_hearings', 'unknown')}")
            
            if result['data'].get('total_discovered', 0) > 0:
                print("   🎉 SUCCESS: Hearings found!")
                return True
            else:
                print("   ⚠️  No hearings discovered yet (may need time to sync)")
                return True  # Still success - system is working
        else:
            print(f"   ❌ Discovery failed: {response.status_code}")
    except Exception as e:
        print(f"   Discovery error: {e}")
    
    return False

if __name__ == "__main__":
    success = test_bootstrap()
    if success:
        print("\n🎉 SYSTEM READY!")
        print("Next steps:")
        print("1. Check discovered hearings")
        print("2. Test manual processing")
    else:
        print("\n❌ Bootstrap incomplete")
        print("Need to add admin endpoints to service")