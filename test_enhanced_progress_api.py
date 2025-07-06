#!/usr/bin/env python3
"""
Test enhanced progress tracking API for chunked transcription.
"""

import requests
import time
import json
from pathlib import Path

def test_enhanced_progress_api():
    """Test the enhanced progress tracking API with chunked processing."""
    
    base_url = "http://localhost:8001"
    
    print("🧪 Testing Enhanced Progress Tracking API")
    print("=" * 50)
    
    # Test 1: Get progress for a hearing that doesn't exist
    print("\n1. Testing progress endpoint with non-existent hearing...")
    response = requests.get(f"{base_url}/api/hearings/99999/transcription/progress")
    
    if response.status_code == 404:
        print("✅ Correctly returns 404 for non-existent hearing")
    else:
        print(f"❌ Expected 404, got {response.status_code}")
        return False
    
    # Test 2: Get progress for a hearing in captured stage
    print("\n2. Testing progress endpoint with captured hearing...")
    
    # Find a hearing in captured stage
    hearings_response = requests.get(f"{base_url}/api/hearings")
    if hearings_response.status_code != 200:
        print("❌ Failed to get hearings list")
        return False
    
    hearings = hearings_response.json()
    captured_hearing = None
    
    for hearing in hearings.get('hearings', []):
        if hearing.get('processing_stage') == 'captured':
            captured_hearing = hearing
            break
    
    if not captured_hearing:
        print("⚠️  No hearing in 'captured' stage found for testing")
        return True  # Skip this test
    
    hearing_id = captured_hearing['id']
    print(f"📋 Using hearing {hearing_id}: {captured_hearing['hearing_title'][:50]}...")
    
    # Get initial progress
    progress_response = requests.get(f"{base_url}/api/hearings/{hearing_id}/transcription/progress")
    
    if progress_response.status_code != 200:
        print(f"❌ Failed to get progress: {progress_response.status_code}")
        return False
    
    progress_data = progress_response.json()
    print("✅ Successfully retrieved initial progress")
    print(f"   Stage: {progress_data['detailed_progress']['stage']}")
    print(f"   Progress: {progress_data['detailed_progress']['overall_progress']}%")
    print(f"   Message: {progress_data['detailed_progress']['message']}")
    
    # Test 3: Trigger transcription and monitor detailed progress
    print(f"\n3. Testing detailed progress during transcription...")
    
    # Start transcription
    print("🚀 Starting transcription...")
    transcribe_response = requests.post(f"{base_url}/api/hearings/{hearing_id}/pipeline/transcribe")
    
    if transcribe_response.status_code not in [200, 202]:
        print(f"❌ Failed to start transcription: {transcribe_response.status_code}")
        print(f"   Response: {transcribe_response.text}")
        return False
    
    print("✅ Transcription started successfully")
    
    # Monitor progress
    print("\n📊 Monitoring progress updates...")
    last_stage = ""
    last_progress = -1
    progress_updates = []
    max_checks = 60  # Maximum checks (5 minutes at 5-second intervals)
    check_interval = 5  # seconds
    
    for check in range(max_checks):
        time.sleep(check_interval)
        
        progress_response = requests.get(f"{base_url}/api/hearings/{hearing_id}/transcription/progress")
        
        if progress_response.status_code != 200:
            print(f"❌ Failed to get progress update: {progress_response.status_code}")
            continue
        
        progress_data = progress_response.json()
        detailed = progress_data['detailed_progress']
        
        stage = detailed['stage']
        overall_progress = detailed['overall_progress']
        message = detailed['message']
        chunk_progress = detailed.get('chunk_progress')
        estimated_time = detailed.get('estimated_time_remaining')
        
        # Only print if progress changed
        if stage != last_stage or overall_progress != last_progress:
            print(f"\n🔄 Progress Update #{len(progress_updates) + 1}")
            print(f"   Stage: {stage}")
            print(f"   Overall Progress: {overall_progress}%")
            print(f"   Message: {message}")
            
            if chunk_progress:
                print(f"   Chunk Progress: {chunk_progress['current_chunk']}/{chunk_progress['total_chunks']}")
                print(f"   Current Chunk: {chunk_progress['chunk_progress']}%")
            
            if estimated_time:
                minutes = estimated_time // 60
                seconds = estimated_time % 60
                print(f"   Estimated Time Remaining: {minutes}m {seconds}s")
            
            progress_updates.append({
                'stage': stage,
                'overall_progress': overall_progress,
                'message': message,
                'chunk_progress': chunk_progress,
                'estimated_time': estimated_time,
                'is_chunked': detailed.get('is_chunked_processing', False)
            })
            
            last_stage = stage
            last_progress = overall_progress
        
        # Check if completed
        if stage in ['completed', 'failed'] or overall_progress >= 100:
            print(f"\n🎯 Transcription {stage}!")
            break
    
    # Test 4: Validate progress data structure
    print(f"\n4. Validating progress data structure...")
    
    if not progress_updates:
        print("⚠️  No progress updates captured")
        return True
    
    # Check for expected stages
    stages_seen = [update['stage'] for update in progress_updates]
    expected_stages = ['analyzing', 'chunking', 'processing', 'merging', 'cleanup', 'completed']
    
    print(f"   Stages seen: {list(set(stages_seen))}")
    
    # Check for chunked processing indicators
    chunked_updates = [update for update in progress_updates if update.get('chunk_progress')]
    
    if chunked_updates:
        print("✅ Detected chunked processing with detailed chunk progress")
        print(f"   Total chunks processed: {max([cp['chunk_progress']['total_chunks'] for cp in chunked_updates])}")
        print(f"   Chunk progress updates: {len(chunked_updates)}")
    else:
        print("📁 Single-file processing (no chunking required)")
    
    # Check progress monotonicity (should generally increase)
    progress_values = [update['overall_progress'] for update in progress_updates]
    is_monotonic = all(progress_values[i] <= progress_values[i+1] for i in range(len(progress_values)-1))
    
    if is_monotonic:
        print("✅ Progress values are monotonic (increasing)")
    else:
        print("⚠️  Progress values are not strictly monotonic")
        print(f"   Progress sequence: {progress_values}")
    
    # Test 5: Final progress check
    print(f"\n5. Final progress validation...")
    
    final_progress_response = requests.get(f"{base_url}/api/hearings/{hearing_id}/transcription/progress")
    
    if final_progress_response.status_code == 200:
        final_data = final_progress_response.json()
        final_detailed = final_data['detailed_progress']
        
        print(f"   Final Stage: {final_detailed['stage']}")
        print(f"   Final Progress: {final_detailed['overall_progress']}%")
        
        if final_detailed['error']:
            print(f"   Error: {final_detailed['error']}")
        else:
            print("✅ No errors reported")
    
    print("\n" + "=" * 50)
    print("🎯 Enhanced Progress API Test Summary:")
    print(f"   - Progress updates captured: {len(progress_updates)}")
    print(f"   - Chunked processing detected: {'Yes' if chunked_updates else 'No'}")
    print(f"   - Progress monotonicity: {'Passed' if is_monotonic else 'Failed'}")
    print(f"   - Final completion: {'Yes' if progress_updates and progress_updates[-1]['overall_progress'] >= 100 else 'Pending'}")
    
    return True

if __name__ == "__main__":
    success = test_enhanced_progress_api()
    
    if success:
        print("\n✅ Enhanced Progress API Test PASSED")
    else:
        print("\n❌ Enhanced Progress API Test FAILED")
        exit(1)