#!/usr/bin/env python3
"""
Create realistic demo hearing data for UI testing
"""

import json
import requests
from datetime import datetime, timedelta
import random

# Demo hearing data with realistic titles and variety
DEMO_HEARINGS = [
    {
        "committee_code": "SCOM",
        "hearing_title": "Artificial Intelligence in Transportation: Opportunities and Challenges",
        "hearing_date": "2025-07-08",
        "hearing_type": "Legislative",
        "processing_stage": "discovered",
        "participants": ["Chair Cantwell", "Ranking Member Cruz", "Sen. Klobuchar", "Dr. Sarah Chen (MIT)"],
        "description": "Examining the role of AI in modern transportation systems and safety protocols"
    },
    {
        "committee_code": "SCOM",
        "hearing_title": "Broadband Infrastructure Investment and Rural Access",
        "hearing_date": "2025-07-09",
        "hearing_type": "Oversight",
        "processing_stage": "analyzed",
        "participants": ["Chair Cantwell", "Sen. Thune", "Commissioner Rodriguez (FCC)"],
        "description": "Oversight hearing on broadband expansion efforts and rural connectivity"
    },
    {
        "committee_code": "SSCI",
        "hearing_title": "Foreign Election Interference and Social Media Platforms",
        "hearing_date": "2025-07-10",
        "hearing_type": "Intelligence",
        "processing_stage": "captured",
        "participants": ["Chair Warner", "Ranking Member Cornyn", "Director Smith (NSA)"],
        "description": "Closed session on foreign interference in democratic processes"
    },
    {
        "committee_code": "SSCI",
        "hearing_title": "Annual Threat Assessment: Global Security Challenges",
        "hearing_date": "2025-07-11",
        "hearing_type": "Intelligence",
        "processing_stage": "transcribed",
        "participants": ["Chair Warner", "Sen. Rubio", "Director Johnson (CIA)", "Director Brown (FBI)"],
        "description": "Annual briefing on global security threats and intelligence priorities"
    },
    {
        "committee_code": "SSJU",
        "hearing_title": "Judicial Nomination: District Court Appointments",
        "hearing_date": "2025-07-12",
        "hearing_type": "Nomination",
        "processing_stage": "reviewed",
        "participants": ["Chair Durbin", "Ranking Member Graham", "Judge Patricia Williams"],
        "description": "Confirmation hearing for federal district court nominee"
    },
    {
        "committee_code": "SSJU",
        "hearing_title": "Antitrust in Digital Markets: Big Tech Competition",
        "hearing_date": "2025-07-15",
        "hearing_type": "Legislative",
        "processing_stage": "published",
        "participants": ["Chair Durbin", "Sen. Hawley", "CEO Martinez (TechCorp)", "Prof. Anderson (Stanford)"],
        "description": "Examining competition and antitrust enforcement in digital markets"
    },
    {
        "committee_code": "SBAN",
        "hearing_title": "Banking Regulations and Small Business Lending",
        "hearing_date": "2025-07-16",
        "hearing_type": "Oversight",
        "processing_stage": "discovered",
        "participants": ["Chair Brown", "Ranking Member Scott", "President Garcia (Community Bank)"],
        "description": "Impact of banking regulations on small business access to capital"
    },
    {
        "committee_code": "SBAN",
        "hearing_title": "Cryptocurrency and Digital Assets Regulation",
        "hearing_date": "2025-07-17",
        "hearing_type": "Legislative",
        "processing_stage": "analyzed",
        "participants": ["Chair Brown", "Sen. Toomey", "Commissioner Lee (SEC)", "CEO Thompson (CryptoExchange)"],
        "description": "Regulatory framework for digital assets and cryptocurrency markets"
    },
    {
        "committee_code": "HELP",
        "hearing_title": "Healthcare Worker Shortage and Training Programs",
        "hearing_date": "2025-07-18",
        "hearing_type": "Oversight",
        "processing_stage": "captured",
        "participants": ["Chair Sanders", "Ranking Member Burr", "Dr. Martinez (AMA)", "Dean Johnson (Nursing School)"],
        "description": "Addressing the national healthcare worker shortage and training initiatives"
    }
]

def create_realistic_hearing_data():
    """Create realistic hearing data for testing"""
    
    api_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app/api"
    
    print("🎯 Creating realistic demo hearing data...")
    
    # First, clear existing bootstrap data
    print("1. Clearing existing bootstrap data...")
    try:
        response = requests.delete(f"{api_url}/admin/bootstrap/clear")
        if response.status_code == 200:
            print("   ✅ Bootstrap data cleared")
        else:
            print(f"   ⚠️  Clear response: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Clear error: {e}")
    
    # Create new realistic hearings
    print("2. Creating realistic demo hearings...")
    
    success_count = 0
    for i, hearing_data in enumerate(DEMO_HEARINGS):
        try:
            # Create hearing via API
            payload = {
                "committee_code": hearing_data["committee_code"],
                "hearing_title": hearing_data["hearing_title"],
                "hearing_date": hearing_data["hearing_date"],
                "hearing_type": hearing_data["hearing_type"],
                "processing_stage": hearing_data["processing_stage"],
                "participants": hearing_data["participants"],
                "description": hearing_data["description"],
                "source": "demo",
                "streams": {},
                "witnesses": {
                    "participants": hearing_data["participants"],
                    "description": hearing_data["description"]
                }
            }
            
            response = requests.post(f"{api_url}/hearings/create", json=payload)
            
            if response.status_code in [200, 201]:
                success_count += 1
                print(f"   ✅ Created: {hearing_data['hearing_title'][:50]}...")
            else:
                print(f"   ❌ Failed: {hearing_data['hearing_title'][:50]}... ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ Error creating hearing {i+1}: {e}")
    
    print(f"\n🎉 Successfully created {success_count}/{len(DEMO_HEARINGS)} demo hearings")
    
    # Verify the results
    print("\n3. Verifying hearing data...")
    try:
        response = requests.get(f"{api_url}/hearings/queue")
        if response.status_code == 200:
            data = response.json()
            hearings = data.get("hearings", [])
            
            print(f"   📊 Total hearings in system: {len(hearings)}")
            
            # Show variety in processing stages
            stages = {}
            for hearing in hearings:
                stage = hearing.get("processing_stage", "unknown")
                stages[stage] = stages.get(stage, 0) + 1
            
            print("   📈 Processing stages:")
            for stage, count in stages.items():
                print(f"      {stage}: {count} hearings")
                
        else:
            print(f"   ❌ Failed to verify: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
    
    print("\n✅ Demo hearing data creation complete!")
    print("🔗 View results at: https://senate-hearing-processor-1066017671167.us-central1.run.app")

if __name__ == "__main__":
    create_realistic_hearing_data()