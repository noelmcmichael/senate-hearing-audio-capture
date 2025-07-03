#!/usr/bin/env python3
"""
Enhanced Transcript Generator - Creates realistic, continuous congressional transcripts
Fixes the time gap and content quality issues
"""

import json
import random
import sqlite3
from pathlib import Path
from datetime import datetime

class EnhancedTranscriptGenerator:
    def __init__(self):
        self.db_path = Path('data/demo_enhanced_ui.db')
        
        # Enhanced content pools for more realistic transcripts
        self.chair_openings = [
            "The committee will come to order. Good morning, everyone.",
            "This hearing of the {committee} committee will now come to order.",
            "Good morning. I'd like to welcome everyone to today's hearing.",
            "The committee will come to order. Thank you all for being here today.",
            "Good morning. This hearing will examine {topic}.",
        ]
        
        self.chair_questions = [
            "Thank you for your testimony. My first question is about implementation. How do you see this moving forward?",
            "I'd like to follow up on the budget implications. Can you walk us through the financial aspects?",
            "Thank you, witness. I want to ask about the timeline. When would we see results?",
            "Following up on your testimony, what about oversight mechanisms? How would this be monitored?",
            "I appreciate your being here. Can you elaborate on the stakeholder engagement process?",
            "Thank you for that comprehensive overview. My question concerns enforcement. How would this be implemented?",
            "I'd like to ask about coordination between agencies. How would that work in practice?",
            "Thank you for your testimony. What about the regulatory framework? How does this fit with existing law?",
            "Can you help the committee understand the compliance costs for affected entities?",
            "I want to ask about international coordination. How does this align with global standards?",
        ]
        
        self.member_questions = [
            "Thank you, Mr. Chairman. Following up on that point, what about privacy concerns?",
            "I appreciate the witness being here today. My question is about small business impacts.",
            "Thank you for your testimony. I'm concerned about the implementation timeline.",
            "Following up on my colleague's question, what about rural communities?",
            "Thank you, witness. I want to ask about state-level coordination.",
            "I have concerns about the cost-benefit analysis. Can you address that?",
            "My question is about transparency. How would the public be informed?",
            "Thank you for being here. What about workforce development implications?",
            "I'm interested in the technology aspects. Can you elaborate on that?",
            "Following up on the Chairman's question, what about environmental considerations?",
        ]
        
        self.ranking_questions = [
            "Thank you, Mr. Chairman. I want to start by thanking the witnesses for their testimony.",
            "I appreciate the opportunity to question the witnesses today.",
            "Thank you for your comprehensive testimony. I have several questions.",
            "I want to follow up on some points raised by my colleagues.",
            "Thank you, witnesses. I have concerns about the approach outlined here.",
            "I appreciate your being here today. Let me ask about oversight.",
            "Thank you for your testimony. I want to ensure we're getting the full picture.",
            "I have some concerns about the timeline that's been proposed.",
            "Thank you, Mr. Chairman. I want to ask about accountability measures.",
            "I appreciate the witnesses taking time to be here with us today.",
        ]
        
        self.witness_responses = [
            "Thank you for that important question, {title}. Let me address that directly. Based on our analysis, we believe the approach we're recommending would provide both adequate oversight and the flexibility needed for effective implementation.",
            "Thank you, {title}. That's a crucial question that gets to the heart of this issue. We've conducted extensive stakeholder outreach, and the feedback has been overwhelmingly positive. Industry representatives have told us this framework strikes the right balance.",
            "I appreciate that question, {title}. The timeline we're proposing is based on lessons learned from similar initiatives. We recommend a phased approach over 18 months, starting with pilot programs in select regions before full national implementation.",
            "Thank you for raising that concern, {title}. Cost-effectiveness is absolutely critical. Our preliminary analysis suggests the benefits would outweigh the costs by a factor of three to one over a five-year period.",
            "That's an excellent question, {title}. Coordination across agencies has been a priority from day one. We've established an interagency working group with representatives from all relevant departments to ensure seamless implementation.",
            "Thank you, {title}. You raise an important point about enforcement. We're proposing a graduated response system that starts with technical assistance and education before moving to more formal enforcement measures.",
            "I appreciate that question, {title}. Transparency is fundamental to this approach. We're committed to regular public reporting, quarterly stakeholder meetings, and maintaining an open-door policy for concerns.",
            "Thank you for that question, {title}. The regulatory framework has been designed to work within existing statutory authority while providing the flexibility needed to address emerging challenges.",
            "That's a critical question, {title}. We've built in robust accountability measures, including regular third-party audits, Congressional reporting requirements, and clear performance metrics.",
            "Thank you, {title}. International coordination is essential. We're working closely with our counterparts in allied nations to ensure our approach is consistent with global best practices.",
        ]
        
        self.witness_elaborations = [
            "If I may elaborate on that point, we've seen similar approaches work effectively in other contexts.",
            "To build on that response, the data we've collected shows consistent positive outcomes.",
            "Let me provide some additional context that might be helpful to the committee.",
            "I think it's important to note that this approach has broad bipartisan support.",
            "The stakeholder feedback we've received has been quite encouraging on this point.",
            "Our research suggests this is the most cost-effective approach available.",
            "We've learned from best practices in other jurisdictions to develop this framework.",
            "The technical working group has validated this approach through extensive modeling.",
            "I want to emphasize that flexibility has been built into every aspect of this proposal.",
            "The public comment period generated over 500 responses, predominantly supportive.",
        ]
    
    def get_hearing_info(self, hearing_id):
        """Get hearing details from database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("""
            SELECT hearing_title, committee_code, hearing_type
            FROM hearings_unified 
            WHERE id = ?
        """, (hearing_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'title': result[0],
                'committee_code': result[1],
                'hearing_type': result[2]
            }
        return None
    
    def generate_continuous_transcript(self, hearing_id, min_duration_minutes=20):
        """Generate a realistic, continuous transcript with proper flow"""
        hearing_info = self.get_hearing_info(hearing_id)
        if not hearing_info:
            return None
        
        title = hearing_info['title']
        committee = hearing_info['committee_code']
        
        segments = []
        current_time = 0
        
        # Opening statement (Chair) - 1-2 minutes
        opening_text = random.choice(self.chair_openings).format(
            committee=committee, 
            topic=title.lower()
        )
        opening_text += f" Today we're examining {title.lower()}. We have distinguished witnesses with us, and I look forward to their testimony and our discussion."
        
        segments.append({
            "start": current_time,
            "end": current_time + random.randint(90, 120),
            "speaker": "CHAIR",
            "text": opening_text
        })
        current_time = segments[-1]["end"]
        
        # Generate continuous dialogue for specified duration
        min_duration_seconds = min_duration_minutes * 60
        speaker_cycle = ['WITNESS', 'CHAIR', 'WITNESS', 'MEMBER', 'WITNESS', 'RANKING', 'WITNESS']
        cycle_position = 0
        
        while current_time < min_duration_seconds:
            speaker = speaker_cycle[cycle_position % len(speaker_cycle)]
            
            if speaker == 'CHAIR':
                text = random.choice(self.chair_questions)
                duration = random.randint(25, 45)
                title_form = "Representative" if random.random() < 0.5 else "Senator"
                
            elif speaker == 'MEMBER':
                text = random.choice(self.member_questions)
                duration = random.randint(30, 50)
                title_form = "Representative" if random.random() < 0.5 else "Senator"
                
            elif speaker == 'RANKING':
                text = random.choice(self.ranking_questions)
                duration = random.randint(35, 55)
                title_form = "Representative" if random.random() < 0.5 else "Senator"
                
            else:  # WITNESS
                # Determine title based on previous speaker
                prev_speaker = segments[-1]["speaker"] if segments else "CHAIR"
                if prev_speaker in ['CHAIR', 'MEMBER', 'RANKING']:
                    title_form = "Representative" if random.random() < 0.5 else "Senator"
                else:
                    title_form = "Representative"
                
                # Main response
                response = random.choice(self.witness_responses).format(title=title_form)
                
                # Sometimes add elaboration
                if random.random() < 0.4:
                    elaboration = random.choice(self.witness_elaborations)
                    response += f" {elaboration}"
                
                text = response
                duration = random.randint(60, 120)
            
            # Add segment with minimal gap (natural speaking pause)
            start_time = current_time + random.randint(1, 3)  # Very small pause
            end_time = start_time + duration
            
            segments.append({
                "start": start_time,
                "end": end_time,
                "speaker": speaker,
                "text": text
            })
            
            current_time = end_time
            cycle_position += 1
        
        # Add closing statement
        closing_text = "Thank you to all our witnesses for their valuable testimony today. This hearing has been very informative. The committee stands adjourned."
        segments.append({
            "start": current_time + random.randint(2, 5),
            "end": current_time + random.randint(25, 35),
            "speaker": "CHAIR",
            "text": closing_text
        })
        
        return {
            "hearing_id": hearing_id,
            "title": title,
            "committee": committee,
            "processed_at": datetime.now().isoformat(),
            "confidence": round(random.uniform(0.88, 0.96), 4),
            "duration_minutes": round(segments[-1]["end"] / 60, 1),
            "segments": segments
        }
    
    def fix_transcript(self, hearing_id, backup=True):
        """Fix a specific transcript with enhanced quality"""
        transcript_dir = Path('output/demo_transcription')
        transcript_file = transcript_dir / f"hearing_{hearing_id}_transcript.json"
        
        if backup and transcript_file.exists():
            backup_dir = Path('output/transcript_backups')
            backup_dir.mkdir(exist_ok=True)
            backup_file = backup_dir / f"hearing_{hearing_id}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(transcript_file, 'r') as f:
                backup_data = json.load(f)
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            print(f"📦 Backed up to: {backup_file}")
        
        # Generate new transcript
        new_transcript = self.generate_continuous_transcript(hearing_id)
        if not new_transcript:
            print(f"❌ Could not generate transcript for hearing {hearing_id}")
            return False
        
        # Save enhanced transcript
        with open(transcript_file, 'w') as f:
            json.dump(new_transcript, f, indent=2)
        
        print(f"✅ Enhanced transcript: hearing_{hearing_id} ({len(new_transcript['segments'])} segments, {new_transcript['duration_minutes']} min)")
        return True
    
    def fix_all_transcripts(self):
        """Fix all existing transcripts"""
        transcript_dir = Path('output/demo_transcription')
        transcript_files = list(transcript_dir.glob('hearing_*_transcript.json'))
        
        print(f"🔧 Fixing {len(transcript_files)} transcripts...")
        
        fixed_count = 0
        for transcript_file in transcript_files:
            hearing_id = int(transcript_file.stem.split('_')[1])
            if self.fix_transcript(hearing_id):
                fixed_count += 1
        
        print(f"✅ Fixed {fixed_count}/{len(transcript_files)} transcripts")
        return fixed_count

def main():
    """Run the enhanced transcript generator"""
    generator = EnhancedTranscriptGenerator()
    
    print("🚀 Enhanced Transcript Generator")
    print("================================")
    
    # Test with a single hearing first
    print("\n📋 Testing with hearing ID 1...")
    if generator.fix_transcript(1):
        print("✅ Test successful")
        
        # Ask user confirmation before fixing all
        response = input("\n🤔 Fix all transcripts? (y/N): ").strip().lower()
        if response == 'y':
            generator.fix_all_transcripts()
        else:
            print("ℹ️  Run with --fix-all to update all transcripts")
    else:
        print("❌ Test failed")

if __name__ == "__main__":
    import sys
    if "--fix-all" in sys.argv:
        generator = EnhancedTranscriptGenerator()
        generator.fix_all_transcripts()
    else:
        main()