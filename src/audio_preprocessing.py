#!/usr/bin/env python3
"""
Audio Preprocessing Pipeline for Congressional Hearings

Automatically detects speech activity and clips audio to remove
pre-session silence/setup periods before Whisper transcription.
"""

import sys
import logging
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List, Dict
import subprocess
import json
from datetime import datetime


class AudioPreprocessor:
    """
    Smart audio preprocessing for congressional hearings.
    
    Detects sustained speech activity and clips audio to remove
    pre-session periods, optimizing for Whisper transcription.
    """
    
    def __init__(self, 
                 min_speech_duration: float = 60.0,
                 speech_threshold: float = 0.02,
                 segment_duration: float = 30.0):
        """
        Initialize audio preprocessor.
        
        Args:
            min_speech_duration: Minimum sustained speech to consider hearing start (seconds)
            speech_threshold: RMS threshold for speech detection
            segment_duration: Duration of analysis segments (seconds)
        """
        self.min_speech_duration = min_speech_duration
        self.speech_threshold = speech_threshold
        self.segment_duration = segment_duration
        self.logger = logging.getLogger(__name__)
        
    def analyze_speech_activity(self, audio_file: Path) -> Dict:
        """
        Analyze audio file for speech activity patterns.
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Dict with speech activity analysis
        """
        self.logger.info(f"🔍 Analyzing speech activity: {audio_file.name}")
        
        # Get audio metadata first
        metadata = self._get_audio_metadata(audio_file)
        if not metadata:
            return {"error": "Could not read audio metadata"}
            
        duration = float(metadata.get('duration', 0))
        self.logger.info(f"   Audio duration: {duration/60:.1f} minutes")
        
        # Analyze audio in segments
        segments = []
        current_time = 0.0
        
        while current_time < duration:
            segment_end = min(current_time + self.segment_duration, duration)
            
            # Extract segment for analysis
            segment_info = self._analyze_segment(
                audio_file, current_time, segment_end
            )
            
            if segment_info:
                segments.append(segment_info)
                
            current_time += self.segment_duration
            
        self.logger.info(f"   Analyzed {len(segments)} segments")
        
        # Find content start
        content_start = self._find_content_start(segments)
        
        return {
            "audio_file": str(audio_file),
            "total_duration": float(duration),
            "segments_analyzed": int(len(segments)),
            "content_start_time": float(content_start) if content_start is not None else None,
            "segments": segments,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _get_audio_metadata(self, audio_file: Path) -> Optional[Dict]:
        """Get audio file metadata using ffprobe."""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', str(audio_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return json.loads(result.stdout).get('format', {})
            else:
                self.logger.error(f"ffprobe failed: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting audio metadata: {e}")
            return None
    
    def _analyze_segment(self, audio_file: Path, start_time: float, end_time: float) -> Optional[Dict]:
        """
        Analyze a single audio segment for speech activity.
        
        Args:
            audio_file: Path to audio file
            start_time: Segment start time in seconds
            end_time: Segment end time in seconds
            
        Returns:
            Segment analysis dictionary
        """
        try:
            # Extract segment to temporary WAV for analysis
            segment_duration = end_time - start_time
            
            # Use ffmpeg to extract segment and convert to raw audio data
            cmd = [
                'ffmpeg', '-y', '-v', 'quiet',
                '-i', str(audio_file),
                '-ss', str(start_time),
                '-t', str(segment_duration),
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',      # Mono
                '-f', 's16le',   # 16-bit little-endian PCM
                '-'              # Output to stdout
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode != 0:
                return None
                
            # Convert bytes to numpy array
            audio_data = np.frombuffer(result.stdout, dtype=np.int16)
            
            if len(audio_data) == 0:
                return None
                
            # Calculate RMS (Root Mean Square) for speech activity
            audio_float = audio_data.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
            rms = np.sqrt(np.mean(audio_float ** 2))
            
            # Simple speech detection based on RMS threshold
            has_speech = rms > self.speech_threshold
            
            return {
                "start_time": float(start_time),
                "end_time": float(end_time),
                "duration": float(segment_duration),
                "rms": float(rms),
                "has_speech": bool(has_speech),
                "speech_confidence": float(min(rms / self.speech_threshold, 2.0))  # Cap at 2.0
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing segment {start_time}-{end_time}: {e}")
            return None
    
    def _find_content_start(self, segments: List[Dict]) -> Optional[float]:
        """
        Find the start of sustained content based on speech activity.
        
        Args:
            segments: List of segment analysis dictionaries
            
        Returns:
            Time in seconds where sustained content begins
        """
        if not segments:
            return None
            
        # Look for sustained speech activity
        speech_segments = [s for s in segments if s.get('has_speech', False)]
        
        if not speech_segments:
            self.logger.warning("No speech detected in audio")
            return None
            
        # Find first sustained period of speech
        for i, segment in enumerate(segments):
            if not segment.get('has_speech', False):
                continue
                
            # Check if we have sustained speech from this point
            sustained_duration = 0
            j = i
            
            while j < len(segments) and segments[j].get('has_speech', False):
                sustained_duration += segments[j]['duration']
                j += 1
                
                if sustained_duration >= self.min_speech_duration:
                    content_start = segment['start_time']
                    self.logger.info(f"   Content start detected at: {content_start/60:.1f} minutes")
                    self.logger.info(f"   Sustained speech duration: {sustained_duration/60:.1f} minutes")
                    return content_start
                    
        # If no sustained period found, use first speech
        first_speech = speech_segments[0]['start_time']
        self.logger.warning(f"No sustained speech found, using first speech at: {first_speech/60:.1f} minutes")
        return first_speech
    
    def clip_audio(self, 
                   audio_file: Path, 
                   start_time: float, 
                   output_file: Path,
                   end_time: Optional[float] = None) -> bool:
        """
        Clip audio file from start_time to end (or end_time if specified).
        
        Args:
            audio_file: Source audio file
            start_time: Start time in seconds
            output_file: Output clipped audio file
            end_time: Optional end time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"🎵 Clipping audio from {start_time/60:.1f} minutes")
            
            # Prepare ffmpeg command
            cmd = [
                'ffmpeg', '-y', '-v', 'quiet',
                '-i', str(audio_file),
                '-ss', str(start_time)
            ]
            
            if end_time:
                duration = end_time - start_time
                cmd.extend(['-t', str(duration)])
                self.logger.info(f"   Duration: {duration/60:.1f} minutes")
            else:
                self.logger.info("   Duration: to end of file")
                
            # Maintain original quality
            cmd.extend(['-c', 'copy', str(output_file)])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Verify output file
                if output_file.exists() and output_file.stat().st_size > 0:
                    self.logger.info(f"✅ Audio clipped successfully: {output_file.name}")
                    
                    # Get clipped file info
                    clipped_metadata = self._get_audio_metadata(output_file)
                    if clipped_metadata:
                        clipped_duration = float(clipped_metadata.get('duration', 0))
                        clipped_size = output_file.stat().st_size / 1024 / 1024  # MB
                        self.logger.info(f"   Clipped duration: {clipped_duration/60:.1f} minutes")
                        self.logger.info(f"   Clipped size: {clipped_size:.1f} MB")
                        
                    return True
                else:
                    self.logger.error("Output file was not created or is empty")
                    return False
            else:
                self.logger.error(f"ffmpeg failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error clipping audio: {e}")
            return False
    
    def preprocess_audio(self, 
                        audio_file: Path, 
                        output_dir: Path,
                        prefix: str = "preprocessed_") -> Optional[Dict]:
        """
        Complete preprocessing workflow: analyze + clip.
        
        Args:
            audio_file: Source audio file
            output_dir: Output directory for preprocessed audio
            prefix: Prefix for output filename
            
        Returns:
            Dictionary with preprocessing results
        """
        self.logger.info(f"🚀 Starting audio preprocessing: {audio_file.name}")
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Analyze speech activity
        analysis = self.analyze_speech_activity(audio_file)
        
        if "error" in analysis:
            self.logger.error(f"Analysis failed: {analysis['error']}")
            return None
            
        content_start = analysis.get('content_start_time')
        if content_start is None:
            self.logger.error("Could not detect content start")
            return None
            
        # Step 2: Clip audio
        output_file = output_dir / f"{prefix}{audio_file.name}"
        clip_success = self.clip_audio(audio_file, content_start, output_file)
        
        if not clip_success:
            self.logger.error("Audio clipping failed")
            return None
            
        # Step 3: Create preprocessing report
        preprocessing_report = {
            "source_file": str(audio_file),
            "preprocessed_file": str(output_file),
            "content_start_time": content_start,
            "time_removed": content_start,
            "analysis": analysis,
            "preprocessing_timestamp": datetime.now().isoformat(),
            "success": True
        }
        
        # Save report
        report_file = output_dir / f"{prefix}analysis_{audio_file.stem}.json"
        with open(report_file, 'w') as f:
            json.dump(preprocessing_report, f, indent=2)
            
        self.logger.info(f"📊 Preprocessing complete!")
        self.logger.info(f"   Removed: {content_start/60:.1f} minutes of pre-session audio")
        self.logger.info(f"   Output: {output_file.name}")
        self.logger.info(f"   Report: {report_file.name}")
        
        return preprocessing_report


def main():
    """Command line interface for audio preprocessing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess congressional hearing audio')
    parser.add_argument('audio_file', help='Path to audio file')
    parser.add_argument('--output-dir', default='./output/preprocessed_audio', 
                       help='Output directory for preprocessed audio')
    parser.add_argument('--min-speech-duration', type=float, default=60.0,
                       help='Minimum sustained speech duration to detect content start (seconds)')
    parser.add_argument('--speech-threshold', type=float, default=0.02,
                       help='RMS threshold for speech detection')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize preprocessor
    preprocessor = AudioPreprocessor(
        min_speech_duration=args.min_speech_duration,
        speech_threshold=args.speech_threshold
    )
    
    # Process audio
    audio_file = Path(args.audio_file)
    output_dir = Path(args.output_dir)
    
    result = preprocessor.preprocess_audio(audio_file, output_dir)
    
    if result:
        print(f"✅ Preprocessing successful!")
        print(f"   Preprocessed file: {result['preprocessed_file']}")
        print(f"   Time removed: {result['time_removed']/60:.1f} minutes")
    else:
        print("❌ Preprocessing failed")
        sys.exit(1)


if __name__ == "__main__":
    main()