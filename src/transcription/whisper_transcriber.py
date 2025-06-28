"""
Whisper-based transcription for congressional hearing audio.

Provides automated transcription using OpenAI Whisper with support for
various audio formats and quality settings optimized for congressional proceedings.
"""

import whisper
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import json

# Note: Hearing import handled dynamically to avoid circular imports


class WhisperTranscriber:
    """
    Congressional hearing transcriber using OpenAI Whisper.
    
    Optimized for political speech, committee proceedings, and formal testimony
    with support for speaker diarization and timestamp preservation.
    """
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper transcriber.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
                       base is recommended for balance of speed/accuracy
        """
        self.logger = logging.getLogger(__name__)
        self.model_size = model_size
        self.model = None
        
        # Model performance characteristics for congressional use
        self.model_specs = {
            "tiny": {"speed": "fastest", "accuracy": "lowest", "vram": "~39MB"},
            "base": {"speed": "fast", "accuracy": "good", "vram": "~74MB"},
            "small": {"speed": "medium", "accuracy": "better", "vram": "~244MB"},
            "medium": {"speed": "slow", "accuracy": "high", "vram": "~769MB"},
            "large": {"speed": "slowest", "accuracy": "highest", "vram": "~1550MB"}
        }
        
        self.logger.info(f"Whisper transcriber initialized with {model_size} model")
        self.logger.info(f"Model specs: {self.model_specs.get(model_size, 'unknown')}")
    
    def load_model(self) -> None:
        """Load the Whisper model into memory."""
        if self.model is None:
            self.logger.info(f"Loading Whisper {self.model_size} model...")
            start_time = time.time()
            
            try:
                self.model = whisper.load_model(self.model_size)
                load_time = time.time() - start_time
                self.logger.info(f"Model loaded successfully in {load_time:.1f}s")
                
            except Exception as e:
                self.logger.error(f"Failed to load Whisper model: {e}")
                raise
    
    def transcribe_audio(
        self, 
        audio_path: Union[str, Path], 
        language: str = "en",
        initial_prompt: Optional[str] = None,
        hearing_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text with congressional context.
        
        Args:
            audio_path: Path to audio file
            language: Language code (default: "en" for English)
            initial_prompt: Optional prompt to guide transcription
            hearing_id: Optional hearing ID for context
            
        Returns:
            Dictionary with transcription results and metadata
        """
        # Ensure model is loaded
        self.load_model()
        
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Congressional hearing context prompt
        if initial_prompt is None:
            initial_prompt = (
                "This is a U.S. Congressional committee hearing with senators, "
                "representatives, witnesses, and formal testimony. Speakers include "
                "Chair, Ranking Member, committee members, and expert witnesses."
            )
        
        self.logger.info(f"Transcribing audio: {audio_path}")
        self.logger.info(f"File size: {audio_path.stat().st_size / (1024*1024):.1f} MB")
        
        start_time = time.time()
        
        try:
            # Whisper transcription with congressional optimizations
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                initial_prompt=initial_prompt,
                verbose=False,
                word_timestamps=True,  # Enable word-level timestamps
                condition_on_previous_text=True  # Better coherence for long hearings
            )
            
            transcription_time = time.time() - start_time
            audio_duration = result.get('duration', 0)
            speed_ratio = audio_duration / transcription_time if transcription_time > 0 else 0
            
            self.logger.info(f"Transcription completed in {transcription_time:.1f}s")
            self.logger.info(f"Audio duration: {audio_duration:.1f}s")
            self.logger.info(f"Speed ratio: {speed_ratio:.1f}x realtime")
            
            # Format results for congressional use
            formatted_result = {
                'hearing_id': hearing_id,
                'audio_file': str(audio_path),
                'transcription': {
                    'text': result['text'],
                    'segments': self._format_segments(result.get('segments', [])),
                    'language': result.get('language'),
                    'duration': audio_duration
                },
                'processing_metadata': {
                    'model_size': self.model_size,
                    'transcription_time': transcription_time,
                    'speed_ratio': speed_ratio,
                    'initial_prompt': initial_prompt,
                    'word_timestamps': True,
                    'whisper_version': whisper.__version__
                },
                'quality_metrics': self._calculate_quality_metrics(result)
            }
            
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise
    
    def _format_segments(self, segments: List[Dict]) -> List[Dict[str, Any]]:
        """
        Format Whisper segments for congressional hearing analysis.
        
        Args:
            segments: Raw Whisper segments
            
        Returns:
            Formatted segments with enhanced metadata
        """
        formatted_segments = []
        
        for i, segment in enumerate(segments):
            formatted_segment = {
                'id': i,
                'start': segment.get('start', 0),
                'end': segment.get('end', 0),
                'duration': segment.get('end', 0) - segment.get('start', 0),
                'text': segment.get('text', '').strip(),
                'tokens': segment.get('tokens', []),
                'avg_logprob': segment.get('avg_logprob'),
                'no_speech_prob': segment.get('no_speech_prob'),
                'words': segment.get('words', [])
            }
            
            # Add quality indicators for congressional analysis
            formatted_segment['confidence'] = self._calculate_segment_confidence(segment)
            formatted_segment['likely_speaker_change'] = self._detect_speaker_change(segment)
            
            formatted_segments.append(formatted_segment)
        
        return formatted_segments
    
    def _calculate_segment_confidence(self, segment: Dict) -> str:
        """Calculate confidence level for a segment."""
        avg_logprob = segment.get('avg_logprob', -1)
        no_speech_prob = segment.get('no_speech_prob', 1)
        
        if avg_logprob > -0.5 and no_speech_prob < 0.1:
            return "high"
        elif avg_logprob > -1.0 and no_speech_prob < 0.3:
            return "medium"
        else:
            return "low"
    
    def _detect_speaker_change(self, segment: Dict) -> bool:
        """
        Detect potential speaker changes within a segment.
        
        This is a heuristic for congressional hearings where speaker
        changes often correlate with longer pauses or text patterns.
        """
        text = segment.get('text', '')
        
        # Look for formal congressional patterns that indicate speaker changes
        speaker_indicators = [
            'Thank you',
            'Chair',
            'Ranking Member',
            'Senator',
            'Representative', 
            'Mr.',
            'Ms.',
            'Dr.'
        ]
        
        # Check if segment starts with formal address
        for indicator in speaker_indicators:
            if text.strip().startswith(indicator):
                return True
        
        return False
    
    def _calculate_quality_metrics(self, result: Dict) -> Dict[str, Any]:
        """Calculate transcription quality metrics."""
        segments = result.get('segments', [])
        
        if not segments:
            return {'overall_confidence': 'unknown', 'metrics': {}}
        
        # Aggregate confidence metrics
        total_logprob = sum(s.get('avg_logprob', -1) for s in segments)
        avg_logprob = total_logprob / len(segments)
        
        total_no_speech = sum(s.get('no_speech_prob', 1) for s in segments)
        avg_no_speech = total_no_speech / len(segments)
        
        # Determine overall confidence
        if avg_logprob > -0.5 and avg_no_speech < 0.1:
            confidence = "high"
        elif avg_logprob > -1.0 and avg_no_speech < 0.3:
            confidence = "medium"
        else:
            confidence = "low"
        
        return {
            'overall_confidence': confidence,
            'metrics': {
                'avg_logprob': avg_logprob,
                'avg_no_speech_prob': avg_no_speech,
                'total_segments': len(segments),
                'high_confidence_segments': len([s for s in segments if self._calculate_segment_confidence(s) == "high"]),
                'potential_speaker_changes': len([s for s in segments if self._detect_speaker_change(s)])
            }
        }
    
    def transcribe_with_enrichment(
        self, 
        audio_path: Union[str, Path], 
        hearing_id: Optional[str] = None,
        output_dir: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Complete transcription and enrichment pipeline.
        
        Args:
            audio_path: Path to audio file
            hearing_id: Optional hearing ID for metadata
            output_dir: Optional directory to save results
            
        Returns:
            Complete transcription and enrichment results
        """
        # Step 1: Transcribe audio
        self.logger.info("🎯 Starting complete transcription pipeline...")
        transcription_result = self.transcribe_audio(audio_path, hearing_id=hearing_id)
        
        # Step 2: Import enrichment here to avoid circular imports
        from enrichment.transcript_enricher import TranscriptEnricher
        
        enricher = TranscriptEnricher()
        
        # Step 3: Enrich with congressional metadata
        self.logger.info("🏛️  Enriching with congressional metadata...")
        enriched_result = enricher.enrich_transcript(
            transcription_result['transcription']['text'], 
            hearing_id
        )
        
        # Step 4: Combine results
        complete_result = {
            'pipeline_version': '5.0',
            'hearing_id': hearing_id,
            'audio_file': str(audio_path),
            'transcription': transcription_result,
            'enrichment': enriched_result,
            'summary': {
                'audio_duration': transcription_result['transcription']['duration'],
                'transcription_confidence': transcription_result['quality_metrics']['overall_confidence'],
                'identified_speakers': enriched_result['identified_speakers'],
                'total_segments': enriched_result['total_segments'],
                'pipeline_complete': True
            }
        }
        
        # Step 5: Save results if output directory specified
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate output filename
            audio_path_obj = Path(audio_path)
            output_file = output_dir / f"{audio_path_obj.stem}_complete_transcript.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(complete_result, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 Complete results saved: {output_file}")
            complete_result['output_file'] = str(output_file)
        
        # Step 6: Generate summary
        self.logger.info("📊 TRANSCRIPTION PIPELINE COMPLETE")
        self.logger.info(f"   Audio Duration: {complete_result['summary']['audio_duration']:.1f}s")
        self.logger.info(f"   Confidence: {complete_result['summary']['transcription_confidence']}")
        self.logger.info(f"   Speakers Identified: {complete_result['summary']['identified_speakers']}")
        self.logger.info(f"   Total Segments: {complete_result['summary']['total_segments']}")
        
        return complete_result
    
    def batch_transcribe(
        self, 
        audio_files: List[Union[str, Path]], 
        output_dir: Union[str, Path],
        hearing_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch transcription for multiple hearing audio files.
        
        Args:
            audio_files: List of audio file paths
            output_dir: Directory to save all results
            hearing_ids: Optional list of hearing IDs (same order as audio_files)
            
        Returns:
            List of transcription results
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        for i, audio_file in enumerate(audio_files):
            hearing_id = hearing_ids[i] if hearing_ids and i < len(hearing_ids) else None
            
            self.logger.info(f"🔄 Processing file {i+1}/{len(audio_files)}: {audio_file}")
            
            try:
                result = self.transcribe_with_enrichment(
                    audio_file, 
                    hearing_id=hearing_id,
                    output_dir=output_dir
                )
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to process {audio_file}: {e}")
                results.append({
                    'audio_file': str(audio_file),
                    'error': str(e),
                    'success': False
                })
        
        # Create batch summary
        batch_summary = {
            'total_files': len(audio_files),
            'successful': len([r for r in results if r.get('summary', {}).get('pipeline_complete', False)]),
            'failed': len([r for r in results if 'error' in r]),
            'results': results
        }
        
        summary_file = output_dir / "batch_transcription_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(batch_summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📋 Batch summary saved: {summary_file}")
        self.logger.info(f"✅ Batch complete: {batch_summary['successful']}/{batch_summary['total_files']} successful")
        
        return results