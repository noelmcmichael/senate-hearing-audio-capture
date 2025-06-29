"""
Database migration for Phase 7C Milestone 2: Enhanced Status Management
Adds status tracking columns to hearings_unified table.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class StatusMigration:
    """Handles database migration for status management features"""
    
    def __init__(self, db_path: str = "data/demo_enhanced_ui.db"):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row  # Enable dict-like access to rows
    
    def run_migration(self):
        """Execute the complete migration for status management"""
        logger.info("Starting Phase 7C Milestone 2 database migration...")
        
        try:
            # Check if migration already applied
            if self._check_migration_applied():
                logger.info("Migration already applied, skipping...")
                return True
            
            # Add status management columns
            self._add_status_columns()
            
            # Create indexes for performance
            self._create_indexes()
            
            # Initialize default values for existing records
            self._initialize_default_values()
            
            # Commit all changes
            self.connection.commit()
            
            logger.info("Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.connection.rollback()
            return False
    
    def _check_migration_applied(self) -> bool:
        """Check if the migration has already been applied"""
        try:
            cursor = self.connection.execute(
                "SELECT status FROM hearings_unified LIMIT 1"
            )
            return True  # Column exists
        except sqlite3.OperationalError:
            return False  # Column doesn't exist
    
    def _add_status_columns(self):
        """Add status management columns to hearings_unified table"""
        logger.info("Adding status management columns...")
        
        # SQLite ALTER TABLE has limitations with CHECK constraints and DEFAULT CURRENT_TIMESTAMP
        # Add columns one by one without constraints first
        
        try:
            # Add status column (main workflow state)
            self.connection.execute("""
                ALTER TABLE hearings_unified 
                ADD COLUMN status TEXT DEFAULT 'new'
            """)
            logger.info("Added status column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
        
        try:
            # Add processing_stage column (detailed stage within workflow)
            self.connection.execute("""
                ALTER TABLE hearings_unified 
                ADD COLUMN processing_stage TEXT DEFAULT 'discovered'
            """)
            logger.info("Added processing_stage column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
        
        try:
            # Add assigned_reviewer column
            self.connection.execute("""
                ALTER TABLE hearings_unified 
                ADD COLUMN assigned_reviewer TEXT
            """)
            logger.info("Added assigned_reviewer column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
        
        try:
            # Add status_updated_at timestamp - SQLite limitation: can't use CURRENT_TIMESTAMP as default in ALTER TABLE
            self.connection.execute("""
                ALTER TABLE hearings_unified 
                ADD COLUMN status_updated_at TEXT
            """)
            logger.info("Added status_updated_at column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
        
        try:
            # Add reviewer_notes column for workflow notes
            self.connection.execute("""
                ALTER TABLE hearings_unified 
                ADD COLUMN reviewer_notes TEXT
            """)
            logger.info("Added reviewer_notes column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
        
        logger.info("Successfully processed status management columns")
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        logger.info("Creating performance indexes...")
        
        # Index on status for filtering
        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_hearings_status 
            ON hearings_unified(status)
        """)
        
        # Index on processing_stage for stage-based queries
        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_hearings_processing_stage 
            ON hearings_unified(processing_stage)
        """)
        
        # Index on assigned_reviewer for reviewer workload queries
        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_hearings_assigned_reviewer 
            ON hearings_unified(assigned_reviewer)
        """)
        
        # Composite index for status workflow queries
        self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_hearings_status_stage 
            ON hearings_unified(status, processing_stage)
        """)
        
        logger.info("Created 4 performance indexes")
    
    def _initialize_default_values(self):
        """Initialize default values for existing records"""
        logger.info("Initializing default values for existing hearings...")
        
        # Set default status and processing_stage for existing records
        # Handle NULL and empty string cases separately
        cursor = self.connection.execute("""
            UPDATE hearings_unified 
            SET 
                status = 'new',
                processing_stage = 'discovered',
                status_updated_at = datetime('now')
            WHERE status IS NULL OR status = '' OR processing_stage IS NULL OR processing_stage = ''
        """)
        
        rows_updated = cursor.rowcount
        logger.info(f"Updated {rows_updated} existing records with default status values")
        
        # Ensure all records have status_updated_at values
        cursor = self.connection.execute("""
            UPDATE hearings_unified 
            SET status_updated_at = datetime('now')
            WHERE status_updated_at IS NULL
        """)
        
        time_rows_updated = cursor.rowcount  
        logger.info(f"Updated {time_rows_updated} records with status_updated_at timestamps")
    
    def get_migration_status(self) -> dict:
        """Get current migration status and table info"""
        try:
            # Get table structure
            cursor = self.connection.execute("PRAGMA table_info(hearings_unified)")
            columns = [row['name'] for row in cursor.fetchall()]
            
            # Get record counts by status
            cursor = self.connection.execute("""
                SELECT status, COUNT(*) as count 
                FROM hearings_unified 
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())
            
            # Get record counts by processing_stage  
            cursor = self.connection.execute("""
                SELECT processing_stage, COUNT(*) as count 
                FROM hearings_unified 
                GROUP BY processing_stage
            """)
            stage_counts = dict(cursor.fetchall())
            
            return {
                "migration_applied": "status" in columns,
                "columns_added": [col for col in ["status", "processing_stage", "assigned_reviewer", "status_updated_at", "reviewer_notes"] if col in columns],
                "total_hearings": sum(status_counts.values()) if status_counts else 0,
                "status_distribution": status_counts,
                "stage_distribution": stage_counts,
                "indexes_created": self._check_indexes()
            }
            
        except Exception as e:
            logger.error(f"Error getting migration status: {e}")
            return {"error": str(e)}
    
    def _check_indexes(self) -> list:
        """Check which indexes have been created"""
        cursor = self.connection.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_hearings_%'
        """)
        return [row['name'] for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()

def run_migration():
    """Convenience function to run the migration"""
    migration = StatusMigration()
    try:
        success = migration.run_migration()
        status = migration.get_migration_status()
        print(f"Migration Status: {status}")
        return success
    finally:
        migration.close()

if __name__ == "__main__":
    run_migration()