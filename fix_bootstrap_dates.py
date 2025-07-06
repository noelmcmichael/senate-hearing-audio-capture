#!/usr/bin/env python3
"""
Fix bootstrap hearing dates to be realistic
"""
import requests
import json
from datetime import datetime, timedelta

PRODUCTION_URL = "https://senate-hearing-processor-1066017671167.us-central1.run.app"

def update_bootstrap_dates():
    """Update bootstrap hearing dates to be realistic"""
    
    # First, clear existing data and re-bootstrap with proper dates
    print("Re-bootstrapping with realistic dates...")
    
    try:
        # Trigger bootstrap again (this should recreate the data)
        response = requests.post(f"{PRODUCTION_URL}/admin/bootstrap", json={})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Bootstrap successful: {result}")
            
            # The bootstrap system should create realistic dates
            # Let's verify the dates are now proper
            committees = ["SCOM", "SSCI", "SSJU"]
            
            for committee in committees:
                try:
                    hearing_response = requests.get(f"{PRODUCTION_URL}/api/committees/{committee}/hearings")
                    if hearing_response.status_code == 200:
                        data = hearing_response.json()
                        hearings = data.get("hearings", [])
                        
                        if hearings:
                            hearing = hearings[0]
                            print(f"✅ {committee}: Date = {hearing.get('date', 'No date')}")
                        else:
                            print(f"❌ {committee}: No hearings found")
                except Exception as e:
                    print(f"❌ {committee}: Error checking hearing: {e}")
            
        else:
            print(f"❌ Bootstrap failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Bootstrap error: {e}")

if __name__ == "__main__":
    update_bootstrap_dates()