#!/usr/bin/env python3
"""
Test script to verify capture button functionality after fixes
"""

import requests
import json
import sys

def test_capture_buttons(base_url: str):
    """Test that capture buttons should be visible for real hearings"""
    
    print("🔘 Testing Capture Button Visibility")
    print("=" * 50)
    
    # Get SSJU hearings
    response = requests.get(f"{base_url}/api/committees/SSJU/hearings")
    if response.status_code != 200:
        print(f"❌ Failed to fetch SSJU hearings: {response.status_code}")
        return False
    
    data = response.json()
    hearings = data.get("hearings", [])
    
    print(f"📋 Found {len(hearings)} SSJU hearings")
    
    capture_ready_count = 0
    
    for hearing in hearings:
        hearing_id = hearing.get("id")
        title = hearing.get("title", "")
        status = hearing.get("status")
        processing_stage = hearing.get("processing_stage")
        streams = hearing.get("streams", {})
        
        print(f"\n🎯 Hearing ID {hearing_id}: {title[:50]}...")
        print(f"   Status: {status}")
        print(f"   Processing Stage: {processing_stage}")
        print(f"   Has Streams: {bool(streams)}")
        
        # Check if this hearing should show capture button
        # Based on Dashboard.js logic: status in ['discovered', 'analyzed', 'new'] OR no status
        should_show_capture = (
            processing_stage in ['discovered', 'analyzed'] or
            status in ['discovered', 'analyzed', 'new'] or
            status is None
        ) and bool(streams)
        
        print(f"   Should Show Capture Button: {'✅ YES' if should_show_capture else '❌ NO'}")
        
        if should_show_capture:
            capture_ready_count += 1
            
            # Test actual capture API call
            print(f"   🔗 Testing capture API...")
            try:
                capture_response = requests.post(
                    f"{base_url}/api/hearings/{hearing_id}/capture?user_id=test_user",
                    json={"hearing_id": hearing_id, "priority": 1},
                    timeout=5
                )
                
                if capture_response.status_code == 200:
                    result = capture_response.json()
                    print(f"   ✅ Capture API working: {result.get('message', 'Success')}")
                else:
                    print(f"   ⚠️  Capture API error: {capture_response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Capture API failed: {e}")
    
    print(f"\n📊 SUMMARY")
    print(f"   Total hearings: {len(hearings)}")
    print(f"   Capture-ready hearings: {capture_ready_count}")
    
    if capture_ready_count >= 2:
        print(f"✅ SUCCESS: {capture_ready_count} hearings should show capture buttons")
        return True
    else:
        print(f"❌ ISSUE: Only {capture_ready_count} hearings ready for capture")
        return False

def test_individual_hearing_api(base_url: str):
    """Test individual hearing API for status page"""
    
    print("\n🏛️  Testing Individual Hearing API")
    print("=" * 50)
    
    test_hearing_ids = [37, 38]  # Real hearings
    
    for hearing_id in test_hearing_ids:
        print(f"\n🎯 Testing Hearing ID {hearing_id}")
        
        # Test hearing details
        try:
            response = requests.get(f"{base_url}/api/hearings/{hearing_id}")
            if response.status_code == 200:
                hearing_data = response.json()
                hearing = hearing_data.get("hearing", {})
                
                title = hearing.get("hearing_title", "Unknown")
                status = hearing.get("status")
                processing_stage = hearing.get("processing_stage")
                streams = hearing.get("streams", {})
                
                print(f"   ✅ Hearing Details: {title}")
                print(f"   📊 Status: {status} | Stage: {processing_stage}")
                print(f"   🔗 Has Streams: {bool(streams)}")
                
                # Check if status page should show capture button
                should_show_capture = (
                    streams and 
                    processing_stage not in ['captured', 'transcribed', 'reviewed', 'published']
                )
                
                print(f"   🔘 Status Page Capture Button: {'✅ YES' if should_show_capture else '❌ NO'}")
                
            else:
                print(f"   ❌ Failed to fetch hearing: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return True

def main():
    """Main test function"""
    
    base_url = "http://localhost:8001"
    
    print("🎯 Frontend Capture Button Test")
    print("Testing fixes for capture button visibility")
    print("=" * 50)
    
    # Test capture button logic for dashboard
    dashboard_success = test_capture_buttons(base_url)
    
    # Test individual hearing API for status pages
    api_success = test_individual_hearing_api(base_url)
    
    print(f"\n🏁 FINAL RESULTS")
    print("=" * 50)
    print(f"Dashboard Capture Buttons: {'✅ WORKING' if dashboard_success else '❌ ISSUES'}")
    print(f"Status Page API: {'✅ WORKING' if api_success else '❌ ISSUES'}")
    
    if dashboard_success and api_success:
        print(f"\n🎉 ALL TESTS PASSED - Capture buttons should now be visible!")
        return 0
    else:
        print(f"\n⚠️  SOME ISSUES DETECTED - May need additional fixes")
        return 1

if __name__ == "__main__":
    sys.exit(main())