"""FFmpeg-based audio converter for extracting audio from streams."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
import tempfile
import logging

from extractors.base_extractor import StreamInfo


@dataclass
class ConversionResult:
    """Result of an audio conversion operation."""
    success: bool
    output_path: Optional[Path] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None


class FFmpegConverter:
    """Converts streams to audio files using FFmpeg."""
    
    def __init__(self, 
                 ffmpeg_path: Optional[str] = None,
                 output_format: str = 'wav',
                 audio_quality: str = 'high'):
        """Initialize the converter.
        
        Args:
            ffmpeg_path: Path to ffmpeg executable (None for auto-detect)
            output_format: Output audio format ('wav', 'mp3', 'flac')
            audio_quality: Quality setting ('low', 'medium', 'high')
        """
        self.ffmpeg_path = ffmpeg_path or self._find_ffmpeg()
        self.output_format = output_format
        self.audio_quality = audio_quality
        
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
    
    def convert_stream(self, 
                      stream: StreamInfo, 
                      output_path: Path,
                      headers: Optional[Dict[str, str]] = None) -> ConversionResult:
        """Convert a stream to audio file.
        
        Args:
            stream: Stream information
            output_path: Where to save the audio file
            headers: Additional HTTP headers for the request
            
        Returns:
            Conversion result
        """
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(stream, output_path, headers)
            
            # Run conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            if result.returncode != 0:
                return ConversionResult(
                    success=False,
                    error_message=f"FFmpeg failed: {result.stderr}"
                )
            
            # Verify output file was created
            if not output_path.exists():
                return ConversionResult(
                    success=False,
                    error_message="Output file was not created"
                )
            
            # Get file info
            file_size = output_path.stat().st_size
            duration = self._get_audio_duration(output_path)
            
            return ConversionResult(
                success=True,
                output_path=output_path,
                duration_seconds=duration,
                file_size_bytes=file_size,
                metadata={
                    'original_stream': stream.url,
                    'format': self.output_format,
                    'quality': self.audio_quality
                }
            )
            
        except subprocess.TimeoutExpired:
            return ConversionResult(
                success=False,
                error_message="Conversion timed out (30 minutes)"
            )
        except Exception as e:
            return ConversionResult(
                success=False,
                error_message=str(e)
            )
    
    def _build_ffmpeg_command(self, 
                             stream: StreamInfo, 
                             output_path: Path,
                             headers: Optional[Dict[str, str]] = None) -> List[str]:
        """Build the FFmpeg command for conversion."""
        cmd = [self.ffmpeg_path]
        
        # Input handling
        if stream.format_type == 'hls':
            # HLS stream specific options
            cmd.extend([
                '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',
                '-i', stream.url
            ])
        else:
            # Generic stream handling
            cmd.extend(['-i', stream.url])
        
        # Audio extraction options
        cmd.extend([
            '-vn',  # No video
            '-acodec', self._get_audio_codec(),
        ])
        
        # Quality settings
        if self.output_format == 'wav':
            cmd.extend(['-ar', '44100', '-ac', '2'])  # 44.1kHz stereo
            if self.audio_quality == 'high':
                cmd.extend(['-sample_fmt', 's16'])
        elif self.output_format == 'mp3':
            if self.audio_quality == 'high':
                cmd.extend(['-b:a', '320k'])
            elif self.audio_quality == 'medium':
                cmd.extend(['-b:a', '192k'])
            else:
                cmd.extend(['-b:a', '128k'])
        
        # Headers if provided
        if headers:
            header_string = '\\r\\n'.join([f'{k}: {v}' for k, v in headers.items()])
            cmd.extend(['-headers', header_string])
        
        # Referer for authentication
        if stream.metadata and 'referer' in stream.metadata:
            cmd.extend(['-referer', stream.metadata['referer']])
        
        # User agent
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 SenateHearingBot/1.0"
        if stream.metadata and 'user_agent' in stream.metadata:
            user_agent = stream.metadata['user_agent']
        cmd.extend(['-user_agent', user_agent])
        
        # Output options
        cmd.extend([
            '-y',  # Overwrite output file
            str(output_path)
        ])
        
        return cmd
    
    def _get_audio_codec(self) -> str:
        """Get the appropriate audio codec for the output format."""
        codecs = {
            'wav': 'pcm_s16le',
            'mp3': 'libmp3lame',
            'flac': 'flac',
            'aac': 'aac'
        }
        return codecs.get(self.output_format, 'pcm_s16le')
    
    def _get_audio_duration(self, file_path: Path) -> Optional[float]:
        """Get the duration of an audio file in seconds."""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', str(file_path),
                '-f', 'null',
                '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Parse duration from stderr
            import re
            duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', result.stderr)
            if duration_match:
                hours, minutes, seconds = duration_match.groups()
                total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                return total_seconds
            
            return None
            
        except Exception:
            return None
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable in system PATH."""
        # Try common locations
        possible_paths = [
            'ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg',
            '/usr/bin/ffmpeg'
        ]
        
        for path in possible_paths:
            if shutil.which(path):
                return path
        
        return None
    
    def get_info(self) -> Dict:
        """Get information about the converter setup."""
        return {
            'ffmpeg_path': self.ffmpeg_path,
            'output_format': self.output_format,
            'audio_quality': self.audio_quality,
            'available': self.ffmpeg_path is not None
        }