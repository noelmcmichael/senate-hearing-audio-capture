#!/usr/bin/env python3
"""
Test Congress API connectivity from cloud platform
"""
import os
import sys
import json
import requests
from google.cloud import secretmanager

def get_secret(secret_name):
    """Get secret from GCP Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'senate-hearing-capture')
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error accessing secret {secret_name}: {e}")
        return None

def test_congress_api():
    """Test Congress.gov API connectivity"""
    print("Testing Congress.gov API connectivity...")
    
    # Get API key from Secret Manager
    api_key = get_secret("congress-api-key")
    if not api_key:
        print("❌ Failed to get Congress API key from Secret Manager")
        return False
    
    print(f"✅ Retrieved Congress API key: {api_key[:10]}...")
    
    # Test API connectivity
    try:
        url = "https://api.congress.gov/v3/member"
        params = {
            'api_key': api_key,
            'format': 'json',
            'limit': 1
        }
        
        print(f"Testing API call to: {url}")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API call successful")
            print(f"Response contains {len(data.get('members', []))} members")
            return True
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API call failed with error: {e}")
        return False

def test_committee_sync():
    """Test committee data synchronization"""
    print("\nTesting committee data synchronization...")
    
    # Get API key
    api_key = get_secret("congress-api-key")
    if not api_key:
        return False
    
    # Test Commerce Committee members
    try:
        url = "https://api.congress.gov/v3/committee/senate/scom"
        params = {
            'api_key': api_key,
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            committee = data.get('committee', {})
            print(f"✅ Committee data retrieved: {committee.get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ Committee API call failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Committee API call failed with error: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 Testing Congress API Configuration on Cloud Platform")
    print("=" * 60)
    
    success = True
    
    # Test API connectivity
    if not test_congress_api():
        success = False
    
    # Test committee sync
    if not test_committee_sync():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All API tests passed! Congress API is properly configured.")
        sys.exit(0)
    else:
        print("❌ Some API tests failed. Check configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()