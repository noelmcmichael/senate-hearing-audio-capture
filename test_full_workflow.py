#!/usr/bin/env python3
"""
Test Full Workflow - End-to-End System Testing
"""

import requests
import json
import sqlite3
from pathlib import Path
from datetime import datetime

class WorkflowTester:
    def __init__(self):
        self.api_base = "http://localhost:8001/api"
        self.db_path = Path('data/demo_enhanced_ui.db')
        self.transcript_dir = Path('output/demo_transcription')
        
    def test_api_health(self):
        """Test API server health"""
        try:
            response = requests.get(f"{self.api_base}/health")
            if response.status_code == 200:
                print("✅ API Server: Healthy")
                return True
            else:
                print(f"❌ API Server: Unhealthy ({response.status_code})")
                return False
        except Exception as e:
            print(f"❌ API Server: Connection failed ({e})")
            return False
    
    def test_database_status(self):
        """Test database connectivity and data"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Check hearing count
            cursor.execute("SELECT COUNT(*) FROM hearings_unified")
            total_count = cursor.fetchone()[0]
            
            # Check complete hearings
            cursor.execute("SELECT COUNT(*) FROM hearings_unified WHERE status = 'complete'")
            complete_count = cursor.fetchone()[0]
            
            # Check processing hearings
            cursor.execute("SELECT COUNT(*) FROM hearings_unified WHERE status = 'processing'")
            processing_count = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"✅ Database: {total_count} hearings ({complete_count} complete, {processing_count} processing)")
            return True
        except Exception as e:
            print(f"❌ Database: Connection failed ({e})")
            return False
    
    def test_transcript_files(self):
        """Test transcript file availability"""
        try:
            transcript_files = list(self.transcript_dir.glob('hearing_*_transcript.json'))
            print(f"✅ Transcript Files: {len(transcript_files)} available")
            
            # Test a sample transcript
            if transcript_files:
                with open(transcript_files[0]) as f:
                    sample = json.load(f)
                segments = len(sample.get('segments', []))
                print(f"   Sample transcript: {segments} segments, confidence: {sample.get('confidence')}")
            
            return True
        except Exception as e:
            print(f"❌ Transcript Files: Error ({e})")
            return False
    
    def test_committee_endpoints(self):
        """Test committee-based hearing endpoints"""
        committees = ['SCOM', 'SSJU', 'HJUD', 'SBAN', 'SSCI']
        success_count = 0
        
        for committee in committees:
            try:
                response = requests.get(f"{self.api_base}/committees/{committee}/hearings")
                if response.status_code == 200:
                    data = response.json()
                    hearing_count = len(data.get('hearings', []))
                    print(f"✅ Committee {committee}: {hearing_count} hearings")
                    success_count += 1
                else:
                    print(f"❌ Committee {committee}: Error ({response.status_code})")
            except Exception as e:
                print(f"❌ Committee {committee}: Connection failed ({e})")
        
        return success_count == len(committees)
    
    def test_transcript_browser(self):
        """Test transcript browser endpoint"""
        try:
            response = requests.get(f"{self.api_base}/transcript-browser/hearings")
            if response.status_code == 200:
                data = response.json()
                transcripts = data.get('transcripts', [])
                print(f"✅ Transcript Browser: {len(transcripts)} transcripts available")
                
                # Test transcript detail
                if transcripts:
                    sample = transcripts[0]
                    segments = len(sample.get('segments', []))
                    print(f"   Sample: {sample.get('title', 'Unknown')[:40]}... ({segments} segments)")
                
                return True
            else:
                print(f"❌ Transcript Browser: Error ({response.status_code})")
                return False
        except Exception as e:
            print(f"❌ Transcript Browser: Connection failed ({e})")
            return False
    
    def test_hearing_detail(self):
        """Test individual hearing detail endpoint"""
        try:
            response = requests.get(f"{self.api_base}/hearings/1")
            if response.status_code == 200:
                data = response.json()
                hearing = data.get('hearing', {})
                title = hearing.get('hearing_title', 'Unknown')
                status = hearing.get('processing_stage', 'Unknown')
                print(f"✅ Hearing Detail: {title[:40]}... (status: {status})")
                return True
            else:
                print(f"❌ Hearing Detail: Error ({response.status_code})")
                return False
        except Exception as e:
            print(f"❌ Hearing Detail: Connection failed ({e})")
            return False
    
    def test_frontend_accessibility(self):
        """Test if frontend is accessible"""
        try:
            response = requests.get("http://localhost:3000")
            if response.status_code == 200:
                print("✅ Frontend: Accessible at http://localhost:3000")
                return True
            else:
                print(f"❌ Frontend: Error ({response.status_code})")
                return False
        except Exception as e:
            print(f"❌ Frontend: Connection failed ({e})")
            return False
    
    def run_full_test(self):
        """Run complete workflow test"""
        print("🧪 Running Full Workflow Test")
        print("=" * 50)
        
        tests = [
            ("API Health", self.test_api_health),
            ("Database Status", self.test_database_status),
            ("Transcript Files", self.test_transcript_files),
            ("Committee Endpoints", self.test_committee_endpoints),
            ("Transcript Browser", self.test_transcript_browser),
            ("Hearing Detail", self.test_hearing_detail),
            ("Frontend Accessibility", self.test_frontend_accessibility)
        ]
        
        results = []
        for name, test_func in tests:
            print(f"\n{name}:")
            result = test_func()
            results.append(result)
        
        print("\n" + "=" * 50)
        print("📊 Test Results:")
        passed = sum(results)
        total = len(results)
        print(f"   {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ All systems operational - Ready for production testing!")
        else:
            print("❌ Some systems need attention")
        
        return passed == total

if __name__ == "__main__":
    tester = WorkflowTester()
    tester.run_full_test()