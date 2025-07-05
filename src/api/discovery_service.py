"""
Discovery Service for Selective Automation
Provides automated hearing discovery with manual processing triggers
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import existing discovery infrastructure
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
try:
    from discover_hearings import HearingDiscoveryEngine, Hearing
except ImportError:
    # Fallback for production deployment
    HearingDiscoveryEngine = None
    Hearing = None

from .database_enhanced import get_enhanced_db

logger = logging.getLogger(__name__)

@dataclass
class DiscoveredHearing:
    """Enhanced hearing data structure for discovery dashboard"""
    id: str
    title: str
    committee_code: str
    committee_name: str
    date: Optional[str] = None
    time: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    media_indicators: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None
    isvp_compatible: Optional[bool] = None
    audio_available: Optional[bool] = None
    status: str = "discovered"  # discovered, capture_requested, capturing, processing, completed, failed
    discovery_date: Optional[str] = None
    processing_priority: int = 0
    estimated_duration: Optional[int] = None
    witness_count: Optional[int] = None
    witnesses: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class DiscoveryService:
    """Service for automated hearing discovery and management"""
    
    def __init__(self):
        self.discovery_engine = HearingDiscoveryEngine() if HearingDiscoveryEngine else None
        self.db = get_enhanced_db()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_discovery_table()
    
    def _initialize_discovery_table(self):
        """Initialize discovered hearings table if it doesn't exist"""
        try:
            self.db.connection.execute("""
                CREATE TABLE IF NOT EXISTS discovered_hearings (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    committee_code TEXT NOT NULL,
                    committee_name TEXT NOT NULL,
                    date TEXT,
                    time TEXT,
                    url TEXT,
                    description TEXT,
                    media_indicators TEXT,  -- JSON
                    quality_score REAL,
                    isvp_compatible BOOLEAN,
                    audio_available BOOLEAN,
                    status TEXT DEFAULT 'discovered' CHECK (status IN (
                        'discovered', 'capture_requested', 'capturing', 
                        'processing', 'completed', 'failed'
                    )),
                    discovery_date TEXT,
                    processing_priority INTEGER DEFAULT 0,
                    estimated_duration INTEGER,
                    witness_count INTEGER,
                    witnesses TEXT,  -- JSON
                    topics TEXT,  -- JSON
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.db.connection.commit()
            logger.info("Initialized discovered_hearings table")
        except Exception as e:
            logger.error(f"Error initializing discovery table: {e}")
    
    async def discover_hearings(self, committee_codes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run automated hearing discovery
        
        Args:
            committee_codes: Optional list of committee codes to discover
            
        Returns:
            Discovery results with counts and summary
        """
        try:
            logger.info("Starting hearing discovery...")
            
            # Run discovery in background thread
            loop = asyncio.get_event_loop()
            hearings = await loop.run_in_executor(
                self.executor, 
                self._run_discovery, 
                committee_codes
            )
            
            # Process and store discovered hearings
            new_hearings = []
            updated_hearings = []
            
            for hearing in hearings:
                discovered = self._convert_to_discovered_hearing(hearing)
                
                # Check if hearing already exists
                existing = self._get_hearing_by_url(discovered.url)
                if existing:
                    # Update existing hearing
                    self._update_discovered_hearing(discovered)
                    updated_hearings.append(discovered)
                else:
                    # Add new hearing
                    self._store_discovered_hearing(discovered)
                    new_hearings.append(discovered)
            
            result = {
                "discovery_date": datetime.now().isoformat(),
                "total_discovered": len(hearings),
                "new_hearings": len(new_hearings),
                "updated_hearings": len(updated_hearings),
                "committee_codes": committee_codes or ["all"],
                "hearings": [asdict(h) for h in new_hearings[:10]]  # First 10 new hearings
            }
            
            logger.info(f"Discovery complete: {len(new_hearings)} new, {len(updated_hearings)} updated")
            return result
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            raise
    
    def _run_discovery(self, committee_codes: Optional[List[str]] = None) -> List[Hearing]:
        """Run discovery in background thread"""
        try:
            if not self.discovery_engine:
                logger.warning("Discovery engine not available - returning empty result")
                return []
                
            if committee_codes:
                hearings = []
                for committee_code in committee_codes:
                    committee_hearings = self.discovery_engine.discover_committee_hearings(committee_code)
                    hearings.extend(committee_hearings)
                return hearings
            else:
                return self.discovery_engine.discover_all_hearings()
        except Exception as e:
            logger.error(f"Discovery engine error: {e}")
            return []
    
    def _convert_to_discovered_hearing(self, hearing) -> DiscoveredHearing:
        """Convert Hearing to DiscoveredHearing"""
        return DiscoveredHearing(
            id=hearing.hearing_id or str(uuid.uuid4()),
            title=hearing.title,
            committee_code=hearing.committee_code,
            committee_name=hearing.committee_name,
            date=hearing.date,
            time=hearing.time,
            url=hearing.url,
            description=f"{hearing.committee_name} - {hearing.title}",
            media_indicators={
                "isvp_url": hearing.isvp_url,
                "youtube_url": hearing.youtube_url,
                "transcript_url": hearing.transcript_url,
                "audio_available": hearing.audio_available,
                "video_available": hearing.video_available
            },
            quality_score=hearing.quality_score,
            isvp_compatible=hearing.isvp_compatible,
            audio_available=hearing.audio_available,
            status="discovered",
            discovery_date=datetime.now().isoformat(),
            processing_priority=hearing.processing_priority or 0,
            estimated_duration=hearing.duration_estimate,
            witness_count=hearing.witness_count,
            witnesses=hearing.witnesses,
            topics=hearing.topics,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def _store_discovered_hearing(self, hearing: DiscoveredHearing):
        """Store discovered hearing in database"""
        try:
            self.db.connection.execute("""
                INSERT INTO discovered_hearings (
                    id, title, committee_code, committee_name, date, time, url,
                    description, media_indicators, quality_score, isvp_compatible,
                    audio_available, status, discovery_date, processing_priority,
                    estimated_duration, witness_count, witnesses, topics,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hearing.id, hearing.title, hearing.committee_code, hearing.committee_name,
                hearing.date, hearing.time, hearing.url, hearing.description,
                json.dumps(hearing.media_indicators) if hearing.media_indicators else None,
                hearing.quality_score, hearing.isvp_compatible, hearing.audio_available,
                hearing.status, hearing.discovery_date, hearing.processing_priority,
                hearing.estimated_duration, hearing.witness_count,
                json.dumps(hearing.witnesses) if hearing.witnesses else None,
                json.dumps(hearing.topics) if hearing.topics else None,
                hearing.created_at, hearing.updated_at
            ))
            self.db.connection.commit()
            logger.debug(f"Stored discovered hearing: {hearing.id}")
        except Exception as e:
            logger.error(f"Error storing hearing {hearing.id}: {e}")
    
    def _update_discovered_hearing(self, hearing: DiscoveredHearing):
        """Update existing discovered hearing"""
        try:
            hearing.updated_at = datetime.now().isoformat()
            self.db.connection.execute("""
                UPDATE discovered_hearings SET
                    title = ?, committee_code = ?, committee_name = ?, date = ?,
                    time = ?, url = ?, description = ?, media_indicators = ?,
                    quality_score = ?, isvp_compatible = ?, audio_available = ?,
                    discovery_date = ?, processing_priority = ?, estimated_duration = ?,
                    witness_count = ?, witnesses = ?, topics = ?, updated_at = ?
                WHERE id = ?
            """, (
                hearing.title, hearing.committee_code, hearing.committee_name,
                hearing.date, hearing.time, hearing.url, hearing.description,
                json.dumps(hearing.media_indicators) if hearing.media_indicators else None,
                hearing.quality_score, hearing.isvp_compatible, hearing.audio_available,
                hearing.discovery_date, hearing.processing_priority,
                hearing.estimated_duration, hearing.witness_count,
                json.dumps(hearing.witnesses) if hearing.witnesses else None,
                json.dumps(hearing.topics) if hearing.topics else None,
                hearing.updated_at, hearing.id
            ))
            self.db.connection.commit()
            logger.debug(f"Updated discovered hearing: {hearing.id}")
        except Exception as e:
            logger.error(f"Error updating hearing {hearing.id}: {e}")
    
    def _get_hearing_by_url(self, url: str) -> Optional[DiscoveredHearing]:
        """Get hearing by URL"""
        if not url:
            return None
        
        try:
            cursor = self.db.connection.execute(
                "SELECT * FROM discovered_hearings WHERE url = ?", (url,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_discovered_hearing(row)
            return None
        except Exception as e:
            logger.error(f"Error getting hearing by URL: {e}")
            return None
    
    def get_discovered_hearings(self, 
                               committee_codes: Optional[List[str]] = None,
                               status: Optional[str] = None,
                               limit: int = 50) -> List[DiscoveredHearing]:
        """
        Get discovered hearings with optional filtering
        
        Args:
            committee_codes: Filter by committee codes
            status: Filter by status
            limit: Maximum number of results
            
        Returns:
            List of discovered hearings
        """
        try:
            query = "SELECT * FROM discovered_hearings WHERE 1=1"
            params = []
            
            if committee_codes:
                placeholders = ",".join(["?"] * len(committee_codes))
                query += f" AND committee_code IN ({placeholders})"
                params.extend(committee_codes)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = self.db.connection.execute(query, params)
            rows = cursor.fetchall()
            
            hearings = []
            for row in rows:
                hearing = self._row_to_discovered_hearing(row)
                if hearing:
                    hearings.append(hearing)
            
            return hearings
            
        except Exception as e:
            logger.error(f"Error getting discovered hearings: {e}")
            return []
    
    def _row_to_discovered_hearing(self, row) -> Optional[DiscoveredHearing]:
        """Convert database row to DiscoveredHearing"""
        try:
            return DiscoveredHearing(
                id=row[0],
                title=row[1],
                committee_code=row[2],
                committee_name=row[3],
                date=row[4],
                time=row[5],
                url=row[6],
                description=row[7],
                media_indicators=json.loads(row[8]) if row[8] else None,
                quality_score=row[9],
                isvp_compatible=row[10],
                audio_available=row[11],
                status=row[12],
                discovery_date=row[13],
                processing_priority=row[14],
                estimated_duration=row[15],
                witness_count=row[16],
                witnesses=json.loads(row[17]) if row[17] else None,
                topics=json.loads(row[18]) if row[18] else None,
                error_message=row[19],
                created_at=row[20],
                updated_at=row[21]
            )
        except Exception as e:
            logger.error(f"Error converting row to hearing: {e}")
            return None
    
    def update_hearing_status(self, hearing_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """
        Update hearing status
        
        Args:
            hearing_id: Hearing ID
            status: New status
            error_message: Optional error message
            
        Returns:
            True if successful
        """
        try:
            self.db.connection.execute("""
                UPDATE discovered_hearings 
                SET status = ?, error_message = ?, updated_at = ?
                WHERE id = ?
            """, (status, error_message, datetime.now().isoformat(), hearing_id))
            self.db.connection.commit()
            logger.info(f"Updated hearing {hearing_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating hearing status: {e}")
            return False
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get discovery statistics"""
        try:
            cursor = self.db.connection.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'discovered' THEN 1 END) as discovered,
                    COUNT(CASE WHEN status = 'capture_requested' THEN 1 END) as capture_requested,
                    COUNT(CASE WHEN status = 'capturing' THEN 1 END) as capturing,
                    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN isvp_compatible = 1 THEN 1 END) as isvp_compatible,
                    AVG(quality_score) as avg_quality_score,
                    MAX(created_at) as last_discovery
                FROM discovered_hearings
            """)
            row = cursor.fetchone()
            
            if row:
                return {
                    "total_hearings": row[0],
                    "status_counts": {
                        "discovered": row[1],
                        "capture_requested": row[2],
                        "capturing": row[3],
                        "processing": row[4],
                        "completed": row[5],
                        "failed": row[6]
                    },
                    "isvp_compatible": row[7],
                    "avg_quality_score": row[8],
                    "last_discovery": row[9]
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting discovery stats: {e}")
            return {}

# Global service instance
_discovery_service = None

def get_discovery_service() -> DiscoveryService:
    """Get discovery service singleton"""
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = DiscoveryService()
    return _discovery_service