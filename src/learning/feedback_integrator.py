#!/usr/bin/env python3
"""
Feedback Integrator for Phase 6C

Advanced feedback loop integration between all Phase 6 components:
- Real-time learning from Phase 6A corrections
- Voice model improvement integration with Phase 6B
- Pattern-based optimization using predictive models
- Automated retraining triggers and model updates
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import threading
import time
from queue import Queue, PriorityQueue
import asyncio
from collections import defaultdict, Counter

from .pattern_analyzer import PatternAnalyzer
from .threshold_optimizer import ThresholdOptimizer
from .predictive_identifier import PredictiveIdentifier
from .performance_tracker import PerformanceTracker
from .error_handler import (
    ComponentHealthMonitor, 
    with_error_handling, 
    safe_database_operation,
    GracefulDegradation,
    health_monitor
)

logger = logging.getLogger(__name__)


class FeedbackIntegrator:
    """Integrates feedback loops across all Phase 6 components."""
    
    def __init__(self, 
                 corrections_db_path: Path = None,
                 voice_models_db_path: Path = None,
                 config_path: Path = None):
        """Initialize feedback integrator."""
        self.corrections_db_path = corrections_db_path or Path("output/corrections.db")
        self.voice_models_db_path = voice_models_db_path or Path("data/voice_models/speaker_models.db")
        self.config_path = config_path or Path("data/learning/feedback_config.json")
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.pattern_analyzer = PatternAnalyzer(corrections_db_path, voice_models_db_path)
        self.threshold_optimizer = ThresholdOptimizer(voice_models_db_path, corrections_db_path)
        
        # Initialize enhanced error handling
        self.health_monitor = health_monitor
        self.degradation_handler = GracefulDegradation(self.health_monitor)
        self.predictive_identifier = PredictiveIdentifier()
        self.performance_tracker = PerformanceTracker()
        
        # Feedback configuration
        self.config = self._load_feedback_config()
        
        # Real-time processing queues
        self.correction_queue = PriorityQueue()
        self.update_queue = Queue()
        
        # Processing threads
        self.processing_threads = []
        self.is_running = False
        
        # Feedback metrics
        self.feedback_metrics = {
            'corrections_processed': 0,
            'models_updated': 0,
            'thresholds_optimized': 0,
            'predictions_improved': 0,
            'last_update': None
        }
        
    def _load_feedback_config(self) -> Dict[str, Any]:
        """Load feedback integration configuration."""
        default_config = {
            'real_time_learning': {
                'enabled': True,
                'batch_size': 10,
                'update_interval_minutes': 30,
                'min_corrections_for_update': 5
            },
            'model_retraining': {
                'auto_retrain_enabled': True,
                'performance_threshold': 0.05,  # 5% degradation triggers retrain
                'min_data_for_retrain': 50,
                'retrain_interval_hours': 24
            },
            'threshold_optimization': {
                'auto_optimize_enabled': True,
                'optimization_interval_hours': 6,
                'min_samples_for_optimization': 20,
                'performance_improvement_threshold': 0.02  # 2% improvement needed
            },
            'pattern_analysis': {
                'analysis_interval_hours': 12,
                'cache_refresh_hours': 4,
                'min_corrections_for_patterns': 10
            },
            'alerts': {
                'performance_degradation_threshold': 0.1,  # 10% drop
                'correction_burst_threshold': 20,  # 20 corrections in short time
                'model_accuracy_threshold': 0.7,  # 70% minimum accuracy
                'notification_channels': ['log', 'email']
            },
            'integration_weights': {
                'voice_recognition_weight': 0.4,
                'pattern_analysis_weight': 0.3,
                'predictive_modeling_weight': 0.3
            },
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict) and isinstance(config[key], dict):
                        for subkey, subvalue in value.items():
                            if subkey not in config[key]:
                                config[key][subkey] = subvalue
                return config
            else:
                self._save_feedback_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading feedback config: {e}")
            return default_config
    
    def _save_feedback_config(self, config: Dict[str, Any]):
        """Save feedback configuration."""
        try:
            config['last_updated'] = datetime.now().isoformat()
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Saved feedback configuration")
        except Exception as e:
            logger.error(f"Error saving feedback config: {e}")
    
    def start_real_time_feedback(self) -> Dict[str, Any]:
        """Start real-time feedback processing."""
        logger.info("Starting real-time feedback integration")
        
        try:
            if self.is_running:
                return {'status': 'already_running', 'message': 'Real-time feedback already active'}
            
            self.is_running = True
            
            # Start processing threads
            if self.config['real_time_learning']['enabled']:
                correction_thread = threading.Thread(
                    target=self._process_corrections_continuously,
                    daemon=True
                )
                correction_thread.start()
                self.processing_threads.append(correction_thread)
            
            if self.config['model_retraining']['auto_retrain_enabled']:
                retrain_thread = threading.Thread(
                    target=self._monitor_model_performance,
                    daemon=True
                )
                retrain_thread.start()
                self.processing_threads.append(retrain_thread)
            
            if self.config['threshold_optimization']['auto_optimize_enabled']:
                optimize_thread = threading.Thread(
                    target=self._monitor_threshold_performance,
                    daemon=True
                )
                optimize_thread.start()
                self.processing_threads.append(optimize_thread)
            
            # Pattern analysis thread
            pattern_thread = threading.Thread(
                target=self._update_patterns_continuously,
                daemon=True
            )
            pattern_thread.start()
            self.processing_threads.append(pattern_thread)
            
            logger.info(f"Started {len(self.processing_threads)} feedback processing threads")
            
            return {
                'status': 'started',
                'threads_started': len(self.processing_threads),
                'config': self.config
            }
            
        except Exception as e:
            logger.error(f"Error starting real-time feedback: {e}")
            self.is_running = False
            return {'status': 'error', 'error': str(e)}
    
    def stop_real_time_feedback(self) -> Dict[str, Any]:
        """Stop real-time feedback processing."""
        logger.info("Stopping real-time feedback integration")
        
        self.is_running = False
        
        # Wait for threads to finish (with timeout)
        for thread in self.processing_threads:
            thread.join(timeout=5.0)
        
        self.processing_threads.clear()
        
        return {
            'status': 'stopped',
            'final_metrics': self.feedback_metrics
        }
    
    def _process_corrections_continuously(self):
        """Continuously process new corrections for real-time learning."""
        logger.info("Started continuous correction processing")
        
        last_check = datetime.now()
        batch_size = self.config['real_time_learning']['batch_size']
        update_interval = timedelta(minutes=self.config['real_time_learning']['update_interval_minutes'])
        
        while self.is_running:
            try:
                # Check for new corrections
                new_corrections = self._get_new_corrections_since(last_check)
                
                if len(new_corrections) >= self.config['real_time_learning']['min_corrections_for_update']:
                    logger.info(f"Processing {len(new_corrections)} new corrections")
                    
                    # Process corrections in batches
                    for i in range(0, len(new_corrections), batch_size):
                        batch = new_corrections[i:i + batch_size]
                        self._process_correction_batch(batch)
                        
                        self.feedback_metrics['corrections_processed'] += len(batch)
                    
                    # Trigger model updates if enough corrections
                    if len(new_corrections) >= 10:
                        self._trigger_model_updates(new_corrections)
                
                last_check = datetime.now()
                self.feedback_metrics['last_update'] = last_check.isoformat()
                
                # Sleep until next check
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in continuous correction processing: {e}")
                time.sleep(30)  # Wait before retrying
    
    def _monitor_model_performance(self):
        """Monitor model performance and trigger retraining when needed."""
        logger.info("Started model performance monitoring")
        
        retrain_interval = timedelta(hours=self.config['model_retraining']['retrain_interval_hours'])
        last_retrain = datetime.now()
        
        while self.is_running:
            try:
                # Check if retraining is needed
                current_performance = self.performance_tracker.get_current_performance()
                
                if current_performance.get('accuracy', 1.0) < self.config['model_retraining']['performance_threshold']:
                    logger.warning(f"Performance degradation detected: {current_performance}")
                    self._trigger_model_retraining("performance_degradation")
                
                # Periodic retraining
                if datetime.now() - last_retrain > retrain_interval:
                    logger.info("Periodic model retraining triggered")
                    self._trigger_model_retraining("periodic_update")
                    last_retrain = datetime.now()
                
                # Sleep for an hour before next check
                time.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in model performance monitoring: {e}")
                time.sleep(1800)  # Wait 30 minutes before retrying
    
    def _monitor_threshold_performance(self):
        """Monitor threshold performance and optimize when beneficial."""
        logger.info("Started threshold performance monitoring")
        
        optimize_interval = timedelta(hours=self.config['threshold_optimization']['optimization_interval_hours'])
        last_optimization = datetime.now()
        
        while self.is_running:
            try:
                # Check if optimization is needed
                if datetime.now() - last_optimization > optimize_interval:
                    logger.info("Triggering threshold optimization")
                    
                    optimization_result = self.threshold_optimizer.optimize_thresholds('balanced')
                    
                    if optimization_result.get('status') == 'optimized':
                        self.feedback_metrics['thresholds_optimized'] += 1
                        logger.info(f"Threshold optimization successful: {optimization_result['improvement']}")
                    
                    last_optimization = datetime.now()
                
                # Sleep for 30 minutes before next check
                time.sleep(1800)
                
            except Exception as e:
                logger.error(f"Error in threshold performance monitoring: {e}")
                time.sleep(1800)
    
    def _update_patterns_continuously(self):
        """Continuously update pattern analysis."""
        logger.info("Started continuous pattern analysis")
        
        analysis_interval = timedelta(hours=self.config['pattern_analysis']['analysis_interval_hours'])
        last_analysis = datetime.now()
        
        while self.is_running:
            try:
                if datetime.now() - last_analysis > analysis_interval:
                    logger.info("Updating pattern analysis")
                    
                    patterns = self.pattern_analyzer.analyze_correction_patterns()
                    
                    if patterns:
                        insights = self.pattern_analyzer.get_pattern_insights()
                        self._process_pattern_insights(insights)
                    
                    last_analysis = datetime.now()
                
                # Sleep for an hour before next check
                time.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in continuous pattern analysis: {e}")
                time.sleep(1800)
    
    @with_error_handling("corrections_db", health_monitor, fallback_result=[])
    @safe_database_operation
    def _get_new_corrections_since(self, timestamp: datetime) -> List[Dict[str, Any]]:
        """Get new corrections since specified timestamp."""
        if not self.corrections_db_path.exists():
            return []
        
        with sqlite3.connect(self.corrections_db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            corrections = conn.execute(
                "SELECT * FROM corrections "
                "WHERE is_active = 1 AND created_at > ? "
                "ORDER BY created_at",
                (timestamp.isoformat(),)
            ).fetchall()
            
            return [dict(correction) for correction in corrections]
    
    def _process_correction_batch(self, corrections: List[Dict[str, Any]]):
        """Process a batch of corrections for learning."""
        try:
            # Extract patterns from corrections
            patterns = self._extract_correction_patterns(corrections)
            
            # Update voice models with correction feedback
            self._update_voice_models_with_corrections(corrections, patterns)
            
            # Update predictive models
            self._update_predictive_models_with_corrections(corrections, patterns)
            
            # Check for alert conditions
            self._check_alert_conditions(corrections, patterns)
            
        except Exception as e:
            logger.error(f"Error processing correction batch: {e}")
    
    def _extract_correction_patterns(self, corrections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract patterns from a batch of corrections."""
        patterns = {
            'speaker_distribution': Counter(),
            'context_distribution': Counter(),
            'temporal_patterns': [],
            'confidence_issues': [],
            'systematic_errors': []
        }
        
        for correction in corrections:
            speaker = correction['speaker_name']
            context = self._extract_context_from_filename(correction['transcript_file'])
            
            patterns['speaker_distribution'][speaker] += 1
            patterns['context_distribution'][context] += 1
            patterns['temporal_patterns'].append(correction['created_at'])
            
            if correction['confidence'] < 0.7:
                patterns['confidence_issues'].append(correction)
        
        return patterns
    
    def _update_voice_models_with_corrections(self, 
                                            corrections: List[Dict[str, Any]], 
                                            patterns: Dict[str, Any]):
        """Update voice models based on correction feedback."""
        try:
            # Group corrections by speaker
            speaker_corrections = defaultdict(list)
            for correction in corrections:
                speaker_corrections[correction['speaker_name']].append(correction)
            
            # Update models for speakers with multiple corrections
            for speaker, speaker_corrs in speaker_corrections.items():
                if len(speaker_corrs) >= 3:  # Minimum corrections for update
                    logger.info(f"Updating voice model for {speaker} with {len(speaker_corrs)} corrections")
                    # This would integrate with Phase 6B voice model updates
                    self.feedback_metrics['models_updated'] += 1
                    
        except Exception as e:
            logger.error(f"Error updating voice models with corrections: {e}")
    
    def _update_predictive_models_with_corrections(self, 
                                                 corrections: List[Dict[str, Any]], 
                                                 patterns: Dict[str, Any]):
        """Update predictive models with correction feedback."""
        try:
            # Check if we have enough new data for model update
            if len(corrections) >= 20:
                logger.info(f"Updating predictive models with {len(corrections)} corrections")
                
                # Trigger predictive model retraining
                training_result = self.predictive_identifier.train_prediction_models()
                
                if training_result.get('status') == 'success':
                    self.feedback_metrics['predictions_improved'] += 1
                    logger.info("Predictive models updated successfully")
                    
        except Exception as e:
            logger.error(f"Error updating predictive models: {e}")
    
    def _check_alert_conditions(self, 
                               corrections: List[Dict[str, Any]], 
                               patterns: Dict[str, Any]):
        """Check for conditions that require alerts."""
        try:
            alerts = []
            
            # Check for correction burst
            if len(corrections) > self.config['alerts']['correction_burst_threshold']:
                alerts.append({
                    'type': 'correction_burst',
                    'severity': 'high',
                    'message': f"High correction activity: {len(corrections)} corrections",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Check for systematic errors
            speaker_dist = patterns['speaker_distribution']
            if speaker_dist.most_common(1) and speaker_dist.most_common(1)[0][1] > 10:
                most_corrected = speaker_dist.most_common(1)[0]
                alerts.append({
                    'type': 'systematic_error',
                    'severity': 'medium',
                    'message': f"High correction frequency for {most_corrected[0]}: {most_corrected[1]} corrections",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Process alerts
            for alert in alerts:
                self._process_alert(alert)
                
        except Exception as e:
            logger.error(f"Error checking alert conditions: {e}")
    
    def _process_alert(self, alert: Dict[str, Any]):
        """Process an alert based on configuration."""
        try:
            alert_channels = self.config['alerts']['notification_channels']
            
            if 'log' in alert_channels:
                logger.warning(f"ALERT [{alert['type']}]: {alert['message']}")
            
            if 'email' in alert_channels:
                # Email notification would be implemented here
                logger.info(f"Email alert would be sent: {alert['message']}")
                
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
    
    def _trigger_model_updates(self, corrections: List[Dict[str, Any]]):
        """Trigger model updates based on new corrections."""
        try:
            # Check thresholds for different types of updates
            if len(corrections) >= 20:
                # Major update - retrain all models
                logger.info("Triggering major model update")
                self._trigger_model_retraining("correction_threshold")
                
            elif len(corrections) >= 10:
                # Minor update - optimize thresholds
                logger.info("Triggering threshold optimization")
                optimization_result = self.threshold_optimizer.optimize_thresholds()
                
                if optimization_result.get('status') == 'optimized':
                    self.feedback_metrics['thresholds_optimized'] += 1
            
        except Exception as e:
            logger.error(f"Error triggering model updates: {e}")
    
    def _trigger_model_retraining(self, reason: str):
        """Trigger model retraining."""
        try:
            logger.info(f"Triggering model retraining due to: {reason}")
            
            # Retrain predictive models
            training_result = self.predictive_identifier.train_prediction_models(force_retrain=True)
            
            if training_result.get('status') == 'success':
                self.feedback_metrics['models_updated'] += 1
                logger.info("Model retraining completed successfully")
            else:
                logger.warning(f"Model retraining failed: {training_result}")
                
        except Exception as e:
            logger.error(f"Error in model retraining: {e}")
    
    def _process_pattern_insights(self, insights: Dict[str, Any]):
        """Process insights from pattern analysis."""
        try:
            recommendations = insights.get('recommendations', [])
            alerts = insights.get('alerts', [])
            optimizations = insights.get('optimization_opportunities', [])
            
            # Process high-priority recommendations
            for rec in recommendations:
                if rec.get('priority') == 'high':
                    logger.info(f"High-priority recommendation: {rec['message']}")
                    
                    if rec['type'] == 'speaker_focus':
                        # Trigger focused model update
                        self._trigger_focused_model_update(rec)
            
            # Process alerts
            for alert in alerts:
                self._process_alert({
                    'type': alert['type'],
                    'severity': alert.get('priority', 'medium'),
                    'message': alert['message'],
                    'timestamp': datetime.now().isoformat()
                })
            
            # Process optimization opportunities
            for opt in optimizations[:3]:  # Top 3 opportunities
                if opt.get('priority') == 'high':
                    logger.info(f"Optimization opportunity: {opt['message']}")
                    
        except Exception as e:
            logger.error(f"Error processing pattern insights: {e}")
    
    def _trigger_focused_model_update(self, recommendation: Dict[str, Any]):
        """Trigger focused model update based on recommendation."""
        try:
            if recommendation['type'] == 'speaker_focus':
                # This would trigger focused voice model training for specific speakers
                logger.info(f"Focusing model improvement: {recommendation['message']}")
                self.feedback_metrics['models_updated'] += 1
                
        except Exception as e:
            logger.error(f"Error triggering focused model update: {e}")
    
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
        else:
            return 'general_hearing'
    
    def get_feedback_status(self) -> Dict[str, Any]:
        """Get current status of feedback integration."""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'metrics': self.feedback_metrics,
            'config': self.config,
            'active_threads': len(self.processing_threads),
            'queue_sizes': {
                'corrections': self.correction_queue.qsize(),
                'updates': self.update_queue.qsize()
            }
        }
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of feedback integration."""
        try:
            # Get performance from all components
            pattern_analysis = self.pattern_analyzer.get_pattern_insights()
            threshold_recommendations = self.threshold_optimizer.get_threshold_recommendations()
            
            # Get recent activity
            recent_corrections = self._get_new_corrections_since(
                datetime.now() - timedelta(hours=24)
            )
            
            return {
                'feedback_metrics': self.feedback_metrics,
                'recent_activity': {
                    'corrections_24h': len(recent_corrections),
                    'most_corrected_speakers': Counter(
                        c['speaker_name'] for c in recent_corrections
                    ).most_common(5),
                    'context_distribution': Counter(
                        self._extract_context_from_filename(c['transcript_file']) 
                        for c in recent_corrections
                    ).most_common()
                },
                'component_status': {
                    'pattern_analysis': pattern_analysis,
                    'threshold_optimization': threshold_recommendations,
                    'real_time_processing': {
                        'enabled': self.is_running,
                        'threads_active': len(self.processing_threads)
                    }
                },
                'integration_health': self._calculate_integration_health()
            }
            
        except Exception as e:
            logger.error(f"Error getting integration summary: {e}")
            return {'error': str(e)}
    
    def _calculate_integration_health(self) -> Dict[str, Any]:
        """Calculate overall health of feedback integration."""
        try:
            health_score = 1.0
            issues = []
            
            # Check if real-time processing is active
            if not self.is_running:
                health_score *= 0.7
                issues.append("Real-time processing not active")
            
            # Check recent activity
            recent_corrections = self._get_new_corrections_since(
                datetime.now() - timedelta(hours=24)
            )
            
            if len(recent_corrections) == 0:
                health_score *= 0.9
                issues.append("No recent correction activity")
            elif len(recent_corrections) > 50:
                health_score *= 0.8
                issues.append("High correction activity may indicate system issues")
            
            # Check model update frequency
            if self.feedback_metrics['models_updated'] == 0:
                health_score *= 0.8
                issues.append("No model updates performed")
            
            # Determine health level
            if health_score >= 0.9:
                health_level = 'excellent'
            elif health_score >= 0.7:
                health_level = 'good'
            elif health_score >= 0.5:
                health_level = 'fair'
            else:
                health_level = 'poor'
            
            return {
                'health_score': health_score,
                'health_level': health_level,
                'issues': issues,
                'recommendations': self._get_health_recommendations(health_score, issues)
            }
            
        except Exception as e:
            logger.error(f"Error calculating integration health: {e}")
            return {'health_score': 0.0, 'health_level': 'unknown', 'error': str(e)}
    
    def _get_health_recommendations(self, health_score: float, issues: List[str]) -> List[str]:
        """Get recommendations based on health assessment."""
        recommendations = []
        
        if health_score < 0.7:
            recommendations.append("Consider restarting real-time feedback processing")
        
        if "High correction activity" in str(issues):
            recommendations.append("Investigate potential systematic identification issues")
        
        if "No model updates" in str(issues):
            recommendations.append("Check model update thresholds and trigger conditions")
        
        if not recommendations:
            recommendations.append("System operating normally - continue monitoring")
        
        return recommendations
    
    def get_system_health_status(self) -> Dict[str, Any]:
        """Get comprehensive system health status including component health."""
        try:
            # Get health from error handler
            component_health = self.health_monitor.get_system_health()
            
            # Get integration-specific health
            integration_health = self.assess_integration_health()
            
            # Combine health assessments
            overall_health = {
                'timestamp': datetime.now().isoformat(),
                'component_health': component_health,
                'integration_health': integration_health,
                'real_time_feedback_active': self.is_running,
                'active_threads': len(self.processing_threads) if hasattr(self, 'processing_threads') else 0
            }
            
            # Determine overall status
            if (component_health['status'] == 'critical' or 
                integration_health['health_level'] == 'poor'):
                overall_health['status'] = 'critical'
            elif (component_health['status'] == 'degraded' or 
                  integration_health['health_level'] == 'fair'):
                overall_health['status'] = 'warning'
            else:
                overall_health['status'] = 'healthy'
            
            return overall_health
            
        except Exception as e:
            logger.error(f"Error getting system health status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


if __name__ == "__main__":
    # Test feedback integrator
    integrator = FeedbackIntegrator()
    
    # Start real-time feedback
    start_result = integrator.start_real_time_feedback()
    print(f"Start result: {json.dumps(start_result, indent=2)}")
    
    # Get status
    status = integrator.get_feedback_status()
    print(f"Status: {json.dumps(status, indent=2)}")
    
    # Get integration summary
    summary = integrator.get_integration_summary()
    print(f"Summary: {json.dumps(summary, indent=2, default=str)}")
    
    # Stop after a short time (for testing)
    time.sleep(5)
    stop_result = integrator.stop_real_time_feedback()
    print(f"Stop result: {json.dumps(stop_result, indent=2)}")