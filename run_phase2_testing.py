#!/usr/bin/env python3
"""
Phase 2 Testing: Committee Diversity with Compatible Formats
Focus on different committees while maintaining format compatibility with Phase 1 success
"""

import json
import time
from datetime import datetime
from pathlib import Path
from process_single_hearing import ManualProcessingFramework

class Phase2TestingFramework:
    """
    Phase 2 testing for committee diversity with compatible formats
    """
    
    def __init__(self):
        self.framework = ManualProcessingFramework()
        self.phase2_results = {
            'phase': 'Phase 2: Committee Diversity Validation',
            'start_time': datetime.now().isoformat(),
            'target_hearings': 5,
            'success_criteria': 0.8,  # 80% success rate (4/5 hearings)
            'format_compatibility': 'ISVP-compatible hearings only',
            'results': [],
            'summary': {}
        }
        
        # Get Phase 1 processed committees to avoid duplication
        self.phase1_committees = self.get_phase1_committees()
        
        # Get Phase 2 hearings (different committees, compatible formats)
        self.target_hearings = self.get_phase2_hearings()
        
    def get_phase1_committees(self):
        """Get committees that were processed in Phase 1"""
        try:
            with open('data/phase1_testing_results.json', 'r') as f:
                phase1_data = json.load(f)
            
            phase1_committees = set()
            for result in phase1_data.get('results', []):
                phase1_committees.add(result.get('committee_code'))
            
            return phase1_committees
        except FileNotFoundError:
            return set()
    
    def get_phase2_hearings(self):
        """Get 5 hearings from different committees with compatible formats"""
        if not self.framework.priority_hearings.get('priority_hearings'):
            return []
        
        # Filter for ISVP-compatible hearings from committees not in Phase 1
        available_hearings = []
        for hearing in self.framework.priority_hearings['priority_hearings']:
            # Must be ISVP compatible
            if not hearing.get('isvp_compatible', False):
                continue
            
            # Must be from different committee than Phase 1
            if hearing.get('committee_code') in self.phase1_committees:
                continue
            
            # Must have good readiness score (similar to Phase 1)
            if hearing.get('readiness_score', 0) < 0.8:
                continue
            
            available_hearings.append(hearing)
        
        # Group by committee to ensure diversity
        committees_represented = {}
        for hearing in available_hearings:
            committee = hearing['committee_code']
            if committee not in committees_represented:
                committees_represented[committee] = []
            committees_represented[committee].append(hearing)
        
        # Select one hearing from each committee, prioritizing high scores
        selected_hearings = []
        for committee, hearings in committees_represented.items():
            if len(selected_hearings) >= 5:
                break
            
            # Sort by priority score and take the best one
            hearings.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
            selected_hearings.append(hearings[0])
        
        # Sort by priority score for consistent ordering
        selected_hearings.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        return selected_hearings[:5]
    
    def display_phase2_plan(self):
        """Display Phase 2 testing plan"""
        print("🎯 PHASE 2 TESTING: COMMITTEE DIVERSITY WITH COMPATIBLE FORMATS")
        print("=" * 70)
        print(f"Target: {len(self.target_hearings)} hearings from different committees")
        print(f"Success Criteria: {self.phase2_results['success_criteria']:.0%} success rate")
        print(f"Expected: {int(len(self.target_hearings) * self.phase2_results['success_criteria'])} successful processes")
        print(f"Format Compatibility: ISVP-compatible hearings only")
        
        print(f"\n📋 PHASE 1 COMMITTEES (ALREADY TESTED):")
        for committee in sorted(self.phase1_committees):
            print(f"   ✅ {committee}")
        
        print(f"\n📋 PHASE 2 HEARING LINEUP (NEW COMMITTEES):")
        if not self.target_hearings:
            print("   ❌ No compatible hearings found for Phase 2")
            return
        
        committees_in_phase2 = set()
        for i, hearing in enumerate(self.target_hearings, 1):
            committees_in_phase2.add(hearing['committee_code'])
            print(f"\n{i}. {hearing['title'][:70]}...")
            print(f"   Committee: {hearing['committee_name']} ({hearing['committee_code']}) 🆕")
            print(f"   Date: {hearing['date']}")
            print(f"   Readiness: {hearing['readiness_score']:.1%}")
            print(f"   Priority: {hearing['priority_score']:.1f}")
            print(f"   Audio: {hearing['audio_source']} (ISVP ✅)")
            print(f"   URL: {hearing['url']}")
        
        print(f"\n📊 COMMITTEE DIVERSITY:")
        print(f"   Phase 1 Committees: {len(self.phase1_committees)}")
        print(f"   Phase 2 Committees: {len(committees_in_phase2)}")
        print(f"   Total Committees Tested: {len(self.phase1_committees) + len(committees_in_phase2)}")
    
    def process_hearing_with_monitoring(self, hearing_num, hearing):
        """Process a single hearing with detailed monitoring"""
        print(f"\n🚀 PROCESSING HEARING {hearing_num}/5")
        print("=" * 50)
        print(f"Title: {hearing['title']}")
        print(f"Committee: {hearing['committee_name']} ({hearing['committee_code']}) 🆕")
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
        
        self.phase2_results['results'].append(result)
        
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
    
    def analyze_phase2_results(self):
        """Analyze Phase 2 results and generate summary"""
        results = self.phase2_results['results']
        
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
        
        # Analyze committee diversity
        committees_tested = set(r['committee_code'] for r in results)
        
        # Update summary
        self.phase2_results['summary'] = {
            'total_hearings': total_hearings,
            'successful_hearings': successful_hearings,
            'failed_hearings': total_hearings - successful_hearings,
            'success_rate': success_rate,
            'target_success_rate': self.phase2_results['success_criteria'],
            'phase2_passed': success_rate >= self.phase2_results['success_criteria'],
            'total_processing_time_seconds': total_duration,
            'average_processing_time_seconds': avg_duration,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'committees_tested': len(committees_tested),
            'committee_codes': list(committees_tested),
            'completion_time': datetime.now().isoformat()
        }
        
        # Display summary
        print("\n📊 PHASE 2 RESULTS SUMMARY")
        print("=" * 40)
        print(f"Total Hearings: {total_hearings}")
        print(f"Successful: {successful_hearings}")
        print(f"Failed: {total_hearings - successful_hearings}")
        print(f"Success Rate: {success_rate:.1%}")
        print(f"Target Rate: {self.phase2_results['success_criteria']:.1%}")
        print(f"Phase 2 Status: {'✅ PASSED' if success_rate >= self.phase2_results['success_criteria'] else '❌ FAILED'}")
        print(f"Total Processing Time: {total_duration:.1f} seconds")
        print(f"Average Processing Time: {avg_duration:.1f} seconds")
        print(f"Total Errors: {total_errors}")
        print(f"Total Warnings: {total_warnings}")
        print(f"Committee Diversity: {len(committees_tested)} committees")
        print(f"Committees: {', '.join(sorted(committees_tested))}")
        
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
    
    def compare_with_phase1(self):
        """Compare Phase 2 results with Phase 1"""
        try:
            with open('data/phase1_testing_results.json', 'r') as f:
                phase1_data = json.load(f)
            
            phase1_summary = phase1_data.get('summary', {})
            phase2_summary = self.phase2_results.get('summary', {})
            
            print("\n📊 PHASE 1 vs PHASE 2 COMPARISON")
            print("=" * 50)
            print(f"Success Rate:")
            print(f"   Phase 1: {phase1_summary.get('success_rate', 0):.1%}")
            print(f"   Phase 2: {phase2_summary.get('success_rate', 0):.1%}")
            
            print(f"Average Processing Time:")
            print(f"   Phase 1: {phase1_summary.get('average_processing_time_seconds', 0):.1f}s")
            print(f"   Phase 2: {phase2_summary.get('average_processing_time_seconds', 0):.1f}s")
            
            print(f"Committee Coverage:")
            print(f"   Phase 1: {len(self.phase1_committees)} committees")
            print(f"   Phase 2: {phase2_summary.get('committees_tested', 0)} committees")
            print(f"   Total: {len(self.phase1_committees) + phase2_summary.get('committees_tested', 0)} committees")
            
        except FileNotFoundError:
            print("\n⚠️  Phase 1 results not found for comparison")
    
    def save_phase2_results(self):
        """Save Phase 2 results to file"""
        results_file = Path("data/phase2_testing_results.json")
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.phase2_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        return results_file
    
    def run_phase2_testing(self):
        """Run complete Phase 2 testing"""
        print("🎯 STARTING PHASE 2 TESTING")
        print("=" * 40)
        
        if not self.target_hearings:
            print("❌ No compatible hearings available for Phase 2 testing")
            print("   All available committees may have been tested in Phase 1")
            return False
        
        # Display plan
        self.display_phase2_plan()
        
        print(f"\n🚀 BEGINNING PROCESSING OF {len(self.target_hearings)} HEARINGS")
        print("=" * 70)
        
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
                self.phase2_results['results'].append(result)
        
        # Analyze results
        self.analyze_phase2_results()
        
        # Compare with Phase 1
        self.compare_with_phase1()
        
        # Save results
        results_file = self.save_phase2_results()
        
        # Return success status
        return self.phase2_results['summary'].get('phase2_passed', False)


def main():
    """Main Phase 2 testing execution"""
    print("🎯 SENATE HEARING PHASE 2 TESTING FRAMEWORK")
    print("=" * 60)
    
    # Initialize testing framework
    tester = Phase2TestingFramework()
    
    # Run Phase 2 testing
    success = tester.run_phase2_testing()
    
    # Final status
    print(f"\n🎯 PHASE 2 TESTING COMPLETE")
    if success:
        print("✅ PHASE 2 PASSED - Ready for Phase 3 (Audio Source Validation)")
    else:
        print("❌ PHASE 2 FAILED - Review results and address issues")
    
    return success


if __name__ == "__main__":
    main()