#!/usr/bin/env python3
"""
Phase 1 Testing: Process 5 High-Priority ISVP Hearings
Automated execution of the manual processing framework for systematic testing
"""

import json
import time
from datetime import datetime
from pathlib import Path
from process_single_hearing import ManualProcessingFramework

class Phase1TestingFramework:
    """
    Automated execution of Phase 1 testing for 5 high-priority ISVP hearings
    """
    
    def __init__(self):
        self.framework = ManualProcessingFramework()
        self.phase1_results = {
            'phase': 'Phase 1: High-Priority ISVP Validation',
            'start_time': datetime.now().isoformat(),
            'target_hearings': 5,
            'success_criteria': 0.9,  # 90% success rate (4/5 hearings)
            'results': [],
            'summary': {}
        }
        
        # Get the 5 highest-priority ISVP hearings
        self.target_hearings = self.get_phase1_hearings()
        
    def get_phase1_hearings(self):
        """Get the 5 highest-priority ISVP-compatible hearings"""
        if not self.framework.priority_hearings.get('priority_hearings'):
            return []
        
        # Filter for ISVP-compatible hearings and sort by priority score
        isvp_hearings = [
            hearing for hearing in self.framework.priority_hearings['priority_hearings']
            if hearing.get('isvp_compatible', False)
        ]
        
        # Sort by priority score (descending) and take top 5
        isvp_hearings.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        return isvp_hearings[:5]
    
    def display_phase1_plan(self):
        """Display Phase 1 testing plan"""
        print("🎯 PHASE 1 TESTING: HIGH-PRIORITY ISVP HEARINGS")
        print("=" * 60)
        print(f"Target: {len(self.target_hearings)} hearings")
        print(f"Success Criteria: {self.phase1_results['success_criteria']:.0%} success rate")
        print(f"Expected: {int(len(self.target_hearings) * self.phase1_results['success_criteria'])} successful processes")
        
        print("\n📋 PHASE 1 HEARING LINEUP:")
        for i, hearing in enumerate(self.target_hearings, 1):
            print(f"\n{i}. {hearing['title'][:70]}...")
            print(f"   Committee: {hearing['committee_name']} ({hearing['committee_code']})")
            print(f"   Date: {hearing['date']}")
            print(f"   Readiness: {hearing['readiness_score']:.1%}")
            print(f"   Priority: {hearing['priority_score']:.1f}")
            print(f"   Audio: {hearing['audio_source']} (ISVP ✅)")
            print(f"   URL: {hearing['url']}")
    
    def process_hearing_with_monitoring(self, hearing_num, hearing):
        """Process a single hearing with detailed monitoring"""
        print(f"\n🚀 PROCESSING HEARING {hearing_num}/5")
        print("=" * 50)
        print(f"Title: {hearing['title']}")
        print(f"Committee: {hearing['committee_name']} ({hearing['committee_code']})")
        print(f"Readiness: {hearing['readiness_score']:.1%}")
        print(f"URL: {hearing['url']}")
        
        # Record start time
        start_time = datetime.now()
        
        # Process the hearing
        session = self.framework.process_single_hearing(hearing)
        
        # Record end time
        end_time = datetime.now()
        processing_duration = (end_time - start_time).total_seconds()
        
        # Analyze results
        success = session['processing_status'] == 'COMPLETED'
        
        # Record results
        result = {
            'hearing_number': hearing_num,
            'hearing_id': hearing['hearing_id'],
            'hearing_title': hearing['title'],
            'committee': hearing['committee_name'],
            'committee_code': hearing['committee_code'],
            'readiness_score': hearing['readiness_score'],
            'priority_score': hearing['priority_score'],
            'processing_start': start_time.isoformat(),
            'processing_end': end_time.isoformat(),
            'processing_duration_seconds': processing_duration,
            'success': success,
            'status': session['processing_status'],
            'session_id': session['session_id'],
            'output_files': session['output_paths'],
            'errors': session.get('errors', []),
            'warnings': session.get('warnings', [])
        }
        
        self.phase1_results['results'].append(result)
        
        # Display results
        status_emoji = "✅" if success else "❌"
        print(f"\n{status_emoji} HEARING {hearing_num} RESULTS:")
        print(f"   Status: {session['processing_status']}")
        print(f"   Duration: {processing_duration:.1f} seconds")
        print(f"   Session: {session['session_id']}")
        
        if success:
            print(f"   Audio: {session['output_paths'].get('audio_file', 'N/A')}")
            print(f"   Transcript: {session['output_paths'].get('transcript_file', 'N/A')}")
            print(f"   Metadata: {session['output_paths'].get('metadata_file', 'N/A')}")
        
        if session.get('errors'):
            print(f"   Errors: {len(session['errors'])}")
            for error in session['errors']:
                print(f"     - {error}")
        
        if session.get('warnings'):
            print(f"   Warnings: {len(session['warnings'])}")
            for warning in session['warnings']:
                print(f"     - {warning}")
        
        return result
    
    def analyze_phase1_results(self):
        """Analyze Phase 1 results and generate summary"""
        results = self.phase1_results['results']
        
        if not results:
            print("❌ No results to analyze")
            return
        
        # Calculate success metrics
        successful_hearings = sum(1 for r in results if r['success'])
        total_hearings = len(results)
        success_rate = successful_hearings / total_hearings if total_hearings > 0 else 0
        
        # Calculate processing metrics
        total_duration = sum(r['processing_duration_seconds'] for r in results)
        avg_duration = total_duration / total_hearings if total_hearings > 0 else 0
        
        # Analyze errors
        total_errors = sum(len(r['errors']) for r in results)
        total_warnings = sum(len(r['warnings']) for r in results)
        
        # Update summary
        self.phase1_results['summary'] = {
            'total_hearings': total_hearings,
            'successful_hearings': successful_hearings,
            'failed_hearings': total_hearings - successful_hearings,
            'success_rate': success_rate,
            'target_success_rate': self.phase1_results['success_criteria'],
            'phase1_passed': success_rate >= self.phase1_results['success_criteria'],
            'total_processing_time_seconds': total_duration,
            'average_processing_time_seconds': avg_duration,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'completion_time': datetime.now().isoformat()
        }
        
        # Display summary
        print("\n📊 PHASE 1 RESULTS SUMMARY")
        print("=" * 40)
        print(f"Total Hearings: {total_hearings}")
        print(f"Successful: {successful_hearings}")
        print(f"Failed: {total_hearings - successful_hearings}")
        print(f"Success Rate: {success_rate:.1%}")
        print(f"Target Rate: {self.phase1_results['success_criteria']:.1%}")
        print(f"Phase 1 Status: {'✅ PASSED' if success_rate >= self.phase1_results['success_criteria'] else '❌ FAILED'}")
        print(f"Total Processing Time: {total_duration:.1f} seconds")
        print(f"Average Processing Time: {avg_duration:.1f} seconds")
        print(f"Total Errors: {total_errors}")
        print(f"Total Warnings: {total_warnings}")
        
        # Show individual results
        print("\n📋 INDIVIDUAL HEARING RESULTS:")
        for result in results:
            status_emoji = "✅" if result['success'] else "❌"
            print(f"{status_emoji} {result['hearing_number']}. {result['hearing_title'][:50]}...")
            print(f"   Committee: {result['committee']} ({result['committee_code']})")
            print(f"   Duration: {result['processing_duration_seconds']:.1f}s")
            print(f"   Status: {result['status']}")
            if result['errors']:
                print(f"   Errors: {len(result['errors'])}")
    
    def save_phase1_results(self):
        """Save Phase 1 results to file"""
        results_file = Path("data/phase1_testing_results.json")
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.phase1_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        return results_file
    
    def run_phase1_testing(self):
        """Run complete Phase 1 testing"""
        print("🎯 STARTING PHASE 1 TESTING")
        print("=" * 40)
        
        if not self.target_hearings:
            print("❌ No ISVP hearings available for testing")
            return False
        
        # Display plan
        self.display_phase1_plan()
        
        print(f"\n🚀 BEGINNING PROCESSING OF {len(self.target_hearings)} HEARINGS")
        print("=" * 60)
        
        # Process each hearing
        for i, hearing in enumerate(self.target_hearings, 1):
            try:
                result = self.process_hearing_with_monitoring(i, hearing)
                
                # Brief pause between hearings
                if i < len(self.target_hearings):
                    print(f"\n⏳ Preparing for hearing {i+1}...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Error processing hearing {i}: {e}")
                # Record the failure
                result = {
                    'hearing_number': i,
                    'hearing_id': hearing['hearing_id'],
                    'hearing_title': hearing['title'],
                    'committee': hearing['committee_name'],
                    'committee_code': hearing['committee_code'],
                    'success': False,
                    'status': 'FAILED',
                    'errors': [str(e)]
                }
                self.phase1_results['results'].append(result)
        
        # Analyze results
        self.analyze_phase1_results()
        
        # Save results
        results_file = self.save_phase1_results()
        
        # Return success status
        return self.phase1_results['summary'].get('phase1_passed', False)


def main():
    """Main Phase 1 testing execution"""
    print("🎯 SENATE HEARING PHASE 1 TESTING FRAMEWORK")
    print("=" * 60)
    
    # Initialize testing framework
    tester = Phase1TestingFramework()
    
    # Run Phase 1 testing
    success = tester.run_phase1_testing()
    
    # Final status
    print(f"\n🎯 PHASE 1 TESTING COMPLETE")
    if success:
        print("✅ PHASE 1 PASSED - Ready for Phase 2 (Committee Diversity Testing)")
    else:
        print("❌ PHASE 1 FAILED - Review results and address issues")
    
    return success


if __name__ == "__main__":
    main()