#!/usr/bin/env python3
"""
Add more demo hearings to simulate a fuller Congressional schedule
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

# Demo hearing data based on real 2025 Congressional activity
demo_hearings = [
    # SCOM (Commerce, Science, and Transportation) - 8 additional hearings
    {
        'committee_code': 'SCOM',
        'hearing_title': 'Oversight of the Federal Aviation Administration',
        'hearing_date': '2025-01-15',
        'hearing_type': 'Oversight Hearing',
        'status': 'complete',
        'processing_stage': 'published'
    },
    {
        'committee_code': 'SCOM',
        'hearing_title': 'Broadband Infrastructure and Digital Equity Act Implementation',
        'hearing_date': '2025-02-12',
        'hearing_type': 'Legislative Hearing',
        'status': 'review',
        'processing_stage': 'transcribed'
    },
    {
        'committee_code': 'SCOM',
        'hearing_title': 'Space Commerce and Innovation: Private Sector Partnerships',
        'hearing_date': '2025-03-08',
        'hearing_type': 'Field Hearing',
        'status': 'processing',
        'processing_stage': 'captured'
    },
    {
        'committee_code': 'SCOM',
        'hearing_title': 'Transportation Safety and Infrastructure Modernization',
        'hearing_date': '2025-04-18',
        'hearing_type': 'Oversight Hearing',
        'status': 'queued',
        'processing_stage': 'analyzed'
    },
    {
        'committee_code': 'SCOM',
        'hearing_title': 'AI in Transportation: Autonomous Vehicles and Safety Standards',
        'hearing_date': '2025-05-22',
        'hearing_type': 'Legislative Hearing',
        'status': 'processing',
        'processing_stage': 'transcribed'
    },
    {
        'committee_code': 'SCOM',
        'hearing_title': 'Supply Chain Resilience and Port Infrastructure',
        'hearing_date': '2025-06-10',
        'hearing_type': 'Joint Hearing',
        'status': 'new',
        'processing_stage': 'discovered'
    },
    
    # HJUD (House Judiciary) - 8 additional hearings
    {
        'committee_code': 'HJUD',
        'hearing_title': 'Constitutional Interpretation and Supreme Court Reform',
        'hearing_date': '2025-01-25',
        'hearing_type': 'Constitutional Hearing',
        'status': 'complete',
        'processing_stage': 'published'
    },
    {
        'committee_code': 'HJUD',
        'hearing_title': 'Immigration Reform and Border Security Measures',
        'hearing_date': '2025-02-28',
        'hearing_type': 'Policy Hearing',
        'status': 'review',
        'processing_stage': 'reviewed'
    },
    {
        'committee_code': 'HJUD',
        'hearing_title': 'Antitrust Enforcement in the Digital Age',
        'hearing_date': '2025-03-15',
        'hearing_type': 'Oversight Hearing',
        'status': 'processing',
        'processing_stage': 'transcribed'
    },
    {
        'committee_code': 'HJUD',
        'hearing_title': 'Voting Rights and Election Security Legislation',
        'hearing_date': '2025-04-08',
        'hearing_type': 'Legislative Hearing',
        'status': 'queued',
        'processing_stage': 'captured'
    },
    {
        'committee_code': 'HJUD',
        'hearing_title': 'Criminal Justice Reform and Federal Sentencing Guidelines',
        'hearing_date': '2025-05-14',
        'hearing_type': 'Policy Hearing',
        'status': 'processing',
        'processing_stage': 'analyzed'
    },
    {
        'committee_code': 'HJUD',
        'hearing_title': 'Intellectual Property Rights in AI and Technology',
        'hearing_date': '2025-06-03',
        'hearing_type': 'Innovation Hearing',
        'status': 'new',
        'processing_stage': 'discovered'
    },
    
    # SBAN (Banking, Housing, and Urban Affairs) - 6 additional hearings
    {
        'committee_code': 'SBAN',
        'hearing_title': 'Cryptocurrency Regulation and Financial Stability',
        'hearing_date': '2025-02-05',
        'hearing_type': 'Regulatory Hearing',
        'status': 'complete',
        'processing_stage': 'published'
    },
    {
        'committee_code': 'SBAN',
        'hearing_title': 'Housing Affordability Crisis and Federal Housing Policy',
        'hearing_date': '2025-03-20',
        'hearing_type': 'Policy Hearing',
        'status': 'review',
        'processing_stage': 'transcribed'
    },
    {
        'committee_code': 'SBAN',
        'hearing_title': 'Community Development Financial Institutions Oversight',
        'hearing_date': '2025-04-25',
        'hearing_type': 'Oversight Hearing',
        'status': 'processing',
        'processing_stage': 'captured'
    },
    {
        'committee_code': 'SBAN',
        'hearing_title': 'Climate Risk in Financial Services and Banking',
        'hearing_date': '2025-05-30',
        'hearing_type': 'Risk Assessment Hearing',
        'status': 'queued',
        'processing_stage': 'analyzed'
    },
    
    # SSCI (Intelligence) - 4 additional hearings
    {
        'committee_code': 'SSCI',
        'hearing_title': 'Cybersecurity Threats and National Intelligence Assessment',
        'hearing_date': '2025-02-18',
        'hearing_type': 'Classified Briefing',
        'status': 'complete',
        'processing_stage': 'published'
    },
    {
        'committee_code': 'SSCI',
        'hearing_title': 'Foreign Election Interference and Disinformation Campaigns',
        'hearing_date': '2025-04-12',
        'hearing_type': 'Intelligence Hearing',
        'status': 'processing',
        'processing_stage': 'transcribed'
    },
    {
        'committee_code': 'SSCI',
        'hearing_title': 'Counterintelligence and Emerging Technology Threats',
        'hearing_date': '2025-05-16',
        'hearing_type': 'Closed Hearing',
        'status': 'queued',
        'processing_stage': 'analyzed'
    },
    
    # SSJU (Judiciary) - 4 additional hearings  
    {
        'committee_code': 'SSJU',
        'hearing_title': 'Federal Judicial Nominations and Confirmation Process',
        'hearing_date': '2025-03-05',
        'hearing_type': 'Nominations Hearing',
        'status': 'complete',
        'processing_stage': 'published'
    },
    {
        'committee_code': 'SSJU',
        'hearing_title': 'Privacy Rights in the Digital Era',
        'hearing_date': '2025-04-22',
        'hearing_type': 'Constitutional Hearing',
        'status': 'review',
        'processing_stage': 'reviewed'
    },
    {
        'committee_code': 'SSJU',
        'hearing_title': 'Corporate Accountability and White-Collar Crime Enforcement',
        'hearing_date': '2025-06-05',
        'hearing_type': 'Oversight Hearing',
        'status': 'processing',
        'processing_stage': 'captured'
    }
]

def add_demo_hearings():
    """Add demo hearings to the database"""
    
    db_path = Path('data/demo_enhanced_ui.db')
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get current max ID
    cursor.execute("SELECT MAX(id) FROM hearings_unified")
    max_id = cursor.fetchone()[0] or 0
    
    added_count = 0
    
    for i, hearing in enumerate(demo_hearings):
        hearing_id = max_id + i + 1
        
        # Create mock streams and metadata
        streams = {
            "isvp": f"http://example.com/stream{hearing_id}",
            "youtube": f"http://youtube.com/watch?v=demo{hearing_id}"
        }
        
        # Insert hearing
        cursor.execute("""
            INSERT INTO hearings_unified (
                id, committee_code, hearing_title, hearing_date, hearing_type,
                source_api, source_website, streams, sync_confidence,
                status, processing_stage, status_updated_at, created_at, updated_at,
                search_keywords, participant_list, content_summary, full_text_content, search_updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            hearing_id,
            hearing['committee_code'],
            hearing['hearing_title'],
            hearing['hearing_date'],
            hearing['hearing_type'],
            1,  # source_api
            1,  # source_website
            json.dumps(streams),
            0.85,  # sync_confidence
            hearing['status'],
            hearing['processing_stage'],
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            # Search fields
            f"{hearing['hearing_title']}, {hearing['committee_code']}, {hearing['hearing_type']}".lower(),
            "Chair, Ranking Member, Expert Witnesses",
            f"{hearing['committee_code']} committee hearing on {hearing['hearing_title']}",
            f"Full text content for {hearing['hearing_title']} hearing with congressional proceedings and testimony",
            datetime.now().isoformat()
        ))
        
        added_count += 1
        print(f"Added: {hearing['committee_code']} - {hearing['hearing_title']}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Added {added_count} demo hearings to database")
    
    # Show updated counts
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute('SELECT committee_code, COUNT(*) as count FROM hearings_unified GROUP BY committee_code ORDER BY count DESC')
    print('\nUpdated hearings per committee:')
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1]} hearings')
    
    total = cursor.execute('SELECT COUNT(*) FROM hearings_unified').fetchone()[0]
    print(f'\nTotal hearings: {total}')
    conn.close()

if __name__ == "__main__":
    add_demo_hearings()