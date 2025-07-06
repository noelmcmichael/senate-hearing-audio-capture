#!/usr/bin/env python3
"""
Bootstrap production hearings via API
"""
import sys
import os
sys.path.append('/Users/noelmcmichael/Workspace/senate_hearing_audio_capture')

import requests
import json

PRODUCTION_URL = "https://senate-hearing-processor-1066017671167.us-central1.run.app"

def create_bootstrap_hearings():
    """Create bootstrap hearings for testing"""
    
    # Committee data
    committees = [
        {
            "code": "SCOM",
            "name": "Commerce, Science, and Transportation",
            "hearing_title": "Bootstrap Entry for Senate Committee on Commerce, Science, and Transportation"
        },
        {
            "code": "SSCI", 
            "name": "Intelligence",
            "hearing_title": "Bootstrap Entry for Senate Select Committee on Intelligence"
        },
        {
            "code": "SSJU",
            "name": "Judiciary", 
            "hearing_title": "Bootstrap Entry for Senate Committee on the Judiciary"
        }
    ]
    
    # Create hearings via API
    for i, committee in enumerate(committees):
        hearing_data = {
            "committee_code": committee["code"],
            "title": committee["hearing_title"],
            "date": "2025-07-06",
            "type": "Setup",
            "sync_confidence": 1.0,
            "streams": {},
            "processing_stage": "discovered"
        }
        
        print(f"Creating hearing {i+1}: {committee['code']}")
        
        # Try creating via direct API call
        try:
            response = requests.post(
                f"{PRODUCTION_URL}/api/committees/{committee['code']}/hearings",
                json=hearing_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"✓ Created hearing for {committee['code']}")
            else:
                print(f"✗ Failed to create hearing for {committee['code']}: {response.status_code}")
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"✗ Error creating hearing for {committee['code']}: {e}")
    
    print("\nBootstrap complete - checking results...")
    
    # Verify hearings were created
    for committee in committees:
        try:
            response = requests.get(f"{PRODUCTION_URL}/api/committees/{committee['code']}/hearings")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {committee['code']}: {data.get('total_hearings', 0)} hearings")
            else:
                print(f"✗ {committee['code']}: Failed to fetch hearings")
        except Exception as e:
            print(f"✗ {committee['code']}: Error fetching hearings: {e}")

if __name__ == "__main__":
    create_bootstrap_hearings()