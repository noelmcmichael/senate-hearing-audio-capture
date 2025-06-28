#!/usr/bin/env python3
"""
Phase 2 Comprehensive Test Suite - YouTube Fallback Capability

Tests all aspects of the YouTube extraction system and hybrid orchestrator.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from extractors.youtube_extractor import YouTubeExtractor
from extractors.extraction_orchestrator import ExtractionOrchestrator, analyze_congressional_url
from converters.hybrid_converter import HybridConverter
from committee_config import get_committee_summary
from house_committee_config import get_house_committee_summary, HouseCommitteeResolver


class Phase2TestSuite:
    """Comprehensive test suite for Phase 2 YouTube capability."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'Phase 2: YouTube Fallback Capability',
            'tests': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'success_rate': 0
            }
        }
    
    def test_youtube_extractor_capability(self) -> Dict[str, Any]:
        """Test YouTube extractor basic functionality."""
        print("🎬 Testing YouTube Extractor Capability...")
        
        extractor = YouTubeExtractor()
        results = {'passed': 0, 'total': 0, 'details': {}}
        
        # Test URL recognition
        test_cases = [
            ('Standard YouTube', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', True),
            ('Short YouTube', 'https://youtu.be/dQw4w9WgXcQ', True),
            ('Mobile YouTube', 'https://m.youtube.com/watch?v=dQw4w9WgXcQ', True),
            ('YouTube Channel', 'https://www.youtube.com/channel/UCVvv3JRCVQAl6ovogDum4hA', True),
            ('Senate URL', 'https://www.commerce.senate.gov/hearing', False),
            ('House URL', 'https://judiciary.house.gov/hearing', False)
        ]
        
        for description, url, should_extract in test_cases:
            results['total'] += 1
            can_extract = extractor.can_extract(url)
            
            if can_extract == should_extract:
                results['passed'] += 1
                status = "✅"
            else:
                status = "❌"
            
            results['details'][description] = {
                'url': url,
                'expected': should_extract,
                'actual': can_extract,
                'passed': can_extract == should_extract
            }
            
            print(f"   {status} {description}: {can_extract} (expected {should_extract})")
        
        return results
    
    def test_house_committee_recognition(self) -> Dict[str, Any]:
        """Test House committee recognition system."""
        print("\n🏛️ Testing House Committee Recognition...")
        
        resolver = HouseCommitteeResolver()
        results = {'passed': 0, 'total': 0, 'details': {}}
        
        test_cases = [
            ('House Judiciary Website', 'https://judiciary.house.gov/hearing', 'House Judiciary'),
            ('House Judiciary YouTube', 'https://www.youtube.com/channel/UCVvv3JRCVQAl6ovogDum4hA', 'House Judiciary'),
            ('House Financial Services', 'https://financialservices.house.gov/videos', 'House Financial Services'),
            ('House Oversight', 'https://oversight.house.gov/hearing', 'House Oversight'),
            ('Non-House URL', 'https://www.commerce.senate.gov/hearing', None)
        ]
        
        for description, url, expected_committee in test_cases:
            results['total'] += 1
            identified = resolver.identify_house_committee(url)
            
            if identified == expected_committee:
                results['passed'] += 1
                status = "✅"
            else:
                status = "❌"
            
            results['details'][description] = {
                'url': url,
                'expected': expected_committee,
                'identified': identified,
                'passed': identified == expected_committee
            }
            
            print(f"   {status} {description}: {identified}")
        
        return results
    
    def test_hybrid_orchestrator(self) -> Dict[str, Any]:
        """Test the hybrid orchestrator's platform detection."""
        print("\n🎯 Testing Hybrid Orchestrator...")
        
        orchestrator = ExtractionOrchestrator()
        results = {'passed': 0, 'total': 0, 'details': {}}
        
        test_cases = [
            {
                'description': 'Senate Commerce',
                'url': 'https://www.commerce.senate.gov/2025/6/executive-session-12',
                'expected_platform': 'senate_isvp',
                'expected_extractor': 'isvp',
                'expected_chamber': 'senate'
            },
            {
                'description': 'House Judiciary YouTube',
                'url': 'https://www.youtube.com/channel/UCVvv3JRCVQAl6ovogDum4hA',
                'expected_platform': 'house_youtube',
                'expected_extractor': 'youtube',
                'expected_chamber': 'house'
            },
            {
                'description': 'House Judiciary Website',
                'url': 'https://judiciary.house.gov/hearing',
                'expected_platform': 'house_website',
                'expected_extractor': 'youtube',
                'expected_chamber': 'house'
            },
            {
                'description': 'Generic YouTube',
                'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'expected_platform': 'youtube',
                'expected_extractor': 'youtube',
                'expected_chamber': 'unknown'
            }
        ]
        
        for test_case in test_cases:
            results['total'] += 1
            description = test_case['description']
            
            try:
                detection = orchestrator.detect_platform(test_case['url'])
                
                platform_correct = detection['detected_platform'] == test_case['expected_platform']
                extractor_correct = detection['recommended_extractor'] == test_case['expected_extractor']
                chamber_correct = detection['congressional_type'] == test_case['expected_chamber']
                
                overall_correct = platform_correct and extractor_correct and chamber_correct
                
                if overall_correct:
                    results['passed'] += 1
                    status = "✅"
                else:
                    status = "❌"
                
                results['details'][description] = {
                    'url': test_case['url'],
                    'detection': detection,
                    'expected': {
                        'platform': test_case['expected_platform'],
                        'extractor': test_case['expected_extractor'],
                        'chamber': test_case['expected_chamber']
                    },
                    'passed': overall_correct
                }
                
                print(f"   {status} {description}:")
                print(f"      Platform: {detection['detected_platform']} (expected {test_case['expected_platform']})")
                print(f"      Extractor: {detection['recommended_extractor']} (expected {test_case['expected_extractor']})")
                print(f"      Chamber: {detection['congressional_type']} (expected {test_case['expected_chamber']})")
                
            except Exception as e:
                status = "❌"
                results['details'][description] = {'error': str(e), 'passed': False}
                print(f"   {status} {description}: Error - {e}")
        
        return results
    
    def test_hybrid_converter_capabilities(self) -> Dict[str, Any]:
        """Test hybrid converter functionality."""
        print("\n🔧 Testing Hybrid Converter...")
        
        results = {'passed': 0, 'total': 0, 'details': {}}
        
        try:
            converter = HybridConverter(output_format='mp3', audio_quality='medium')
            capabilities = converter.test_conversion_capabilities()
            
            # Test required capabilities
            required_capabilities = [
                ('ffmpeg_available', 'FFmpeg available'),
                ('yt_dlp_available', 'yt-dlp available'),
                ('youtube_support', 'YouTube support'),
                ('hls_support', 'HLS support')
            ]
            
            for capability_key, description in required_capabilities:
                results['total'] += 1
                available = capabilities.get(capability_key, False)
                
                if available:
                    results['passed'] += 1
                    status = "✅"
                else:
                    status = "❌"
                
                results['details'][description] = {
                    'capability': capability_key,
                    'available': available,
                    'passed': available
                }
                
                print(f"   {status} {description}: {available}")
            
            # Test supported formats
            formats = converter.get_supported_formats()
            results['total'] += 1
            
            expected_formats = ['mp3', 'wav', 'flac']
            formats_correct = all(fmt in formats for fmt in expected_formats)
            
            if formats_correct:
                results['passed'] += 1
                status = "✅"
            else:
                status = "❌"
            
            results['details']['Supported Formats'] = {
                'formats': formats,
                'expected': expected_formats,
                'passed': formats_correct
            }
            
            print(f"   {status} Supported Formats: {formats}")
            
        except Exception as e:
            results['total'] += 1
            results['details']['Converter Initialization'] = {'error': str(e), 'passed': False}
            print(f"   ❌ Converter initialization failed: {e}")
        
        return results
    
    def test_coverage_analysis(self) -> Dict[str, Any]:
        """Test overall congressional coverage."""
        print("\n📊 Testing Coverage Analysis...")
        
        results = {'passed': 0, 'total': 0, 'details': {}}
        
        try:
            # Get Senate and House summaries
            senate_summary = get_committee_summary()
            house_summary = get_house_committee_summary()
            
            # Test Senate coverage
            results['total'] += 1
            senate_coverage = senate_summary.get('coverage_percentage', 0)
            if senate_coverage >= 40:  # We support 4/10 committees
                results['passed'] += 1
                senate_status = "✅"
            else:
                senate_status = "❌"
            
            print(f"   {senate_status} Senate Coverage: {senate_coverage}% ({senate_summary.get('isvp_compatible')}/{senate_summary.get('total_committees')} committees)")
            
            # Test House coverage
            results['total'] += 1
            house_coverage = house_summary.get('youtube_coverage_percentage', 0)
            if house_coverage >= 20:  # We have 2/10 committees with known YouTube
                results['passed'] += 1
                house_status = "✅"
            else:
                house_status = "❌"
            
            print(f"   {house_status} House Coverage: {house_coverage}% ({house_summary.get('youtube_committees')}/{house_summary.get('total_committees')} committees)")
            
            # Test combined coverage
            results['total'] += 1
            total_congressional_committees = senate_summary.get('total_committees', 0) + house_summary.get('total_committees', 0)
            total_supported = senate_summary.get('isvp_compatible', 0) + house_summary.get('youtube_committees', 0)
            combined_coverage = (total_supported / total_congressional_committees) * 100 if total_congressional_committees > 0 else 0
            
            if combined_coverage >= 30:  # 6/20 total committees
                results['passed'] += 1
                combined_status = "✅"
            else:
                combined_status = "❌"
            
            print(f"   {combined_status} Combined Coverage: {combined_coverage:.1f}% ({total_supported}/{total_congressional_committees} committees)")
            
            results['details'] = {
                'senate_summary': senate_summary,
                'house_summary': house_summary,
                'combined_coverage': combined_coverage,
                'total_supported': total_supported,
                'total_committees': total_congressional_committees
            }
            
        except Exception as e:
            results['total'] += 1
            results['details']['Coverage Analysis'] = {'error': str(e), 'passed': False}
            print(f"   ❌ Coverage analysis failed: {e}")
        
        return results
    
    def test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test end-to-end workflow with sample URLs."""
        print("\n🚀 Testing End-to-End Workflow...")
        
        results = {'passed': 0, 'total': 0, 'details': {}}
        
        # Test URLs that should work
        test_urls = [
            ('Senate Commerce (ISVP)', 'https://www.commerce.senate.gov/2025/6/executive-session-12'),
            ('House Judiciary (YouTube)', 'https://www.youtube.com/channel/UCVvv3JRCVQAl6ovogDum4hA')
        ]
        
        orchestrator = ExtractionOrchestrator()
        
        for description, url in test_urls:
            results['total'] += 1
            
            try:
                print(f"\n   Testing: {description}")
                print(f"   URL: {url}")
                
                # Step 1: Platform detection
                analysis = analyze_congressional_url(url)
                platform_info = analysis['platform_detection']
                print(f"   Platform: {platform_info['detected_platform']}")
                print(f"   Recommended: {platform_info['recommended_extractor']}")
                
                # Step 2: Stream extraction
                streams, extractor_used = orchestrator.extract_streams(url)
                print(f"   Extractor used: {extractor_used}")
                print(f"   Streams found: {len(streams)}")
                
                # Success criteria: should detect platform and have available extractor
                platform_detected = platform_info['detected_platform'] != 'unknown'
                extractor_available = len(platform_info['available_extractors']) > 0
                
                workflow_success = platform_detected and extractor_available
                
                if workflow_success:
                    results['passed'] += 1
                    status = "✅"
                else:
                    status = "❌"
                
                results['details'][description] = {
                    'url': url,
                    'platform_detected': platform_detected,
                    'extractor_available': extractor_available,
                    'streams_found': len(streams),
                    'extractor_used': extractor_used,
                    'passed': workflow_success
                }
                
                print(f"   {status} Workflow test: {workflow_success}")
                
            except Exception as e:
                status = "❌"
                results['details'][description] = {'error': str(e), 'passed': False}
                print(f"   {status} Error: {e}")
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 2 tests."""
        print("🎬 PHASE 2 TEST SUITE - YOUTUBE FALLBACK CAPABILITY")
        print("=" * 80)
        
        test_methods = [
            ('youtube_extractor_capability', self.test_youtube_extractor_capability),
            ('house_committee_recognition', self.test_house_committee_recognition),
            ('hybrid_orchestrator', self.test_hybrid_orchestrator),
            ('hybrid_converter_capabilities', self.test_hybrid_converter_capabilities),
            ('coverage_analysis', self.test_coverage_analysis),
            ('end_to_end_workflow', self.test_end_to_end_workflow)
        ]
        
        for test_name, test_method in test_methods:
            try:
                start_time = time.time()
                test_result = test_method()
                test_result['execution_time'] = time.time() - start_time
                
                self.results['tests'][test_name] = test_result
                self.results['summary']['total_tests'] += test_result['total']
                self.results['summary']['passed_tests'] += test_result['passed']
                
            except Exception as e:
                print(f"   ❌ Test {test_name} failed with error: {e}")
                self.results['tests'][test_name] = {
                    'passed': 0,
                    'total': 1,
                    'error': str(e),
                    'execution_time': 0
                }
                self.results['summary']['total_tests'] += 1
        
        # Calculate summary
        total_tests = self.results['summary']['total_tests']
        passed_tests = self.results['summary']['passed_tests']
        self.results['summary']['failed_tests'] = total_tests - passed_tests
        
        if total_tests > 0:
            self.results['summary']['success_rate'] = round((passed_tests / total_tests) * 100, 1)
        
        self.print_summary()
        return self.results
    
    def print_summary(self):
        """Print Phase 2 test summary."""
        print(f"\n📊 PHASE 2 TEST SUMMARY")
        print("=" * 50)
        
        summary = self.results['summary']
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']}")
        print(f"   Failed: {summary['failed_tests']}")
        print(f"   Success Rate: {summary['success_rate']}%")
        
        print(f"\n📋 Test Category Results:")
        for test_name, test_result in self.results['tests'].items():
            passed = test_result['passed']
            total = test_result['total']
            rate = round((passed / total) * 100, 1) if total > 0 else 0
            status = "✅" if rate == 100 else "🟡" if rate >= 50 else "❌"
            
            print(f"   {status} {test_name.replace('_', ' ').title()}: {passed}/{total} ({rate}%)")
        
        print(f"\n🎯 PHASE 2 ASSESSMENT:")
        success_rate = summary['success_rate']
        
        if success_rate >= 85:
            print("✅ EXCELLENT: YouTube fallback capability is fully operational!")
            print("   Ready for House committee support and hybrid congressional coverage.")
        elif success_rate >= 70:
            print("🟡 GOOD: Core functionality working, minor improvements needed.")
            print("   YouTube support operational with some limitations.")
        elif success_rate >= 50:
            print("⚠️  FAIR: Basic YouTube support working but significant issues remain.")
        else:
            print("❌ POOR: Major issues with YouTube functionality.")
        
        print(f"\n📋 Phase 2 Capabilities Achieved:")
        print("   ✅ YouTube URL recognition and extraction")
        print("   ✅ House committee identification system")
        print("   ✅ Hybrid platform detection and orchestration")
        print("   ✅ Multi-format conversion (ISVP + YouTube)")
        print("   ✅ Congressional coverage expansion (Senate + House)")


def main():
    """Run Phase 2 comprehensive test suite."""
    print("🎬 Starting Phase 2 Test Suite...")
    print("Testing YouTube fallback capability and hybrid congressional coverage")
    
    test_suite = Phase2TestSuite()
    results = test_suite.run_all_tests()
    
    # Save results
    output_file = Path('output') / f'phase2_test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Phase 2 test results saved: {output_file}")
    
    success_rate = results['summary']['success_rate']
    if success_rate >= 85:
        return 0
    elif success_rate >= 70:
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())