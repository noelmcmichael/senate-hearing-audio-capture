#!/usr/bin/env python3
"""
Fix data quality issues identified in Phase 2 QA.
Creates realistic hearing data with proper status progression and quality transcripts.
"""

import sqlite3
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

def update_database_schema():
    """Update database with proper status definitions and realistic data"""
    
    db_path = "data/demo_enhanced_ui.db"
    conn = sqlite3.connect(db_path)
    
    # Add new columns if they don't exist
    try:
        conn.execute("ALTER TABLE hearings_unified ADD COLUMN status TEXT DEFAULT 'in_progress'")
        conn.execute("ALTER TABLE hearings_unified ADD COLUMN processing_stage TEXT DEFAULT 'discovered'")
        conn.execute("ALTER TABLE hearings_unified ADD COLUMN status_updated_at TEXT")
        conn.execute("ALTER TABLE hearings_unified ADD COLUMN assigned_reviewer TEXT")
        conn.execute("ALTER TABLE hearings_unified ADD COLUMN reviewer_notes TEXT")
    except sqlite3.OperationalError:
        # Columns already exist
        pass
    
    # Define realistic hearing progression stages
    # Status must be: 'new', 'queued', 'processing', 'review', 'complete', 'error'
    # Processing stage must be: 'discovered', 'analyzed', 'captured', 'transcribed', 'reviewed', 'published'
    stages = [
        ('discovered', 'new'),
        ('analyzed', 'queued'), 
        ('captured', 'processing'),
        ('transcribed', 'review'),
        ('reviewed', 'review'),
        ('published', 'complete')
    ]
    
    # Update hearings with realistic status distribution
    cursor = conn.execute("SELECT id, hearing_title, committee_code FROM hearings_unified")
    hearings = cursor.fetchall()
    
    # Create realistic distribution:
    # 20% published (complete)
    # 30% transcribed/reviewed (review) 
    # 30% captured (processing)
    # 20% early stages (new/queued)
    
    for i, hearing in enumerate(hearings):
        hearing_id, title, committee = hearing
        
        # Assign stages based on distribution
        if i < len(hearings) * 0.2:  # 20% published
            stage, status = 'published', 'complete'
            reviewer = random.choice(['alice', 'bob', 'carol'])
            notes = 'Review complete. High quality transcript.'
        elif i < len(hearings) * 0.5:  # 30% needs review
            stage, status = random.choice([('transcribed', 'review'), ('reviewed', 'review')])
            reviewer = random.choice(['alice', 'bob', 'carol']) if stage == 'reviewed' else None
            notes = 'Speaker identification in progress.' if stage == 'reviewed' else None
        elif i < len(hearings) * 0.8:  # 30% in progress
            stage, status = 'captured', 'processing'
            reviewer = None
            notes = None
        else:  # 20% early stages
            stage, status = random.choice([('discovered', 'new'), ('analyzed', 'queued')])
            reviewer = None
            notes = None
        
        # Update with realistic timestamp
        status_updated = (datetime.now() - timedelta(days=random.randint(0, 14))).isoformat()
        
        conn.execute("""
            UPDATE hearings_unified 
            SET status = ?, processing_stage = ?, status_updated_at = ?, 
                assigned_reviewer = ?, reviewer_notes = ?
            WHERE id = ?
        """, (status, stage, status_updated, reviewer, notes, hearing_id))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated {len(hearings)} hearings with realistic status progression")
    return len(hearings)

def create_quality_transcripts():
    """Create realistic transcript samples with proper content and speaker identification"""
    
    # Templates for realistic hearing content
    opening_statements = [
        "The committee will come to order. This hearing will examine {topic}.",
        "Good morning. Today we're here to discuss {topic}.",
        "The hearing is called to order. We'll focus on {topic} today.",
        "Thank you all for being here. Our topic is {topic}."
    ]
    
    questions = [
        "Thank you for your testimony. My question concerns {aspect}.",
        "I appreciate your being here today. Can you elaborate on {aspect}?",
        "Thank you, {speaker}. I'd like to ask about {aspect}.",
        "Following up on that point, what about {aspect}?"
    ]
    
    responses = [
        "Thank you for that question, {title}. The answer is {response}.",
        "Senator, that's an important point. {response}",
        "Thank you, {title}. I believe {response}",
        "That's a crucial question. {response}"
    ]
    
    topics = [
        "artificial intelligence oversight and regulation",
        "cybersecurity threats to critical infrastructure", 
        "banking regulations and consumer protection",
        "judicial nominations and court administration",
        "intelligence community modernization efforts"
    ]
    
    aspects = [
        "implementation timeline",
        "budget implications", 
        "privacy concerns",
        "enforcement mechanisms",
        "stakeholder engagement"
    ]
    
    response_content = [
        "we are taking a comprehensive approach to address these challenges",
        "the current framework provides adequate protection while allowing innovation",
        "we recommend a phased implementation over the next 18 months",
        "coordination across agencies remains our top priority",
        "stakeholder feedback has been overwhelmingly positive"
    ]
    
    # Get hearings that should have transcripts (transcribed, reviewed, published)
    db_path = "data/demo_enhanced_ui.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("""
        SELECT id, hearing_title, committee_code, processing_stage 
        FROM hearings_unified 
        WHERE processing_stage IN ('transcribed', 'reviewed', 'published')
    """)
    
    hearings_with_transcripts = cursor.fetchall()
    conn.close()
    
    transcript_dir = Path("output/demo_transcription")
    transcript_dir.mkdir(parents=True, exist_ok=True)
    
    for hearing_id, title, committee, stage in hearings_with_transcripts:
        
        # Create realistic transcript content
        topic = random.choice(topics)
        segments = []
        current_time = 0
        
        # Opening statement by Chair
        opening = random.choice(opening_statements).format(topic=topic)
        segments.append({
            "start": current_time,
            "end": current_time + 45,
            "speaker": "CHAIR",
            "text": opening
        })
        current_time += 60
        
        # Generate 15-25 segments of Q&A
        num_segments = random.randint(15, 25)
        
        for i in range(num_segments):
            if i % 3 == 0:  # Every 3rd segment is a question
                speaker = random.choice(["RANKING", "MEMBER", "CHAIR"])
                aspect = random.choice(aspects)
                question_text = random.choice(questions).format(
                    aspect=aspect,
                    speaker="witness"
                )
                duration = random.randint(20, 45)
            else:  # Answer from witness
                speaker = "WITNESS"
                response_text = random.choice(responses).format(
                    title=random.choice(["Senator", "Representative", "Chair"]),
                    response=random.choice(response_content)
                )
                question_text = response_text
                duration = random.randint(30, 90)
            
            segments.append({
                "start": current_time,
                "end": current_time + duration,
                "speaker": speaker if stage in ['reviewed', 'published'] else "UNKNOWN",
                "text": question_text
            })
            current_time += duration + random.randint(5, 15)
        
        # Closing statement
        segments.append({
            "start": current_time,
            "end": current_time + 30,
            "speaker": "CHAIR" if stage in ['reviewed', 'published'] else "UNKNOWN",
            "text": "Thank you to all witnesses. The hearing is adjourned."
        })
        
        # Create transcript file
        transcript = {
            "hearing_id": hearing_id,
            "title": title,
            "committee": committee,
            "processed_at": datetime.now().isoformat(),
            "confidence": random.uniform(0.82, 0.95),
            "segments": segments
        }
        
        # Add speaker assignment timestamp if reviewed
        if stage in ['reviewed', 'published']:
            transcript["updated_at"] = (datetime.now() - timedelta(days=random.randint(1, 7))).isoformat()
        
        # Save transcript file
        file_path = transcript_dir / f"hearing_{hearing_id}_transcript.json"
        with open(file_path, 'w') as f:
            json.dump(transcript, f, indent=2)
    
    print(f"✅ Created {len(hearings_with_transcripts)} quality transcript files")
    return len(hearings_with_transcripts)

def verify_fix():
    """Verify the data quality fixes"""
    
    # Check database status distribution
    db_path = "data/demo_enhanced_ui.db"
    conn = sqlite3.connect(db_path)
    
    cursor = conn.execute("SELECT status, COUNT(*) FROM hearings_unified GROUP BY status")
    status_dist = dict(cursor.fetchall())
    
    cursor = conn.execute("SELECT processing_stage, COUNT(*) FROM hearings_unified GROUP BY processing_stage")
    stage_dist = dict(cursor.fetchall())
    
    conn.close()
    
    print("\n📊 Status Distribution:")
    for status, count in status_dist.items():
        print(f"  {status}: {count} hearings")
    
    print("\n📈 Processing Stage Distribution:")
    for stage, count in stage_dist.items():
        print(f"  {stage}: {count} hearings")
    
    # Check transcript files
    transcript_dir = Path("output/demo_transcription")
    transcript_files = list(transcript_dir.glob("hearing_*_transcript.json"))
    
    print(f"\n📄 Transcript Files: {len(transcript_files)} available")
    
    # Sample one transcript to verify quality
    if transcript_files:
        sample_file = random.choice(transcript_files)
        with open(sample_file, 'r') as f:
            sample = json.load(f)
        
        print(f"\n🔍 Sample Transcript ({sample_file.name}):")
        print(f"  Title: {sample['title']}")
        print(f"  Segments: {len(sample['segments'])}")
        print(f"  Sample text: {sample['segments'][0]['text'][:80]}...")

if __name__ == "__main__":
    print("🔧 Starting Data Quality Fix...")
    
    # Step 1: Update database schema and status progression
    hearings_updated = update_database_schema()
    
    # Step 2: Create quality transcript samples
    transcripts_created = create_quality_transcripts()
    
    # Step 3: Verify fixes
    verify_fix()
    
    print(f"\n✅ Data Quality Fix Complete!")
    print(f"   📊 {hearings_updated} hearings updated with realistic status progression")
    print(f"   📄 {transcripts_created} quality transcripts created")
    print(f"   🎯 Ready for user testing with meaningful data")