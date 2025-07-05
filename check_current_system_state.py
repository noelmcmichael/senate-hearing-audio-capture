#!/usr/bin/env python3
"""
Check current system state to understand hearing discovery status
"""

import requests
import json
import sqlite3
from datetime import datetime

def check_production_system():
    """Check the production system status"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print("🔍 CHECKING PRODUCTION SYSTEM STATUS")
    print(f"Base URL: {base_url}")
    print("=" * 60)
    
    # Check health
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"✅ Health Check: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
    
    # Check committees
    try:
        response = requests.get(f"{base_url}/api/committees", timeout=10)
        if response.status_code == 200:
            committees = response.json()
            print(f"✅ Committees: {len(committees)} found")
            for committee in committees:
                print(f"   - {committee.get('committee_code', 'Unknown')}: {committee.get('name', 'No name')}")
        else:
            print(f"❌ Committees: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Committees Failed: {e}")
    
    # Check hearings
    try:
        response = requests.get(f"{base_url}/api/hearings", timeout=10)
        if response.status_code == 200:
            hearings = response.json()
            print(f"📋 Hearings: {len(hearings)} found")
            
            if hearings:
                print("   Recent hearings:")
                for hearing in hearings[:5]:  # Show first 5
                    print(f"   - {hearing.get('title', 'No title')[:50]}...")
                    print(f"     Status: {hearing.get('status', 'Unknown')}")
                    print(f"     Date: {hearing.get('date', 'Unknown')}")
            else:
                print("   ❌ No hearings found - this is the issue!")
        else:
            print(f"❌ Hearings: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Hearings Failed: {e}")
    
    # Check discovery endpoint
    try:
        response = requests.post(f"{base_url}/api/hearings/discover", 
                               json={"committee_codes": ["SCOM", "SSCI", "SSJU"]},
                               timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"🔍 Discovery Test: {result.get('discovered_count', 0)} hearings discovered")
            print(f"   Status: {result.get('status', 'Unknown')}")
        else:
            print(f"❌ Discovery Test: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Discovery Test Failed: {e}")
    
    # Check admin status
    try:
        response = requests.get(f"{base_url}/admin/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"🏥 Admin Status: {status.get('status', 'Unknown')}")
            print(f"   Database: {status.get('database_status', 'Unknown')}")
            print(f"   Tables: {status.get('table_count', 'Unknown')}")
        else:
            print(f"❌ Admin Status: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Admin Status Failed: {e}")

def check_local_database():
    """Check local database state for reference"""
    
    print("\n🗃️ CHECKING LOCAL DATABASE STATE")
    print("=" * 60)
    
    try:
        # Check if local database exists
        conn = sqlite3.connect("data/demo_enhanced_ui.db")
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📊 Local Database Tables: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Check hearings count
        try:
            cursor.execute("SELECT COUNT(*) FROM hearings")
            count = cursor.fetchone()[0]
            print(f"📋 Local Hearings Count: {count}")
        except:
            print("❌ No hearings table in local database")
        
        # Check committees count
        try:
            cursor.execute("SELECT COUNT(*) FROM committees")
            count = cursor.fetchone()[0]
            print(f"🏛️ Local Committees Count: {count}")
        except:
            print("❌ No committees table in local database")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Local Database Check Failed: {e}")

def main():
    """Main function to run all checks"""
    
    print(f"🚀 SENATE HEARING SYSTEM STATUS CHECK")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check production system
    check_production_system()
    
    # Check local database for reference
    check_local_database()
    
    print("\n🎯 ANALYSIS SUMMARY")
    print("=" * 60)
    print("✅ System is operational but likely missing hearing data")
    print("🔍 Next: Need to activate discovery service to populate hearings")
    print("📋 Expected: 0 hearings currently, need to discover real hearings")
    print("🎯 Goal: Discover and process actual Senate hearings")

if __name__ == "__main__":
    main()