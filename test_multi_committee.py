#!/usr/bin/env python3
"""
Multi-Committee ISVP Extraction Test

Test the enhanced ISVP extractor across all 4 priority committees.
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from extractors.isvp_extractor import ISVPExtractor
from committee_config import CommitteeResolver, get_committee_summary


# Test URLs for each committee
TEST_HEARINGS = {
    'Commerce': 'https://www.commerce.senate.gov/2025/6/executive-session-12',
    'Intelligence': 'https://www.intelligence.senate.gov/hearings/open-hearing-worldwide-threats',
    'Banking': 'https://www.banking.senate.gov/hearings/06/18/2025/the-semiannual-monetary-policy-report-to-the-congress',
    'Judiciary': 'https://www.judiciary.senate.gov/committee-activity/hearings/executive-business-meeting-06-26-2025'
}


def test_multi_committee_extraction():
    """Test ISVP extraction across all priority committees."""
    print("🎯 MULTI-COMMITTEE ISVP EXTRACTION TEST")
    print("=" * 60)
    
    extractor = ISVPExtractor()
    results = {
        'timestamp': datetime.now().isoformat(),
        'committee_tests': {},
        'summary': {
            'total_committees_tested': 0,
            'successful_extractions': 0,
            'total_streams_found': 0,
            'committees_with_streams': []
        }
    }
    
    for committee, url in TEST_HEARINGS.items():
        print(f"\n🔍 Testing {committee} Committee")
        print(f"   URL: {url}")
        
        test_result = {
            'committee': committee,
            'url': url,
            'can_extract': False,
            'streams_found': 0,
            'streams': [],
            'error': None
        }
        
        try:
            # Test if extractor can handle this URL
            can_extract = extractor.can_extract(url)
            test_result['can_extract'] = can_extract
            
            if can_extract:
                print(f"   ✅ Extractor can handle {committee} URLs")
                
                # Extract streams
                streams = extractor.extract_streams(url)
                test_result['streams_found'] = len(streams)
                
                if streams:
                    print(f"   📡 Found {len(streams)} streams:")
                    for i, stream in enumerate(streams, 1):
                        print(f"      {i}. {stream.title}")
                        print(f"         URL: {stream.url}")
                        print(f"         Type: {stream.metadata.get('stream_type', 'unknown')}")
                        print(f"         Source: {stream.metadata.get('source', 'unknown')}")
                        
                        # Store simplified stream info
                        test_result['streams'].append({
                            'title': stream.title,
                            'url': stream.url,
                            'format_type': stream.format_type,
                            'stream_type': stream.metadata.get('stream_type'),
                            'source': stream.metadata.get('source'),
                            'committee': stream.metadata.get('committee')
                        })
                    
                    results['summary']['successful_extractions'] += 1
                    results['summary']['total_streams_found'] += len(streams)
                    results['summary']['committees_with_streams'].append(committee)
                else:
                    print(f"   ⚠️  No streams found for {committee}")
            else:
                print(f"   ❌ Extractor cannot handle {committee} URLs")
                test_result['error'] = 'Extractor cannot handle URL'
        
        except Exception as e:
            print(f"   ❌ Error testing {committee}: {e}")
            test_result['error'] = str(e)
        
        results['committee_tests'][committee] = test_result
        results['summary']['total_committees_tested'] += 1
    
    # Summary
    print(f"\n📊 MULTI-COMMITTEE TEST SUMMARY")
    print("=" * 40)
    print(f"   Committees Tested: {results['summary']['total_committees_tested']}")
    print(f"   Successful Extractions: {results['summary']['successful_extractions']}")
    print(f"   Total Streams Found: {results['summary']['total_streams_found']}")
    print(f"   Success Rate: {(results['summary']['successful_extractions'] / results['summary']['total_committees_tested']) * 100:.1f}%")
    
    if results['summary']['committees_with_streams']:
        print(f"\n✅ Committees with Working Streams:")
        for committee in results['summary']['committees_with_streams']:
            streams_count = results['committee_tests'][committee]['streams_found']
            print(f"   • {committee}: {streams_count} streams")
    
    # Save results
    output_file = Path('output') / f'multi_committee_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Test results saved: {output_file}")
    
    return results


def test_committee_resolver():
    """Test the committee resolver functionality."""
    print(f"\n🧭 COMMITTEE RESOLVER TEST")
    print("=" * 40)
    
    resolver = CommitteeResolver()
    
    # Test committee identification
    for committee, url in TEST_HEARINGS.items():
        identified = resolver.identify_committee(url)
        print(f"   {url[:50]}... → {identified}")
        
        if identified:
            config = resolver.get_committee_config(identified)
            if config:
                print(f"      Description: {config['description']}")
                print(f"      ISVP Compatible: {config['isvp_compatible']}")
                print(f"      Priority: {config['priority']}")
    
    # Test committee summary
    print(f"\n📋 Committee Summary:")
    summary = get_committee_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    # Test committee resolver
    test_committee_resolver()
    
    # Test multi-committee extraction
    results = test_multi_committee_extraction()
    
    # Provide recommendations
    print(f"\n🎯 RECOMMENDATIONS:")
    success_rate = (results['summary']['successful_extractions'] / results['summary']['total_committees_tested']) * 100
    
    if success_rate >= 75:
        print("✅ Excellent! Multi-committee extraction is working well.")
        print("   Ready to proceed with dashboard integration and automated testing.")
    elif success_rate >= 50:
        print("🟡 Good progress. Some committees need attention.")
        print("   Review failed extractions and improve error handling.")
    else:
        print("❌ Needs improvement. Most extractions failed.")
        print("   Debug extractor issues before proceeding.")
    
    print(f"\n🚀 Next Steps:")
    print("   1. Update dashboard for multi-committee tracking")
    print("   2. Create automated test suite for all committees")
    print("   3. Test extraction with real audio conversion")
    print("   4. Add committee-specific error handling")