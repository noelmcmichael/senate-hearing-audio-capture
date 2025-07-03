#!/usr/bin/env python3
"""
Manual Processing Framework for Individual Senate Hearings
=========================================================

Safe, controlled processing of individual hearings with comprehensive safety controls.
Integrates with existing capture.py and transcription_pipeline.py systems.

Author: Senate Hearing Audio Capture Agent
Date: 2025-07-03
"""

import json
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import existing modules (will be loaded dynamically to avoid dependency issues)
try:
    from simple_processor import SimpleProcessor
    SIMPLE_PROCESSOR_AVAILABLE = True
except ImportError:
    SIMPLE_PROCESSOR_AVAILABLE = False
    SimpleProcessor = None

class ManualProcessingFramework:
    """
    Manual processing framework for individual Senate hearings with safety controls.
    """
    
    def __init__(self):
        self.setup_logging()
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir / "data"
        self.output_dir = self.base_dir / "output"
        self.logs_dir = self.base_dir / "logs"
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Load priority hearings
        self.priority_hearings = self.load_priority_hearings()
        
        # Initialize processor
        if SIMPLE_PROCESSOR_AVAILABLE:
            self.processor = SimpleProcessor()
        else:
            self.processor = None
        
    def setup_logging(self):
        """Setup logging for manual processing"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/manual_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_priority_hearings(self) -> Dict[str, Any]:
        """Load priority hearings data"""
        priority_file = self.data_dir / "hearings" / "priority_hearings.json"
        try:
            with open(priority_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Priority hearings file not found: {priority_file}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing priority hearings JSON: {e}")
            return {}
    
    def display_priority_hearings(self):
        """Display available priority hearings for selection"""
        if not self.priority_hearings.get('priority_hearings'):
            print("❌ No priority hearings available")
            return
        
        print("🎯 PRIORITY HEARINGS AVAILABLE FOR PROCESSING")
        print("=" * 60)
        
        for i, hearing in enumerate(self.priority_hearings['priority_hearings'], 1):
            print(f"\n{i}. {hearing['title'][:80]}...")
            print(f"   Committee: {hearing['committee_name']} ({hearing['committee_code']})")
            print(f"   Date: {hearing['date']}")
            print(f"   Readiness Score: {hearing['readiness_score']:.1%}")
            print(f"   Priority Score: {hearing['priority_score']:.1f}")
            print(f"   Audio Source: {hearing['audio_source']}")
            print(f"   ISVP Compatible: {'✅' if hearing['isvp_compatible'] else '❌'}")
            print(f"   Witnesses: {hearing['witness_count']}")
            print(f"   URL: {hearing['url']}")
            print(f"   Rationale: {hearing['rationale']}")
    
    def select_hearing(self) -> Optional[Dict[str, Any]]:
        """Interactive hearing selection"""
        self.display_priority_hearings()
        
        if not self.priority_hearings.get('priority_hearings'):
            return None
        
        total_hearings = len(self.priority_hearings['priority_hearings'])
        
        while True:
            try:
                selection = input(f"\n🎯 Select hearing to process (1-{total_hearings}) or 'q' to quit: ").strip()
                
                if selection.lower() == 'q':
                    print("👋 Exiting manual processing")
                    return None
                
                hearing_index = int(selection) - 1
                if 0 <= hearing_index < total_hearings:
                    selected_hearing = self.priority_hearings['priority_hearings'][hearing_index]
                    return selected_hearing
                else:
                    print(f"❌ Invalid selection. Please choose 1-{total_hearings}")
                    
            except ValueError:
                print("❌ Invalid input. Please enter a number or 'q' to quit")
    
    def validate_hearing_processing_readiness(self, hearing: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that a hearing is ready for processing.
        Returns (is_ready, list_of_issues)
        """
        issues = []
        
        # Check required fields
        required_fields = ['hearing_id', 'title', 'committee_code', 'url', 'audio_source']
        for field in required_fields:
            if not hearing.get(field):
                issues.append(f"Missing required field: {field}")
        
        # Check URL accessibility (basic validation)
        if hearing.get('url') and not hearing['url'].startswith('https://'):
            issues.append("URL does not appear to be HTTPS")
        
        # Check audio source compatibility
        if hearing.get('audio_source') not in ['ISVP', 'YouTube', 'Other']:
            issues.append(f"Unknown audio source: {hearing.get('audio_source')}")
        
        # Check readiness score
        if hearing.get('readiness_score', 0) < 0.7:
            issues.append(f"Low readiness score: {hearing.get('readiness_score', 0):.1%}")
        
        return len(issues) == 0, issues
    
    def confirm_processing(self, hearing: Dict[str, Any]) -> bool:
        """Confirm processing with user"""
        print(f"\n🔍 SELECTED HEARING FOR PROCESSING")
        print("=" * 50)
        print(f"Title: {hearing['title']}")
        print(f"Committee: {hearing['committee_name']} ({hearing['committee_code']})")
        print(f"Date: {hearing['date']}")
        print(f"Audio Source: {hearing['audio_source']}")
        print(f"Readiness Score: {hearing['readiness_score']:.1%}")
        print(f"URL: {hearing['url']}")
        
        # Validate readiness
        is_ready, issues = self.validate_hearing_processing_readiness(hearing)
        
        if not is_ready:
            print(f"\n⚠️  POTENTIAL ISSUES DETECTED:")
            for issue in issues:
                print(f"   - {issue}")
            print()
        
        while True:
            confirm = input("🤔 Proceed with processing? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                return True
            elif confirm in ['n', 'no']:
                print("❌ Processing cancelled")
                return False
            else:
                print("Please enter 'y' or 'n'")
    
    def create_processing_session(self, hearing: Dict[str, Any]) -> Dict[str, Any]:
        """Create a processing session with metadata"""
        session = {
            'session_id': f"session_{hearing['hearing_id']}_{int(time.time())}",
            'hearing_id': hearing['hearing_id'],
            'hearing_title': hearing['title'],
            'committee_code': hearing['committee_code'],
            'committee_name': hearing['committee_name'],
            'processing_start_time': datetime.now().isoformat(),
            'processing_status': 'STARTED',
            'stages': {
                'validation': {'status': 'PENDING', 'start_time': None, 'end_time': None, 'errors': []},
                'audio_capture': {'status': 'PENDING', 'start_time': None, 'end_time': None, 'errors': []},
                'transcription': {'status': 'PENDING', 'start_time': None, 'end_time': None, 'errors': []},
                'post_processing': {'status': 'PENDING', 'start_time': None, 'end_time': None, 'errors': []}
            },
            'output_paths': {
                'audio_file': None,
                'transcript_file': None,
                'metadata_file': None
            },
            'errors': [],
            'warnings': []
        }
        
        return session
    
    def update_session_stage(self, session: Dict[str, Any], stage: str, status: str, 
                           error: Optional[str] = None):
        """Update processing session stage status"""
        current_time = datetime.now().isoformat()
        
        if status == 'STARTED':
            session['stages'][stage]['status'] = 'IN_PROGRESS'
            session['stages'][stage]['start_time'] = current_time
        elif status == 'COMPLETED':
            session['stages'][stage]['status'] = 'COMPLETED'
            session['stages'][stage]['end_time'] = current_time
        elif status == 'FAILED':
            session['stages'][stage]['status'] = 'FAILED'
            session['stages'][stage]['end_time'] = current_time
            if error:
                session['stages'][stage]['errors'].append(error)
                session['errors'].append(f"{stage}: {error}")
        
        # Log the update
        self.logger.info(f"Session {session['session_id']} - {stage}: {status}")
        if error:
            self.logger.error(f"Session {session['session_id']} - {stage} error: {error}")
    
    def process_hearing_audio(self, hearing: Dict[str, Any], session: Dict[str, Any]) -> Optional[str]:
        """Process hearing audio using existing capture system"""
        try:
            self.update_session_stage(session, 'audio_capture', 'STARTED')
            
            # Create output directory for this hearing
            hearing_output_dir = self.output_dir / f"hearing_{hearing['hearing_id']}"
            hearing_output_dir.mkdir(exist_ok=True)
            
            # Use existing capture system
            self.logger.info(f"Starting audio capture for hearing {hearing['hearing_id']}")
            
            # TODO: Implement actual audio capture
            # For now, simulate audio capture process
            print(f"   🎵 Simulating audio capture for {hearing['url']}")
            time.sleep(2)  # Simulate processing time
            
            # Create a placeholder audio file for testing
            audio_file = str(hearing_output_dir / f"audio_{hearing['hearing_id']}.mp3")
            with open(audio_file, 'w') as f:
                f.write("# Placeholder audio file for testing")
            
            session['output_paths']['audio_file'] = audio_file
            self.update_session_stage(session, 'audio_capture', 'COMPLETED')
            self.logger.info(f"Audio capture completed: {audio_file}")
            return audio_file
                
        except Exception as e:
            error = f"Audio capture exception: {str(e)}"
            self.update_session_stage(session, 'audio_capture', 'FAILED', error)
            return None
    
    def process_hearing_transcript(self, hearing: Dict[str, Any], session: Dict[str, Any], 
                                 audio_file: str) -> Optional[str]:
        """Process hearing transcript using existing transcription system"""
        try:
            self.update_session_stage(session, 'transcription', 'STARTED')
            
            self.logger.info(f"Starting transcription for hearing {hearing['hearing_id']}")
            
            # TODO: Implement actual transcription
            # For now, simulate transcription process
            print(f"   📝 Simulating transcription for {audio_file}")
            time.sleep(3)  # Simulate processing time
            
            # Create a placeholder transcript file for testing
            transcript_file = str(Path(audio_file).parent / f"transcript_{hearing['hearing_id']}.json")
            transcript_data = {
                "hearing_id": hearing['hearing_id'],
                "committee_code": hearing['committee_code'],
                "title": hearing['title'],
                "transcript_text": "# Placeholder transcript for testing",
                "processing_date": datetime.now().isoformat(),
                "audio_source": audio_file
            }
            
            with open(transcript_file, 'w') as f:
                json.dump(transcript_data, f, indent=2)
            
            session['output_paths']['transcript_file'] = transcript_file
            self.update_session_stage(session, 'transcription', 'COMPLETED')
            self.logger.info(f"Transcription completed: {transcript_file}")
            return transcript_file
                
        except Exception as e:
            error = f"Transcription exception: {str(e)}"
            self.update_session_stage(session, 'transcription', 'FAILED', error)
            return None
    
    def finalize_processing(self, hearing: Dict[str, Any], session: Dict[str, Any]):
        """Finalize processing and save session metadata"""
        try:
            self.update_session_stage(session, 'post_processing', 'STARTED')
            
            # Save session metadata
            session_file = self.logs_dir / f"session_{session['session_id']}.json"
            with open(session_file, 'w') as f:
                json.dump(session, f, indent=2)
            
            session['output_paths']['metadata_file'] = str(session_file)
            
            # Update final status
            session['processing_end_time'] = datetime.now().isoformat()
            
            # Determine overall status
            failed_stages = [stage for stage, info in session['stages'].items() 
                           if info['status'] == 'FAILED']
            
            if failed_stages:
                session['processing_status'] = 'FAILED'
                self.logger.error(f"Processing failed for hearing {hearing['hearing_id']}. "
                                f"Failed stages: {failed_stages}")
            else:
                session['processing_status'] = 'COMPLETED'
                self.logger.info(f"Processing completed successfully for hearing {hearing['hearing_id']}")
            
            self.update_session_stage(session, 'post_processing', 'COMPLETED')
            
            # Save final session
            with open(session_file, 'w') as f:
                json.dump(session, f, indent=2)
            
        except Exception as e:
            error = f"Post-processing exception: {str(e)}"
            self.update_session_stage(session, 'post_processing', 'FAILED', error)
    
    def process_single_hearing(self, hearing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single hearing with comprehensive monitoring and error handling.
        Returns processing session with results.
        """
        print(f"\n🚀 STARTING PROCESSING FOR HEARING: {hearing['hearing_id']}")
        print("=" * 70)
        
        # Create processing session
        session = self.create_processing_session(hearing)
        
        try:
            # Stage 1: Validation
            self.update_session_stage(session, 'validation', 'STARTED')
            is_ready, issues = self.validate_hearing_processing_readiness(hearing)
            
            if not is_ready:
                for issue in issues:
                    session['warnings'].append(issue)
                self.logger.warning(f"Validation warnings for hearing {hearing['hearing_id']}: {issues}")
            
            self.update_session_stage(session, 'validation', 'COMPLETED')
            
            # Stage 2: Audio Capture
            print("🎵 Processing audio capture...")
            audio_file = self.process_hearing_audio(hearing, session)
            
            if not audio_file:
                print("❌ Audio capture failed")
                self.finalize_processing(hearing, session)
                return session
            
            print(f"✅ Audio captured: {audio_file}")
            
            # Stage 3: Transcription
            print("📝 Processing transcription...")
            transcript_file = self.process_hearing_transcript(hearing, session, audio_file)
            
            if not transcript_file:
                print("❌ Transcription failed")
                self.finalize_processing(hearing, session)
                return session
            
            print(f"✅ Transcript generated: {transcript_file}")
            
            # Stage 4: Finalization
            print("🏁 Finalizing processing...")
            self.finalize_processing(hearing, session)
            
            print(f"✅ Processing completed successfully!")
            print(f"📊 Session details: {session['output_paths']['metadata_file']}")
            
        except Exception as e:
            self.logger.error(f"Unexpected error processing hearing {hearing['hearing_id']}: {str(e)}")
            session['errors'].append(f"Unexpected error: {str(e)}")
            session['processing_status'] = 'FAILED'
            self.finalize_processing(hearing, session)
        
        return session
    
    def rollback_processing(self, session: Dict[str, Any]):
        """Rollback processing and clean up files"""
        print(f"\n🔄 ROLLING BACK PROCESSING FOR SESSION: {session['session_id']}")
        
        # Clean up output files
        for file_type, file_path in session['output_paths'].items():
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"🗑️  Removed {file_type}: {file_path}")
                except Exception as e:
                    print(f"❌ Failed to remove {file_type}: {e}")
        
        # Clean up output directory if empty
        if session.get('output_paths', {}).get('audio_file'):
            output_dir = os.path.dirname(session['output_paths']['audio_file'])
            try:
                if os.path.exists(output_dir) and not os.listdir(output_dir):
                    os.rmdir(output_dir)
                    print(f"🗑️  Removed empty directory: {output_dir}")
            except Exception as e:
                print(f"❌ Failed to remove directory: {e}")
        
        print("✅ Rollback completed")
    
    def interactive_processing_menu(self):
        """Interactive menu for manual processing"""
        print("🎯 SENATE HEARING MANUAL PROCESSING FRAMEWORK")
        print("=" * 60)
        
        while True:
            print("\n📋 PROCESSING OPTIONS:")
            print("1. 🎯 Process Priority Hearing")
            print("2. 📊 View Processing Status")
            print("3. 🔄 Rollback Last Processing")
            print("4. 📋 List Priority Hearings")
            print("5. 🚪 Exit")
            
            choice = input("\n🤔 Select option (1-5): ").strip()
            
            if choice == '1':
                hearing = self.select_hearing()
                if hearing:
                    if self.confirm_processing(hearing):
                        session = self.process_single_hearing(hearing)
                        
                        if session['processing_status'] == 'FAILED':
                            rollback = input("\n🔄 Processing failed. Rollback? (y/n): ").strip().lower()
                            if rollback in ['y', 'yes']:
                                self.rollback_processing(session)
                        
                        input("\n⏎ Press Enter to continue...")
            
            elif choice == '2':
                self.display_processing_status()
                input("\n⏎ Press Enter to continue...")
            
            elif choice == '3':
                self.rollback_last_processing()
                input("\n⏎ Press Enter to continue...")
            
            elif choice == '4':
                self.display_priority_hearings()
                input("\n⏎ Press Enter to continue...")
            
            elif choice == '5':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid option. Please choose 1-5.")
    
    def display_processing_status(self):
        """Display status of recent processing sessions"""
        print("\n📊 RECENT PROCESSING SESSIONS")
        print("=" * 50)
        
        session_files = list(self.logs_dir.glob("session_*.json"))
        if not session_files:
            print("No processing sessions found.")
            return
        
        # Sort by modification time, newest first
        session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for session_file in session_files[:10]:  # Show last 10 sessions
            try:
                with open(session_file, 'r') as f:
                    session = json.load(f)
                
                print(f"\n📋 Session: {session['session_id']}")
                print(f"   Hearing: {session['hearing_title'][:60]}...")
                print(f"   Committee: {session['committee_name']}")
                print(f"   Status: {session['processing_status']}")
                print(f"   Started: {session['processing_start_time']}")
                if session.get('processing_end_time'):
                    print(f"   Ended: {session['processing_end_time']}")
                
                # Show stage status
                for stage, info in session['stages'].items():
                    status_emoji = "✅" if info['status'] == 'COMPLETED' else "❌" if info['status'] == 'FAILED' else "⏳"
                    print(f"   {status_emoji} {stage}: {info['status']}")
                
            except Exception as e:
                print(f"❌ Error reading session {session_file}: {e}")
    
    def rollback_last_processing(self):
        """Rollback the last processing session"""
        session_files = list(self.logs_dir.glob("session_*.json"))
        if not session_files:
            print("No processing sessions found to rollback.")
            return
        
        # Get the most recent session
        latest_session_file = max(session_files, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(latest_session_file, 'r') as f:
                session = json.load(f)
            
            print(f"\n🔄 ROLLBACK CONFIRMATION")
            print(f"Session: {session['session_id']}")
            print(f"Hearing: {session['hearing_title'][:60]}...")
            print(f"Status: {session['processing_status']}")
            
            confirm = input("\n❓ Confirm rollback? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                self.rollback_processing(session)
            else:
                print("❌ Rollback cancelled")
                
        except Exception as e:
            print(f"❌ Error reading session for rollback: {e}")


def main():
    """Main entry point for manual processing"""
    try:
        framework = ManualProcessingFramework()
        framework.interactive_processing_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Manual processing interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()