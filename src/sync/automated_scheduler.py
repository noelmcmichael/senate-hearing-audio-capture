"""
Automated scheduler for Phase 7A hearing synchronization.
Manages scheduled sync operations, monitoring, and health checks.
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import schedule
import time
from concurrent.futures import ThreadPoolExecutor

from .sync_orchestrator import SyncOrchestrator

logger = logging.getLogger(__name__)

class AutomatedScheduler:
    """Automated scheduler for hearing synchronization operations"""
    
    def __init__(self, config_path: str = "data/scheduler_config.json"):
        """Initialize automated scheduler with configuration"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.orchestrator = SyncOrchestrator()
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Health monitoring
        self.last_successful_sync = None
        self.consecutive_failures = 0
        self.health_check_interval = 300  # 5 minutes
        
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load scheduler configuration"""
        
        default_config = {
            "sync_schedules": {
                "daily_api_sync": {
                    "time": "12:30",  # 12:30 PM ET (30 min after Congress.gov update)
                    "enabled": True,
                    "committees": "all"
                },
                "morning_website_sync": {
                    "time": "08:00",
                    "enabled": True,
                    "committees": "priority"
                },
                "afternoon_website_sync": {
                    "time": "14:00", 
                    "enabled": True,
                    "committees": "priority"
                },
                "evening_website_sync": {
                    "time": "20:00",
                    "enabled": True,
                    "committees": "priority"
                }
            },
            "monitoring": {
                "health_check_enabled": True,
                "max_consecutive_failures": 5,
                "failure_notification_threshold": 3,
                "performance_alert_threshold": 0.7  # 70% success rate
            },
            "circuit_breakers": {
                "api_failure_threshold": 5,
                "scraper_failure_threshold": 5,
                "recovery_time_hours": 2
            },
            "logging": {
                "level": "INFO",
                "file": "logs/scheduler.log",
                "max_size_mb": 50,
                "backup_count": 5
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    default_config.update(loaded_config)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error loading config, using defaults: {e}")
        else:
            # Save default config
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _setup_logging(self):
        """Setup logging configuration"""
        
        log_config = self.config.get('logging', {})
        log_file = Path(log_config.get('file', 'logs/scheduler.log'))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure file handler with rotation
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_config.get('max_size_mb', 50) * 1024 * 1024,
            backupCount=log_config.get('backup_count', 5)
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        # Configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def start(self):
        """Start the automated scheduler"""
        
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting automated sync scheduler")
        self.running = True
        
        # Schedule sync operations
        self._setup_schedules()
        
        # Start main loop
        try:
            self._run_scheduler_loop()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        finally:
            self.stop()
    
    def _setup_schedules(self):
        """Setup scheduled sync operations"""
        
        schedules = self.config.get('sync_schedules', {})
        
        for schedule_name, schedule_config in schedules.items():
            if not schedule_config.get('enabled', True):
                logger.info(f"Skipping disabled schedule: {schedule_name}")
                continue
            
            sync_time = schedule_config.get('time')
            committees = schedule_config.get('committees', 'all')
            
            if sync_time:
                # Schedule the sync operation
                schedule.every().day.at(sync_time).do(
                    self._schedule_sync_job, 
                    schedule_name, 
                    committees
                ).tag(schedule_name)
                
                logger.info(f"Scheduled {schedule_name} at {sync_time} for {committees} committees")
        
        # Schedule health checks
        if self.config.get('monitoring', {}).get('health_check_enabled', True):
            schedule.every(5).minutes.do(self._health_check_job).tag('health_check')
            logger.info("Scheduled health checks every 5 minutes")
    
    def _run_scheduler_loop(self):
        """Main scheduler loop"""
        
        logger.info("Scheduler loop started")
        
        while self.running:
            try:
                # Run pending scheduled jobs
                schedule.run_pending()
                
                # Sleep for a short period
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _schedule_sync_job(self, schedule_name: str, committees: str):
        """Execute a scheduled sync job"""
        
        logger.info(f"Starting scheduled sync: {schedule_name}")
        
        try:
            # Determine committee list
            if committees == 'all':
                committee_codes = None  # Will use all active committees
            elif committees == 'priority':
                committee_codes = ['SCOM', 'SSCI', 'SSJU']  # High priority committees
            else:
                committee_codes = committees if isinstance(committees, list) else [committees]
            
            # Run sync in executor to avoid blocking
            future = self.executor.submit(self._run_sync_job, schedule_name, committee_codes)
            
            # Don't wait for completion to avoid blocking scheduler
            # Result will be logged when job completes
            
        except Exception as e:
            logger.error(f"Error starting sync job {schedule_name}: {e}")
            self.consecutive_failures += 1
            self._check_failure_threshold()
    
    def _run_sync_job(self, schedule_name: str, committee_codes: Optional[list]):
        """Run sync job in executor"""
        
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run sync operation
                results = loop.run_until_complete(
                    self.orchestrator.run_full_sync(committee_codes)
                )
                
                # Analyze results
                total_operations = len(results)
                successful_operations = sum(1 for r in results.values() if r.success)
                success_rate = successful_operations / total_operations if total_operations > 0 else 0
                
                logger.info(f"Sync job {schedule_name} completed: "
                           f"{successful_operations}/{total_operations} operations successful "
                           f"(success rate: {success_rate:.1%})")
                
                # Update health status
                if success_rate >= 0.7:  # 70% success threshold
                    self.last_successful_sync = datetime.now()
                    self.consecutive_failures = 0
                else:
                    self.consecutive_failures += 1
                    logger.warning(f"Low success rate for {schedule_name}: {success_rate:.1%}")
                
                # Check for alerts
                self._check_performance_alerts(schedule_name, results)
                
            finally:
                loop.close()
        
        except Exception as e:
            logger.error(f"Sync job {schedule_name} failed: {e}")
            self.consecutive_failures += 1
            self._check_failure_threshold()
    
    def _health_check_job(self):
        """Perform health check"""
        
        try:
            status = self.orchestrator.get_sync_status()
            
            # Check database connectivity
            db_healthy = status.get('database_stats', {}).get('total_hearings', 0) >= 0
            
            # Check API availability
            api_healthy = status.get('api_available', False)
            
            # Check circuit breakers
            circuit_breakers = status.get('circuit_breakers', {})
            active_breakers = [source for source, info in circuit_breakers.items() 
                             if info.get('active', False)]
            
            # Log health status
            health_status = {
                'database_healthy': db_healthy,
                'api_healthy': api_healthy,
                'active_circuit_breakers': active_breakers,
                'last_successful_sync': self.last_successful_sync.isoformat() if self.last_successful_sync else None,
                'consecutive_failures': self.consecutive_failures
            }
            
            logger.debug(f"Health check: {json.dumps(health_status)}")
            
            # Alert on significant issues
            if active_breakers:
                logger.warning(f"Active circuit breakers: {active_breakers}")
            
            if not db_healthy:
                logger.error("Database health check failed")
            
            # Check if sync is overdue
            if self.last_successful_sync:
                hours_since_sync = (datetime.now() - self.last_successful_sync).total_seconds() / 3600
                if hours_since_sync > 25:  # More than 25 hours (should sync daily)
                    logger.warning(f"No successful sync in {hours_since_sync:.1f} hours")
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def _check_failure_threshold(self):
        """Check if failure threshold has been exceeded"""
        
        threshold = self.config.get('monitoring', {}).get('max_consecutive_failures', 5)
        
        if self.consecutive_failures >= threshold:
            logger.critical(f"Maximum consecutive failures reached: {self.consecutive_failures}")
            # Could implement notification system here
    
    def _check_performance_alerts(self, schedule_name: str, results: Dict[str, Any]):
        """Check for performance issues and generate alerts"""
        
        threshold = self.config.get('monitoring', {}).get('performance_alert_threshold', 0.7)
        
        for operation_name, result in results.items():
            if result.errors_encountered > 0:
                logger.warning(f"Errors in {operation_name}: {result.errors_encountered}")
            
            if result.execution_time > 300:  # More than 5 minutes
                logger.warning(f"Slow operation {operation_name}: {result.execution_time:.1f}s")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully")
        self.stop()
    
    def stop(self):
        """Stop the scheduler"""
        
        if not self.running:
            return
        
        logger.info("Stopping automated sync scheduler")
        self.running = False
        
        # Clear scheduled jobs
        schedule.clear()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Close orchestrator
        self.orchestrator.close()
        
        logger.info("Scheduler stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        
        return {
            'running': self.running,
            'scheduled_jobs': [
                {
                    'job': str(job.job_func),
                    'next_run': job.next_run.isoformat() if job.next_run else None,
                    'tags': list(job.tags)
                }
                for job in schedule.jobs
            ],
            'last_successful_sync': self.last_successful_sync.isoformat() if self.last_successful_sync else None,
            'consecutive_failures': self.consecutive_failures,
            'sync_orchestrator_status': self.orchestrator.get_sync_status()
        }
    
    def run_manual_sync(self, committee_codes: Optional[list] = None) -> Dict[str, Any]:
        """Run manual sync operation"""
        
        logger.info(f"Starting manual sync for committees: {committee_codes or 'all'}")
        
        try:
            # Run sync in executor
            future = self.executor.submit(self._run_sync_job, 'manual', committee_codes)
            
            # Wait for completion with timeout
            result = future.result(timeout=600)  # 10 minute timeout
            
            return {'success': True, 'message': 'Manual sync completed'}
        
        except Exception as e:
            logger.error(f"Manual sync failed: {e}")
            return {'success': False, 'error': str(e)}

def main():
    """Main entry point for scheduler"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Hearing Sync Scheduler')
    parser.add_argument('--config', default='data/scheduler_config.json',
                       help='Path to scheduler configuration file')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    parser.add_argument('--manual-sync', action='store_true',
                       help='Run manual sync and exit')
    parser.add_argument('--committees', nargs='*',
                       help='Specific committees for manual sync')
    
    args = parser.parse_args()
    
    # Create scheduler
    scheduler = AutomatedScheduler(args.config)
    
    if args.manual_sync:
        # Run manual sync
        result = scheduler.run_manual_sync(args.committees)
        print(json.dumps(result, indent=2))
        scheduler.stop()
    else:
        # Start automated scheduler
        try:
            scheduler.start()
        except KeyboardInterrupt:
            print("\nShutdown requested")
        finally:
            scheduler.stop()

if __name__ == "__main__":
    main()