#!/usr/bin/env python3
"""
Use the Congress API to bootstrap committees
This leverages the fact that the service has Congress API access
"""

import requests
import json
import time

API_BASE = "https://senate-hearing-processor-518203250893.us-central1.run.app"

def try_congress_api_bootstrap():
    """Try to use Congress API to bootstrap committees"""
    
    print("🚀 Congress API Bootstrap Attempt")
    print("=" * 35)
    
    # The service has Congress API access - let's try to leverage it
    # Maybe there's a way to force committee sync through discovery
    
    # Try different discovery approaches
    attempts = [
        {"force_committee_discovery": True, "committee_codes": ["all"]},
        {"initialize_committees": True, "committee_codes": ["SCOM", "SSCI", "SSJU"]},
        {"bootstrap_mode": True, "committee_codes": ["all"]},
        {"create_committees": True, "committee_codes": ["SCOM", "SSCI", "SSJU"]},
        {"sync_committees": True, "committee_codes": ["all"]},
    ]
    
    for i, attempt in enumerate(attempts, 1):
        print(f"\n{i}. Trying discovery approach: {attempt}")
        
        try:
            response = requests.post(f"{API_BASE}/api/hearings/discover", json=attempt)
            if response.status_code == 200:
                result = response.json()
                print(f"   Response: {result.get('message', 'No message')}")
                
                # Check if committees were created
                committee_check = requests.get(f"{API_BASE}/api/committees")
                if committee_check.status_code == 200:
                    committees = committee_check.json()
                    committee_count = committees.get('total_committees', 0)
                    print(f"   Committees after attempt: {committee_count}")
                    
                    if committee_count > 0:
                        print(f"   ✅ SUCCESS! Bootstrap worked!")
                        return True
                        
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n❌ Congress API bootstrap unsuccessful")
    return False

def try_simple_discovery_loop():
    """Try running discovery multiple times to see if it bootstraps"""
    
    print("\n🔄 Trying Discovery Loop")
    print("=" * 25)
    
    for i in range(3):
        print(f"\nAttempt {i+1}:")
        
        try:
            response = requests.post(f"{API_BASE}/api/hearings/discover", 
                                   json={"committee_codes": ["all"]})
            if response.status_code == 200:
                result = response.json()
                print(f"   Discovered: {result['data'].get('total_discovered', 0)}")
                
                # Check committees
                committee_check = requests.get(f"{API_BASE}/api/committees")
                if committee_check.status_code == 200:
                    committees = committee_check.json()
                    committee_count = committees.get('total_committees', 0)
                    print(f"   Committees: {committee_count}")
                    
                    if committee_count > 0:
                        print(f"   ✅ Committees appeared!")
                        return True
                        
        except Exception as e:
            print(f"   Error: {e}")
        
        time.sleep(2)  # Wait 2 seconds between attempts
    
    return False

def main():
    """Main bootstrap attempt"""
    
    print("🎯 Alternative Bootstrap Approaches")
    print("=" * 40)
    
    # Check initial state
    print("Initial state:")
    try:
        response = requests.get(f"{API_BASE}/api/committees")
        if response.status_code == 200:
            data = response.json()
            print(f"   Committees: {data.get('total_committees', 0)}")
    except:
        pass
    
    # Try Congress API bootstrap
    if try_congress_api_bootstrap():
        print("\n🎉 Congress API bootstrap successful!")
    elif try_simple_discovery_loop():
        print("\n🎉 Discovery loop successful!")
    else:
        print("\n❌ All bootstrap attempts failed")
        print("\nRECOMMENDATION:")
        print("The service needs admin endpoints to bootstrap.")
        print("The architecture is sound, just needs initialization.")
        return False
    
    # Final test
    print("\n🧪 Final Test:")
    try:
        response = requests.post(f"{API_BASE}/api/hearings/discover", 
                               json={"committee_codes": ["all"]})
        if response.status_code == 200:
            result = response.json()
            hearings = result['data'].get('total_discovered', 0)
            print(f"   Hearings discovered: {hearings}")
            
            if hearings > 0:
                print("   🎉 MILESTONE ACHIEVED!")
                print("   System is discovering hearings!")
                return True
                
    except Exception as e:
        print(f"   Final test error: {e}")
    
    return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 READY FOR MANUAL PROCESSING TEST!")
    else:
        print("\n🔧 Need to add admin endpoints to service")