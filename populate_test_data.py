#!/usr/bin/env python3
"""
Direct database population script for testing production environment.
Bypasses Congress API to populate test data directly.
"""

import asyncio
import asyncpg
import json
import os
from datetime import datetime, date
from typing import Dict, List, Any

# Test data
TEST_COMMITTEES = [
    {
        'committee_code': 'SCOM',
        'committee_name': 'Senate Committee on Commerce, Science, and Transportation',
        'chamber': 'Senate',
        'total_members': 28,
        'majority_party': 'Democrat',
        'minority_party': 'Republican',
        'metadata': {
            'description': 'Committee with jurisdiction over commerce, science, and transportation',
            'website': 'https://www.commerce.senate.gov',
            'isvp_compatible': True
        }
    },
    {
        'committee_code': 'SSCI',
        'committee_name': 'Senate Select Committee on Intelligence',
        'chamber': 'Senate',
        'total_members': 21,
        'majority_party': 'Democrat',
        'minority_party': 'Republican',
        'metadata': {
            'description': 'Select committee overseeing intelligence community',
            'website': 'https://www.intelligence.senate.gov',
            'isvp_compatible': True
        }
    },
    {
        'committee_code': 'SSJU',
        'committee_name': 'Senate Committee on the Judiciary',
        'chamber': 'Senate',
        'total_members': 22,
        'majority_party': 'Democrat',
        'minority_party': 'Republican',
        'metadata': {
            'description': 'Committee with jurisdiction over federal judiciary',
            'website': 'https://www.judiciary.senate.gov',
            'isvp_compatible': True
        }
    }
]

TEST_HEARINGS = [
    {
        'hearing_id': 'SCOM-2025-06-25-executive-session-12',
        'committee_code': 'SCOM',
        'title': 'Executive Session 12',
        'date': date(2025, 6, 25),
        'url': 'https://www.commerce.senate.gov/2025/6/executive-session-12',
        'status': 'discovered',
        'audio_available': True,
        'transcript_available': False,
        'metadata': {
            'duration': '44:42',
            'committee': 'Commerce, Science, and Transportation',
            'session_type': 'Executive Session',
            'description': 'Executive session to consider nominations and other business'
        }
    },
    {
        'hearing_id': 'SSCI-2025-06-20-intelligence-briefing',
        'committee_code': 'SSCI',
        'title': 'Intelligence Community Briefing',
        'date': date(2025, 6, 20),
        'url': 'https://www.intelligence.senate.gov/hearings/intelligence-community-briefing',
        'status': 'discovered',
        'audio_available': True,
        'transcript_available': False,
        'metadata': {
            'duration': '2:15:30',
            'committee': 'Intelligence',
            'session_type': 'Briefing',
            'description': 'Classified briefing on current intelligence matters'
        }
    },
    {
        'hearing_id': 'SSJU-2025-06-15-judicial-nominations',
        'committee_code': 'SSJU',
        'title': 'Judicial Nominations Hearing',
        'date': date(2025, 6, 15),
        'url': 'https://www.judiciary.senate.gov/meetings/judicial-nominations-hearing',
        'status': 'discovered',
        'audio_available': True,
        'transcript_available': False,
        'metadata': {
            'duration': '3:45:20',
            'committee': 'Judiciary',
            'session_type': 'Confirmation Hearing',
            'description': 'Hearing to consider federal judicial nominees'
        }
    }
]

async def populate_production_database():
    """Populate production database with test data"""
    
    # Production database URL
    db_url = os.getenv('DATABASE_URL', 'postgresql://app_user:qlb-10DB:Gwa_tX&@/senate_hearing_db?host=/cloudsql/senate-hearing-capture:us-central1:senate-hearing-db-development')
    
    print(f"Connecting to database...")
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Check if tables exist
        committees_exist = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'committees'
            )
        """)
        
        hearings_exist = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'hearings'
            )
        """)
        
        print(f"Committees table exists: {committees_exist}")
        print(f"Hearings table exists: {hearings_exist}")
        
        # If tables don't exist, create them
        if not committees_exist:
            print("Creating committees table...")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS committees (
                    committee_code VARCHAR(10) PRIMARY KEY,
                    committee_name VARCHAR(255) NOT NULL,
                    chamber VARCHAR(10) NOT NULL,
                    total_members INTEGER,
                    majority_party VARCHAR(20),
                    minority_party VARCHAR(20),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        if not hearings_exist:
            print("Creating hearings table...")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS hearings (
                    hearing_id VARCHAR(100) PRIMARY KEY,
                    committee_code VARCHAR(10) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    date DATE,
                    url VARCHAR(500),
                    status VARCHAR(20) DEFAULT 'discovered',
                    audio_available BOOLEAN DEFAULT FALSE,
                    transcript_available BOOLEAN DEFAULT FALSE,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (committee_code) REFERENCES committees(committee_code)
                )
            """)
        
        # Populate committees
        print(f"Populating {len(TEST_COMMITTEES)} committees...")
        for committee in TEST_COMMITTEES:
            await conn.execute("""
                INSERT INTO committees (committee_code, committee_name, chamber, total_members, majority_party, minority_party, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (committee_code) DO UPDATE SET
                    committee_name = EXCLUDED.committee_name,
                    chamber = EXCLUDED.chamber,
                    total_members = EXCLUDED.total_members,
                    majority_party = EXCLUDED.majority_party,
                    minority_party = EXCLUDED.minority_party,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """, committee['committee_code'], committee['committee_name'], committee['chamber'],
                committee['total_members'], committee['majority_party'], committee['minority_party'],
                json.dumps(committee['metadata']))
        
        # Populate hearings
        print(f"Populating {len(TEST_HEARINGS)} hearings...")
        for hearing in TEST_HEARINGS:
            await conn.execute("""
                INSERT INTO hearings (hearing_id, committee_code, title, date, url, status, audio_available, transcript_available, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (hearing_id) DO UPDATE SET
                    committee_code = EXCLUDED.committee_code,
                    title = EXCLUDED.title,
                    date = EXCLUDED.date,
                    url = EXCLUDED.url,
                    status = EXCLUDED.status,
                    audio_available = EXCLUDED.audio_available,
                    transcript_available = EXCLUDED.transcript_available,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """, hearing['hearing_id'], hearing['committee_code'], hearing['title'],
                hearing['date'], hearing['url'], hearing['status'], hearing['audio_available'],
                hearing['transcript_available'], json.dumps(hearing['metadata']))
        
        # Verify data
        committee_count = await conn.fetchval("SELECT COUNT(*) FROM committees")
        hearing_count = await conn.fetchval("SELECT COUNT(*) FROM hearings")
        
        print(f"✅ Database populated successfully!")
        print(f"   - Committees: {committee_count}")
        print(f"   - Hearings: {hearing_count}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Main execution"""
    print("=== Production Database Population ===")
    success = await populate_production_database()
    
    if success:
        print("\n🎉 Test data population completed successfully!")
        print("You can now test the production API endpoints:")
        print("- GET /api/committees")
        print("- GET /api/stats")
        print("- POST /api/hearings/discover")
    else:
        print("\n❌ Database population failed")
        
    return success

if __name__ == "__main__":
    asyncio.run(main())