#!/usr/bin/env python3
"""
Pattern Analyzer for Phase 6C

Analyzes patterns in human corrections to identify:
- Common misidentification causes
- Speaker-specific identification challenges
- Contextual factors affecting accuracy
- Temporal patterns in corrections
- Feature importance for different speakers
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
import pickle

logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """Analyzes patterns in human corrections and system performance."""
    
    def __init__(self, 
                 corrections_db_path: Path = None,
                 voice_models_db_path: Path = None,
                 patterns_cache_path: Path = None):
        """Initialize pattern analyzer."""
        self.corrections_db_path = corrections_db_path or Path("output/corrections.db")
        self.voice_models_db_path = voice_models_db_path or Path("data/voice_models/speaker_models.db")
        self.patterns_cache_path = patterns_cache_path or Path("data/learning/pattern_cache.pkl")
        
        # Ensure cache directory exists
        self.patterns_cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Pattern analysis cache
        self.pattern_cache = {}
        self._load_pattern_cache()
        
        # Analysis thresholds
        self.min_corrections_for_pattern = 5
        self.confidence_threshold_low = 0.3
        self.confidence_threshold_high = 0.8
        
    def _load_pattern_cache(self):
        """Load cached pattern analysis results."""
        try:
            if self.patterns_cache_path.exists():
                with open(self.patterns_cache_path, 'rb') as f:
                    self.pattern_cache = pickle.load(f)
                logger.info("Loaded pattern cache from disk")
            else:
                self.pattern_cache = {
                    'speaker_patterns': {},
                    'temporal_patterns': {},
                    'context_patterns': {},
                    'error_patterns': {},
                    'last_updated': None
                }
        except Exception as e:
            logger.error(f"Error loading pattern cache: {e}")
            self.pattern_cache = {}
    
    def _save_pattern_cache(self):
        """Save pattern analysis results to cache."""
        try:
            self.pattern_cache['last_updated'] = datetime.now().isoformat()
            with open(self.patterns_cache_path, 'wb') as f:
                pickle.dump(self.pattern_cache, f)
            logger.info("Saved pattern cache to disk")
        except Exception as e:
            logger.error(f"Error saving pattern cache: {e}")
    
    def analyze_correction_patterns(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Analyze comprehensive patterns in human corrections."""
        logger.info("Starting comprehensive pattern analysis")
        
        # Check if we need to refresh analysis
        if not force_refresh and self._is_cache_valid():
            logger.info("Using cached pattern analysis")
            return self.pattern_cache
        
        try:
            # Get correction data
            corrections_data = self._get_corrections_data()
            recognition_data = self._get_recognition_data()
            
            if not corrections_data:
                logger.warning("No correction data available for analysis")
                return {}
            
            # Perform different types of pattern analysis
            analysis_results = {
                'speaker_patterns': self._analyze_speaker_patterns(corrections_data, recognition_data),
                'temporal_patterns': self._analyze_temporal_patterns(corrections_data),
                'context_patterns': self._analyze_context_patterns(corrections_data),
                'error_patterns': self._analyze_error_patterns(corrections_data, recognition_data),
                'confidence_patterns': self._analyze_confidence_patterns(recognition_data),
                'correction_frequency': self._analyze_correction_frequency(corrections_data),
                'analysis_timestamp': datetime.now().isoformat(),
                'data_summary': {
                    'total_corrections': len(corrections_data),
                    'unique_speakers': len(set(c['speaker_name'] for c in corrections_data)),
                    'unique_transcripts': len(set(c['transcript_file'] for c in corrections_data)),
                    'date_range': self._get_date_range(corrections_data)
                }
            }
            
            # Update cache
            self.pattern_cache.update(analysis_results)
            self._save_pattern_cache()
            
            logger.info(f"Completed pattern analysis: {analysis_results['data_summary']}")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}")
            return {'error': str(e)}
    
    def _is_cache_valid(self, max_age_hours: int = 24) -> bool:
        """Check if pattern cache is still valid."""
        if not self.pattern_cache.get('last_updated'):
            return False
        
        last_updated = datetime.fromisoformat(self.pattern_cache['last_updated'])
        max_age = timedelta(hours=max_age_hours)
        
        return datetime.now() - last_updated < max_age
    
    def _get_corrections_data(self) -> List[Dict[str, Any]]:
        """Get correction data from Phase 6A database."""
        try:
            if not self.corrections_db_path.exists():
                logger.warning("Corrections database not found")
                return []
            
            with sqlite3.connect(self.corrections_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                corrections = conn.execute("""
                    SELECT c.*, 
                           rs.reviewer_id as session_reviewer,
                           rs.start_time as session_start,
                           rs.progress_data
                    FROM corrections c
                    LEFT JOIN review_sessions rs ON c.transcript_file = rs.transcript_file
                    WHERE c.is_active = 1
                    ORDER BY c.created_at
                """).fetchall()
                
                return [dict(correction) for correction in corrections]
                
        except Exception as e:
            logger.error(f"Error getting corrections data: {e}")
            return []
    
    def _get_recognition_data(self) -> List[Dict[str, Any]]:
        """Get recognition data from Phase 6B database."""
        try:
            if not self.voice_models_db_path.exists():
                logger.warning("Voice models database not found")
                return []
            
            with sqlite3.connect(self.voice_models_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                recognitions = conn.execute("""
                    SELECT * FROM recognition_results
                    ORDER BY created_at
                """).fetchall()
                
                return [dict(recognition) for recognition in recognitions]
                
        except Exception as e:
            logger.error(f"Error getting recognition data: {e}")
            return []
    
    def _create_speaker_stats_dict(self):
        """Create default speaker statistics dictionary."""
        return {
            'total_corrections': 0,
            'correction_contexts': [],
            'common_misidentifications': Counter(),
            'avg_confidence_before_correction': 0.0,
            'transcript_files': set(),
            'correction_times': [],
            'difficulty_score': 0.0
        }
    
    def _create_context_stats_dict(self):
        """Create default context statistics dictionary."""
        return {
            'correction_count': 0,
            'speakers': set(),
            'common_speakers': Counter(),
            'file_patterns': []
        }
    
    def _analyze_speaker_patterns(self, 
                                 corrections_data: List[Dict], 
                                 recognition_data: List[Dict]) -> Dict[str, Any]:
        """Analyze speaker-specific correction patterns."""
        logger.info("Analyzing speaker patterns")
        
        speaker_stats = defaultdict(self._create_speaker_stats_dict)
        
        # Analyze corrections by speaker
        for correction in corrections_data:
            speaker = correction['speaker_name']
            speaker_stats[speaker]['total_corrections'] += 1
            speaker_stats[speaker]['transcript_files'].add(correction['transcript_file'])
            speaker_stats[speaker]['correction_times'].append(correction['created_at'])
            
            # Extract context from transcript file name
            context = self._extract_context_from_filename(correction['transcript_file'])
            speaker_stats[speaker]['correction_contexts'].append(context)
        
        # Analyze recognition data for misidentifications
        for recognition in recognition_data:
            if recognition.get('correction_applied') and recognition.get('human_verified'):
                original_speaker = recognition['recognized_speaker']
                if original_speaker:
                    # Find corresponding correction
                    for correction in corrections_data:
                        if (correction['transcript_file'] in recognition['audio_segment_id'] and
                            correction['speaker_name'] != original_speaker):
                            
                            speaker_stats[correction['speaker_name']]['common_misidentifications'][original_speaker] += 1
                            break
        
        # Calculate difficulty scores and statistics
        processed_stats = {}
        for speaker, stats in speaker_stats.items():
            if stats['total_corrections'] >= self.min_corrections_for_pattern:
                # Convert sets to lists for serialization
                stats['transcript_files'] = list(stats['transcript_files'])
                
                # Calculate difficulty score based on correction frequency and context diversity
                context_diversity = len(set(stats['correction_contexts'])) / max(len(stats['correction_contexts']), 1)
                transcript_diversity = len(stats['transcript_files'])
                stats['difficulty_score'] = stats['total_corrections'] * (1 + context_diversity) * transcript_diversity
                
                # Get most common contexts and misidentifications
                stats['common_contexts'] = Counter(stats['correction_contexts']).most_common(3)
                stats['most_confused_with'] = stats['common_misidentifications'].most_common(3)
                
                processed_stats[speaker] = stats
        
        return {
            'speaker_difficulty_ranking': sorted(
                processed_stats.items(), 
                key=lambda x: x[1]['difficulty_score'], 
                reverse=True
            )[:10],
            'total_speakers_analyzed': len(processed_stats),
            'speakers_needing_attention': [
                speaker for speaker, stats in processed_stats.items()
                if stats['difficulty_score'] > np.mean([s['difficulty_score'] for s in processed_stats.values()])
            ]
        }
    
    def _analyze_temporal_patterns(self, corrections_data: List[Dict]) -> Dict[str, Any]:
        """Analyze temporal patterns in corrections."""
        logger.info("Analyzing temporal patterns")
        
        if not corrections_data:
            return {}
        
        # Convert timestamps to datetime objects
        correction_times = []
        for correction in corrections_data:
            try:
                dt = datetime.fromisoformat(correction['created_at'])
                correction_times.append({
                    'datetime': dt,
                    'hour': dt.hour,
                    'day_of_week': dt.weekday(),
                    'speaker': correction['speaker_name'],
                    'transcript': correction['transcript_file']
                })
            except Exception as e:
                logger.warning(f"Error parsing timestamp {correction['created_at']}: {e}")
                continue
        
        if not correction_times:
            return {}
        
        # Analyze patterns
        hourly_distribution = Counter(ct['hour'] for ct in correction_times)
        daily_distribution = Counter(ct['day_of_week'] for ct in correction_times)
        
        # Find peak correction periods
        peak_hour = hourly_distribution.most_common(1)[0][0]
        peak_day = daily_distribution.most_common(1)[0][0]
        
        # Analyze correction clustering
        correction_intervals = []
        sorted_times = sorted(correction_times, key=lambda x: x['datetime'])
        for i in range(1, len(sorted_times)):
            interval = (sorted_times[i]['datetime'] - sorted_times[i-1]['datetime']).total_seconds() / 60
            correction_intervals.append(interval)
        
        return {
            'hourly_distribution': dict(hourly_distribution),
            'daily_distribution': dict(daily_distribution),
            'peak_correction_hour': peak_hour,
            'peak_correction_day': peak_day,
            'avg_correction_interval_minutes': np.mean(correction_intervals) if correction_intervals else 0,
            'correction_bursts': self._identify_correction_bursts(sorted_times),
            'seasonal_patterns': self._analyze_seasonal_patterns(sorted_times)
        }
    
    def _analyze_context_patterns(self, corrections_data: List[Dict]) -> Dict[str, Any]:
        """Analyze contextual patterns in corrections."""
        logger.info("Analyzing context patterns")
        
        context_stats = defaultdict(self._create_context_stats_dict)
        
        for correction in corrections_data:
            context = self._extract_context_from_filename(correction['transcript_file'])
            
            context_stats[context]['correction_count'] += 1
            context_stats[context]['speakers'].add(correction['speaker_name'])
            context_stats[context]['common_speakers'][correction['speaker_name']] += 1
            context_stats[context]['file_patterns'].append(correction['transcript_file'])
        
        # Process context statistics
        processed_contexts = {}
        for context, stats in context_stats.items():
            if stats['correction_count'] >= self.min_corrections_for_pattern:
                processed_contexts[context] = {
                    'correction_count': stats['correction_count'],
                    'unique_speakers': len(stats['speakers']),
                    'most_corrected_speakers': stats['common_speakers'].most_common(3),
                    'complexity_score': stats['correction_count'] * len(stats['speakers'])
                }
        
        return {
            'context_complexity_ranking': sorted(
                processed_contexts.items(),
                key=lambda x: x[1]['complexity_score'],
                reverse=True
            ),
            'high_correction_contexts': [
                context for context, stats in processed_contexts.items()
                if stats['correction_count'] > np.mean([s['correction_count'] for s in processed_contexts.values()])
            ]
        }
    
    def _analyze_error_patterns(self, 
                               corrections_data: List[Dict], 
                               recognition_data: List[Dict]) -> Dict[str, Any]:
        """Analyze error patterns and misidentification causes."""
        logger.info("Analyzing error patterns")
        
        error_patterns = {
            'common_misidentifications': Counter(),
            'confidence_vs_errors': {},
            'systematic_errors': [],
            'speaker_confusion_matrix': {}
        }
        
        # Build speaker confusion matrix from corrections
        for recognition in recognition_data:
            if recognition.get('correction_applied') and recognition.get('human_verified'):
                original_speaker = recognition.get('recognized_speaker', 'Unknown')
                
                # Find the correct speaker from corrections
                for correction in corrections_data:
                    if correction['transcript_file'] in recognition.get('audio_segment_id', ''):
                        correct_speaker = correction['speaker_name']
                        # Handle confusion matrix with regular dict
                        if original_speaker not in error_patterns['speaker_confusion_matrix']:
                            error_patterns['speaker_confusion_matrix'][original_speaker] = {}
                        if correct_speaker not in error_patterns['speaker_confusion_matrix'][original_speaker]:
                            error_patterns['speaker_confusion_matrix'][original_speaker][correct_speaker] = 0
                        error_patterns['speaker_confusion_matrix'][original_speaker][correct_speaker] += 1
                        error_patterns['common_misidentifications'][(original_speaker, correct_speaker)] += 1
                        break
        
        # Analyze confidence vs error relationship
        confidence_bins = np.arange(0, 1.1, 0.1)
        for recognition in recognition_data:
            confidence = recognition.get('confidence_score', 0)
            bin_idx = np.digitize(confidence, confidence_bins) - 1
            bin_key = f"{confidence_bins[bin_idx]:.1f}-{confidence_bins[min(bin_idx + 1, len(confidence_bins) - 1)]:.1f}"
            
            if bin_key not in error_patterns['confidence_vs_errors']:
                error_patterns['confidence_vs_errors'][bin_key] = {'total': 0, 'errors': 0}
            
            error_patterns['confidence_vs_errors'][bin_key]['total'] += 1
            if recognition.get('correction_applied'):
                error_patterns['confidence_vs_errors'][bin_key]['errors'] += 1
        
        # Identify systematic errors
        for (original, correct), count in error_patterns['common_misidentifications'].most_common(10):
            if count >= 3:  # Minimum occurrences for systematic error
                error_patterns['systematic_errors'].append({
                    'misidentified_as': original,
                    'actual_speaker': correct,
                    'frequency': count,
                    'error_type': self._classify_error_type(original, correct)
                })
        
        return error_patterns
    
    def _analyze_confidence_patterns(self, recognition_data: List[Dict]) -> Dict[str, Any]:
        """Analyze confidence score patterns and calibration."""
        logger.info("Analyzing confidence patterns")
        
        if not recognition_data:
            return {}
        
        confidences = [r.get('confidence_score', 0) for r in recognition_data]
        
        return {
            'confidence_distribution': {
                'mean': np.mean(confidences),
                'std': np.std(confidences),
                'median': np.median(confidences),
                'min': np.min(confidences),
                'max': np.max(confidences)
            },
            'confidence_calibration': self._analyze_confidence_calibration(recognition_data),
            'threshold_analysis': self._analyze_threshold_performance(recognition_data)
        }
    
    def _analyze_correction_frequency(self, corrections_data: List[Dict]) -> Dict[str, Any]:
        """Analyze frequency and timing of corrections."""
        logger.info("Analyzing correction frequency")
        
        if not corrections_data:
            return {}
        
        # Group corrections by transcript
        transcript_corrections = defaultdict(list)
        for correction in corrections_data:
            transcript_corrections[correction['transcript_file']].append(correction)
        
        correction_frequencies = [len(corrections) for corrections in transcript_corrections.values()]
        
        return {
            'avg_corrections_per_transcript': np.mean(correction_frequencies),
            'max_corrections_per_transcript': np.max(correction_frequencies),
            'transcripts_with_high_corrections': [
                transcript for transcript, corrections in transcript_corrections.items()
                if len(corrections) > np.mean(correction_frequencies) + np.std(correction_frequencies)
            ],
            'correction_distribution': Counter(correction_frequencies)
        }
    
    def _extract_context_from_filename(self, filename: str) -> str:
        """Extract context information from transcript filename."""
        # Simple context extraction - can be enhanced
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
    
    def _get_date_range(self, corrections_data: List[Dict]) -> Dict[str, str]:
        """Get date range of corrections data."""
        if not corrections_data:
            return {}
        
        timestamps = [c['created_at'] for c in corrections_data if c.get('created_at')]
        if not timestamps:
            return {}
        
        timestamps.sort()
        return {
            'earliest': timestamps[0],
            'latest': timestamps[-1],
            'span_days': (datetime.fromisoformat(timestamps[-1]) - 
                         datetime.fromisoformat(timestamps[0])).days
        }
    
    def _identify_correction_bursts(self, sorted_times: List[Dict]) -> List[Dict]:
        """Identify periods of high correction activity."""
        bursts = []
        burst_threshold_minutes = 30
        min_burst_size = 3
        
        if len(sorted_times) < min_burst_size:
            return bursts
        
        current_burst = [sorted_times[0]]
        
        for i in range(1, len(sorted_times)):
            time_diff = (sorted_times[i]['datetime'] - current_burst[-1]['datetime']).total_seconds() / 60
            
            if time_diff <= burst_threshold_minutes:
                current_burst.append(sorted_times[i])
            else:
                if len(current_burst) >= min_burst_size:
                    bursts.append({
                        'start_time': current_burst[0]['datetime'].isoformat(),
                        'end_time': current_burst[-1]['datetime'].isoformat(),
                        'correction_count': len(current_burst),
                        'duration_minutes': (current_burst[-1]['datetime'] - current_burst[0]['datetime']).total_seconds() / 60,
                        'speakers_involved': list(set(ct['speaker'] for ct in current_burst))
                    })
                current_burst = [sorted_times[i]]
        
        # Check final burst
        if len(current_burst) >= min_burst_size:
            bursts.append({
                'start_time': current_burst[0]['datetime'].isoformat(),
                'end_time': current_burst[-1]['datetime'].isoformat(),
                'correction_count': len(current_burst),
                'duration_minutes': (current_burst[-1]['datetime'] - current_burst[0]['datetime']).total_seconds() / 60,
                'speakers_involved': list(set(ct['speaker'] for ct in current_burst))
            })
        
        return bursts
    
    def _analyze_seasonal_patterns(self, sorted_times: List[Dict]) -> Dict[str, Any]:
        """Analyze seasonal/periodic patterns in corrections."""
        if len(sorted_times) < 10:
            return {}
        
        # Group by month
        monthly_counts = defaultdict(int)
        for ct in sorted_times:
            month_key = ct['datetime'].strftime('%Y-%m')
            monthly_counts[month_key] += 1
        
        return {
            'monthly_distribution': dict(monthly_counts),
            'most_active_month': max(monthly_counts.items(), key=lambda item: item[1])[0] if monthly_counts else None
        }
    
    def _classify_error_type(self, original_speaker: str, correct_speaker: str) -> str:
        """Classify the type of identification error."""
        if not original_speaker or original_speaker.lower() == 'unknown':
            return 'unknown_speaker'
        elif 'sen.' in original_speaker.lower() and 'sen.' in correct_speaker.lower():
            return 'senator_confusion'
        elif original_speaker.lower() == correct_speaker.lower():
            return 'case_mismatch'
        else:
            return 'systematic_misidentification'
    
    def _analyze_confidence_calibration(self, recognition_data: List[Dict]) -> Dict[str, Any]:
        """Analyze how well confidence scores reflect actual accuracy."""
        confidence_bins = np.arange(0, 1.1, 0.1)
        calibration_data = {}
        
        for recognition in recognition_data:
            confidence = recognition.get('confidence_score', 0)
            is_correct = not recognition.get('correction_applied', False)
            
            bin_idx = np.digitize(confidence, confidence_bins) - 1
            bin_key = f"{confidence_bins[bin_idx]:.1f}"
            
            if bin_key not in calibration_data:
                calibration_data[bin_key] = {'total': 0, 'correct': 0}
            
            calibration_data[bin_key]['total'] += 1
            if is_correct:
                calibration_data[bin_key]['correct'] += 1
        
        # Calculate calibration accuracy for each bin
        for bin_key, data in calibration_data.items():
            if data['total'] > 0:
                data['accuracy'] = data['correct'] / data['total']
            else:
                data['accuracy'] = 0
        
        return calibration_data
    
    def _analyze_threshold_performance(self, recognition_data: List[Dict]) -> Dict[str, Any]:
        """Analyze performance at different confidence thresholds."""
        thresholds = np.arange(0.1, 1.0, 0.1)
        threshold_performance = {}
        
        for threshold in thresholds:
            above_threshold = [r for r in recognition_data if r.get('confidence_score', 0) >= threshold]
            
            if above_threshold:
                correct_above = sum(1 for r in above_threshold if not r.get('correction_applied', False))
                accuracy = correct_above / len(above_threshold)
                coverage = len(above_threshold) / len(recognition_data)
                
                threshold_performance[f"{threshold:.1f}"] = {
                    'accuracy': accuracy,
                    'coverage': coverage,
                    'f1_score': 2 * (accuracy * coverage) / (accuracy + coverage) if (accuracy + coverage) > 0 else 0
                }
        
        return threshold_performance
    
    def get_pattern_insights(self) -> Dict[str, Any]:
        """Get actionable insights from pattern analysis."""
        if not self.pattern_cache:
            logger.warning("No pattern cache available - run analyze_correction_patterns first")
            return {}
        
        insights = {
            'recommendations': [],
            'alerts': [],
            'optimization_opportunities': []
        }
        
        # Generate recommendations based on patterns
        speaker_patterns = self.pattern_cache.get('speaker_patterns', {})
        if speaker_patterns.get('speakers_needing_attention'):
            insights['recommendations'].append({
                'type': 'speaker_focus',
                'message': f"Focus on improving models for speakers: {', '.join(speaker_patterns['speakers_needing_attention'][:3])}",
                'priority': 'high'
            })
        
        temporal_patterns = self.pattern_cache.get('temporal_patterns', {})
        if temporal_patterns.get('correction_bursts'):
            insights['alerts'].append({
                'type': 'correction_burst',
                'message': f"Detected {len(temporal_patterns['correction_bursts'])} correction bursts - possible systematic issues",
                'priority': 'medium'
            })
        
        error_patterns = self.pattern_cache.get('error_patterns', {})
        if error_patterns.get('systematic_errors'):
            insights['optimization_opportunities'].extend([
                {
                    'type': 'systematic_error',
                    'message': f"Systematic confusion: {error['misidentified_as']} → {error['actual_speaker']} ({error['frequency']} times)",
                    'priority': 'high',
                    'action': 'retrain_model'
                }
                for error in error_patterns['systematic_errors'][:3]
            ])
        
        return insights


if __name__ == "__main__":
    # Test pattern analyzer
    analyzer = PatternAnalyzer()
    
    # Run pattern analysis
    patterns = analyzer.analyze_correction_patterns(force_refresh=True)
    print(f"Pattern analysis results: {json.dumps(patterns, indent=2, default=str)}")
    
    # Get insights
    insights = analyzer.get_pattern_insights()
    print(f"Pattern insights: {json.dumps(insights, indent=2)}")