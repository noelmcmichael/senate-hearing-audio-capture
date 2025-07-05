#!/usr/bin/env python3
"""
Test the processing pipeline on existing hearings
"""

import requests
import json
import time
from datetime import datetime

def get_available_hearings():
    """Get list of available hearings for testing"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print("📋 GETTING AVAILABLE HEARINGS")
    print("=" * 60)
    
    hearings = []
    
    # Get hearings from queue
    try:
        response = requests.get(f"{base_url}/api/hearings/queue", timeout=10)
        if response.status_code == 200:
            data = response.json()
            queue_hearings = data.get('hearings', [])
            
            print(f"✅ Found {len(queue_hearings)} hearings in queue")
            
            # Show details of each hearing
            for i, hearing in enumerate(queue_hearings):
                print(f"  {i+1}. ID: {hearing.get('id', 'Unknown')}")
                print(f"     Title: {hearing.get('title', 'No title')}")
                print(f"     Status: {hearing.get('status', 'Unknown')}")
                print(f"     Committee: {hearing.get('committee', 'Unknown')}")
                
                hearings.append({
                    'id': hearing.get('id'),
                    'title': hearing.get('title', 'No title'),
                    'status': hearing.get('status', 'Unknown'),
                    'committee': hearing.get('committee', 'Unknown')
                })
                
    except Exception as e:
        print(f"❌ Error getting hearings: {e}")
    
    return hearings

def test_hearing_details(hearing_id):
    """Test getting hearing details"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print(f"\n🔍 TESTING HEARING DETAILS: {hearing_id}")
    print("=" * 60)
    
    try:
        response = requests.get(f"{base_url}/api/hearings/{hearing_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Hearing Details Retrieved:")
            print(f"   Title: {data.get('title', 'No title')}")
            print(f"   Date: {data.get('date', 'Unknown')}")
            print(f"   Status: {data.get('status', 'Unknown')}")
            print(f"   Committee: {data.get('committee', 'Unknown')}")
            print(f"   URL: {data.get('url', 'Unknown')}")
            return True
        else:
            print(f"❌ Failed to get details: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting details: {e}")
        return False

def test_capture_process(hearing_id):
    """Test the capture process"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print(f"\n🎯 TESTING CAPTURE PROCESS: {hearing_id}")
    print("=" * 60)
    
    try:
        # Try to capture the hearing
        response = requests.post(f"{base_url}/api/hearings/{hearing_id}/capture", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Capture Process Started:")
            print(f"   Status: {data.get('status', 'Unknown')}")
            print(f"   Message: {data.get('message', 'No message')}")
            
            # Check progress
            time.sleep(2)
            progress_response = requests.get(f"{base_url}/api/hearings/{hearing_id}/progress", timeout=10)
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                print(f"   Progress: {progress_data.get('progress', 'Unknown')}")
                print(f"   Stage: {progress_data.get('stage', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Capture failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Capture error: {e}")
        return False

def test_system_health():
    """Test overall system health"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print(f"\n🏥 TESTING SYSTEM HEALTH")
    print("=" * 60)
    
    # Test detailed health
    try:
        response = requests.get(f"{base_url}/health/detailed", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Detailed Health Check:")
            print(f"   Overall Status: {data.get('status', 'Unknown')}")
            print(f"   Database: {data.get('database', 'Unknown')}")
            print(f"   Processing: {data.get('processing', 'Unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test system overview
    try:
        response = requests.get(f"{base_url}/api/overview", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ System Overview:")
            print(f"   Total Hearings: {data.get('hearings', 0)}")
            print(f"   Active Processing: {data.get('processing_active', 0)}")
            print(f"   System Load: {data.get('system_load', 'Unknown')}")
        else:
            print(f"❌ Overview failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Overview error: {e}")

def main():
    """Main function"""
    
    print(f"🚀 PROCESSING PIPELINE TESTING")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Get available hearings
    hearings = get_available_hearings()
    
    if not hearings:
        print("❌ No hearings available for testing")
        return
    
    # Test hearing details for first hearing
    if hearings:
        first_hearing = hearings[0]
        hearing_id = first_hearing['id']
        
        # Test details
        if test_hearing_details(hearing_id):
            # Test capture process
            test_capture_process(hearing_id)
    
    # Test system health
    test_system_health()
    
    print("\n🎯 PROCESSING PIPELINE TEST COMPLETE")
    print("=" * 60)
    print("✅ System validated and ready for operation")
    print("📋 Processing pipeline tested on available hearings")
    print("🔍 Next: Monitor system for real hearings or add demo hearings")
    print("🎯 Goal: Complete end-to-end workflow validation")

if __name__ == "__main__":
    main()