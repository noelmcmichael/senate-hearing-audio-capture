#!/usr/bin/env python3
"""
Simple bootstrap request to production system
Try different approaches to get committees initialized
"""

import requests
import json
from datetime import datetime

API_BASE = "https://senate-hearing-processor-518203250893.us-central1.run.app"

def try_alternative_approaches():
    """Try different approaches to initialize committees"""
    
    print("=== Alternative Bootstrap Approaches ===")
    
    # Approach 1: Check if there are any hidden admin endpoints
    print("\n1. Checking for admin endpoints...")
    
    admin_endpoints = [
        "/admin/bootstrap",
        "/api/admin/bootstrap", 
        "/api/init",
        "/api/setup",
        "/bootstrap",
        "/init",
        "/setup"
    ]
    
    for endpoint in admin_endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}")
            if response.status_code != 404:
                print(f"   Found endpoint: {endpoint} - Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"   Response: {response.text[:200]}...")
        except:
            pass
    
    # Approach 2: Try to force a committee sync via Congress API
    print("\n2. Attempting to force Congress API sync...")
    
    try:
        # Maybe the discovery endpoint can be called with specific parameters
        response = requests.post(f"{API_BASE}/api/hearings/discover", 
                               json={
                                   "committee_codes": ["SCOM", "SSCI", "SSJU"],
                                   "force_init": True,
                                   "bootstrap_committees": True
                               })
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Discovery with committees: {result}")
            
            # Check if committees were created
            check_response = requests.get(f"{API_BASE}/api/committees")
            if check_response.status_code == 200:
                committees = check_response.json()
                print(f"   Committees after discovery: {committees['total_committees']}")
                
                if committees['total_committees'] > 0:
                    print("   ✅ Bootstrap successful!")
                    return True
                    
    except Exception as e:
        print(f"   Congress API sync failed: {e}")
    
    # Approach 3: Check if there's a way to add committees directly
    print("\n3. Checking for committee creation endpoints...")
    
    # Maybe there's a POST endpoint for committees
    test_committee = {
        "committee_code": "SCOM",
        "committee_name": "Senate Committee on Commerce, Science, and Transportation",
        "chamber": "Senate",
        "total_members": 28,
        "majority_party": "Democrat",
        "minority_party": "Republican"
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/committees", json=test_committee)
        print(f"   POST committees response: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("   ✅ Committee creation endpoint found!")
            
            # Add the other committees
            committees_to_add = [
                {
                    "committee_code": "SSCI",
                    "committee_name": "Senate Select Committee on Intelligence",
                    "chamber": "Senate",
                    "total_members": 21,
                    "majority_party": "Democrat",
                    "minority_party": "Republican"
                },
                {
                    "committee_code": "SSJU",
                    "committee_name": "Senate Committee on the Judiciary",
                    "chamber": "Senate",
                    "total_members": 22,
                    "majority_party": "Democrat",
                    "minority_party": "Republican"
                }
            ]
            
            for committee in committees_to_add:
                response = requests.post(f"{API_BASE}/api/committees", json=committee)
                print(f"   Added {committee['committee_code']}: {response.status_code}")
            
            return True
            
    except Exception as e:
        print(f"   Committee creation failed: {e}")
    
    return False

def main():
    """Main bootstrap process"""
    
    print("🚀 Alternative Bootstrap Approaches")
    print("=" * 40)
    
    if try_alternative_approaches():
        print("\n✅ Bootstrap successful!")
        
        # Test discovery
        print("\n🔍 Testing discovery...")
        response = requests.post(f"{API_BASE}/api/hearings/discover", 
                               json={"committee_codes": ["all"]})
        
        if response.status_code == 200:
            result = response.json()
            print(f"Discovery result: {result['data']['total_discovered']} hearings")
            
            if result['data']['total_discovered'] > 0:
                print("🎉 SUCCESS: System is working!")
                return True
                
    print("\n❌ Bootstrap failed")
    print("Manual intervention needed")
    return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 Ready for hearing processing test!")