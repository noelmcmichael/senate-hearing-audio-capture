#!/usr/bin/env python3
"""
Test frontend functionality by verifying all key endpoints work correctly.
"""
import requests
import json
import time
from datetime import datetime

# Production service URL
BASE_URL = "https://senate-hearing-processor-518203250893.us-central1.run.app"

def test_frontend_endpoints():
    """Test all key frontend endpoints."""
    print("="*60)
    print("🎯 FRONTEND FUNCTIONALITY TEST")
    print("="*60)
    print(f"Testing service at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test frontend pages
    frontend_tests = [
        ("Frontend Root", "/", "Should load React dashboard"),
        ("Admin Page", "/admin", "Should load admin interface"),
        ("Health Check", "/health", "Should return health status"),
        ("API Documentation", "/docs", "Should load Swagger UI"),
    ]
    
    # Test API endpoints
    api_tests = [
        ("Committees API", "/api/committees", "Should return committee list"),
        ("Admin Status", "/admin/status", "Should return system status"),
        ("Health API", "/health", "Should return JSON health"),
    ]
    
    print("\n📱 FRONTEND PAGES:")
    for name, endpoint, description in frontend_tests:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                length = len(response.text)
                print(f"   ✅ {name}: {response.status_code} ({length} chars)")
            else:
                print(f"   ❌ {name}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
    
    print("\n🔌 API ENDPOINTS:")
    for name, endpoint, description in api_tests:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if endpoint == "/api/committees":
                        committees = data.get('committees', [])
                        print(f"   ✅ {name}: {len(committees)} committees")
                        for committee in committees[:2]:  # Show first 2
                            print(f"      - {committee.get('code')}: {committee.get('name')}")
                    elif endpoint == "/admin/status":
                        print(f"   ✅ {name}: {data.get('committees', 0)} committees, {data.get('hearings', 0)} hearings")
                    else:
                        print(f"   ✅ {name}: {response.status_code}")
                except:
                    print(f"   ✅ {name}: {response.status_code} (non-JSON)")
            else:
                print(f"   ❌ {name}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
    
    print("\n🔍 FRONTEND RESOURCE CHECK:")
    # Check if React resources are loading
    resources = [
        ("React JS", "/static/js/main.2581e3e8.js"),
        ("React CSS", "/static/css/main.09a0e5c7.css"),
        ("Favicon", "/favicon.ico"),
    ]
    
    for name, path in resources:
        url = f"{BASE_URL}{path}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                size = len(response.content)
                print(f"   ✅ {name}: {size} bytes")
            else:
                print(f"   ❌ {name}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
    
    print("\n🌐 BROWSER COMPATIBILITY TEST:")
    # Test if HTML contains proper React structure
    try:
        response = requests.get(BASE_URL, timeout=10)
        html = response.text
        
        checks = [
            ("React Root Div", '<div id="root">' in html),
            ("React Scripts", 'static/js/main' in html),
            ("React CSS", 'static/css/main' in html),
            ("Proper DOCTYPE", '<!doctype html>' in html.lower()),
        ]
        
        for name, check in checks:
            if check:
                print(f"   ✅ {name}: Present")
            else:
                print(f"   ❌ {name}: Missing")
                
    except Exception as e:
        print(f"   ❌ HTML Check: Error - {e}")
    
    print("\n" + "="*60)
    print("✅ FRONTEND TEST COMPLETE")
    print("="*60)
    
    print("\n🚀 NEXT STEPS:")
    print("   1. Open browser and navigate to:", BASE_URL)
    print("   2. Check that committees are displayed")
    print("   3. Test admin page functionality")
    print("   4. Verify discovery system works")

if __name__ == "__main__":
    test_frontend_endpoints()