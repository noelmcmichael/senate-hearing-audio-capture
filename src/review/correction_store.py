#!/usr/bin/env python3
"""
Correction Storage for Human Review System

Manages speaker correction data with SQLite backend:
- Store speaker assignments and corrections
- Track review audit trail
- Support correction queries and updates
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


logger = logging.getLogger(__name__)


class CorrectionStore:
    """SQLite-based storage for transcript corrections."""
    
    def __init__(self, db_path: Path = None):
        """Initialize correction store."""
        self.db_path = db_path or Path("output/corrections.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS corrections (
                    id TEXT PRIMARY KEY,
                    transcript_file TEXT NOT NULL,
                    segment_id INTEGER NOT NULL,
                    speaker_name TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    reviewer_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    is_active BOOLEAN DEFAULT 1
                );
                
                CREATE INDEX IF NOT EXISTS idx_transcript_file 
                ON corrections(transcript_file);
                
                CREATE INDEX IF NOT EXISTS idx_segment_id 
                ON corrections(transcript_file, segment_id);
                
                CREATE TABLE IF NOT EXISTS review_sessions (
                    id TEXT PRIMARY KEY,
                    transcript_file TEXT NOT NULL,
                    reviewer_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    progress_data TEXT,
                    status TEXT DEFAULT 'active'
                );
                
                CREATE INDEX IF NOT EXISTS idx_review_sessions 
                ON review_sessions(transcript_file, reviewer_id);
                
                CREATE TABLE IF NOT EXISTS correction_audit (
                    id TEXT PRIMARY KEY,
                    correction_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    reviewer_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (correction_id) REFERENCES corrections (id)
                );
            """)
    
    def save_correction(
        self,
        transcript_file: str,
        segment_id: int,
        speaker_name: str,
        confidence: float = 1.0,
        reviewer_id: str = "unknown"
    ) -> str:
        """Save a speaker correction."""
        correction_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if correction already exists for this segment
                existing = conn.execute(
                    "SELECT id, speaker_name FROM corrections "
                    "WHERE transcript_file = ? AND segment_id = ? AND is_active = 1",
                    (transcript_file, segment_id)
                ).fetchone()
                
                if existing:
                    # Update existing correction
                    old_correction_id, old_speaker = existing
                    
                    # Deactivate old correction
                    conn.execute(
                        "UPDATE corrections SET is_active = 0, updated_at = ? "
                        "WHERE id = ?",
                        (timestamp, old_correction_id)
                    )
                    
                    # Log audit trail
                    self._log_audit(
                        conn, old_correction_id, "UPDATE", 
                        old_speaker, speaker_name, reviewer_id, timestamp
                    )
                
                # Insert new correction
                conn.execute(
                    "INSERT INTO corrections "
                    "(id, transcript_file, segment_id, speaker_name, confidence, "
                    "reviewer_id, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (correction_id, transcript_file, segment_id, speaker_name,
                     confidence, reviewer_id, timestamp)
                )
                
                # Log audit trail for new correction
                self._log_audit(
                    conn, correction_id, "CREATE", 
                    None, speaker_name, reviewer_id, timestamp
                )
                
                logger.info(f"Saved correction {correction_id} for segment {segment_id}")
                return correction_id
                
        except Exception as e:
            logger.error(f"Error saving correction: {e}")
            raise
    
    def get_corrections(self, transcript_file: str) -> List[Dict[str, Any]]:
        """Get all active corrections for a transcript."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                rows = conn.execute(
                    "SELECT * FROM corrections "
                    "WHERE transcript_file = ? AND is_active = 1 "
                    "ORDER BY segment_id",
                    (transcript_file,)
                ).fetchall()
                
                corrections = []
                for row in rows:
                    correction = dict(row)
                    correction['created_at'] = datetime.fromisoformat(correction['created_at'])
                    if correction['updated_at']:
                        correction['updated_at'] = datetime.fromisoformat(correction['updated_at'])
                    corrections.append(correction)
                
                return corrections
                
        except Exception as e:
            logger.error(f"Error getting corrections: {e}")
            return []
    
    def has_corrections(self, transcript_file: str) -> bool:
        """Check if transcript has any corrections."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute(
                    "SELECT COUNT(*) FROM corrections "
                    "WHERE transcript_file = ? AND is_active = 1",
                    (transcript_file,)
                ).fetchone()
                
                return result[0] > 0
                
        except Exception as e:
            logger.error(f"Error checking corrections: {e}")
            return False
    
    def get_correction_stats(self, transcript_file: str) -> Dict[str, Any]:
        """Get correction statistics for a transcript."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Basic stats
                basic_stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_corrections,
                        COUNT(DISTINCT segment_id) as segments_corrected,
                        COUNT(DISTINCT speaker_name) as unique_speakers,
                        COUNT(DISTINCT reviewer_id) as reviewers,
                        AVG(confidence) as avg_confidence
                    FROM corrections 
                    WHERE transcript_file = ? AND is_active = 1
                """, (transcript_file,)).fetchone()
                
                # Speaker distribution
                speaker_stats = conn.execute("""
                    SELECT speaker_name, COUNT(*) as segment_count
                    FROM corrections 
                    WHERE transcript_file = ? AND is_active = 1
                    GROUP BY speaker_name
                    ORDER BY segment_count DESC
                """, (transcript_file,)).fetchall()
                
                return {
                    "total_corrections": basic_stats["total_corrections"],
                    "segments_corrected": basic_stats["segments_corrected"],
                    "unique_speakers": basic_stats["unique_speakers"],
                    "reviewers": basic_stats["reviewers"],
                    "avg_confidence": round(basic_stats["avg_confidence"] or 0, 2),
                    "speaker_distribution": [dict(row) for row in speaker_stats]
                }
                
        except Exception as e:
            logger.error(f"Error getting correction stats: {e}")
            return {}
    
    def start_review_session(
        self, 
        transcript_file: str, 
        reviewer_id: str
    ) -> str:
        """Start a new review session."""
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO review_sessions "
                    "(id, transcript_file, reviewer_id, start_time) "
                    "VALUES (?, ?, ?, ?)",
                    (session_id, transcript_file, reviewer_id, timestamp)
                )
                
                logger.info(f"Started review session {session_id}")
                return session_id
                
        except Exception as e:
            logger.error(f"Error starting review session: {e}")
            raise
    
    def update_review_progress(
        self, 
        session_id: str, 
        progress_data: Dict[str, Any]
    ):
        """Update review session progress."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE review_sessions "
                    "SET progress_data = ? "
                    "WHERE id = ?",
                    (json.dumps(progress_data), session_id)
                )
                
        except Exception as e:
            logger.error(f"Error updating review progress: {e}")
            raise
    
    def end_review_session(self, session_id: str):
        """End a review session."""
        timestamp = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE review_sessions "
                    "SET end_time = ?, status = 'completed' "
                    "WHERE id = ?",
                    (timestamp, session_id)
                )
                
                logger.info(f"Ended review session {session_id}")
                
        except Exception as e:
            logger.error(f"Error ending review session: {e}")
            raise
    
    def _log_audit(
        self,
        conn: sqlite3.Connection,
        correction_id: str,
        action: str,
        old_value: Optional[str],
        new_value: str,
        reviewer_id: str,
        timestamp: str
    ):
        """Log audit trail entry."""
        audit_id = str(uuid.uuid4())
        
        conn.execute(
            "INSERT INTO correction_audit "
            "(id, correction_id, action, old_value, new_value, reviewer_id, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (audit_id, correction_id, action, old_value, new_value, reviewer_id, timestamp)
        )
    
    def get_audit_trail(self, transcript_file: str) -> List[Dict[str, Any]]:
        """Get audit trail for a transcript."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                rows = conn.execute("""
                    SELECT ca.*, c.segment_id
                    FROM correction_audit ca
                    JOIN corrections c ON ca.correction_id = c.id
                    WHERE c.transcript_file = ?
                    ORDER BY ca.timestamp DESC
                """, (transcript_file,)).fetchall()
                
                audit_entries = []
                for row in rows:
                    entry = dict(row)
                    entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                    audit_entries.append(entry)
                
                return audit_entries
                
        except Exception as e:
            logger.error(f"Error getting audit trail: {e}")
            return []


if __name__ == "__main__":
    # Test the correction store
    store = CorrectionStore()
    
    # Save test correction
    correction_id = store.save_correction(
        transcript_file="test_transcript.json",
        segment_id=1,
        speaker_name="Sen. Cruz",
        confidence=0.95,
        reviewer_id="test_reviewer"
    )
    
    print(f"Saved correction: {correction_id}")
    
    # Get corrections
    corrections = store.get_corrections("test_transcript.json")
    print(f"Corrections: {corrections}")
    
    # Get stats
    stats = store.get_correction_stats("test_transcript.json")
    print(f"Stats: {stats}")