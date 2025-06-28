#!/usr/bin/env python3
"""
Performance Tracker for Phase 6C

Comprehensive performance tracking and analytics:
- Real-time accuracy metrics and trend analysis
- Performance forecasting and anomaly detection
- ROC curve analysis for threshold optimization
- System health monitoring and alerting
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
from sklearn.metrics import roc_curve, auc, precision_recall_curve
from sklearn.linear_model import LinearRegression
import pickle
import io
import base64

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """Tracks and analyzes performance across all Phase 6 components."""
    
    def __init__(self, 
                 corrections_db_path: Path = None,
                 voice_models_db_path: Path = None,
                 metrics_db_path: Path = None):
        """Initialize performance tracker."""
        self.corrections_db_path = corrections_db_path or Path("output/corrections.db")
        self.voice_models_db_path = voice_models_db_path or Path("data/voice_models/speaker_models.db")
        self.metrics_db_path = metrics_db_path or Path("data/learning/performance_metrics.db")
        
        # Ensure metrics database directory exists
        self.metrics_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize metrics database
        self._init_metrics_database()
        
        # Performance thresholds
        self.performance_thresholds = {
            'accuracy_warning': 0.7,
            'accuracy_critical': 0.5,
            'coverage_warning': 0.6,
            'coverage_critical': 0.4,
            'latency_warning': 5.0,  # seconds
            'latency_critical': 10.0  # seconds
        }
        
        # Visualization settings
        plt.style.use('dark_background')
        sns.set_palette("husl")
        
    def _init_metrics_database(self):
        """Initialize performance metrics database."""
        with sqlite3.connect(self.metrics_db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    context_data TEXT,
                    component TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS system_health (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    component TEXT NOT NULL,
                    health_score REAL NOT NULL,
                    status TEXT NOT NULL,
                    issues TEXT,
                    recommendations TEXT
                );
                
                CREATE TABLE IF NOT EXISTS performance_alerts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    component TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT 0,
                    resolved_at TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                ON performance_metrics(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_metrics_component 
                ON performance_metrics(component, metric_type);
                
                CREATE INDEX IF NOT EXISTS idx_health_timestamp 
                ON system_health(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
                ON performance_alerts(timestamp);
            """)
    
    def record_performance_metric(self, 
                                component: str,
                                metric_type: str,
                                metric_name: str,
                                metric_value: float,
                                context_data: Dict[str, Any] = None) -> str:
        """Record a performance metric."""
        try:
            metric_id = f"metric_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            timestamp = datetime.now().isoformat()
            
            with sqlite3.connect(self.metrics_db_path) as conn:
                conn.execute(
                    "INSERT INTO performance_metrics "
                    "(id, timestamp, metric_type, metric_name, metric_value, context_data, component) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        metric_id,
                        timestamp,
                        metric_type,
                        metric_name,
                        metric_value,
                        json.dumps(context_data) if context_data else None,
                        component
                    )
                )
            
            # Check for alert conditions
            self._check_metric_alerts(component, metric_type, metric_name, metric_value)
            
            return metric_id
            
        except Exception as e:
            logger.error(f"Error recording performance metric: {e}")
            return ""
    
    def get_current_performance(self, 
                              component: str = None,
                              time_window_hours: int = 24) -> Dict[str, Any]:
        """Get current performance metrics."""
        try:
            start_time = datetime.now() - timedelta(hours=time_window_hours)
            
            with sqlite3.connect(self.metrics_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Build query
                query = """
                    SELECT component, metric_type, metric_name, 
                           AVG(metric_value) as avg_value,
                           MIN(metric_value) as min_value,
                           MAX(metric_value) as max_value,
                           COUNT(*) as sample_count
                    FROM performance_metrics 
                    WHERE timestamp > ?
                """
                params = [start_time.isoformat()]
                
                if component:
                    query += " AND component = ?"
                    params.append(component)
                
                query += " GROUP BY component, metric_type, metric_name"
                
                metrics = conn.execute(query, params).fetchall()
                
                # Organize results
                performance = defaultdict(lambda: defaultdict(dict))
                
                for metric in metrics:
                    comp = metric['component']
                    m_type = metric['metric_type']
                    m_name = metric['metric_name']
                    
                    performance[comp][m_type][m_name] = {
                        'average': metric['avg_value'],
                        'minimum': metric['min_value'],
                        'maximum': metric['max_value'],
                        'samples': metric['sample_count']
                    }
                
                # Calculate overall scores
                overall_performance = self._calculate_overall_performance(performance)
                
                return {
                    'time_window_hours': time_window_hours,
                    'timestamp': datetime.now().isoformat(),
                    'component_performance': dict(performance),
                    'overall_performance': overall_performance,
                    'health_status': self._assess_current_health(performance)
                }
                
        except Exception as e:
            logger.error(f"Error getting current performance: {e}")
            return {'error': str(e)}
    
    def get_performance_trends(self, 
                             component: str = None,
                             days: int = 7) -> Dict[str, Any]:
        """Get performance trends over time."""
        try:
            start_time = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.metrics_db_path) as conn:
                query = """
                    SELECT timestamp, component, metric_type, metric_name, metric_value
                    FROM performance_metrics 
                    WHERE timestamp > ?
                """
                params = [start_time.isoformat()]
                
                if component:
                    query += " AND component = ?"
                    params.append(component)
                
                query += " ORDER BY timestamp"
                
                df = pd.read_sql_query(query, conn, params=params)
                
                if df.empty:
                    return {'status': 'no_data', 'message': 'No performance data available'}
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Calculate trends for key metrics
                trends = {}
                
                # Accuracy trend
                accuracy_data = df[df['metric_name'] == 'accuracy']
                if not accuracy_data.empty:
                    trends['accuracy'] = self._calculate_trend(accuracy_data)
                
                # Coverage trend
                coverage_data = df[df['metric_name'] == 'coverage']
                if not coverage_data.empty:
                    trends['coverage'] = self._calculate_trend(coverage_data)
                
                # Response time trend
                latency_data = df[df['metric_name'] == 'response_time']
                if not latency_data.empty:
                    trends['response_time'] = self._calculate_trend(latency_data)
                
                # Generate forecasts
                forecasts = self._generate_forecasts(df, days=3)
                
                return {
                    'period_days': days,
                    'trends': trends,
                    'forecasts': forecasts,
                    'data_points': len(df),
                    'components_analyzed': df['component'].unique().tolist()
                }
                
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            return {'error': str(e)}
    
    def _calculate_trend(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate trend for a metric."""
        if len(data) < 2:
            return {'status': 'insufficient_data'}
        
        # Convert timestamps to numeric for regression
        data = data.copy()
        data['timestamp_numeric'] = (data['timestamp'] - data['timestamp'].min()).dt.total_seconds()
        
        # Linear regression
        X = data['timestamp_numeric'].values.reshape(-1, 1)
        y = data['metric_value'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        slope = model.coef_[0]
        r_squared = model.score(X, y)
        
        # Determine trend direction
        if abs(slope) < 0.001:
            direction = 'stable'
        elif slope > 0:
            direction = 'improving'
        else:
            direction = 'declining'
        
        # Calculate percentage change
        if len(data) >= 7:  # Weekly change
            recent_avg = data.tail(7)['metric_value'].mean()
            older_avg = data.head(7)['metric_value'].mean()
            percent_change = ((recent_avg - older_avg) / older_avg) * 100 if older_avg != 0 else 0
        else:
            percent_change = 0
        
        return {
            'direction': direction,
            'slope': slope,
            'r_squared': r_squared,
            'percent_change_weekly': percent_change,
            'current_value': data['metric_value'].iloc[-1],
            'average_value': data['metric_value'].mean(),
            'data_points': len(data)
        }
    
    def _generate_forecasts(self, data: pd.DataFrame, days: int = 3) -> Dict[str, Any]:
        """Generate performance forecasts."""
        forecasts = {}
        
        for metric_name in ['accuracy', 'coverage', 'response_time']:
            metric_data = data[data['metric_name'] == metric_name]
            
            if len(metric_data) >= 10:  # Minimum data for forecasting
                forecast = self._forecast_metric(metric_data, days)
                forecasts[metric_name] = forecast
        
        return forecasts
    
    def _forecast_metric(self, data: pd.DataFrame, days: int) -> Dict[str, Any]:
        """Forecast a specific metric."""
        try:
            # Prepare data
            data = data.copy().sort_values('timestamp')
            data['timestamp_numeric'] = (data['timestamp'] - data['timestamp'].min()).dt.total_seconds()
            
            # Fit model
            X = data['timestamp_numeric'].values.reshape(-1, 1)
            y = data['metric_value'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Generate future timestamps
            last_timestamp = data['timestamp'].iloc[-1]
            future_timestamps = [last_timestamp + timedelta(days=i) for i in range(1, days + 1)]
            future_numeric = [(ts - data['timestamp'].min()).total_seconds() for ts in future_timestamps]
            
            # Predict
            predictions = model.predict(np.array(future_numeric).reshape(-1, 1))
            
            # Calculate confidence intervals (simple approach)
            residuals = y - model.predict(X)
            std_error = np.std(residuals)
            
            forecast_data = []
            for i, (timestamp, prediction) in enumerate(zip(future_timestamps, predictions)):
                forecast_data.append({
                    'timestamp': timestamp.isoformat(),
                    'predicted_value': prediction,
                    'confidence_lower': prediction - 1.96 * std_error,
                    'confidence_upper': prediction + 1.96 * std_error
                })
            
            return {
                'status': 'success',
                'model_r_squared': model.score(X, y),
                'forecast_data': forecast_data,
                'trend': 'improving' if model.coef_[0] > 0 else 'declining'
            }
            
        except Exception as e:
            logger.error(f"Error forecasting metric: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def analyze_system_performance(self) -> Dict[str, Any]:
        """Comprehensive system performance analysis."""
        try:
            logger.info("Running comprehensive system performance analysis")
            
            # Get current performance
            current_perf = self.get_current_performance()
            
            # Get trends
            trends = self.get_performance_trends(days=7)
            
            # Get ROC analysis
            roc_analysis = self._analyze_roc_performance()
            
            # Get error analysis
            error_analysis = self._analyze_error_patterns()
            
            # Generate recommendations
            recommendations = self._generate_performance_recommendations(
                current_perf, trends, roc_analysis, error_analysis
            )
            
            # System health assessment
            health_assessment = self._comprehensive_health_assessment()
            
            return {
                'analysis_timestamp': datetime.now().isoformat(),
                'current_performance': current_perf,
                'trends': trends,
                'roc_analysis': roc_analysis,
                'error_analysis': error_analysis,
                'recommendations': recommendations,
                'health_assessment': health_assessment,
                'system_status': self._determine_system_status(current_perf, trends)
            }
            
        except Exception as e:
            logger.error(f"Error in system performance analysis: {e}")
            return {'error': str(e)}
    
    def _analyze_roc_performance(self) -> Dict[str, Any]:
        """Analyze ROC curve performance for threshold optimization."""
        try:
            # Get recognition results with confidence scores
            if not self.voice_models_db_path.exists():
                return {'status': 'no_voice_data'}
            
            with sqlite3.connect(self.voice_models_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                results = conn.execute("""
                    SELECT confidence_score, correction_applied, human_verified
                    FROM recognition_results
                    WHERE confidence_score IS NOT NULL AND human_verified = 1
                """).fetchall()
                
                if len(results) < 10:
                    return {'status': 'insufficient_data'}
                
                # Prepare data for ROC analysis
                y_true = [1 if not r['correction_applied'] else 0 for r in results]
                y_scores = [r['confidence_score'] for r in results]
                
                # Calculate ROC curve
                fpr, tpr, thresholds = roc_curve(y_true, y_scores)
                roc_auc = auc(fpr, tpr)
                
                # Calculate precision-recall curve
                precision, recall, pr_thresholds = precision_recall_curve(y_true, y_scores)
                pr_auc = auc(recall, precision)
                
                # Find optimal threshold (Youden's J statistic)
                j_scores = tpr - fpr
                optimal_idx = np.argmax(j_scores)
                optimal_threshold = thresholds[optimal_idx]
                
                return {
                    'status': 'success',
                    'roc_auc': roc_auc,
                    'pr_auc': pr_auc,
                    'optimal_threshold': optimal_threshold,
                    'optimal_tpr': tpr[optimal_idx],
                    'optimal_fpr': fpr[optimal_idx],
                    'data_points': len(results),
                    'threshold_analysis': self._analyze_threshold_performance(y_true, y_scores)
                }
                
        except Exception as e:
            logger.error(f"Error in ROC analysis: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _analyze_threshold_performance(self, y_true: List[int], y_scores: List[float]) -> Dict[str, Any]:
        """Analyze performance at different thresholds."""
        thresholds = np.arange(0.1, 1.0, 0.1)
        threshold_performance = {}
        
        for threshold in thresholds:
            y_pred = [1 if score >= threshold else 0 for score in y_scores]
            
            tp = sum(1 for true, pred in zip(y_true, y_pred) if true == 1 and pred == 1)
            fp = sum(1 for true, pred in zip(y_true, y_pred) if true == 0 and pred == 1)
            tn = sum(1 for true, pred in zip(y_true, y_pred) if true == 0 and pred == 0)
            fn = sum(1 for true, pred in zip(y_true, y_pred) if true == 1 and pred == 0)
            
            accuracy = (tp + tn) / len(y_true) if len(y_true) > 0 else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            threshold_performance[f"{threshold:.1f}"] = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'tp': tp,
                'fp': fp,
                'tn': tn,
                'fn': fn
            }
        
        return threshold_performance
    
    def _analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns from corrections data."""
        try:
            if not self.corrections_db_path.exists():
                return {'status': 'no_corrections_data'}
            
            with sqlite3.connect(self.corrections_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                corrections = conn.execute("""
                    SELECT speaker_name, transcript_file, segment_id, confidence, created_at
                    FROM corrections
                    WHERE is_active = 1
                    ORDER BY created_at DESC
                    LIMIT 1000
                """).fetchall()
                
                if len(corrections) < 5:
                    return {'status': 'insufficient_corrections'}
                
                # Analyze error patterns
                speaker_errors = Counter(c['speaker_name'] for c in corrections)
                context_errors = Counter(self._extract_context_from_filename(c['transcript_file']) for c in corrections)
                
                # Temporal patterns
                correction_times = [datetime.fromisoformat(c['created_at']) for c in corrections]
                hourly_pattern = Counter(dt.hour for dt in correction_times)
                
                # Confidence patterns
                confidence_values = [c['confidence'] for c in corrections if c['confidence']]
                avg_confidence = np.mean(confidence_values) if confidence_values else 0
                
                return {
                    'status': 'success',
                    'total_corrections': len(corrections),
                    'top_error_speakers': speaker_errors.most_common(10),
                    'error_by_context': dict(context_errors),
                    'hourly_error_pattern': dict(hourly_pattern),
                    'confidence_statistics': {
                        'average': avg_confidence,
                        'std': np.std(confidence_values) if confidence_values else 0,
                        'min': min(confidence_values) if confidence_values else 0,
                        'max': max(confidence_values) if confidence_values else 0
                    },
                    'error_frequency': self._calculate_error_frequency(corrections)
                }
                
        except Exception as e:
            logger.error(f"Error analyzing error patterns: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _calculate_error_frequency(self, corrections: List[sqlite3.Row]) -> Dict[str, Any]:
        """Calculate error frequency metrics."""
        if not corrections:
            return {}
        
        # Group by day
        daily_counts = defaultdict(int)
        for correction in corrections:
            day = datetime.fromisoformat(correction['created_at']).date()
            daily_counts[day] += 1
        
        # Calculate statistics
        counts = list(daily_counts.values())
        
        return {
            'daily_average': np.mean(counts) if counts else 0,
            'daily_std': np.std(counts) if counts else 0,
            'max_daily': max(counts) if counts else 0,
            'days_with_errors': len(daily_counts),
            'total_days': (max(daily_counts.keys()) - min(daily_counts.keys())).days + 1 if daily_counts else 0
        }
    
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
    
    def _generate_performance_recommendations(self, 
                                            current_perf: Dict[str, Any],
                                            trends: Dict[str, Any],
                                            roc_analysis: Dict[str, Any],
                                            error_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        # Accuracy recommendations
        overall_perf = current_perf.get('overall_performance', {})
        if overall_perf.get('accuracy', 1.0) < self.performance_thresholds['accuracy_warning']:
            recommendations.append({
                'type': 'accuracy_improvement',
                'priority': 'high',
                'message': f"System accuracy ({overall_perf.get('accuracy', 0):.2%}) below warning threshold",
                'actions': ['Retrain voice models', 'Optimize thresholds', 'Increase training data']
            })
        
        # Coverage recommendations
        if overall_perf.get('coverage', 1.0) < self.performance_thresholds['coverage_warning']:
            recommendations.append({
                'type': 'coverage_improvement',
                'priority': 'medium',
                'message': f"System coverage ({overall_perf.get('coverage', 0):.2%}) below warning threshold",
                'actions': ['Lower confidence thresholds', 'Improve voice collection', 'Add more speaker models']
            })
        
        # Trend-based recommendations
        accuracy_trend = trends.get('trends', {}).get('accuracy', {})
        if accuracy_trend.get('direction') == 'declining':
            recommendations.append({
                'type': 'trend_alert',
                'priority': 'medium',
                'message': f"Accuracy trending downward ({accuracy_trend.get('percent_change_weekly', 0):.1f}% weekly change)",
                'actions': ['Investigate recent changes', 'Check data quality', 'Consider model refresh']
            })
        
        # ROC-based recommendations
        if roc_analysis.get('status') == 'success':
            if roc_analysis.get('roc_auc', 0) < 0.8:
                recommendations.append({
                    'type': 'model_performance',
                    'priority': 'high',
                    'message': f"ROC AUC ({roc_analysis.get('roc_auc', 0):.3f}) indicates poor discrimination",
                    'actions': ['Feature engineering', 'Model architecture review', 'Data quality assessment']
                })
        
        # Error pattern recommendations
        if error_analysis.get('status') == 'success':
            top_error_speakers = error_analysis.get('top_error_speakers', [])
            if top_error_speakers and top_error_speakers[0][1] > 10:
                speaker, count = top_error_speakers[0]
                recommendations.append({
                    'type': 'speaker_focus',
                    'priority': 'medium',
                    'message': f"High error rate for {speaker} ({count} corrections)",
                    'actions': ['Collect more voice samples', 'Review voice quality', 'Manual model tuning']
                })
        
        return recommendations
    
    def _comprehensive_health_assessment(self) -> Dict[str, Any]:
        """Comprehensive system health assessment."""
        try:
            health_scores = {}
            
            # Performance health
            current_perf = self.get_current_performance()
            overall_perf = current_perf.get('overall_performance', {})
            
            accuracy = overall_perf.get('accuracy', 0)
            coverage = overall_perf.get('coverage', 0)
            
            performance_health = min(
                accuracy / self.performance_thresholds['accuracy_warning'],
                coverage / self.performance_thresholds['coverage_warning'],
                1.0
            )
            health_scores['performance'] = performance_health
            
            # Data quality health
            error_analysis = self._analyze_error_patterns()
            if error_analysis.get('status') == 'success':
                total_corrections = error_analysis.get('total_corrections', 0)
                error_frequency = error_analysis.get('error_frequency', {})
                daily_avg = error_frequency.get('daily_average', 0)
                
                # Lower correction frequency indicates better health
                data_quality_health = max(0, 1 - (daily_avg / 50))  # 50 corrections/day = 0 health
                health_scores['data_quality'] = data_quality_health
            else:
                health_scores['data_quality'] = 0.5  # Unknown
            
            # System stability health
            trends = self.get_performance_trends(days=3)
            if trends.get('trends'):
                stability_health = 1.0
                for metric, trend in trends['trends'].items():
                    if trend.get('direction') == 'declining':
                        stability_health *= 0.8
                health_scores['stability'] = stability_health
            else:
                health_scores['stability'] = 0.5  # Unknown
            
            # Overall health
            overall_health = np.mean(list(health_scores.values()))
            
            # Health level
            if overall_health >= 0.9:
                health_level = 'excellent'
            elif overall_health >= 0.7:
                health_level = 'good'
            elif overall_health >= 0.5:
                health_level = 'fair'
            else:
                health_level = 'poor'
            
            return {
                'overall_health': overall_health,
                'health_level': health_level,
                'component_scores': health_scores,
                'assessment_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in health assessment: {e}")
            return {'overall_health': 0.0, 'health_level': 'unknown', 'error': str(e)}
    
    def _calculate_overall_performance(self, performance: Dict[str, Dict]) -> Dict[str, float]:
        """Calculate overall performance scores."""
        overall = {
            'accuracy': 0.0,
            'coverage': 0.0,
            'response_time': 0.0,
            'reliability': 0.0
        }
        
        accuracy_values = []
        coverage_values = []
        response_times = []
        
        for component, metrics in performance.items():
            for metric_type, metric_data in metrics.items():
                if 'accuracy' in metric_data:
                    accuracy_values.append(metric_data['accuracy']['average'])
                if 'coverage' in metric_data:
                    coverage_values.append(metric_data['coverage']['average'])
                if 'response_time' in metric_data:
                    response_times.append(metric_data['response_time']['average'])
        
        if accuracy_values:
            overall['accuracy'] = np.mean(accuracy_values)
        if coverage_values:
            overall['coverage'] = np.mean(coverage_values)
        if response_times:
            overall['response_time'] = np.mean(response_times)
        
        # Reliability based on consistency
        reliability_scores = []
        for values in [accuracy_values, coverage_values]:
            if values:
                coefficient_of_variation = np.std(values) / np.mean(values) if np.mean(values) > 0 else 1
                reliability_score = max(0, 1 - coefficient_of_variation)
                reliability_scores.append(reliability_score)
        
        if reliability_scores:
            overall['reliability'] = np.mean(reliability_scores)
        
        return overall
    
    def _assess_current_health(self, performance: Dict[str, Dict]) -> Dict[str, str]:
        """Assess current health status for each component."""
        health_status = {}
        
        for component, metrics in performance.items():
            component_health = 'good'
            
            for metric_type, metric_data in metrics.items():
                for metric_name, values in metric_data.items():
                    avg_value = values['average']
                    
                    if metric_name == 'accuracy' and avg_value < self.performance_thresholds['accuracy_warning']:
                        component_health = 'warning' if component_health == 'good' else 'critical'
                    elif metric_name == 'coverage' and avg_value < self.performance_thresholds['coverage_warning']:
                        component_health = 'warning' if component_health == 'good' else 'critical'
                    elif metric_name == 'response_time' and avg_value > self.performance_thresholds['latency_warning']:
                        component_health = 'warning' if component_health == 'good' else 'critical'
            
            health_status[component] = component_health
        
        return health_status
    
    def _determine_system_status(self, current_perf: Dict[str, Any], trends: Dict[str, Any]) -> str:
        """Determine overall system status."""
        overall_perf = current_perf.get('overall_performance', {})
        accuracy = overall_perf.get('accuracy', 0)
        coverage = overall_perf.get('coverage', 0)
        
        # Check critical thresholds
        if accuracy < self.performance_thresholds['accuracy_critical']:
            return 'critical'
        if coverage < self.performance_thresholds['coverage_critical']:
            return 'critical'
        
        # Check warning thresholds
        if accuracy < self.performance_thresholds['accuracy_warning']:
            return 'warning'
        if coverage < self.performance_thresholds['coverage_warning']:
            return 'warning'
        
        # Check trends
        accuracy_trend = trends.get('trends', {}).get('accuracy', {})
        if accuracy_trend.get('direction') == 'declining' and accuracy_trend.get('percent_change_weekly', 0) < -10:
            return 'warning'
        
        return 'healthy'
    
    def _check_metric_alerts(self, 
                           component: str, 
                           metric_type: str, 
                           metric_name: str, 
                           metric_value: float):
        """Check if metric value triggers any alerts."""
        try:
            alert_triggered = False
            severity = 'info'
            message = ""
            
            # Define alert conditions
            if metric_name == 'accuracy':
                if metric_value < self.performance_thresholds['accuracy_critical']:
                    alert_triggered = True
                    severity = 'critical'
                    message = f"Critical accuracy drop: {metric_value:.2%}"
                elif metric_value < self.performance_thresholds['accuracy_warning']:
                    alert_triggered = True
                    severity = 'warning'
                    message = f"Accuracy below warning threshold: {metric_value:.2%}"
            
            elif metric_name == 'coverage':
                if metric_value < self.performance_thresholds['coverage_critical']:
                    alert_triggered = True
                    severity = 'critical'
                    message = f"Critical coverage drop: {metric_value:.2%}"
                elif metric_value < self.performance_thresholds['coverage_warning']:
                    alert_triggered = True
                    severity = 'warning'
                    message = f"Coverage below warning threshold: {metric_value:.2%}"
            
            elif metric_name == 'response_time':
                if metric_value > self.performance_thresholds['latency_critical']:
                    alert_triggered = True
                    severity = 'critical'
                    message = f"Critical response time: {metric_value:.2f}s"
                elif metric_value > self.performance_thresholds['latency_warning']:
                    alert_triggered = True
                    severity = 'warning'
                    message = f"Response time above threshold: {metric_value:.2f}s"
            
            # Record alert if triggered
            if alert_triggered:
                self._record_alert(component, metric_type, severity, message)
            
        except Exception as e:
            logger.error(f"Error checking metric alerts: {e}")
    
    def _record_alert(self, component: str, alert_type: str, severity: str, message: str):
        """Record a performance alert."""
        try:
            alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            timestamp = datetime.now().isoformat()
            
            with sqlite3.connect(self.metrics_db_path) as conn:
                conn.execute(
                    "INSERT INTO performance_alerts "
                    "(id, timestamp, alert_type, severity, message, component) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (alert_id, timestamp, alert_type, severity, message, component)
                )
            
            logger.warning(f"Performance alert [{severity}]: {message} (Component: {component})")
            
        except Exception as e:
            logger.error(f"Error recording alert: {e}")
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent performance alerts."""
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.metrics_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                alerts = conn.execute(
                    "SELECT * FROM performance_alerts "
                    "WHERE timestamp > ? AND resolved = 0 "
                    "ORDER BY timestamp DESC",
                    (start_time.isoformat(),)
                ).fetchall()
                
                return [dict(alert) for alert in alerts]
                
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []


if __name__ == "__main__":
    # Test performance tracker
    tracker = PerformanceTracker()
    
    # Record some test metrics
    tracker.record_performance_metric('phase6a', 'accuracy', 'speaker_identification', 0.85)
    tracker.record_performance_metric('phase6b', 'coverage', 'voice_recognition', 0.72)
    tracker.record_performance_metric('phase6c', 'response_time', 'prediction_latency', 1.5)
    
    # Get current performance
    performance = tracker.get_current_performance()
    print(f"Current performance: {json.dumps(performance, indent=2, default=str)}")
    
    # Run comprehensive analysis
    analysis = tracker.analyze_system_performance()
    print(f"System analysis: {json.dumps(analysis, indent=2, default=str)}")
    
    # Get recent alerts
    alerts = tracker.get_recent_alerts()
    print(f"Recent alerts: {json.dumps(alerts, indent=2)}")