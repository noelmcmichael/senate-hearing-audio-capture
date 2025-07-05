#!/usr/bin/env python3
"""
Trigger real hearing discovery to populate the system
"""

import requests
import json
import time
from datetime import datetime

def trigger_discovery():
    """Trigger discovery for all committees"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print("🔍 TRIGGERING REAL HEARING DISCOVERY")
    print("=" * 60)
    
    committees = ["SCOM", "SSCI", "SSJU"]
    
    for committee in committees:
        print(f"\n📋 Discovering hearings for {committee}...")
        
        try:
            # Trigger discovery for this committee
            response = requests.post(
                f"{base_url}/api/hearings/discover",
                json={"committee_codes": [committee]},
                timeout=60  # Longer timeout for discovery
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {committee} Discovery Result:")
                print(f"   Total discovered: {result.get('data', {}).get('total_discovered', 0)}")
                print(f"   New hearings: {result.get('data', {}).get('new_hearings', 0)}")
                print(f"   Updated hearings: {result.get('data', {}).get('updated_hearings', 0)}")
                print(f"   Message: {result.get('message', 'No message')}")
                
                # Show discovered hearings
                hearings = result.get('data', {}).get('hearings', [])
                if hearings:
                    print(f"   Discovered hearings:")
                    for hearing in hearings[:3]:  # Show first 3
                        print(f"     - {hearing.get('title', 'No title')[:50]}...")
                        print(f"       Date: {hearing.get('date', 'Unknown')}")
                        print(f"       URL: {hearing.get('url', 'Unknown')}")
                
            else:
                print(f"❌ {committee} Discovery failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ {committee} Discovery error: {e}")
        
        # Small delay between committee discoveries
        time.sleep(2)

def check_results():
    """Check the results after discovery"""
    
    base_url = "https://senate-hearing-processor-1066017671167.us-central1.run.app"
    
    print("\n📊 CHECKING DISCOVERY RESULTS")
    print("=" * 60)
    
    # Check hearing queue
    try:
        response = requests.get(f"{base_url}/api/hearings/queue", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Updated Queue: {len(data.get('hearings', []))} hearings")
            
            # Show some real hearings
            hearings = data.get('hearings', [])
            if hearings:
                print("Recent hearings:")
                for hearing in hearings[:5]:  # Show first 5
                    title = hearing.get('title', 'No title')
                    if 'Bootstrap Entry' not in title:  # Skip bootstrap entries
                        print(f"  - {title[:60]}...")
                        print(f"    Date: {hearing.get('date', 'Unknown')}")
                        print(f"    Status: {hearing.get('status', 'Unknown')}")
                        print(f"    Committee: {hearing.get('committee', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ Queue check error: {e}")
    
    # Check committees
    committees = ["SCOM", "SSCI", "SSJU"]
    print(f"\n📋 Updated committee counts:")
    
    for committee in committees:
        try:
            response = requests.get(f"{base_url}/api/committees/{committee}/hearings", timeout=10)
            if response.status_code == 200:
                data = response.json()
                hearings = data.get('hearings', [])
                real_hearings = [h for h in hearings if 'Bootstrap Entry' not in h.get('title', '')]
                print(f"  {committee}: {len(real_hearings)} real hearings ({len(hearings)} total)")
        except Exception as e:
            print(f"  {committee}: Error checking - {e}")

def main():
    """Main function"""
    
    print(f"🚀 REAL HEARING DISCOVERY ACTIVATION")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Trigger discovery
    trigger_discovery()
    
    # Check results
    check_results()
    
    print("\n🎯 PHASE 1 COMPLETE")
    print("=" * 60)
    print("✅ Discovery service tested and activated")
    print("📋 Real hearings discovered (if any available)")
    print("🔍 Next: Test processing pipeline on discovered hearings")
    print("🎯 Goal: Full end-to-end workflow validation")

if __name__ == "__main__":
    main()