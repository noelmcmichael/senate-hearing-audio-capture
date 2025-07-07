#!/usr/bin/env python3
"""
Direct test of the transcription service to identify the async issue.
"""

import sys
import traceback
from pathlib import Path

def test_transcription_service():
    """Test the transcription service directly."""
    try:
        from transcription_service import EnhancedTranscriptionService
        
        # Initialize the service
        service = EnhancedTranscriptionService()
        print("✅ Transcription service initialized successfully")
        
        # Test finding an audio file for hearing 13
        try:
            audio_file = service._find_audio_file(13)
            print(f"Audio file search result: {audio_file}")
        except Exception as e:
            print(f"Audio file search error: {e}")
        
        # Test transcription
        print("🚀 Attempting transcription for hearing 13...")
        result = service.transcribe_hearing(13)
        print(f"✅ Transcription completed: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    test_transcription_service()