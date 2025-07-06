#!/usr/bin/env python3
"""
Direct bootstrap script using database connection
"""
import sys
import os
sys.path.append('/Users/noelmcmichael/Workspace/senate_hearing_audio_capture')

import sqlite3
from datetime import datetime

def create_bootstrap_data():
    """Create bootstrap data directly in database"""
    
    # Connect to database
    db_path = "data/enhanced_ui.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create hearings table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hearings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            committee_code TEXT NOT NULL,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            sync_confidence REAL NOT NULL DEFAULT 1.0,
            streams TEXT NOT NULL DEFAULT '{}',
            processing_stage TEXT NOT NULL DEFAULT 'discovered',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # Clear existing data
    cursor.execute('DELETE FROM hearings')
    
    # Insert bootstrap hearings
    hearings = [
        {
            "committee_code": "SCOM",
            "title": "Bootstrap Entry for Senate Committee on Commerce, Science, and Transportation",
            "date": "2025-07-06",
            "type": "Setup",
            "sync_confidence": 1.0,
            "streams": "{}",
            "processing_stage": "discovered"
        },
        {
            "committee_code": "SSCI",
            "title": "Bootstrap Entry for Senate Select Committee on Intelligence",
            "date": "2025-07-06",
            "type": "Setup",
            "sync_confidence": 1.0,
            "streams": "{}",
            "processing_stage": "discovered"
        },
        {
            "committee_code": "SSJU",
            "title": "Bootstrap Entry for Senate Committee on the Judiciary",
            "date": "2025-07-06",
            "type": "Setup",
            "sync_confidence": 1.0,
            "streams": "{}",
            "processing_stage": "discovered"
        }
    ]
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for hearing in hearings:
        cursor.execute('''
            INSERT INTO hearings (committee_code, title, date, type, sync_confidence, streams, processing_stage, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            hearing["committee_code"],
            hearing["title"],
            hearing["date"],
            hearing["type"],
            hearing["sync_confidence"],
            hearing["streams"],
            hearing["processing_stage"],
            now,
            now
        ))
    
    conn.commit()
    conn.close()
    
    print(f"Bootstrap data created successfully at {db_path}")
    print(f"Created {len(hearings)} hearings")

if __name__ == "__main__":
    create_bootstrap_data()