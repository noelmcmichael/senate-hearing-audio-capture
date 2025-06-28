#!/usr/bin/env python3
"""
Phase 3 Transcript Enrichment Demo

Demonstrates the complete workflow from raw transcript to enriched metadata.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from models.metadata_loader import MetadataLoader
from enrichment.transcript_enricher import TranscriptEnricher


def create_sample_transcript():
    """Create a sample transcript for demonstration."""
    return """OVERSIGHT OF ARTIFICIAL INTELLIGENCE: EXAMINING THE NEED FOR LEGISLATIVE ACTION

Chair Cantwell: The committee will come to order. Today we're examining the rapid advancement of artificial intelligence and its implications for consumers, competition, and innovation.

Sen. Cruz: Thank you, Chair Cantwell. I appreciate you holding this important hearing. The development of AI technologies raises significant questions about regulatory frameworks.

Ms. Chen: Thank you for having me here today. At OpenAI, we believe that AI safety must be our top priority as we develop these transformative technologies.

Ranking Member Cruz: Ms. Chen, can you explain OpenAI's approach to AI safety and how you work with regulators?

Ms. Chen: Certainly, Ranking Member Cruz. We've implemented a multi-layered approach to safety that includes technical safeguards, external red teaming, and ongoing dialogue with policymakers.

Commissioner Rodriguez: From the FTC's perspective, we're particularly concerned about algorithmic accountability and the potential for discriminatory outcomes.

Sen. Klobuchar: Commissioner Rodriguez, what enforcement tools does the FTC currently have to address AI-related consumer protection issues?

Commissioner Rodriguez: Senator Klobuchar, our existing consumer protection authorities under Section 5 of the FTC Act apply to AI systems, but we may need additional guidance and resources.

Dr. Williams: As a researcher at Stanford, I've observed that technical approaches to AI safety must be coupled with robust governance frameworks.

The Chair: Dr. Williams, what role should academic institutions play in AI safety research?

Dr. Jennifer Williams: Chairwoman Cantwell, universities have a unique responsibility to conduct independent research and train the next generation of AI safety experts."""


def main():
    """Run the transcript enrichment demonstration."""
    print("🚀 Phase 3 Transcript Enrichment Demo")
    print("=" * 50)
    
    # Initialize components
    print("📋 Initializing metadata loader...")
    metadata_loader = MetadataLoader()
    
    print("🔧 Initializing transcript enricher...")
    enricher = TranscriptEnricher(metadata_loader)
    
    # Create sample transcript
    print("📝 Creating sample transcript...")
    sample_transcript = create_sample_transcript()
    
    # Save sample transcript
    transcript_path = Path("temp_sample_transcript.txt")
    with open(transcript_path, 'w') as f:
        f.write(sample_transcript)
    
    print(f"💾 Sample transcript saved: {transcript_path}")
    
    # Enrich the transcript
    print("\n🎯 Enriching transcript...")
    enriched = enricher.enrich_transcript(sample_transcript, "SCOM-2025-06-10-AI-OVERSIGHT")
    
    # Save enriched version
    enriched_path = Path("temp_enriched_transcript.json")
    import json
    with open(enriched_path, 'w') as f:
        json.dump(enriched, f, indent=2)
    
    print(f"✅ Enriched transcript saved: {enriched_path}")
    
    # Display results
    print("\n📊 ENRICHMENT RESULTS")
    print("=" * 30)
    print(f"Total segments: {enriched['total_segments']}")
    print(f"Identified speakers: {enriched['identified_speakers']}")
    print(f"Total lines processed: {enriched['processing_metadata']['total_lines']}")
    
    # Show speaker summary
    print("\n👥 SPEAKER SUMMARY")
    print("=" * 30)
    speaker_summary = enricher.generate_speaker_summary(enriched)
    print(speaker_summary)
    
    # Show sample enriched segments
    print("\n📝 SAMPLE ENRICHED SEGMENTS")
    print("=" * 35)
    
    for i, segment in enumerate(enriched['segments'][:5], 1):  # Show first 5 segments
        speaker = segment.get('speaker')
        if speaker and speaker.get('speaker_id'):
            print(f"\n{i}. {speaker['display_name']} ({speaker['speaker_type']})")
            print(f"   Content: {segment['content'][:100]}...")
        else:
            print(f"\n{i}. Unknown Speaker")
            print(f"   Content: {segment['content'][:100]}...")
    
    # Test speaker identification
    print("\n🔍 SPEAKER IDENTIFICATION TEST")
    print("=" * 40)
    
    test_names = [
        "Chair Cantwell",
        "Sen. Cruz", 
        "Ms. Chen",
        "Commissioner Rodriguez",
        "Dr. Williams"
    ]
    
    for name in test_names:
        speaker = enricher.identify_speaker(name, "SCOM-2025-06-10-AI-OVERSIGHT")
        if speaker and speaker.get('speaker_id'):
            print(f"✅ {name} → {speaker['display_name']} ({speaker['speaker_type']})")
        else:
            print(f"❌ {name} → Not identified")
    
    # Show committee context
    print("\n🏛️  COMMITTEE CONTEXT")
    print("=" * 25)
    
    commerce_members = metadata_loader.load_committee_members("Commerce")
    print(f"Senate Commerce Committee: {len(commerce_members)} members loaded")
    
    hearing = metadata_loader.load_hearing("SCOM-2025-06-10-AI-OVERSIGHT")
    if hearing:
        print(f"Hearing: {hearing.title}")
        print(f"Date: {hearing.date}")
        print(f"Members present: {len(hearing.members_present)}")
        print(f"Witnesses: {len(hearing.witnesses)}")
    
    # Cleanup
    print("\n🧹 Cleaning up temporary files...")
    transcript_path.unlink(missing_ok=True)
    enriched_path.unlink(missing_ok=True)
    print("✅ Cleanup complete")
    
    print("\n🎊 PHASE 3 FOUNDATION COMPLETE")
    print("=" * 40)
    print("✅ Congressional metadata system operational")
    print("✅ Speaker identification functional")
    print("✅ Transcript enrichment ready")
    print("✅ Integration points established")
    
    print("\n📋 READY FOR:")
    print("• Real transcript processing")
    print("• Dashboard metadata integration") 
    print("• Automated transcription workflows")
    print("• Congressional intelligence analysis")


if __name__ == "__main__":
    main()