"""
Hybrid Audio Converter - Supports both ISVP and YouTube streams

Handles conversion from multiple stream types with platform-specific optimizations.
"""

import os
import sys
import subprocess
import shutil
import tempfile
import yt_dlp
from pathlib import Path
from typing import Optional, Dict, List, Union
from dataclasses import dataclass
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.base_extractor import StreamInfo
from converters.ffmpeg_converter import FFmpegConverter, ConversionResult


class HybridConverter:
    """Enhanced converter supporting ISVP, YouTube, and other stream types."""
    
    def __init__(self, 
                 output_format: str = 'mp3',
                 audio_quality: str = 'medium',
                 ffmpeg_path: Optional[str] = None):
        """Initialize hybrid converter.
        
        Args:
            output_format: Output format ('mp3', 'wav', 'flac')
            audio_quality: Quality setting ('low', 'medium', 'high')
            ffmpeg_path: Path to ffmpeg executable
        """
        self.output_format = output_format
        self.audio_quality = audio_quality
        self.ffmpeg_path = ffmpeg_path or self._find_ffmpeg()
        
        # Initialize FFmpeg converter for ISVP streams
        self.ffmpeg_converter = FFmpegConverter(
            ffmpeg_path=self.ffmpeg_path,
            output_format=output_format,
            audio_quality=audio_quality
        )
        
        # YouTube-dl options for YouTube streams
        self.yt_dlp_opts = self._get_yt_dlp_options()
        
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
    
    def convert_stream(self, 
                      stream: StreamInfo, 
                      output_path: Path,
                      headers: Optional[Dict[str, str]] = None,
                      duration_limit: Optional[int] = None) -> ConversionResult:
        """
        Convert a stream to audio file using the appropriate method.
        
        Args:
            stream: Stream information
            output_path: Output file path
            headers: HTTP headers for requests
            duration_limit: Maximum duration in seconds
            
        Returns:
            ConversionResult with success status and metadata
        """
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Route to appropriate converter based on stream type
        if stream.format_type == 'youtube':
            return self._convert_youtube_stream(stream, output_path, duration_limit)
        elif stream.format_type == 'hls':
            return self._convert_hls_stream(stream, output_path, headers, duration_limit)
        else:
            # Fallback to FFmpeg converter
            return self.ffmpeg_converter.convert_stream(stream, output_path, headers)
    
    def _convert_youtube_stream(self, 
                               stream: StreamInfo, 
                               output_path: Path,
                               duration_limit: Optional[int] = None) -> ConversionResult:
        """Convert YouTube stream using yt-dlp."""
        try:
            # Get YouTube URL from metadata or use stream URL
            youtube_url = stream.metadata.get('youtube_url', stream.metadata.get('original_page'))
            if not youtube_url:
                return ConversionResult(
                    success=False,
                    error_message="No YouTube URL found in stream metadata"
                )
            
            print(f"🎵 Converting YouTube stream: {stream.title}")
            print(f"   URL: {youtube_url}")
            
            # Prepare yt-dlp options
            ydl_opts = self.yt_dlp_opts.copy()
            ydl_opts['outtmpl'] = str(output_path.with_suffix(''))  # yt-dlp will add extension
            
            # Add duration limit if specified
            if duration_limit:
                ydl_opts['external_downloader_args'] = {
                    'ffmpeg': ['-t', str(duration_limit)]
                }
            
            # Download and convert
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                
                if not info:
                    return ConversionResult(
                        success=False,
                        error_message="Failed to extract YouTube video info"
                    )
                
                # Find the actual output file (yt-dlp adds extension)
                actual_output_path = None
                for ext in ['.mp3', '.wav', '.m4a', '.opus']:
                    potential_path = output_path.with_suffix(ext)
                    if potential_path.exists():
                        actual_output_path = potential_path
                        break
                
                if not actual_output_path or not actual_output_path.exists():
                    return ConversionResult(
                        success=False,
                        error_message="Output file not found after YouTube download"
                    )
                
                # Rename to desired output path if needed
                if actual_output_path != output_path:
                    shutil.move(str(actual_output_path), str(output_path))
                
                # Get file stats
                file_size = output_path.stat().st_size
                duration = info.get('duration', 0)
                
                return ConversionResult(
                    success=True,
                    output_path=output_path,
                    duration_seconds=duration,
                    file_size_bytes=file_size,
                    metadata={
                        'source': 'youtube',
                        'title': info.get('title', stream.title),
                        'uploader': info.get('uploader', ''),
                        'video_id': info.get('id', ''),
                        'format': self.output_format,
                        'quality': self.audio_quality
                    }
                )
                
        except Exception as e:
            return ConversionResult(
                success=False,
                error_message=f"YouTube conversion failed: {str(e)}"
            )
    
    def _convert_hls_stream(self, 
                           stream: StreamInfo, 
                           output_path: Path,
                           headers: Optional[Dict[str, str]] = None,
                           duration_limit: Optional[int] = None) -> ConversionResult:
        """Convert HLS stream using FFmpeg with enhanced options."""
        try:
            print(f"🎵 Converting HLS stream: {stream.title}")
            print(f"   URL: {stream.url}")
            
            # Build FFmpeg command
            cmd = [self.ffmpeg_path]
            
            # Add headers if provided
            if headers:
                header_string = '\r\n'.join([f"{k}: {v}" for k, v in headers.items()])
                cmd.extend(['-headers', header_string])
            
            # Add referer header for Senate streams
            if stream.metadata.get('referer'):
                cmd.extend(['-referer', stream.metadata['referer']])
            
            # Add User-Agent
            cmd.extend(['-user_agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'])
            
            # Input
            cmd.extend(['-i', stream.url])
            
            # Duration limit
            if duration_limit:
                cmd.extend(['-t', str(duration_limit)])
            
            # Audio processing options
            cmd.extend(self._get_audio_processing_options())
            
            # Output
            cmd.extend(['-y', str(output_path)])  # -y to overwrite
            
            print(f"   🔧 Running FFmpeg conversion...")
            
            # Run conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration_limit + 60 if duration_limit else 3600  # 1 hour default timeout
            )
            
            if result.returncode != 0:
                return ConversionResult(
                    success=False,
                    error_message=f"FFmpeg failed: {result.stderr}"
                )
            
            if not output_path.exists():
                return ConversionResult(
                    success=False,
                    error_message="Output file was not created"
                )
            
            # Get file stats
            file_size = output_path.stat().st_size
            duration = self._extract_duration_from_ffmpeg_output(result.stderr)
            
            return ConversionResult(
                success=True,
                output_path=output_path,
                duration_seconds=duration,
                file_size_bytes=file_size,
                metadata={
                    'source': 'hls',
                    'title': stream.title,
                    'committee': stream.metadata.get('committee'),
                    'format': self.output_format,
                    'quality': self.audio_quality
                }
            )
            
        except subprocess.TimeoutExpired:
            return ConversionResult(
                success=False,
                error_message="Conversion timed out"
            )
        except Exception as e:
            return ConversionResult(
                success=False,
                error_message=f"HLS conversion failed: {str(e)}"
            )
    
    def _get_yt_dlp_options(self) -> Dict:
        """Get yt-dlp options based on output format and quality."""
        # Quality settings
        quality_settings = {
            'low': 'worst[height<=480]/worst',
            'medium': 'best[height<=720]/best',
            'high': 'best/best'
        }
        
        # Format settings for audio extraction
        if self.output_format == 'mp3':
            audio_format = 'mp3'
            audio_quality = '128K' if self.audio_quality == 'low' else '192K' if self.audio_quality == 'medium' else '320K'
        elif self.output_format == 'wav':
            audio_format = 'wav'
            audio_quality = None
        else:
            audio_format = 'best'
            audio_quality = None
        
        opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': audio_format,
            'noplaylist': True,
            'writeinfojson': False,
            'writeautomaticsub': False,
            'writesubtitles': False,
        }
        
        if audio_quality:
            opts['audioquality'] = audio_quality
        
        return opts
    
    def _get_audio_processing_options(self) -> List[str]:
        """Get FFmpeg audio processing options based on format and quality."""
        options = []
        
        if self.output_format == 'mp3':
            options.extend(['-acodec', 'libmp3lame'])
            
            # Quality settings for MP3
            if self.audio_quality == 'low':
                options.extend(['-ab', '128k'])
            elif self.audio_quality == 'medium':
                options.extend(['-ab', '192k'])
            else:  # high
                options.extend(['-ab', '320k'])
                
        elif self.output_format == 'wav':
            options.extend(['-acodec', 'pcm_s16le'])
            
        elif self.output_format == 'flac':
            options.extend(['-acodec', 'flac'])
        
        # Common audio settings
        options.extend([
            '-ar', '48000',  # Sample rate
            '-ac', '2'       # Stereo
        ])
        
        return options
    
    def _extract_duration_from_ffmpeg_output(self, stderr: str) -> Optional[float]:
        """Extract duration from FFmpeg stderr output."""
        import re
        
        # Look for duration in format "Duration: HH:MM:SS.ss"
        duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', stderr)
        if duration_match:
            hours, minutes, seconds, centiseconds = map(int, duration_match.groups())
            return hours * 3600 + minutes * 60 + seconds + centiseconds / 100
        
        return None
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable."""
        return shutil.which('ffmpeg')
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        return ['mp3', 'wav', 'flac', 'm4a']
    
    def test_conversion_capabilities(self) -> Dict[str, bool]:
        """Test conversion capabilities."""
        capabilities = {
            'ffmpeg_available': bool(self.ffmpeg_path),
            'yt_dlp_available': True,  # Always true if imported successfully
            'youtube_support': True,
            'hls_support': bool(self.ffmpeg_path)
        }
        
        return capabilities