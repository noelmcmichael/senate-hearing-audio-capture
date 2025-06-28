#!/usr/bin/env python3
"""
Test script for Phase 7B Enhanced UI system.
Tests the integrated hearing management, system monitoring, and enhanced APIs.
"""

import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import time
import requests

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from api.database_enhanced import EnhancedUIDatabase
from api.hearing_management import HearingManagementAPI
from api.system_monitoring import SystemMonitoringAPI

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase7BTestSuite:
    """Comprehensive test suite for Phase 7B Enhanced UI"""
    
    def __init__(self):
        self.db = None
        self.hearing_api = None
        self.monitoring_api = None
        self.test_results = {
            'database_tests': [],
            'api_tests': [],
            'ui_tests': [],
            'integration_tests': []
        }
    
    def setup_test_environment(self):
        """Setup test environment and database"""
        logger.info("Setting up Phase 7B test environment...")
        
        try:
            # Initialize enhanced database
            self.db = EnhancedUIDatabase("data/test_hearings_enhanced.db")
            logger.info("✅ Enhanced database initialized")
            
            # Initialize APIs
            self.hearing_api = HearingManagementAPI()
            self.monitoring_api = SystemMonitoringAPI()
            logger.info("✅ API services initialized")
            
            # Create test data
            self._create_test_data()
            logger.info("✅ Test data created")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {str(e)}")
            return False
    
    def _create_test_data(self):
        """Create test data for Phase 7B features"""
        
        # Create test user sessions
        session_ids = []
        for i, role in enumerate(['admin', 'reviewer', 'quality_controller']):
            session_id = self.db.create_user_session(f"test_user_{i}", role)
            session_ids.append(session_id)
        
        logger.info(f"Created {len(session_ids)} test user sessions")
        
        # Create test hearings (simulate Phase 7A sync results)
        test_hearings = [
            {
                'committee_code': 'SCOM',
                'hearing_title': 'Oversight of Federal Maritime Administration',
                'hearing_date': (datetime.now() + timedelta(days=1)).isoformat()[:10],
                'hearing_type': 'Oversight Hearing',
                'source_api': 1,
                'source_website': 1,
                'streams': '{"isvp": "http://example.com/stream1", "youtube": "http://youtube.com/watch?v=test1"}',
                'sync_confidence': 0.95
            },
            {
                'committee_code': 'SSJU',
                'hearing_title': 'Executive Session - Judicial Nominations',
                'hearing_date': datetime.now().isoformat()[:10],
                'hearing_type': 'Executive Session',
                'source_api': 1,
                'source_website': 0,
                'streams': '{"isvp": "http://example.com/stream2"}',
                'sync_confidence': 0.87
            },
            {
                'committee_code': 'SSCI',
                'hearing_title': 'Annual Threat Assessment Briefing',
                'hearing_date': (datetime.now() - timedelta(days=1)).isoformat()[:10],
                'hearing_type': 'Briefing',
                'source_api': 0,
                'source_website': 1,
                'streams': '{}',
                'sync_confidence': 0.72
            }
        ]
        
        hearing_ids = []
        for hearing_data in test_hearings:
            # Insert hearing into database
            cursor = self.db.connection.execute("""
                INSERT INTO hearings_unified 
                (committee_code, hearing_title, hearing_date, hearing_type,
                 source_api, source_website, streams, sync_confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                hearing_data['committee_code'], hearing_data['hearing_title'],
                hearing_data['hearing_date'], hearing_data['hearing_type'],
                hearing_data['source_api'], hearing_data['source_website'],
                hearing_data['streams'], hearing_data['sync_confidence']
            ))
            
            hearing_ids.append(cursor.lastrowid)
        
        self.db.connection.commit()
        logger.info(f"Created {len(hearing_ids)} test hearings")
        
        # Create test review assignments
        for i, hearing_id in enumerate(hearing_ids):
            assignment_id = self.db.create_review_assignment(
                hearing_id=str(hearing_id),
                assigned_to=f"test_user_{i % 2}",
                priority=5 + i
            )
        
        logger.info(f"Created {len(hearing_ids)} review assignments")
        
        # Create test alerts
        test_alerts = [
            {
                'alert_type': 'sync_failure',
                'severity': 'high',
                'title': 'SSCI Website Scraper Failed',
                'description': 'Unable to connect to Senate Intelligence Committee website',
                'component': 'scraper',
                'auto_resolvable': False
            },
            {
                'alert_type': 'quality_degradation',
                'severity': 'medium',
                'title': 'Transcript Accuracy Below Threshold',
                'description': 'Speaker identification accuracy dropped to 82%',
                'component': 'transcription',
                'auto_resolvable': True
            },
            {
                'alert_type': 'api_limit',
                'severity': 'medium',
                'title': 'Congress API Rate Limit Warning',
                'description': 'Daily API usage at 85% of limit',
                'component': 'api',
                'auto_resolvable': True
            }
        ]
        
        for alert_data in test_alerts:
            self.db.create_alert(**alert_data)
        
        logger.info(f"Created {len(test_alerts)} test alerts")
        
        # Create test quality metrics
        metrics = [
            ('accuracy_score', 87.3, 85.0),
            ('review_speed', 15.2, 18.5),
            ('correction_count', 12.5, 15.0)
        ]
        
        for metric_type, value, baseline in metrics:
            self.db.record_quality_metric(
                metric_type=metric_type,
                metric_value=value,
                baseline_value=baseline
            )
        
        logger.info(f"Created {len(metrics)} quality metrics")
        
        # Update sync status
        self.db.update_sync_status(
            component='congress_api',
            status='healthy',
            committee_code='SCOM',
            performance_metrics={'success_rate': 96.5, 'avg_response_time': 245}
        )
        
        self.db.update_sync_status(
            component='committee_scraper',
            status='warning',
            committee_code='SSCI',
            error_message='Connection timeout',
            performance_metrics={'success_rate': 89.2, 'last_attempt': datetime.now().isoformat()}
        )
        
        logger.info("Created sync status entries")
    
    def test_database_functionality(self):
        """Test enhanced database functionality"""
        logger.info("\n🧪 Testing Enhanced Database Functionality...")
        
        tests = [
            self._test_user_sessions,
            self._test_review_assignments,
            self._test_system_alerts,
            self._test_quality_metrics,
            self._test_sync_status
        ]
        
        for test in tests:
            try:
                result = test()
                self.test_results['database_tests'].append(result)
                status = "✅" if result['passed'] else "❌"
                logger.info(f"{status} {result['name']}: {result['message']}")
            except Exception as e:
                self.test_results['database_tests'].append({
                    'name': test.__name__,
                    'passed': False,
                    'message': f"Exception: {str(e)}"
                })
                logger.error(f"❌ {test.__name__}: {str(e)}")
    
    def _test_user_sessions(self):
        """Test user session management"""
        # Create session
        session_id = self.db.create_user_session("test_user", "admin")
        
        # Validate session
        session_data = self.db.validate_session(session_id)
        
        if session_data and session_data['user_id'] == 'test_user':
            return {'name': 'User Sessions', 'passed': True, 'message': 'Session creation and validation working'}
        else:
            return {'name': 'User Sessions', 'passed': False, 'message': 'Session validation failed'}
    
    def _test_review_assignments(self):
        """Test review assignment management"""
        # Get review queue
        queue = self.db.get_review_queue(limit=10)
        
        if len(queue) >= 3:  # We created 3 test assignments
            return {'name': 'Review Assignments', 'passed': True, 'message': f'Found {len(queue)} assignments in queue'}
        else:
            return {'name': 'Review Assignments', 'passed': False, 'message': f'Expected >= 3 assignments, found {len(queue)}'}
    
    def _test_system_alerts(self):
        """Test system alert management"""
        # Get active alerts
        alerts = self.db.get_active_alerts()
        
        if len(alerts) >= 3:  # We created 3 test alerts
            # Test alert resolution
            alert_id = alerts[0]['alert_id']
            success = self.db.resolve_alert(alert_id, "test_user")
            
            if success:
                return {'name': 'System Alerts', 'passed': True, 'message': f'Found {len(alerts)} alerts, resolution working'}
            else:
                return {'name': 'System Alerts', 'passed': False, 'message': 'Alert resolution failed'}
        else:
            return {'name': 'System Alerts', 'passed': False, 'message': f'Expected >= 3 alerts, found {len(alerts)}'}
    
    def _test_quality_metrics(self):
        """Test quality metrics recording and retrieval"""
        # Get quality trends
        trends = self.db.get_quality_trends('accuracy_score', days=30)
        
        if len(trends) > 0:
            return {'name': 'Quality Metrics', 'passed': True, 'message': f'Found {len(trends)} metric entries'}
        else:
            return {'name': 'Quality Metrics', 'passed': False, 'message': 'No quality metrics found'}
    
    def _test_sync_status(self):
        """Test sync status tracking"""
        # Get sync health
        health = self.db.get_sync_health()
        
        if health and 'components' in health:
            component_count = len(health['components'])
            return {'name': 'Sync Status', 'passed': True, 'message': f'Found {component_count} sync components'}
        else:
            return {'name': 'Sync Status', 'passed': False, 'message': 'Sync health data not found'}
    
    def test_api_functionality(self):
        """Test API functionality"""
        logger.info("\n🧪 Testing API Functionality...")
        
        tests = [
            self._test_hearing_queue_api,
            self._test_system_health_api,
            self._test_duplicate_resolution_api
        ]
        
        for test in tests:
            try:
                result = test()
                self.test_results['api_tests'].append(result)
                status = "✅" if result['passed'] else "❌"
                logger.info(f"{status} {result['name']}: {result['message']}")
            except Exception as e:
                self.test_results['api_tests'].append({
                    'name': test.__name__,
                    'passed': False,
                    'message': f"Exception: {str(e)}"
                })
                logger.error(f"❌ {test.__name__}: {str(e)}")
    
    def _test_hearing_queue_api(self):
        """Test hearing queue API"""
        # Get hearing queue
        queue_data = self.hearing_api.get_hearing_queue(limit=10)
        
        if 'hearings' in queue_data and len(queue_data['hearings']) > 0:
            hearing_count = len(queue_data['hearings'])
            return {'name': 'Hearing Queue API', 'passed': True, 'message': f'Retrieved {hearing_count} hearings'}
        else:
            return {'name': 'Hearing Queue API', 'passed': False, 'message': 'No hearings found in queue'}
    
    def _test_system_health_api(self):
        """Test system health API"""
        # Get system health
        health_data = self.monitoring_api.get_system_health()
        
        if 'overall_status' in health_data and 'sync_health' in health_data:
            status = health_data['overall_status']
            return {'name': 'System Health API', 'passed': True, 'message': f'System status: {status}'}
        else:
            return {'name': 'System Health API', 'passed': False, 'message': 'Health data incomplete'}
    
    def _test_duplicate_resolution_api(self):
        """Test duplicate resolution API"""
        # Get duplicate queue
        duplicates = self.hearing_api.get_duplicate_queue(limit=10)
        
        if 'duplicate_pairs' in duplicates:
            duplicate_count = len(duplicates['duplicate_pairs'])
            return {'name': 'Duplicate Resolution API', 'passed': True, 'message': f'Found {duplicate_count} potential duplicates'}
        else:
            return {'name': 'Duplicate Resolution API', 'passed': False, 'message': 'Duplicate queue not accessible'}
    
    def test_ui_integration(self):
        """Test UI integration by starting the FastAPI server"""
        logger.info("\n🧪 Testing UI Integration...")
        
        try:
            # Start the FastAPI server in the background
            logger.info("Starting FastAPI server...")
            
            import subprocess
            import time
            
            # Start the server
            proc = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "src.api.main_app:app", 
                "--host", "0.0.0.0", 
                "--port", "8002",
                "--reload"
            ], cwd=Path(__file__).parent)
            
            # Wait for server to start
            time.sleep(5)
            
            # Test API endpoints
            base_url = "http://localhost:8002"
            endpoints_to_test = [
                "/api",
                "/api/overview",
                "/api/stats",
                "/api/hearings/queue",
                "/api/system/health"
            ]
            
            test_results = []
            for endpoint in endpoints_to_test:
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=10)
                    if response.status_code == 200:
                        test_results.append(f"✅ {endpoint}: {response.status_code}")
                    else:
                        test_results.append(f"❌ {endpoint}: {response.status_code}")
                except Exception as e:
                    test_results.append(f"❌ {endpoint}: {str(e)}")
            
            # Stop the server
            proc.terminate()
            proc.wait()
            
            success_count = sum(1 for result in test_results if "✅" in result)
            total_count = len(test_results)
            
            self.test_results['ui_tests'] = test_results
            
            if success_count == total_count:
                logger.info(f"✅ UI Integration: All {total_count} endpoints working")
                return True
            else:
                logger.warning(f"⚠️ UI Integration: {success_count}/{total_count} endpoints working")
                for result in test_results:
                    logger.info(f"  {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ UI Integration test failed: {str(e)}")
            return False
    
    def test_integration_workflows(self):
        """Test complete integration workflows"""
        logger.info("\n🧪 Testing Integration Workflows...")
        
        workflows = [
            self._test_hearing_discovery_to_review_workflow,
            self._test_alert_resolution_workflow,
            self._test_quality_monitoring_workflow
        ]
        
        for workflow in workflows:
            try:
                result = workflow()
                self.test_results['integration_tests'].append(result)
                status = "✅" if result['passed'] else "❌"
                logger.info(f"{status} {result['name']}: {result['message']}")
            except Exception as e:
                self.test_results['integration_tests'].append({
                    'name': workflow.__name__,
                    'passed': False,
                    'message': f"Exception: {str(e)}"
                })
                logger.error(f"❌ {workflow.__name__}: {str(e)}")
    
    def _test_hearing_discovery_to_review_workflow(self):
        """Test complete hearing discovery to review workflow"""
        
        # 1. Get hearing from queue
        queue_data = self.hearing_api.get_hearing_queue(limit=1)
        if not queue_data['hearings']:
            return {'name': 'Hearing Discovery Workflow', 'passed': False, 'message': 'No hearings in queue'}
        
        hearing = queue_data['hearings'][0]
        hearing_id = hearing['id']
        
        # 2. Update hearing priority
        priority_result = self.hearing_api.update_hearing_priority(
            hearing_id=hearing_id,
            priority=8,
            user_id="test_user",
            reason="Test workflow"
        )
        
        # 3. Check if assignment was created/updated
        assignments = self.db.get_review_queue(limit=10)
        assignment_found = any(a['hearing_id'] == hearing_id for a in assignments)
        
        if assignment_found and priority_result:
            return {'name': 'Hearing Discovery Workflow', 'passed': True, 'message': 'Complete workflow successful'}
        else:
            return {'name': 'Hearing Discovery Workflow', 'passed': False, 'message': 'Workflow incomplete'}
    
    def _test_alert_resolution_workflow(self):
        """Test alert creation and resolution workflow"""
        
        # 1. Create test alert
        alert_id = self.db.create_alert(
            alert_type="system_error",
            severity="medium",
            title="Test Alert for Workflow",
            description="This is a test alert for workflow testing",
            component="test",
            auto_resolvable=True
        )
        
        # 2. Get active alerts
        alerts = self.monitoring_api.get_active_alerts()
        alert_found = any(a['alert_id'] == alert_id for a in alerts['alerts'])
        
        # 3. Resolve the alert
        resolution_result = self.monitoring_api.resolve_alert(
            alert_id=alert_id,
            user_id="test_user",
            resolution_notes="Resolved by test workflow"
        )
        
        if alert_found and resolution_result['resolved']:
            return {'name': 'Alert Resolution Workflow', 'passed': True, 'message': 'Alert workflow successful'}
        else:
            return {'name': 'Alert Resolution Workflow', 'passed': False, 'message': 'Alert workflow failed'}
    
    def _test_quality_monitoring_workflow(self):
        """Test quality monitoring and metrics workflow"""
        
        # 1. Record quality metric
        metric_id = self.db.record_quality_metric(
            metric_type="test_metric",
            metric_value=95.5,
            baseline_value=90.0
        )
        
        # 2. Get quality trends
        trends = self.db.get_quality_trends("test_metric", days=1)
        
        # 3. Check if metric appears in trends
        metric_found = len(trends) > 0
        
        if metric_id and metric_found:
            return {'name': 'Quality Monitoring Workflow', 'passed': True, 'message': 'Quality workflow successful'}
        else:
            return {'name': 'Quality Monitoring Workflow', 'passed': False, 'message': 'Quality workflow failed'}
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n📊 Generating Test Report...")
        
        total_tests = sum(len(tests) for tests in self.test_results.values())
        passed_tests = sum(
            sum(1 for test in tests if isinstance(test, dict) and test.get('passed', False))
            for tests in self.test_results.values()
        )
        
        # Add UI test results
        if self.test_results['ui_tests']:
            ui_passed = sum(1 for result in self.test_results['ui_tests'] if "✅" in str(result))
            total_tests += len(self.test_results['ui_tests'])
            passed_tests += ui_passed
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'phase': 'Phase 7B - Enhanced UI/UX Workflows',
            'test_date': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': round(success_rate, 1)
            },
            'test_results': self.test_results,
            'recommendations': []
        }
        
        # Add recommendations based on results
        if success_rate >= 90:
            report['recommendations'].append("✅ Phase 7B implementation is production-ready")
        elif success_rate >= 75:
            report['recommendations'].append("⚠️ Phase 7B has minor issues that should be addressed")
        else:
            report['recommendations'].append("❌ Phase 7B requires significant fixes before production")
        
        # Save report to file
        report_path = Path("PHASE_7B_TEST_REPORT.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Test report saved to {report_path}")
        
        # Print summary
        logger.info(f"\n🎯 Phase 7B Test Summary:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Passed: {passed_tests}")
        logger.info(f"   Failed: {total_tests - passed_tests}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        
        for category, tests in self.test_results.items():
            if category == 'ui_tests':
                category_passed = sum(1 for result in tests if "✅" in str(result))
                category_total = len(tests)
            else:
                category_passed = sum(1 for test in tests if test.get('passed', False))
                category_total = len(tests)
            
            if category_total > 0:
                category_rate = category_passed / category_total * 100
                logger.info(f"   {category.replace('_', ' ').title()}: {category_passed}/{category_total} ({category_rate:.1f}%)")
        
        return report
    
    def cleanup(self):
        """Clean up test resources"""
        if self.db:
            self.db.close()
        logger.info("🧹 Test cleanup completed")

def main():
    """Main test execution"""
    print("🚀 Starting Phase 7B Enhanced UI Test Suite")
    print("=" * 60)
    
    test_suite = Phase7BTestSuite()
    
    try:
        # Setup test environment
        if not test_suite.setup_test_environment():
            print("❌ Test setup failed. Exiting.")
            return 1
        
        # Run all test categories
        test_suite.test_database_functionality()
        test_suite.test_api_functionality()
        test_suite.test_ui_integration()
        test_suite.test_integration_workflows()
        
        # Generate report
        report = test_suite.generate_test_report()
        
        # Return appropriate exit code
        success_rate = report['summary']['success_rate']
        return 0 if success_rate >= 90 else 1
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n💥 Test suite failed with exception: {str(e)}")
        return 1
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    exit(main())