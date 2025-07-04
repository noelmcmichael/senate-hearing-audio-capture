#!/usr/bin/env python3
"""
Test Congress API synchronization directly on cloud platform
"""
import os
import sys
import json
import logging
import requests
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def test_congress_api_env():
    """Test Congress API using environment variable"""
    print("🔧 Testing Congress API with environment variable...")
    
    api_key = os.environ.get('CONGRESS_API_KEY')
    if not api_key:
        print("❌ CONGRESS_API_KEY environment variable not set")
        return False
    
    print(f"✅ Found Congress API key: {api_key[:10]}...")
    
    try:
        # Test basic API connectivity
        url = "https://api.congress.gov/v3/member"
        params = {
            'api_key': api_key,
            'format': 'json',
            'limit': 5
        }
        
        print(f"Testing API call to: {url}")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            members = data.get('members', [])
            print(f"✅ API call successful! Retrieved {len(members)} members")
            
            # Show first member as example
            if members:
                first_member = members[0]
                print(f"Example member: {first_member.get('name', 'Unknown')}")
            
            return True
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API call failed with error: {e}")
        return False

def test_committee_data():
    """Test committee data retrieval"""
    print("\n🔧 Testing committee data retrieval...")
    
    api_key = os.environ.get('CONGRESS_API_KEY')
    if not api_key:
        return False
    
    try:
        # Test Commerce Committee
        url = "https://api.congress.gov/v3/committee/senate/scom"
        params = {
            'api_key': api_key,
            'format': 'json'
        }
        
        print(f"Testing committee API call to: {url}")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            committee = data.get('committee', {})
            print(f"✅ Committee data retrieved: {committee.get('name', 'Unknown')}")
            print(f"Committee code: {committee.get('systemCode', 'Unknown')}")
            return True
        else:
            print(f"❌ Committee API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Committee API call failed with error: {e}")
        return False

def test_hearing_data():
    """Test hearing data retrieval"""
    print("\n🔧 Testing hearing data retrieval...")
    
    api_key = os.environ.get('CONGRESS_API_KEY')
    if not api_key:
        return False
    
    try:
        # Test recent hearings
        url = "https://api.congress.gov/v3/hearing"
        params = {
            'api_key': api_key,
            'format': 'json',
            'limit': 3
        }
        
        print(f"Testing hearing API call to: {url}")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            hearings = data.get('hearings', [])
            print(f"✅ Hearing data retrieved: {len(hearings)} hearings")
            
            # Show first hearing as example
            if hearings:
                first_hearing = hearings[0]
                print(f"Example hearing: {first_hearing.get('title', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Hearing API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Hearing API call failed with error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Congress API Configuration on Cloud Platform")
    print("=" * 60)
    
    success = True
    
    # Test basic API connectivity
    if not test_congress_api_env():
        success = False
    
    # Test committee data
    if not test_committee_data():
        success = False
    
    # Test hearing data
    if not test_hearing_data():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All Congress API tests passed!")
        print("🎯 Ready to proceed with Milestone 2: Cloud Audio Processing")
        return True
    else:
        print("❌ Some Congress API tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)