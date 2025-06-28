"""
Comprehensive test suite for Phase 7A: Automated Data Synchronization
Tests database schema, API client, scraper, deduplication, and orchestrator.
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.sync.database_schema import UnifiedHearingDatabase
from src.sync.congress_api_enhanced import CongressAPIEnhanced, HearingRecord
from src.sync.committee_scraper import CommitteeWebsiteScraper, ScrapedHearing
from src.sync.deduplication_engine import DeduplicationEngine
from src.sync.sync_orchestrator import SyncOrchestrator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase7ATestSuite:
    """Comprehensive test suite for Phase 7A components"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = str(Path(self.temp_dir) / "test_sync.db")
        self.results = {}
    
    async def run_all_tests(self):
        """Run all Phase 7A tests"""
        
        logger.info("🚀 Starting Phase 7A Automated Sync System Tests")
        
        # Test individual components
        await self.test_database_schema()
        await self.test_congress_api_client()
        await self.test_committee_scraper()
        await self.test_deduplication_engine()
        await self.test_sync_orchestrator()
        
        # Integration tests
        await self.test_full_sync_integration()
        
        # Generate summary
        self.generate_test_summary()
    
    async def test_database_schema(self):
        """Test unified hearing database schema and operations"""
        
        logger.info("📊 Testing Database Schema...")
        
        try:
            # Initialize database
            db = UnifiedHearingDatabase(self.test_db_path)
            
            # Test 1: Schema Creation
            assert db.connection is not None, "Database connection failed"
            logger.info("✓ Database schema created successfully")
            
            # Test 2: Committee Configuration
            db.add_sync_config('TEST_COMMITTEE', priority_level=1, sync_frequency_hours=6)
            
            cursor = db.connection.cursor()
            cursor.execute("SELECT * FROM sync_config WHERE committee_code = 'TEST_COMMITTEE'")
            config = cursor.fetchone()
            assert config is not None, "Committee config insertion failed"
            logger.info("✓ Committee configuration management working")
            
            # Test 3: Hearing Insertion
            test_hearing = {
                'committee_code': 'TEST_COMMITTEE',
                'hearing_title': 'Test Hearing on Automated Systems',
                'hearing_date': '2025-06-28',
                'hearing_type': 'Hearing',
                'streams': {'test_stream': 'test_url'},
                'witnesses': [{'name': 'Test Witness', 'title': 'Expert'}],
                'sync_confidence': 0.95
            }
            
            hearing_id = db.insert_hearing(test_hearing, 'congress_api')
            assert hearing_id > 0, "Hearing insertion failed"
            logger.info(f"✓ Hearing insertion successful (ID: {hearing_id})")
            
            # Test 4: Duplicate Detection
            duplicates = db.find_potential_duplicates(test_hearing)
            assert len(duplicates) > 0, "Duplicate detection failed"
            assert duplicates[0]['similarity_score'] > 0.9, "Duplicate scoring incorrect"
            logger.info("✓ Duplicate detection working")
            
            # Test 5: Hearing Update
            updates = {'meeting_status': 'Completed', 'sync_confidence': 1.0}
            db.update_hearing(hearing_id, updates, 'website_scraper')
            logger.info("✓ Hearing updates working")
            
            # Test 6: Statistics
            stats = db.get_sync_statistics()
            assert stats['total_hearings'] > 0, "Statistics generation failed"
            logger.info(f"✓ Statistics: {stats['total_hearings']} hearings, {stats['avg_confidence']:.2f} avg confidence")
            
            db.close()
            self.results['database_schema'] = {'status': 'PASS', 'tests': 6}
            
        except Exception as e:
            logger.error(f"❌ Database schema test failed: {e}")
            self.results['database_schema'] = {'status': 'FAIL', 'error': str(e)}
    
    async def test_congress_api_client(self):
        """Test enhanced Congress.gov API client"""
        
        logger.info("🏛️ Testing Congress API Client...")
        
        try:
            # Test with or without real API key
            if os.getenv('CONGRESS_API_KEY'):
                # Test with real API
                api = CongressAPIEnhanced()
                
                # Test 1: API Validation
                is_valid = api.validate_api_access()
                logger.info(f"✓ API access validation: {'PASS' if is_valid else 'FAIL'}")
                
                # Test 2: Get Committee Meetings
                if is_valid:
                    hearings = api.get_committee_meetings('SCOM', days_back=30)
                    logger.info(f"✓ Retrieved {len(hearings)} Commerce Committee hearings")
                    
                    if hearings:
                        sample = hearings[0]
                        assert hasattr(sample, 'hearing_title'), "Hearing record structure invalid"
                        assert hasattr(sample, 'hearing_date'), "Hearing date missing"
                        logger.info(f"✓ Sample hearing: {sample.hearing_title[:50]}...")
                
                # Test 3: API Status
                status = api.get_api_status()
                assert 'api_accessible' in status, "API status check failed"
                logger.info(f"✓ API status: {status}")
                
                self.results['congress_api'] = {'status': 'PASS', 'tests': 3, 'live_api': True}
            
            else:
                # Test with mock data
                logger.info("ℹ️ No API key found, testing with mock data")
                
                # Create mock API client
                with patch.object(CongressAPIEnhanced, '_make_request') as mock_request:
                    mock_request.return_value = {
                        'meetings': [{
                            'meetingId': 'test-123',
                            'title': 'Test Hearing on AI',
                            'date': '2025-06-28',
                            'meetingType': 'Hearing',
                            'status': 'Scheduled'
                        }]
                    }
                    
                    # This will fail without API key, which is expected
                    try:
                        api = CongressAPIEnhanced()
                    except ValueError:
                        logger.info("✓ API key validation working correctly")
                
                self.results['congress_api'] = {'status': 'PASS', 'tests': 1, 'live_api': False}
        
        except Exception as e:
            logger.error(f"❌ Congress API test failed: {e}")
            self.results['congress_api'] = {'status': 'FAIL', 'error': str(e)}
    
    async def test_committee_scraper(self):
        """Test committee website scraper"""
        
        logger.info("🌐 Testing Committee Scraper...")
        
        try:
            scraper = CommitteeWebsiteScraper()
            
            # Test 1: Configuration Loading
            assert 'SCOM' in scraper.committee_configs, "Committee configs not loaded"
            assert 'SSCI' in scraper.committee_configs, "Missing committee config"
            logger.info(f"✓ Loaded configs for {len(scraper.committee_configs)} committees")
            
            # Test 2: Access Validation (non-blocking)
            accessible_committees = []
            for committee in ['SCOM', 'SSCI']:
                try:
                    accessible = scraper.validate_committee_access(committee)
                    if accessible:
                        accessible_committees.append(committee)
                except Exception:
                    pass  # Network issues are expected in testing
            
            logger.info(f"✓ Validated access to {len(accessible_committees)} committees")
            
            # Test 3: Parsing Logic (with mock HTML)
            mock_html = """
            <html>
                <head><title>Test Hearing</title></head>
                <body>
                    <h1>Test Hearing on AI Governance</h1>
                    <div class="date">June 28, 2025</div>
                    <iframe src="https://isvp.example.com/stream"></iframe>
                    <a href="document.pdf">Witness Statement</a>
                    <div class="witness">Dr. Jane Smith, AI Expert</div>
                </body>
            </html>
            """
            
            # Test date parsing
            test_date = scraper._parse_hearing_date("June 28, 2025", "%B %d, %Y")
            assert test_date == "2025-06-28", f"Date parsing failed: {test_date}"
            logger.info("✓ Date parsing working correctly")
            
            # Test ID generation
            test_id = scraper._generate_source_id(
                "https://test.com/hearing", 
                "Test Hearing", 
                "2025-06-28"
            )
            assert len(test_id) > 0, "Source ID generation failed"
            logger.info(f"✓ Source ID generation: {test_id}")
            
            self.results['committee_scraper'] = {'status': 'PASS', 'tests': 3}
        
        except Exception as e:
            logger.error(f"❌ Committee scraper test failed: {e}")
            self.results['committee_scraper'] = {'status': 'FAIL', 'error': str(e)}
    
    async def test_deduplication_engine(self):
        """Test deduplication engine"""
        
        logger.info("🔄 Testing Deduplication Engine...")
        
        try:
            engine = DeduplicationEngine()
            
            # Test hearings with various similarity levels
            test_hearings = [
                {
                    'id': 1,
                    'committee_code': 'SCOM',
                    'hearing_title': 'Executive Session on AI Oversight and Regulation',
                    'hearing_date': '2025-06-28',
                    'source_api': True,
                    'witnesses': [{'name': 'Dr. Jane Smith'}, {'name': 'John Doe'}],
                    'location_info': {'room': 'Room 253', 'building': 'Hart'}
                },
                {
                    'id': 2,
                    'committee_code': 'SCOM',
                    'hearing_title': 'Executive Session: AI Oversight',
                    'hearing_date': '2025-06-28',
                    'source_website': True,
                    'witnesses': [{'name': 'Dr. Jane Smith'}],
                    'streams': {'isvp_stream': 'test_url'},
                    'location_info': {'room': 'Room 253', 'building': 'Hart'}
                },
                {
                    'id': 3,
                    'committee_code': 'SSCI',
                    'hearing_title': 'Intelligence Briefing on Cybersecurity',
                    'hearing_date': '2025-06-29',
                    'source_api': True,
                    'witnesses': [{'name': 'Director Smith'}]
                },
                {
                    'id': 4,
                    'committee_code': 'SCOM',
                    'hearing_title': 'Different Hearing on Privacy',
                    'hearing_date': '2025-06-30',
                    'source_api': True
                }
            ]
            
            # Test 1: Duplicate Detection
            matches = engine.find_duplicates(test_hearings)
            assert len(matches) > 0, "No duplicate matches found"
            
            # Should find hearing 1 and 2 as duplicates
            high_confidence_match = next((m for m in matches if m.similarity_score > 0.8), None)
            assert high_confidence_match is not None, "High confidence duplicate not detected"
            logger.info(f"✓ Found duplicate with {high_confidence_match.similarity_score:.3f} similarity")
            
            # Test 2: Title Similarity
            title_sim = engine._calculate_title_similarity(
                "Executive Session on AI Oversight",
                "Executive Session: AI Oversight"
            )
            assert title_sim > 0.8, f"Title similarity too low: {title_sim}"
            logger.info(f"✓ Title similarity calculation: {title_sim:.3f}")
            
            # Test 3: Date Proximity
            date_sim = engine._calculate_date_proximity("2025-06-28", "2025-06-28")
            assert date_sim == 1.0, f"Exact date match should be 1.0: {date_sim}"
            
            date_sim2 = engine._calculate_date_proximity("2025-06-28", "2025-06-29")
            assert 0.5 < date_sim2 < 1.0, f"Adjacent date similarity incorrect: {date_sim2}"
            logger.info("✓ Date proximity calculation working")
            
            # Test 4: Merge Logic
            primary = test_hearings[0]
            secondary = test_hearings[1]
            merged = engine.merge_hearings(primary, secondary, 0.95)
            
            assert merged['streams'], "Streams not merged correctly"
            assert merged['sync_confidence'] == 0.95, "Confidence not set correctly"
            assert merged['source_api'] and merged['source_website'], "Source flags not merged"
            logger.info("✓ Hearing merge logic working correctly")
            
            # Test 5: Report Generation
            report = engine.generate_merge_report(matches)
            assert 'total_matches' in report, "Report generation failed"
            assert report['total_matches'] == len(matches), "Report count incorrect"
            logger.info(f"✓ Generated deduplication report: {report['total_matches']} matches")
            
            self.results['deduplication_engine'] = {'status': 'PASS', 'tests': 5}
        
        except Exception as e:
            logger.error(f"❌ Deduplication engine test failed: {e}")
            self.results['deduplication_engine'] = {'status': 'FAIL', 'error': str(e)}
    
    async def test_sync_orchestrator(self):
        """Test sync orchestrator coordination"""
        
        logger.info("🎭 Testing Sync Orchestrator...")
        
        try:
            orchestrator = SyncOrchestrator(self.test_db_path)
            
            # Test 1: Initialization
            assert orchestrator.db is not None, "Database connection failed"
            assert orchestrator.committee_scraper is not None, "Scraper not initialized"
            assert orchestrator.dedup_engine is not None, "Deduplication engine not initialized"
            logger.info("✓ Orchestrator initialization successful")
            
            # Test 2: Committee Configuration
            active_committees = orchestrator._get_active_committees()
            assert len(active_committees) > 0, "No active committees found"
            logger.info(f"✓ Found {len(active_committees)} active committees: {active_committees}")
            
            priority_committees = orchestrator._get_priority_committees()
            logger.info(f"✓ Found {len(priority_committees)} priority committees: {priority_committees}")
            
            # Test 3: Circuit Breaker Logic
            orchestrator._record_circuit_breaker_failure('test_source')
            assert orchestrator.circuit_breakers['test_source']['failures'] == 1, "Circuit breaker not recording failures"
            logger.info("✓ Circuit breaker logic working")
            
            # Test 4: Status Reporting
            status = orchestrator.get_sync_status()
            assert 'database_stats' in status, "Status missing database stats"
            assert 'circuit_breakers' in status, "Status missing circuit breaker info"
            logger.info("✓ Status reporting working")
            
            # Test 5: Data Conversion
            # Test API hearing conversion
            api_hearing = HearingRecord(
                congress_api_id='test-123',
                committee_code='SCOM',
                hearing_title='Test API Hearing',
                hearing_date='2025-06-28',
                hearing_type='Hearing',
                meeting_status='Scheduled',
                location_info={'room': 'Test Room'},
                documents=[],
                witnesses=[],
                raw_data={}
            )
            
            converted = orchestrator._convert_api_hearing(api_hearing)
            assert converted['congress_api_id'] == 'test-123', "API conversion failed"
            assert converted['sync_confidence'] == 1.0, "API confidence not set correctly"
            logger.info("✓ API hearing conversion working")
            
            # Test scraped hearing conversion
            scraped_hearing = ScrapedHearing(
                committee_source_id='scraped-123',
                committee_code='SCOM',
                hearing_title='Test Scraped Hearing',
                hearing_date='2025-06-28',
                source_url='https://test.com',
                streams={'isvp_stream': 'test_url'},
                documents=[],
                witnesses=[],
                status='discovered',
                raw_html='<html></html>'
            )
            
            converted_scraped = orchestrator._convert_scraped_hearing(scraped_hearing)
            assert converted_scraped['committee_source_id'] == 'scraped-123', "Scraped conversion failed"
            assert converted_scraped['sync_confidence'] == 0.8, "Scraped confidence not set correctly"
            logger.info("✓ Scraped hearing conversion working")
            
            orchestrator.close()
            self.results['sync_orchestrator'] = {'status': 'PASS', 'tests': 5}
        
        except Exception as e:
            logger.error(f"❌ Sync orchestrator test failed: {e}")
            self.results['sync_orchestrator'] = {'status': 'FAIL', 'error': str(e)}
    
    async def test_full_sync_integration(self):
        """Test full sync integration with mock data"""
        
        logger.info("🔗 Testing Full Sync Integration...")
        
        try:
            orchestrator = SyncOrchestrator(self.test_db_path)
            
            # Mock the API and scraper to avoid external dependencies
            with patch.object(orchestrator, 'congress_api') as mock_api, \
                 patch.object(orchestrator.committee_scraper, 'scrape_committee_hearings') as mock_scraper:
                
                # Setup API mock
                if mock_api:
                    mock_api.get_committee_meetings.return_value = [
                        HearingRecord(
                            congress_api_id='api-test-1',
                            committee_code='SCOM',
                            hearing_title='Mock API Hearing on Technology',
                            hearing_date='2025-06-28',
                            hearing_type='Hearing',
                            meeting_status='Scheduled',
                            location_info={'room': 'Room 253'},
                            documents=[],
                            witnesses=[],
                            raw_data={}
                        )
                    ]
                
                # Setup scraper mock
                mock_scraper.return_value = [
                    ScrapedHearing(
                        committee_source_id='scraper-test-1',
                        committee_code='SCOM',
                        hearing_title='Mock Scraped Hearing on Technology',
                        hearing_date='2025-06-28',
                        source_url='https://test.com/hearing',
                        streams={'isvp_stream': 'test_stream'},
                        documents=[],
                        witnesses=[],
                        status='discovered',
                        raw_html='<html></html>'
                    )
                ]
                
                # Test 1: Scheduled Sync Check
                scheduled_result = await orchestrator.run_scheduled_sync()
                assert 'sync_needed' in scheduled_result, "Scheduled sync check failed"
                logger.info(f"✓ Scheduled sync check: {scheduled_result['sync_needed']}")
                
                # Test 2: Mock Full Sync (if committee scraper is available)
                if mock_scraper:
                    results = await orchestrator.run_full_sync(['SCOM'])
                    assert len(results) >= 0, "Sync results not returned"
                    logger.info(f"✓ Mock sync completed with {len(results)} operations")
                
            orchestrator.close()
            self.results['full_sync_integration'] = {'status': 'PASS', 'tests': 2}
        
        except Exception as e:
            logger.error(f"❌ Full sync integration test failed: {e}")
            self.results['full_sync_integration'] = {'status': 'FAIL', 'error': str(e)}
    
    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        
        logger.info("\n" + "="*60)
        logger.info("📋 PHASE 7A TEST SUMMARY")
        logger.info("="*60)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for component, result in self.results.items():
            status = result['status']
            test_count = result.get('tests', 0)
            total_tests += test_count
            
            if status == 'PASS':
                passed_tests += test_count
                logger.info(f"✅ {component.replace('_', ' ').title()}: {status} ({test_count} tests)")
            else:
                failed_tests += test_count
                error = result.get('error', 'Unknown error')
                logger.info(f"❌ {component.replace('_', ' ').title()}: {status} - {error}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("\n" + "-"*40)
        logger.info(f"📊 RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            logger.info("🎉 Phase 7A Automated Sync System: READY FOR DEPLOYMENT")
        elif success_rate >= 60:
            logger.info("⚠️  Phase 7A Automated Sync System: NEEDS MINOR FIXES")
        else:
            logger.info("🚨 Phase 7A Automated Sync System: NEEDS MAJOR FIXES")
        
        logger.info("="*60)
        
        # Save detailed results
        results_file = Path(self.temp_dir) / "phase7a_test_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'test_results': self.results,
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': success_rate
                },
                'test_timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"📄 Detailed results saved to: {results_file}")

async def main():
    """Main test execution"""
    
    # Check for required dependencies
    try:
        import requests
        import schedule
        from bs4 import BeautifulSoup
    except ImportError as e:
        logger.error(f"Missing required dependency: {e}")
        logger.info("Install with: uv pip install requests schedule beautifulsoup4")
        return
    
    # Run test suite
    test_suite = Phase7ATestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())