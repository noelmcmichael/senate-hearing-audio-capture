"""
Enhanced database schema for unified hearing management with multi-source tracking.
Part of Phase 7A: Automated Data Synchronization
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class UnifiedHearingDatabase:
    """Manages unified hearing database with multi-source tracking"""
    
    def __init__(self, db_path: str = "data/hearings_unified.db"):
        """Initialize database connection and ensure schema exists"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()
    
    def _create_schema(self):
        """Create unified hearing schema if it doesn't exist"""
        
        # Unified hearings table with multi-source tracking
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS hearings_unified (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- Source Identification
                congress_api_id TEXT,
                committee_source_id TEXT,
                external_urls TEXT, -- JSON array
                
                -- Core Data
                committee_code TEXT NOT NULL,
                hearing_title TEXT NOT NULL,
                hearing_date TEXT NOT NULL, -- ISO format
                hearing_type TEXT, -- Hearing, Markup, Meeting
                
                -- Sync Tracking  
                source_api INTEGER DEFAULT 0, -- Boolean (0/1)
                source_website INTEGER DEFAULT 0,
                last_api_sync TEXT, -- ISO timestamp
                last_website_sync TEXT,
                sync_confidence REAL DEFAULT 0.0,
                
                -- Media Resources
                streams TEXT, -- JSON: {audio_stream, video_stream, archive_links}
                documents TEXT, -- JSON: Witness docs, committee materials  
                witnesses TEXT, -- JSON: Witness information
                
                -- Processing Pipeline
                sync_status TEXT DEFAULT 'discovered',
                extraction_status TEXT DEFAULT 'pending',
                transcription_status TEXT DEFAULT 'pending', 
                review_status TEXT DEFAULT 'pending',
                
                -- Metadata
                meeting_status TEXT, -- Scheduled, Completed, Canceled
                location_info TEXT, -- JSON
                
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sync audit trail
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hearing_id INTEGER,
                sync_source TEXT, -- 'congress_api', 'website_scraper'
                sync_type TEXT, -- 'create', 'update', 'merge'
                changes_detected TEXT, -- JSON
                sync_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 1,
                error_message TEXT,
                FOREIGN KEY (hearing_id) REFERENCES hearings_unified(id)
            )
        """)
        
        # Source priority configuration
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sync_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                committee_code TEXT UNIQUE,
                priority_level INTEGER DEFAULT 1, -- 1=highest, 5=lowest
                api_enabled INTEGER DEFAULT 1,
                website_enabled INTEGER DEFAULT 1,
                sync_frequency_hours INTEGER DEFAULT 8,
                last_sync_attempt TEXT,
                active INTEGER DEFAULT 1
            )
        """)
        
        # Performance metrics tracking
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sync_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_run_id TEXT,
                committee_code TEXT,
                sync_source TEXT,
                hearings_discovered INTEGER DEFAULT 0,
                hearings_updated INTEGER DEFAULT 0,
                duplicates_merged INTEGER DEFAULT 0,
                errors_encountered INTEGER DEFAULT 0,
                execution_time_seconds REAL,
                success_rate REAL,
                sync_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.connection.commit()
        
        # Initialize default priority committees if table is empty
        self._initialize_priority_committees()
    
    def _initialize_priority_committees(self):
        """Initialize priority committee configurations"""
        
        priority_committees = [
            {
                'committee_code': 'SCOM', 
                'priority_level': 1,
                'sync_frequency_hours': 4  # High frequency for testing
            },
            {
                'committee_code': 'SSCI', 
                'priority_level': 1,
                'sync_frequency_hours': 6
            },
            {
                'committee_code': 'SBAN',
                'priority_level': 2, 
                'sync_frequency_hours': 8
            },
            {
                'committee_code': 'SSJU',
                'priority_level': 1,
                'sync_frequency_hours': 6
            },
            {
                'committee_code': 'HJUD',
                'priority_level': 2,
                'sync_frequency_hours': 12
            }
        ]
        
        # Check if configs already exist
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM sync_config")
        if cursor.fetchone()[0] == 0:
            for committee in priority_committees:
                self.add_sync_config(**committee)
    
    def add_sync_config(self, committee_code: str, priority_level: int = 1, 
                       sync_frequency_hours: int = 8, **kwargs):
        """Add or update sync configuration for a committee"""
        
        self.connection.execute("""
            INSERT OR REPLACE INTO sync_config 
            (committee_code, priority_level, sync_frequency_hours, api_enabled, website_enabled)
            VALUES (?, ?, ?, ?, ?)
        """, (committee_code, priority_level, sync_frequency_hours, 1, 1))
        self.connection.commit()
    
    def insert_hearing(self, hearing_data: Dict[str, Any], source: str) -> int:
        """Insert new hearing record with source tracking"""
        
        now = datetime.now().isoformat()
        
        # Determine source flags
        source_api = 1 if source == 'congress_api' else 0
        source_website = 1 if source == 'website_scraper' else 0
        
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO hearings_unified (
                congress_api_id, committee_source_id, committee_code,
                hearing_title, hearing_date, hearing_type,
                source_api, source_website, 
                last_api_sync, last_website_sync,
                streams, documents, witnesses,
                meeting_status, location_info,
                sync_confidence, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            hearing_data.get('congress_api_id'),
            hearing_data.get('committee_source_id'),
            hearing_data['committee_code'],
            hearing_data['hearing_title'],
            hearing_data['hearing_date'],
            hearing_data.get('hearing_type', 'Hearing'),
            source_api, source_website,
            now if source_api else None,
            now if source_website else None,
            json.dumps(hearing_data.get('streams', {})),
            json.dumps(hearing_data.get('documents', {})),
            json.dumps(hearing_data.get('witnesses', {})),
            hearing_data.get('meeting_status', 'Scheduled'),
            json.dumps(hearing_data.get('location_info', {})),
            hearing_data.get('sync_confidence', 1.0),
            now, now
        ))
        
        hearing_id = cursor.lastrowid
        self.connection.commit()
        
        # Record sync history
        self.record_sync_event(hearing_id, source, 'create', hearing_data)
        
        return hearing_id
    
    def update_hearing(self, hearing_id: int, updates: Dict[str, Any], source: str):
        """Update existing hearing with change tracking"""
        
        now = datetime.now().isoformat()
        
        # Build update query dynamically
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key in ['streams', 'documents', 'witnesses', 'location_info']:
                set_clauses.append(f"{key} = ?")
                values.append(json.dumps(value))
            else:
                set_clauses.append(f"{key} = ?") 
                values.append(value)
        
        # Update source tracking
        if source == 'congress_api':
            set_clauses.append("source_api = 1, last_api_sync = ?")
            values.append(now)
        elif source == 'website_scraper':
            set_clauses.append("source_website = 1, last_website_sync = ?")
            values.append(now)
        
        set_clauses.append("updated_at = ?")
        values.append(now)
        values.append(hearing_id)  # For WHERE clause
        
        query = f"UPDATE hearings_unified SET {', '.join(set_clauses)} WHERE id = ?"
        
        self.connection.execute(query, values)
        self.connection.commit()
        
        # Record sync history
        self.record_sync_event(hearing_id, source, 'update', updates)
    
    def find_potential_duplicates(self, hearing_data: Dict[str, Any]) -> list:
        """Find potential duplicate hearings based on multiple criteria"""
        
        cursor = self.connection.cursor()
        
        # Search by title similarity, date proximity, and committee
        cursor.execute("""
            SELECT id, hearing_title, hearing_date, committee_code,
                   sync_confidence, congress_api_id, committee_source_id
            FROM hearings_unified 
            WHERE committee_code = ? 
            AND date(hearing_date) = date(?)
        """, (hearing_data['committee_code'], hearing_data['hearing_date']))
        
        candidates = []
        for row in cursor.fetchall():
            # Calculate similarity score
            similarity_score = self._calculate_similarity(hearing_data, dict(row))
            if similarity_score > 0.6:  # 60% similarity threshold
                candidates.append({
                    'id': row['id'],
                    'similarity_score': similarity_score,
                    'existing_record': dict(row)
                })
        
        return sorted(candidates, key=lambda x: x['similarity_score'], reverse=True)
    
    def _calculate_similarity(self, new_hearing: Dict[str, Any], existing_hearing: Dict[str, Any]) -> float:
        """Calculate similarity score between two hearings"""
        
        score = 0.0
        
        # Title similarity (60% weight)
        title_similarity = self._text_similarity(
            new_hearing['hearing_title'], 
            existing_hearing['hearing_title']
        )
        score += title_similarity * 0.6
        
        # Date exact match (30% weight)
        if new_hearing['hearing_date'] == existing_hearing['hearing_date']:
            score += 0.3
        
        # Committee match (10% weight)
        if new_hearing['committee_code'] == existing_hearing['committee_code']:
            score += 0.1
        
        return score
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity using word overlap"""
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def merge_hearing_records(self, primary_id: int, secondary_id: int, confidence: float = 0.9):
        """Merge two hearing records with confidence tracking"""
        
        cursor = self.connection.cursor()
        
        # Get both records
        cursor.execute("SELECT * FROM hearings_unified WHERE id = ?", (primary_id,))
        primary = dict(cursor.fetchone())
        
        cursor.execute("SELECT * FROM hearings_unified WHERE id = ?", (secondary_id,))
        secondary = dict(cursor.fetchone())
        
        # Merge logic: prefer API data over website data
        merged_data = self._merge_hearing_data(primary, secondary)
        merged_data['sync_confidence'] = confidence
        
        # Update primary record
        self.update_hearing(primary_id, merged_data, 'merge_operation')
        
        # Archive secondary record
        cursor.execute("""
            UPDATE hearings_unified 
            SET sync_status = 'merged_into_' || ?, updated_at = ?
            WHERE id = ?
        """, (str(primary_id), datetime.now().isoformat(), secondary_id))
        
        self.connection.commit()
        
        # Record merge event
        self.record_sync_event(primary_id, 'merge_operation', 'merge', {
            'merged_from': secondary_id,
            'confidence': confidence
        })
    
    def _merge_hearing_data(self, primary: Dict, secondary: Dict) -> Dict:
        """Merge two hearing records with intelligent field selection"""
        
        merged = {}
        
        # Prefer API data over website data
        api_priority_fields = ['congress_api_id', 'hearing_type', 'meeting_status']
        
        for field in api_priority_fields:
            if primary.get('source_api') and primary.get(field):
                merged[field] = primary[field]
            elif secondary.get('source_api') and secondary.get(field):
                merged[field] = secondary[field]
            elif primary.get(field):
                merged[field] = primary[field]
            elif secondary.get(field):
                merged[field] = secondary[field]
        
        # Combine media resources
        merged['streams'] = self._merge_json_field(primary.get('streams'), secondary.get('streams'))
        merged['documents'] = self._merge_json_field(primary.get('documents'), secondary.get('documents'))
        merged['witnesses'] = self._merge_json_field(primary.get('witnesses'), secondary.get('witnesses'))
        
        # Set source flags
        merged['source_api'] = max(primary.get('source_api', 0), secondary.get('source_api', 0))
        merged['source_website'] = max(primary.get('source_website', 0), secondary.get('source_website', 0))
        
        return merged
    
    def _merge_json_field(self, primary_json: str, secondary_json: str) -> Dict:
        """Merge two JSON fields with conflict resolution"""
        
        try:
            primary_data = json.loads(primary_json) if primary_json else {}
            secondary_data = json.loads(secondary_json) if secondary_json else {}
            
            # Deep merge with primary taking precedence
            merged = secondary_data.copy()
            merged.update(primary_data)
            
            return merged
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def record_sync_event(self, hearing_id: int, source: str, sync_type: str, changes: Dict[str, Any]):
        """Record sync event in audit trail"""
        
        self.connection.execute("""
            INSERT INTO sync_history (
                hearing_id, sync_source, sync_type, changes_detected, success
            ) VALUES (?, ?, ?, ?, ?)
        """, (hearing_id, source, sync_type, json.dumps(changes), 1))
        self.connection.commit()
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """Get comprehensive sync statistics"""
        
        cursor = self.connection.cursor()
        
        # Total hearings by source
        cursor.execute("""
            SELECT 
                COUNT(*) as total_hearings,
                SUM(source_api) as from_api,
                SUM(source_website) as from_website,
                SUM(CASE WHEN source_api AND source_website THEN 1 ELSE 0 END) as merged,
                AVG(sync_confidence) as avg_confidence
            FROM hearings_unified
            WHERE sync_status != 'merged_into_' || id
        """)
        
        stats = dict(cursor.fetchone())
        
        # Recent sync activity  
        cursor.execute("""
            SELECT sync_source, COUNT(*) as events
            FROM sync_history 
            WHERE sync_timestamp > datetime('now', '-24 hours')
            GROUP BY sync_source
        """)
        
        stats['recent_activity'] = {row['sync_source']: row['events'] for row in cursor.fetchall()}
        
        return stats
    
    def get_hearings_needing_sync(self, hours_threshold: int = 24) -> list:
        """Get hearings that need sync updates"""
        
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT h.*, c.sync_frequency_hours
            FROM hearings_unified h
            JOIN sync_config c ON h.committee_code = c.committee_code
            WHERE c.active = 1
            AND (
                h.last_api_sync IS NULL 
                OR datetime(h.last_api_sync) < datetime('now', '-' || c.sync_frequency_hours || ' hours')
                OR h.last_website_sync IS NULL
                OR datetime(h.last_website_sync) < datetime('now', '-' || c.sync_frequency_hours || ' hours')
            )
            ORDER BY c.priority_level, h.hearing_date DESC
        """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()

if __name__ == "__main__":
    # Test database creation
    db = UnifiedHearingDatabase("data/test_unified.db")
    
    # Test hearing insertion
    test_hearing = {
        'committee_code': 'SCOM',
        'hearing_title': 'Test Hearing on AI Oversight',
        'hearing_date': '2025-06-28',
        'hearing_type': 'Hearing',
        'streams': {'audio_stream': 'test_url'},
        'witnesses': [{'name': 'Test Witness'}],
        'sync_confidence': 0.95
    }
    
    hearing_id = db.insert_hearing(test_hearing, 'congress_api')
    print(f"Inserted test hearing with ID: {hearing_id}")
    
    # Test statistics
    stats = db.get_sync_statistics()
    print(f"Sync statistics: {stats}")
    
    db.close()
    print("Database schema creation and testing completed successfully")