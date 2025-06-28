#!/usr/bin/env python3
"""
Comprehensive Multi-Committee Test Suite

Tests all aspects of the multi-committee ISVP extraction system.
"""

import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from extractors.isvp_extractor import ISVPExtractor
from committee_config import CommitteeResolver, get_committee_summary, SENATE_COMMITTEES


class MultiCommitteeTestSuite:
    """Comprehensive test suite for multi-committee functionality."""
    
    def __init__(self):
        self.extractor = ISVPExtractor()
        self.resolver = CommitteeResolver()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'success_rate': 0
            }
        }
    
    def test_committee_resolution(self) -> Dict[str, Any]:
        """Test committee identification and configuration."""
        print("🧭 Testing Committee Resolution...")
        
        test_urls = {
            'Commerce': 'https://www.commerce.senate.gov/2025/6/executive-session-12',
            'Banking': 'https://www.banking.senate.gov/hearings/06/18/2025/test',
            'Judiciary': 'https://www.judiciary.senate.gov/committee-activity/hearings/test',
            'Intelligence': 'https://www.intelligence.senate.gov/hearings/test'
        }
        
        results = {'passed': 0, 'total': 0, 'details': {}}
        
        for expected_committee, url in test_urls.items():
            results['total'] += 1
            identified = self.resolver.identify_committee(url)
            
            if identified == expected_committee:
                results['passed'] += 1
                status = "✅"
            else:
                status = "❌"
            
            results['details'][expected_committee] = {
                'url': url,
                'expected': expected_committee,
                'identified': identified,
                'passed': identified == expected_committee
            }
            
            print(f"   {status} {expected_committee}: {identified}")
        
        return results
    
    def test_stream_extraction(self) -> Dict[str, Any]:
        """Test stream extraction for all committees."""
        print("\n📡 Testing Stream Extraction...")
        
        test_hearings = {
            'Commerce': 'https://www.commerce.senate.gov/2025/6/executive-session-12',
            'Banking': 'https://www.banking.senate.gov/hearings/06/18/2025/the-semiannual-monetary-policy-report-to-the-congress',
            'Judiciary': 'https://www.judiciary.senate.gov/committee-activity/hearings/executive-business-meeting-06-26-2025',
            'Intelligence': 'https://www.intelligence.senate.gov/hearings/open-hearing-worldwide-threats'
        }
        
        results = {'passed': 0, 'total': 0, 'details': {}}
        
        for committee, url in test_hearings.items():
            results['total'] += 1
            print(f"   Testing {committee}...")
            
            try:
                streams = self.extractor.extract_streams(url)
                
                if streams and len(streams) > 0:
                    results['passed'] += 1
                    status = "✅"
                    details = {
                        'streams_found': len(streams),
                        'stream_types': [s.metadata.get('stream_type', 'unknown') for s in streams],
                        'passed': True
                    }
                else:
                    status = "❌"
                    details = {'streams_found': 0, 'passed': False, 'error': 'No streams found'}
                
            except Exception as e:
                status = "❌"
                details = {'passed': False, 'error': str(e)}
            
            results['details'][committee] = details
            print(f"      {status} {committee}: {details.get('streams_found', 0)} streams")
        
        return results
    
    def test_extractor_capabilities(self) -> Dict[str, Any]:
        """Test extractor can_extract method for all committees."""
        print("\n🔧 Testing Extractor Capabilities...")
        
        results = {'passed': 0, 'total': 0, 'details': {}}
        
        for committee_name, config in SENATE_COMMITTEES.items():
            if config.get('isvp_compatible'):
                results['total'] += 1
                test_url = f"{config['base_url']}/test-hearing"
                
                can_extract = self.extractor.can_extract(test_url)
                
                if can_extract:
                    results['passed'] += 1
                    status = "✅"
                else:
                    status = "❌"
                
                results['details'][committee_name] = {
                    'url': test_url,
                    'can_extract': can_extract,
                    'passed': can_extract
                }
                
                print(f"   {status} {committee_name}: {can_extract}")
        
        return results
    
    def test_configuration_consistency(self) -> Dict[str, Any]:
        """Test committee configuration consistency."""
        print("\n⚙️ Testing Configuration Consistency...")
        
        results = {'passed': 0, 'total': 0, 'details': {}}
        
        # Test 1: All ISVP-compatible committees have required fields
        required_fields = ['stream_id', 'url_pattern', 'archive_pattern']
        
        for committee_name, config in SENATE_COMMITTEES.items():
            if config.get('isvp_compatible'):
                results['total'] += 1
                
                missing_fields = [field for field in required_fields if not config.get(field)]
                
                if not missing_fields:
                    results['passed'] += 1
                    status = "✅"
                else:
                    status = "❌"
                
                results['details'][committee_name] = {
                    'missing_fields': missing_fields,
                    'passed': len(missing_fields) == 0
                }
                
                print(f"   {status} {committee_name}: {len(missing_fields)} missing fields")
        
        return results
    
    def test_dashboard_integration(self) -> Dict[str, Any]:
        """Test dashboard API integration."""
        print("\n📊 Testing Dashboard Integration...")
        
        results = {'passed': 0, 'total': 1, 'details': {}}
        
        try:
            # Import and test data service
            from api.data_service import DataService
            
            service = DataService()
            dashboard_data = service.get_dashboard_data()
            
            # Check required fields
            required_fields = ['summary', 'committee_stats', 'committee_coverage', 'recent_extractions']
            missing_fields = [field for field in required_fields if field not in dashboard_data]
            
            if not missing_fields:
                results['passed'] = 1
                status = "✅"
                
                # Check committee coverage data
                coverage = dashboard_data.get('committee_coverage', {})
                coverage_checks = {
                    'has_total_committees': 'total_committees' in coverage,
                    'has_isvp_compatible': 'isvp_compatible' in coverage,
                    'has_coverage_percentage': 'coverage_percentage' in coverage
                }
                
                details = {
                    'missing_fields': missing_fields,
                    'coverage_checks': coverage_checks,
                    'passed': True
                }
            else:
                status = "❌"
                details = {'missing_fields': missing_fields, 'passed': False}
            
        except Exception as e:
            status = "❌"
            details = {'error': str(e), 'passed': False}
        
        results['details']['dashboard_api'] = details
        print(f"   {status} Dashboard API: {details.get('passed', False)}")
        
        return results
    
    def test_system_health(self) -> Dict[str, Any]:
        """Test overall system health."""
        print("\n🏥 Testing System Health...")
        
        results = {'passed': 0, 'total': 0, 'details': {}}
        
        # Test 1: Dependencies available
        dependencies = ['ffmpeg', 'playwright']
        
        for dep in dependencies:
            results['total'] += 1
            
            try:
                if dep == 'ffmpeg':
                    result = subprocess.run(['ffmpeg', '-version'], 
                                          capture_output=True, timeout=5)
                    available = result.returncode == 0
                elif dep == 'playwright':
                    # Check if playwright is importable
                    import playwright
                    available = True
                else:
                    available = False
                
                if available:
                    results['passed'] += 1
                    status = "✅"
                else:
                    status = "❌"
                
            except Exception:
                status = "❌"
                available = False
            
            results['details'][dep] = {'available': available, 'passed': available}
            print(f"   {status} {dep}: {available}")
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        print("🧪 MULTI-COMMITTEE TEST SUITE")
        print("=" * 60)
        
        # Run all test categories
        test_methods = [
            ('committee_resolution', self.test_committee_resolution),
            ('stream_extraction', self.test_stream_extraction),
            ('extractor_capabilities', self.test_extractor_capabilities),
            ('configuration_consistency', self.test_configuration_consistency),
            ('dashboard_integration', self.test_dashboard_integration),
            ('system_health', self.test_system_health)
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
        
        # Print summary
        self.print_summary()
        
        return self.results
    
    def print_summary(self):
        """Print test summary."""
        print(f"\n📊 TEST SUITE SUMMARY")
        print("=" * 40)
        
        summary = self.results['summary']
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']}")
        print(f"   Failed: {summary['failed_tests']}")
        print(f"   Success Rate: {summary['success_rate']}%")
        
        # Test category results
        print(f"\n📋 Test Category Results:")
        for test_name, test_result in self.results['tests'].items():
            passed = test_result['passed']
            total = test_result['total']
            rate = round((passed / total) * 100, 1) if total > 0 else 0
            status = "✅" if rate == 100 else "🟡" if rate >= 50 else "❌"
            
            print(f"   {status} {test_name.replace('_', ' ').title()}: {passed}/{total} ({rate}%)")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if summary['success_rate'] >= 90:
            print("✅ EXCELLENT: System is fully operational and ready for production!")
        elif summary['success_rate'] >= 75:
            print("🟡 GOOD: System is mostly working with minor issues to address.")
        elif summary['success_rate'] >= 50:
            print("⚠️  FAIR: System has significant issues that need attention.")
        else:
            print("❌ POOR: System requires major fixes before deployment.")
    
    def save_results(self, filename: str = None):
        """Save test results to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"multi_committee_test_results_{timestamp}.json"
        
        output_file = Path('output') / filename
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Test results saved: {output_file}")


def main():
    """Run the multi-committee test suite."""
    print("🎯 Starting Multi-Committee Test Suite...")
    print("This will test all aspects of the Phase 1 implementation.")
    
    test_suite = MultiCommitteeTestSuite()
    results = test_suite.run_all_tests()
    test_suite.save_results()
    
    # Return exit code based on success rate
    success_rate = results['summary']['success_rate']
    if success_rate >= 90:
        return 0  # Success
    elif success_rate >= 75:
        return 1  # Warning
    else:
        return 2  # Error


if __name__ == "__main__":
    sys.exit(main())