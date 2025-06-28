"""
Main synchronization orchestrator for Phase 7A automated data synchronization.
Coordinates Congress.gov API, committee scraping, and deduplication.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .database_schema import UnifiedHearingDatabase
from .congress_api_enhanced import CongressAPIEnhanced, HearingRecord
from .committee_scraper import CommitteeWebsiteScraper, ScrapedHearing
from .deduplication_engine import DeduplicationEngine, DuplicationMatch

logger = logging.getLogger(__name__)

@dataclass
class SyncResult:
    """Result of a synchronization operation"""
    sync_id: str
    committee_code: str
    source: str
    hearings_discovered: int
    hearings_updated: int
    duplicates_merged: int
    errors_encountered: int
    execution_time: float
    success: bool
    error_message: Optional[str] = None

class SyncOrchestrator:
    """Main orchestrator for automated hearing synchronization"""
    
    def __init__(self, db_path: str = "data/hearings_unified.db"):
        """Initialize sync orchestrator with database and components"""
        self.db = UnifiedHearingDatabase(db_path)
        self.congress_api = None  # Initialize only if API key available
        self.committee_scraper = CommitteeWebsiteScraper()
        self.dedup_engine = DeduplicationEngine()
        
        # Try to initialize Congress API
        try:
            self.congress_api = CongressAPIEnhanced()
            logger.info("Congress API client initialized successfully")
        except ValueError as e:
            logger.warning(f"Congress API not available: {e}")
        
        # Sync configuration
        self.sync_config = {
            'api_daily_sync_hour': 12,  # 12 PM ET (Congress.gov updates at noon)
            'website_sync_hours': [8, 14, 20],  # 8 AM, 2 PM, 8 PM
            'max_concurrent_committees': 3,
            'retry_attempts': 3,
            'retry_delay': 30,  # seconds
            'circuit_breaker_threshold': 5  # failures before disabling source
        }
        
        # Circuit breaker state
        self.circuit_breakers = {
            'congress_api': {'failures': 0, 'disabled_until': None},
            'website_scraper': {'failures': 0, 'disabled_until': None}
        }
    
    async def run_full_sync(self, committee_codes: List[str] = None) -> Dict[str, SyncResult]:
        """Run full synchronization for all or specified committees"""
        
        sync_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        logger.info(f"Starting full sync operation: {sync_id}")
        
        if committee_codes is None:
            # Get all active committees from database config
            committee_codes = self._get_active_committees()
        
        results = {}
        
        # Run API sync first (more authoritative)
        if self.congress_api and not self._is_circuit_breaker_active('congress_api'):
            api_results = await self._sync_congress_api(committee_codes, sync_id)
            results.update(api_results)
        
        # Run website scraping (for real-time updates)
        if not self._is_circuit_breaker_active('website_scraper'):
            scraper_results = await self._sync_committee_websites(committee_codes, sync_id)
            results.update(scraper_results)
        
        # Run deduplication on all hearings
        await self._run_deduplication(sync_id)
        
        # Update sync metrics
        self._record_sync_metrics(sync_id, results)
        
        logger.info(f"Full sync operation {sync_id} completed")
        return results
    
    async def run_scheduled_sync(self) -> Dict[str, Any]:
        """Run scheduled sync based on current time and committee priorities"""
        
        current_hour = datetime.now().hour
        sync_type = 'unknown'
        
        # Determine sync type based on schedule
        if current_hour == self.sync_config['api_daily_sync_hour']:
            sync_type = 'daily_api'
            committee_codes = self._get_active_committees()
        elif current_hour in self.sync_config['website_sync_hours']:
            sync_type = 'website_update'
            committee_codes = self._get_priority_committees()
        else:
            # Check for overdue syncs
            overdue_committees = self._get_overdue_committees()
            if overdue_committees:
                sync_type = 'overdue'
                committee_codes = overdue_committees
            else:
                logger.info("No scheduled sync needed at this time")
                return {'sync_needed': False, 'current_hour': current_hour}
        
        logger.info(f"Running {sync_type} sync for committees: {committee_codes}")
        
        results = await self.run_full_sync(committee_codes)
        
        return {
            'sync_type': sync_type,
            'sync_needed': True,
            'results': results
        }
    
    async def _sync_congress_api(self, committee_codes: List[str], sync_id: str) -> Dict[str, SyncResult]:
        """Synchronize hearings from Congress.gov API"""
        
        logger.info(f"Starting Congress API sync for {len(committee_codes)} committees")
        results = {}
        
        for committee_code in committee_codes:
            start_time = time.time()
            
            try:
                # Get hearings from API
                hearings = self.congress_api.get_committee_meetings(committee_code, days_back=30)
                
                discovered = 0
                updated = 0
                errors = 0
                
                for hearing in hearings:
                    try:
                        # Convert to database format
                        hearing_data = self._convert_api_hearing(hearing)
                        
                        # Check for existing records
                        duplicates = self.db.find_potential_duplicates(hearing_data)
                        
                        if duplicates and duplicates[0]['similarity_score'] > 0.8:
                            # Update existing record
                            self.db.update_hearing(
                                duplicates[0]['id'], 
                                hearing_data, 
                                'congress_api'
                            )
                            updated += 1
                        else:
                            # Insert new record
                            self.db.insert_hearing(hearing_data, 'congress_api')
                            discovered += 1
                    
                    except Exception as e:
                        logger.error(f"Error processing API hearing {hearing.congress_api_id}: {e}")
                        errors += 1
                
                execution_time = time.time() - start_time
                
                results[f"{committee_code}_api"] = SyncResult(
                    sync_id=sync_id,
                    committee_code=committee_code,
                    source='congress_api',
                    hearings_discovered=discovered,
                    hearings_updated=updated,
                    duplicates_merged=0,  # Will be handled in deduplication step
                    errors_encountered=errors,
                    execution_time=execution_time,
                    success=True
                )
                
                # Reset circuit breaker on success
                self.circuit_breakers['congress_api']['failures'] = 0
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"API sync failed for {committee_code}: {e}")
                
                results[f"{committee_code}_api"] = SyncResult(
                    sync_id=sync_id,
                    committee_code=committee_code,
                    source='congress_api',
                    hearings_discovered=0,
                    hearings_updated=0,
                    duplicates_merged=0,
                    errors_encountered=1,
                    execution_time=execution_time,
                    success=False,
                    error_message=str(e)
                )
                
                # Update circuit breaker
                self._record_circuit_breaker_failure('congress_api')
        
        return results
    
    async def _sync_committee_websites(self, committee_codes: List[str], sync_id: str) -> Dict[str, SyncResult]:
        """Synchronize hearings from committee websites"""
        
        logger.info(f"Starting website scraping for {len(committee_codes)} committees")
        results = {}
        
        # Use thread pool for concurrent scraping
        with ThreadPoolExecutor(max_workers=self.sync_config['max_concurrent_committees']) as executor:
            future_to_committee = {
                executor.submit(self._scrape_single_committee, committee_code, sync_id): committee_code
                for committee_code in committee_codes
            }
            
            for future in as_completed(future_to_committee):
                committee_code = future_to_committee[future]
                try:
                    result = future.result()
                    results[f"{committee_code}_website"] = result
                except Exception as e:
                    logger.error(f"Website scraping failed for {committee_code}: {e}")
                    
                    results[f"{committee_code}_website"] = SyncResult(
                        sync_id=sync_id,
                        committee_code=committee_code,
                        source='website_scraper',
                        hearings_discovered=0,
                        hearings_updated=0,
                        duplicates_merged=0,
                        errors_encountered=1,
                        execution_time=0,
                        success=False,
                        error_message=str(e)
                    )
        
        return results
    
    def _scrape_single_committee(self, committee_code: str, sync_id: str) -> SyncResult:
        """Scrape hearings for a single committee"""
        
        start_time = time.time()
        
        try:
            # Scrape committee hearings
            hearings = self.committee_scraper.scrape_committee_hearings(committee_code, days_back=14)
            
            discovered = 0
            updated = 0
            errors = 0
            
            for hearing in hearings:
                try:
                    # Convert to database format
                    hearing_data = self._convert_scraped_hearing(hearing)
                    
                    # Check for existing records
                    duplicates = self.db.find_potential_duplicates(hearing_data)
                    
                    if duplicates and duplicates[0]['similarity_score'] > 0.7:
                        # Update existing record with website data
                        self.db.update_hearing(
                            duplicates[0]['id'],
                            hearing_data,
                            'website_scraper'
                        )
                        updated += 1
                    else:
                        # Insert new record
                        self.db.insert_hearing(hearing_data, 'website_scraper')
                        discovered += 1
                
                except Exception as e:
                    logger.error(f"Error processing scraped hearing {hearing.committee_source_id}: {e}")
                    errors += 1
            
            execution_time = time.time() - start_time
            
            # Reset circuit breaker on success
            if not errors or errors < len(hearings) * 0.5:  # Less than 50% failure rate
                self.circuit_breakers['website_scraper']['failures'] = 0
            
            return SyncResult(
                sync_id=sync_id,
                committee_code=committee_code,
                source='website_scraper',
                hearings_discovered=discovered,
                hearings_updated=updated,
                duplicates_merged=0,
                errors_encountered=errors,
                execution_time=execution_time,
                success=True
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Website scraping failed for {committee_code}: {e}")
            
            # Update circuit breaker
            self._record_circuit_breaker_failure('website_scraper')
            
            return SyncResult(
                sync_id=sync_id,
                committee_code=committee_code,
                source='website_scraper',
                hearings_discovered=0,
                hearings_updated=0,
                duplicates_merged=0,
                errors_encountered=1,
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
    
    async def _run_deduplication(self, sync_id: str):
        """Run deduplication on recent hearings"""
        
        logger.info("Starting deduplication analysis")
        
        try:
            # Get recent hearings (last 60 days)
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT * FROM hearings_unified 
                WHERE hearing_date >= date('now', '-60 days')
                AND sync_status NOT LIKE 'merged_into_%'
                ORDER BY hearing_date DESC
            """)
            
            hearings = [dict(row) for row in cursor.fetchall()]
            
            if len(hearings) < 2:
                logger.info("Not enough hearings for deduplication")
                return
            
            # Find duplicates
            matches = self.dedup_engine.find_duplicates(hearings)
            
            auto_merged = 0
            manual_review = 0
            
            for match in matches:
                if match.recommended_action == 'auto_merge':
                    # Automatically merge high-confidence duplicates
                    primary_hearing = next(h for h in hearings if h['id'] == match.primary_id)
                    secondary_hearing = next(h for h in hearings if h['id'] == match.secondary_id)
                    
                    self.db.merge_hearing_records(
                        match.primary_id,
                        match.secondary_id,
                        match.similarity_score
                    )
                    auto_merged += 1
                    
                elif match.recommended_action == 'manual_review':
                    # Log for manual review
                    logger.info(f"Manual review needed: hearings {match.primary_id} and {match.secondary_id} "
                               f"(similarity: {match.similarity_score:.3f})")
                    manual_review += 1
            
            logger.info(f"Deduplication completed: {auto_merged} auto-merged, {manual_review} need manual review")
        
        except Exception as e:
            logger.error(f"Deduplication failed: {e}")
    
    def _convert_api_hearing(self, hearing: HearingRecord) -> Dict[str, Any]:
        """Convert API hearing record to database format"""
        
        return {
            'congress_api_id': hearing.congress_api_id,
            'committee_code': hearing.committee_code,
            'hearing_title': hearing.hearing_title,
            'hearing_date': hearing.hearing_date,
            'hearing_type': hearing.hearing_type,
            'meeting_status': hearing.meeting_status,
            'location_info': hearing.location_info,
            'documents': hearing.documents,
            'witnesses': hearing.witnesses,
            'streams': {},  # API doesn't provide direct stream links
            'sync_confidence': 1.0  # High confidence for API data
        }
    
    def _convert_scraped_hearing(self, hearing: ScrapedHearing) -> Dict[str, Any]:
        """Convert scraped hearing record to database format"""
        
        return {
            'committee_source_id': hearing.committee_source_id,
            'committee_code': hearing.committee_code,
            'hearing_title': hearing.hearing_title,
            'hearing_date': hearing.hearing_date,
            'hearing_type': 'Hearing',  # Default for scraped data
            'meeting_status': hearing.status,
            'location_info': {},
            'documents': hearing.documents,
            'witnesses': hearing.witnesses,
            'streams': hearing.streams,
            'external_urls': [hearing.source_url],
            'sync_confidence': 0.8  # Medium confidence for scraped data
        }
    
    def _get_active_committees(self) -> List[str]:
        """Get list of active committees from database config"""
        
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT committee_code 
            FROM sync_config 
            WHERE active = 1 
            ORDER BY priority_level
        """)
        
        return [row[0] for row in cursor.fetchall()]
    
    def _get_priority_committees(self) -> List[str]:
        """Get high-priority committees for frequent updates"""
        
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT committee_code 
            FROM sync_config 
            WHERE active = 1 AND priority_level <= 2
            ORDER BY priority_level
        """)
        
        return [row[0] for row in cursor.fetchall()]
    
    def _get_overdue_committees(self) -> List[str]:
        """Get committees that haven't been synced recently"""
        
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT c.committee_code
            FROM sync_config c
            LEFT JOIN hearings_unified h ON c.committee_code = h.committee_code
            WHERE c.active = 1
            AND (
                h.last_api_sync IS NULL 
                OR datetime(h.last_api_sync) < datetime('now', '-' || c.sync_frequency_hours || ' hours')
            )
            GROUP BY c.committee_code
            ORDER BY c.priority_level
        """)
        
        return [row[0] for row in cursor.fetchall()]
    
    def _is_circuit_breaker_active(self, source: str) -> bool:
        """Check if circuit breaker is active for a source"""
        
        breaker = self.circuit_breakers.get(source, {})
        disabled_until = breaker.get('disabled_until')
        
        if disabled_until and datetime.now() < disabled_until:
            return True
        
        return breaker.get('failures', 0) >= self.sync_config['circuit_breaker_threshold']
    
    def _record_circuit_breaker_failure(self, source: str):
        """Record a failure for circuit breaker tracking"""
        
        if source not in self.circuit_breakers:
            self.circuit_breakers[source] = {'failures': 0, 'disabled_until': None}
        
        self.circuit_breakers[source]['failures'] += 1
        
        # Disable source if threshold reached
        if self.circuit_breakers[source]['failures'] >= self.sync_config['circuit_breaker_threshold']:
            disabled_until = datetime.now() + timedelta(hours=1)  # Disable for 1 hour
            self.circuit_breakers[source]['disabled_until'] = disabled_until
            logger.warning(f"Circuit breaker activated for {source} until {disabled_until}")
    
    def _record_sync_metrics(self, sync_id: str, results: Dict[str, SyncResult]):
        """Record sync metrics in database"""
        
        for result in results.values():
            self.db.connection.execute("""
                INSERT INTO sync_metrics (
                    sync_run_id, committee_code, sync_source,
                    hearings_discovered, hearings_updated, duplicates_merged,
                    errors_encountered, execution_time_seconds, success_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sync_id,
                result.committee_code,
                result.source,
                result.hearings_discovered,
                result.hearings_updated,
                result.duplicates_merged,
                result.errors_encountered,
                result.execution_time,
                1.0 if result.success else 0.0
            ))
        
        self.db.connection.commit()
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and health metrics"""
        
        stats = self.db.get_sync_statistics()
        
        # Add circuit breaker status
        circuit_status = {}
        for source, breaker in self.circuit_breakers.items():
            circuit_status[source] = {
                'failures': breaker['failures'],
                'active': self._is_circuit_breaker_active(source),
                'disabled_until': breaker.get('disabled_until').isoformat() if breaker.get('disabled_until') else None
            }
        
        # Get recent sync performance
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT sync_source, AVG(success_rate) as avg_success_rate,
                   COUNT(*) as total_runs, MAX(sync_timestamp) as last_run
            FROM sync_metrics 
            WHERE sync_timestamp > datetime('now', '-24 hours')
            GROUP BY sync_source
        """)
        
        recent_performance = {
            row[0]: {
                'avg_success_rate': row[1],
                'total_runs': row[2],
                'last_run': row[3]
            }
            for row in cursor.fetchall()
        }
        
        return {
            'database_stats': stats,
            'circuit_breakers': circuit_status,
            'recent_performance': recent_performance,
            'api_available': self.congress_api is not None,
            'scraper_available': True,
            'last_status_check': datetime.now().isoformat()
        }
    
    def close(self):
        """Close database connections"""
        self.db.close()

if __name__ == "__main__":
    # Test sync orchestrator
    import asyncio
    
    orchestrator = SyncOrchestrator("data/test_sync.db")
    
    async def test_sync():
        # Test status check
        status = orchestrator.get_sync_status()
        print("Sync Status:")
        print(json.dumps(status, indent=2))
        
        # Test scheduled sync check
        scheduled_result = await orchestrator.run_scheduled_sync()
        print("\nScheduled Sync Result:")
        print(json.dumps(scheduled_result, indent=2, default=str))
        
        orchestrator.close()
    
    # Run test
    asyncio.run(test_sync())
    print("Sync orchestrator testing completed")