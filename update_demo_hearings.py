#!/usr/bin/env python3
"""
Update existing bootstrap hearings with realistic data
"""

import json
import requests
from datetime import datetime, timedelta
import random

# Updated hearing data that matches existing IDs
UPDATED_HEARINGS = {
    1: {
        "committee_code": "SCOM",
        "hearing_title": "Artificial Intelligence in Transportation: Opportunities and Challenges",
        "hearing_date": "2025-07-08",
        "hearing_type": "Legislative",
        "extraction_status": "pending",
        "transcription_status": "pending",
        "review_status": "pending",
        "witnesses": {
            "participants": ["Chair Cantwell", "Ranking Member Cruz", "Sen. Klobuchar", "Dr. Sarah Chen (MIT)"],
            "description": "Examining the role of AI in modern transportation systems and safety protocols"
        }
    },
    2: {
        "committee_code": "SSCI",
        "hearing_title": "Foreign Election Interference and Social Media Platforms",
        "hearing_date": "2025-07-10",
        "hearing_type": "Intelligence",
        "extraction_status": "captured",
        "transcription_status": "pending",
        "review_status": "pending",
        "witnesses": {
            "participants": ["Chair Warner", "Ranking Member Cornyn", "Director Smith (NSA)"],
            "description": "Closed session on foreign interference in democratic processes"
        }
    },
    3: {
        "committee_code": "SSJU",
        "hearing_title": "Judicial Nomination: District Court Appointments",
        "hearing_date": "2025-07-12",
        "hearing_type": "Nomination",
        "extraction_status": "transcribed",
        "transcription_status": "completed",
        "review_status": "pending",
        "witnesses": {
            "participants": ["Chair Durbin", "Ranking Member Graham", "Judge Patricia Williams"],
            "description": "Confirmation hearing for federal district court nominee"
        }
    },
    4: {
        "committee_code": "SCOM",
        "hearing_title": "Broadband Infrastructure Investment and Rural Access",
        "hearing_date": "2025-07-09",
        "hearing_type": "Oversight",
        "extraction_status": "analyzed",
        "transcription_status": "pending",
        "review_status": "pending",
        "witnesses": {
            "participants": ["Chair Cantwell", "Sen. Thune", "Commissioner Rodriguez (FCC)"],
            "description": "Oversight hearing on broadband expansion efforts and rural connectivity"
        }
    },
    5: {
        "committee_code": "SSCI",
        "hearing_title": "Annual Threat Assessment: Global Security Challenges",
        "hearing_date": "2025-07-11",
        "hearing_type": "Intelligence",
        "extraction_status": "reviewed",
        "transcription_status": "completed",
        "review_status": "completed",
        "witnesses": {
            "participants": ["Chair Warner", "Sen. Rubio", "Director Johnson (CIA)", "Director Brown (FBI)"],
            "description": "Annual briefing on global security threats and intelligence priorities"
        }
    },
    6: {
        "committee_code": "SSJU",
        "hearing_title": "Antitrust in Digital Markets: Big Tech Competition",
        "hearing_date": "2025-07-15",
        "hearing_type": "Legislative",
        "extraction_status": "published",
        "transcription_status": "completed",
        "review_status": "completed",
        "witnesses": {
            "participants": ["Chair Durbin", "Sen. Hawley", "CEO Martinez (TechCorp)", "Prof. Anderson (Stanford)"],
            "description": "Examining competition and antitrust enforcement in digital markets"
        }
    },
    7: {
        "committee_code": "SCOM",
        "hearing_title": "Space Commerce and Satellite Regulation",
        "hearing_date": "2025-07-16",
        "hearing_type": "Oversight",
        "extraction_status": "discovered",
        "transcription_status": "pending",
        "review_status": "pending",
        "witnesses": {
            "participants": ["Chair Cantwell", "Sen. Wicker", "Administrator Chen (NASA)", "CEO Roberts (SpaceX)"],
            "description": "Oversight of commercial space activities and satellite licensing"
        }
    },
    8: {
        "committee_code": "SSCI",
        "hearing_title": "Cybersecurity Threats to Critical Infrastructure",
        "hearing_date": "2025-07-17",
        "hearing_type": "Intelligence",
        "extraction_status": "analyzed",
        "transcription_status": "pending",
        "review_status": "pending",
        "witnesses": {
            "participants": ["Chair Warner", "Sen. Cotton", "Director Johnson (CISA)", "Gen. Smith (NSA)"],
            "description": "Assessment of cybersecurity threats to national critical infrastructure"
        }
    },
    9: {
        "committee_code": "SSJU",
        "hearing_title": "Immigration Court Backlog and Due Process",
        "hearing_date": "2025-07-18",
        "hearing_type": "Oversight",
        "extraction_status": "captured",
        "transcription_status": "pending",
        "review_status": "pending",
        "witnesses": {
            "participants": ["Chair Durbin", "Ranking Member Graham", "Judge Martinez (Immigration Court)", "Dir. Thompson (EOIR)"],
            "description": "Addressing immigration court case backlogs and due process concerns"
        }
    }
}

def update_hearing_data():
    """Update existing hearings with realistic data"""
    
    api_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app/api"
    
    print("🎯 Updating existing hearings with realistic data...")
    
    # Get current hearings
    print("1. Fetching current hearings...")
    try:
        response = requests.get(f"{api_url}/hearings/queue")
        if response.status_code == 200:
            data = response.json()
            hearings = data.get("hearings", [])
            print(f"   📊 Found {len(hearings)} existing hearings")
        else:
            print(f"   ❌ Failed to fetch hearings: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Error fetching hearings: {e}")
        return
    
    # Update each hearing with realistic data
    print("2. Updating hearings with realistic data...")
    
    success_count = 0
    for hearing in hearings:
        hearing_id = hearing.get("id")
        
        if hearing_id in UPDATED_HEARINGS:
            update_data = UPDATED_HEARINGS[hearing_id]
            
            try:
                # Try to update via PUT request
                response = requests.put(f"{api_url}/hearings/{hearing_id}", json=update_data)
                
                if response.status_code in [200, 204]:
                    success_count += 1
                    print(f"   ✅ Updated hearing {hearing_id}: {update_data['hearing_title'][:50]}...")
                else:
                    print(f"   ❌ Failed to update hearing {hearing_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error updating hearing {hearing_id}: {e}")
    
    print(f"\n🎉 Successfully updated {success_count}/{len(UPDATED_HEARINGS)} hearings")
    
    # Verify the results
    print("\n3. Verifying updated hearing data...")
    try:
        response = requests.get(f"{api_url}/hearings/queue")
        if response.status_code == 200:
            data = response.json()
            hearings = data.get("hearings", [])
            
            print(f"   📊 Total hearings in system: {len(hearings)}")
            
            # Show variety in processing stages
            stages = {}
            for hearing in hearings:
                stage = hearing.get("extraction_status", "unknown")
                stages[stage] = stages.get(stage, 0) + 1
            
            print("   📈 Processing stages:")
            for stage, count in stages.items():
                print(f"      {stage}: {count} hearings")
                
            # Show sample titles
            print("\n   📝 Sample hearing titles:")
            for i, hearing in enumerate(hearings[:5]):
                title = hearing.get("hearing_title", "No title")
                print(f"      {i+1}. {title[:60]}...")
                
        else:
            print(f"   ❌ Failed to verify: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
    
    print("\n✅ Hearing data update complete!")
    print("🔗 View results at: https://senate-hearing-processor-1066017671167.us-central1.run.app")

if __name__ == "__main__":
    update_hearing_data()