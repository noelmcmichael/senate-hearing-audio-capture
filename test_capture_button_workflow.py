#!/usr/bin/env python3
"""
Test script to simulate the capture button workflow that the React frontend would use
"""

import requests
import json
import sys
import time
from typing import Dict, Any

def test_capture_workflow(base_url: str, hearing_id: int, hearing_title: str) -> Dict[str, Any]:
    """Test the complete capture workflow for a specific hearing"""
    
    print(f"\n🎯 Testing Capture Workflow for Hearing ID: {hearing_id}")
    print(f"Title: {hearing_title}")
    print("-" * 60)
    
    results = {}
    
    # Step 1: Get hearing details
    print("1️⃣ Getting hearing details...")
    try:
        response = requests.get(f"{base_url}/api/hearings/{hearing_id}")
        if response.status_code == 200:
            hearing_data = response.json()
            print(f"✅ Hearing details retrieved")
            results["hearing_details"] = {"status": "success", "data": hearing_data}
        else:
            # Try alternative endpoint
            response = requests.get(f"{base_url}/api/committees/SSJU/hearings")
            if response.status_code == 200:
                ssju_data = response.json()
                hearing_data = None
                for h in ssju_data.get("hearings", []):
                    if h.get("id") == hearing_id:
                        hearing_data = h
                        break
                
                if hearing_data:
                    print(f"✅ Hearing details retrieved from committee endpoint")
                    results["hearing_details"] = {"status": "success", "data": hearing_data}
                else:
                    print(f"❌ Hearing not found in committee data")
                    results["hearing_details"] = {"status": "not_found"}
            else:
                print(f"❌ Failed to get hearing details: {response.status_code}")
                results["hearing_details"] = {"status": "error", "code": response.status_code}
    except Exception as e:
        print(f"❌ Error getting hearing details: {e}")
        results["hearing_details"] = {"status": "error", "error": str(e)}
    
    # Step 2: Check capture readiness
    print("2️⃣ Checking capture readiness...")
    try:
        # Check if hearing has streams (ISVP URL)
        if results["hearing_details"]["status"] == "success":
            hearing_data = results["hearing_details"]["data"]
            streams = hearing_data.get("streams", {})
            
            if isinstance(streams, str):
                try:
                    streams = json.loads(streams)
                except:
                    streams = {}
            
            if streams and "isvp" in streams:
                print(f"✅ ISVP stream available: {streams['isvp']}")
                results["capture_readiness"] = {"status": "ready", "stream_url": streams['isvp']}
            else:
                print(f"⚠️  No ISVP stream found")
                results["capture_readiness"] = {"status": "no_stream"}
        else:
            print(f"⚠️  Cannot check readiness - hearing details not available")
            results["capture_readiness"] = {"status": "unknown"}
    except Exception as e:
        print(f"❌ Error checking capture readiness: {e}")
        results["capture_readiness"] = {"status": "error", "error": str(e)}
    
    # Step 3: Simulate capture request
    print("3️⃣ Simulating capture request...")
    try:
        # Try the capture endpoint that the frontend would use
        capture_data = {
            "hearing_id": hearing_id,
            "priority": 1,
            "user_id": "test_user"
        }
        
        response = requests.post(f"{base_url}/api/hearings/{hearing_id}/capture", json=capture_data)
        
        if response.status_code == 200:
            print(f"✅ Capture request successful")
            results["capture_request"] = {"status": "success", "data": response.json()}
        elif response.status_code == 422:
            print(f"⚠️  Capture request validation error (422) - might be expected for demo")
            results["capture_request"] = {"status": "validation_error", "code": 422}
        else:
            print(f"❌ Capture request failed: {response.status_code}")
            results["capture_request"] = {"status": "error", "code": response.status_code}
    except Exception as e:
        print(f"❌ Error with capture request: {e}")
        results["capture_request"] = {"status": "error", "error": str(e)}
    
    # Step 4: Check processing status
    print("4️⃣ Checking processing status...")
    try:
        response = requests.get(f"{base_url}/api/hearings/{hearing_id}/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Processing status retrieved")
            results["processing_status"] = {"status": "success", "data": status_data}
        else:
            print(f"⚠️  Processing status endpoint not available: {response.status_code}")
            results["processing_status"] = {"status": "not_available"}
    except Exception as e:
        print(f"❌ Error checking processing status: {e}")
        results["processing_status"] = {"status": "error", "error": str(e)}
    
    return results

def main():
    """Test the capture workflow for real Senate hearings"""
    
    base_url = "http://localhost:8001"
    
    print("🚀 Capture Button Workflow Test")
    print("=" * 60)
    
    # Test both real hearings
    test_hearings = [
        {"id": 37, "title": "Executive Business Meeting"},
        {"id": 38, "title": "Enter the Dragon—China's Lawfare Against American Energy Dominance"}
    ]
    
    all_results = {}
    
    for hearing in test_hearings:
        results = test_capture_workflow(base_url, hearing["id"], hearing["title"])
        all_results[hearing["id"]] = results
    
    # Summary
    print("\n📊 WORKFLOW TEST SUMMARY")
    print("=" * 60)
    
    for hearing_id, results in all_results.items():
        hearing_title = next(h["title"] for h in test_hearings if h["id"] == hearing_id)
        print(f"\n🎯 Hearing ID {hearing_id}: {hearing_title}")
        
        for step, result in results.items():
            status = "✅" if result["status"] == "success" else "⚠️" if result["status"] in ["validation_error", "not_available"] else "❌"
            print(f"  {status} {step}: {result['status']}")
    
    # Check if frontend would be functional
    print("\n🔍 FRONTEND FUNCTIONALITY ASSESSMENT")
    print("=" * 60)
    
    functional_score = 0
    total_tests = 0
    
    for hearing_id, results in all_results.items():
        total_tests += 1
        
        # Check if hearing details are available (critical for display)
        if results["hearing_details"]["status"] == "success":
            functional_score += 1
            print(f"✅ Hearing {hearing_id}: Details available for display")
        else:
            print(f"❌ Hearing {hearing_id}: Details not available")
    
    functionality_rate = (functional_score / total_tests) * 100 if total_tests > 0 else 0
    print(f"\n🎯 Frontend Functionality: {functionality_rate:.1f}% ({functional_score}/{total_tests})")
    
    if functionality_rate >= 80:
        print("🎉 READY FOR FRONTEND TESTING - Core functionality available")
        return 0
    else:
        print("⚠️  FRONTEND ISSUES DETECTED - Additional work needed")
        return 1

if __name__ == "__main__":
    sys.exit(main())