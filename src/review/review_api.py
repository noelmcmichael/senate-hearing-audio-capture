#!/usr/bin/env python3
"""
Review API for Human-in-the-Loop Speaker Correction

FastAPI backend to support transcript review interface:
- Load transcripts for review
- Save speaker corrections
- Track review progress
- Export correction data
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .correction_store import CorrectionStore
from .review_utils import ReviewUtils


logger = logging.getLogger(__name__)


class SpeakerAssignment(BaseModel):
    """Speaker assignment for a transcript segment."""
    segment_id: int
    speaker_name: str
    confidence: float = 1.0
    reviewer_id: str
    timestamp: datetime


class BulkAssignment(BaseModel):
    """Bulk speaker assignment for multiple segments."""
    segment_ids: List[int]
    speaker_name: str
    confidence: float = 1.0
    reviewer_id: str


class ReviewSession(BaseModel):
    """Review session data."""
    session_id: str
    transcript_file: str
    reviewer_id: str
    start_time: datetime
    last_saved: Optional[datetime] = None
    progress: Dict[str, Any] = {}


class ReviewAPI:
    """FastAPI application for transcript review operations."""
    
    def __init__(self, data_dir: Path = None):
        """Initialize review API."""
        self.app = FastAPI(title="Senate Hearing Review API", version="6.0")
        self.data_dir = data_dir or Path("output")
        self.correction_store = CorrectionStore()
        self.review_utils = ReviewUtils()
        
        # Setup CORS for React frontend
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],  # React dev server
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def root():
            """Health check endpoint."""
            return {"status": "ok", "service": "review-api", "version": "6.0"}
        
        @self.app.get("/transcripts")
        async def list_transcripts():
            """List available transcripts for review."""
            try:
                transcripts = []
                for file_path in self.data_dir.glob("**/*transcript*.json"):
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        # Extract metadata
                        transcript_info = {
                            "file_path": str(file_path),
                            "filename": file_path.name,
                            "hearing_id": data.get("hearing_id", "unknown"),
                            "audio_file": data.get("audio_file", "unknown"),
                            "pipeline_version": data.get("pipeline_version", "unknown"),
                            "created": file_path.stat().st_mtime,
                            "segments_count": len(data.get("transcription", {}).get("segments", [])),
                            "has_corrections": self.correction_store.has_corrections(str(file_path))
                        }
                        transcripts.append(transcript_info)
                    except Exception as e:
                        logger.warning(f"Could not process {file_path}: {e}")
                        continue
                
                return {"transcripts": sorted(transcripts, key=lambda x: x["created"], reverse=True)}
            
            except Exception as e:
                logger.error(f"Error listing transcripts: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/transcripts/{transcript_id}")
        async def get_transcript(transcript_id: str):
            """Get transcript data for review."""
            try:
                # Find transcript file
                transcript_file = self._find_transcript_file(transcript_id)
                if not transcript_file:
                    raise HTTPException(status_code=404, detail="Transcript not found")
                
                # Load transcript data
                with open(transcript_file, 'r') as f:
                    transcript_data = json.load(f)
                
                # Add existing corrections
                corrections = self.correction_store.get_corrections(str(transcript_file))
                
                # Enhance transcript with review metadata
                enhanced_transcript = self.review_utils.prepare_for_review(
                    transcript_data, corrections
                )
                
                return {
                    "transcript": enhanced_transcript,
                    "file_path": str(transcript_file),
                    "corrections_count": len(corrections),
                    "review_ready": True
                }
                
            except Exception as e:
                logger.error(f"Error loading transcript {transcript_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/transcripts/{transcript_id}/corrections")
        async def save_speaker_assignment(transcript_id: str, assignment: SpeakerAssignment):
            """Save a speaker assignment correction."""
            try:
                transcript_file = self._find_transcript_file(transcript_id)
                if not transcript_file:
                    raise HTTPException(status_code=404, detail="Transcript not found")
                
                # Save correction
                correction_id = self.correction_store.save_correction(
                    transcript_file=str(transcript_file),
                    segment_id=assignment.segment_id,
                    speaker_name=assignment.speaker_name,
                    confidence=assignment.confidence,
                    reviewer_id=assignment.reviewer_id
                )
                
                return {
                    "correction_id": correction_id,
                    "status": "saved",
                    "segment_id": assignment.segment_id,
                    "speaker": assignment.speaker_name
                }
                
            except Exception as e:
                logger.error(f"Error saving speaker assignment: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/transcripts/{transcript_id}/bulk-corrections")
        async def save_bulk_assignment(transcript_id: str, assignment: BulkAssignment):
            """Save bulk speaker assignments."""
            try:
                transcript_file = self._find_transcript_file(transcript_id)
                if not transcript_file:
                    raise HTTPException(status_code=404, detail="Transcript not found")
                
                correction_ids = []
                for segment_id in assignment.segment_ids:
                    correction_id = self.correction_store.save_correction(
                        transcript_file=str(transcript_file),
                        segment_id=segment_id,
                        speaker_name=assignment.speaker_name,
                        confidence=assignment.confidence,
                        reviewer_id=assignment.reviewer_id
                    )
                    correction_ids.append(correction_id)
                
                return {
                    "correction_ids": correction_ids,
                    "status": "saved",
                    "segments_updated": len(assignment.segment_ids),
                    "speaker": assignment.speaker_name
                }
                
            except Exception as e:
                logger.error(f"Error saving bulk assignments: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/transcripts/{transcript_id}/corrections")
        async def get_corrections(transcript_id: str):
            """Get all corrections for a transcript."""
            try:
                transcript_file = self._find_transcript_file(transcript_id)
                if not transcript_file:
                    raise HTTPException(status_code=404, detail="Transcript not found")
                
                corrections = self.correction_store.get_corrections(str(transcript_file))
                
                return {
                    "transcript_id": transcript_id,
                    "corrections": corrections,
                    "count": len(corrections)
                }
                
            except Exception as e:
                logger.error(f"Error getting corrections: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/transcripts/{transcript_id}/export")
        async def export_corrected_transcript(transcript_id: str):
            """Export transcript with all corrections applied."""
            try:
                transcript_file = self._find_transcript_file(transcript_id)
                if not transcript_file:
                    raise HTTPException(status_code=404, detail="Transcript not found")
                
                # Load original transcript
                with open(transcript_file, 'r') as f:
                    transcript_data = json.load(f)
                
                # Apply all corrections
                corrections = self.correction_store.get_corrections(str(transcript_file))
                corrected_transcript = self.review_utils.apply_corrections(
                    transcript_data, corrections
                )
                
                # Save corrected version
                export_path = transcript_file.parent / f"{transcript_file.stem}_corrected.json"
                with open(export_path, 'w') as f:
                    json.dump(corrected_transcript, f, indent=2, default=str)
                
                return {
                    "export_path": str(export_path),
                    "corrections_applied": len(corrections),
                    "status": "exported"
                }
                
            except Exception as e:
                logger.error(f"Error exporting transcript: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def _find_transcript_file(self, transcript_id: str) -> Optional[Path]:
        """Find transcript file by ID or filename."""
        # Try direct filename match
        for file_path in self.data_dir.glob("**/*transcript*.json"):
            if transcript_id in file_path.name:
                return file_path
        
        return None


def create_app(data_dir: Path = None) -> FastAPI:
    """Create and configure the review API application."""
    review_api = ReviewAPI(data_dir)
    return review_api.app


if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)