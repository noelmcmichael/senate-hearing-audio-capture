#!/usr/bin/env python3
"""
Audio file analyzer for Senate hearing audio processing.
Analyzes audio files for size, duration, format, and chunking requirements.
"""

import os
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any
import json

@dataclass
class AudioAnalysis:
    """Container for audio file analysis results."""
    file_path: Path
    file_size_bytes: int
    file_size_mb: float
    duration_seconds: float
    duration_minutes: float
    format: str
    sample_rate: int
    channels: int
    bitrate: int
    needs_chunking: bool
    max_chunk_size_mb: float = 20.0  # 5MB buffer under 25MB API limit
    estimated_chunks: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'file_path': str(self.file_path),
            'file_size_bytes': self.file_size_bytes,
            'file_size_mb': round(self.file_size_mb, 2),
            'duration_seconds': round(self.duration_seconds, 2),
            'duration_minutes': round(self.duration_minutes, 2),
            'format': self.format,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'bitrate': self.bitrate,
            'needs_chunking': self.needs_chunking,
            'max_chunk_size_mb': self.max_chunk_size_mb,
            'estimated_chunks': self.estimated_chunks
        }

class AudioAnalyzer:
    """Analyzer for audio file properties and chunking requirements."""
    
    def __init__(self):
        """Initialize the audio analyzer."""
        self.max_size_mb = 20.0  # Safe limit under OpenAI's 25MB
        self.max_size_bytes = int(self.max_size_mb * 1024 * 1024)
        
    def analyze_file(self, file_path: Path) -> AudioAnalysis:
        """Analyze an audio file and determine processing requirements."""
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Get basic file info
        file_size_bytes = file_path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # Get audio metadata using ffprobe
        audio_info = self._get_audio_metadata(file_path)
        
        # Determine if chunking is needed
        needs_chunking = file_size_mb > self.max_size_mb
        
        # Estimate number of chunks needed
        estimated_chunks = 0
        if needs_chunking:
            estimated_chunks = max(1, int(file_size_mb / self.max_size_mb) + 1)
        
        return AudioAnalysis(
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            file_size_mb=file_size_mb,
            duration_seconds=audio_info.get('duration', 0.0),
            duration_minutes=audio_info.get('duration', 0.0) / 60.0,
            format=audio_info.get('format', 'unknown'),
            sample_rate=audio_info.get('sample_rate', 0),
            channels=audio_info.get('channels', 0),
            bitrate=audio_info.get('bitrate', 0),
            needs_chunking=needs_chunking,
            max_chunk_size_mb=self.max_size_mb,
            estimated_chunks=estimated_chunks
        )
    
    def _get_audio_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract audio metadata using ffprobe."""
        try:
            # Use ffprobe to get audio metadata
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            probe_data = json.loads(result.stdout)
            
            # Extract relevant information
            format_info = probe_data.get('format', {})
            audio_stream = None
            
            # Find the first audio stream
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise ValueError("No audio stream found in file")
            
            return {
                'duration': float(format_info.get('duration', 0)),
                'format': format_info.get('format_name', 'unknown'),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'bitrate': int(format_info.get('bit_rate', 0))
            }
            
        except subprocess.CalledProcessError as e:
            print(f"Warning: ffprobe failed for {file_path}: {e}")
            # Fallback to basic analysis
            return self._basic_audio_analysis(file_path)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Warning: Error parsing ffprobe output for {file_path}: {e}")
            return self._basic_audio_analysis(file_path)
    
    def _basic_audio_analysis(self, file_path: Path) -> Dict[str, Any]:
        """Basic audio analysis when ffprobe is not available."""
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        # Rough estimates based on common audio formats
        estimated_duration = 0.0
        
        if file_path.suffix.lower() == '.mp3':
            # Rough estimate: 1MB = ~1 minute for typical MP3
            estimated_duration = file_size_mb * 60
        elif file_path.suffix.lower() in ['.wav', '.flac']:
            # Uncompressed audio: ~10MB per minute
            estimated_duration = file_size_mb * 6
        else:
            # Conservative estimate
            estimated_duration = file_size_mb * 30
        
        return {
            'duration': estimated_duration,
            'format': file_path.suffix.lower().replace('.', ''),
            'sample_rate': 44100,  # Common default
            'channels': 2,  # Stereo default
            'bitrate': 128000  # Common MP3 bitrate
        }
    
    def check_ffmpeg_available(self) -> bool:
        """Check if ffmpeg tools are available on the system."""
        try:
            subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def analyze_for_chunking(self, file_path: Path) -> Dict[str, Any]:
        """Analyze file specifically for chunking requirements."""
        analysis = self.analyze_file(file_path)
        
        chunking_info = {
            'needs_chunking': analysis.needs_chunking,
            'file_size_mb': analysis.file_size_mb,
            'max_chunk_size_mb': analysis.max_chunk_size_mb,
            'estimated_chunks': analysis.estimated_chunks,
            'duration_minutes': analysis.duration_minutes,
            'chunk_duration_estimate': 0.0,
            'overlap_duration': 30.0,  # 30 seconds overlap
            'processing_estimate_minutes': 0.0
        }
        
        if analysis.needs_chunking:
            # Estimate chunk duration and processing time
            chunk_duration = analysis.duration_minutes / analysis.estimated_chunks
            processing_time = analysis.estimated_chunks * 2.0  # 2 min per chunk estimate
            
            chunking_info.update({
                'chunk_duration_estimate': round(chunk_duration, 2),
                'processing_estimate_minutes': round(processing_time, 2)
            })
        
        return chunking_info

def main():
    """Test the audio analyzer with the real captured audio file."""
    analyzer = AudioAnalyzer()
    
    # Test with the real captured audio file
    audio_file = Path(__file__).parent / 'output' / 'real_audio' / 'senate_hearing_20250705_225321_stream1.mp3'
    
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return False
    
    print(f"🔍 Analyzing audio file: {audio_file.name}")
    print(f"📍 Path: {audio_file}")
    
    try:
        # Check if ffmpeg is available
        ffmpeg_available = analyzer.check_ffmpeg_available()
        print(f"🛠️  FFmpeg available: {'✅' if ffmpeg_available else '❌'}")
        
        # Analyze the file
        analysis = analyzer.analyze_file(audio_file)
        
        print("\n📊 Audio Analysis Results:")
        print(f"📁 File size: {analysis.file_size_mb:.2f} MB ({analysis.file_size_bytes:,} bytes)")
        print(f"⏱️  Duration: {analysis.duration_minutes:.2f} minutes ({analysis.duration_seconds:.2f} seconds)")
        print(f"🎵 Format: {analysis.format}")
        print(f"📡 Sample rate: {analysis.sample_rate:,} Hz")
        print(f"🔊 Channels: {analysis.channels}")
        print(f"📈 Bitrate: {analysis.bitrate:,} bps")
        
        print(f"\n🔧 Chunking Analysis:")
        print(f"📏 Max chunk size: {analysis.max_chunk_size_mb} MB")
        print(f"🧮 Needs chunking: {'✅ YES' if analysis.needs_chunking else '❌ NO'}")
        if analysis.needs_chunking:
            print(f"📦 Estimated chunks: {analysis.estimated_chunks}")
            
            # Get detailed chunking info
            chunking_info = analyzer.analyze_for_chunking(audio_file)
            print(f"⏱️  Chunk duration estimate: {chunking_info['chunk_duration_estimate']:.2f} minutes each")
            print(f"🔗 Overlap duration: {chunking_info['overlap_duration']:.0f} seconds")
            print(f"⏳ Processing time estimate: {chunking_info['processing_estimate_minutes']:.1f} minutes")
        
        print(f"\n✅ Audio analysis completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Audio analysis failed: {e}")
        return False

if __name__ == "__main__":
    main()