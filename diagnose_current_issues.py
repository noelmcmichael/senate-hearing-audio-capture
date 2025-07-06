#!/usr/bin/env python3
"""
Diagnose current system issues and get it working properly
"""

import requests
import json
from datetime import datetime

def check_frontend_display():
    """Check what the frontend is actually showing"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print("🔍 CHECKING FRONTEND DISPLAY")
    print("=" * 60)
    
    try:
        # Get the main page
        response = requests.get(base_url, timeout=10)
        print(f"Frontend Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            # Check for key content
            if "hearings" in content.lower():
                print("✅ Frontend mentions hearings")
            else:
                print("❌ Frontend does not mention hearings")
                
            if "committee" in content.lower():
                print("✅ Frontend mentions committees")
            else:
                print("❌ Frontend does not mention committees")
                
            # Look for actual numbers
            if "6 of 6" in content:
                print("✅ Frontend shows '6 of 6' hearings")
            elif "0 of 0" in content:
                print("❌ Frontend shows '0 of 0' hearings - NO DATA")
            else:
                print("❓ Frontend hearing count unclear")
                
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Frontend check failed: {e}")

def check_api_endpoints():
    """Check all critical API endpoints"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print("\n🔍 CHECKING API ENDPOINTS")
    print("=" * 60)
    
    # Critical endpoints to check
    endpoints = [
        ("/health", "Health Check"),
        ("/api/committees", "Committees"),
        ("/api/hearings/queue", "Hearing Queue"),
        ("/admin/status", "Admin Status"),
        ("/admin/bootstrap", "Bootstrap")
    ]
    
    for endpoint, name in endpoints:
        try:
            if endpoint == "/admin/bootstrap":
                # POST request for bootstrap
                response = requests.post(f"{base_url}{endpoint}", timeout=30)
            else:
                # GET request for others
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                
            print(f"\n{name} ({endpoint}):")
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if endpoint == "/api/committees":
                        committees = data.get('committees', [])
                        print(f"  ✅ {len(committees)} committees found")
                        for committee in committees:
                            print(f"    - {committee.get('code', 'Unknown')}: {committee.get('name', 'No name')}")
                    elif endpoint == "/api/hearings/queue":
                        hearings = data.get('hearings', [])
                        print(f"  ✅ {len(hearings)} hearings in queue")
                        for hearing in hearings[:3]:  # Show first 3
                            print(f"    - {hearing.get('title', 'No title')[:50]}...")
                    elif endpoint == "/admin/status":
                        print(f"  ✅ Status: {data.get('status', 'Unknown')}")
                        print(f"  ✅ Committees: {data.get('committees', 'Unknown')}")
                        print(f"  ✅ Hearings: {data.get('hearings', 'Unknown')}")
                    elif endpoint == "/admin/bootstrap":
                        print(f"  ✅ Bootstrap: {data.get('message', 'Unknown')}")
                        print(f"  ✅ Committees Added: {data.get('committees_added', 'Unknown')}")
                        print(f"  ✅ Total Hearings: {data.get('total_hearings', 'Unknown')}")
                    else:
                        print(f"  ✅ Response: {data}")
                except json.JSONDecodeError:
                    print(f"  ❌ Non-JSON response: {response.text[:100]}...")
            else:
                print(f"  ❌ Failed: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_database_bootstrap():
    """Test database bootstrap specifically"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print("\n🔍 TESTING DATABASE BOOTSTRAP")
    print("=" * 60)
    
    try:
        # Force bootstrap
        print("Triggering bootstrap...")
        response = requests.post(f"{base_url}/admin/bootstrap", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Bootstrap Success:")
            print(f"  Message: {data.get('message', 'No message')}")
            print(f"  Committees Added: {data.get('committees_added', 0)}")
            print(f"  Total Committees: {data.get('total_committees', 0)}")
            print(f"  Total Hearings: {data.get('total_hearings', 0)}")
            
            # Check if data was actually created
            if data.get('total_committees', 0) > 0 and data.get('total_hearings', 0) > 0:
                print("✅ Bootstrap created data successfully")
                return True
            else:
                print("❌ Bootstrap did not create expected data")
                return False
        else:
            print(f"❌ Bootstrap failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Bootstrap error: {e}")
        return False

def fix_system_issues():
    """Try to fix identified issues"""
    
    print("\n🔧 ATTEMPTING TO FIX SYSTEM ISSUES")
    print("=" * 60)
    
    # Step 1: Force bootstrap
    print("1. Force bootstrapping system...")
    bootstrap_success = test_database_bootstrap()
    
    if bootstrap_success:
        print("✅ Bootstrap successful")
        
        # Step 2: Wait a moment for data to propagate
        import time
        print("2. Waiting for data propagation...")
        time.sleep(3)
        
        # Step 3: Check if data is now available
        print("3. Checking data availability...")
        check_api_endpoints()
        
        # Step 4: Check frontend again
        print("4. Checking frontend display...")
        check_frontend_display()
        
        return True
    else:
        print("❌ Bootstrap failed - system needs manual intervention")
        return False

def main():
    """Main diagnostic function"""
    
    print(f"🚨 DIAGNOSING SYSTEM ISSUES")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check current state
    check_frontend_display()
    check_api_endpoints()
    
    # Try to fix issues
    fix_success = fix_system_issues()
    
    if fix_success:
        print("\n✅ SYSTEM ISSUES RESOLVED")
        print("The system should now be showing committees and hearings.")
        print("Please refresh the frontend to see the updated data.")
    else:
        print("\n❌ SYSTEM ISSUES PERSIST")
        print("Manual intervention may be required.")
        print("Check the container logs for more details.")
    
    print(f"\n📋 SYSTEM URL: https://senate-hearing-processor-1066017671167.us-central1.run.app")

if __name__ == "__main__":
    main()