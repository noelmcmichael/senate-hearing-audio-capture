#!/usr/bin/env python3
"""
Test script to verify frontend API integration
Tests the endpoints that the React dashboard is trying to use
"""

import requests
import json
import sys
from typing import Dict, Any

def test_api_endpoint(url: str, description: str) -> Dict[str, Any]:
    """Test a single API endpoint"""
    print(f"\n🔍 Testing: {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ SUCCESS: {response.status_code}")
                return {"status": "success", "data": data}
            except json.JSONDecodeError:
                print(f"⚠️  SUCCESS but invalid JSON: {response.status_code}")
                return {"status": "success_no_json", "text": response.text[:200]}
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return {"status": "error", "code": response.status_code, "text": response.text[:200]}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ CONNECTION ERROR: {e}")
        return {"status": "connection_error", "error": str(e)}

def main():
    """Test all API endpoints that the frontend uses"""
    
    base_url = "http://localhost:8001"
    
    # Test basic API endpoints
    endpoints = [
        (f"{base_url}/health", "Health Check"),
        (f"{base_url}/api", "API Info"),
        (f"{base_url}/api/committees", "Committees List"),
        (f"{base_url}/api/committees/SSJU/hearings", "SSJU Hearings (Real Data)"),
        (f"{base_url}/api/committees/SCOM/hearings", "SCOM Hearings"),
        (f"{base_url}/api/committees/SSCI/hearings", "SSCI Hearings"),
        (f"{base_url}/api/transcript-browser/hearings", "Transcript Browser"),
        (f"{base_url}/api/transcripts", "Transcripts List"),
    ]
    
    print("🚀 Frontend Integration Test")
    print("=" * 50)
    
    results = {}
    
    for url, description in endpoints:
        results[description] = test_api_endpoint(url, description)
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    
    success_count = 0
    for description, result in results.items():
        status = "✅" if result["status"] == "success" else "❌"
        print(f"{status} {description}")
        if result["status"] == "success":
            success_count += 1
    
    success_rate = (success_count / len(results)) * 100
    print(f"\n🎯 Success Rate: {success_rate:.1f}% ({success_count}/{len(results)})")
    
    # Check for real hearing data
    print("\n🔍 REAL HEARING DATA CHECK")
    print("=" * 50)
    
    ssju_result = results.get("SSJU Hearings (Real Data)")
    if ssju_result and ssju_result["status"] == "success":
        hearings = ssju_result["data"].get("hearings", [])
        print(f"SSJU Hearings Found: {len(hearings)}")
        
        real_hearings = [
            h for h in hearings 
            if "Executive Business Meeting" in h.get("title", "") or 
               "Dragon" in h.get("title", "")
        ]
        
        print(f"Real Senate Hearings: {len(real_hearings)}")
        for hearing in real_hearings:
            print(f"  - {hearing.get('title', 'Unknown')} ({hearing.get('date', 'Unknown')})")
            
        if len(real_hearings) == 2:
            print("✅ REAL DATA VERIFIED: Both expected hearings found!")
        else:
            print("⚠️  REAL DATA INCOMPLETE: Expected 2 hearings")
    else:
        print("❌ REAL DATA NOT ACCESSIBLE")
    
    # Return success rate for script exit code
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())