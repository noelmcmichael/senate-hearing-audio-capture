#!/usr/bin/env python3
"""
Bootstrap the production system with committees and test data.
"""
import requests
import json
import time
from datetime import datetime

# Production service URL
BASE_URL = "https://senate-hearing-processor-518203250893.us-central1.run.app"

def bootstrap_committees():
    """Bootstrap the committees in the production system."""
    print("🔄 Bootstrapping committees...")
    
    # Committee data to bootstrap
    committees = [
        {
            "code": "SCOM",
            "name": "Senate Committee on Commerce, Science, and Transportation",
            "type": "Senate"
        },
        {
            "code": "SSCI",
            "name": "Senate Select Committee on Intelligence",
            "type": "Senate"
        },
        {
            "code": "SSJU",
            "name": "Senate Committee on the Judiciary",
            "type": "Senate"
        }
    ]
    
    for committee in committees:
        try:
            response = requests.post(
                f"{BASE_URL}/admin/committees",
                json=committee,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"   ✅ Added {committee['code']}: {committee['name']}")
            else:
                print(f"   ❌ Failed to add {committee['code']}: {response.text}")
        except Exception as e:
            print(f"   ❌ Error adding {committee['code']}: {e}")
    
    print()

def bootstrap_hearings():
    """Bootstrap some test hearings."""
    print("🔄 Bootstrapping test hearings...")
    
    # Test hearings to bootstrap
    hearings = [
        {
            "committee_code": "SCOM",
            "title": "Oversight of the Federal Aviation Administration",
            "date": "2024-01-15",
            "url": "https://www.commerce.senate.gov/hearings/oversight-of-the-federal-aviation-administration"
        },
        {
            "committee_code": "SSCI",
            "title": "Annual Threat Assessment",
            "date": "2024-01-18",
            "url": "https://www.intelligence.senate.gov/hearings/annual-threat-assessment"
        },
        {
            "committee_code": "SSJU",
            "title": "Oversight of the Department of Justice",
            "date": "2024-01-22",
            "url": "https://www.judiciary.senate.gov/hearings/oversight-of-the-department-of-justice"
        }
    ]
    
    for hearing in hearings:
        try:
            response = requests.post(
                f"{BASE_URL}/admin/hearings",
                json=hearing,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"   ✅ Added hearing: {hearing['title']}")
            else:
                print(f"   ❌ Failed to add hearing: {response.text}")
        except Exception as e:
            print(f"   ❌ Error adding hearing: {e}")
    
    print()

def verify_bootstrap():
    """Verify the bootstrap was successful."""
    print("🔍 Verifying bootstrap...")
    
    try:
        # Check committees
        response = requests.get(f"{BASE_URL}/api/committees", timeout=30)
        if response.status_code == 200:
            data = response.json()
            committees_count = data.get('total_committees', 0)
            hearings_count = data.get('total_hearings', 0)
            
            print(f"   📊 Committees: {committees_count}")
            print(f"   📊 Hearings: {hearings_count}")
            
            if committees_count > 0:
                print("   ✅ Bootstrap successful!")
                return True
            else:
                print("   ❌ Bootstrap failed - no committees found")
                return False
        else:
            print(f"   ❌ Failed to verify: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error verifying: {e}")
        return False

def test_discovery():
    """Test the discovery system."""
    print("🔄 Testing discovery system...")
    
    try:
        # Test discovery with proper payload
        response = requests.post(
            f"{BASE_URL}/api/hearings/discover",
            json={"committee_codes": ["SCOM", "SSCI", "SSJU"]},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Discovery successful")
            print(f"   📊 Committees processed: {data.get('committees_processed', 0)}")
            print(f"   📊 Hearings discovered: {data.get('hearings_discovered', 0)}")
        else:
            print(f"   ❌ Discovery failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error in discovery: {e}")

def main():
    """Main bootstrap process."""
    print("="*60)
    print("🚀 PRODUCTION SYSTEM BOOTSTRAP")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Bootstrap committees
    bootstrap_committees()
    
    # Step 2: Bootstrap test hearings
    bootstrap_hearings()
    
    # Step 3: Verify bootstrap
    success = verify_bootstrap()
    
    # Step 4: Test discovery
    if success:
        test_discovery()
    
    print("\n" + "="*60)
    print("✅ BOOTSTRAP COMPLETE")
    print("="*60)
    
    if success:
        print("🎉 System is ready for use!")
        print(f"🌐 Frontend: {BASE_URL}")
        print(f"📚 API Docs: {BASE_URL}/docs")
        print(f"⚙️ Admin: {BASE_URL}/admin")
    else:
        print("❌ Bootstrap failed - check logs above")

if __name__ == "__main__":
    main()