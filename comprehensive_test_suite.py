#!/usr/bin/env python3
"""
Comprehensive Test Suite for Senate Hearing Audio Capture System

This script runs the complete test suite including:
1. Multi-committee discovery
2. Audio quality analysis  
3. Dashboard data generation
4. System health checks
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import subprocess

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from api.data_service import DataService


def run_comprehensive_tests():
    """Run complete test suite and generate final report."""
    print("🎯 COMPREHENSIVE SENATE HEARING SYSTEM TEST")
    print("=" * 60)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'tests_run': [],
        'summary': {},
        'recommendations': []
    }
    
    # Test 1: Committee Discovery
    print("\n📋 TEST 1: COMMITTEE DISCOVERY")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            sys.executable, 'src/committee_discovery.py'
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Committee discovery completed successfully")
            report['tests_run'].append({
                'name': 'Committee Discovery',
                'status': 'success',
                'details': 'Found ISVP compatibility across committees'
            })
        else:
            print(f"❌ Committee discovery failed: {result.stderr}")
            report['tests_run'].append({
                'name': 'Committee Discovery', 
                'status': 'failed',
                'error': result.stderr
            })
    except Exception as e:
        print(f"❌ Committee discovery error: {e}")
        report['tests_run'].append({
            'name': 'Committee Discovery',
            'status': 'error', 
            'error': str(e)
        })
    
    # Test 2: Audio Quality Analysis
    print("\n🎵 TEST 2: AUDIO QUALITY ANALYSIS")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            sys.executable, 'src/audio_quality_tester.py'
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Audio quality analysis completed")
            report['tests_run'].append({
                'name': 'Audio Quality Analysis',
                'status': 'success',
                'details': 'Quality metrics calculated for all audio files'
            })
        else:
            print(f"❌ Audio quality analysis failed: {result.stderr}")
            report['tests_run'].append({
                'name': 'Audio Quality Analysis',
                'status': 'failed', 
                'error': result.stderr
            })
    except Exception as e:
        print(f"❌ Audio quality analysis error: {e}")
        report['tests_run'].append({
            'name': 'Audio Quality Analysis',
            'status': 'error',
            'error': str(e)
        })
    
    # Test 3: Dashboard Data Service
    print("\n📊 TEST 3: DASHBOARD DATA SERVICE")
    print("-" * 40)
    
    try:
        data_service = DataService()
        dashboard_data = data_service.get_dashboard_data()
        
        print(f"✅ Dashboard data service working")
        print(f"   - Total extractions: {dashboard_data['summary']['total_extractions']}")
        print(f"   - Success rate: {dashboard_data['summary']['success_rate']}%")
        print(f"   - Total audio: {dashboard_data['summary']['total_duration_hours']} hours")
        
        report['tests_run'].append({
            'name': 'Dashboard Data Service',
            'status': 'success',
            'details': f"Loaded {dashboard_data['summary']['total_extractions']} extraction records"
        })
        
        report['summary']['dashboard_data'] = dashboard_data['summary']
        
    except Exception as e:
        print(f"❌ Dashboard data service error: {e}")
        report['tests_run'].append({
            'name': 'Dashboard Data Service',
            'status': 'error',
            'error': str(e)
        })
    
    # Test 4: System Health Check
    print("\n🔧 TEST 4: SYSTEM HEALTH CHECK")
    print("-" * 40)
    
    health_issues = []
    
    # Check FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg available")
    except:
        print("❌ FFmpeg not available") 
        health_issues.append("FFmpeg not installed")
    
    # Check Python dependencies
    try:
        import librosa, requests, playwright
        print("✅ Required Python packages available")
    except ImportError as e:
        print(f"❌ Missing Python package: {e}")
        health_issues.append(f"Missing Python package: {e}")
    
    # Check output directory and files
    output_dir = Path('output')
    if output_dir.exists():
        audio_files = list(output_dir.glob('*.mp3')) + list(output_dir.glob('*.wav'))
        result_files = list(output_dir.glob('results_*.json'))
        
        print(f"✅ Output directory exists with {len(audio_files)} audio files and {len(result_files)} result files")
    else:
        print("❌ Output directory missing")
        health_issues.append("Output directory missing")
    
    if health_issues:
        report['tests_run'].append({
            'name': 'System Health Check',
            'status': 'warning',
            'issues': health_issues
        })
    else:
        report['tests_run'].append({
            'name': 'System Health Check', 
            'status': 'success',
            'details': 'All system components available'
        })
    
    # Generate final summary and recommendations
    print("\n🎯 FINAL SUMMARY & RECOMMENDATIONS")
    print("=" * 50)
    
    successful_tests = len([t for t in report['tests_run'] if t['status'] == 'success'])
    total_tests = len(report['tests_run'])
    
    print(f"Tests passed: {successful_tests}/{total_tests}")
    
    # Load latest committee discovery results
    try:
        discovery_files = list(Path('output').glob('committee_discovery_*.json'))
        if discovery_files:
            latest_discovery = max(discovery_files, key=lambda x: x.stat().st_mtime)
            with open(latest_discovery) as f:
                discovery_data = json.load(f)
            
            compatible_committees = discovery_data['committees_isvp_compatible']
            print(f"ISVP compatible committees: {compatible_committees}")
            
            report['summary']['committee_discovery'] = {
                'total_analyzed': discovery_data['committees_analyzed'],
                'accessible': discovery_data['committees_accessible'], 
                'isvp_compatible': compatible_committees
            }
    except Exception as e:
        print(f"Could not load committee discovery data: {e}")
    
    # Load latest audio quality results
    try:
        quality_files = list(Path('output').glob('audio_quality_analysis_*.json'))
        if quality_files:
            latest_quality = max(quality_files, key=lambda x: x.stat().st_mtime)
            with open(latest_quality) as f:
                quality_data = json.load(f)
            
            transcription_ready = quality_data['transcription_ready_count']
            total_files = quality_data['total_files']
            quality_rate = (transcription_ready / total_files * 100) if total_files > 0 else 0
            
            print(f"Audio quality: {transcription_ready}/{total_files} files transcription-ready ({quality_rate:.1f}%)")
            
            report['summary']['audio_quality'] = {
                'total_files': total_files,
                'transcription_ready': transcription_ready,
                'quality_rate': quality_rate
            }
    except Exception as e:
        print(f"Could not load audio quality data: {e}")
    
    # Generate recommendations
    recommendations = []
    
    if successful_tests == total_tests:
        recommendations.append("✅ System is fully operational and ready for production deployment")
    else:
        recommendations.append("⚠️ Some test failures detected - review logs before deployment")
    
    # Committee recommendations
    if 'committee_discovery' in report['summary']:
        compatible = report['summary']['committee_discovery']['isvp_compatible']
        if compatible >= 2:
            recommendations.append(f"🏛️ {compatible} committees support ISVP - ready for multi-committee expansion")
        elif compatible == 1:
            recommendations.append("🏛️ Limited committee support - expand gradually")
        else:
            recommendations.append("🏛️ No additional ISVP support found - focus on Commerce Committee")
    
    # Audio quality recommendations  
    if 'audio_quality' in report['summary']:
        quality_rate = report['summary']['audio_quality']['quality_rate']
        if quality_rate >= 80:
            recommendations.append("🎵 Excellent audio quality - ready for transcription pipelines")
        elif quality_rate >= 60:
            recommendations.append("🎵 Good audio quality - minor optimization needed")
        else:
            recommendations.append("🎵 Audio quality issues detected - review compression settings")
    
    # Next steps
    recommendations.append("🚀 Next steps: Deploy dashboard, set up monitoring, add transcription")
    
    report['recommendations'] = recommendations
    
    for rec in recommendations:
        print(f"   {rec}")
    
    # Save comprehensive report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = Path('output') / f'comprehensive_test_report_{timestamp}.json'
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Comprehensive report saved: {report_file}")
    
    return report


if __name__ == "__main__":
    report = run_comprehensive_tests()
    
    # Exit with appropriate code
    failed_tests = len([t for t in report['tests_run'] if t['status'] in ['failed', 'error']])
    sys.exit(failed_tests)