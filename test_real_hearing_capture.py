#!/usr/bin/env python3
"""
Test Real Hearing Capture
Test the complete workflow on real Senate hearings
"""

import requests
import json
import sqlite3
import time
import sys
from pathlib import Path

class RealHearingCaptureTester:
    def __init__(self, db_path="data/hearings_unified.db"):
        self.db_path = db_path
        self.base_url = "http://localhost:8001"  # Local API server
        
    def get_real_hearings(self):
        """Get real hearings from local database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, committee_code, hearing_title, hearing_date, 
                       external_urls, sync_status, extraction_status
                FROM hearings_unified
                ORDER BY id
            """)
            
            hearings = cursor.fetchall()
            conn.close()
            
            print(f"📊 Found {len(hearings)} real hearings in database")
            for hearing in hearings:
                hearing_id, committee, title, date, urls, sync_status, extraction_status = hearing
                print(f"  {hearing_id}. {committee} - {title}")
                print(f"     Status: {sync_status} → {extraction_status}")
                print(f"     URLs: {urls}")
                
            return hearings
            
        except Exception as e:
            print(f"❌ Error getting real hearings: {e}")
            return []
    
    def test_api_endpoint(self):
        """Test if local API is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Local API server is running")
                return True
            else:
                print(f"❌ API server returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Cannot reach local API server: {e}")
            print("💡 Start the API server with: python -m uvicorn src.api.main_app:app --host 0.0.0.0 --port 8001 --reload")
            return False
    
    def test_committee_endpoint(self, committee_code):
        """Test committee hearings endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/committees/{committee_code}/hearings", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                hearings = data.get('hearings', [])
                print(f"✅ Committee {committee_code} endpoint working - {len(hearings)} hearings")
                
                for hearing in hearings:
                    print(f"  - {hearing.get('title', 'No title')}")
                    print(f"    ID: {hearing.get('id')}, Date: {hearing.get('date')}")
                    
                return hearings
            else:
                print(f"❌ Committee endpoint failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error testing committee endpoint: {e}")
            return []
    
    def test_capture_audio(self, hearing_id):
        """Test audio capture on a real hearing"""
        try:
            print(f"\n🎯 Testing audio capture for hearing {hearing_id}")
            
            # Make capture request
            response = requests.post(
                f"{self.base_url}/hearings/{hearing_id}/capture",
                params={"user_id": "test-user"},
                json={
                    "hearing_id": str(hearing_id),
                    "options": {
                        "format": "wav",
                        "quality": "high"
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Capture request successful")
                print(f"   Response: {result}")
                return True
            else:
                error_text = response.text
                print(f"❌ Capture request failed: {response.status_code}")
                print(f"   Error: {error_text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing capture: {e}")
            return False
    
    def test_hearing_detail_page(self, hearing_id):
        """Test hearing detail page analysis"""
        try:
            print(f"\n🔍 Testing hearing detail page analysis for hearing {hearing_id}")
            
            # Get hearing details first
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT external_urls FROM hearings_unified WHERE id = ?", (hearing_id,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                print("❌ Hearing not found in database")
                return False
            
            urls = json.loads(result[0])
            hearing_url = urls[0] if urls else None
            
            if not hearing_url:
                print("❌ No URL found for hearing")
                return False
            
            print(f"🌐 Analyzing hearing page: {hearing_url}")
            
            # Test page analysis
            from analyze_target import analyze_page
            
            try:
                analysis = analyze_page(hearing_url)
                print(f"✅ Page analysis successful")
                print(f"   Title: {analysis.get('title', 'N/A')}")
                print(f"   ISVP Players: {len(analysis.get('isvp_players', []))}")
                print(f"   YouTube Videos: {len(analysis.get('youtube_videos', []))}")
                
                return analysis
                
            except Exception as e:
                print(f"❌ Page analysis failed: {e}")
                return None
                
        except Exception as e:
            print(f"❌ Error testing hearing detail page: {e}")
            return None
    
    def run_comprehensive_test(self):
        """Run comprehensive test on real hearings"""
        print("🚀 Testing Real Hearing Capture System")
        print("=" * 50)
        
        # Step 1: Get real hearings
        hearings = self.get_real_hearings()
        if not hearings:
            print("❌ No real hearings found")
            return False
        
        # Step 2: Test API connectivity
        if not self.test_api_endpoint():
            return False
        
        # Step 3: Test committee endpoint
        committee_hearings = self.test_committee_endpoint("SSJU")
        if not committee_hearings:
            print("❌ No hearings found via API")
            return False
        
        # Step 4: Test page analysis on first hearing
        first_hearing = hearings[0]
        hearing_id = first_hearing[0]
        
        page_analysis = self.test_hearing_detail_page(hearing_id)
        if not page_analysis:
            print("❌ Page analysis failed")
            return False
        
        # Step 5: Test capture request
        capture_success = self.test_capture_audio(hearing_id)
        
        # Results summary
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        print(f"✅ Database: {len(hearings)} real hearings loaded")
        print(f"✅ API: Local server responding")
        print(f"✅ Committee Endpoint: {len(committee_hearings)} hearings via API")
        print(f"✅ Page Analysis: {'Success' if page_analysis else 'Failed'}")
        print(f"{'✅' if capture_success else '❌'} Capture Request: {'Success' if capture_success else 'Failed'}")
        
        overall_success = all([
            len(hearings) > 0,
            len(committee_hearings) > 0,
            page_analysis is not None,
            capture_success
        ])
        
        if overall_success:
            print("\n🎉 ALL TESTS PASSED - Ready for real hearing processing!")
        else:
            print("\n⚠️ Some tests failed - Review issues above")
            
        return overall_success

def main():
    tester = RealHearingCaptureTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n🎯 Next Steps:")
            print("1. Start the API server: python -m uvicorn src.api.main_app:app --host 0.0.0.0 --port 8001 --reload")
            print("2. Start the frontend: cd dashboard && npm start")
            print("3. Test capture buttons in the web interface")
            print("4. Deploy updated system to production")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()