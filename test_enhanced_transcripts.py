#!/usr/bin/env python3
"""
Test Enhanced Transcripts - Verify the time gap fixes are working
"""

import json
import requests
import sqlite3
from pathlib import Path

def test_enhanced_transcripts():
    """Test the enhanced transcript quality"""
    
    print("🧪 Testing Enhanced Transcripts")
    print("=" * 50)
    
    # Test 1: API Health
    try:
        response = requests.get("http://localhost:8001/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server responding")
        else:
            print(f"❌ API server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API server not reachable: {e}")
        return False
    
    # Test 2: Sample transcript quality
    sample_hearing_ids = [1, 5, 10, 15, 20]
    
    for hearing_id in sample_hearing_ids:
        print(f"\n📋 Testing Hearing {hearing_id}:")
        
        try:
            response = requests.get(f"http://localhost:8001/api/hearings/{hearing_id}/transcript", timeout=10)
            if response.status_code != 200:
                print(f"   ❌ API error {response.status_code}")
                continue
            
            data = response.json()
            if not data.get('success'):
                print(f"   ❌ API returned error: {data}")
                continue
                
            transcript = data['transcript']
            segments = transcript['segments']
            
            # Quality checks
            duration_ok = transcript['duration_minutes'] > 15
            segment_count_ok = len(segments) > 15
            confidence_ok = transcript['confidence'] > 0.8
            
            print(f"   📊 Duration: {transcript['duration_minutes']:.1f} min {'✅' if duration_ok else '❌'}")
            print(f"   📊 Segments: {len(segments)} {'✅' if segment_count_ok else '❌'}")
            print(f"   📊 Confidence: {transcript['confidence']:.3f} {'✅' if confidence_ok else '❌'}")
            
            # Check time gaps
            if len(segments) > 1:
                gaps = []
                for i in range(1, len(segments)):
                    gap = segments[i]['start'] - segments[i-1]['end']
                    gaps.append(gap)
                
                avg_gap = sum(gaps) / len(gaps)
                max_gap = max(gaps)
                gaps_ok = max_gap <= 10  # Should be ≤ 10 seconds
                
                print(f"   🕐 Time gaps: avg={avg_gap:.1f}s, max={max_gap}s {'✅' if gaps_ok else '❌'}")
                
                if not gaps_ok:
                    print(f"   ❌ Large gaps detected: {[g for g in gaps if g > 10]}")
            
        except Exception as e:
            print(f"   ❌ Error testing hearing {hearing_id}: {e}")
    
    # Test 3: Database consistency
    print(f"\n🗄️ Testing Database Consistency:")
    try:
        conn = sqlite3.connect('data/demo_enhanced_ui.db')
        cursor = conn.execute("SELECT COUNT(*) FROM hearings_unified WHERE status = 'complete'")
        complete_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM hearings_unified")
        total_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"   📊 Total hearings: {total_count}")
        print(f"   📊 Complete hearings: {complete_count}")
        
        # Check transcript files
        transcript_dir = Path('output/demo_transcription')
        transcript_files = list(transcript_dir.glob('hearing_*_transcript.json'))
        
        print(f"   📊 Transcript files: {len(transcript_files)}")
        
        if len(transcript_files) >= complete_count:
            print("   ✅ Transcript files match database")
        else:
            print("   ❌ Missing transcript files")
            
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    # Test 4: Content quality sample
    print(f"\n📝 Testing Content Quality:")
    try:
        # Load a sample transcript directly
        with open('output/demo_transcription/hearing_1_transcript.json') as f:
            sample = json.load(f)
        
        # Check for realistic content
        sample_segments = sample['segments'][:5]
        
        realistic_content = True
        for segment in sample_segments:
            text = segment['text']
            # Check for congressional language indicators
            if not any(indicator in text.lower() for indicator in [
                'committee', 'testimony', 'question', 'representative', 'senator', 
                'thank you', 'chair', 'witness', 'hearing'
            ]):
                realistic_content = False
                break
        
        print(f"   📋 Realistic congressional content: {'✅' if realistic_content else '❌'}")
        
        # Check speaker variety
        speakers = set(seg['speaker'] for seg in sample_segments)
        speaker_variety = len(speakers) >= 3
        print(f"   🗣️ Speaker variety: {speakers} {'✅' if speaker_variety else '❌'}")
        
    except Exception as e:
        print(f"   ❌ Content quality error: {e}")
    
    print(f"\n🏁 Enhanced Transcript Test Complete")
    return True

if __name__ == "__main__":
    test_enhanced_transcripts()