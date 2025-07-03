#!/usr/bin/env python3
"""
Professional Transcript Comparison Tool

Compare Whisper-generated transcripts against professional politicopro standard
to validate accuracy and identify areas for improvement.
"""

import json
import difflib
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse
import logging


class TranscriptComparator:
    """
    Compare Whisper transcripts against professional standards.
    """
    
    def __init__(self, hearing_id: str = "33"):
        self.hearing_id = hearing_id
        self.project_root = Path(__file__).parent
        self.logger = logging.getLogger(__name__)
        
    def load_professional_transcript(self, transcript_path: Path) -> Dict:
        """Load the professional transcript (politicopro structured format)"""
        self.logger.info(f"Loading professional transcript: {transcript_path}")
        
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.logger.info(f"   Professional transcript loaded: {len(data.get('segments', []))} segments")
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading professional transcript: {e}")
            return {}
    
    def load_whisper_transcript(self, transcript_path: Path) -> Dict:
        """Load the Whisper-generated transcript"""
        self.logger.info(f"Loading Whisper transcript: {transcript_path}")
        
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Extract transcript data from nested structure
            if 'transcription' in data and 'transcription' in data['transcription']:
                transcript_data = data['transcription']['transcription']
            else:
                transcript_data = data
                
            segments = transcript_data.get('segments', [])
            text = transcript_data.get('text', '')
            
            self.logger.info(f"   Whisper transcript loaded: {len(segments)} segments, {len(text)} characters")
            
            return {
                'text': text,
                'segments': segments,
                'metadata': data.get('metadata', {})
            }
            
        except Exception as e:
            self.logger.error(f"Error loading Whisper transcript: {e}")
            return {}
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison by removing extra whitespace and standardizing punctuation"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Standardize punctuation
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"[''']", "'", text)
        text = re.sub(r'[–—]', '-', text)
        
        # Remove speaker indicators for content comparison
        text = re.sub(r'^(CHAIR|RANKING|MEMBER|WITNESS|Mr\.|Ms\.|Mrs\.|Dr\.|Sen\.|Rep\.)\s*[A-Z]+[:\.]?\s*', '', text)
        
        return text
    
    def extract_words(self, text: str) -> List[str]:
        """Extract words from text for word-level comparison"""
        # Split on whitespace and punctuation, keep only alphanumeric
        words = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
        return words
    
    def calculate_word_accuracy(self, reference_words: List[str], hypothesis_words: List[str]) -> Dict:
        """Calculate word-level accuracy metrics"""
        
        # Use difflib to find matching sequences
        matcher = difflib.SequenceMatcher(None, reference_words, hypothesis_words)
        matches = matcher.get_matching_blocks()
        
        # Calculate metrics
        total_reference_words = len(reference_words)
        total_hypothesis_words = len(hypothesis_words)
        
        # Count matching words
        matching_words = sum(match.size for match in matches)
        
        if total_reference_words == 0:
            word_accuracy = 0.0
        else:
            word_accuracy = matching_words / total_reference_words
            
        # Calculate insertion, deletion, substitution rates
        opcodes = matcher.get_opcodes()
        insertions = sum(j2 - j1 for tag, i1, i2, j1, j2 in opcodes if tag == 'insert')
        deletions = sum(i2 - i1 for tag, i1, i2, j1, j2 in opcodes if tag == 'delete')
        substitutions = sum(min(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in opcodes if tag == 'replace')
        
        return {
            'word_accuracy': word_accuracy,
            'total_reference_words': total_reference_words,
            'total_hypothesis_words': total_hypothesis_words,
            'matching_words': matching_words,
            'insertions': insertions,
            'deletions': deletions,
            'substitutions': substitutions,
            'word_error_rate': 1 - word_accuracy if word_accuracy > 0 else 1.0
        }
    
    def compare_content_structure(self, professional: Dict, whisper: Dict) -> Dict:
        """Compare overall content structure and coverage"""
        
        prof_text = professional.get('text', '')
        whisper_text = whisper.get('text', '')
        
        prof_segments = professional.get('segments', [])
        whisper_segments = whisper.get('segments', [])
        
        # Normalize texts for comparison
        prof_normalized = self.normalize_text(prof_text)
        whisper_normalized = self.normalize_text(whisper_text)
        
        # Extract words for detailed comparison
        prof_words = self.extract_words(prof_normalized)
        whisper_words = self.extract_words(whisper_normalized)
        
        # Calculate word-level accuracy
        word_metrics = self.calculate_word_accuracy(prof_words, whisper_words)
        
        # Content coverage analysis
        prof_length = len(prof_text)
        whisper_length = len(whisper_text)
        
        length_ratio = whisper_length / prof_length if prof_length > 0 else 0
        
        return {
            'content_metrics': {
                'professional_length': prof_length,
                'whisper_length': whisper_length,
                'length_ratio': length_ratio,
                'professional_segments': len(prof_segments),
                'whisper_segments': len(whisper_segments),
                'segment_ratio': len(whisper_segments) / len(prof_segments) if prof_segments else 0
            },
            'word_accuracy_metrics': word_metrics,
            'text_samples': {
                'professional_start': prof_text[:300] if prof_text else "",
                'whisper_start': whisper_text[:300] if whisper_text else "",
                'professional_normalized': prof_normalized[:300] if prof_normalized else "",
                'whisper_normalized': whisper_normalized[:300] if whisper_normalized else ""
            }
        }
    
    def analyze_speaker_identification(self, professional: Dict, whisper: Dict) -> Dict:
        """Analyze speaker identification accuracy"""
        
        prof_segments = professional.get('segments', [])
        whisper_segments = whisper.get('segments', [])
        
        # Extract speaker information
        prof_speakers = set()
        whisper_speakers = set()
        
        for seg in prof_segments:
            speaker = seg.get('speaker', 'Unknown')
            if speaker and speaker != 'Unknown':
                prof_speakers.add(speaker)
                
        for seg in whisper_segments:
            speaker = seg.get('speaker', 'Unknown')
            if speaker and speaker != 'Unknown':
                whisper_speakers.add(speaker)
        
        # Calculate speaker identification metrics
        common_speakers = prof_speakers.intersection(whisper_speakers)
        
        return {
            'professional_speakers': sorted(list(prof_speakers)),
            'whisper_speakers': sorted(list(whisper_speakers)),
            'common_speakers': sorted(list(common_speakers)),
            'speaker_identification_rate': len(common_speakers) / len(prof_speakers) if prof_speakers else 0,
            'total_professional_speakers': len(prof_speakers),
            'total_whisper_speakers': len(whisper_speakers)
        }
    
    def generate_comparison_report(self, professional: Dict, whisper: Dict, output_path: Path) -> Dict:
        """Generate comprehensive comparison report"""
        
        self.logger.info("Generating comprehensive comparison report...")
        
        # Content structure comparison
        content_analysis = self.compare_content_structure(professional, whisper)
        
        # Speaker identification analysis
        speaker_analysis = self.analyze_speaker_identification(professional, whisper)
        
        # Overall assessment
        word_accuracy = content_analysis['word_accuracy_metrics']['word_accuracy']
        
        if word_accuracy >= 0.9:
            overall_quality = "EXCELLENT"
        elif word_accuracy >= 0.8:
            overall_quality = "GOOD"
        elif word_accuracy >= 0.7:
            overall_quality = "FAIR"
        else:
            overall_quality = "POOR"
        
        # Create comprehensive report
        report = {
            'comparison_metadata': {
                'hearing_id': self.hearing_id,
                'comparison_timestamp': datetime.now().isoformat(),
                'professional_transcript_source': 'politicopro',
                'whisper_transcript_source': 'OpenAI Whisper (preprocessed audio)',
                'comparison_tool_version': '1.0'
            },
            'content_analysis': content_analysis,
            'speaker_analysis': speaker_analysis,
            'overall_assessment': {
                'quality_rating': overall_quality,
                'word_accuracy': word_accuracy,
                'primary_strengths': [],
                'areas_for_improvement': [],
                'recommendation': ""
            },
            'methodology_validation': {
                'preprocessing_effectiveness': "TBD",
                'benchmark_approach_success': "TBD",
                'system_readiness': "TBD"
            }
        }
        
        # Add specific findings
        strengths = []
        improvements = []
        
        if word_accuracy >= 0.8:
            strengths.append("High word accuracy achieved")
        if content_analysis['content_metrics']['length_ratio'] > 0.8:
            strengths.append("Good content coverage")
        if len(whisper['segments']) > 100:
            strengths.append("Detailed segmentation")
            
        if word_accuracy < 0.9:
            improvements.append("Word accuracy could be improved")
        if speaker_analysis['speaker_identification_rate'] < 0.5:
            improvements.append("Speaker identification needs enhancement")
            
        report['overall_assessment']['primary_strengths'] = strengths
        report['overall_assessment']['areas_for_improvement'] = improvements
        
        # Add recommendation
        if word_accuracy >= 0.8:
            report['overall_assessment']['recommendation'] = "System demonstrates good accuracy. Ready for production with minor refinements."
        else:
            report['overall_assessment']['recommendation'] = "System shows promise but needs improvement before production deployment."
            
        # Save report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"Comparison report saved: {output_path}")
        
        return report
    
    def compare_transcripts(self, professional_path: Path, whisper_path: Path, output_dir: Path) -> Dict:
        """Main comparison workflow"""
        
        self.logger.info("🔍 Starting professional transcript comparison...")
        
        # Load transcripts
        professional = self.load_professional_transcript(professional_path)
        whisper = self.load_whisper_transcript(whisper_path)
        
        if not professional or not whisper:
            self.logger.error("Failed to load one or both transcripts")
            return {}
        
        # Generate comparison report
        output_path = output_dir / f"hearing_{self.hearing_id}_benchmark_comparison.json"
        report = self.generate_comparison_report(professional, whisper, output_path)
        
        # Log key findings
        self.logger.info("📊 BENCHMARK COMPARISON RESULTS")
        self.logger.info("=" * 50)
        
        content_metrics = report['content_analysis']['content_metrics']
        word_metrics = report['content_analysis']['word_accuracy_metrics']
        
        self.logger.info(f"   Overall Quality: {report['overall_assessment']['quality_rating']}")
        self.logger.info(f"   Word Accuracy: {word_metrics['word_accuracy']:.3f}")
        self.logger.info(f"   Content Coverage: {content_metrics['length_ratio']:.3f}")
        self.logger.info(f"   Professional Segments: {content_metrics['professional_segments']}")
        self.logger.info(f"   Whisper Segments: {content_metrics['whisper_segments']}")
        
        return report


def main():
    """Command line interface for transcript comparison"""
    
    parser = argparse.ArgumentParser(description='Compare Whisper transcript against professional standard')
    parser.add_argument('--hearing-id', default='33', help='Hearing ID for comparison')
    parser.add_argument('--professional-transcript', required=True, help='Path to professional transcript JSON')
    parser.add_argument('--whisper-transcript', required=True, help='Path to Whisper transcript JSON')
    parser.add_argument('--output-dir', required=True, help='Output directory for comparison results')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize comparator
    comparator = TranscriptComparator(args.hearing_id)
    
    # Execute comparison
    result = comparator.compare_transcripts(
        Path(args.professional_transcript),
        Path(args.whisper_transcript),
        Path(args.output_dir)
    )
    
    if result:
        print("✅ Benchmark comparison completed successfully!")
        print(f"   Quality Rating: {result['overall_assessment']['quality_rating']}")
        print(f"   Word Accuracy: {result['content_analysis']['word_accuracy_metrics']['word_accuracy']:.3f}")
        print(f"   Report saved to: {args.output_dir}")
    else:
        print("❌ Comparison failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
