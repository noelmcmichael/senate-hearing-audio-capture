#!/usr/bin/env python3
"""
Background Processing Worker for Senate Hearing Pipeline

This worker simulates the complete processing pipeline:
discovered → analyzed → captured → transcribed → reviewed → published

For demonstration purposes, this uses simulated processing with delays.
In production, this would integrate with actual audio capture and Whisper transcription.
"""

import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Direct import from database_enhanced
import sqlite3
import os

def get_demo_db():
    """Get demo database connection"""
    db_path = Path(__file__).parent / 'data' / 'demo_enhanced_ui.db'
    return sqlite3.connect(str(db_path))

# Use direct database connection instead of the complex import

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/background_processor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class HearingProcessor:
    """Background processor for hearing pipeline stages"""
    
    def __init__(self):
        self.db_connection = get_demo_db()
        self.running = True
        self.processing_times = {
            'discovered': 5,    # 5 seconds to analyze
            'analyzed': 15,     # 15 seconds to capture (simulated)
            'captured': 30,     # 30 seconds to transcribe (simulated)
            'transcribed': 10,  # 10 seconds for review prep
            'reviewed': 5       # 5 seconds to publish
        }
    
    def get_hearings_for_processing(self) -> List[Dict]:
        """Get hearings ready for next processing stage"""
        cursor = self.db_connection.execute("""
            SELECT id, hearing_title, committee_code, status, processing_stage, 
                   status_updated_at, created_at
            FROM hearings_unified 
            WHERE status IN ('queued', 'processing') 
            AND processing_stage IN ('discovered', 'analyzed', 'captured', 'transcribed', 'reviewed')
            ORDER BY created_at ASC
            LIMIT 5
        """)
        
        hearings = []
        for row in cursor.fetchall():
            hearings.append({
                'id': row[0],
                'hearing_title': row[1],
                'committee_code': row[2],
                'status': row[3],
                'processing_stage': row[4],
                'status_updated_at': row[5],
                'created_at': row[6]
            })
        
        return hearings
    
    def advance_hearing_stage(self, hearing: Dict) -> bool:
        """Advance a hearing to the next processing stage"""
        current_stage = hearing['processing_stage']
        hearing_id = hearing['id']
        
        # Define stage progression
        stage_progression = {
            'discovered': ('analyzed', 'processing'),
            'analyzed': ('captured', 'processing'), 
            'captured': ('transcribed', 'processing'),
            'transcribed': ('reviewed', 'review'),
            'reviewed': ('published', 'complete')
        }
        
        if current_stage not in stage_progression:
            logger.warning(f"Unknown stage {current_stage} for hearing {hearing_id}")
            return False
        
        next_stage, next_status = stage_progression[current_stage]
        processing_time = self.processing_times.get(current_stage, 10)
        
        logger.info(f"Processing hearing {hearing_id}: {current_stage} → {next_stage} (ETA: {processing_time}s)")
        
        # Simulate processing time
        for i in range(processing_time):
            if not self.running:
                return False
            time.sleep(1)
            if i % 5 == 0:  # Progress update every 5 seconds
                progress = int((i / processing_time) * 100)
                logger.info(f"  Progress: {progress}% - {hearing['hearing_title'][:50]}...")
        
        # Update database
        try:
            self.db_connection.execute("""
                UPDATE hearings_unified 
                SET processing_stage = ?, status = ?, status_updated_at = ?
                WHERE id = ?
            """, (next_stage, next_status, datetime.now().isoformat(), hearing_id))
            
            self.db_connection.commit()
            
            logger.info(f"✅ Completed: {hearing['hearing_title'][:50]}... → {next_stage}")
            
            # Create mock transcript for transcribed stage
            if next_stage == 'transcribed':
                self.create_mock_transcript(hearing)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update hearing {hearing_id}: {str(e)}")
            return False
    
    def create_mock_transcript(self, hearing: Dict):
        """Create a mock transcript file for demonstration"""
        try:
            output_dir = Path('output/demo_transcription')
            output_dir.mkdir(exist_ok=True)
            
            transcript_file = output_dir / f"hearing_{hearing['id']}_transcript.json"
            
            mock_transcript = {
                "hearing_id": hearing['id'],
                "hearing_title": hearing['hearing_title'],
                "committee_code": hearing['committee_code'],
                "transcription_date": datetime.now().isoformat(),
                "confidence_score": 0.85,
                "segments": [
                    {
                        "start_time": 0.0,
                        "end_time": 30.0,
                        "speaker": "CHAIRPERSON",
                        "text": f"The committee will come to order. Today we are here to discuss {hearing['hearing_title'][:50]}..."
                    },
                    {
                        "start_time": 30.0,
                        "end_time": 90.0,
                        "speaker": "WITNESS_1",
                        "text": "Thank you, Chair. I am pleased to appear before the committee today to discuss this important matter..."
                    },
                    {
                        "start_time": 90.0,
                        "end_time": 120.0,
                        "speaker": "CHAIRPERSON", 
                        "text": "Thank you for your testimony. We'll now proceed with questions from committee members..."
                    }
                ],
                "summary": f"Mock transcript for {hearing['hearing_title']} - Generated by background processor for demonstration",
                "keywords": ["oversight", "committee", "hearing", "testimony"],
                "total_duration": 120.0
            }
            
            with open(transcript_file, 'w') as f:
                json.dump(mock_transcript, f, indent=2)
            
            logger.info(f"📄 Created mock transcript: {transcript_file}")
            
        except Exception as e:
            logger.error(f"Failed to create mock transcript for hearing {hearing['id']}: {str(e)}")
    
    def run(self):
        """Main processing loop"""
        logger.info("🚀 Background processor started")
        logger.info("Monitoring hearings for processing...")
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                logger.info(f"\n--- Processing Cycle {cycle_count} ---")
                
                # Get hearings ready for processing
                hearings = self.get_hearings_for_processing()
                
                if not hearings:
                    logger.info("No hearings ready for processing")
                    time.sleep(10)  # Wait 10 seconds before next check
                    continue
                
                logger.info(f"Found {len(hearings)} hearings for processing")
                
                # Process each hearing
                for hearing in hearings:
                    if not self.running:
                        break
                    
                    logger.info(f"\n📊 Processing: {hearing['hearing_title'][:50]}...")
                    logger.info(f"   Committee: {hearing['committee_code']}")
                    logger.info(f"   Current: {hearing['status']} / {hearing['processing_stage']}")
                    
                    success = self.advance_hearing_stage(hearing)
                    
                    if not success:
                        logger.error(f"❌ Failed to process hearing {hearing['id']}")
                        continue
                    
                    # Small delay between hearings
                    time.sleep(2)
                
                # Longer delay between processing cycles
                logger.info(f"\n⏳ Cycle {cycle_count} complete. Waiting 15 seconds...")
                time.sleep(15)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                self.running = False
            except Exception as e:
                logger.error(f"Error in processing cycle: {str(e)}")
                time.sleep(5)
        
        logger.info("🛑 Background processor stopped")

def main():
    """Main entry point"""
    processor = HearingProcessor()
    
    try:
        processor.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        processor.running = False

if __name__ == "__main__":
    main()