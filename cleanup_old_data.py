#!/usr/bin/env python3
"""
Clean Slate Data Purge - Remove all old audio files and generated transcripts
Prepare for professional benchmark approach
"""

import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

class DataCleanupTool:
    def __init__(self):
        self.project_root = Path('/Users/noelmcmichael/Workspace/senate_hearing_audio_capture')
        self.backup_dir = self.project_root / 'cleanup_backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def backup_important_files(self):
        """Backup important configuration and schema files before cleanup"""
        print("📦 Backing up important files...")
        
        important_files = [
            'data/demo_enhanced_ui.db',  # Database schema
            'requirements.txt',
            'README.md',
            'rules.md'
        ]
        
        for file_path in important_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                backup_path = self.backup_dir / file_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(full_path, backup_path)
                print(f"  ✅ Backed up: {file_path}")
        
        return True
    
    def clean_audio_files(self):
        """Remove all audio files (mp3, wav) and related analysis files"""
        print("🗑️  Cleaning up audio files...")
        
        output_dir = self.project_root / 'output'
        if not output_dir.exists():
            print("  ℹ️  No output directory found")
            return
        
        # Audio file extensions to remove
        audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
        
        removed_count = 0
        for file_path in output_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                print(f"  🗑️  Removing: {file_path.name}")
                file_path.unlink()
                removed_count += 1
        
        # Remove audio analysis files
        analysis_patterns = [
            'audio_quality_analysis_*.json',
            'multi_committee_test_*.json',
            'results_*.json'
        ]
        
        for pattern in analysis_patterns:
            for file_path in output_dir.glob(pattern):
                print(f"  🗑️  Removing: {file_path.name}")
                file_path.unlink()
                removed_count += 1
        
        print(f"  ✅ Removed {removed_count} audio-related files")
        return removed_count
    
    def clean_transcript_files(self):
        """Remove all generated transcript files"""
        print("🗑️  Cleaning up transcript files...")
        
        # Remove demo transcription directory
        demo_transcription = self.project_root / 'output' / 'demo_transcription'
        if demo_transcription.exists():
            file_count = len(list(demo_transcription.glob('*.json')))
            shutil.rmtree(demo_transcription)
            print(f"  ✅ Removed demo_transcription/ ({file_count} files)")
        
        # Remove transcript backups
        transcript_backups = self.project_root / 'output' / 'transcript_backups'
        if transcript_backups.exists():
            file_count = len(list(transcript_backups.glob('*.json')))
            shutil.rmtree(transcript_backups)
            print(f"  ✅ Removed transcript_backups/ ({file_count} files)")
        
        # Remove temp audio analysis
        temp_audio = self.project_root / 'temp_audio_analysis'
        if temp_audio.exists():
            shutil.rmtree(temp_audio)
            print(f"  ✅ Removed temp_audio_analysis/")
        
        return True
    
    def clean_database_demo_data(self):
        """Clean demo/test data from database, keep schema"""
        print("🗑️  Cleaning up database demo data...")
        
        db_path = self.project_root / 'data' / 'demo_enhanced_ui.db'
        if not db_path.exists():
            print("  ℹ️  No database found")
            return
        
        try:
            conn = sqlite3.connect(str(db_path))
            
            # Count existing records
            cursor = conn.execute("SELECT COUNT(*) FROM hearings_unified")
            before_count = cursor.fetchone()[0]
            
            # Clear demo/test hearings but keep schema
            conn.execute("DELETE FROM hearings_unified WHERE hearing_title LIKE '%Test%' OR hearing_title LIKE '%Demo%'")
            
            # Count remaining records
            cursor = conn.execute("SELECT COUNT(*) FROM hearings_unified")
            after_count = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            removed_count = before_count - after_count
            print(f"  ✅ Removed {removed_count} demo/test hearing records")
            print(f"  ℹ️  Kept {after_count} potentially real hearing records")
            
            return removed_count
            
        except Exception as e:
            print(f"  ❌ Database cleanup error: {e}")
            return 0
    
    def remove_fake_transcript_generators(self):
        """Remove fake transcript generation scripts"""
        print("🗑️  Removing fake transcript generators...")
        
        files_to_remove = [
            'enhanced_transcript_generator.py',
            'fix_simple_transcripts.py',
            'demo_transcript_enrichment.py'
        ]
        
        removed_count = 0
        for filename in files_to_remove:
            file_path = self.project_root / filename
            if file_path.exists():
                file_path.unlink()
                print(f"  ✅ Removed: {filename}")
                removed_count += 1
        
        return removed_count
    
    def setup_fresh_directories(self):
        """Create clean directory structure for fresh start"""
        print("📁 Setting up fresh directory structure...")
        
        fresh_dirs = [
            'output/real_audio',
            'output/real_transcripts',
            'output/benchmark_comparisons',
            'data/professional_transcripts'
        ]
        
        for dir_path in fresh_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Created: {dir_path}")
        
        return True
    
    def run_complete_cleanup(self):
        """Run complete cleanup process"""
        print("🚀 Starting Complete Data Cleanup")
        print("=" * 50)
        
        # Step 1: Backup important files
        self.backup_important_files()
        
        # Step 2: Clean audio files
        audio_removed = self.clean_audio_files()
        
        # Step 3: Clean transcript files
        self.clean_transcript_files()
        
        # Step 4: Clean database demo data
        db_removed = self.clean_database_demo_data()
        
        # Step 5: Remove fake generators
        generators_removed = self.remove_fake_transcript_generators()
        
        # Step 6: Setup fresh directories
        self.setup_fresh_directories()
        
        print("\n✅ Cleanup Complete!")
        print("=" * 30)
        print(f"Audio files removed: {audio_removed}")
        print(f"Database records removed: {db_removed}")
        print(f"Fake generators removed: {generators_removed}")
        print(f"Backup location: {self.backup_dir}")
        
        return True

def main():
    """Main cleanup function"""
    cleanup_tool = DataCleanupTool()
    
    print("⚠️  WARNING: This will remove all old audio files and generated transcripts!")
    response = input("Continue? (y/N): ").strip().lower()
    
    if response == 'y':
        cleanup_tool.run_complete_cleanup()
        print("\n🎯 Ready for professional benchmark approach!")
    else:
        print("Cleanup cancelled.")

if __name__ == "__main__":
    main()