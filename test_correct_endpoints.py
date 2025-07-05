#!/usr/bin/env python3
"""
Test the correct API endpoints for hearings
"""

import requests
import json
from datetime import datetime

def test_hearing_endpoints():
    """Test the correct hearing endpoints"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print("🔍 TESTING CORRECT HEARING ENDPOINTS")
    print("=" * 60)
    
    # Test hearing queue
    print("\n📋 Testing: /api/hearings/queue")
    try:
        response = requests.get(f"{base_url}/api/hearings/queue", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Queue Response: {len(data.get('hearings', []))} hearings")
            print(f"Total: {data.get('total', 0)}")
            if data.get('hearings'):
                for hearing in data['hearings'][:3]:  # Show first 3
                    print(f"  - {hearing.get('title', 'No title')[:50]}...")
                    print(f"    Status: {hearing.get('status', 'Unknown')}")
        else:
            print(f"❌ Queue failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Queue error: {e}")
    
    # Test discovered hearings
    print("\n📋 Testing: /api/hearings/discovered")
    try:
        response = requests.get(f"{base_url}/api/hearings/discovered", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Discovered Response: {len(data.get('hearings', []))} hearings")
            if data.get('hearings'):
                for hearing in data['hearings'][:3]:  # Show first 3
                    print(f"  - {hearing.get('title', 'No title')[:50]}...")
                    print(f"    Date: {hearing.get('date', 'Unknown')}")
        else:
            print(f"❌ Discovered failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Discovered error: {e}")
    
    # Test committee hearings
    print("\n📋 Testing: Committee hearings")
    committees = ["SCOM", "SSCI", "SSJU"]
    
    for committee in committees:
        try:
            response = requests.get(f"{base_url}/api/committees/{committee}/hearings", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {committee}: {len(data.get('hearings', []))} hearings")
                if data.get('hearings'):
                    for hearing in data['hearings'][:2]:  # Show first 2
                        print(f"  - {hearing.get('title', 'No title')[:40]}...")
            else:
                print(f"❌ {committee} failed: {response.status_code}")
        except Exception as e:
            print(f"❌ {committee} error: {e}")
    
    # Test status-based hearings
    print("\n📋 Testing: Hearings by status")
    statuses = ["discovered", "captured", "transcribed", "completed"]
    
    for status in statuses:
        try:
            response = requests.get(f"{base_url}/api/hearings/by-status/{status}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status '{status}': {len(data.get('hearings', []))} hearings")
            else:
                print(f"❌ Status '{status}' failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Status '{status}' error: {e}")

def test_system_overview():
    """Test system overview endpoints"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print("\n🌐 TESTING SYSTEM OVERVIEW")
    print("=" * 60)
    
    # Test system overview
    try:
        response = requests.get(f"{base_url}/api/overview", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ System Overview:")
            print(f"  Committees: {data.get('committees', 0)}")
            print(f"  Hearings: {data.get('hearings', 0)}")
            print(f"  Processing: {data.get('processing_active', 0)}")
        else:
            print(f"❌ Overview failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Overview error: {e}")
    
    # Test discovery stats
    try:
        response = requests.get(f"{base_url}/api/hearings/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Discovery Stats:")
            print(f"  Total discovered: {data.get('total_discovered', 0)}")
            print(f"  Last discovery: {data.get('last_discovery', 'Unknown')}")
        else:
            print(f"❌ Stats failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats error: {e}")

def main():
    """Main function"""
    
    print(f"🎯 TESTING CORRECT API ENDPOINTS")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    test_hearing_endpoints()
    test_system_overview()
    
    print("\n🎯 NEXT STEPS")
    print("=" * 60)
    print("1. Check which endpoints have hearings")
    print("2. Test the frontend to see what it's calling")
    print("3. Trigger discovery to populate more hearings")
    print("4. Test the processing pipeline")

if __name__ == "__main__":
    main()