#!/usr/bin/env python3
"""
Audio Quality Testing Module

Tests the quality of extracted MP3 files to ensure they're suitable for
downstream processing like transcription and analysis.
"""

import subprocess
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import wave
import librosa
import matplotlib.pyplot as plt
from datetime import datetime


@dataclass
class AudioQualityMetrics:
    """Audio quality analysis results."""
    file_path: str
    duration_seconds: float
    sample_rate: int
    bit_rate: Optional[int]
    channels: int
    format: str
    
    # Quality metrics
    snr_db: Optional[float]  # Signal-to-noise ratio
    thd_percent: Optional[float]  # Total harmonic distortion  
    dynamic_range_db: Optional[float]  # Dynamic range
    spectral_centroid_hz: Optional[float]  # Spectral brightness
    zero_crossing_rate: Optional[float]  # Speech clarity indicator
    rms_energy: Optional[float]  # Overall energy level
    
    # Transcription readiness
    speech_clarity_score: Optional[float]  # 0-1 score for speech clarity
    transcription_ready: bool
    quality_grade: str  # A, B, C, D, F
    
    # Issues detected
    clipping_detected: bool
    silence_ratio: Optional[float]  # Percentage of silence
    noise_floor_db: Optional[float]
    
    error_message: Optional[str] = None


class AudioQualityTester:
    """Tests audio quality of extracted files."""
    
    def __init__(self):
        self.temp_dir = Path('temp_audio_analysis')
        self.temp_dir.mkdir(exist_ok=True)
    
    def analyze_audio_file(self, file_path: Path) -> AudioQualityMetrics:
        """Comprehensive audio quality analysis."""
        print(f"🔍 Analyzing audio quality: {file_path.name}")
        
        try:
            # Basic file info
            basic_info = self._get_basic_audio_info(file_path)
            
            # Load audio for analysis
            audio_data, sample_rate = librosa.load(str(file_path), sr=None, mono=False)
            
            # Ensure mono for analysis (average channels if stereo)
            if len(audio_data.shape) > 1:
                audio_mono = np.mean(audio_data, axis=0)
            else:
                audio_mono = audio_data
            
            # Calculate quality metrics
            metrics = AudioQualityMetrics(
                file_path=str(file_path),
                duration_seconds=basic_info['duration'],
                sample_rate=basic_info['sample_rate'],
                bit_rate=basic_info.get('bit_rate'),
                channels=basic_info['channels'],
                format=basic_info['format'],
                
                # Quality analysis
                snr_db=self._calculate_snr(audio_mono),
                thd_percent=None,  # Not implemented yet
                dynamic_range_db=self._calculate_dynamic_range(audio_mono),
                spectral_centroid_hz=float(np.mean(librosa.feature.spectral_centroid(y=audio_mono, sr=sample_rate))),
                zero_crossing_rate=float(np.mean(librosa.feature.zero_crossing_rate(audio_mono))),
                rms_energy=float(np.sqrt(np.mean(audio_mono**2))),
                
                # Speech analysis
                speech_clarity_score=None,  # Will be calculated
                transcription_ready=False,  # Will be determined
                quality_grade='',  # Will be determined
                clipping_detected=self._detect_clipping(audio_mono),
                silence_ratio=self._calculate_silence_ratio(audio_mono),
                noise_floor_db=self._estimate_noise_floor(audio_mono)
            )
            
            # Calculate composite scores
            metrics.speech_clarity_score = self._calculate_speech_clarity_score(metrics, audio_mono, sample_rate)
            metrics.quality_grade = self._assign_quality_grade(metrics)
            metrics.transcription_ready = self._assess_transcription_readiness(metrics)
            
            print(f"   ✅ Analysis complete - Grade: {metrics.quality_grade}")
            return metrics
            
        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
            return AudioQualityMetrics(
                file_path=str(file_path),
                duration_seconds=0,
                sample_rate=0,
                bit_rate=None,
                channels=0,
                format='unknown',
                snr_db=None,
                thd_percent=None,
                dynamic_range_db=None,
                spectral_centroid_hz=None,
                zero_crossing_rate=None,
                rms_energy=None,
                speech_clarity_score=None,
                transcription_ready=False,
                quality_grade='F',
                clipping_detected=False,
                silence_ratio=None,
                noise_floor_db=None,
                error_message=str(e)
            )
    
    def _get_basic_audio_info(self, file_path: Path) -> Dict:
        """Get basic audio file information using ffprobe."""
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
            raise RuntimeError(f"ffprobe failed: {result.stderr}")
        
        info = json.loads(result.stdout)
        stream = info['streams'][0]  # First audio stream
        format_info = info['format']
        
        return {
            'duration': float(format_info.get('duration', 0)),
            'sample_rate': int(stream.get('sample_rate', 0)),
            'channels': int(stream.get('channels', 0)),
            'bit_rate': int(stream.get('bit_rate', 0)) if stream.get('bit_rate') else None,
            'format': format_info.get('format_name', 'unknown')
        }
    
    def _calculate_snr(self, audio: np.ndarray) -> float:
        """Calculate signal-to-noise ratio."""
        try:
            # Simple SNR: assume first and last 10% are noise
            signal_portion = audio[int(0.1*len(audio)):int(0.9*len(audio))]
            noise_portion = np.concatenate([audio[:int(0.05*len(audio))], audio[int(0.95*len(audio)):]])
            
            signal_power = np.mean(signal_portion**2)
            noise_power = np.mean(noise_portion**2)
            
            if noise_power > 0:
                snr = 10 * np.log10(signal_power / noise_power)
                return float(snr)
            return 60.0  # Very high SNR if no noise detected
        except:
            return None
    
    def _calculate_dynamic_range(self, audio: np.ndarray) -> float:
        """Calculate dynamic range in dB."""
        try:
            # Dynamic range: difference between 95th and 5th percentile
            p95 = np.percentile(np.abs(audio), 95)
            p5 = np.percentile(np.abs(audio), 5)
            
            if p5 > 0:
                dynamic_range = 20 * np.log10(p95 / p5)
                return float(dynamic_range)
            return 60.0  # High dynamic range
        except:
            return None
    
    def _calculate_silence_ratio(self, audio: np.ndarray, threshold: float = 0.01) -> float:
        """Calculate percentage of audio that is silence."""
        try:
            silence_samples = np.sum(np.abs(audio) < threshold)
            return float(silence_samples / len(audio))
        except:
            return None
    
    def _estimate_noise_floor(self, audio: np.ndarray) -> float:
        """Estimate the noise floor in dB."""
        try:
            # Noise floor: 5th percentile of absolute values
            noise_level = np.percentile(np.abs(audio), 5)
            if noise_level > 0:
                return float(20 * np.log10(noise_level))
            return -60.0  # Very low noise floor
        except:
            return None
    
    def _detect_clipping(self, audio: np.ndarray, threshold: float = 0.98) -> bool:
        """Detect if audio has clipping distortion."""
        try:
            # Check if samples exceed threshold
            clipped_samples = np.sum(np.abs(audio) > threshold)
            return clipped_samples > (0.001 * len(audio))  # More than 0.1% clipped
        except:
            return False
    
    def _calculate_speech_clarity_score(self, metrics: AudioQualityMetrics, 
                                       audio: np.ndarray, sample_rate: int) -> float:
        """Calculate a composite speech clarity score (0-1)."""
        try:
            score = 1.0
            
            # SNR contribution (0.3 weight)
            if metrics.snr_db is not None:
                if metrics.snr_db > 20:
                    snr_score = 1.0
                elif metrics.snr_db > 10:
                    snr_score = 0.8
                elif metrics.snr_db > 5:
                    snr_score = 0.6
                else:
                    snr_score = 0.3
                score *= (0.7 + 0.3 * snr_score)
            
            # Dynamic range contribution (0.2 weight)
            if metrics.dynamic_range_db is not None:
                if metrics.dynamic_range_db > 40:
                    dr_score = 1.0
                elif metrics.dynamic_range_db > 20:
                    dr_score = 0.8
                else:
                    dr_score = 0.5
                score *= (0.8 + 0.2 * dr_score)
            
            # Silence ratio penalty
            if metrics.silence_ratio is not None:
                if metrics.silence_ratio > 0.5:  # More than 50% silence
                    score *= 0.7
                elif metrics.silence_ratio > 0.3:
                    score *= 0.9
            
            # Clipping penalty
            if metrics.clipping_detected:
                score *= 0.8
            
            return min(1.0, max(0.0, score))
            
        except:
            return 0.5  # Default moderate score
    
    def _assign_quality_grade(self, metrics: AudioQualityMetrics) -> str:
        """Assign letter grade based on quality metrics."""
        try:
            score = metrics.speech_clarity_score or 0.5
            
            # Additional penalties
            if metrics.clipping_detected:
                score -= 0.1
            
            if metrics.silence_ratio and metrics.silence_ratio > 0.4:
                score -= 0.1
            
            if metrics.snr_db and metrics.snr_db < 10:
                score -= 0.1
            
            # Assign grades
            if score >= 0.9:
                return 'A'
            elif score >= 0.8:
                return 'B'
            elif score >= 0.7:
                return 'C'
            elif score >= 0.6:
                return 'D'
            else:
                return 'F'
                
        except:
            return 'F'
    
    def _assess_transcription_readiness(self, metrics: AudioQualityMetrics) -> bool:
        """Determine if audio is suitable for transcription."""
        try:
            # Minimum requirements for transcription
            min_snr = 5.0  # dB
            max_silence = 0.6  # 60%
            min_clarity = 0.6
            
            if metrics.error_message:
                return False
            
            if metrics.clipping_detected:
                return False
            
            if metrics.snr_db and metrics.snr_db < min_snr:
                return False
            
            if metrics.silence_ratio and metrics.silence_ratio > max_silence:
                return False
            
            if metrics.speech_clarity_score and metrics.speech_clarity_score < min_clarity:
                return False
            
            return True
            
        except:
            return False
    
    def analyze_all_audio_files(self, audio_dir: Path = None) -> List[AudioQualityMetrics]:
        """Analyze all audio files in the output directory."""
        audio_dir = audio_dir or Path('output')
        
        audio_files = []
        for ext in ['*.mp3', '*.wav', '*.flac']:
            audio_files.extend(audio_dir.glob(ext))
        
        if not audio_files:
            print("No audio files found for quality analysis")
            return []
        
        print(f"🎵 AUDIO QUALITY ANALYSIS")
        print("=" * 50)
        print(f"Found {len(audio_files)} audio files to analyze...")
        
        results = []
        for audio_file in audio_files:
            metrics = self.analyze_audio_file(audio_file)
            results.append(metrics)
        
        # Summary
        self._print_quality_summary(results)
        
        return results
    
    def _print_quality_summary(self, results: List[AudioQualityMetrics]):
        """Print summary of quality analysis."""
        print(f"\n📊 QUALITY SUMMARY")
        print("=" * 30)
        
        total_files = len(results)
        transcription_ready = sum(1 for r in results if r.transcription_ready)
        
        # Grade distribution
        grades = {}
        for result in results:
            grades[result.quality_grade] = grades.get(result.quality_grade, 0) + 1
        
        print(f"Total files analyzed: {total_files}")
        print(f"Transcription ready: {transcription_ready} ({transcription_ready/total_files*100:.1f}%)")
        
        print(f"\nGrade Distribution:")
        for grade in ['A', 'B', 'C', 'D', 'F']:
            count = grades.get(grade, 0)
            if count > 0:
                print(f"  {grade}: {count} files")
        
        # Individual file details
        print(f"\n📋 Individual Results:")
        for result in results:
            status = "✅" if result.transcription_ready else "⚠️"
            filename = Path(result.file_path).name
            clarity = f"{result.speech_clarity_score:.2f}" if result.speech_clarity_score else "N/A"
            snr = f"{result.snr_db:.1f} dB" if result.snr_db else "N/A"
            
            print(f"  {status} {filename}")
            print(f"     Grade: {result.quality_grade}, Clarity: {clarity}, SNR: {snr}")
            
            if result.clipping_detected:
                print(f"     ⚠️  Clipping detected")
            if result.silence_ratio and result.silence_ratio > 0.3:
                print(f"     ⚠️  High silence ratio: {result.silence_ratio:.1%}")


def main():
    """Run audio quality analysis on all files."""
    tester = AudioQualityTester()
    results = tester.analyze_all_audio_files()
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = Path('output') / f'audio_quality_analysis_{timestamp}.json'
    
    # Convert to serializable format
    serializable_results = []
    for result in results:
        serializable_results.append({
            'file_path': result.file_path,
            'duration_seconds': result.duration_seconds,
            'sample_rate': result.sample_rate,
            'bit_rate': result.bit_rate,
            'channels': result.channels,
            'format': result.format,
            'snr_db': result.snr_db,
            'dynamic_range_db': result.dynamic_range_db,
            'spectral_centroid_hz': result.spectral_centroid_hz,
            'zero_crossing_rate': result.zero_crossing_rate,
            'rms_energy': result.rms_energy,
            'speech_clarity_score': result.speech_clarity_score,
            'transcription_ready': bool(result.transcription_ready),
            'quality_grade': str(result.quality_grade),
            'clipping_detected': bool(result.clipping_detected),
            'silence_ratio': result.silence_ratio,
            'noise_floor_db': result.noise_floor_db,
            'error_message': result.error_message
        })
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'total_files': len(results),
            'transcription_ready_count': sum(1 for r in results if r.transcription_ready),
            'results': serializable_results
        }, f, indent=2)
    
    print(f"\n💾 Detailed analysis saved: {results_file}")


if __name__ == "__main__":
    # Install required dependencies if needed
    try:
        import librosa
    except ImportError:
        print("Installing audio analysis dependencies...")
        subprocess.run(['pip', 'install', 'librosa', 'matplotlib'], check=True)
        import librosa
    
    main()