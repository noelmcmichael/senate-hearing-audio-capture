#!/usr/bin/env python3
"""
Voice Processor for Phase 6B

Audio feature extraction and voice fingerprinting for speaker recognition:
- MFCC (Mel-Frequency Cepstral Coefficients) analysis
- Pitch and spectral feature extraction
- Voice similarity matching
- Speaker model creation and storage
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import hashlib

import librosa
import librosa.display
from scipy.spatial.distance import cosine
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
import joblib


logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Voice fingerprinting and similarity analysis system."""
    
    def __init__(self, models_dir: Path = None):
        """Initialize voice processor."""
        self.models_dir = models_dir or Path("data/voice_models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Audio processing parameters
        self.sample_rate = 16000  # Standard for speech recognition
        self.frame_length = 2048
        self.hop_length = 512
        self.n_mfcc = 13
        self.n_mels = 40
        
        # Feature extraction parameters
        self.feature_window_size = 3.0  # seconds
        self.feature_overlap = 0.5  # 50% overlap
        
        # Voice model parameters
        self.gmm_components = 16  # Gaussian Mixture Model components
        self.min_training_samples = 5  # Minimum samples to create voice model
        
        # Similarity thresholds
        self.similarity_thresholds = {
            'high_confidence': 0.8,
            'medium_confidence': 0.6,
            'low_confidence': 0.4
        }
        
        # Feature scaler for normalization
        self.scaler = StandardScaler()
    
    def extract_voice_features(self, audio_file: Path) -> Dict[str, Any]:
        """Extract comprehensive voice features from audio file."""
        try:
            logger.info(f"Extracting voice features from {audio_file}")
            
            # Load audio
            y, sr = librosa.load(audio_file, sr=self.sample_rate)
            
            if len(y) < self.sample_rate:  # Less than 1 second
                logger.warning(f"Audio file too short: {len(y)/sr:.2f}s")
                return None
            
            # Extract multiple feature types
            features = {
                'mfcc': self._extract_mfcc_features(y, sr),
                'spectral': self._extract_spectral_features(y, sr),
                'prosodic': self._extract_prosodic_features(y, sr),
                'temporal': self._extract_temporal_features(y, sr),
                'quality': self._assess_audio_quality(y, sr)
            }
            
            # Combine features into single vector
            feature_vector = self._combine_features(features)
            
            return {
                'features': features,
                'feature_vector': feature_vector,
                'audio_duration': len(y) / sr,
                'sample_rate': sr,
                'quality_score': features['quality']['overall_quality'],
                'file_path': str(audio_file)
            }
            
        except Exception as e:
            logger.error(f"Error extracting features from {audio_file}: {e}")
            return None
    
    def _extract_mfcc_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract MFCC (Mel-Frequency Cepstral Coefficients) features."""
        try:
            # Extract MFCCs
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc)
            
            # Calculate statistics
            mfcc_mean = np.mean(mfccs, axis=1)
            mfcc_std = np.std(mfccs, axis=1)
            mfcc_delta = librosa.feature.delta(mfccs)
            mfcc_delta2 = librosa.feature.delta(mfccs, order=2)
            
            return {
                'mfcc_mean': mfcc_mean.tolist(),
                'mfcc_std': mfcc_std.tolist(),
                'mfcc_delta_mean': np.mean(mfcc_delta, axis=1).tolist(),
                'mfcc_delta2_mean': np.mean(mfcc_delta2, axis=1).tolist(),
                'mfcc_covariance': np.cov(mfccs).tolist()
            }
            
        except Exception as e:
            logger.error(f"Error extracting MFCC features: {e}")
            return {}
    
    def _extract_spectral_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract spectral features."""
        try:
            # Spectral centroid
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            
            # Spectral bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            
            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            
            # Chroma features
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            
            # Mel spectrogram
            mel_spectrogram = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=self.n_mels)
            
            return {
                'spectral_centroid_mean': np.mean(spectral_centroids),
                'spectral_centroid_std': np.std(spectral_centroids),
                'spectral_bandwidth_mean': np.mean(spectral_bandwidth),
                'spectral_bandwidth_std': np.std(spectral_bandwidth),
                'spectral_rolloff_mean': np.mean(spectral_rolloff),
                'spectral_rolloff_std': np.std(spectral_rolloff),
                'zero_crossing_rate_mean': np.mean(zcr),
                'zero_crossing_rate_std': np.std(zcr),
                'chroma_mean': np.mean(chroma, axis=1).tolist(),
                'chroma_std': np.std(chroma, axis=1).tolist(),
                'mel_spectrogram_mean': np.mean(mel_spectrogram, axis=1).tolist(),
                'mel_spectrogram_std': np.std(mel_spectrogram, axis=1).tolist()
            }
            
        except Exception as e:
            logger.error(f"Error extracting spectral features: {e}")
            return {}
    
    def _extract_prosodic_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract prosodic features (pitch, rhythm, etc.)."""
        try:
            # Fundamental frequency (pitch)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            
            # Extract pitch values
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if len(pitch_values) == 0:
                pitch_values = [0]
            
            # Tempo and beat tracking
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # RMS energy
            rms = librosa.feature.rms(y=y)[0]
            
            return {
                'pitch_mean': np.mean(pitch_values),
                'pitch_std': np.std(pitch_values),
                'pitch_range': np.max(pitch_values) - np.min(pitch_values) if len(pitch_values) > 1 else 0,
                'tempo': float(tempo),
                'beat_count': len(beats),
                'rms_energy_mean': np.mean(rms),
                'rms_energy_std': np.std(rms),
                'speech_rate': len(beats) / (len(y) / sr)  # beats per second
            }
            
        except Exception as e:
            logger.error(f"Error extracting prosodic features: {e}")
            return {}
    
    def _extract_temporal_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract temporal features."""
        try:
            # Voice activity detection (simplified)
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)    # 10ms hop
            
            # Calculate frame energy
            frames = librosa.util.frame(y, frame_length=frame_length, hop_length=hop_length)
            energy = np.sum(frames ** 2, axis=0)
            
            # Voice activity detection threshold
            energy_threshold = np.mean(energy) * 0.1
            voice_frames = energy > energy_threshold
            
            # Calculate speaking rate and pauses
            voice_segments = []
            in_speech = False
            segment_start = 0
            
            for i, is_voice in enumerate(voice_frames):
                if is_voice and not in_speech:
                    segment_start = i
                    in_speech = True
                elif not is_voice and in_speech:
                    voice_segments.append(i - segment_start)
                    in_speech = False
            
            if in_speech:
                voice_segments.append(len(voice_frames) - segment_start)
            
            return {
                'voice_activity_ratio': np.sum(voice_frames) / len(voice_frames),
                'average_voice_segment_length': np.mean(voice_segments) if voice_segments else 0,
                'voice_segment_count': len(voice_segments),
                'pause_count': max(0, len(voice_segments) - 1),
                'speech_rhythm_regularity': np.std(voice_segments) if len(voice_segments) > 1 else 0
            }
            
        except Exception as e:
            logger.error(f"Error extracting temporal features: {e}")
            return {}
    
    def _assess_audio_quality(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Assess audio quality metrics."""
        try:
            # Signal-to-noise ratio estimation
            # Assuming first and last 0.5 seconds are noise
            noise_samples = int(0.5 * sr)
            if len(y) > 2 * noise_samples:
                noise = np.concatenate([y[:noise_samples], y[-noise_samples:]])
                signal = y[noise_samples:-noise_samples]
                
                noise_power = np.mean(noise ** 2)
                signal_power = np.mean(signal ** 2)
                snr = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 50
            else:
                snr = 20  # Default reasonable value
            
            # Dynamic range
            dynamic_range = np.max(np.abs(y)) - np.min(np.abs(y))
            
            # Clipping detection
            clipping_ratio = np.sum(np.abs(y) > 0.99) / len(y)
            
            # Overall quality score
            quality_factors = {
                'snr': min(snr / 30, 1.0),  # Normalize to 0-1
                'dynamic_range': min(dynamic_range * 2, 1.0),
                'no_clipping': max(0, 1.0 - clipping_ratio * 10)
            }
            
            overall_quality = np.mean(list(quality_factors.values()))
            
            return {
                'snr_db': snr,
                'dynamic_range': dynamic_range,
                'clipping_ratio': clipping_ratio,
                'overall_quality': overall_quality,
                'quality_factors': quality_factors
            }
            
        except Exception as e:
            logger.error(f"Error assessing audio quality: {e}")
            return {'overall_quality': 0.5}  # Default neutral quality
    
    def _combine_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Combine all features into a single vector."""
        try:
            feature_vector = []
            
            # MFCC features
            mfcc = features.get('mfcc', {})
            feature_vector.extend(mfcc.get('mfcc_mean', []))
            feature_vector.extend(mfcc.get('mfcc_std', []))
            feature_vector.extend(mfcc.get('mfcc_delta_mean', []))
            
            # Spectral features
            spectral = features.get('spectral', {})
            feature_vector.extend([
                spectral.get('spectral_centroid_mean', 0),
                spectral.get('spectral_centroid_std', 0),
                spectral.get('spectral_bandwidth_mean', 0),
                spectral.get('spectral_bandwidth_std', 0),
                spectral.get('spectral_rolloff_mean', 0),
                spectral.get('spectral_rolloff_std', 0),
                spectral.get('zero_crossing_rate_mean', 0),
                spectral.get('zero_crossing_rate_std', 0)
            ])
            
            # Prosodic features
            prosodic = features.get('prosodic', {})
            feature_vector.extend([
                prosodic.get('pitch_mean', 0),
                prosodic.get('pitch_std', 0),
                prosodic.get('pitch_range', 0),
                prosodic.get('tempo', 0),
                prosodic.get('rms_energy_mean', 0),
                prosodic.get('rms_energy_std', 0),
                prosodic.get('speech_rate', 0)
            ])
            
            # Temporal features
            temporal = features.get('temporal', {})
            feature_vector.extend([
                temporal.get('voice_activity_ratio', 0),
                temporal.get('average_voice_segment_length', 0),
                temporal.get('speech_rhythm_regularity', 0)
            ])
            
            # Quality features
            quality = features.get('quality', {})
            feature_vector.extend([
                quality.get('overall_quality', 0),
                quality.get('snr_db', 0),
                quality.get('dynamic_range', 0)
            ])
            
            return np.array(feature_vector, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error combining features: {e}")
            return np.array([])
    
    def create_speaker_model(self, senator_name: str, feature_vectors: List[np.ndarray]) -> Dict[str, Any]:
        """Create a voice model for a speaker using Gaussian Mixture Model."""
        try:
            logger.info(f"Creating voice model for {senator_name} with {len(feature_vectors)} samples")
            
            if len(feature_vectors) < self.min_training_samples:
                logger.warning(f"Insufficient samples for {senator_name}: {len(feature_vectors)} < {self.min_training_samples}")
                return None
            
            # Stack feature vectors
            X = np.vstack(feature_vectors)
            
            # Normalize features
            X_normalized = self.scaler.fit_transform(X)
            
            # Train Gaussian Mixture Model
            gmm = GaussianMixture(
                n_components=min(self.gmm_components, len(feature_vectors)),
                covariance_type='full',
                random_state=42
            )
            
            gmm.fit(X_normalized)
            
            # Calculate model statistics
            log_likelihood = gmm.score(X_normalized)
            
            # Create voice model
            voice_model = {
                'senator_name': senator_name,
                'model_type': 'gaussian_mixture',
                'n_components': gmm.n_components,
                'training_samples': len(feature_vectors),
                'feature_dimension': X.shape[1],
                'log_likelihood': log_likelihood,
                'model_weights': gmm.weights_.tolist(),
                'model_means': gmm.means_.tolist(),
                'model_covariances': gmm.covariances_.tolist(),
                'scaler_mean': self.scaler.mean_.tolist(),
                'scaler_scale': self.scaler.scale_.tolist(),
                'created_at': np.datetime64('now').astype(str)
            }
            
            # Save model
            model_path = self._save_speaker_model(senator_name, voice_model, gmm)
            voice_model['model_path'] = str(model_path)
            
            logger.info(f"Created voice model for {senator_name}: {model_path}")
            return voice_model
            
        except Exception as e:
            logger.error(f"Error creating speaker model for {senator_name}: {e}")
            return None
    
    def _save_speaker_model(self, senator_name: str, voice_model: Dict[str, Any], gmm: GaussianMixture) -> Path:
        """Save speaker voice model to disk."""
        safe_name = senator_name.replace(' ', '_').replace('.', '_')
        
        # Save metadata
        metadata_path = self.models_dir / f"{safe_name}_model.json"
        with open(metadata_path, 'w') as f:
            json.dump(voice_model, f, indent=2)
        
        # Save sklearn model
        model_path = self.models_dir / f"{safe_name}_gmm.joblib"
        joblib.dump({
            'gmm': gmm,
            'scaler_mean': self.scaler.mean_,
            'scaler_scale': self.scaler.scale_
        }, model_path)
        
        return metadata_path
    
    def load_speaker_model(self, senator_name: str) -> Optional[Tuple[Dict[str, Any], GaussianMixture]]:
        """Load speaker voice model from disk."""
        try:
            safe_name = senator_name.replace(' ', '_').replace('.', '_')
            
            # Load metadata
            metadata_path = self.models_dir / f"{safe_name}_model.json"
            if not metadata_path.exists():
                return None
            
            with open(metadata_path, 'r') as f:
                voice_model = json.load(f)
            
            # Load sklearn model
            model_path = self.models_dir / f"{safe_name}_gmm.joblib"
            if not model_path.exists():
                return None
            
            model_data = joblib.load(model_path)
            gmm = model_data['gmm']
            
            # Restore scaler
            self.scaler.mean_ = model_data['scaler_mean']
            self.scaler.scale_ = model_data['scaler_scale']
            
            return voice_model, gmm
            
        except Exception as e:
            logger.error(f"Error loading speaker model for {senator_name}: {e}")
            return None
    
    def calculate_voice_similarity(
        self, 
        feature_vector: np.ndarray, 
        senator_name: str
    ) -> Dict[str, Any]:
        """Calculate voice similarity with a speaker model."""
        try:
            # Load speaker model
            model_data = self.load_speaker_model(senator_name)
            if not model_data:
                return {
                    'senator_name': senator_name,
                    'similarity_score': 0.0,
                    'confidence_level': 'none',
                    'error': 'No voice model found'
                }
            
            voice_model, gmm = model_data
            
            # Normalize feature vector
            feature_normalized = self.scaler.transform(feature_vector.reshape(1, -1))
            
            # Calculate log-likelihood
            log_likelihood = gmm.score(feature_normalized)
            
            # Convert to similarity score (0-1 range)
            # Higher log-likelihood = higher similarity
            baseline_likelihood = voice_model.get('log_likelihood', -100)
            similarity_score = max(0, min(1, (log_likelihood - baseline_likelihood + 50) / 50))
            
            # Determine confidence level
            if similarity_score >= self.similarity_thresholds['high_confidence']:
                confidence_level = 'high'
            elif similarity_score >= self.similarity_thresholds['medium_confidence']:
                confidence_level = 'medium'
            elif similarity_score >= self.similarity_thresholds['low_confidence']:
                confidence_level = 'low'
            else:
                confidence_level = 'very_low'
            
            return {
                'senator_name': senator_name,
                'similarity_score': similarity_score,
                'confidence_level': confidence_level,
                'log_likelihood': log_likelihood,
                'baseline_likelihood': baseline_likelihood,
                'model_training_samples': voice_model.get('training_samples', 0)
            }
            
        except Exception as e:
            logger.error(f"Error calculating voice similarity for {senator_name}: {e}")
            return {
                'senator_name': senator_name,
                'similarity_score': 0.0,
                'confidence_level': 'error',
                'error': str(e)
            }
    
    def identify_speaker(
        self, 
        feature_vector: np.ndarray, 
        candidate_senators: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Identify speaker by comparing with all available voice models."""
        try:
            # Get list of available models
            if candidate_senators is None:
                model_files = list(self.models_dir.glob("*_model.json"))
                candidate_senators = []
                for model_file in model_files:
                    senator_name = model_file.stem.replace('_model', '').replace('_', ' ')
                    candidate_senators.append(senator_name)
            
            if not candidate_senators:
                logger.warning("No voice models available for speaker identification")
                return []
            
            # Calculate similarities with all candidates
            similarities = []
            for senator_name in candidate_senators:
                similarity = self.calculate_voice_similarity(feature_vector, senator_name)
                similarities.append(similarity)
            
            # Sort by similarity score
            similarities.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            
            logger.info(f"Speaker identification results: top match = {similarities[0]['senator_name']} "
                       f"(score: {similarities[0]['similarity_score']:.3f})")
            
            return similarities
            
        except Exception as e:
            logger.error(f"Error in speaker identification: {e}")
            return []
    
    def get_model_summary(self) -> Dict[str, Any]:
        """Get summary of all available voice models."""
        try:
            model_files = list(self.models_dir.glob("*_model.json"))
            
            models = []
            for model_file in model_files:
                with open(model_file, 'r') as f:
                    model_data = json.load(f)
                
                models.append({
                    'senator_name': model_data.get('senator_name', ''),
                    'training_samples': model_data.get('training_samples', 0),
                    'created_at': model_data.get('created_at', ''),
                    'feature_dimension': model_data.get('feature_dimension', 0),
                    'log_likelihood': model_data.get('log_likelihood', 0)
                })
            
            return {
                'total_models': len(models),
                'models': models,
                'total_training_samples': sum(m['training_samples'] for m in models)
            }
            
        except Exception as e:
            logger.error(f"Error getting model summary: {e}")
            return {'total_models': 0, 'models': [], 'error': str(e)}


if __name__ == "__main__":
    # Test voice processing
    processor = VoiceProcessor()
    
    # Test feature extraction (would need an actual audio file)
    print("Voice processor initialized")
    print(f"Models directory: {processor.models_dir}")
    
    # Get model summary
    summary = processor.get_model_summary()
    print(f"Available models: {summary}")