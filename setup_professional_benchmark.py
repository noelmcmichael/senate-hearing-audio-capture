#!/usr/bin/env python3
"""
Professional Benchmark Setup for Senate Judiciary Hearing
"Deregulation and Competition: Reducing Regulatory Burdens to Unlock Innovation and Spur New Entry"
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

class ProfessionalBenchmarkSetup:
    def __init__(self):
        self.project_root = Path('/Users/noelmcmichael/Workspace/senate_hearing_audio_capture')
        self.hearing_info = {
            'committee': 'SSJU',
            'committee_name': 'Senate Judiciary Committee',
            'title': 'Deregulation and Competition: Reducing Regulatory Burdens to Unlock Innovation and Spur New Entry',
            'url': 'https://www.judiciary.senate.gov/committee-activity/hearings/deregulation-and-competition-reducing-regulatory-burdens-to-unlock-innovation-and-spur-new-entry',
            'date': '2024-12-05',  # Will need to get actual date
            'type': 'Committee Hearing'
        }
        
    def create_benchmark_hearing_record(self):
        """Create a clean database record for the benchmark hearing"""
        print("🗄️  Creating benchmark hearing record...")
        
        db_path = self.project_root / 'data' / 'demo_enhanced_ui.db'
        
        try:
            conn = sqlite3.connect(str(db_path))
            
            # Insert the benchmark hearing
            conn.execute("""
                INSERT INTO hearings_unified (
                    committee_code, hearing_title, hearing_date, hearing_type,
                    status, processing_stage, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.hearing_info['committee'],
                self.hearing_info['title'],
                self.hearing_info['date'],
                self.hearing_info['type'],
                'new',  # Use valid status
                'discovered',  # Use valid stage
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            # Get the hearing ID
            cursor = conn.execute("SELECT last_insert_rowid()")
            hearing_id = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            print(f"  ✅ Created benchmark hearing record (ID: {hearing_id})")
            return hearing_id
            
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            return None
    
    def create_benchmark_metadata(self, hearing_id):
        """Create metadata file for the benchmark hearing"""
        print("📋 Creating benchmark metadata...")
        
        metadata = {
            'hearing_id': hearing_id,
            'committee': self.hearing_info['committee'],
            'committee_name': self.hearing_info['committee_name'],
            'title': self.hearing_info['title'],
            'date': self.hearing_info['date'],
            'url': self.hearing_info['url'],
            'type': self.hearing_info['type'],
            'benchmark_approach': {
                'professional_transcript': 'politicopro PDF',
                'audio_source': 'TBD - Senate website or YouTube',
                'comparison_metrics': [
                    'word_accuracy',
                    'speaker_identification',
                    'timing_accuracy',
                    'content_completeness'
                ]
            },
            'directories': {
                'audio': f'output/real_audio/hearing_{hearing_id}/',
                'transcripts': f'output/real_transcripts/hearing_{hearing_id}/',
                'benchmark': f'output/benchmark_comparisons/hearing_{hearing_id}/',
                'professional': f'data/professional_transcripts/hearing_{hearing_id}/'
            },
            'created_at': datetime.now().isoformat()
        }
        
        # Save metadata
        metadata_file = self.project_root / f'data/professional_transcripts/hearing_{hearing_id}_metadata.json'
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"  ✅ Created metadata file: {metadata_file}")
        return metadata
    
    def create_directory_structure(self, hearing_id):
        """Create dedicated directory structure for the benchmark hearing"""
        print("📁 Creating benchmark directory structure...")
        
        directories = [
            f'output/real_audio/hearing_{hearing_id}',
            f'output/real_transcripts/hearing_{hearing_id}',
            f'output/benchmark_comparisons/hearing_{hearing_id}',
            f'data/professional_transcripts/hearing_{hearing_id}'
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Created: {directory}")
        
        return directories
    
    def create_benchmark_tools(self):
        """Create tools for benchmark comparison"""
        print("🔧 Creating benchmark comparison tools...")
        
        # Create transcript comparison tool
        comparison_tool = '''#!/usr/bin/env python3
"""
Transcript Comparison Tool - Compare Whisper output against professional transcript
"""

import json
import difflib
from pathlib import Path

class TranscriptComparator:
    def __init__(self, hearing_id):
        self.hearing_id = hearing_id
        self.project_root = Path(__file__).parent
        
    def load_professional_transcript(self):
        """Load the professional transcript (from politicopro PDF)"""
        # Will be implemented when PDF is provided
        pass
        
    def load_whisper_transcript(self):
        """Load the Whisper-generated transcript"""
        # Will be implemented when audio is processed
        pass
        
    def compare_transcripts(self):
        """Compare transcripts and generate accuracy metrics"""
        # Will be implemented for detailed comparison
        pass
        
    def generate_comparison_report(self):
        """Generate detailed comparison report"""
        # Will be implemented for analysis
        pass

if __name__ == "__main__":
    # Will be used for actual comparison
    pass
'''
        
        tool_file = self.project_root / 'benchmark_transcript_comparison.py'
        with open(tool_file, 'w') as f:
            f.write(comparison_tool)
        
        print(f"  ✅ Created: benchmark_transcript_comparison.py")
        
        return True
    
    def setup_benchmark_framework(self):
        """Set up complete benchmark framework"""
        print("🎯 Setting up Professional Benchmark Framework")
        print("=" * 60)
        print(f"Target Hearing: {self.hearing_info['title']}")
        print(f"Committee: {self.hearing_info['committee_name']}")
        print(f"URL: {self.hearing_info['url']}")
        print()
        
        # Step 1: Create database record
        hearing_id = self.create_benchmark_hearing_record()
        if not hearing_id:
            print("❌ Failed to create hearing record")
            return False
        
        # Step 2: Create metadata
        metadata = self.create_benchmark_metadata(hearing_id)
        
        # Step 3: Create directories
        directories = self.create_directory_structure(hearing_id)
        
        # Step 4: Create tools
        self.create_benchmark_tools()
        
        print("\n✅ Professional Benchmark Framework Ready!")
        print("=" * 50)
        print(f"📊 Benchmark Hearing ID: {hearing_id}")
        print(f"📋 Committee: {self.hearing_info['committee']} ({self.hearing_info['committee_name']})")
        print(f"📄 Title: {self.hearing_info['title']}")
        print(f"📁 Directories created: {len(directories)}")
        print(f"🔧 Tools created: benchmark_transcript_comparison.py")
        print()
        print("🎯 READY FOR PHASE 2: Professional Transcript Import")
        print("   Please provide the politicopro PDF transcript")
        
        return {
            'hearing_id': hearing_id,
            'metadata': metadata,
            'directories': directories,
            'status': 'ready_for_professional_transcript'
        }

def main():
    """Main setup function"""
    setup = ProfessionalBenchmarkSetup()
    result = setup.setup_benchmark_framework()
    
    if result:
        print(f"\n📋 Next Steps:")
        print(f"1. Provide politicopro PDF transcript")
        print(f"2. Capture audio from Senate website")
        print(f"3. Process with Whisper transcription")
        print(f"4. Compare and measure accuracy")
        
        return result['hearing_id']
    else:
        print("❌ Setup failed")
        return None

if __name__ == "__main__":
    main()