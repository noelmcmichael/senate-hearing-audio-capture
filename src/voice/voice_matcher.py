#!/usr/bin/env python3
"""
Voice Matcher for Phase 6B

Integration layer between voice recognition and existing speaker identification:
- Enhanced speaker identification using voice patterns
- Confidence scoring and decision making
- Integration with Phase 5 transcription pipeline
- Real-time voice-based speaker detection
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

from .voice_processor import VoiceProcessor
from .speaker_models import SpeakerModelManager
try:
    from ..enrichment.transcript_enricher import TranscriptEnricher
except ImportError:
    # Fallback for testing
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from enrichment.transcript_enricher import TranscriptEnricher


logger = logging.getLogger(__name__)


class VoiceMatcher:
    """Enhanced speaker identification using voice recognition."""
    
    def __init__(self):
        """Initialize voice matcher."""
        self.voice_processor = VoiceProcessor()
        self.model_manager = SpeakerModelManager()
        self.transcript_enricher = TranscriptEnricher()
        
        # Confidence thresholds for decision making
        self.decision_thresholds = {
            'high_confidence_override': 0.85,  # Voice recognition overrides text-based ID
            'medium_confidence_boost': 0.65,   # Voice recognition boosts text-based confidence
            'low_confidence_hint': 0.45,       # Voice recognition provides suggestion
            'minimum_usable': 0.25             # Below this, ignore voice recognition
        }
        
        # Combination weights for voice + text identification
        self.combination_weights = {
            'voice_recognition': 0.6,
            'text_patterns': 0.3,
            'context_clues': 0.1
        }
    
    def enhance_speaker_identification(
        self,
        audio_file: Path,
        transcript_segments: List[Dict[str, Any]],
        hearing_context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Enhance speaker identification using voice recognition."""
        try:
            logger.info(f"Enhancing speaker identification for {audio_file}")
            
            enhanced_segments = []
            
            for segment in transcript_segments:
                try:
                    # Extract audio segment
                    segment_audio = self._extract_audio_segment(
                        audio_file, 
                        segment.get('start', 0), 
                        segment.get('end', 0)
                    )
                    
                    if segment_audio:
                        # Get voice-based identification
                        voice_result = self._identify_speaker_by_voice(
                            segment_audio, 
                            hearing_context
                        )
                        
                        # Get text-based identification (existing system)
                        text_result = self._identify_speaker_by_text(
                            segment, 
                            hearing_context
                        )
                        
                        # Combine voice and text identification
                        combined_result = self._combine_identification_results(
                            voice_result, 
                            text_result, 
                            segment
                        )
                        
                        # Update segment with enhanced identification
                        enhanced_segment = segment.copy()
                        enhanced_segment.update({
                            'voice_identification': voice_result,
                            'text_identification': text_result,
                            'enhanced_speaker': combined_result['speaker'],
                            'enhanced_confidence': combined_result['confidence'],
                            'identification_method': combined_result['method'],
                            'identification_sources': combined_result['sources']
                        })
                        
                        enhanced_segments.append(enhanced_segment)
                    else:
                        # No audio available, use original segment
                        enhanced_segments.append(segment)
                
                except Exception as e:
                    logger.error(f"Error enhancing segment {segment.get('id', 'unknown')}: {e}")
                    enhanced_segments.append(segment)
            
            logger.info(f"Enhanced {len(enhanced_segments)} segments with voice recognition")
            return enhanced_segments
            
        except Exception as e:
            logger.error(f"Error enhancing speaker identification: {e}")
            return transcript_segments  # Return original segments on error
    
    def _extract_audio_segment(
        self, 
        audio_file: Path, 
        start_time: float, 
        end_time: float
    ) -> Optional[Path]:
        """Extract audio segment for voice analysis."""
        try:
            import subprocess
            
            if end_time <= start_time:
                return None
            
            duration = end_time - start_time
            if duration < 1.0:  # Too short for reliable voice recognition
                return None
            
            # Create temporary segment file
            segment_file = Path(f"/tmp/segment_{start_time}_{end_time}.wav")
            
            # Use ffmpeg to extract segment
            cmd = [
                'ffmpeg',
                '-i', str(audio_file),
                '-ss', str(start_time),
                '-t', str(duration),
                '-ac', '1',  # Mono
                '-ar', '16000',  # 16kHz sample rate
                '-y',  # Overwrite
                str(segment_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and segment_file.exists():
                return segment_file
            else:
                logger.error(f"ffmpeg error: {result.stderr}")
                return None
            
        except Exception as e:
            logger.error(f"Error extracting audio segment: {e}")
            return None
    
    def _identify_speaker_by_voice(
        self, 
        audio_segment: Path, 
        hearing_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Identify speaker using voice recognition."""
        try:
            # Get candidate speakers from hearing context
            candidate_speakers = self._get_candidate_speakers(hearing_context)
            
            # Perform voice recognition
            recognition_result = self.model_manager.recognize_speaker_in_audio(
                audio_segment, 
                candidate_speakers
            )
            
            # Clean up temporary file
            try:
                audio_segment.unlink()
            except:
                pass
            
            return {
                'method': 'voice_recognition',
                'speaker': recognition_result.get('recognized_speaker'),
                'confidence': recognition_result.get('confidence_score', 0.0),
                'confidence_level': recognition_result.get('confidence_level', 'very_low'),
                'all_similarities': recognition_result.get('all_similarities', []),
                'audio_quality': recognition_result.get('audio_quality', 0.0),
                'error': recognition_result.get('error')
            }
            
        except Exception as e:
            logger.error(f"Error in voice-based speaker identification: {e}")
            return {
                'method': 'voice_recognition',
                'speaker': None,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _identify_speaker_by_text(
        self, 
        segment: Dict[str, Any], 
        hearing_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Identify speaker using text patterns (existing system)."""
        try:
            # Use existing transcript enricher
            text = segment.get('text', '')
            
            if not text:
                return {
                    'method': 'text_patterns',
                    'speaker': None,
                    'confidence': 0.0,
                    'error': 'No text content'
                }
            
            # Get speaker from existing identification
            existing_speaker = segment.get('speaker')
            existing_confidence = segment.get('speaker_confidence', 0.5)
            
            # Enhanced text pattern matching
            text_patterns = self._analyze_text_patterns(text, hearing_context)
            
            # Combine existing and pattern-based identification
            if existing_speaker and existing_confidence > 0.6:
                speaker = existing_speaker
                confidence = existing_confidence
            elif text_patterns['speaker']:
                speaker = text_patterns['speaker']
                confidence = text_patterns['confidence']
            else:
                speaker = existing_speaker
                confidence = max(0.1, existing_confidence)
            
            return {
                'method': 'text_patterns',
                'speaker': speaker,
                'confidence': confidence,
                'patterns_found': text_patterns.get('patterns', []),
                'existing_speaker': existing_speaker,
                'existing_confidence': existing_confidence
            }
            
        except Exception as e:
            logger.error(f"Error in text-based speaker identification: {e}")
            return {
                'method': 'text_patterns',
                'speaker': segment.get('speaker'),
                'confidence': 0.1,
                'error': str(e)
            }
    
    def _analyze_text_patterns(
        self, 
        text: str, 
        hearing_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze text for speaker identification patterns."""
        try:
            patterns = []
            confidence = 0.0
            identified_speaker = None
            
            text_lower = text.lower()
            
            # Congressional role patterns
            role_patterns = {
                'Chair': ['mr. chairman', 'madam chair', 'thank you, chair'],
                'Ranking Member': ['ranking member', 'as ranking member'],
                'Member': ['the gentleman from', 'the gentlewoman from', 'yield'],
                'Witness': ['thank you for having me', 'i appreciate the opportunity']
            }
            
            for role, pattern_list in role_patterns.items():
                for pattern in pattern_list:
                    if pattern in text_lower:
                        patterns.append({
                            'type': 'role_pattern',
                            'pattern': pattern,
                            'role': role,
                            'confidence': 0.3
                        })
            
            # Name mention patterns
            if hearing_context and 'committee_members' in hearing_context:
                for member in hearing_context['committee_members']:
                    member_names = [
                        member.get('name', '').lower(),
                        member.get('display_name', '').lower(),
                        *[alias.lower() for alias in member.get('aliases', [])]
                    ]
                    
                    for name in member_names:
                        if name and name in text_lower:
                            patterns.append({
                                'type': 'name_mention',
                                'name': name,
                                'speaker': member.get('display_name', member.get('name')),
                                'confidence': 0.7
                            })
                            
                            if confidence < 0.7:
                                identified_speaker = member.get('display_name', member.get('name'))
                                confidence = 0.7
            
            # State/party references
            state_patterns = ['from [state]', 'senator from', 'representative from']
            for pattern in state_patterns:
                if any(phrase in text_lower for phrase in ['from texas', 'from california', 'from new york']):
                    patterns.append({
                        'type': 'geographic_reference',
                        'confidence': 0.2
                    })
            
            return {
                'speaker': identified_speaker,
                'confidence': confidence,
                'patterns': patterns
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text patterns: {e}")
            return {'speaker': None, 'confidence': 0.0, 'patterns': []}
    
    def _combine_identification_results(
        self,
        voice_result: Dict[str, Any],
        text_result: Dict[str, Any],
        segment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine voice and text identification results."""
        try:
            voice_speaker = voice_result.get('speaker')
            voice_confidence = voice_result.get('confidence', 0.0)
            
            text_speaker = text_result.get('speaker')
            text_confidence = text_result.get('confidence', 0.0)
            
            # Decision logic based on confidence thresholds
            if voice_confidence >= self.decision_thresholds['high_confidence_override']:
                # High confidence voice recognition overrides everything
                return {
                    'speaker': voice_speaker,
                    'confidence': voice_confidence,
                    'method': 'voice_override',
                    'sources': ['voice_recognition']
                }
            
            elif voice_speaker == text_speaker and voice_confidence >= self.decision_thresholds['minimum_usable']:
                # Voice and text agree
                combined_confidence = (
                    voice_confidence * self.combination_weights['voice_recognition'] +
                    text_confidence * self.combination_weights['text_patterns']
                )
                
                return {
                    'speaker': voice_speaker,
                    'confidence': min(0.95, combined_confidence + 0.1),  # Boost for agreement
                    'method': 'voice_text_agreement',
                    'sources': ['voice_recognition', 'text_patterns']
                }
            
            elif voice_confidence >= self.decision_thresholds['medium_confidence_boost']:
                # Medium confidence voice recognition
                if text_confidence < 0.3:
                    # Low text confidence, trust voice
                    return {
                        'speaker': voice_speaker,
                        'confidence': voice_confidence,
                        'method': 'voice_primary',
                        'sources': ['voice_recognition']
                    }
                else:
                    # Conflicting results, weight by confidence
                    if voice_confidence > text_confidence:
                        return {
                            'speaker': voice_speaker,
                            'confidence': voice_confidence * 0.8,  # Slight penalty for conflict
                            'method': 'voice_weighted',
                            'sources': ['voice_recognition', 'text_patterns']
                        }
                    else:
                        return {
                            'speaker': text_speaker,
                            'confidence': text_confidence * 0.8,
                            'method': 'text_weighted',
                            'sources': ['text_patterns', 'voice_recognition']
                        }
            
            elif text_confidence >= 0.4:
                # Trust text identification
                voice_boost = 0.0
                if (voice_confidence >= self.decision_thresholds['low_confidence_hint'] and 
                    voice_speaker == text_speaker):
                    voice_boost = 0.1  # Small boost for voice agreement
                
                return {
                    'speaker': text_speaker,
                    'confidence': min(0.9, text_confidence + voice_boost),
                    'method': 'text_primary',
                    'sources': ['text_patterns']
                }
            
            else:
                # Low confidence all around
                if voice_confidence > text_confidence and voice_confidence >= self.decision_thresholds['minimum_usable']:
                    return {
                        'speaker': voice_speaker,
                        'confidence': voice_confidence * 0.7,
                        'method': 'voice_fallback',
                        'sources': ['voice_recognition']
                    }
                else:
                    return {
                        'speaker': text_speaker or 'Unknown Speaker',
                        'confidence': max(0.1, text_confidence),
                        'method': 'low_confidence',
                        'sources': ['text_patterns'] if text_speaker else []
                    }
            
        except Exception as e:
            logger.error(f"Error combining identification results: {e}")
            return {
                'speaker': segment.get('speaker', 'Unknown Speaker'),
                'confidence': 0.1,
                'method': 'error_fallback',
                'sources': [],
                'error': str(e)
            }
    
    def _get_candidate_speakers(self, hearing_context: Dict[str, Any] = None) -> List[str]:
        """Get list of candidate speakers for voice recognition."""
        try:
            candidates = []
            
            if hearing_context and 'committee_members' in hearing_context:
                for member in hearing_context['committee_members']:
                    candidates.append(member.get('display_name', member.get('name', '')))
            
            # Add common witness titles if no specific context
            if not candidates:
                # Get all available speaker models
                stats = self.model_manager.get_model_performance_stats()
                candidates = [model['senator_name'] for model in stats.get('models', [])]
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error getting candidate speakers: {e}")
            return []
    
    def get_enhancement_statistics(self) -> Dict[str, Any]:
        """Get statistics on voice recognition enhancement performance."""
        try:
            # Get model performance stats
            model_stats = self.model_manager.get_model_performance_stats()
            
            # Calculate enhancement metrics
            enhancement_stats = {
                'total_voice_models': model_stats.get('total_models', 0),
                'total_recognitions': model_stats.get('total_recognitions', 0),
                'model_details': model_stats.get('models', []),
                'recognition_performance': model_stats.get('recognition_stats', [])
            }
            
            # Calculate accuracy improvements
            if model_stats.get('recognition_stats'):
                accuracies = []
                for stat in model_stats['recognition_stats']:
                    if stat['verified_recognitions'] > 0:
                        accuracy = stat['correct_recognitions'] / stat['verified_recognitions']
                        accuracies.append(accuracy)
                
                if accuracies:
                    enhancement_stats['average_accuracy'] = np.mean(accuracies)
                    enhancement_stats['accuracy_range'] = {
                        'min': np.min(accuracies),
                        'max': np.max(accuracies)
                    }
            
            return enhancement_stats
            
        except Exception as e:
            logger.error(f"Error getting enhancement statistics: {e}")
            return {'error': str(e)}
    
    def update_models_from_corrections(self) -> Dict[str, Any]:
        """Update voice models using Phase 6A human corrections."""
        try:
            # Integrate with Phase 6A corrections
            integration_result = self.model_manager.integrate_with_phase6a_corrections()
            
            if 'error' in integration_result:
                return integration_result
            
            # Update models with new data
            update_result = self.model_manager.update_speaker_models()
            
            return {
                'corrections_integrated': integration_result.get('corrections_processed', 0),
                'models_updated': len([r for r in update_result.values() if r.get('status') == 'success']),
                'update_details': update_result,
                'integration_status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error updating models from corrections: {e}")
            return {'error': str(e)}


if __name__ == "__main__":
    # Test voice matcher
    matcher = VoiceMatcher()
    
    # Get enhancement statistics
    stats = matcher.get_enhancement_statistics()
    print(f"Voice recognition enhancement stats: {stats}")
    
    # Test model updates from corrections
    update_result = matcher.update_models_from_corrections()
    print(f"Model update result: {update_result}")