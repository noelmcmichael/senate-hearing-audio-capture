#!/usr/bin/env python3
"""
Bootstrap production database with minimal committee definitions
Simple approach to enable discovery system
"""

import requests
import json
from datetime import datetime

# Production API base URL
API_BASE = "https://senate-hearing-processor-518203250893.us-central1.run.app"

def bootstrap_via_api():
    """Bootstrap system using API calls"""
    
    print("=== Production Bootstrap via API ===")
    
    # Check current status
    print("1. Checking current status...")
    try:
        response = requests.get(f"{API_BASE}/api/committees")
        data = response.json()
        print(f"   Current committees: {data['total_committees']}")
        print(f"   Current hearings: {data['total_hearings']}")
        
        if data['total_committees'] > 0:
            print("   ✅ Database already has committees!")
            return True
            
    except Exception as e:
        print(f"   ❌ Error checking status: {e}")
        return False
    
    # Try to find a way to add committees
    print("\n2. Attempting to bootstrap committees...")
    
    # Option 1: Try to trigger a sync that might create committees
    try:
        print("   Trying discovery with force flag...")
        response = requests.post(f"{API_BASE}/api/hearings/discover", 
                               json={"force_committee_sync": True})
        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {result}")
            
    except Exception as e:
        print(f"   Discovery attempt failed: {e}")
    
    # Option 2: Check if there's a way to force initialization
    try:
        print("   Checking sync status...")
        response = requests.get(f"{API_BASE}/api/system/sync-status")
        if response.status_code == 200:
            result = response.json()
            print(f"   Sync status: {result}")
            
    except Exception as e:
        print(f"   Sync status check failed: {e}")
    
    # Check if committees appeared
    try:
        response = requests.get(f"{API_BASE}/api/committees")
        data = response.json()
        print(f"\n   Final check - committees: {data['total_committees']}")
        
        if data['total_committees'] > 0:
            print("   ✅ Bootstrap successful!")
            return True
        else:
            print("   ❌ Bootstrap failed - committees still 0")
            return False
            
    except Exception as e:
        print(f"   Final check failed: {e}")
        return False

def test_discovery():
    """Test the discovery system"""
    print("\n=== Testing Discovery System ===")
    
    try:
        print("Running discovery...")
        response = requests.post(f"{API_BASE}/api/hearings/discover", 
                               json={"committee_codes": ["all"]})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Discovery result:")
            print(f"   Total discovered: {result['data']['total_discovered']}")
            print(f"   New hearings: {result['data']['new_hearings']}")
            print(f"   Hearings found: {len(result['data']['hearings'])}")
            
            if result['data']['total_discovered'] > 0:
                print("\n🎉 SUCCESS: Hearings discovered!")
                for hearing in result['data']['hearings'][:3]:  # Show first 3
                    print(f"   - {hearing.get('title', 'Unknown')}")
                return True
            else:
                print("   ❌ Still no hearings discovered")
                return False
                
        else:
            print(f"❌ Discovery failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Discovery error: {e}")
        return False

def main():
    """Main bootstrap process"""
    
    print("🚀 Bootstrap Production System")
    print("=" * 40)
    
    # Step 1: Bootstrap committees
    if bootstrap_via_api():
        print("\n✅ Bootstrap phase completed")
    else:
        print("\n⚠️  Bootstrap phase incomplete")
    
    # Step 2: Test discovery
    if test_discovery():
        print("\n🎉 MILESTONE ACHIEVED!")
        print("   - System has discovered hearings")
        print("   - Ready for manual processing test")
        return True
    else:
        print("\n❌ Discovery still not working")
        print("   - Need to investigate further")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 Next steps:")
        print("1. Check discovered hearings via API")
        print("2. Pick one hearing for manual processing test")
        print("3. Test end-to-end workflow")
    else:
        print("\n🔧 Troubleshooting needed:")
        print("1. Check database connection")
        print("2. Verify Congress API key")
        print("3. Check system logs")