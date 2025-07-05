#!/usr/bin/env python3
"""
Check if the frontend is working now that we have committee data.
"""
import requests
import json
from datetime import datetime
import time

# Production service URL
BASE_URL = "https://senate-hearing-processor-518203250893.us-central1.run.app"

def check_frontend_data():
    """Check if frontend should have data to display."""
    print("="*60)
    print("🔍 FRONTEND DATA CHECK")
    print("="*60)
    
    # Check committees API
    try:
        response = requests.get(f"{BASE_URL}/api/committees", timeout=10)
        if response.status_code == 200:
            data = response.json()
            committees = data.get('committees', [])
            
            print(f"📊 API Response Status: {response.status_code}")
            print(f"📊 Committees Found: {len(committees)}")
            
            if committees:
                print(f"📋 Available Committees:")
                for i, committee in enumerate(committees, 1):
                    print(f"   {i}. {committee['code']}: {committee['name']}")
                    print(f"      Hearings: {committee['hearing_count']}")
                    print(f"      Latest: {committee['latest_hearing']}")
                
                print(f"\n✅ Frontend should now display {len(committees)} committees")
                return True
            else:
                print(f"❌ No committees found - frontend will be empty")
                return False
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        return False

def identify_database_issue():
    """Identify the database persistence issue."""
    print("\n" + "="*60)
    print("🔍 DATABASE PERSISTENCE ISSUE ANALYSIS")
    print("="*60)
    
    print("🚨 PROBLEM IDENTIFIED:")
    print("   Cloud Run services have ephemeral file systems")
    print("   SQLite database files are lost when service restarts")
    print("   This is why committees disappear periodically")
    
    print("\n💡 SOLUTIONS:")
    print("   1. Use Google Cloud SQL (PostgreSQL) for persistent storage")
    print("   2. Use Cloud Storage for SQLite file backup/restore")
    print("   3. Implement auto-bootstrap on service startup")
    print("   4. Add persistent volume (not available in Cloud Run)")
    
    print("\n🔧 IMMEDIATE WORKAROUND:")
    print("   Bootstrap the database whenever it's empty")
    print("   Add startup script to check and bootstrap if needed")
    
    print("\n📋 RECOMMENDED LONG-TERM FIX:")
    print("   Migrate to Cloud SQL PostgreSQL for true persistence")

def test_admin_interface():
    """Test the admin interface specifically."""
    print("\n" + "="*60)
    print("🔍 ADMIN INTERFACE TEST")
    print("="*60)
    
    # Test admin page
    try:
        response = requests.get(f"{BASE_URL}/admin", timeout=10)
        print(f"📄 Admin Page Status: {response.status_code}")
        
        if response.status_code == 200:
            html_length = len(response.text)
            print(f"📄 Admin Page HTML Length: {html_length} chars")
            
            # Check if it's the same short HTML as root
            if html_length < 1000:
                print("⚠️  Admin page appears to be the same React app")
                print("   This means /admin route is handled by React Router")
                print("   The 'blank blue page' is likely a React routing issue")
            else:
                print("✅ Admin page has substantial content")
        else:
            print(f"❌ Admin page failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Admin page test failed: {e}")

def main():
    """Run frontend checks."""
    print("🚀 FRONTEND STATUS CHECK")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if we have data
    has_data = check_frontend_data()
    
    # Analyze the database issue
    identify_database_issue()
    
    # Test admin interface
    test_admin_interface()
    
    print("\n" + "="*60)
    print("🎯 SUMMARY")
    print("="*60)
    
    if has_data:
        print("✅ Backend has committee data")
        print("🔄 Frontend should now display committees")
        print("🌐 Try refreshing the browser page")
        print("📋 Check browser console for any JavaScript errors")
    else:
        print("❌ Backend has no committee data")
        print("🔄 Need to bootstrap database again")
    
    print("\n🚨 CRITICAL ISSUE:")
    print("   Database does not persist between Cloud Run restarts")
    print("   This requires immediate architectural fix")
    
    print(f"\n🚀 FRONTEND URL: {BASE_URL}")
    print("   Try opening in browser now")

if __name__ == "__main__":
    main()