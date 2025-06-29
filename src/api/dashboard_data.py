"""
Legacy dashboard data API for Phase 7B compatibility.
Provides simple API endpoints for dashboard data display.
"""

from pathlib import Path
from typing import Dict, List, Any
import json
import glob
from datetime import datetime

class DashboardDataAPI:
    """Simple API wrapper for dashboard data"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path('output')
    
    def get_hearings_summary(self) -> Dict[str, Any]:
        """Get basic hearings summary for dashboard"""
        return {
            "total_hearings": 0,
            "successful_extractions": 0,
            "total_duration_hours": 0,
            "committees_covered": []
        }
    
    def get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent extraction activity"""
        return []
    
    def get_committee_stats(self) -> Dict[str, Any]:
        """Get committee-specific statistics"""
        return {}
    
    def get_transcripts(self) -> Dict[str, Any]:
        """Get list of available transcripts"""
        return {
            "transcripts": [],
            "total": 0,
            "message": "No transcripts available in demo mode"
        }
    
    def get_transcript_content(self, transcript_id: str) -> Dict[str, Any]:
        """Get specific transcript content"""
        return {
            "transcript_id": transcript_id,
            "content": "Demo transcript content not available",
            "status": "demo_mode",
            "message": f"Transcript {transcript_id} not found in demo mode"
        }