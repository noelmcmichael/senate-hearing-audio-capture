#!/usr/bin/env python3
"""
Test script to validate audio extraction across multiple Senate Commerce hearings.
This ensures our approach works consistently across different hearing types.
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import subprocess

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.page_inspector import PageInspector

# Test URLs - diverse hearing types
TEST_HEARINGS = [
    {
        "url": "https://www.commerce.senate.gov/2025/6/executive-session-12",
        "name": "Executive Session 12",
        "type": "executive_session",
        "expected_duration_min": 40
    },
    {
        "url": "https://www.commerce.senate.gov/2025/6/on-the-right-track-modernizing-america-s-rail-network_2", 
        "name": "Rail Network Modernization",
        "type": "subcommittee_hearing",
        "expected_duration_min": 120
    },
    {
        "url": "https://www.commerce.senate.gov/2025/6/finding-nemo-s-future-conflicts-over-ocean-resources_2",
        "name": "Ocean Resources Conflicts", 
        "type": "subcommittee_hearing",
        "expected_duration_min": 120
    },
    {
        "url": "https://www.commerce.senate.gov/2025/5/faa-reauthorization-one-year-later-aviation-safety-air-traffic-and-next-generation-technology_2",
        "name": "FAA Reauthorization Review",
        "type": "full_committee_hearing", 
        "expected_duration_min": 150
    },
    {
        "url": "https://www.commerce.senate.gov/2025/5/field-of-streams-the-new-channel-guide-for-sports-fans_2",
        "name": "Sports Streaming",
        "type": "full_committee_hearing",
        "expected_duration_min": 120
    }
]

def analyze_hearing_page(hearing_info):
    """Analyze a single hearing page for ISVP streams."""
    print(f"\n🔍 ANALYZING: {hearing_info['name']}")
    print(f"   URL: {hearing_info['url']}")
    print(f"   Type: {hearing_info['type']}")
    
    try:
        with PageInspector(headless=True, timeout=15000) as inspector:
            analysis = inspector.analyze_page(hearing_info['url'])
        
        result = {
            'hearing': hearing_info,
            'analysis': analysis,
            'has_isvp_stream': False,
            'has_youtube': False,
            'stream_urls': [],
            'recommendation': 'skip'
        }
        
        # Check for ISVP streams in network requests
        isvp_streams = []
        for req in analysis.get('network_requests', []):
            if req['url'].endswith('.m3u8') and 'senate' in req['url'].lower():
                isvp_streams.append(req['url'])
                result['has_isvp_stream'] = True
        
        # Check for YouTube embeds
        youtube_count = 0
        for player in analysis.get('players_found', []):
            if player.get('type') == 'youtube':
                youtube_count += 1
                result['has_youtube'] = True
        
        result['stream_urls'] = isvp_streams
        
        # Determine recommendation
        if result['has_isvp_stream'] and not result['has_youtube']:
            result['recommendation'] = 'extract_isvp_only'
        elif result['has_isvp_stream'] and result['has_youtube']:
            result['recommendation'] = 'extract_isvp_ignore_youtube'
        elif result['has_youtube'] and not result['has_isvp_stream']:
            result['recommendation'] = 'skip_youtube_only'
        else:
            result['recommendation'] = 'skip_no_streams'
        
        # Print results
        status_icon = "✅" if result['has_isvp_stream'] else "❌"
        print(f"   {status_icon} ISVP Streams: {len(isvp_streams)}")
        if isvp_streams:
            for stream in isvp_streams:
                print(f"      • {stream}")
        
        if result['has_youtube']:
            print(f"   🟡 YouTube embeds: {youtube_count} (will ignore)")
        
        print(f"   📋 Recommendation: {result['recommendation']}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Error analyzing page: {e}")
        return {
            'hearing': hearing_info,
            'error': str(e),
            'recommendation': 'skip_error'
        }

def run_extraction_test(hearing_info, stream_url):
    """Test audio extraction on a specific hearing."""
    print(f"\n🚀 TESTING EXTRACTION: {hearing_info['name']}")
    
    try:
        # Run the capture script
        cmd = [
            'python', 'capture.py',
            '--url', hearing_info['url'],
            '--format', 'mp3',
            '--quality', 'medium',  # Use medium for testing to save time
            '--headless'
        ]
        
        print(f"   Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for testing
        )
        
        if result.returncode == 0:
            print(f"   ✅ Extraction successful")
            return {
                'success': True,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        else:
            print(f"   ❌ Extraction failed")
            print(f"   Error: {result.stderr}")
            return {
                'success': False,
                'stdout': result.stdout, 
                'stderr': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ Extraction timed out (10 minutes)")
        return {
            'success': False,
            'error': 'timeout'
        }
    except Exception as e:
        print(f"   ❌ Extraction error: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    print("🎯 TESTING MULTIPLE SENATE COMMERCE HEARINGS")
    print("=" * 60)
    print(f"Testing {len(TEST_HEARINGS)} different hearing pages...")
    
    results = []
    
    # Phase 1: Analyze all pages
    print(f"\n📊 PHASE 1: ANALYZING PAGES")
    print("=" * 40)
    
    for hearing in TEST_HEARINGS:
        result = analyze_hearing_page(hearing)
        results.append(result)
    
    # Phase 2: Extract from suitable pages
    print(f"\n🎵 PHASE 2: TESTING EXTRACTION")
    print("=" * 40)
    
    extraction_candidates = [
        r for r in results 
        if r['recommendation'] in ['extract_isvp_only', 'extract_isvp_ignore_youtube']
    ]
    
    print(f"Found {len(extraction_candidates)} suitable hearings for extraction testing")
    
    extraction_results = []
    for result in extraction_candidates[:3]:  # Test first 3 to save time
        if 'stream_urls' in result and result['stream_urls']:
            extraction_result = run_extraction_test(result['hearing'], result['stream_urls'][0])
            extraction_results.append({
                'hearing': result['hearing']['name'],
                'result': extraction_result
            })
    
    # Phase 3: Summary
    print(f"\n📋 FINAL SUMMARY")
    print("=" * 40)
    
    total_analyzed = len(results)
    has_isvp = len([r for r in results if r.get('has_isvp_stream', False)])
    has_youtube_only = len([r for r in results if r.get('has_youtube', False) and not r.get('has_isvp_stream', False)])
    extraction_success = len([r for r in extraction_results if r['result']['success']])
    
    print(f"📊 Analysis Results:")
    print(f"   • Total pages analyzed: {total_analyzed}")
    print(f"   • Pages with ISVP streams: {has_isvp}")
    print(f"   • Pages with YouTube only: {has_youtube_only}")
    print(f"   • Pages suitable for extraction: {len(extraction_candidates)}")
    
    print(f"\n🎵 Extraction Results:")
    print(f"   • Extraction attempts: {len(extraction_results)}")
    print(f"   • Successful extractions: {extraction_success}")
    
    for ext_result in extraction_results:
        status = "✅" if ext_result['result']['success'] else "❌"
        print(f"   {status} {ext_result['hearing']}")
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = Path('output') / f'multi_hearing_test_{timestamp}.json'
    
    detailed_results = {
        'timestamp': timestamp,
        'analysis_results': results,
        'extraction_results': extraction_results,
        'summary': {
            'total_analyzed': total_analyzed,
            'has_isvp': has_isvp,
            'has_youtube_only': has_youtube_only,
            'extraction_candidates': len(extraction_candidates),
            'extraction_attempts': len(extraction_results),
            'extraction_success': extraction_success
        }
    }
    
    with open(results_file, 'w') as f:
        json.dump(detailed_results, f, indent=2)
    
    print(f"\n💾 Detailed results saved: {results_file}")
    
    # Final recommendation
    success_rate = extraction_success / len(extraction_results) if extraction_results else 0
    print(f"\n🎯 SUCCESS RATE: {success_rate:.1%}")
    
    if success_rate >= 0.8:
        print("✅ CONSISTENT: Extraction approach works reliably across hearing types")
    elif success_rate >= 0.5:
        print("🟡 MIXED: Some inconsistencies detected - may need refinement")
    else:
        print("❌ INCONSISTENT: Approach needs significant improvement")

if __name__ == "__main__":
    main()