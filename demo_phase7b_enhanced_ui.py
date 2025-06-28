#!/usr/bin/env python3
"""
Demo script for Phase 7B Enhanced UI system.
Demonstrates the integrated hearing management, system monitoring, and enhanced APIs.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_demo_database():
    """Create demo database with Phase 7B enhanced schema"""
    
    db_path = "data/demo_enhanced_ui.db"
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Create enhanced tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hearings_unified (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            committee_code TEXT NOT NULL,
            hearing_title TEXT NOT NULL,
            hearing_date TEXT NOT NULL,
            hearing_type TEXT,
            source_api INTEGER DEFAULT 0,
            source_website INTEGER DEFAULT 0,
            streams TEXT DEFAULT '{}',
            sync_confidence REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('reviewer', 'quality_controller', 'admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
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
            completed_at TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS system_alerts (
            alert_id TEXT PRIMARY KEY,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
            title TEXT NOT NULL,
            description TEXT,
            component TEXT,
            metadata TEXT,
            resolved BOOLEAN DEFAULT FALSE,
            auto_resolvable BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            resolved_by TEXT
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quality_metrics (
            metric_id TEXT PRIMARY KEY,
            hearing_id TEXT,
            reviewer_id TEXT,
            metric_type TEXT NOT NULL,
            metric_value REAL NOT NULL,
            baseline_value REAL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_status (
            status_id TEXT PRIMARY KEY,
            component TEXT NOT NULL,
            committee_code TEXT,
            status TEXT NOT NULL CHECK (status IN ('healthy', 'warning', 'error', 'maintenance')),
            last_success TIMESTAMP,
            last_attempt TIMESTAMP,
            error_count INTEGER DEFAULT 0,
            error_message TEXT,
            performance_metrics TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert demo data
    demo_hearings = [
        ('SCOM', 'Oversight of Federal Maritime Administration', '2025-06-29', 'Oversight Hearing', 1, 1, '{"isvp": "http://example.com/stream1", "youtube": "http://youtube.com/watch?v=test1"}', 0.95),
        ('SSJU', 'Executive Session - Judicial Nominations', '2025-06-28', 'Executive Session', 1, 0, '{"isvp": "http://example.com/stream2"}', 0.87),
        ('SSCI', 'Annual Threat Assessment Briefing', '2025-06-27', 'Briefing', 0, 1, '{}', 0.72),
        ('SBAN', 'Semiannual Monetary Policy Report', '2025-06-26', 'Hearing', 1, 1, '{"isvp": "http://example.com/stream3"}', 0.91),
        ('HJUD', 'Markup of H.R. 1234', '2025-06-25', 'Markup', 0, 1, '{}', 0.68)
    ]
    
    for hearing in demo_hearings:
        conn.execute("""
            INSERT INTO hearings_unified 
            (committee_code, hearing_title, hearing_date, hearing_type, source_api, source_website, streams, sync_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, hearing)
    
    # Insert demo user sessions
    import uuid
    sessions = [
        (str(uuid.uuid4()), 'admin_user', 'admin'),
        (str(uuid.uuid4()), 'reviewer_1', 'reviewer'),
        (str(uuid.uuid4()), 'reviewer_2', 'reviewer'),
        (str(uuid.uuid4()), 'quality_controller', 'quality_controller')
    ]
    
    for session in sessions:
        conn.execute("""
            INSERT INTO user_sessions (session_id, user_id, role)
            VALUES (?, ?, ?)
        """, session)
    
    # Insert demo review assignments
    assignments = [
        (str(uuid.uuid4()), '1', None, 'reviewer_1', 8, 'pending'),
        (str(uuid.uuid4()), '2', None, 'reviewer_2', 6, 'in_progress'),
        (str(uuid.uuid4()), '3', None, 'reviewer_1', 4, 'completed'),
        (str(uuid.uuid4()), '4', None, 'reviewer_2', 7, 'pending')
    ]
    
    for assignment in assignments:
        conn.execute("""
            INSERT INTO review_assignments 
            (assignment_id, hearing_id, transcript_id, assigned_to, priority, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, assignment)
    
    # Insert demo alerts
    alerts = [
        (str(uuid.uuid4()), 'sync_failure', 'high', 'SSCI Website Scraper Failed', 'Unable to connect to Senate Intelligence Committee website', 'scraper', '{}', False, False),
        (str(uuid.uuid4()), 'quality_degradation', 'medium', 'Transcript Accuracy Below Threshold', 'Speaker identification accuracy dropped to 82%', 'transcription', '{}', False, True),
        (str(uuid.uuid4()), 'api_limit', 'medium', 'Congress API Rate Limit Warning', 'Daily API usage at 85% of limit', 'api', '{"usage": 850, "limit": 1000}', False, True)
    ]
    
    for alert in alerts:
        conn.execute("""
            INSERT INTO system_alerts 
            (alert_id, alert_type, severity, title, description, component, metadata, resolved, auto_resolvable)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, alert)
    
    # Insert demo quality metrics
    metrics = [
        (str(uuid.uuid4()), '1', 'reviewer_1', 'accuracy_score', 87.3, 85.0),
        (str(uuid.uuid4()), '2', 'reviewer_2', 'accuracy_score', 89.1, 85.0),
        (str(uuid.uuid4()), '1', 'reviewer_1', 'review_speed', 15.2, 18.5),
        (str(uuid.uuid4()), '2', 'reviewer_2', 'review_speed', 14.8, 18.5)
    ]
    
    for metric in metrics:
        conn.execute("""
            INSERT INTO quality_metrics 
            (metric_id, hearing_id, reviewer_id, metric_type, metric_value, baseline_value)
            VALUES (?, ?, ?, ?, ?, ?)
        """, metric)
    
    # Insert demo sync status
    sync_statuses = [
        (str(uuid.uuid4()), 'congress_api', 'SCOM', 'healthy', datetime.now().isoformat(), datetime.now().isoformat(), 0, None, '{"success_rate": 96.5, "avg_response_time": 245}'),
        (str(uuid.uuid4()), 'committee_scraper', 'SSCI', 'warning', (datetime.now() - timedelta(hours=2)).isoformat(), datetime.now().isoformat(), 3, 'Connection timeout', '{"success_rate": 89.2, "last_attempt": "' + datetime.now().isoformat() + '"}'),
        (str(uuid.uuid4()), 'deduplication', None, 'healthy', datetime.now().isoformat(), datetime.now().isoformat(), 0, None, '{"processed": 156, "duplicates_found": 3}')
    ]
    
    for status in sync_statuses:
        conn.execute("""
            INSERT INTO sync_status 
            (status_id, component, committee_code, status, last_success, last_attempt, error_count, error_message, performance_metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, status)
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Demo database created: {db_path}")
    return db_path

def test_database_queries():
    """Test database queries for Phase 7B features"""
    
    db_path = "data/demo_enhanced_ui.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    tests = []
    
    # Test 1: Hearing Queue Query
    cursor = conn.execute("""
        SELECT h.*, ra.status as review_status, ra.priority as review_priority
        FROM hearings_unified h
        LEFT JOIN review_assignments ra ON CAST(h.id AS TEXT) = ra.hearing_id
        ORDER BY ra.priority DESC, h.hearing_date DESC
        LIMIT 10
    """)
    
    hearings = cursor.fetchall()
    tests.append(f"✅ Hearing Queue: Found {len(hearings)} hearings")
    
    # Test 2: System Health Query
    cursor = conn.execute("""
        SELECT 
            COUNT(*) as total_hearings,
            SUM(CASE WHEN (source_api = 1 OR source_website = 1) THEN 1 ELSE 0 END) as discovered,
            SUM(CASE WHEN streams != '{}' THEN 1 ELSE 0 END) as with_streams
        FROM hearings_unified
    """)
    
    health_stats = cursor.fetchone()
    discovery_rate = (health_stats['discovered'] / health_stats['total_hearings'] * 100) if health_stats['total_hearings'] > 0 else 0
    tests.append(f"✅ System Health: {discovery_rate:.1f}% discovery rate")
    
    # Test 3: Active Alerts Query
    cursor = conn.execute("""
        SELECT COUNT(*) as total_alerts,
               SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical,
               SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high
        FROM system_alerts
        WHERE resolved = FALSE
    """)
    
    alert_stats = cursor.fetchone()
    tests.append(f"✅ Active Alerts: {alert_stats['total_alerts']} total ({alert_stats['critical']} critical, {alert_stats['high']} high)")
    
    # Test 4: Quality Metrics Query
    cursor = conn.execute("""
        SELECT metric_type, AVG(metric_value) as avg_value, COUNT(*) as count
        FROM quality_metrics
        GROUP BY metric_type
    """)
    
    quality_metrics = cursor.fetchall()
    tests.append(f"✅ Quality Metrics: {len(quality_metrics)} metric types tracked")
    
    # Test 5: Sync Status Query
    cursor = conn.execute("""
        SELECT component, status, COUNT(*) as count
        FROM sync_status
        GROUP BY component, status
    """)
    
    sync_components = cursor.fetchall()
    tests.append(f"✅ Sync Status: {len(sync_components)} component status entries")
    
    conn.close()
    
    for test in tests:
        logger.info(test)
    
    return len(tests)

def generate_demo_data_summary():
    """Generate summary of demo data for Phase 7B"""
    
    db_path = "data/demo_enhanced_ui.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    summary = {
        'phase': 'Phase 7B - Enhanced UI/UX Workflows',
        'demo_date': datetime.now().isoformat(),
        'database_path': db_path,
        'features_demonstrated': [
            'Automated hearing discovery and synchronization',
            'Real-time system health monitoring',
            'Enhanced transcript review workflows',
            'Duplicate resolution management',
            'Quality metrics and analytics',
            'User session management',
            'Alert system with auto-resolution'
        ],
        'data_summary': {}
    }
    
    # Get table counts
    tables = ['hearings_unified', 'user_sessions', 'review_assignments', 'system_alerts', 'quality_metrics', 'sync_status']
    
    for table in tables:
        cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
        count = cursor.fetchone()['count']
        summary['data_summary'][table] = count
    
    # Get hearing queue status
    cursor = conn.execute("""
        SELECT ra.status, COUNT(*) as count
        FROM review_assignments ra
        GROUP BY ra.status
    """)
    
    review_status = {row['status']: row['count'] for row in cursor.fetchall()}
    summary['review_queue_status'] = review_status
    
    # Get alert severity breakdown
    cursor = conn.execute("""
        SELECT severity, COUNT(*) as count
        FROM system_alerts
        WHERE resolved = FALSE
        GROUP BY severity
    """)
    
    alert_severity = {row['severity']: row['count'] for row in cursor.fetchall()}
    summary['active_alerts_by_severity'] = alert_severity
    
    # Get committee coverage
    cursor = conn.execute("""
        SELECT committee_code, COUNT(*) as count,
               AVG(sync_confidence) as avg_confidence
        FROM hearings_unified
        GROUP BY committee_code
    """)
    
    committee_stats = {}
    for row in cursor.fetchall():
        committee_stats[row['committee_code']] = {
            'hearing_count': row['count'],
            'avg_confidence': round(row['avg_confidence'], 3)
        }
    
    summary['committee_coverage'] = committee_stats
    
    conn.close()
    
    # Save summary to file
    summary_path = Path("PHASE_7B_DEMO_SUMMARY.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"📄 Demo summary saved to {summary_path}")
    
    return summary

def start_demo_server():
    """Instructions for starting the demo server"""
    
    logger.info("\n🚀 Phase 7B Enhanced UI Demo Ready!")
    logger.info("=" * 50)
    logger.info("\n📋 To start the demo:")
    logger.info("1. Start the FastAPI backend:")
    logger.info("   python -m uvicorn src.api.main_app:app --host 0.0.0.0 --port 8001 --reload")
    logger.info("\n2. Start the React frontend (in another terminal):")
    logger.info("   cd dashboard && npm start")
    logger.info("\n3. Access the enhanced UI:")
    logger.info("   - Main Dashboard: http://localhost:3000")
    logger.info("   - API Documentation: http://localhost:8001/api/docs")
    logger.info("   - System Health: http://localhost:3000 (click 'System Health' button)")
    logger.info("   - Hearing Queue: http://localhost:3000 (click 'Hearing Queue' button)")
    logger.info("\n🔍 Demo Features:")
    logger.info("   ✅ Automated hearing discovery and sync monitoring")
    logger.info("   ✅ Real-time system health dashboard")
    logger.info("   ✅ Enhanced hearing queue management")
    logger.info("   ✅ Quality metrics and performance tracking")
    logger.info("   ✅ Alert management system")
    logger.info("   ✅ Role-based user sessions")
    logger.info("\n📊 Demo Data Includes:")
    logger.info("   • 5 sample hearings from different committees")
    logger.info("   • 4 review assignments in various states")
    logger.info("   • 3 system alerts (high, medium priority)")
    logger.info("   • Quality metrics and sync status data")
    logger.info("   • Multiple user roles (admin, reviewers, quality controller)")

def main():
    """Main demo setup"""
    print("🎯 Phase 7B Enhanced UI Demo Setup")
    print("=" * 40)
    
    try:
        # Create demo database
        db_path = create_demo_database()
        
        # Test database functionality
        logger.info("\n🧪 Testing Database Functionality...")
        test_count = test_database_queries()
        logger.info(f"✅ All {test_count} database tests passed")
        
        # Generate demo summary
        summary = generate_demo_data_summary()
        logger.info(f"\n📊 Demo Summary Generated:")
        logger.info(f"   Database: {summary['database_path']}")
        logger.info(f"   Tables: {len(summary['data_summary'])} created")
        logger.info(f"   Hearings: {summary['data_summary']['hearings_unified']}")
        logger.info(f"   Review Assignments: {summary['data_summary']['review_assignments']}")
        logger.info(f"   Active Alerts: {sum(summary['active_alerts_by_severity'].values())}")
        
        # Show startup instructions
        start_demo_server()
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Demo setup failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())