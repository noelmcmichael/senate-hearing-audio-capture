#!/usr/bin/env python3
"""
Quick script to verify the extracted audio file.
"""

import subprocess
from pathlib import Path

def verify_audio_file(file_path: Path):
    """Verify audio file using ffmpeg."""
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        # Use ffprobe to get detailed information
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(file_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ ffprobe failed: {result.stderr}")
            return False
        
        import json
        info = json.loads(result.stdout)
        
        # Extract key information
        format_info = info.get('format', {})
        streams = info.get('streams', [])
        
        print(f"✅ Audio file verified: {file_path.name}")
        print(f"   Format: {format_info.get('format_name', 'unknown')}")
        print(f"   Duration: {float(format_info.get('duration', 0)):.1f} seconds")
        print(f"   Size: {int(format_info.get('size', 0)) / 1024 / 1024:.1f} MB")
        
        if streams:
            audio_stream = streams[0]
            print(f"   Sample Rate: {audio_stream.get('sample_rate', 'unknown')}")
            print(f"   Channels: {audio_stream.get('channels', 'unknown')}")
            print(f"   Codec: {audio_stream.get('codec_name', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying file: {e}")
        return False

def main():
    output_dir = Path('output')
    
    # Find audio files
    audio_files = list(output_dir.glob('*.wav')) + list(output_dir.glob('*.mp3'))
    
    if not audio_files:
        print("No audio files found in output directory")
        return
    
    print(f"Found {len(audio_files)} audio file(s):")
    
    for audio_file in sorted(audio_files):
        print(f"\n🎵 Verifying: {audio_file.name}")
        verify_audio_file(audio_file)

if __name__ == "__main__":
    main()