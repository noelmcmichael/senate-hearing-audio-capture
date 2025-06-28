#!/usr/bin/env python3
"""
Speaker Models for Phase 6B

Voice model management and speaker recognition integration:
- Voice model storage and retrieval
- Speaker profile management
- Integration with Phase 6A correction data
- Voice recognition enhancement for speaker identification
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np

from .voice_processor import VoiceProcessor


logger = logging.getLogger(__name__)


class SpeakerModelManager:
    """Manager for speaker voice models and recognition."""
    
    def __init__(self, models_dir: Path = None, db_path: Path = None):
        """Initialize speaker model manager."""
        self.models_dir = models_dir or Path("data/voice_models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path or Path("data/voice_models/speaker_models.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.voice_processor = VoiceProcessor(self.models_dir)
        
        # Initialize database
        self._init_database()
        
        # Integration with Phase 6A corrections
        self.corrections_db_path = Path("output/corrections.db")
    
    def _init_database(self):
        """Initialize speaker models database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS speaker_models (
                    id TEXT PRIMARY KEY,
                    senator_name TEXT NOT NULL UNIQUE,
                    model_path TEXT NOT NULL,
                    training_samples INTEGER DEFAULT 0,
                    accuracy_score REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    is_active BOOLEAN DEFAULT 1
                );
                
                CREATE TABLE IF NOT EXISTS voice_samples (
                    id TEXT PRIMARY KEY,
                    senator_name TEXT NOT NULL,
                    sample_path TEXT NOT NULL,
                    source TEXT NOT NULL,
                    duration REAL DEFAULT 0.0,
                    quality_score REAL DEFAULT 0.0,
                    feature_vector_path TEXT,
                    created_at TEXT NOT NULL,
                    is_processed BOOLEAN DEFAULT 0,
                    FOREIGN KEY (senator_name) REFERENCES speaker_models (senator_name)
                );
                
                CREATE TABLE IF NOT EXISTS recognition_results (
                    id TEXT PRIMARY KEY,
                    audio_segment_id TEXT,
                    recognized_speaker TEXT,
                    confidence_score REAL DEFAULT 0.0,
                    similarity_scores TEXT,  -- JSON of all similarity scores
                    correction_applied BOOLEAN DEFAULT 0,
                    human_verified BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                
                CREATE INDEX IF NOT EXISTS idx_speaker_models_senator 
                ON speaker_models(senator_name);
                
                CREATE INDEX IF NOT EXISTS idx_voice_samples_senator 
                ON voice_samples(senator_name);
                
                CREATE INDEX IF NOT EXISTS idx_recognition_results_speaker 
                ON recognition_results(recognized_speaker);
            """)
    
    def register_speaker_model(
        self, 
        senator_name: str, 
        model_metadata: Dict[str, Any]
    ) -> str:
        """Register a new speaker voice model."""
        try:
            model_id = f"model_{senator_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            timestamp = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                # Check if model already exists
                existing = conn.execute(
                    "SELECT id FROM speaker_models WHERE senator_name = ? AND is_active = 1",
                    (senator_name,)
                ).fetchone()
                
                if existing:
                    # Deactivate old model
                    conn.execute(
                        "UPDATE speaker_models SET is_active = 0, updated_at = ? WHERE senator_name = ?",
                        (timestamp, senator_name)
                    )
                
                # Insert new model
                conn.execute(
                    "INSERT INTO speaker_models "
                    "(id, senator_name, model_path, training_samples, accuracy_score, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        model_id,
                        senator_name,
                        model_metadata.get('model_path', ''),
                        model_metadata.get('training_samples', 0),
                        model_metadata.get('log_likelihood', 0.0),
                        timestamp
                    )
                )
                
                logger.info(f"Registered speaker model {model_id} for {senator_name}")
                return model_id
                
        except Exception as e:
            logger.error(f"Error registering speaker model for {senator_name}: {e}")
            raise
    
    def get_speaker_model(self, senator_name: str) -> Optional[Dict[str, Any]]:
        """Get active speaker model for a senator."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                result = conn.execute(
                    "SELECT * FROM speaker_models "
                    "WHERE senator_name = ? AND is_active = 1 "
                    "ORDER BY created_at DESC LIMIT 1",
                    (senator_name,)
                ).fetchone()
                
                if result:
                    return dict(result)
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting speaker model for {senator_name}: {e}")
            return None
    
    def add_voice_sample(
        self, 
        senator_name: str, 
        sample_path: Path, 
        source: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add voice sample to database."""
        try:
            sample_id = f"sample_{senator_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            timestamp = datetime.now().isoformat()
            
            metadata = metadata or {}
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO voice_samples "
                    "(id, senator_name, sample_path, source, duration, quality_score, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        sample_id,
                        senator_name,
                        str(sample_path),
                        source,
                        metadata.get('duration', 0.0),
                        metadata.get('quality_score', 0.0),
                        timestamp
                    )
                )
                
                logger.info(f"Added voice sample {sample_id} for {senator_name}")
                return sample_id
                
        except Exception as e:
            logger.error(f"Error adding voice sample for {senator_name}: {e}")
            raise
    
    def process_voice_samples(self, senator_name: str = None) -> Dict[str, Any]:
        """Process unprocessed voice samples to extract features."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get unprocessed samples
                if senator_name:
                    samples = conn.execute(
                        "SELECT * FROM voice_samples "
                        "WHERE senator_name = ? AND is_processed = 0",
                        (senator_name,)
                    ).fetchall()
                else:
                    samples = conn.execute(
                        "SELECT * FROM voice_samples WHERE is_processed = 0"
                    ).fetchall()
                
                processed_count = 0
                feature_vectors = {}
                
                for sample in samples:
                    try:
                        sample_path = Path(sample['sample_path'])
                        if not sample_path.exists():
                            logger.warning(f"Sample file not found: {sample_path}")
                            continue
                        
                        # Extract features
                        features = self.voice_processor.extract_voice_features(sample_path)
                        
                        if features and features.get('quality_score', 0) >= 0.3:  # Minimum quality
                            # Save feature vector
                            feature_path = self._save_feature_vector(
                                sample['id'], 
                                features['feature_vector']
                            )
                            
                            # Update sample as processed
                            conn.execute(
                                "UPDATE voice_samples "
                                "SET is_processed = 1, feature_vector_path = ?, quality_score = ? "
                                "WHERE id = ?",
                                (str(feature_path), features['quality_score'], sample['id'])
                            )
                            
                            # Collect for model training
                            senator = sample['senator_name']
                            if senator not in feature_vectors:
                                feature_vectors[senator] = []
                            
                            feature_vectors[senator].append(features['feature_vector'])
                            processed_count += 1
                            
                        else:
                            logger.warning(f"Low quality sample skipped: {sample['id']}")
                    
                    except Exception as e:
                        logger.error(f"Error processing sample {sample['id']}: {e}")
                        continue
                
                logger.info(f"Processed {processed_count} voice samples")
                return {
                    'processed_samples': processed_count,
                    'feature_vectors': feature_vectors,
                    'senators_updated': list(feature_vectors.keys())
                }
                
        except Exception as e:
            logger.error(f"Error processing voice samples: {e}")
            return {'processed_samples': 0, 'error': str(e)}
    
    def _save_feature_vector(self, sample_id: str, feature_vector: np.ndarray) -> Path:
        """Save feature vector to disk."""
        feature_dir = self.models_dir / "features"
        feature_dir.mkdir(exist_ok=True)
        
        feature_path = feature_dir / f"{sample_id}_features.npy"
        np.save(feature_path, feature_vector)
        
        return feature_path
    
    def update_speaker_models(self, senators: List[str] = None) -> Dict[str, Any]:
        """Update speaker models with new voice samples."""
        try:
            results = {}
            
            # Process samples first
            processing_results = self.process_voice_samples()
            feature_vectors = processing_results.get('feature_vectors', {})
            
            senators_to_update = senators or list(feature_vectors.keys())
            
            for senator_name in senators_to_update:
                try:
                    # Get all feature vectors for senator
                    senator_features = self._get_senator_feature_vectors(senator_name)
                    
                    if len(senator_features) >= self.voice_processor.min_training_samples:
                        # Create/update voice model
                        voice_model = self.voice_processor.create_speaker_model(
                            senator_name, 
                            senator_features
                        )
                        
                        if voice_model:
                            # Register model in database
                            model_id = self.register_speaker_model(senator_name, voice_model)
                            
                            results[senator_name] = {
                                'status': 'success',
                                'model_id': model_id,
                                'training_samples': len(senator_features),
                                'accuracy_score': voice_model.get('log_likelihood', 0.0)
                            }
                        else:
                            results[senator_name] = {
                                'status': 'failed',
                                'error': 'Model creation failed'
                            }
                    else:
                        results[senator_name] = {
                            'status': 'insufficient_data',
                            'available_samples': len(senator_features),
                            'required_samples': self.voice_processor.min_training_samples
                        }
                
                except Exception as e:
                    logger.error(f"Error updating model for {senator_name}: {e}")
                    results[senator_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            logger.info(f"Updated speaker models for {len(results)} senators")
            return results
            
        except Exception as e:
            logger.error(f"Error updating speaker models: {e}")
            return {'error': str(e)}
    
    def _get_senator_feature_vectors(self, senator_name: str) -> List[np.ndarray]:
        """Get all feature vectors for a senator."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                samples = conn.execute(
                    "SELECT feature_vector_path FROM voice_samples "
                    "WHERE senator_name = ? AND is_processed = 1 AND feature_vector_path IS NOT NULL",
                    (senator_name,)
                ).fetchall()
                
                feature_vectors = []
                for sample in samples:
                    feature_path = Path(sample['feature_vector_path'])
                    if feature_path.exists():
                        features = np.load(feature_path)
                        feature_vectors.append(features)
                
                return feature_vectors
                
        except Exception as e:
            logger.error(f"Error getting feature vectors for {senator_name}: {e}")
            return []
    
    def recognize_speaker_in_audio(
        self, 
        audio_segment_path: Path,
        candidate_senators: List[str] = None
    ) -> Dict[str, Any]:
        """Recognize speaker in audio segment using voice models."""
        try:
            logger.info(f"Recognizing speaker in {audio_segment_path}")
            
            # Extract features from audio segment
            features = self.voice_processor.extract_voice_features(audio_segment_path)
            
            if not features:
                return {
                    'recognized_speaker': None,
                    'confidence_score': 0.0,
                    'error': 'Feature extraction failed'
                }
            
            # Identify speaker
            similarities = self.voice_processor.identify_speaker(
                features['feature_vector'], 
                candidate_senators
            )
            
            if not similarities:
                return {
                    'recognized_speaker': None,
                    'confidence_score': 0.0,
                    'error': 'No speaker models available'
                }
            
            # Get best match
            best_match = similarities[0]
            
            # Save recognition result
            result_id = self._save_recognition_result(audio_segment_path, similarities)
            
            return {
                'recognized_speaker': best_match['senator_name'],
                'confidence_score': best_match['similarity_score'],
                'confidence_level': best_match['confidence_level'],
                'all_similarities': similarities,
                'result_id': result_id,
                'audio_quality': features.get('quality_score', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error recognizing speaker in {audio_segment_path}: {e}")
            return {
                'recognized_speaker': None,
                'confidence_score': 0.0,
                'error': str(e)
            }
    
    def _save_recognition_result(
        self, 
        audio_segment_path: Path, 
        similarities: List[Dict[str, Any]]
    ) -> str:
        """Save speaker recognition result to database."""
        try:
            result_id = f"recognition_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            timestamp = datetime.now().isoformat()
            
            best_match = similarities[0] if similarities else {}
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO recognition_results "
                    "(id, audio_segment_id, recognized_speaker, confidence_score, "
                    "similarity_scores, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        result_id,
                        str(audio_segment_path),
                        best_match.get('senator_name'),
                        best_match.get('similarity_score', 0.0),
                        json.dumps(similarities),
                        timestamp
                    )
                )
            
            return result_id
            
        except Exception as e:
            logger.error(f"Error saving recognition result: {e}")
            return ""
    
    def integrate_with_phase6a_corrections(self) -> Dict[str, Any]:
        """Integrate with Phase 6A human corrections for learning."""
        try:
            if not self.corrections_db_path.exists():
                return {'error': 'Phase 6A corrections database not found'}
            
            # Get corrections from Phase 6A
            with sqlite3.connect(self.corrections_db_path) as corrections_conn:
                corrections_conn.row_factory = sqlite3.Row
                
                corrections = corrections_conn.execute(
                    "SELECT * FROM corrections WHERE is_active = 1"
                ).fetchall()
                
                learning_data = []
                for correction in corrections:
                    learning_data.append({
                        'transcript_file': correction['transcript_file'],
                        'segment_id': correction['segment_id'],
                        'correct_speaker': correction['speaker_name'],
                        'confidence': correction['confidence'],
                        'reviewer_id': correction['reviewer_id']
                    })
            
            # Update recognition results with human feedback
            with sqlite3.connect(self.db_path) as conn:
                for correction in learning_data:
                    # Mark as human verified if we have a recognition result
                    conn.execute(
                        "UPDATE recognition_results "
                        "SET human_verified = 1, correction_applied = 1 "
                        "WHERE audio_segment_id LIKE ? AND recognized_speaker != ?",
                        (f"%{correction['transcript_file']}%", correction['correct_speaker'])
                    )
            
            logger.info(f"Integrated {len(learning_data)} Phase 6A corrections")
            return {
                'corrections_processed': len(learning_data),
                'integration_status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error integrating Phase 6A corrections: {e}")
            return {'error': str(e)}
    
    def get_model_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all speaker models."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Model statistics
                models = conn.execute(
                    "SELECT senator_name, training_samples, accuracy_score, created_at "
                    "FROM speaker_models WHERE is_active = 1"
                ).fetchall()
                
                # Recognition statistics
                recognition_stats = conn.execute("""
                    SELECT 
                        recognized_speaker,
                        COUNT(*) as total_recognitions,
                        AVG(confidence_score) as avg_confidence,
                        SUM(CASE WHEN human_verified = 1 AND correction_applied = 0 THEN 1 ELSE 0 END) as correct_recognitions,
                        SUM(CASE WHEN human_verified = 1 THEN 1 ELSE 0 END) as verified_recognitions
                    FROM recognition_results 
                    WHERE recognized_speaker IS NOT NULL
                    GROUP BY recognized_speaker
                """).fetchall()
                
                # Sample statistics
                sample_stats = conn.execute("""
                    SELECT 
                        senator_name,
                        COUNT(*) as total_samples,
                        SUM(CASE WHEN is_processed = 1 THEN 1 ELSE 0 END) as processed_samples,
                        AVG(quality_score) as avg_quality
                    FROM voice_samples
                    GROUP BY senator_name
                """).fetchall()
                
                return {
                    'models': [dict(model) for model in models],
                    'recognition_stats': [dict(stat) for stat in recognition_stats],
                    'sample_stats': [dict(stat) for stat in sample_stats],
                    'total_models': len(models),
                    'total_recognitions': sum(stat['total_recognitions'] for stat in recognition_stats)
                }
                
        except Exception as e:
            logger.error(f"Error getting model performance stats: {e}")
            return {'error': str(e)}


if __name__ == "__main__":
    # Test speaker model manager
    manager = SpeakerModelManager()
    
    # Get performance stats
    stats = manager.get_model_performance_stats()
    print(f"Speaker models statistics: {stats}")
    
    # Test Phase 6A integration
    integration_result = manager.integrate_with_phase6a_corrections()
    print(f"Phase 6A integration: {integration_result}")