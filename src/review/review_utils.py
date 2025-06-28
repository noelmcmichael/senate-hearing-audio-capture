#!/usr/bin/env python3
"""
Review Utilities for Human-in-the-Loop Speaker Correction

Utilities to prepare transcripts for review and apply corrections:
- Enhance transcripts with review metadata
- Apply corrections to generate final output
- Calculate review progress and quality metrics
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class ReviewUtils:
    """Utilities for transcript review operations."""
    
    def __init__(self):
        """Initialize review utilities."""
        pass
    
    def prepare_for_review(
        self, 
        transcript_data: Dict[str, Any], 
        existing_corrections: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare transcript data for human review interface."""
        try:
            # Create correction lookup
            corrections_by_segment = {}
            if existing_corrections:
                for correction in existing_corrections:
                    segment_id = correction["segment_id"]
                    corrections_by_segment[segment_id] = correction
            
            # Enhance segments with review metadata
            enhanced_segments = []
            segments = transcript_data.get("transcription", {}).get("segments", [])
            
            for i, segment in enumerate(segments):
                enhanced_segment = segment.copy()
                segment_id = segment.get("id", i)
                
                # Add review metadata
                enhanced_segment.update({
                    "review_metadata": {
                        "segment_index": i,
                        "needs_review": self._segment_needs_review(segment),
                        "has_correction": segment_id in corrections_by_segment,
                        "correction": corrections_by_segment.get(segment_id),
                        "speaker_options": self._get_speaker_options(transcript_data),
                        "confidence_level": self._assess_confidence(segment),
                        "duration_seconds": segment.get("end", 0) - segment.get("start", 0)
                    }
                })
                
                enhanced_segments.append(enhanced_segment)
            
            # Calculate overall review statistics
            review_stats = self._calculate_review_stats(enhanced_segments, existing_corrections)
            
            # Create enhanced transcript
            enhanced_transcript = transcript_data.copy()
            enhanced_transcript["transcription"]["segments"] = enhanced_segments
            enhanced_transcript["review_metadata"] = {
                "total_segments": len(enhanced_segments),
                "needs_review_count": review_stats["needs_review"],
                "corrected_count": review_stats["corrected"],
                "completion_percentage": review_stats["completion_percentage"],
                "estimated_review_time": review_stats["estimated_time"],
                "speaker_summary": review_stats["speaker_summary"]
            }
            
            return enhanced_transcript
            
        except Exception as e:
            logger.error(f"Error preparing transcript for review: {e}")
            raise
    
    def apply_corrections(
        self, 
        transcript_data: Dict[str, Any], 
        corrections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply all corrections to transcript data."""
        try:
            # Create correction lookup
            corrections_by_segment = {}
            for correction in corrections:
                segment_id = correction["segment_id"]
                corrections_by_segment[segment_id] = correction
            
            # Apply corrections to segments
            corrected_transcript = transcript_data.copy()
            segments = corrected_transcript.get("transcription", {}).get("segments", [])
            
            corrections_applied = 0
            for segment in segments:
                segment_id = segment.get("id")
                if segment_id in corrections_by_segment:
                    correction = corrections_by_segment[segment_id]
                    
                    # Apply speaker correction
                    segment["speaker"] = correction["speaker_name"]
                    segment["speaker_confidence"] = correction["confidence"]
                    segment["corrected"] = True
                    segment["correction_metadata"] = {
                        "correction_id": correction["id"],
                        "reviewer_id": correction["reviewer_id"],
                        "corrected_at": correction["created_at"],
                        "original_speaker": segment.get("original_speaker", "unknown")
                    }
                    
                    corrections_applied += 1
            
            # Update transcript metadata
            if "enrichment" not in corrected_transcript:
                corrected_transcript["enrichment"] = {}
            
            corrected_transcript["enrichment"]["corrections_applied"] = {
                "count": corrections_applied,
                "total_segments": len(segments),
                "correction_percentage": (corrections_applied / len(segments)) * 100 if segments else 0,
                "corrected_speakers": list(set(c["speaker_name"] for c in corrections))
            }
            
            return corrected_transcript
            
        except Exception as e:
            logger.error(f"Error applying corrections: {e}")
            raise
    
    def _segment_needs_review(self, segment: Dict[str, Any]) -> bool:
        """Determine if a segment needs human review."""
        # Segment needs review if:
        # 1. No speaker identified
        # 2. Low confidence score
        # 3. Likely speaker change detected
        # 4. Short duration (might be noise)
        
        has_speaker = segment.get("speaker") and segment.get("speaker") != "unknown"
        confidence = segment.get("confidence", "unknown")
        is_low_confidence = confidence == "low" or (
            isinstance(confidence, (int, float)) and confidence < 0.7
        )
        likely_speaker_change = segment.get("likely_speaker_change", False)
        
        duration = segment.get("end", 0) - segment.get("start", 0)
        is_very_short = duration < 2.0  # Less than 2 seconds
        
        needs_review = (
            not has_speaker or 
            is_low_confidence or 
            likely_speaker_change or
            is_very_short
        )
        
        return needs_review
    
    def _get_speaker_options(self, transcript_data: Dict[str, Any]) -> List[str]:
        """Get list of possible speakers for this hearing."""
        speakers = set(["Unknown Speaker"])
        
        # From enrichment data
        enrichment = transcript_data.get("enrichment", {})
        if "committee_members" in enrichment:
            for member in enrichment["committee_members"]:
                speakers.add(member.get("display_name", member.get("name", "")))
        
        # From existing speaker analysis
        speaker_analysis = enrichment.get("speaker_analysis", {})
        if "identified_speakers" in speaker_analysis:
            speakers.update(speaker_analysis["identified_speakers"].keys())
        
        # Common congressional titles
        speakers.update([
            "Chair/Chairman", "Ranking Member", "Committee Staff",
            "Witness", "Expert Witness", "Public Commenter"
        ])
        
        return sorted(list(speakers))
    
    def _assess_confidence(self, segment: Dict[str, Any]) -> str:
        """Assess confidence level for speaker identification."""
        confidence = segment.get("confidence", "unknown")
        
        if isinstance(confidence, str):
            return confidence
        elif isinstance(confidence, (int, float)):
            if confidence >= 0.8:
                return "high"
            elif confidence >= 0.6:
                return "medium"
            else:
                return "low"
        else:
            return "unknown"
    
    def _calculate_review_stats(
        self, 
        segments: List[Dict[str, Any]], 
        corrections: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate review progress statistics."""
        total_segments = len(segments)
        needs_review = sum(1 for s in segments if s["review_metadata"]["needs_review"])
        corrected = len(corrections) if corrections else 0
        
        completion_percentage = 0
        if needs_review > 0:
            completion_percentage = (corrected / needs_review) * 100
        
        # Estimate review time (30 seconds per segment needing review)
        remaining_review = max(0, needs_review - corrected)
        estimated_time = remaining_review * 30  # seconds
        
        # Speaker summary
        speaker_counts = {}
        for correction in (corrections or []):
            speaker = correction["speaker_name"]
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
        
        return {
            "needs_review": needs_review,
            "corrected": corrected,
            "completion_percentage": round(completion_percentage, 1),
            "estimated_time": estimated_time,
            "speaker_summary": speaker_counts
        }
    
    def export_review_summary(
        self, 
        transcript_file: str, 
        corrections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export a summary of review work completed."""
        try:
            # Calculate summary statistics
            total_corrections = len(corrections)
            unique_speakers = len(set(c["speaker_name"] for c in corrections))
            unique_reviewers = len(set(c["reviewer_id"] for c in corrections))
            
            # Speaker distribution
            speaker_distribution = {}
            for correction in corrections:
                speaker = correction["speaker_name"]
                speaker_distribution[speaker] = speaker_distribution.get(speaker, 0) + 1
            
            # Reviewer activity
            reviewer_activity = {}
            for correction in corrections:
                reviewer = correction["reviewer_id"]
                reviewer_activity[reviewer] = reviewer_activity.get(reviewer, 0) + 1
            
            # Confidence distribution
            confidence_levels = {"high": 0, "medium": 0, "low": 0}
            for correction in corrections:
                conf = correction.get("confidence", 1.0)
                if conf >= 0.8:
                    confidence_levels["high"] += 1
                elif conf >= 0.6:
                    confidence_levels["medium"] += 1
                else:
                    confidence_levels["low"] += 1
            
            review_summary = {
                "transcript_file": transcript_file,
                "review_completed": True,
                "summary_statistics": {
                    "total_corrections": total_corrections,
                    "unique_speakers": unique_speakers,
                    "unique_reviewers": unique_reviewers,
                    "avg_confidence": sum(c.get("confidence", 1.0) for c in corrections) / total_corrections if corrections else 0
                },
                "speaker_distribution": speaker_distribution,
                "reviewer_activity": reviewer_activity,
                "confidence_distribution": confidence_levels,
                "export_timestamp": json.dumps(None, default=str)  # Will be replaced with actual timestamp
            }
            
            return review_summary
            
        except Exception as e:
            logger.error(f"Error exporting review summary: {e}")
            raise


if __name__ == "__main__":
    # Test review utilities
    utils = ReviewUtils()
    
    # Test transcript data
    test_transcript = {
        "transcription": {
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Thank you Mr. Chairman",
                    "confidence": "low"
                },
                {
                    "id": 1,
                    "start": 5.0,
                    "end": 10.0,
                    "text": "I yield the floor to Senator Cruz",
                    "confidence": "high",
                    "speaker": "Chair"
                }
            ]
        }
    }
    
    # Test corrections
    test_corrections = [
        {
            "id": "test-1",
            "segment_id": 0,
            "speaker_name": "Sen. Warren",
            "confidence": 0.9,
            "reviewer_id": "test_reviewer",
            "created_at": "2024-01-01T10:00:00"
        }
    ]
    
    # Test prepare for review
    enhanced = utils.prepare_for_review(test_transcript, test_corrections)
    print("Enhanced transcript:", json.dumps(enhanced, indent=2, default=str))
    
    # Test apply corrections
    corrected = utils.apply_corrections(test_transcript, test_corrections)
    print("Corrected transcript:", json.dumps(corrected, indent=2, default=str))