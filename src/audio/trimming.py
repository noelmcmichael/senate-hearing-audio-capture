"""
Audio Trimming Module for Milestone 5.2
Implements silence detection and trimming for improved transcription quality
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Tuple, Optional, Any
import json
import wave
import numpy as np

logger = logging.getLogger(__name__)

class AudioTrimmer:
    """Audio trimming with silence detection for congressional hearings"""
    
    def __init__(self):
        """Initialize audio trimmer"""
        self.temp_dir = Path(tempfile.gettempdir()) / "senate_audio_trimming"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Default trimming parameters optimized for congressional hearings
        self.default_params = {
            "silence_threshold": "-30dB",  # Threshold for silence detection
            "min_silence_duration": "2.0",  # Minimum silence duration to detect (seconds)
            "silence_removal_threshold": "0.5",  # Threshold for silence removal
            "max_trim_start": 300,  # Maximum seconds to trim from start
            "fade_in_duration": "0.1",  # Fade in duration to avoid clicks
            "fade_out_duration": "0.1"  # Fade out duration to avoid clicks
        }
    
    def detect_silence_boundaries(self, audio_path: Path, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detect silence boundaries in audio file
        
        Args:
            audio_path: Path to audio file
            params: Optional parameters for silence detection
            
        Returns:
            Dictionary with silence analysis results
        """
        try:
            if params is None:
                params = self.default_params
            
            logger.info(f"Analyzing silence in audio file: {audio_path}")
            
            # Use FFmpeg to detect silence
            cmd = [
                "ffmpeg", "-y",
                "-i", str(audio_path),
                "-af", f"silencedetect=noise={params['silence_threshold']}:d={params['min_silence_duration']}",
                "-f", "null",
                "-"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg silence detection failed: {result.stderr}")
            
            # Parse silence detection output
            silence_info = self._parse_silence_output(result.stderr)
            
            # Get audio duration
            duration = self._get_audio_duration(audio_path)
            
            analysis_result = {
                "audio_path": str(audio_path),
                "duration": duration,
                "silence_segments": silence_info["silence_segments"],
                "silence_count": len(silence_info["silence_segments"]),
                "total_silence_duration": silence_info["total_silence"],
                "recommended_trim_start": self._calculate_recommended_trim_start(silence_info, duration),
                "quality_score": self._calculate_quality_score(silence_info, duration)
            }
            
            logger.info(f"Silence analysis complete: {analysis_result['silence_count']} segments, "
                       f"{analysis_result['total_silence_duration']:.1f}s total silence")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Silence detection failed for {audio_path}: {e}")
            raise
    
    def trim_audio(self, audio_path: Path, output_path: Optional[Path] = None, 
                   trim_start: Optional[float] = None, trim_end: Optional[float] = None,
                   params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Trim audio file to remove silence from start and optionally end
        
        Args:
            audio_path: Path to input audio file
            output_path: Path for output file (optional)
            trim_start: Seconds to trim from start (optional, auto-detect if None)
            trim_end: Seconds to trim from end (optional)
            params: Optional trimming parameters
            
        Returns:
            Dictionary with trimming results
        """
        try:
            if params is None:
                params = self.default_params
            
            if output_path is None:
                output_path = audio_path.parent / f"{audio_path.stem}_trimmed{audio_path.suffix}"
            
            logger.info(f"Trimming audio: {audio_path} -> {output_path}")
            
            # Auto-detect trim points if not provided
            if trim_start is None:
                silence_analysis = self.detect_silence_boundaries(audio_path, params)
                trim_start = silence_analysis["recommended_trim_start"]
                logger.info(f"Auto-detected trim start: {trim_start:.2f} seconds")
            
            original_duration = self._get_audio_duration(audio_path)
            
            # Build FFmpeg command
            cmd = ["ffmpeg", "-i", str(audio_path)]
            
            # Add filters
            filters = []
            
            # Trim filter
            if trim_start > 0 or trim_end:
                trim_filter = f"atrim=start={trim_start}"
                if trim_end:
                    trim_filter += f":end={original_duration - trim_end}"
                filters.append(trim_filter)
            
            # Add fade in/out to avoid clicks
            if float(params["fade_in_duration"]) > 0:
                filters.append(f"afade=t=in:d={params['fade_in_duration']}")
            
            if float(params["fade_out_duration"]) > 0:
                # Calculate fade out start time (relative to trimmed audio)
                trimmed_duration = original_duration - trim_start
                if trim_end:
                    trimmed_duration -= trim_end
                fade_start = max(0, trimmed_duration - float(params["fade_out_duration"]))
                filters.append(f"afade=t=out:st={fade_start}:d={params['fade_out_duration']}")
            
            # Apply filters if any
            if filters:
                cmd.extend(["-af", ",".join(filters)])
            
            # Output settings
            cmd.extend([
                "-c:a", "libmp3lame",  # MP3 codec
                "-b:a", "128k",        # Bitrate
                "-y",                  # Overwrite output
                str(output_path)
            ])
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg trimming failed: {result.stderr}")
            
            # Get output file info
            new_duration = self._get_audio_duration(output_path)
            trimmed_seconds = original_duration - new_duration
            
            trim_result = {
                "input_path": str(audio_path),
                "output_path": str(output_path),
                "original_duration": original_duration,
                "new_duration": new_duration,
                "trimmed_seconds": trimmed_seconds,
                "trim_start": trim_start,
                "trim_end": trim_end or 0,
                "quality_improvement": self._calculate_quality_improvement(trimmed_seconds, original_duration),
                "file_size_reduction": self._calculate_file_size_reduction(audio_path, output_path)
            }
            
            logger.info(f"Audio trimmed successfully: {trimmed_seconds:.1f}s removed, "
                       f"{trim_result['quality_improvement']:.1f}% quality improvement")
            
            return trim_result
            
        except Exception as e:
            logger.error(f"Audio trimming failed for {audio_path}: {e}")
            raise
    
    def smart_trim(self, audio_path: Path, output_path: Optional[Path] = None,
                   params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Smart trimming with automatic silence detection and optimization
        
        Args:
            audio_path: Path to input audio file
            output_path: Path for output file (optional)
            params: Optional parameters
            
        Returns:
            Dictionary with complete trimming analysis and results
        """
        try:
            if params is None:
                params = self.default_params
            
            logger.info(f"Starting smart trim for: {audio_path}")
            
            # Step 1: Analyze silence
            silence_analysis = self.detect_silence_boundaries(audio_path, params)
            
            # Step 2: Determine optimal trim points
            trim_start = silence_analysis["recommended_trim_start"]
            
            # Step 3: Trim audio
            trim_result = self.trim_audio(audio_path, output_path, trim_start=trim_start, params=params)
            
            # Step 4: Combine results
            smart_trim_result = {
                "analysis": silence_analysis,
                "trimming": trim_result,
                "optimization": {
                    "content_improvement": trim_result["quality_improvement"],
                    "file_size_reduction": trim_result["file_size_reduction"],
                    "processing_time_reduction": self._estimate_processing_time_reduction(trim_result["trimmed_seconds"]),
                    "transcription_quality_improvement": self._estimate_transcription_quality_improvement(silence_analysis)
                }
            }
            
            logger.info(f"Smart trim complete: {trim_result['trimmed_seconds']:.1f}s removed, "
                       f"{smart_trim_result['optimization']['content_improvement']:.1f}% improvement")
            
            return smart_trim_result
            
        except Exception as e:
            logger.error(f"Smart trim failed for {audio_path}: {e}")
            raise
    
    def _parse_silence_output(self, ffmpeg_output: str) -> Dict[str, Any]:
        """Parse FFmpeg silence detection output"""
        silence_segments = []
        total_silence = 0.0
        
        lines = ffmpeg_output.split('\n')
        current_silence = {}
        
        for line in lines:
            if "silence_start:" in line:
                try:
                    start_time = float(line.split("silence_start:")[1].strip())
                    current_silence = {"start": start_time}
                except (ValueError, IndexError):
                    continue
            
            elif "silence_end:" in line and current_silence:
                try:
                    parts = line.split("|")
                    end_time = float(parts[0].split("silence_end:")[1].strip())
                    duration = float(parts[1].split("silence_duration:")[1].strip())
                    
                    current_silence.update({
                        "end": end_time,
                        "duration": duration
                    })
                    
                    silence_segments.append(current_silence)
                    total_silence += duration
                    current_silence = {}
                    
                except (ValueError, IndexError):
                    continue
        
        return {
            "silence_segments": silence_segments,
            "total_silence": total_silence
        }
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio file duration using FFprobe"""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                raise RuntimeError(f"FFprobe failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Failed to get duration for {audio_path}: {e}")
            return 0.0
    
    def _calculate_recommended_trim_start(self, silence_info: Dict[str, Any], duration: float) -> float:
        """Calculate recommended trim start point"""
        silence_segments = silence_info["silence_segments"]
        
        if not silence_segments:
            return 0.0
        
        # Find the first significant content after initial silence
        for segment in silence_segments:
            # If there's silence at the very beginning lasting more than 10 seconds
            if segment["start"] < 5.0 and segment["duration"] > 10.0:
                # Trim to just before the silence ends
                return max(0.0, segment["end"] - 1.0)
        
        # If there's early silence lasting more than 5 seconds
        for segment in silence_segments[:3]:  # Check first 3 segments
            if segment["start"] < 30.0 and segment["duration"] > 5.0:
                return max(0.0, segment["end"] - 0.5)
        
        return 0.0
    
    def _calculate_quality_score(self, silence_info: Dict[str, Any], duration: float) -> float:
        """Calculate audio quality score based on silence analysis"""
        if duration == 0:
            return 0.0
        
        silence_ratio = silence_info["total_silence"] / duration
        content_ratio = 1.0 - silence_ratio
        
        # Quality score from 0-100
        quality_score = content_ratio * 100
        
        # Adjust for number of silence segments (more segments = lower quality)
        segment_penalty = min(10, len(silence_info["silence_segments"]) * 0.5)
        quality_score = max(0, quality_score - segment_penalty)
        
        return quality_score
    
    def _calculate_quality_improvement(self, trimmed_seconds: float, original_duration: float) -> float:
        """Calculate quality improvement percentage"""
        if original_duration == 0:
            return 0.0
        return (trimmed_seconds / original_duration) * 100
    
    def _calculate_file_size_reduction(self, input_path: Path, output_path: Path) -> float:
        """Calculate file size reduction percentage"""
        try:
            input_size = input_path.stat().st_size
            output_size = output_path.stat().st_size
            
            if input_size == 0:
                return 0.0
            
            return ((input_size - output_size) / input_size) * 100
            
        except Exception:
            return 0.0
    
    def _estimate_processing_time_reduction(self, trimmed_seconds: float) -> float:
        """Estimate processing time reduction for transcription"""
        # Assume roughly 1:1 ratio for transcription processing
        return trimmed_seconds
    
    def _estimate_transcription_quality_improvement(self, silence_analysis: Dict[str, Any]) -> float:
        """Estimate transcription quality improvement"""
        # More silence removed = better transcription quality
        silence_count = len(silence_analysis["silence_segments"])
        total_silence = silence_analysis["total_silence"]
        
        # Quality improvement estimate (0-30%)
        improvement = min(30, (silence_count * 2) + (total_silence * 0.1))
        return improvement

# Global trimmer instance
_audio_trimmer = None

def get_audio_trimmer() -> AudioTrimmer:
    """Get audio trimmer singleton"""
    global _audio_trimmer
    if _audio_trimmer is None:
        _audio_trimmer = AudioTrimmer()
    return _audio_trimmer