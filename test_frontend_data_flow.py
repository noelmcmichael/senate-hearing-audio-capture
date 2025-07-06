#!/usr/bin/env python3
"""
Test script to simulate exactly what the React frontend does when it loads
"""

import requests
import json
import sys
from typing import Dict, Any, List

def simulate_dashboard_load(base_url: str) -> Dict[str, Any]:
    """Simulate the exact data loading process the Dashboard component does"""
    
    print("🚀 Simulating Dashboard.js fetchHearings() function")
    print("=" * 60)
    
    # Committee list from Dashboard.js
    committees = [
        { "code": "SCOM", "name": "Senate Commerce" },
        { "code": "SSCI", "name": "Senate Intelligence" },
        { "code": "HJUD", "name": "House Judiciary" },
        { "code": "SSJU", "name": "Senate Judiciary" },
        { "code": "SBAN", "name": "Senate Banking" },
        { "code": "SSAF", "name": "Senate Armed Forces" },
        { "code": "SSHR", "name": "Senate Health" },
        { "code": "SSBE", "name": "Senate Budget" }
    ]
    
    all_hearings = []
    committee_results = {}
    
    # Step 1: Fetch hearings from each committee (exactly like Dashboard.js)
    print("1️⃣ Fetching hearings from each committee...")
    
    for committee in committees:
        committee_code = committee["code"]
        committee_name = committee["name"]
        
        print(f"   📡 Fetching {committee_code} ({committee_name})...")
        
        try:
            url = f"{base_url}/api/committees/{committee_code}/hearings"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                hearings = data.get("hearings", [])
                
                print(f"   ✅ {committee_code}: {len(hearings)} hearings")
                all_hearings.extend(hearings)
                committee_results[committee_code] = {"status": "success", "count": len(hearings)}
            else:
                print(f"   ❌ {committee_code}: HTTP {response.status_code}")
                committee_results[committee_code] = {"status": "error", "code": response.status_code}
                
        except Exception as e:
            print(f"   ❌ {committee_code}: {str(e)}")
            committee_results[committee_code] = {"status": "error", "error": str(e)}
    
    # Step 2: Remove duplicates (like Dashboard.js does)
    print(f"\n2️⃣ Processing {len(all_hearings)} total hearings...")
    
    # Remove duplicates by ID
    unique_hearings = []
    seen_ids = set()
    
    for hearing in all_hearings:
        hearing_id = hearing.get("id")
        if hearing_id not in seen_ids:
            unique_hearings.append(hearing)
            seen_ids.add(hearing_id)
    
    print(f"   ✅ After deduplication: {len(unique_hearings)} unique hearings")
    
    # Step 3: Try to fetch transcript data (like Dashboard.js does)
    print("\n3️⃣ Fetching transcript data...")
    
    try:
        transcript_url = f"{base_url}/api/transcript-browser/hearings"
        transcript_response = requests.get(transcript_url, timeout=10)
        
        if transcript_response.status_code == 200:
            transcript_data = transcript_response.json()
            transcripts = transcript_data.get("transcripts", [])
            print(f"   ✅ Found {len(transcripts)} transcripts")
        else:
            print(f"   ⚠️  Transcript endpoint returned {transcript_response.status_code}")
            transcripts = []
    except Exception as e:
        print(f"   ❌ Transcript fetch error: {e}")
        transcripts = []
    
    # Step 4: Enhance hearings with transcript information (like Dashboard.js does)
    print("\n4️⃣ Enhancing hearings with transcript data...")
    
    enhanced_hearings = []
    for hearing in unique_hearings:
        # Find matching transcript
        transcript = None
        for t in transcripts:
            if t.get("hearing_id") == hearing.get("id"):
                transcript = t
                break
        
        # Enhance hearing object
        enhanced_hearing = {
            **hearing,
            "has_transcript": transcript is not None,
            "transcript_confidence": transcript.get("confidence", 0) if transcript else 0,
            "transcript_segments": len(transcript.get("segments", [])) if transcript else 0,
            "speaker_review_status": "needs_review" if transcript else "no_transcript"
        }
        
        enhanced_hearings.append(enhanced_hearing)
    
    print(f"   ✅ Enhanced {len(enhanced_hearings)} hearings")
    
    return {
        "committee_results": committee_results,
        "total_hearings": len(all_hearings),
        "unique_hearings": len(unique_hearings),
        "enhanced_hearings": enhanced_hearings,
        "transcripts_available": len(transcripts)
    }

def analyze_ssju_hearings(enhanced_hearings: List[Dict]) -> Dict[str, Any]:
    """Analyze the specific SSJU hearings that should be displayed"""
    
    print("\n🔍 SSJU HEARING ANALYSIS")
    print("=" * 60)
    
    ssju_hearings = [h for h in enhanced_hearings if h.get("committee_code") == "SSJU"]
    
    print(f"Total SSJU hearings: {len(ssju_hearings)}")
    
    real_hearings = []
    for hearing in ssju_hearings:
        title = hearing.get("title", "")
        hearing_id = hearing.get("id")
        date = hearing.get("date", "")
        
        print(f"\n📋 Hearing ID {hearing_id}:")
        print(f"   Title: {title}")
        print(f"   Date: {date}")
        print(f"   Has Transcript: {hearing.get('has_transcript', False)}")
        print(f"   Streams: {hearing.get('streams', {})}")
        
        # Check if this is one of our real hearings
        if "Executive Business Meeting" in title or "Dragon" in title:
            real_hearings.append(hearing)
            print(f"   ✅ REAL SENATE HEARING IDENTIFIED")
        else:
            print(f"   ℹ️  Demo/Bootstrap hearing")
    
    return {
        "total_ssju": len(ssju_hearings),
        "real_hearings": len(real_hearings),
        "real_hearing_details": real_hearings
    }

def main():
    """Main test function"""
    
    base_url = "http://localhost:8001"
    
    print("🎯 Frontend Data Flow Simulation")
    print("Testing exact React Dashboard.js behavior")
    print("=" * 60)
    
    # Simulate the complete dashboard loading process
    results = simulate_dashboard_load(base_url)
    
    # Analyze SSJU hearings specifically
    ssju_analysis = analyze_ssju_hearings(results["enhanced_hearings"])
    
    # Summary
    print("\n📊 SIMULATION SUMMARY")
    print("=" * 60)
    
    print(f"🏛️  Committees contacted: {len(results['committee_results'])}")
    print(f"📋 Total hearings found: {results['total_hearings']}")
    print(f"🔄 Unique hearings: {results['unique_hearings']}")
    print(f"💬 Transcripts available: {results['transcripts_available']}")
    
    print(f"\n🏛️  SSJU Committee Analysis:")
    print(f"   Total SSJU hearings: {ssju_analysis['total_ssju']}")
    print(f"   Real Senate hearings: {ssju_analysis['real_hearings']}")
    
    # Success assessment
    success_criteria = [
        ssju_analysis['total_ssju'] >= 2,  # At least 2 SSJU hearings
        ssju_analysis['real_hearings'] >= 2,  # At least 2 real hearings
        results['unique_hearings'] >= 10,  # Reasonable number of total hearings
    ]
    
    success_rate = sum(success_criteria) / len(success_criteria) * 100
    
    print(f"\n🎯 Frontend Readiness: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("✅ FRONTEND READY - React dashboard should display real hearings correctly")
        
        # Show what user would see
        print("\n👀 USER WOULD SEE:")
        print("=" * 60)
        
        for hearing in ssju_analysis['real_hearing_details']:
            print(f"📋 {hearing['title']}")
            print(f"   📅 Date: {hearing['date']}")
            print(f"   🏛️  Committee: {hearing['committee_code']}")
            print(f"   🎯 Capture Ready: {'Yes' if hearing.get('streams') else 'No'}")
            print(f"   💬 Has Transcript: {'Yes' if hearing.get('has_transcript') else 'No'}")
            print()
        
        return 0
    else:
        print("❌ FRONTEND NOT READY - Issues detected")
        return 1

if __name__ == "__main__":
    sys.exit(main())