#!/usr/bin/env python3
"""
Predictive Identifier for Phase 6C

Implements predictive speaker identification using context and patterns:
- Context-aware speaker prediction
- Meeting pattern recognition (opening statements, Q&A, closing)
- Senator participation likelihood modeling
- Committee-specific speaker patterns
- Temporal pattern analysis
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import pickle

logger = logging.getLogger(__name__)


class PredictiveIdentifier:
    """Predicts likely speakers based on context and historical patterns."""
    
    def __init__(self, 
                 models_dir: Path = None,
                 corrections_db_path: Path = None,
                 voice_models_db_path: Path = None):
        """Initialize predictive identifier."""
        self.models_dir = models_dir or Path("data/learning/predictive_models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.corrections_db_path = corrections_db_path or Path("output/corrections.db")
        self.voice_models_db_path = voice_models_db_path or Path("data/voice_models/speaker_models.db")
        
        # Prediction models
        self.context_model = None
        self.temporal_model = None
        self.participation_model = None
        
        # Feature scalers
        self.context_scaler = StandardScaler()
        self.temporal_scaler = StandardScaler()
        self.participation_scaler = StandardScaler()
        
        # Pattern cache
        self.committee_patterns = {}
        self.speaker_patterns = {}
        self.temporal_patterns = {}
        
        # Load existing models
        self._load_models()
        
    def _load_models(self):
        """Load pre-trained prediction models."""
        try:
            # Context model
            context_model_path = self.models_dir / "context_model.pkl"
            if context_model_path.exists():
                with open(context_model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.context_model = model_data['model']
                    self.context_scaler = model_data['scaler']
                    logger.info("Loaded context prediction model")
            
            # Temporal model
            temporal_model_path = self.models_dir / "temporal_model.pkl"
            if temporal_model_path.exists():
                with open(temporal_model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.temporal_model = model_data['model']
                    self.temporal_scaler = model_data['scaler']
                    logger.info("Loaded temporal prediction model")
            
            # Participation model
            participation_model_path = self.models_dir / "participation_model.pkl"
            if participation_model_path.exists():
                with open(participation_model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.participation_model = model_data['model']
                    self.participation_scaler = model_data['scaler']
                    logger.info("Loaded participation prediction model")
            
            # Load pattern cache
            patterns_cache_path = self.models_dir / "patterns_cache.pkl"
            if patterns_cache_path.exists():
                with open(patterns_cache_path, 'rb') as f:
                    patterns = pickle.load(f)
                    self.committee_patterns = patterns.get('committee_patterns', {})
                    self.speaker_patterns = patterns.get('speaker_patterns', {})
                    self.temporal_patterns = patterns.get('temporal_patterns', {})
                    logger.info("Loaded prediction patterns cache")
                    
        except Exception as e:
            logger.error(f"Error loading prediction models: {e}")
    
    def _save_models(self):
        """Save trained prediction models."""
        try:
            # Save context model
            if self.context_model:
                context_model_path = self.models_dir / "context_model.pkl"
                with open(context_model_path, 'wb') as f:
                    pickle.dump({
                        'model': self.context_model,
                        'scaler': self.context_scaler
                    }, f)
            
            # Save temporal model
            if self.temporal_model:
                temporal_model_path = self.models_dir / "temporal_model.pkl"
                with open(temporal_model_path, 'wb') as f:
                    pickle.dump({
                        'model': self.temporal_model,
                        'scaler': self.temporal_scaler
                    }, f)
            
            # Save participation model
            if self.participation_model:
                participation_model_path = self.models_dir / "participation_model.pkl"
                with open(participation_model_path, 'wb') as f:
                    pickle.dump({
                        'model': self.participation_model,
                        'scaler': self.participation_scaler
                    }, f)
            
            # Save pattern cache
            patterns_cache_path = self.models_dir / "patterns_cache.pkl"
            with open(patterns_cache_path, 'wb') as f:
                pickle.dump({
                    'committee_patterns': self.committee_patterns,
                    'speaker_patterns': self.speaker_patterns,
                    'temporal_patterns': self.temporal_patterns,
                    'last_updated': datetime.now().isoformat()
                }, f)
            
            logger.info("Saved prediction models and patterns")
            
        except Exception as e:
            logger.error(f"Error saving prediction models: {e}")
    
    def train_prediction_models(self, force_retrain: bool = False) -> Dict[str, Any]:
        """Train prediction models using historical data."""
        logger.info("Training prediction models")
        
        try:
            # Get training data
            training_data = self._get_training_data()
            
            if len(training_data) < 50:  # Minimum training data requirement
                return {
                    'status': 'insufficient_data',
                    'message': f'Need at least 50 samples, got {len(training_data)}',
                    'models_trained': []
                }
            
            training_results = {}
            
            # Train context model
            context_result = self._train_context_model(training_data)
            training_results['context_model'] = context_result
            
            # Train temporal model
            temporal_result = self._train_temporal_model(training_data)
            training_results['temporal_model'] = temporal_result
            
            # Train participation model
            participation_result = self._train_participation_model(training_data)
            training_results['participation_model'] = participation_result
            
            # Update patterns
            patterns_result = self._update_patterns(training_data)
            training_results['patterns'] = patterns_result
            
            # Save models
            self._save_models()
            
            # Calculate overall training success
            successful_models = sum(1 for result in training_results.values() 
                                  if result.get('success', False))
            
            return {
                'status': 'success',
                'training_data_samples': len(training_data),
                'models_trained': successful_models,
                'total_models': len(training_results),
                'results': training_results
            }
            
        except Exception as e:
            logger.error(f"Error training prediction models: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_training_data(self) -> List[Dict[str, Any]]:
        """Get training data from corrections and recognition databases."""
        try:
            training_samples = []
            
            # Get correction data as ground truth
            if self.corrections_db_path.exists():
                with sqlite3.connect(self.corrections_db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    corrections = conn.execute("""
                        SELECT c.*, rs.start_time as session_start, rs.progress_data
                        FROM corrections c
                        LEFT JOIN review_sessions rs ON c.transcript_file = rs.transcript_file
                        WHERE c.is_active = 1
                        ORDER BY c.created_at
                    """).fetchall()
                    
                    for correction in corrections:
                        # Convert sqlite3.Row to dict for easier access
                        correction_dict = dict(correction)
                        
                        sample = {
                            'speaker_name': correction_dict['speaker_name'],
                            'transcript_file': correction_dict['transcript_file'],
                            'segment_id': correction_dict['segment_id'],
                            'confidence': correction_dict['confidence'],
                            'created_at': correction_dict['created_at'],
                            'session_start': correction_dict.get('session_start')
                        }
                        
                        # Extract features
                        features = self._extract_features_for_sample(sample)
                        sample.update(features)
                        
                        training_samples.append(sample)
            
            # Augment with recognition data
            if self.voice_models_db_path.exists():
                with sqlite3.connect(self.voice_models_db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    recognitions = conn.execute("""
                        SELECT * FROM recognition_results
                        WHERE human_verified = 1 AND correction_applied = 0
                    """).fetchall()
                    
                    for recognition in recognitions:
                        # Convert sqlite3.Row to dict for easier access
                        recognition_dict = dict(recognition)
                        
                        if recognition_dict['recognized_speaker']:
                            sample = {
                                'speaker_name': recognition_dict['recognized_speaker'],
                                'audio_segment_id': recognition_dict['audio_segment_id'],
                                'confidence': recognition_dict['confidence_score'],
                                'created_at': recognition_dict['created_at']
                            }
                            
                            # Extract features
                            features = self._extract_features_from_recognition(sample)
                            sample.update(features)
                            
                            training_samples.append(sample)
            
            logger.info(f"Collected {len(training_samples)} training samples")
            return training_samples
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return []
    
    def _extract_features_for_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features for a training sample."""
        features = {}
        
        # Context features
        context = self._extract_context_from_filename(sample.get('transcript_file', ''))
        features.update(self._encode_context_features(context))
        
        # Temporal features
        if sample.get('created_at'):
            features.update(self._extract_temporal_features(sample['created_at']))
        
        # Segment position features
        if sample.get('segment_id'):
            features.update(self._extract_position_features(sample['segment_id']))
        
        # Speaker history features
        features.update(self._extract_speaker_history_features(sample.get('speaker_name', '')))
        
        return features
    
    def _extract_features_from_recognition(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from recognition data."""
        features = {}
        
        # Try to extract context from audio segment ID
        audio_id = sample.get('audio_segment_id', '')
        context = self._extract_context_from_audio_id(audio_id)
        features.update(self._encode_context_features(context))
        
        # Temporal features
        if sample.get('created_at'):
            features.update(self._extract_temporal_features(sample['created_at']))
        
        # Extract segment info from audio ID
        segment_info = self._extract_segment_info_from_audio_id(audio_id)
        features.update(segment_info)
        
        # Speaker history features
        features.update(self._extract_speaker_history_features(sample.get('speaker_name', '')))
        
        return features
    
    def _encode_context_features(self, context: str) -> Dict[str, float]:
        """Encode context as numerical features."""
        context_mapping = {
            'judiciary_committee': [1, 0, 0, 0, 0],
            'intelligence_committee': [0, 1, 0, 0, 0],
            'armed_services_committee': [0, 0, 1, 0, 0],
            'foreign_relations_committee': [0, 0, 0, 1, 0],
            'general_hearing': [0, 0, 0, 0, 1],
            'unknown_context': [0, 0, 0, 0, 0]
        }
        
        encoding = context_mapping.get(context, context_mapping['unknown_context'])
        
        return {
            'context_judiciary': encoding[0],
            'context_intelligence': encoding[1],
            'context_armed_services': encoding[2],
            'context_foreign_relations': encoding[3],
            'context_general': encoding[4]
        }
    
    def _extract_temporal_features(self, timestamp: str) -> Dict[str, float]:
        """Extract temporal features from timestamp."""
        try:
            dt = datetime.fromisoformat(timestamp)
            
            return {
                'hour_of_day': dt.hour / 24.0,
                'day_of_week': dt.weekday() / 6.0,
                'day_of_month': dt.day / 31.0,
                'month_of_year': dt.month / 12.0,
                'is_weekend': float(dt.weekday() >= 5),
                'is_business_hours': float(9 <= dt.hour <= 17)
            }
        except:
            return {
                'hour_of_day': 0.5,
                'day_of_week': 0.5,
                'day_of_month': 0.5,
                'month_of_year': 0.5,
                'is_weekend': 0.0,
                'is_business_hours': 1.0
            }
    
    def _extract_position_features(self, segment_id: int) -> Dict[str, float]:
        """Extract position-based features."""
        # Normalize segment position (assumes max ~200 segments per hearing)
        position_normalized = min(segment_id / 200.0, 1.0)
        
        return {
            'segment_position': position_normalized,
            'is_opening': float(segment_id <= 5),
            'is_early': float(segment_id <= 20),
            'is_middle': float(20 < segment_id <= 100),
            'is_late': float(segment_id > 100),
            'is_closing': float(segment_id > 180)
        }
    
    def _extract_speaker_history_features(self, speaker_name: str) -> Dict[str, float]:
        """Extract speaker history and pattern features."""
        # Simple speaker categorization
        features = {
            'is_senator': float('sen.' in speaker_name.lower()),
            'is_chairman': float('chairman' in speaker_name.lower() or 'chair' in speaker_name.lower()),
            'is_ranking_member': float('ranking' in speaker_name.lower()),
            'is_witness': float('dr.' in speaker_name.lower() or 'mr.' in speaker_name.lower() or 'ms.' in speaker_name.lower()),
            'speaker_name_length': len(speaker_name) / 50.0  # Normalize name length
        }
        
        # Add speaker frequency if available in patterns
        if speaker_name in self.speaker_patterns:
            pattern = self.speaker_patterns[speaker_name]
            features.update({
                'speaker_frequency': min(pattern.get('total_appearances', 0) / 100.0, 1.0),
                'speaker_avg_segments': min(pattern.get('avg_segments_per_hearing', 0) / 50.0, 1.0),
                'speaker_committee_diversity': min(pattern.get('committee_diversity', 0) / 5.0, 1.0)
            })
        else:
            features.update({
                'speaker_frequency': 0.0,
                'speaker_avg_segments': 0.0,
                'speaker_committee_diversity': 0.0
            })
        
        return features
    
    def _extract_context_from_filename(self, filename: str) -> str:
        """Extract context from filename."""
        filename = filename.lower()
        
        if 'judiciary' in filename:
            return 'judiciary_committee'
        elif 'intelligence' in filename:
            return 'intelligence_committee'
        elif 'armed_services' in filename:
            return 'armed_services_committee'
        elif 'foreign_relations' in filename:
            return 'foreign_relations_committee'
        elif 'hearing' in filename:
            return 'general_hearing'
        else:
            return 'unknown_context'
    
    def _extract_context_from_audio_id(self, audio_id: str) -> str:
        """Extract context from audio segment ID."""
        return self._extract_context_from_filename(audio_id)
    
    def _extract_segment_info_from_audio_id(self, audio_id: str) -> Dict[str, float]:
        """Extract segment information from audio ID."""
        try:
            # Try to extract segment number from audio ID
            parts = audio_id.split('_')
            segment_id = 0
            
            for part in parts:
                if part.startswith('segment'):
                    segment_id = int(part.replace('segment', ''))
                    break
                elif part.isdigit():
                    segment_id = int(part)
                    break
            
            return self._extract_position_features(segment_id)
        except:
            return self._extract_position_features(0)
    
    def _train_context_model(self, training_data: List[Dict]) -> Dict[str, Any]:
        """Train context-based speaker prediction model."""
        try:
            # Prepare features and labels
            feature_names = [
                'context_judiciary', 'context_intelligence', 'context_armed_services',
                'context_foreign_relations', 'context_general', 'segment_position',
                'is_opening', 'is_early', 'is_middle', 'is_late', 'is_closing'
            ]
            
            X = []
            y = []
            
            for sample in training_data:
                features = [sample.get(fname, 0.0) for fname in feature_names]
                X.append(features)
                y.append(sample['speaker_name'])
            
            if len(set(y)) < 2:  # Need at least 2 different speakers
                return {'success': False, 'error': 'Insufficient speaker diversity'}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
            )
            
            # Scale features
            X_train_scaled = self.context_scaler.fit_transform(X_train)
            X_test_scaled = self.context_scaler.transform(X_test)
            
            # Train model
            self.context_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            
            self.context_model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.context_model.score(X_train_scaled, y_train)
            test_score = self.context_model.score(X_test_scaled, y_test)
            
            return {
                'success': True,
                'train_accuracy': train_score,
                'test_accuracy': test_score,
                'feature_names': feature_names,
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
        except Exception as e:
            logger.error(f"Error training context model: {e}")
            return {'success': False, 'error': str(e)}
    
    def _train_temporal_model(self, training_data: List[Dict]) -> Dict[str, Any]:
        """Train temporal pattern prediction model."""
        try:
            # Prepare temporal features
            feature_names = [
                'hour_of_day', 'day_of_week', 'day_of_month', 'month_of_year',
                'is_weekend', 'is_business_hours', 'segment_position'
            ]
            
            X = []
            y = []
            
            for sample in training_data:
                features = [sample.get(fname, 0.0) for fname in feature_names]
                X.append(features)
                y.append(sample['speaker_name'])
            
            if len(set(y)) < 2:
                return {'success': False, 'error': 'Insufficient speaker diversity'}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
            )
            
            # Scale features
            X_train_scaled = self.temporal_scaler.fit_transform(X_train)
            X_test_scaled = self.temporal_scaler.transform(X_test)
            
            # Train model
            self.temporal_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=8,
                random_state=42,
                class_weight='balanced'
            )
            
            self.temporal_model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.temporal_model.score(X_train_scaled, y_train)
            test_score = self.temporal_model.score(X_test_scaled, y_test)
            
            return {
                'success': True,
                'train_accuracy': train_score,
                'test_accuracy': test_score,
                'feature_names': feature_names,
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
        except Exception as e:
            logger.error(f"Error training temporal model: {e}")
            return {'success': False, 'error': str(e)}
    
    def _train_participation_model(self, training_data: List[Dict]) -> Dict[str, Any]:
        """Train speaker participation likelihood model."""
        try:
            # Prepare participation features
            feature_names = [
                'is_senator', 'is_chairman', 'is_ranking_member', 'is_witness',
                'speaker_frequency', 'speaker_avg_segments', 'speaker_committee_diversity',
                'context_judiciary', 'context_intelligence', 'context_armed_services'
            ]
            
            X = []
            y = []
            
            for sample in training_data:
                features = [sample.get(fname, 0.0) for fname in feature_names]
                X.append(features)
                y.append(sample['speaker_name'])
            
            if len(set(y)) < 2:
                return {'success': False, 'error': 'Insufficient speaker diversity'}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
            )
            
            # Scale features
            X_train_scaled = self.participation_scaler.fit_transform(X_train)
            X_test_scaled = self.participation_scaler.transform(X_test)
            
            # Train model
            self.participation_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=12,
                random_state=42,
                class_weight='balanced'
            )
            
            self.participation_model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.participation_model.score(X_train_scaled, y_train)
            test_score = self.participation_model.score(X_test_scaled, y_test)
            
            return {
                'success': True,
                'train_accuracy': train_score,
                'test_accuracy': test_score,
                'feature_names': feature_names,
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
        except Exception as e:
            logger.error(f"Error training participation model: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_patterns(self, training_data: List[Dict]) -> Dict[str, Any]:
        """Update speaker and committee patterns from training data."""
        try:
            # Update speaker patterns
            speaker_stats = defaultdict(lambda: {
                'total_appearances': 0,
                'committees': set(),
                'segments': [],
                'contexts': []
            })
            
            # Update committee patterns
            committee_stats = defaultdict(lambda: {
                'speakers': set(),
                'segments_count': 0,
                'common_speakers': Counter()
            })
            
            for sample in training_data:
                speaker = sample['speaker_name']
                context = sample.get('context_judiciary', 0) + sample.get('context_intelligence', 0) + \
                         sample.get('context_armed_services', 0) + sample.get('context_foreign_relations', 0)
                
                # Update speaker patterns
                speaker_stats[speaker]['total_appearances'] += 1
                speaker_stats[speaker]['segments'].append(sample.get('segment_position', 0))
                
                # Determine context
                if sample.get('context_judiciary', 0) > 0:
                    speaker_stats[speaker]['committees'].add('judiciary')
                    committee_stats['judiciary']['speakers'].add(speaker)
                    committee_stats['judiciary']['common_speakers'][speaker] += 1
                elif sample.get('context_intelligence', 0) > 0:
                    speaker_stats[speaker]['committees'].add('intelligence')
                    committee_stats['intelligence']['speakers'].add(speaker)
                    committee_stats['intelligence']['common_speakers'][speaker] += 1
                # ... similar for other committees
            
            # Process speaker patterns
            for speaker, stats in speaker_stats.items():
                stats['committees'] = list(stats['committees'])
                stats['committee_diversity'] = len(stats['committees'])
                stats['avg_segments_per_hearing'] = np.mean(stats['segments']) if stats['segments'] else 0
                del stats['segments']  # Remove large data for storage
            
            # Process committee patterns
            for committee, stats in committee_stats.items():
                stats['speakers'] = list(stats['speakers'])
                stats['unique_speakers'] = len(stats['speakers'])
                stats['most_common_speakers'] = stats['common_speakers'].most_common(10)
                del stats['common_speakers']  # Remove Counter for storage
            
            # Update internal patterns
            self.speaker_patterns.update(speaker_stats)
            self.committee_patterns.update(committee_stats)
            
            return {
                'success': True,
                'speakers_updated': len(speaker_stats),
                'committees_updated': len(committee_stats)
            }
            
        except Exception as e:
            logger.error(f"Error updating patterns: {e}")
            return {'success': False, 'error': str(e)}
    
    def predict_speaker_likelihood(self, 
                                  context: Dict[str, Any],
                                  candidate_speakers: List[str] = None) -> Dict[str, Any]:
        """Predict speaker likelihood for given context."""
        try:
            if not all([self.context_model, self.temporal_model, self.participation_model]):
                return {
                    'status': 'models_not_trained',
                    'message': 'Prediction models not available - train models first'
                }
            
            # Extract features from context
            features = self._extract_prediction_features(context)
            
            # Get predictions from each model
            predictions = {}
            
            # Context model prediction
            if self.context_model:
                context_features = [features.get(fname, 0.0) for fname in [
                    'context_judiciary', 'context_intelligence', 'context_armed_services',
                    'context_foreign_relations', 'context_general', 'segment_position',
                    'is_opening', 'is_early', 'is_middle', 'is_late', 'is_closing'
                ]]
                context_features_scaled = self.context_scaler.transform([context_features])
                context_probs = self.context_model.predict_proba(context_features_scaled)[0]
                context_classes = self.context_model.classes_
                
                predictions['context'] = {
                    class_name: prob for class_name, prob in zip(context_classes, context_probs)
                }
            
            # Temporal model prediction
            if self.temporal_model:
                temporal_features = [features.get(fname, 0.0) for fname in [
                    'hour_of_day', 'day_of_week', 'day_of_month', 'month_of_year',
                    'is_weekend', 'is_business_hours', 'segment_position'
                ]]
                temporal_features_scaled = self.temporal_scaler.transform([temporal_features])
                temporal_probs = self.temporal_model.predict_proba(temporal_features_scaled)[0]
                temporal_classes = self.temporal_model.classes_
                
                predictions['temporal'] = {
                    class_name: prob for class_name, prob in zip(temporal_classes, temporal_probs)
                }
            
            # Participation model prediction
            if self.participation_model:
                participation_features = [features.get(fname, 0.0) for fname in [
                    'is_senator', 'is_chairman', 'is_ranking_member', 'is_witness',
                    'speaker_frequency', 'speaker_avg_segments', 'speaker_committee_diversity',
                    'context_judiciary', 'context_intelligence', 'context_armed_services'
                ]]
                participation_features_scaled = self.participation_scaler.transform([participation_features])
                participation_probs = self.participation_model.predict_proba(participation_features_scaled)[0]
                participation_classes = self.participation_model.classes_
                
                predictions['participation'] = {
                    class_name: prob for class_name, prob in zip(participation_classes, participation_probs)
                }
            
            # Combine predictions
            combined_predictions = self._combine_predictions(predictions, candidate_speakers)
            
            return {
                'status': 'success',
                'combined_predictions': combined_predictions,
                'individual_predictions': predictions,
                'context_features': features
            }
            
        except Exception as e:
            logger.error(f"Error predicting speaker likelihood: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _extract_prediction_features(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Extract features for prediction from context."""
        features = {}
        
        # Context features
        committee = context.get('committee', 'unknown')
        context_str = f"{committee}_committee" if committee != 'unknown' else 'general_hearing'
        features.update(self._encode_context_features(context_str))
        
        # Temporal features
        timestamp = context.get('timestamp', datetime.now().isoformat())
        features.update(self._extract_temporal_features(timestamp))
        
        # Position features
        segment_id = context.get('segment_id', 0)
        features.update(self._extract_position_features(segment_id))
        
        # Speaker features for candidates
        candidate_speakers = context.get('candidate_speakers', [])
        if candidate_speakers:
            # Use first candidate as reference for features
            features.update(self._extract_speaker_history_features(candidate_speakers[0]))
        else:
            # Default speaker features
            features.update(self._extract_speaker_history_features(''))
        
        return features
    
    def _combine_predictions(self, 
                           predictions: Dict[str, Dict[str, float]], 
                           candidate_speakers: List[str] = None) -> List[Dict[str, Any]]:
        """Combine predictions from multiple models."""
        # Weights for different prediction models
        model_weights = {
            'context': 0.4,
            'temporal': 0.3,
            'participation': 0.3
        }
        
        # Get all unique speakers from predictions
        all_speakers = set()
        for model_preds in predictions.values():
            all_speakers.update(model_preds.keys())
        
        # Filter by candidate speakers if provided
        if candidate_speakers:
            all_speakers = all_speakers.intersection(set(candidate_speakers))
        
        # Combine predictions
        combined_scores = {}
        for speaker in all_speakers:
            score = 0.0
            weight_sum = 0.0
            
            for model_name, model_preds in predictions.items():
                if speaker in model_preds:
                    weight = model_weights.get(model_name, 0.0)
                    score += model_preds[speaker] * weight
                    weight_sum += weight
            
            if weight_sum > 0:
                combined_scores[speaker] = score / weight_sum
            else:
                combined_scores[speaker] = 0.0
        
        # Sort by combined score
        sorted_predictions = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Format results
        results = []
        for i, (speaker, score) in enumerate(sorted_predictions[:10]):  # Top 10
            results.append({
                'speaker_name': speaker,
                'likelihood_score': score,
                'rank': i + 1,
                'confidence_level': self._get_confidence_level(score)
            })
        
        return results
    
    def _get_confidence_level(self, score: float) -> str:
        """Get confidence level based on likelihood score."""
        if score >= 0.8:
            return 'very_high'
        elif score >= 0.6:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        elif score >= 0.2:
            return 'low'
        else:
            return 'very_low'
    
    def get_meeting_structure_prediction(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict meeting structure and likely speaker patterns."""
        try:
            committee = context.get('committee', 'unknown')
            
            # Default meeting structure
            structure = {
                'phases': [
                    {'name': 'opening_statements', 'duration_segments': 20, 'likely_speakers': ['chairman']},
                    {'name': 'witness_testimony', 'duration_segments': 40, 'likely_speakers': ['witnesses']},
                    {'name': 'qa_rounds', 'duration_segments': 100, 'likely_speakers': ['senators', 'witnesses']},
                    {'name': 'closing_remarks', 'duration_segments': 10, 'likely_speakers': ['chairman', 'ranking_member']}
                ],
                'total_estimated_segments': 170,
                'committee_specific_patterns': {}
            }
            
            # Committee-specific adjustments
            if committee in self.committee_patterns:
                committee_info = self.committee_patterns[committee]
                structure['committee_specific_patterns'] = {
                    'most_active_speakers': committee_info.get('most_common_speakers', [])[:5],
                    'average_speakers_per_hearing': committee_info.get('unique_speakers', 0),
                    'typical_segments': committee_info.get('segments_count', 0)
                }
            
            return {
                'status': 'success',
                'meeting_structure': structure,
                'committee': committee
            }
            
        except Exception as e:
            logger.error(f"Error predicting meeting structure: {e}")
            return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    # Test predictive identifier
    predictor = PredictiveIdentifier()
    
    # Train models
    training_result = predictor.train_prediction_models()
    print(f"Training result: {json.dumps(training_result, indent=2)}")
    
    # Test prediction
    context = {
        'committee': 'judiciary',
        'segment_id': 25,
        'timestamp': datetime.now().isoformat(),
        'candidate_speakers': ['Sen. Cruz', 'Sen. Feinstein', 'Sen. Graham']
    }
    
    prediction = predictor.predict_speaker_likelihood(context)
    print(f"Prediction result: {json.dumps(prediction, indent=2)}")