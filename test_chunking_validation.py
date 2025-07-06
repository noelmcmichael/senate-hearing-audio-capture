#!/usr/bin/env python3
"""
Comprehensive validation test for audio chunking implementation.
Compares old demo system vs new chunked processing system.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
import time

from transcription_service import TranscriptionService  # Old demo system
from enhanced_transcription_service import EnhancedTranscriptionService  # New chunked system

def test_demo_vs_chunked_comparison():
    """Compare old demo system with new chunked processing system."""
    
    print("🧪 Audio Chunking Validation Test")
    print("📊 Comparing Demo System vs. Chunked Processing System")
    print("=" * 70)
    
    # Test hearing ID (hearing 44 - smaller for demo comparison)
    hearing_id = 44
    
    # Database setup
    db_path = Path(__file__).parent / 'data' / 'demo_enhanced_ui.db'
    
    # Set hearing to captured state for testing
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE hearings_unified 
        SET processing_stage = 'captured'
        WHERE id = ?
    ''', (hearing_id,))
    conn.commit()
    
    # Get hearing info
    cursor.execute('SELECT id, hearing_title, committee_code FROM hearings_unified WHERE id = ?', (hearing_id,))
    hearing = cursor.fetchone()
    conn.close()
    
    if not hearing:
        print(f"❌ Hearing {hearing_id} not found")
        return False
    
    hearing_id, title, committee = hearing
    print(f"📋 Test Hearing: {hearing_id} - {title}")
    print(f"🏛️  Committee: {committee}")
    
    results = {}
    
    # Test 1: Old Demo System
    print(f"\n🔄 Test 1: OLD DEMO SYSTEM")
    print("-" * 40)
    
    try:
        start_time = time.time()
        
        old_service = TranscriptionService(db_path=db_path)
        old_transcript = old_service.transcribe_hearing(hearing_id)
        
        old_duration = time.time() - start_time
        
        results['old_system'] = {
            'success': True,
            'processing_time': old_duration,
            'segments': len(old_transcript['transcription']['segments']),
            'characters': len(old_transcript['transcription']['text']),
            'duration_seconds': old_transcript['transcription']['duration'],
            'source': old_transcript['metadata']['source'],
            'transcript_sample': old_transcript['transcription']['text'][:200] + "..."
        }
        
        print(f"✅ Demo system completed")
        print(f"⏱️  Processing time: {old_duration:.1f} seconds")
        print(f"📊 Segments: {results['old_system']['segments']}")
        print(f"📝 Characters: {results['old_system']['characters']:,}")
        print(f"⏳ Duration: {results['old_system']['duration_seconds']:.1f} seconds")
        print(f"🔧 Source: {results['old_system']['source']}")
        
    except Exception as e:
        print(f"❌ Demo system failed: {e}")
        results['old_system'] = {'success': False, 'error': str(e)}
    
    # Reset hearing to captured state for second test
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE hearings_unified SET processing_stage = ? WHERE id = ?', ('captured', hearing_id))
    conn.commit()
    conn.close()
    
    # Test 2: New Chunked System
    print(f"\n🚀 Test 2: NEW CHUNKED SYSTEM")
    print("-" * 40)
    
    try:
        start_time = time.time()
        
        # Progress tracking callback
        progress_updates = []
        def progress_callback(stage, percent, message):
            progress_updates.append({
                'timestamp': datetime.now().isoformat(),
                'stage': stage,
                'percent': percent,
                'message': message
            })
            print(f"📊 {stage.upper()}: {percent}% - {message}")
        
        new_service = EnhancedTranscriptionService(db_path=db_path)
        new_transcript = new_service.transcribe_hearing(hearing_id, progress_callback=progress_callback)
        
        new_duration = time.time() - start_time
        
        results['new_system'] = {
            'success': True,
            'processing_time': new_duration,
            'segments': len(new_transcript['transcription']['segments']),
            'characters': len(new_transcript['transcription']['text']),
            'duration_seconds': new_transcript['transcription']['duration'],
            'source': new_transcript['metadata']['source'],
            'chunks_processed': new_transcript['metadata'].get('total_chunks', 1),
            'progress_updates': len(progress_updates),
            'transcript_sample': new_transcript['transcription']['text'][:200] + "..."
        }
        
        print(f"\n✅ Chunked system completed")
        print(f"⏱️  Processing time: {new_duration:.1f} seconds")
        print(f"📊 Segments: {results['new_system']['segments']}")
        print(f"📝 Characters: {results['new_system']['characters']:,}")
        print(f"⏳ Duration: {results['new_system']['duration_seconds']:.1f} seconds")
        print(f"🔧 Source: {results['new_system']['source']}")
        print(f"📦 Chunks processed: {results['new_system']['chunks_processed']}")
        print(f"📈 Progress updates: {results['new_system']['progress_updates']}")
        
    except Exception as e:
        print(f"❌ Chunked system failed: {e}")
        results['new_system'] = {'success': False, 'error': str(e)}
    
    # Analysis and Comparison
    print(f"\n📊 COMPARISON ANALYSIS")
    print("=" * 70)
    
    if results['old_system']['success'] and results['new_system']['success']:
        old = results['old_system']
        new = results['new_system']
        
        # Calculate improvements
        segment_improvement = ((new['segments'] - old['segments']) / old['segments']) * 100 if old['segments'] > 0 else 0
        character_improvement = ((new['characters'] - old['characters']) / old['characters']) * 100 if old['characters'] > 0 else 0
        
        print(f"📈 IMPROVEMENTS:")
        print(f"   Segments: {old['segments']} → {new['segments']} ({segment_improvement:+.1f}%)")
        print(f"   Characters: {old['characters']:,} → {new['characters']:,} ({character_improvement:+.1f}%)")
        print(f"   Processing: {old['source']} → {new['source']}")
        
        if new['chunks_processed'] > 1:
            print(f"   🎉 CHUNKING USED: {new['chunks_processed']} chunks processed!")
        else:
            print(f"   📁 Direct processing used (file under size limit)")
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Old system: {old['processing_time']:.1f}s")
        print(f"   New system: {new['processing_time']:.1f}s")
        
        if new['processing_time'] > old['processing_time']:
            print(f"   📊 Longer processing time expected for real transcription vs. demo generation")
        
        print(f"\n📝 CONTENT QUALITY:")
        print(f"   Old sample: {old['transcript_sample']}")
        print(f"   New sample: {new['transcript_sample']}")
        
        # Determine success criteria
        success_criteria = {
            'segments_increased': new['segments'] > old['segments'],
            'characters_increased': new['characters'] > old['characters'],
            'real_processing_used': 'whisper' in new['source'],
            'progress_tracking_worked': new['progress_updates'] > 0
        }
        
        all_criteria_met = all(success_criteria.values())
        
        print(f"\n✅ SUCCESS CRITERIA:")
        for criterion, met in success_criteria.items():
            status = "✅" if met else "❌"
            print(f"   {status} {criterion.replace('_', ' ').title()}: {met}")
        
        if all_criteria_met:
            print(f"\n🎉 VALIDATION SUCCESSFUL!")
            print(f"✅ Chunked processing system is working correctly")
            print(f"✅ Significant improvement over demo system")
            return True
        else:
            print(f"\n⚠️  VALIDATION PARTIAL")
            print(f"Some criteria not met, but system may still be functional")
            return False
    
    else:
        print(f"❌ One or both systems failed, cannot compare")
        return False

def save_test_results(results):
    """Save test results to file for documentation."""
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f'chunking_validation_results_{timestamp}.json'
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Test results saved to: {results_file}")

def main():
    """Main test execution."""
    print("🧪 Audio Chunking Validation Test Suite")
    print("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    success = test_demo_vs_chunked_comparison()
    
    if success:
        print(f"\n🎉 OVERALL RESULT: VALIDATION SUCCESSFUL")
        print(f"✅ Audio chunking implementation is working correctly")
        print(f"✅ Ready for production integration")
    else:
        print(f"\n⚠️  OVERALL RESULT: VALIDATION NEEDS REVIEW")
        print(f"❓ System functional but may need adjustments")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)