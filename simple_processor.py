#!/usr/bin/env python3
"""
Simple Background Processing Worker for Demo
"""

import time
import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/processor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SimpleProcessor:
    def __init__(self):
        self.db_path = Path('data/demo_enhanced_ui.db')
        self.running = True
        self.processing_times = {
            'discovered': 5,
            'analyzed': 15, 
            'captured': 30,
            'transcribed': 10,
            'reviewed': 5
        }
    
    def get_db_connection(self):
        return sqlite3.connect(str(self.db_path))
    
    def get_hearings_for_processing(self):
        conn = self.get_db_connection()
        cursor = conn.execute("""
            SELECT id, hearing_title, committee_code, status, processing_stage
            FROM hearings_unified 
            WHERE status IN ('queued', 'processing', 'new', 'review') 
            AND processing_stage IN ('discovered', 'analyzed', 'captured', 'transcribed', 'reviewed')
            ORDER BY created_at ASC
            LIMIT 3
        """)
        
        hearings = []
        for row in cursor.fetchall():
            hearings.append({
                'id': row[0],
                'title': row[1][:40] + '...' if len(row[1]) > 40 else row[1],
                'committee': row[2],
                'status': row[3],
                'stage': row[4]
            })
        
        conn.close()
        return hearings
    
    def advance_hearing(self, hearing):
        stage_map = {
            'discovered': ('analyzed', 'processing'),
            'analyzed': ('captured', 'processing'),
            'captured': ('transcribed', 'processing'),
            'transcribed': ('reviewed', 'review'),
            'reviewed': ('published', 'complete')
        }
        
        current = hearing['stage']
        if current not in stage_map:
            return False
        
        next_stage, next_status = stage_map[current]
        processing_time = self.processing_times.get(current, 10)
        
        logger.info(f"Processing {hearing['title']} ({current} → {next_stage})")
        
        # Simulate processing
        for i in range(processing_time):
            if not self.running:
                return False
            time.sleep(1)
            if i % 5 == 0:
                progress = int((i / processing_time) * 100)
                logger.info(f"  Progress: {progress}%")
        
        # Update database
        conn = self.get_db_connection()
        conn.execute("""
            UPDATE hearings_unified 
            SET processing_stage = ?, status = ?, status_updated_at = ?
            WHERE id = ?
        """, (next_stage, next_status, datetime.now().isoformat(), hearing['id']))
        conn.commit()
        conn.close()
        
        logger.info(f"✅ {hearing['title']} → {next_stage}")
        
        # Create mock transcript for transcribed stage
        if next_stage == 'transcribed':
            self.create_mock_transcript(hearing)
        
        return True
    
    def create_mock_transcript(self, hearing):
        output_dir = Path('output/demo_transcription')
        output_dir.mkdir(exist_ok=True)
        
        transcript_file = output_dir / f"hearing_{hearing['id']}_transcript.json"
        
        # Check if quality transcript already exists
        if transcript_file.exists():
            try:
                with open(transcript_file) as f:
                    existing_data = json.load(f)
                existing_segments = len(existing_data.get('segments', []))
                
                # If it's a quality transcript (>10 segments), don't overwrite
                if existing_segments > 10:
                    logger.info(f"📄 Quality transcript exists: {transcript_file.name} ({existing_segments} segments) - skipping")
                    return
                else:
                    logger.info(f"📄 Replacing simple transcript: {transcript_file.name} ({existing_segments} segments)")
            except:
                logger.info(f"📄 Error reading existing transcript, creating new one")
        
        mock_transcript = {
            "hearing_id": hearing['id'],
            "title": hearing['title'],
            "committee": hearing['committee'],
            "processed_at": datetime.now().isoformat(),
            "confidence": 0.85,
            "segments": [
                {"start": 0, "end": 30, "speaker": "CHAIR", "text": f"The committee will come to order for {hearing['title']}..."},
                {"start": 30, "end": 90, "speaker": "WITNESS", "text": "Thank you for the opportunity to testify..."},
                {"start": 90, "end": 120, "speaker": "CHAIR", "text": "Thank you. We'll now proceed with questions..."}
            ]
        }
        
        with open(transcript_file, 'w') as f:
            json.dump(mock_transcript, f, indent=2)
        
        logger.info(f"📄 Created transcript: {transcript_file.name}")
    
    def run(self):
        logger.info("🚀 Simple processor started")
        cycle = 0
        
        while self.running:
            try:
                cycle += 1
                logger.info(f"\n--- Cycle {cycle} ---")
                
                hearings = self.get_hearings_for_processing()
                
                if not hearings:
                    logger.info("No hearings to process")
                    time.sleep(10)
                    continue
                
                logger.info(f"Processing {len(hearings)} hearings")
                
                for hearing in hearings:
                    if not self.running:
                        break
                    
                    logger.info(f"📊 {hearing['title']} [{hearing['status']}/{hearing['stage']}]")
                    self.advance_hearing(hearing)
                    time.sleep(2)
                
                logger.info("⏳ Waiting 15 seconds...")
                time.sleep(15)
                
            except KeyboardInterrupt:
                logger.info("Interrupted")
                self.running = False
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(5)
        
        logger.info("🛑 Processor stopped")

if __name__ == "__main__":
    processor = SimpleProcessor()
    processor.run()