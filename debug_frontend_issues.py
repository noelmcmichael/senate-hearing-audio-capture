#!/usr/bin/env python3
"""
Debug frontend issues by testing browser compatibility and API responses.
"""
import requests
import json
from datetime import datetime

# Production service URL
BASE_URL = "https://senate-hearing-processor-518203250893.us-central1.run.app"

def test_cors_and_api_calls():
    """Test CORS and API call responses that the frontend would make."""
    print("="*60)
    print("🔍 FRONTEND-BACKEND COMMUNICATION DEBUG")
    print("="*60)
    
    # Test API calls with proper headers that a browser would send
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Origin': BASE_URL,
        'Referer': BASE_URL,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    print("\n📡 Testing API calls with browser headers...")
    
    # Test the main API endpoints the frontend would call
    api_tests = [
        ("GET /api/committees", "GET", "/api/committees", None),
        ("GET /api/committees/SCOM/hearings", "GET", "/api/committees/SCOM/hearings", None),
        ("POST /api/hearings/discover", "POST", "/api/hearings/discover", {"committee_codes": ["SCOM"]}),
        ("GET /admin/status", "GET", "/admin/status", None),
    ]
    
    for test_name, method, endpoint, payload in api_tests:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n🔍 {test_name}")
        print(f"   URL: {url}")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            else:
                response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Success - JSON Response")
                    if endpoint == "/api/committees":
                        committees = data.get('committees', [])
                        print(f"   📊 Committees found: {len(committees)}")
                        for i, committee in enumerate(committees[:2]):
                            print(f"   - Committee {i+1}: {committee.get('code')} - {committee.get('name')}")
                    elif endpoint == "/admin/status":
                        print(f"   📊 Status: {data.get('status')}")
                        print(f"   📊 Committees: {data.get('committees')}")
                        print(f"   📊 Hearings: {data.get('hearings')}")
                except Exception as e:
                    print(f"   ❌ Failed to parse JSON: {e}")
                    print(f"   Raw response: {response.text[:200]}...")
            else:
                print(f"   ❌ Failed with status {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    print("\n📋 Testing CORS headers...")
    try:
        response = requests.options(f"{BASE_URL}/api/committees", headers=headers)
        print(f"   OPTIONS request status: {response.status_code}")
        cors_headers = {k: v for k, v in response.headers.items() if k.lower().startswith('access-control')}
        if cors_headers:
            print(f"   CORS headers: {cors_headers}")
        else:
            print("   ⚠️  No CORS headers found")
    except Exception as e:
        print(f"   ❌ CORS test failed: {e}")

def check_frontend_structure():
    """Check the actual frontend HTML and JavaScript structure."""
    print("\n" + "="*60)
    print("🌐 FRONTEND STRUCTURE ANALYSIS")
    print("="*60)
    
    try:
        # Get the main page
        response = requests.get(BASE_URL, timeout=10)
        html = response.text
        
        print(f"📄 HTML Response ({len(html)} chars):")
        print(html[:1000] + "..." if len(html) > 1000 else html)
        
        # Check for specific React elements
        react_checks = [
            ("React root div", '<div id="root">' in html),
            ("React scripts", 'static/js/main' in html),
            ("React CSS", 'static/css/main' in html),
            ("Proper doctype", html.lower().startswith('<!doctype html>')),
            ("Meta viewport", 'viewport' in html),
            ("Title tag", '<title>' in html),
        ]
        
        print(f"\n🔍 React Structure Checks:")
        for check_name, passed in react_checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
        
        # Check if the HTML looks complete
        if len(html) < 1000:
            print(f"\n⚠️  HTML seems short ({len(html)} chars) - possible incomplete response")
        
    except Exception as e:
        print(f"❌ Frontend structure check failed: {e}")

def test_static_resources():
    """Test if static resources are loading properly."""
    print("\n" + "="*60)
    print("📦 STATIC RESOURCES TEST")
    print("="*60)
    
    # Extract resource URLs from the HTML
    try:
        response = requests.get(BASE_URL, timeout=10)
        html = response.text
        
        # Look for JavaScript and CSS files
        import re
        js_files = re.findall(r'src="(/static/js/[^"]+)"', html)
        css_files = re.findall(r'href="(/static/css/[^"]+)"', html)
        
        print(f"📄 Found {len(js_files)} JS files and {len(css_files)} CSS files")
        
        # Test each resource
        for resource_type, files in [("JavaScript", js_files), ("CSS", css_files)]:
            for file_path in files:
                url = f"{BASE_URL}{file_path}"
                try:
                    response = requests.get(url, timeout=10)
                    size = len(response.content)
                    content_type = response.headers.get('content-type', 'unknown')
                    
                    if response.status_code == 200:
                        print(f"   ✅ {resource_type}: {file_path} ({size} bytes, {content_type})")
                        
                        # Check if JS file contains React code
                        if resource_type == "JavaScript" and size > 0:
                            content = response.text
                            if 'React' in content or 'jsx' in content or 'useState' in content:
                                print(f"      📋 Contains React code")
                            else:
                                print(f"      ⚠️  No React code detected")
                    else:
                        print(f"   ❌ {resource_type}: {file_path} - Status {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ {resource_type}: {file_path} - Error: {e}")
    
    except Exception as e:
        print(f"❌ Static resources test failed: {e}")

def main():
    """Run all frontend debugging tests."""
    print("🚀 FRONTEND DEBUGGING SUITE")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_cors_and_api_calls()
    check_frontend_structure()
    test_static_resources()
    
    print("\n" + "="*60)
    print("🎯 DEBUGGING COMPLETE")
    print("="*60)
    
    print("\n💡 NEXT STEPS:")
    print("1. Check browser console for JavaScript errors")
    print("2. Verify network requests in browser dev tools")
    print("3. Check if React app is making API calls")
    print("4. Inspect React component rendering")

if __name__ == "__main__":
    main()