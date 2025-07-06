#!/usr/bin/env python3
"""
Test script for enhanced transcription API with chunking support.
"""

import requests
import json
import time
import sqlite3
from pathlib import Path

def test_enhanced_transcription_api():
    """Test the enhanced transcription API with real hearing."""
    
    API_BASE = "http://localhost:8001"
    
    print("🧪 Testing Enhanced Transcription API with Chunking")
    
    # First, find a hearing in 'captured' state
    db_path = Path(__file__).parent / 'data' / 'demo_enhanced_ui.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get hearings in captured state
    cursor.execute('''
        SELECT id, hearing_title, processing_stage, committee_code
        FROM hearings_unified 
        WHERE processing_stage = 'captured'
        LIMIT 1
    ''')
    result = cursor.fetchone()
    
    if not result:
        print("❌ No hearings in 'captured' state found for testing")
        
        # Let's set hearing 44 to captured state for testing
        cursor.execute('''
            UPDATE hearings_unified 
            SET processing_stage = 'captured'
            WHERE id = 44
        ''')
        conn.commit()
        
        cursor.execute('SELECT id, hearing_title, processing_stage, committee_code FROM hearings_unified WHERE id = 44')
        result = cursor.fetchone()
    
    conn.close()
    
    if not result:
        print("❌ Could not find or create test hearing")
        return False
    
    hearing_id, title, stage, committee = result
    print(f"📋 Test hearing: {hearing_id} - {title}")
    print(f"📊 Current stage: {stage}")
    print(f"🏛️  Committee: {committee}")
    
    # Test 1: Check progress before transcription
    print(f"\n🔍 Test 1: Check initial progress")
    try:
        response = requests.get(f"{API_BASE}/api/hearings/{hearing_id}/transcription/progress")
        if response.status_code == 200:
            progress = response.json()
            print(f"✅ Initial progress: {progress['progress_percent']}% - {progress['progress_message']}")
        else:
            print(f"❌ Progress check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Progress check error: {e}")
        return False
    
    # Test 2: Trigger transcription
    print(f"\n🎵 Test 2: Trigger enhanced transcription")
    try:
        response = requests.post(f"{API_BASE}/api/hearings/{hearing_id}/pipeline/transcribe")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Transcription successful!")
            print(f"📊 Results:")
            print(f"   Processing method: {result.get('processing_method', 'unknown')}")
            print(f"   Segments: {result.get('transcript_segments', 0)}")
            print(f"   Duration: {result.get('transcript_duration', 0):.1f} seconds")
            print(f"   Characters: {result.get('transcript_characters', 0):,}")
            print(f"   Chunks processed: {result.get('chunks_processed', 1)}")
            
            # Determine if chunking was used
            if result.get('chunks_processed', 1) > 1:
                print(f"🎉 CHUNKED PROCESSING SUCCESSFUL! {result['chunks_processed']} chunks processed")
            else:
                print(f"📁 Direct processing used (small file)")
            
        else:
            print(f"❌ Transcription failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return False
    
    # Test 3: Check progress after transcription
    print(f"\n🔍 Test 3: Check final progress")
    try:
        response = requests.get(f"{API_BASE}/api/hearings/{hearing_id}/transcription/progress")
        if response.status_code == 200:
            progress = response.json()
            print(f"✅ Final progress: {progress['progress_percent']}% - {progress['progress_message']}")
            print(f"📊 Processing stage: {progress['processing_stage']}")
        else:
            print(f"❌ Final progress check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Final progress check error: {e}")
        return False
    
    # Test 4: Verify transcript is available
    print(f"\n📄 Test 4: Verify transcript availability")
    try:
        response = requests.get(f"{API_BASE}/api/hearings/{hearing_id}/transcript")
        if response.status_code == 200:
            transcript = response.json()
            segments = len(transcript.get('segments', []))
            text_length = len(transcript.get('text', ''))
            print(f"✅ Transcript available: {segments} segments, {text_length:,} characters")
            
            # Show a sample of the transcript
            if transcript.get('text'):
                sample = transcript['text'][:200] + "..." if len(transcript['text']) > 200 else transcript['text']
                print(f"📝 Sample: {sample}")
            
        else:
            print(f"❌ Transcript not available: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Transcript check error: {e}")
        return False
    
    print(f"\n🎉 All tests completed successfully!")
    print(f"✅ Enhanced transcription API working with chunking support")
    return True

def check_api_server():
    """Check if API server is running."""
    try:
        response = requests.get("http://localhost:8001/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Main test execution."""
    print("🧪 Enhanced Transcription API Test Suite")
    
    # Check if API server is running
    if not check_api_server():
        print("❌ API server not running on localhost:8001")
        print("💡 Start the server with: python simple_api_server.py")
        return False
    
    print("✅ API server is running")
    
    # Run the test
    return test_enhanced_transcription_api()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)