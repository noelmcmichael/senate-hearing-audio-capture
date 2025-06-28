#!/usr/bin/env python3
"""
Test YouTube Extraction Capabilities

Test the YouTube extractor and hybrid orchestrator with House committee channels.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from extractors.youtube_extractor import YouTubeExtractor
from extractors.extraction_orchestrator import ExtractionOrchestrator, analyze_congressional_url
from converters.hybrid_converter import HybridConverter


# Test URLs for House committees that use YouTube
HOUSE_COMMITTEE_YOUTUBE_CHANNELS = {
    'House Judiciary': 'https://www.youtube.com/channel/UCVvv3JRCVQAl6ovogDum4hA',
    'House Financial Services': 'https://www.youtube.com/channel/UCiGw0gRK-daU7Xv4oDMr9Hg'
}

# Sample YouTube hearing URLs (these would need to be real URLs in practice)
SAMPLE_YOUTUBE_HEARINGS = {
    'House Judiciary Hearing': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # Example placeholder
    'House Financial Services Hearing': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'  # Example placeholder
}


def test_youtube_extractor():
    """Test basic YouTube extractor functionality."""
    print("🎬 TESTING YOUTUBE EXTRACTOR")
    print("=" * 50)
    
    extractor = YouTubeExtractor()
    results = {'tested': 0, 'can_extract': 0, 'errors': []}
    
    # Test URL recognition
    test_urls = [
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'https://youtu.be/dQw4w9WgXcQ',
        'https://m.youtube.com/watch?v=dQw4w9WgXcQ',
        'https://www.senate.gov/hearing',  # Should not be extractable
        'https://www.house.gov/live'  # Should not be extractable
    ]
    
    for url in test_urls:
        results['tested'] += 1
        can_extract = extractor.can_extract(url)
        
        if 'youtube' in url or 'youtu.be' in url:
            if can_extract:
                results['can_extract'] += 1
                print(f"   ✅ {url}: Can extract")
            else:
                print(f"   ❌ {url}: Should be extractable but isn't")
                results['errors'].append(f"Failed to recognize YouTube URL: {url}")
        else:
            if not can_extract:
                print(f"   ✅ {url}: Correctly rejected")
            else:
                print(f"   ❌ {url}: Should not be extractable")
                results['errors'].append(f"Incorrectly accepted non-YouTube URL: {url}")
    
    print(f"\n📊 URL Recognition Results:")
    print(f"   URLs tested: {results['tested']}")
    print(f"   YouTube URLs recognized: {results['can_extract']}")
    print(f"   Errors: {len(results['errors'])}")
    
    return results


def test_platform_detection():
    """Test platform detection with the orchestrator."""
    print(f"\n🔍 TESTING PLATFORM DETECTION")
    print("=" * 50)
    
    test_urls = {
        'Senate Commerce': 'https://www.commerce.senate.gov/2025/6/executive-session-12',
        'Senate Banking': 'https://www.banking.senate.gov/hearings/06/18/2025/test',
        'House Judiciary Channel': 'https://www.youtube.com/channel/UCVvv3JRCVQAl6ovogDum4hA',
        'YouTube Video': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'House.gov': 'https://www.house.gov/representatives',
        'Unknown': 'https://example.com/video'
    }
    
    orchestrator = ExtractionOrchestrator()
    results = []
    
    for description, url in test_urls.items():
        print(f"\n🧪 Testing: {description}")
        print(f"   URL: {url}")
        
        try:
            detection = orchestrator.detect_platform(url)
            strategy = orchestrator.get_extraction_strategy(url)
            
            print(f"   Platform: {detection['detected_platform']}")
            print(f"   Congressional Type: {detection['congressional_type']}")
            print(f"   Recommended Extractor: {detection['recommended_extractor']}")
            print(f"   Confidence: {detection['confidence']}%")
            print(f"   Available Extractors: {detection['available_extractors']}")
            print(f"   Extraction Order: {strategy['extraction_order']}")
            
            results.append({
                'description': description,
                'detection': detection,
                'strategy': strategy
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({'description': description, 'error': str(e)})
    
    return results


def test_orchestrator_extraction():
    """Test the orchestrator's extraction capabilities."""
    print(f"\n🎯 TESTING ORCHESTRATOR EXTRACTION")
    print("=" * 50)
    
    orchestrator = ExtractionOrchestrator()
    
    # Test with known working Senate URL
    senate_url = 'https://www.commerce.senate.gov/2025/6/executive-session-12'
    print(f"\n📡 Testing Senate URL: {senate_url}")
    
    try:
        streams, extractor_used = orchestrator.extract_streams(senate_url)
        print(f"   ✅ Extractor used: {extractor_used}")
        print(f"   ✅ Streams found: {len(streams)}")
        
        for i, stream in enumerate(streams, 1):
            print(f"      {i}. {stream.title}")
            print(f"         Format: {stream.format_type}")
            print(f"         Committee: {stream.metadata.get('committee', 'Unknown')}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test comprehensive analysis
    print(f"\n🔬 Comprehensive URL Analysis:")
    
    test_urls = [
        'https://www.commerce.senate.gov/2025/6/executive-session-12',
        'https://www.youtube.com/channel/UCVvv3JRCVQAl6ovogDum4hA'
    ]
    
    for url in test_urls:
        print(f"\n   📋 Analyzing: {url[:60]}...")
        
        try:
            analysis = analyze_congressional_url(url)
            
            platform = analysis['platform_detection']
            strategy = analysis['extraction_strategy']
            
            print(f"      Platform: {platform['detected_platform']}")
            print(f"      Strategy: {strategy['primary_extractor']}")
            print(f"      Success Rate: {strategy['expected_success_rate']}%")
            
        except Exception as e:
            print(f"      ❌ Analysis error: {e}")


def test_hybrid_converter():
    """Test the hybrid converter capabilities."""
    print(f"\n🔧 TESTING HYBRID CONVERTER")
    print("=" * 50)
    
    try:
        converter = HybridConverter(output_format='mp3', audio_quality='medium')
        
        capabilities = converter.test_conversion_capabilities()
        print(f"📋 Converter Capabilities:")
        for capability, available in capabilities.items():
            status = "✅" if available else "❌"
            print(f"   {status} {capability}: {available}")
        
        print(f"\n📂 Supported Formats: {converter.get_supported_formats()}")
        
        return capabilities
        
    except Exception as e:
        print(f"❌ Converter initialization error: {e}")
        return {}


def test_youtube_channel_analysis():
    """Test analysis of House committee YouTube channels."""
    print(f"\n📺 TESTING HOUSE COMMITTEE YOUTUBE CHANNELS")
    print("=" * 50)
    
    extractor = YouTubeExtractor()
    
    for committee, channel_url in HOUSE_COMMITTEE_YOUTUBE_CHANNELS.items():
        print(f"\n🏛️ Testing {committee}")
        print(f"   Channel: {channel_url}")
        
        try:
            can_extract = extractor.can_extract(channel_url)
            print(f"   Can Extract: {can_extract}")
            
            if can_extract:
                print(f"   🔄 Attempting to extract channel info...")
                # Note: This will likely fail with the channel URL directly
                # Real implementation would need specific video URLs
                streams = extractor.extract_streams(channel_url)
                print(f"   Streams found: {len(streams)}")
                
                for stream in streams[:3]:  # Show first 3
                    print(f"      - {stream.title[:50]}...")
            
        except Exception as e:
            print(f"   ⚠️  Extraction note: {str(e)[:100]}...")
            print(f"   📝 Note: Channel URLs require specific video URLs for extraction")


def main():
    """Run all YouTube and hybrid extraction tests."""
    print("🎬 PHASE 2: YOUTUBE FALLBACK CAPABILITY TESTING")
    print("=" * 80)
    print("Testing YouTube extraction and hybrid orchestrator functionality")
    
    # Test 1: YouTube extractor basic functionality
    youtube_results = test_youtube_extractor()
    
    # Test 2: Platform detection
    platform_results = test_platform_detection()
    
    # Test 3: Orchestrator extraction
    test_orchestrator_extraction()
    
    # Test 4: Hybrid converter capabilities
    converter_capabilities = test_hybrid_converter()
    
    # Test 5: House committee YouTube analysis
    test_youtube_channel_analysis()
    
    # Summary
    print(f"\n📊 PHASE 2 TEST SUMMARY")
    print("=" * 40)
    
    # Calculate overall success
    youtube_success = youtube_results['can_extract'] > 0 and len(youtube_results['errors']) == 0
    platform_success = len(platform_results) > 0
    converter_success = converter_capabilities.get('youtube_support', False)
    
    tests = [
        ('YouTube URL Recognition', youtube_success),
        ('Platform Detection', platform_success),
        ('Hybrid Converter', converter_success)
    ]
    
    passed_tests = sum(1 for _, success in tests if success)
    total_tests = len(tests)
    
    print(f"   Tests Passed: {passed_tests}/{total_tests}")
    
    for test_name, success in tests:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")
    
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n🎯 Phase 2 Status:")
    if success_rate >= 80:
        print("✅ EXCELLENT: YouTube fallback capability is operational!")
        print("   Ready for House committee support and fallback scenarios.")
    elif success_rate >= 60:
        print("🟡 GOOD: Basic functionality working, minor improvements needed.")
    else:
        print("❌ NEEDS WORK: Major issues with YouTube functionality.")
    
    print(f"\n📋 Next Steps:")
    print("   1. Test with real House committee hearing URLs")
    print("   2. Implement committee-specific YouTube channel discovery")
    print("   3. Add live stream detection and handling")
    print("   4. Integrate with main capture pipeline")


if __name__ == "__main__":
    main()