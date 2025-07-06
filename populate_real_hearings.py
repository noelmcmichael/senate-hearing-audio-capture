#!/usr/bin/env python3
"""
Populate Database with Real Hearings
Replace bootstrap data with discovered real hearings
"""

import json
import sqlite3
from datetime import datetime
import sys

class RealHearingPopulator:
    def __init__(self, db_path="data/hearings_unified.db"):
        self.db_path = db_path
        
    def load_discovered_hearings(self):
        """Load discovered hearings from JSON file"""
        try:
            with open("discovered_hearings.json", 'r') as f:
                hearings = json.load(f)
            print(f"📊 Loaded {len(hearings)} discovered hearings")
            return hearings
        except Exception as e:
            print(f"❌ Error loading discovered hearings: {e}")
            return []
    
    def clear_bootstrap_data(self):
        """Clear existing bootstrap data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get count of existing hearings
            cursor.execute("SELECT COUNT(*) FROM hearings_unified")
            count = cursor.fetchone()[0]
            print(f"📋 Found {count} existing hearings in database")
            
            # Clear existing data
            cursor.execute("DELETE FROM hearings_unified")
            conn.commit()
            
            print("🗑️ Cleared existing bootstrap data")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error clearing bootstrap data: {e}")
            return False
    
    def insert_real_hearings(self, hearings):
        """Insert real hearings into database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert real hearings using existing schema
            for hearing in hearings:
                committee_code = self.map_committee_code(hearing['committee'])
                hearing_date = self.estimate_hearing_date(hearing)
                
                cursor.execute("""
                    INSERT INTO hearings_unified 
                    (committee_code, hearing_title, hearing_date, hearing_type, 
                     sync_confidence, streams, external_urls, source_website, 
                     sync_status, extraction_status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    committee_code,
                    hearing['title'],
                    hearing_date,
                    'Legislative',
                    0.90,  # High confidence for real hearings
                    json.dumps({"isvp": hearing['url']}),
                    json.dumps([hearing['url']]),
                    1,  # Source from website
                    'discovered',
                    'ready_for_capture',
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            
            # Verify insertion
            cursor.execute("SELECT COUNT(*) FROM hearings_unified")
            count = cursor.fetchone()[0]
            print(f"✅ Inserted {count} real hearings into database")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error inserting real hearings: {e}")
            return False
    
    def map_committee_code(self, committee_name):
        """Map committee name to code"""
        mapping = {
            'Judiciary': 'SSJU',
            'Commerce, Science, and Transportation': 'SCOM',
            'Intelligence': 'SSCI',
            'Banking, Housing, and Urban Affairs': 'SBAN'
        }
        return mapping.get(committee_name, 'SSJU')
    
    def estimate_hearing_date(self, hearing):
        """Estimate hearing date from URL or title"""
        # Try to extract date from URL
        import re
        url = hearing['url']
        
        # Look for date patterns in URL
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            r'(\d{2})-(\d{2})-(\d{4})',  # MM-DD-YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})'  # M-D-YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    if len(match.group(1)) == 4:  # YYYY-MM-DD
                        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                    else:  # MM-DD-YYYY or M-D-YYYY
                        month = match.group(1).zfill(2)
                        day = match.group(2).zfill(2)
                        year = match.group(3)
                        return f"{year}-{month}-{day}"
                except:
                    continue
        
        # Default to recent date if no date found
        return "2025-01-15"
    
    def verify_database_state(self):
        """Verify database state after population"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all hearings
            cursor.execute("""
                SELECT id, committee_code, hearing_title, hearing_date, 
                       external_urls, sync_status, extraction_status
                FROM hearings_unified
                ORDER BY id
            """)
            
            hearings = cursor.fetchall()
            
            print("\n📊 DATABASE STATE VERIFICATION")
            print("=" * 50)
            print(f"📋 Total Hearings: {len(hearings)}")
            
            for hearing in hearings:
                hearing_id, committee, title, date, urls, sync_status, extraction_status = hearing
                print(f"\n{hearing_id}. {committee} - {title}")
                print(f"   Date: {date}")
                print(f"   URLs: {urls}")
                print(f"   Sync Status: {sync_status}")
                print(f"   Extraction Status: {extraction_status}")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error verifying database: {e}")
            return False

def main():
    print("🚀 Populating Database with Real Hearings")
    print("=" * 50)
    
    populator = RealHearingPopulator()
    
    # Load discovered hearings
    hearings = populator.load_discovered_hearings()
    if not hearings:
        print("❌ No discovered hearings to process")
        sys.exit(1)
    
    # Clear bootstrap data
    if not populator.clear_bootstrap_data():
        print("❌ Failed to clear bootstrap data")
        sys.exit(1)
    
    # Insert real hearings
    if not populator.insert_real_hearings(hearings):
        print("❌ Failed to insert real hearings")
        sys.exit(1)
    
    # Verify database state
    if not populator.verify_database_state():
        print("❌ Failed to verify database state")
        sys.exit(1)
    
    print("\n✅ Successfully populated database with real hearings!")
    print("🎯 Ready to test capture functionality on real Senate hearings")

if __name__ == "__main__":
    main()