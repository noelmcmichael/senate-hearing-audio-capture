#!/usr/bin/env python3
"""
Integration test to verify modal and transcript fixes
Tests API endpoints and verifies data availability
"""

import requests
import json
import time
from typing import Dict, List

class ModalFixTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        
    def test_api_health(self) -> bool:
        """Test API health"""
        try:
            response = requests.get(f"{self.base_url}/api")
            return response.status_code == 200
        except:
            return False
    
    def test_hearing_details(self, hearing_id: int) -> Dict:
        """Test hearing details endpoint"""
        response = requests.get(f"{self.base_url}/api/hearings/{hearing_id}")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch hearing {hearing_id}: {response.status_code}")
    
    def test_transcript_browser(self) -> Dict:
        """Test transcript browser endpoint"""
        response = requests.get(f"{self.base_url}/api/transcript-browser/hearings")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch transcripts: {response.status_code}")
    
    def test_multiple_hearing_details(self, hearing_ids: List[int]) -> Dict:
        """Test multiple hearing detail requests (simulating rapid clicks)"""
        results = {}
        
        # Make rapid requests
        for hearing_id in hearing_ids:
            try:
                start_time = time.time()
                result = self.test_hearing_details(hearing_id)
                end_time = time.time()
                
                results[hearing_id] = {
                    'success': True,
                    'response_time': end_time - start_time,
                    'hearing_title': result.get('hearing_title', 'Unknown'),
                    'processing_stage': result.get('processing_stage', 'Unknown')
                }
            except Exception as e:
                results[hearing_id] = {
                    'success': False,
                    'error': str(e)
                }
                
        return results
    
    def test_transcript_availability(self) -> Dict:
        """Test transcript availability for hearings"""
        transcript_data = self.test_transcript_browser()
        transcripts = transcript_data.get('transcripts', [])
        
        # Group by hearing ID
        transcript_map = {}
        for transcript in transcripts:
            hearing_id = transcript.get('hearing_id')
            if hearing_id:
                transcript_map[hearing_id] = {
                    'title': transcript.get('hearing_title', 'Unknown'),
                    'committee': transcript.get('committee_code', 'Unknown'),
                    'status': transcript.get('processing_stage', 'Unknown'),
                    'confidence': transcript.get('confidence', 0),
                    'segments': len(transcript.get('segments', []))
                }
        
        return {
            'total_transcripts': len(transcripts),
            'hearing_transcripts': transcript_map
        }
    
    def run_full_test(self) -> Dict:
        """Run comprehensive test suite"""
        print("🧪 Running Modal and Transcript Fixes Test Suite...")
        
        results = {}
        
        # Test 1: API Health
        print("1. Testing API health...")
        results['api_health'] = self.test_api_health()
        print(f"   API Health: {'✅ PASS' if results['api_health'] else '❌ FAIL'}")
        
        if not results['api_health']:
            print("❌ API is not responding. Cannot continue tests.")
            return results
        
        # Test 2: Multiple hearing details (simulating rapid modal opens)
        print("2. Testing multiple hearing details (simulating rapid clicks)...")
        test_hearing_ids = [1, 2, 3, 4]  # Same IDs from console log
        results['multiple_hearings'] = self.test_multiple_hearing_details(test_hearing_ids)
        
        success_count = sum(1 for r in results['multiple_hearings'].values() if r['success'])
        print(f"   Multiple Hearings: {success_count}/{len(test_hearing_ids)} successful")
        
        for hearing_id, result in results['multiple_hearings'].items():
            if result['success']:
                print(f"   - Hearing {hearing_id}: ✅ {result['hearing_title']} ({result['processing_stage']}) - {result['response_time']:.3f}s")
            else:
                print(f"   - Hearing {hearing_id}: ❌ {result['error']}")
        
        # Test 3: Transcript availability
        print("3. Testing transcript availability...")
        try:
            results['transcripts'] = self.test_transcript_availability()
            print(f"   Transcripts: ✅ {results['transcripts']['total_transcripts']} available")
            
            # Show which hearings have transcripts
            hearing_transcripts = results['transcripts']['hearing_transcripts']
            for hearing_id, transcript_info in hearing_transcripts.items():
                if hearing_id in test_hearing_ids:
                    print(f"   - Hearing {hearing_id}: {transcript_info['title']} ({transcript_info['status']}) - {transcript_info['segments']} segments")
        except Exception as e:
            results['transcripts'] = {'error': str(e)}
            print(f"   Transcripts: ❌ {e}")
        
        # Test 4: Cross-reference hearing details with transcript availability
        print("4. Cross-referencing hearing details with transcript availability...")
        if 'transcripts' in results and 'hearing_transcripts' in results['transcripts']:
            transcript_hearing_ids = set(results['transcripts']['hearing_transcripts'].keys())
            detail_hearing_ids = set(h_id for h_id, result in results['multiple_hearings'].items() if result['success'])
            
            common_hearings = transcript_hearing_ids.intersection(detail_hearing_ids)
            print(f"   Common hearings with both details and transcripts: {len(common_hearings)}")
            
            for hearing_id in common_hearings:
                hearing_detail = results['multiple_hearings'][hearing_id]
                transcript_info = results['transcripts']['hearing_transcripts'][hearing_id]
                
                print(f"   - Hearing {hearing_id}: Details stage '{hearing_detail['processing_stage']}' vs Transcript stage '{transcript_info['status']}'")
        
        print("\n🎯 Test Summary:")
        print(f"   API Health: {'✅' if results['api_health'] else '❌'}")
        print(f"   Hearing Details: {'✅' if success_count == len(test_hearing_ids) else '❌'}")
        print(f"   Transcripts: {'✅' if 'transcripts' in results and 'error' not in results['transcripts'] else '❌'}")
        
        return results

def main():
    tester = ModalFixTester()
    results = tester.run_full_test()
    
    # Save results for documentation
    with open('modal_fix_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📊 Detailed results saved to modal_fix_test_results.json")

if __name__ == "__main__":
    main()