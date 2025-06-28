#!/usr/bin/env python3
"""
Threshold Optimizer for Phase 6C

Automatically optimizes confidence thresholds for speaker identification:
- Multi-objective optimization (accuracy vs. coverage)
- Dynamic threshold adjustment based on performance
- A/B testing framework for threshold changes
- Automated rollback for performance degradation
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy import optimize
from sklearn.metrics import precision_recall_curve, roc_curve, auc
import pickle

logger = logging.getLogger(__name__)


class ThresholdOptimizer:
    """Optimizes confidence thresholds for speaker identification system."""
    
    def __init__(self, 
                 voice_models_db_path: Path = None,
                 corrections_db_path: Path = None,
                 config_path: Path = None):
        """Initialize threshold optimizer."""
        self.voice_models_db_path = voice_models_db_path or Path("data/voice_models/speaker_models.db")
        self.corrections_db_path = corrections_db_path or Path("output/corrections.db")
        self.config_path = config_path or Path("data/learning/threshold_config.json")
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Current thresholds configuration
        self.current_thresholds = self._load_threshold_config()
        
        # Optimization parameters
        self.optimization_weights = {
            'accuracy': 0.4,
            'coverage': 0.3,
            'f1_score': 0.3
        }
        
        # A/B testing configuration
        self.ab_test_duration_hours = 24
        self.min_samples_for_ab_test = 50
        self.performance_degradation_threshold = 0.05  # 5% drop triggers rollback
        
        # Performance tracking
        self.performance_history = []
        
    def _load_threshold_config(self) -> Dict[str, Any]:
        """Load current threshold configuration."""
        default_config = {
            'voice_thresholds': {
                'high_confidence': 0.85,
                'medium_confidence': 0.65,
                'low_confidence': 0.45,
                'minimum_confidence': 0.25
            },
            'text_thresholds': {
                'high_confidence': 0.90,
                'medium_confidence': 0.70,
                'low_confidence': 0.50
            },
            'combined_thresholds': {
                'voice_override': 0.85,
                'voice_boost': 0.65,
                'voice_suggest': 0.45,
                'voice_ignore': 0.25
            },
            'decision_rules': {
                'voice_weight': 0.6,
                'text_weight': 0.4,
                'uncertainty_threshold': 0.3
            },
            'last_updated': datetime.now().isoformat(),
            'optimization_history': []
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                self._save_threshold_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading threshold config: {e}")
            return default_config
    
    def _save_threshold_config(self, config: Dict[str, Any]):
        """Save threshold configuration to file."""
        try:
            config['last_updated'] = datetime.now().isoformat()
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Saved threshold configuration")
        except Exception as e:
            logger.error(f"Error saving threshold config: {e}")
    
    def optimize_thresholds(self, 
                           optimization_target: str = 'balanced',
                           validation_split: float = 0.2) -> Dict[str, Any]:
        """Optimize thresholds using historical performance data."""
        logger.info(f"Starting threshold optimization with target: {optimization_target}")
        
        try:
            # Get performance data
            performance_data = self._get_performance_data()
            
            if len(performance_data) < 20:  # Minimum data requirement
                return {
                    'status': 'insufficient_data',
                    'message': f'Need at least 20 samples, got {len(performance_data)}',
                    'current_thresholds': self.current_thresholds
                }
            
            # Split data for validation
            train_data, val_data = self._split_data(performance_data, validation_split)
            
            # Define optimization objective
            objective_func = self._get_objective_function(optimization_target, train_data)
            
            # Optimize different threshold categories
            optimization_results = {}
            
            # Optimize voice thresholds
            voice_optimal = self._optimize_voice_thresholds(objective_func, train_data)
            optimization_results['voice'] = voice_optimal
            
            # Optimize text thresholds  
            text_optimal = self._optimize_text_thresholds(objective_func, train_data)
            optimization_results['text'] = text_optimal
            
            # Optimize combined decision rules
            combined_optimal = self._optimize_combined_thresholds(objective_func, train_data)
            optimization_results['combined'] = combined_optimal
            
            # Validate optimized thresholds
            validation_results = self._validate_thresholds(optimization_results, val_data)
            
            # Create new threshold configuration
            new_thresholds = self._create_optimized_config(optimization_results)
            
            # Performance comparison
            current_performance = self._evaluate_threshold_performance(
                self.current_thresholds, val_data
            )
            new_performance = self._evaluate_threshold_performance(
                new_thresholds, val_data
            )
            
            improvement = {
                'accuracy_change': new_performance['accuracy'] - current_performance['accuracy'],
                'coverage_change': new_performance['coverage'] - current_performance['coverage'],
                'f1_change': new_performance['f1_score'] - current_performance['f1_score']
            }
            
            # Record optimization in history
            optimization_record = {
                'timestamp': datetime.now().isoformat(),
                'target': optimization_target,
                'data_samples': len(performance_data),
                'old_thresholds': self.current_thresholds.copy(),
                'new_thresholds': new_thresholds,
                'performance_improvement': improvement,
                'validation_results': validation_results
            }
            
            # Update configuration if improvement is significant
            if self._should_apply_optimization(improvement):
                self.current_thresholds.update(new_thresholds)
                self.current_thresholds['optimization_history'].append(optimization_record)
                self._save_threshold_config(self.current_thresholds)
                
                return {
                    'status': 'optimized',
                    'improvement': improvement,
                    'new_thresholds': new_thresholds,
                    'validation_results': validation_results,
                    'applied': True
                }
            else:
                return {
                    'status': 'no_improvement',
                    'improvement': improvement,
                    'new_thresholds': new_thresholds,
                    'validation_results': validation_results,
                    'applied': False
                }
                
        except Exception as e:
            logger.error(f"Error in threshold optimization: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_performance_data(self) -> List[Dict[str, Any]]:
        """Get performance data from recognition and correction databases."""
        try:
            performance_data = []
            
            # Get recognition results
            if self.voice_models_db_path.exists():
                with sqlite3.connect(self.voice_models_db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    recognitions = conn.execute("""
                        SELECT * FROM recognition_results
                        WHERE confidence_score IS NOT NULL
                        ORDER BY created_at DESC
                        LIMIT 1000
                    """).fetchall()
                    
                    for recognition in recognitions:
                        # Convert sqlite3.Row to dict for easier access
                        row_dict = dict(recognition)
                        
                        data_point = {
                            'voice_confidence': row_dict.get('confidence_score', 0),
                            'recognized_speaker': row_dict.get('recognized_speaker'),
                            'was_corrected': row_dict.get('correction_applied', False),
                            'human_verified': row_dict.get('human_verified', False),
                            'audio_segment_id': row_dict.get('audio_segment_id'),
                            'timestamp': row_dict.get('created_at')
                        }
                        
                        # Add similarity scores if available
                        if row_dict.get('similarity_scores'):
                            try:
                                similarities = json.loads(row_dict['similarity_scores'])
                                if similarities:
                                    data_point['text_confidence'] = self._extract_text_confidence(similarities)
                                    data_point['similarity_scores'] = similarities
                            except:
                                pass
                        
                        performance_data.append(data_point)
            
            # Enrich with correction data
            if self.corrections_db_path.exists():
                with sqlite3.connect(self.corrections_db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    corrections = conn.execute("""
                        SELECT * FROM corrections WHERE is_active = 1
                    """).fetchall()
                    
                    # Create lookup for corrections
                    corrections_lookup = {}
                    for correction in corrections:
                        key = (correction['transcript_file'], correction['segment_id'])
                        corrections_lookup[key] = {
                            'correct_speaker': correction['speaker_name'],
                            'correction_confidence': correction['confidence'],
                            'reviewer_id': correction['reviewer_id']
                        }
                    
                    # Match corrections to recognition data
                    for data_point in performance_data:
                        segment_id = self._extract_segment_id(data_point.get('audio_segment_id', ''))
                        transcript_file = self._extract_transcript_file(data_point.get('audio_segment_id', ''))
                        
                        correction_key = (transcript_file, segment_id)
                        if correction_key in corrections_lookup:
                            correction_info = corrections_lookup[correction_key]
                            data_point.update(correction_info)
                            data_point['is_correct'] = (
                                data_point['recognized_speaker'] == correction_info['correct_speaker']
                            )
                        else:
                            # Assume correct if not corrected and human verified
                            data_point['is_correct'] = (
                                data_point['human_verified'] and not data_point['was_corrected']
                            )
            
            logger.info(f"Collected {len(performance_data)} performance data points")
            return performance_data
            
        except Exception as e:
            logger.error(f"Error getting performance data: {e}")
            return []
    
    def _extract_text_confidence(self, similarities: List[Dict]) -> float:
        """Extract text-based confidence from similarity scores."""
        # Simple heuristic - can be enhanced with actual text confidence scores
        if not similarities:
            return 0.5
        
        best_similarity = similarities[0].get('similarity_score', 0)
        return min(best_similarity + 0.2, 1.0)  # Boost for text patterns
    
    def _extract_segment_id(self, audio_segment_id: str) -> int:
        """Extract segment ID from audio segment identifier."""
        try:
            # Extract segment ID from filename pattern
            parts = audio_segment_id.split('_')
            for part in parts:
                if part.startswith('segment'):
                    return int(part.replace('segment', ''))
            return 0
        except:
            return 0
    
    def _extract_transcript_file(self, audio_segment_id: str) -> str:
        """Extract transcript filename from audio segment identifier."""
        try:
            # Simple extraction - enhance based on actual naming patterns
            if '/' in audio_segment_id:
                return audio_segment_id.split('/')[-1].replace('.wav', '.json')
            return audio_segment_id
        except:
            return ""
    
    def _split_data(self, data: List[Dict], validation_split: float) -> Tuple[List[Dict], List[Dict]]:
        """Split data into training and validation sets."""
        split_index = int(len(data) * (1 - validation_split))
        return data[:split_index], data[split_index:]
    
    def _get_objective_function(self, target: str, data: List[Dict]):
        """Get optimization objective function based on target."""
        def objective(thresholds_array):
            voice_thresh, text_thresh, combined_thresh = thresholds_array
            
            # Evaluate performance with these thresholds
            performance = self._evaluate_threshold_array(
                voice_thresh, text_thresh, combined_thresh, data
            )
            
            if target == 'accuracy':
                return -performance['accuracy']  # Negative for minimization
            elif target == 'coverage':
                return -performance['coverage']
            elif target == 'f1':
                return -performance['f1_score']
            else:  # balanced
                return -(
                    self.optimization_weights['accuracy'] * performance['accuracy'] +
                    self.optimization_weights['coverage'] * performance['coverage'] +
                    self.optimization_weights['f1_score'] * performance['f1_score']
                )
        
        return objective
    
    def _optimize_voice_thresholds(self, objective_func, data: List[Dict]) -> Dict[str, Any]:
        """Optimize voice confidence thresholds."""
        # Current voice thresholds
        current = self.current_thresholds['voice_thresholds']
        
        # Define bounds for optimization
        bounds = [
            (0.1, 0.95),  # high_confidence
            (0.1, 0.85),  # medium_confidence  
            (0.1, 0.75),  # low_confidence
            (0.1, 0.65),  # minimum_confidence
        ]
        
        # Initial guess
        x0 = [
            current['high_confidence'],
            current['medium_confidence'],
            current['low_confidence'],
            current['minimum_confidence']
        ]
        
        # Optimize
        result = optimize.minimize(
            lambda x: objective_func([x[0], 0.5, x[1]]),  # Focus on voice thresholds
            x0[:2],  # Optimize high and medium first
            bounds=bounds[:2],
            method='L-BFGS-B'
        )
        
        if result.success:
            optimized_thresholds = {
                'high_confidence': result.x[0],
                'medium_confidence': result.x[1],
                'low_confidence': max(result.x[1] - 0.2, 0.1),
                'minimum_confidence': max(result.x[1] - 0.4, 0.1)
            }
        else:
            optimized_thresholds = current
        
        return {
            'thresholds': optimized_thresholds,
            'optimization_success': result.success,
            'optimization_result': str(result)
        }
    
    def _optimize_text_thresholds(self, objective_func, data: List[Dict]) -> Dict[str, Any]:
        """Optimize text confidence thresholds."""
        current = self.current_thresholds['text_thresholds']
        
        bounds = [
            (0.1, 0.95),  # high_confidence
            (0.1, 0.85),  # medium_confidence
            (0.1, 0.75),  # low_confidence
        ]
        
        x0 = [
            current['high_confidence'],
            current['medium_confidence'],
            current['low_confidence']
        ]
        
        result = optimize.minimize(
            lambda x: objective_func([0.5, x[0], x[1]]),  # Focus on text thresholds
            x0[:2],
            bounds=bounds[:2],
            method='L-BFGS-B'
        )
        
        if result.success:
            optimized_thresholds = {
                'high_confidence': result.x[0],
                'medium_confidence': result.x[1],
                'low_confidence': max(result.x[1] - 0.2, 0.1)
            }
        else:
            optimized_thresholds = current
        
        return {
            'thresholds': optimized_thresholds,
            'optimization_success': result.success,
            'optimization_result': str(result)
        }
    
    def _optimize_combined_thresholds(self, objective_func, data: List[Dict]) -> Dict[str, Any]:
        """Optimize combined decision thresholds."""
        current = self.current_thresholds['combined_thresholds']
        
        bounds = [
            (0.1, 0.95),  # voice_override
            (0.1, 0.85),  # voice_boost
            (0.1, 0.75),  # voice_suggest
            (0.1, 0.65),  # voice_ignore
        ]
        
        x0 = [
            current['voice_override'],
            current['voice_boost'],
            current['voice_suggest'],
            current['voice_ignore']
        ]
        
        result = optimize.minimize(
            lambda x: objective_func([x[0], 0.5, x[1]]),
            x0[:2],
            bounds=bounds[:2],
            method='L-BFGS-B'
        )
        
        if result.success:
            optimized_thresholds = {
                'voice_override': result.x[0],
                'voice_boost': result.x[1],
                'voice_suggest': max(result.x[1] - 0.2, 0.1),
                'voice_ignore': max(result.x[1] - 0.4, 0.1)
            }
        else:
            optimized_thresholds = current
        
        return {
            'thresholds': optimized_thresholds,
            'optimization_success': result.success,
            'optimization_result': str(result)
        }
    
    def _evaluate_threshold_array(self, 
                                 voice_thresh: float, 
                                 text_thresh: float, 
                                 combined_thresh: float, 
                                 data: List[Dict]) -> Dict[str, float]:
        """Evaluate performance with given threshold values."""
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0
        covered_samples = 0
        
        for sample in data:
            voice_conf = sample.get('voice_confidence', 0)
            text_conf = sample.get('text_confidence', 0.5)
            is_correct = sample.get('is_correct', False)
            
            # Apply threshold logic
            prediction_made = False
            predicted_correct = False
            
            if voice_conf >= voice_thresh:
                prediction_made = True
                predicted_correct = is_correct
            elif text_conf >= text_thresh:
                prediction_made = True
                predicted_correct = is_correct
            elif (voice_conf + text_conf) / 2 >= combined_thresh:
                prediction_made = True
                predicted_correct = is_correct
            
            if prediction_made:
                covered_samples += 1
                if predicted_correct and is_correct:
                    true_positives += 1
                elif predicted_correct and not is_correct:
                    false_positives += 1
                elif not predicted_correct and is_correct:
                    false_negatives += 1
                else:
                    true_negatives += 1
        
        # Calculate metrics
        total_samples = len(data)
        coverage = covered_samples / total_samples if total_samples > 0 else 0
        
        if (true_positives + false_positives) > 0:
            precision = true_positives / (true_positives + false_positives)
        else:
            precision = 0
        
        if (true_positives + false_negatives) > 0:
            recall = true_positives / (true_positives + false_negatives)
        else:
            recall = 0
        
        if covered_samples > 0:
            accuracy = (true_positives + true_negatives) / covered_samples
        else:
            accuracy = 0
        
        if (precision + recall) > 0:
            f1_score = 2 * (precision * recall) / (precision + recall)
        else:
            f1_score = 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'coverage': coverage,
            'f1_score': f1_score
        }
    
    def _validate_thresholds(self, 
                            optimization_results: Dict[str, Any], 
                            validation_data: List[Dict]) -> Dict[str, Any]:
        """Validate optimized thresholds on validation data."""
        # Create test configuration
        test_config = self._create_optimized_config(optimization_results)
        
        # Evaluate on validation data
        performance = self._evaluate_threshold_performance(test_config, validation_data)
        
        return {
            'validation_performance': performance,
            'validation_samples': len(validation_data),
            'meets_quality_threshold': performance['accuracy'] >= 0.7,  # 70% minimum accuracy
        }
    
    def _create_optimized_config(self, optimization_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create new threshold configuration from optimization results."""
        new_config = self.current_thresholds.copy()
        
        if 'voice' in optimization_results and optimization_results['voice']['optimization_success']:
            new_config['voice_thresholds'].update(optimization_results['voice']['thresholds'])
        
        if 'text' in optimization_results and optimization_results['text']['optimization_success']:
            new_config['text_thresholds'].update(optimization_results['text']['thresholds'])
        
        if 'combined' in optimization_results and optimization_results['combined']['optimization_success']:
            new_config['combined_thresholds'].update(optimization_results['combined']['thresholds'])
        
        return new_config
    
    def _evaluate_threshold_performance(self, 
                                       config: Dict[str, Any], 
                                       data: List[Dict]) -> Dict[str, float]:
        """Evaluate performance of a threshold configuration."""
        voice_thresh = config['voice_thresholds']['high_confidence']
        text_thresh = config['text_thresholds']['high_confidence']
        combined_thresh = config['combined_thresholds']['voice_boost']
        
        return self._evaluate_threshold_array(voice_thresh, text_thresh, combined_thresh, data)
    
    def _should_apply_optimization(self, improvement: Dict[str, float]) -> bool:
        """Determine if optimization should be applied based on improvement metrics."""
        # Apply if any significant improvement (>2%) without significant degradation (>1%) in others
        significant_improvement = any(
            improvement[metric] > 0.02 
            for metric in ['accuracy_change', 'coverage_change', 'f1_change']
        )
        
        no_significant_degradation = all(
            improvement[metric] > -0.01
            for metric in ['accuracy_change', 'coverage_change', 'f1_change']
        )
        
        return significant_improvement and no_significant_degradation
    
    def start_ab_test(self, 
                     new_thresholds: Dict[str, Any], 
                     test_name: str = None) -> Dict[str, Any]:
        """Start A/B test for new threshold configuration."""
        test_id = f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_name = test_name or f"Threshold optimization test {test_id}"
        
        ab_test_config = {
            'test_id': test_id,
            'test_name': test_name,
            'start_time': datetime.now().isoformat(),
            'end_time': (datetime.now() + timedelta(hours=self.ab_test_duration_hours)).isoformat(),
            'control_thresholds': self.current_thresholds.copy(),
            'treatment_thresholds': new_thresholds,
            'status': 'active',
            'traffic_split': 0.5,  # 50/50 split
            'performance_metrics': {
                'control': {'samples': 0, 'accuracy': 0, 'coverage': 0},
                'treatment': {'samples': 0, 'accuracy': 0, 'coverage': 0}
            }
        }
        
        # Save A/B test configuration
        ab_test_path = Path(f"data/learning/ab_tests/{test_id}.json")
        ab_test_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(ab_test_path, 'w') as f:
            json.dump(ab_test_config, f, indent=2)
        
        logger.info(f"Started A/B test {test_id} for {self.ab_test_duration_hours} hours")
        
        return {
            'test_id': test_id,
            'status': 'started',
            'duration_hours': self.ab_test_duration_hours,
            'config_path': str(ab_test_path)
        }
    
    def evaluate_ab_test(self, test_id: str) -> Dict[str, Any]:
        """Evaluate results of an A/B test."""
        ab_test_path = Path(f"data/learning/ab_tests/{test_id}.json")
        
        if not ab_test_path.exists():
            return {'status': 'not_found', 'error': f'A/B test {test_id} not found'}
        
        try:
            with open(ab_test_path, 'r') as f:
                ab_test_config = json.load(f)
            
            # Check if test is complete
            end_time = datetime.fromisoformat(ab_test_config['end_time'])
            if datetime.now() < end_time:
                return {
                    'status': 'in_progress',
                    'time_remaining': str(end_time - datetime.now()),
                    'current_metrics': ab_test_config['performance_metrics']
                }
            
            # Evaluate test results
            control_performance = ab_test_config['performance_metrics']['control']
            treatment_performance = ab_test_config['performance_metrics']['treatment']
            
            # Calculate statistical significance (simple t-test approximation)
            improvement = {
                'accuracy': treatment_performance['accuracy'] - control_performance['accuracy'],
                'coverage': treatment_performance['coverage'] - control_performance['coverage']
            }
            
            # Determine winner
            significant_improvement = improvement['accuracy'] > 0.02  # 2% improvement threshold
            winner = 'treatment' if significant_improvement else 'control'
            
            # Update test config with results
            ab_test_config['status'] = 'completed'
            ab_test_config['winner'] = winner
            ab_test_config['improvement'] = improvement
            ab_test_config['significant'] = significant_improvement
            
            with open(ab_test_path, 'w') as f:
                json.dump(ab_test_config, f, indent=2)
            
            return {
                'status': 'completed',
                'winner': winner,
                'improvement': improvement,
                'significant': significant_improvement,
                'recommendation': 'apply_treatment' if winner == 'treatment' else 'keep_control'
            }
            
        except Exception as e:
            logger.error(f"Error evaluating A/B test {test_id}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_threshold_recommendations(self) -> Dict[str, Any]:
        """Get current threshold recommendations based on recent performance."""
        try:
            performance_data = self._get_performance_data()
            
            if len(performance_data) < 10:
                return {
                    'status': 'insufficient_data',
                    'message': 'Need more performance data for recommendations'
                }
            
            # Analyze current performance
            current_performance = self._evaluate_threshold_performance(
                self.current_thresholds, performance_data
            )
            
            recommendations = []
            
            # Check accuracy threshold
            if current_performance['accuracy'] < 0.8:
                recommendations.append({
                    'type': 'accuracy_improvement',
                    'message': f"Current accuracy ({current_performance['accuracy']:.2%}) below target (80%)",
                    'suggestion': 'Increase voice_override threshold',
                    'priority': 'high'
                })
            
            # Check coverage threshold
            if current_performance['coverage'] < 0.7:
                recommendations.append({
                    'type': 'coverage_improvement',
                    'message': f"Current coverage ({current_performance['coverage']:.2%}) below target (70%)",
                    'suggestion': 'Decrease minimum confidence thresholds',
                    'priority': 'medium'
                })
            
            # Check for potential over-optimization
            if current_performance['accuracy'] > 0.95:
                recommendations.append({
                    'type': 'over_optimization',
                    'message': f"Very high accuracy ({current_performance['accuracy']:.2%}) may indicate over-fitting",
                    'suggestion': 'Consider lowering thresholds to improve coverage',
                    'priority': 'low'
                })
            
            return {
                'status': 'success',
                'current_performance': current_performance,
                'recommendations': recommendations,
                'data_samples': len(performance_data),
                'next_optimization_recommended': len(recommendations) > 0
            }
            
        except Exception as e:
            logger.error(f"Error getting threshold recommendations: {e}")
            return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    # Test threshold optimizer
    optimizer = ThresholdOptimizer()
    
    # Get current recommendations
    recommendations = optimizer.get_threshold_recommendations()
    print(f"Threshold recommendations: {json.dumps(recommendations, indent=2)}")
    
    # Run optimization if recommended
    if recommendations.get('next_optimization_recommended'):
        optimization_result = optimizer.optimize_thresholds('balanced')
        print(f"Optimization result: {json.dumps(optimization_result, indent=2)}")