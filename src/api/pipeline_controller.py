"""
Pipeline Controller for Selective Processing
Orchestrates the full processing pipeline: capture → convert → trim → transcribe → speaker labels
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from pathlib import Path
import json
import uuid
from dataclasses import dataclass
from enum import Enum

from .discovery_service import get_discovery_service
from .capture_service import get_capture_service, CaptureException
from .transcription_service import get_transcription_service, TranscriptionException
from ..audio.trimming import get_audio_trimmer
from ..speaker.enhanced_labeling import get_enhanced_speaker_labeler

logger = logging.getLogger(__name__)

class ProcessingStage(Enum):
    """Processing pipeline stages"""
    CAPTURE_REQUESTED = "capture_requested"
    CAPTURING = "capturing"
    CONVERTING = "converting"
    TRIMMING = "trimming"
    TRANSCRIBING = "transcribing"
    SPEAKER_LABELING = "speaker_labeling"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProcessingProgress:
    """Processing progress tracking"""
    hearing_id: str
    stage: ProcessingStage
    progress_percent: float
    message: str
    started_at: str
    stage_started_at: str
    estimated_completion: Optional[str] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class PipelineController:
    """Controller for orchestrating the complete processing pipeline"""
    
    def __init__(self):
        self.discovery_service = get_discovery_service()
        self.capture_service = get_capture_service()
        self.transcription_service = get_transcription_service()
        self.audio_trimmer = get_audio_trimmer()
        self.speaker_labeler = get_enhanced_speaker_labeler()
        self.active_processes: Dict[str, ProcessingProgress] = {}
        self.progress_callbacks: Dict[str, Callable] = {}
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    async def start_processing(self, hearing_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start processing pipeline for a hearing
        
        Args:
            hearing_id: Hearing ID to process
            options: Optional processing options
            
        Returns:
            Processing start confirmation
        """
        try:
            # Check if hearing exists
            hearings = self.discovery_service.get_discovered_hearings()
            hearing = next((h for h in hearings if h.id == hearing_id), None)
            
            if not hearing:
                raise ValueError(f"Hearing {hearing_id} not found")
            
            if hearing.status != "discovered":
                raise ValueError(f"Hearing {hearing_id} is not in 'discovered' status (current: {hearing.status})")
            
            # Check if already processing
            if hearing_id in self.active_processes:
                raise ValueError(f"Hearing {hearing_id} is already being processed")
            
            # Update hearing status
            self.discovery_service.update_hearing_status(hearing_id, "capture_requested")
            
            # Initialize progress tracking
            progress = ProcessingProgress(
                hearing_id=hearing_id,
                stage=ProcessingStage.CAPTURE_REQUESTED,
                progress_percent=0.0,
                message="Processing request received",
                started_at=datetime.now().isoformat(),
                stage_started_at=datetime.now().isoformat()
            )
            
            self.active_processes[hearing_id] = progress
            
            # Start processing in background
            asyncio.create_task(self._run_pipeline(hearing_id, hearing, options or {}))
            
            return {
                "hearing_id": hearing_id,
                "status": "processing_started",
                "message": "Processing pipeline started successfully",
                "progress": progress.__dict__
            }
            
        except Exception as e:
            logger.error(f"Error starting processing for {hearing_id}: {e}")
            # Update hearing status to failed
            self.discovery_service.update_hearing_status(hearing_id, "failed", str(e))
            raise
    
    async def _run_pipeline(self, hearing_id: str, hearing: Any, options: Dict[str, Any]):
        """Run the complete processing pipeline"""
        try:
            logger.info(f"Starting processing pipeline for hearing {hearing_id}")
            
            # Stage 1: Capture Audio
            await self._update_progress(hearing_id, ProcessingStage.CAPTURING, 10, "Capturing audio from source")
            audio_path = await self._capture_audio(hearing_id, hearing, options)
            
            # Stage 2: Convert Audio
            await self._update_progress(hearing_id, ProcessingStage.CONVERTING, 30, "Converting audio to MP3")
            converted_path = await self._convert_audio(hearing_id, audio_path, options)
            
            # Stage 3: Trim Audio
            await self._update_progress(hearing_id, ProcessingStage.TRIMMING, 50, "Trimming silence from audio")
            trimmed_path = await self._trim_audio(hearing_id, converted_path, options)
            
            # Stage 4: Transcribe Audio
            await self._update_progress(hearing_id, ProcessingStage.TRANSCRIBING, 70, "Transcribing audio to text")
            transcript_path = await self._transcribe_audio(hearing_id, trimmed_path, options)
            
            # Stage 5: Speaker Labeling
            await self._update_progress(hearing_id, ProcessingStage.SPEAKER_LABELING, 90, "Adding speaker labels")
            final_transcript = await self._add_speaker_labels(hearing_id, transcript_path, options)
            
            # Stage 6: Complete
            await self._update_progress(hearing_id, ProcessingStage.COMPLETED, 100, "Processing completed successfully")
            
            # Update hearing status
            self.discovery_service.update_hearing_status(hearing_id, "completed")
            
            # Store final results
            await self._store_results(hearing_id, {
                "audio_path": str(trimmed_path),
                "transcript_path": str(final_transcript),
                "completed_at": datetime.now().isoformat()
            })
            
            logger.info(f"Processing pipeline completed for hearing {hearing_id}")
            
        except Exception as e:
            logger.error(f"Pipeline failed for hearing {hearing_id}: {e}")
            await self._update_progress(hearing_id, ProcessingStage.FAILED, 0, f"Processing failed: {str(e)}")
            self.discovery_service.update_hearing_status(hearing_id, "failed", str(e))
        finally:
            # Clean up active process
            if hearing_id in self.active_processes:
                del self.active_processes[hearing_id]
    
    async def _capture_audio(self, hearing_id: str, hearing: Any, options: Dict[str, Any]) -> Path:
        """Capture audio from hearing source"""
        try:
            if not hearing.url:
                raise ValueError("No URL available for audio capture")
            
            # Create hearing-specific output directory
            output_dir = self.output_dir / "audio" / hearing_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Use capture service
            result = await self.capture_service.capture_audio(
                url=hearing.url,
                output_dir=str(output_dir),
                format="wav",  # Start with WAV for processing
                options=options.get("capture", {})
            )
            
            if not result.get("success"):
                raise CaptureException(f"Audio capture failed: {result.get('error', 'Unknown error')}")
            
            audio_path = Path(result["file_path"])
            if not audio_path.exists():
                raise CaptureException(f"Captured audio file not found: {audio_path}")
            
            logger.info(f"Audio captured successfully for {hearing_id}: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Audio capture failed for {hearing_id}: {e}")
            raise CaptureException(f"Audio capture failed: {e}")
    
    async def _convert_audio(self, hearing_id: str, audio_path: Path, options: Dict[str, Any]) -> Path:
        """Convert audio to MP3"""
        try:
            # Output path for converted audio
            output_path = audio_path.parent / f"{audio_path.stem}_converted.mp3"
            
            # For now, simulate conversion (would use FFmpeg in production)
            await asyncio.sleep(1)  # Simulate processing time
            
            # In production, this would use FFmpeg:
            # ffmpeg -i input.wav -codec:a mp3 -b:a 128k output.mp3
            
            # For demo, copy the file
            import shutil
            shutil.copy(audio_path, output_path)
            
            logger.info(f"Audio converted successfully for {hearing_id}: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Audio conversion failed for {hearing_id}: {e}")
            raise
    
    async def _trim_audio(self, hearing_id: str, audio_path: Path, options: Dict[str, Any]) -> Path:
        """Trim silence from beginning of audio using AudioTrimmer"""
        try:
            logger.info(f"Starting audio trimming for {hearing_id}")
            
            # Output path for trimmed audio
            output_path = audio_path.parent / f"{audio_path.stem}_trimmed.mp3"
            
            # Get trimming parameters from options
            trim_params = options.get("trimming", {})
            
            # Use smart trimming with silence detection
            trim_result = self.audio_trimmer.smart_trim(
                audio_path=audio_path,
                output_path=output_path,
                params=trim_params
            )
            
            # Log trimming results
            trimming_info = trim_result["trimming"]
            optimization_info = trim_result["optimization"]
            
            logger.info(f"Audio trimmed successfully for {hearing_id}:")
            logger.info(f"  - Original duration: {trimming_info['original_duration']:.1f}s")
            logger.info(f"  - New duration: {trimming_info['new_duration']:.1f}s")
            logger.info(f"  - Trimmed: {trimming_info['trimmed_seconds']:.1f}s")
            logger.info(f"  - Quality improvement: {optimization_info['content_improvement']:.1f}%")
            logger.info(f"  - File size reduction: {optimization_info['file_size_reduction']:.1f}%")
            
            # Store trimming metadata for later use
            metadata_path = output_path.parent / f"{output_path.stem}_trim_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(trim_result, f, indent=2)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Audio trimming failed for {hearing_id}: {e}")
            raise
    
    async def _transcribe_audio(self, hearing_id: str, audio_path: Path, options: Dict[str, Any]) -> Path:
        """Transcribe audio to text"""
        try:
            # Output path for transcript
            output_path = audio_path.parent / f"{audio_path.stem}_transcript.json"
            
            # Use transcription service
            result = await self.transcription_service.transcribe_audio(
                audio_path=str(audio_path),
                options=options.get("transcription", {})
            )
            
            if not result.get("success"):
                raise TranscriptionException(f"Transcription failed: {result.get('error', 'Unknown error')}")
            
            # Save transcript
            with open(output_path, 'w') as f:
                json.dump(result["transcript"], f, indent=2)
            
            logger.info(f"Audio transcribed successfully for {hearing_id}: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Audio transcription failed for {hearing_id}: {e}")
            raise TranscriptionException(f"Audio transcription failed: {e}")
    
    async def _add_speaker_labels(self, hearing_id: str, transcript_path: Path, options: Dict[str, Any]) -> Path:
        """Add speaker labels to transcript using enhanced congressional metadata"""
        try:
            logger.info(f"Starting speaker labeling for {hearing_id}")
            
            # Output path for labeled transcript
            output_path = transcript_path.parent / f"{transcript_path.stem}_labeled.json"
            
            # Load transcript
            with open(transcript_path, 'r') as f:
                transcript = json.load(f)
            
            # Get hearing information for committee context
            hearings = self.discovery_service.get_discovered_hearings()
            hearing = next((h for h in hearings if h.id == hearing_id), None)
            
            committee_code = hearing.committee_code if hearing else "UNKNOWN"
            logger.info(f"Using committee code for speaker labeling: {committee_code}")
            
            # Get segments from transcript
            segments = transcript.get("segments", [])
            if not segments:
                logger.warning(f"No segments found in transcript for {hearing_id}")
                # Still save the transcript even if no segments
                with open(output_path, 'w') as f:
                    json.dump(transcript, f, indent=2)
                return output_path
            
            # Enhance segments with speaker identification
            enhanced_segments = self.speaker_labeler.enhance_transcript_segments(
                segments, committee_code, hearing_id
            )
            
            # Update transcript with enhanced segments
            transcript["segments"] = enhanced_segments
            
            # Add metadata about speaker labeling
            transcript["speaker_labeling"] = {
                "enhanced": True,
                "committee_code": committee_code,
                "labeling_timestamp": datetime.now().isoformat(),
                "total_segments": len(enhanced_segments),
                "enhanced_segments": len([s for s in enhanced_segments if s.get("enhanced_speaker", {}).get("confidence", 0) > 0.5])
            }
            
            # Save labeled transcript
            with open(output_path, 'w') as f:
                json.dump(transcript, f, indent=2)
            
            # Log speaker labeling results
            speaker_stats = self._analyze_speaker_labeling_results(enhanced_segments)
            logger.info(f"Speaker labeling completed for {hearing_id}:")
            logger.info(f"  - Total segments: {len(enhanced_segments)}")
            logger.info(f"  - High confidence: {speaker_stats['high_confidence']}")
            logger.info(f"  - Roles identified: {', '.join(speaker_stats['roles_found'])}")
            logger.info(f"  - Metadata matches: {speaker_stats['metadata_matches']}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Speaker labeling failed for {hearing_id}: {e}")
            raise
    
    def _analyze_speaker_labeling_results(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze speaker labeling results for logging"""
        try:
            high_confidence = 0
            roles_found = set()
            metadata_matches = 0
            
            for segment in segments:
                enhanced_speaker = segment.get("enhanced_speaker", {})
                confidence = enhanced_speaker.get("confidence", 0)
                role = enhanced_speaker.get("role", "UNKNOWN")
                source = enhanced_speaker.get("source", "unknown")
                
                if confidence > 0.7:
                    high_confidence += 1
                
                if role != "UNKNOWN":
                    roles_found.add(role)
                
                if source == "metadata":
                    metadata_matches += 1
            
            return {
                "high_confidence": high_confidence,
                "roles_found": list(roles_found),
                "metadata_matches": metadata_matches
            }
            
        except Exception as e:
            logger.error(f"Error analyzing speaker labeling results: {e}")
            return {
                "high_confidence": 0,
                "roles_found": [],
                "metadata_matches": 0
            }
    
    async def _store_results(self, hearing_id: str, results: Dict[str, Any]):
        """Store final processing results"""
        try:
            # Store in database or file system
            results_path = self.output_dir / "results" / f"{hearing_id}_results.json"
            results_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Results stored for {hearing_id}: {results_path}")
            
        except Exception as e:
            logger.error(f"Error storing results for {hearing_id}: {e}")
    
    async def _update_progress(self, hearing_id: str, stage: ProcessingStage, progress_percent: float, message: str):
        """Update processing progress"""
        try:
            if hearing_id in self.active_processes:
                progress = self.active_processes[hearing_id]
                progress.stage = stage
                progress.progress_percent = progress_percent
                progress.message = message
                progress.stage_started_at = datetime.now().isoformat()
                
                # Update database
                self.discovery_service.update_hearing_status(hearing_id, stage.value)
                
                # Trigger callbacks
                if hearing_id in self.progress_callbacks:
                    await self.progress_callbacks[hearing_id](progress)
                
                logger.info(f"Progress updated for {hearing_id}: {stage.value} - {progress_percent}% - {message}")
                
        except Exception as e:
            logger.error(f"Error updating progress for {hearing_id}: {e}")
    
    def get_processing_progress(self, hearing_id: str) -> Optional[ProcessingProgress]:
        """Get current processing progress"""
        return self.active_processes.get(hearing_id)
    
    def get_active_processes(self) -> Dict[str, ProcessingProgress]:
        """Get all active processes"""
        return dict(self.active_processes)
    
    def register_progress_callback(self, hearing_id: str, callback: Callable):
        """Register progress callback for real-time updates"""
        self.progress_callbacks[hearing_id] = callback
    
    def unregister_progress_callback(self, hearing_id: str):
        """Unregister progress callback"""
        if hearing_id in self.progress_callbacks:
            del self.progress_callbacks[hearing_id]
    
    async def cancel_processing(self, hearing_id: str) -> bool:
        """Cancel active processing"""
        try:
            if hearing_id in self.active_processes:
                # Update status
                await self._update_progress(hearing_id, ProcessingStage.FAILED, 0, "Processing cancelled by user")
                self.discovery_service.update_hearing_status(hearing_id, "discovered")  # Reset to discovered
                
                # Clean up
                del self.active_processes[hearing_id]
                
                logger.info(f"Processing cancelled for {hearing_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling processing for {hearing_id}: {e}")
            return False

# Global controller instance
_pipeline_controller = None

def get_pipeline_controller() -> PipelineController:
    """Get pipeline controller singleton"""
    global _pipeline_controller
    if _pipeline_controller is None:
        _pipeline_controller = PipelineController()
    return _pipeline_controller