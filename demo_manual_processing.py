#!/usr/bin/env python3
"""
Demo script for Manual Processing Framework
Shows the framework capabilities without requiring user interaction
"""

import json
from process_single_hearing import ManualProcessingFramework

def main():
    print("🎯 SENATE HEARING MANUAL PROCESSING FRAMEWORK DEMO")
    print("=" * 60)
    
    # Initialize framework
    framework = ManualProcessingFramework()
    
    print(f"✅ Framework initialized successfully")
    print(f"📊 Priority hearings loaded: {len(framework.priority_hearings.get('priority_hearings', []))}")
    
    # Display available hearings
    print("\n🎯 AVAILABLE PRIORITY HEARINGS:")
    framework.display_priority_hearings()
    
    # Show processing capabilities
    print("\n🔍 FRAMEWORK CAPABILITIES:")
    print("✅ Interactive hearing selection")
    print("✅ Pre-processing validation")
    print("✅ Confirmation prompts")
    print("✅ Real-time monitoring")
    print("✅ Session tracking")
    print("✅ Error handling")
    print("✅ Rollback capability")
    print("✅ Processing history")
    
    # Show processing session example
    if framework.priority_hearings.get('priority_hearings'):
        print("\n📋 PROCESSING SESSION EXAMPLE:")
        sample_hearing = framework.priority_hearings['priority_hearings'][0]
        session = framework.create_processing_session(sample_hearing)
        
        print(f"Session ID: {session['session_id']}")
        print(f"Hearing: {session['hearing_title'][:50]}...")
        print(f"Committee: {session['committee_name']}")
        print(f"Status: {session['processing_status']}")
        print(f"Processing Stages:")
        for stage, info in session['stages'].items():
            print(f"  - {stage}: {info['status']}")
    
    # Display processing status
    print("\n📊 PROCESSING STATUS:")
    framework.display_processing_status()
    
    print("\n🚀 FRAMEWORK READY FOR MANUAL PROCESSING!")
    print("Run 'python3 process_single_hearing.py' to start interactive processing")

if __name__ == "__main__":
    main()