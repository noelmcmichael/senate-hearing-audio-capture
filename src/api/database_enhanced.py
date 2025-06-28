"""
Enhanced database schema for Phase 7B UI components.
Extends Phase 7A database with UI-specific tables for session management,
review assignments, system alerts, and user preferences.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
from datetime import datetime
import uuid

# Import the Phase 7A database
from ..sync.database_schema import UnifiedHearingDatabase

logger = logging.getLogger(__name__)

class EnhancedUIDatabase(UnifiedHearingDatabase):
    """Enhanced database with UI-specific tables and functionality"""
    
    def __init__(self, db_path: str = "data/hearings_unified.db"):
        """Initialize enhanced database with UI tables"""
        super().__init__(db_path)
        self._create_ui_schema()
    
    def _create_ui_schema(self):
        """Create UI-specific tables"""
        
        # User sessions for basic authentication and role management
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('reviewer', 'quality_controller', 'admin')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Review assignments for workflow management
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS review_assignments (
                assignment_id TEXT PRIMARY KEY,
                hearing_id TEXT NOT NULL,
                transcript_id TEXT,
                assigned_to TEXT,
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped')),
                estimated_duration_minutes INTEGER,
                actual_duration_minutes INTEGER,
                quality_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (hearing_id) REFERENCES hearings_unified(id)
            )
        """)
        
        # System alerts for monitoring and error management
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS system_alerts (
                alert_id TEXT PRIMARY KEY,
                alert_type TEXT NOT NULL CHECK (alert_type IN (
                    'sync_failure', 'quality_degradation', 'system_error', 
                    'capacity_warning', 'api_limit', 'duplicate_overload'
                )),
                severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
                title TEXT NOT NULL,
                description TEXT,
                component TEXT CHECK (component IN ('api', 'scraper', 'transcription', 'review', 'database')),
                metadata TEXT, -- JSON for additional context
                resolved BOOLEAN DEFAULT FALSE,
                auto_resolvable BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                resolved_by TEXT
            )
        """)
        
        # UI preferences for user customization
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS ui_preferences (
                user_id TEXT NOT NULL,
                preference_key TEXT NOT NULL,
                preference_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, preference_key)
            )
        """)
        
        # Quality metrics for performance tracking
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS quality_metrics (
                metric_id TEXT PRIMARY KEY,
                hearing_id TEXT,
                reviewer_id TEXT,
                metric_type TEXT NOT NULL CHECK (metric_type IN (
                    'accuracy_score', 'review_speed', 'correction_count', 
                    'confidence_improvement', 'user_satisfaction'
                )),
                metric_value REAL NOT NULL,
                baseline_value REAL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hearing_id) REFERENCES hearings_unified(id)
            )
        """)
        
        # Sync status tracking for real-time monitoring
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sync_status (
                status_id TEXT PRIMARY KEY,
                component TEXT NOT NULL CHECK (component IN ('congress_api', 'committee_scraper', 'deduplication')),
                committee_code TEXT,
                status TEXT NOT NULL CHECK (status IN ('healthy', 'warning', 'error', 'maintenance')),
                last_success TIMESTAMP,
                last_attempt TIMESTAMP,
                error_count INTEGER DEFAULT 0,
                error_message TEXT,
                performance_metrics TEXT, -- JSON
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        self._create_indexes()
        
        self.connection.commit()
        logger.info("Enhanced UI database schema created successfully")
    
    def _create_indexes(self):
        """Create database indexes for performance optimization"""
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_review_assignments_status ON review_assignments(status)",
            "CREATE INDEX IF NOT EXISTS idx_review_assignments_priority ON review_assignments(priority DESC)",
            "CREATE INDEX IF NOT EXISTS idx_review_assignments_assigned_to ON review_assignments(assigned_to)",
            "CREATE INDEX IF NOT EXISTS idx_system_alerts_severity ON system_alerts(severity)",
            "CREATE INDEX IF NOT EXISTS idx_system_alerts_resolved ON system_alerts(resolved)",
            "CREATE INDEX IF NOT EXISTS idx_quality_metrics_hearing_id ON quality_metrics(hearing_id)",
            "CREATE INDEX IF NOT EXISTS idx_quality_metrics_type ON quality_metrics(metric_type)",
            "CREATE INDEX IF NOT EXISTS idx_sync_status_component ON sync_status(component)",
            "CREATE INDEX IF NOT EXISTS idx_sync_status_updated ON sync_status(updated_at DESC)"
        ]
        
        for index_sql in indexes:
            self.connection.execute(index_sql)
    
    # User Session Management
    def create_user_session(self, user_id: str, role: str = "reviewer") -> str:
        """Create a new user session"""
        session_id = str(uuid.uuid4())
        
        self.connection.execute("""
            INSERT INTO user_sessions (session_id, user_id, role)
            VALUES (?, ?, ?)
        """, (session_id, user_id, role))
        
        self.connection.commit()
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Validate user session and return user info"""
        cursor = self.connection.execute("""
            SELECT user_id, role, created_at, last_active
            FROM user_sessions
            WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        if row:
            # Update last active timestamp
            self.connection.execute("""
                UPDATE user_sessions 
                SET last_active = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, (session_id,))
            self.connection.commit()
            
            return dict(row)
        return None
    
    # Review Assignment Management
    def create_review_assignment(self, hearing_id: str, assigned_to: str = None, 
                               priority: int = 0, transcript_id: str = None) -> str:
        """Create a new review assignment"""
        assignment_id = str(uuid.uuid4())
        
        self.connection.execute("""
            INSERT INTO review_assignments 
            (assignment_id, hearing_id, transcript_id, assigned_to, priority)
            VALUES (?, ?, ?, ?, ?)
        """, (assignment_id, hearing_id, transcript_id, assigned_to, priority))
        
        self.connection.commit()
        return assignment_id
    
    def get_review_queue(self, assigned_to: str = None, status: str = None, 
                        limit: int = 50) -> List[Dict]:
        """Get review queue with optional filtering"""
        
        conditions = []
        params = []
        
        if assigned_to:
            conditions.append("ra.assigned_to = ?")
            params.append(assigned_to)
        
        if status:
            conditions.append("ra.status = ?")
            params.append(status)
        
        where_clause = " AND " + " AND ".join(conditions) if conditions else ""
        params.append(limit)
        
        cursor = self.connection.execute(f"""
            SELECT ra.*, h.hearing_title, h.committee_code, h.hearing_date
            FROM review_assignments ra
            JOIN hearings_unified h ON ra.hearing_id = h.id
            WHERE 1=1 {where_clause}
            ORDER BY ra.priority DESC, ra.created_at ASC
            LIMIT ?
        """, params)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def update_assignment_status(self, assignment_id: str, status: str, 
                               quality_score: float = None) -> bool:
        """Update review assignment status"""
        
        update_fields = ["status = ?"]
        params = [status]
        
        if status == "in_progress":
            update_fields.append("started_at = CURRENT_TIMESTAMP")
        elif status == "completed":
            update_fields.append("completed_at = CURRENT_TIMESTAMP")
            if quality_score is not None:
                update_fields.append("quality_score = ?")
                params.append(quality_score)
        
        params.append(assignment_id)
        
        cursor = self.connection.execute(f"""
            UPDATE review_assignments 
            SET {', '.join(update_fields)}
            WHERE assignment_id = ?
        """, params)
        
        self.connection.commit()
        return cursor.rowcount > 0
    
    # System Alert Management
    def create_alert(self, alert_type: str, severity: str, title: str, 
                    description: str = None, component: str = None, 
                    metadata: Dict = None, auto_resolvable: bool = False) -> str:
        """Create a new system alert"""
        
        alert_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata) if metadata else None
        
        self.connection.execute("""
            INSERT INTO system_alerts 
            (alert_id, alert_type, severity, title, description, component, 
             metadata, auto_resolvable)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (alert_id, alert_type, severity, title, description, 
              component, metadata_json, auto_resolvable))
        
        self.connection.commit()
        return alert_id
    
    def get_active_alerts(self, severity: str = None, component: str = None) -> List[Dict]:
        """Get active system alerts"""
        
        conditions = ["resolved = FALSE"]
        params = []
        
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        
        if component:
            conditions.append("component = ?")
            params.append(component)
        
        where_clause = " AND ".join(conditions)
        
        cursor = self.connection.execute(f"""
            SELECT alert_id, alert_type, severity, title, description, 
                   component, metadata, created_at, auto_resolvable
            FROM system_alerts
            WHERE {where_clause}
            ORDER BY 
                CASE severity 
                    WHEN 'critical' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'medium' THEN 3 
                    WHEN 'low' THEN 4 
                END,
                created_at DESC
        """, params)
        
        alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            if alert['metadata']:
                alert['metadata'] = json.loads(alert['metadata'])
            alerts.append(alert)
        
        return alerts
    
    def resolve_alert(self, alert_id: str, resolved_by: str = None) -> bool:
        """Resolve a system alert"""
        
        cursor = self.connection.execute("""
            UPDATE system_alerts 
            SET resolved = TRUE, resolved_at = CURRENT_TIMESTAMP, resolved_by = ?
            WHERE alert_id = ? AND resolved = FALSE
        """, (resolved_by, alert_id))
        
        self.connection.commit()
        return cursor.rowcount > 0
    
    # Quality Metrics Management
    def record_quality_metric(self, metric_type: str, metric_value: float,
                            hearing_id: str = None, reviewer_id: str = None,
                            baseline_value: float = None) -> str:
        """Record a quality metric"""
        
        metric_id = str(uuid.uuid4())
        
        self.connection.execute("""
            INSERT INTO quality_metrics 
            (metric_id, hearing_id, reviewer_id, metric_type, metric_value, baseline_value)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (metric_id, hearing_id, reviewer_id, metric_type, metric_value, baseline_value))
        
        self.connection.commit()
        return metric_id
    
    def get_quality_trends(self, metric_type: str, days: int = 30) -> List[Dict]:
        """Get quality trends over time"""
        
        cursor = self.connection.execute("""
            SELECT DATE(recorded_at) as date, 
                   AVG(metric_value) as avg_value,
                   COUNT(*) as count
            FROM quality_metrics
            WHERE metric_type = ? 
            AND recorded_at >= datetime('now', '-{} days')
            GROUP BY DATE(recorded_at)
            ORDER BY date ASC
        """.format(days), (metric_type,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # Sync Status Management
    def update_sync_status(self, component: str, status: str, 
                          committee_code: str = None, error_message: str = None,
                          performance_metrics: Dict = None) -> str:
        """Update sync status for a component"""
        
        status_id = f"{component}_{committee_code or 'global'}_{int(datetime.now().timestamp())}"
        performance_json = json.dumps(performance_metrics) if performance_metrics else None
        
        # Update or insert sync status
        self.connection.execute("""
            INSERT OR REPLACE INTO sync_status 
            (status_id, component, committee_code, status, last_attempt, 
             error_message, performance_metrics, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, CURRENT_TIMESTAMP)
        """, (status_id, component, committee_code, status, error_message, performance_json))
        
        # Update last_success if status is healthy
        if status == "healthy":
            self.connection.execute("""
                UPDATE sync_status 
                SET last_success = CURRENT_TIMESTAMP, error_count = 0
                WHERE status_id = ?
            """, (status_id,))
        else:
            # Increment error count
            self.connection.execute("""
                UPDATE sync_status 
                SET error_count = error_count + 1
                WHERE status_id = ?
            """, (status_id,))
        
        self.connection.commit()
        return status_id
    
    def get_sync_health(self) -> Dict[str, Any]:
        """Get overall sync health status"""
        
        cursor = self.connection.execute("""
            SELECT component, committee_code, status, last_success, 
                   last_attempt, error_count, error_message, performance_metrics
            FROM sync_status
            WHERE updated_at >= datetime('now', '-1 hour')
            ORDER BY updated_at DESC
        """)
        
        health_data = {
            'overall_status': 'healthy',
            'components': {},
            'last_updated': datetime.now().isoformat()
        }
        
        for row in cursor.fetchall():
            component = row['component']
            if component not in health_data['components']:
                health_data['components'][component] = {
                    'status': row['status'],
                    'committees': {},
                    'last_success': row['last_success'],
                    'error_count': row['error_count']
                }
            
            if row['committee_code']:
                health_data['components'][component]['committees'][row['committee_code']] = {
                    'status': row['status'],
                    'last_success': row['last_success'],
                    'error_message': row['error_message'],
                    'performance_metrics': json.loads(row['performance_metrics']) if row['performance_metrics'] else None
                }
            
            # Update overall status based on component status
            if row['status'] in ['error', 'warning'] and health_data['overall_status'] == 'healthy':
                health_data['overall_status'] = row['status']
            elif row['status'] == 'error':
                health_data['overall_status'] = 'error'
        
        return health_data
    
    # User Preferences Management
    def set_user_preference(self, user_id: str, key: str, value: str) -> bool:
        """Set user preference"""
        
        self.connection.execute("""
            INSERT OR REPLACE INTO ui_preferences (user_id, preference_key, preference_value)
            VALUES (?, ?, ?)
        """, (user_id, key, value))
        
        self.connection.commit()
        return True
    
    def get_user_preferences(self, user_id: str) -> Dict[str, str]:
        """Get all user preferences"""
        
        cursor = self.connection.execute("""
            SELECT preference_key, preference_value
            FROM ui_preferences
            WHERE user_id = ?
        """, (user_id,))
        
        return {row['preference_key']: row['preference_value'] for row in cursor.fetchall()}
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Enhanced UI database connection closed")

# Convenience function to get database instance
def get_enhanced_db() -> EnhancedUIDatabase:
    """Get singleton enhanced database instance"""
    return EnhancedUIDatabase()