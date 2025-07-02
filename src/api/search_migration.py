"""
Database migration for Phase 7C Milestone 3: Search & Discovery System
Adds search-optimized columns and indexes to hearings_unified table
"""

import sqlite3
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class SearchMigration:
    """Handles database migration for search functionality"""
    
    def __init__(self, db_path: str = "data/demo_enhanced_ui.db"):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        
    def run_migration(self):
        """Run the complete search migration"""
        logger.info("Starting search migration...")
        
        try:
            self._add_search_columns()
            self._create_search_indexes()
            self._populate_search_fields()
            self._verify_migration()
            self.connection.commit()
            logger.info("Search migration completed successfully")
            return True
        except Exception as e:
            logger.error(f"Search migration failed: {e}")
            self.connection.rollback()
            return False
        finally:
            self.connection.close()
    
    def _add_search_columns(self):
        """Add search-optimized columns"""
        logger.info("Adding search columns...")
        
        # Add search metadata columns
        search_columns = [
            "search_keywords TEXT",  # Extracted keywords for quick search
            "participant_list TEXT",  # Comma-separated list of participants  
            "content_summary TEXT",  # Brief description for search results
            "full_text_content TEXT",  # Full searchable content
            "search_updated_at TEXT"  # Last time search fields were updated
        ]
        
        for column in search_columns:
            try:
                self.connection.execute(f"ALTER TABLE hearings_unified ADD COLUMN {column}")
                logger.info(f"Added column: {column}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    logger.info(f"Column already exists: {column}")
                else:
                    raise e
    
    def _create_search_indexes(self):
        """Create performance indexes for search queries"""
        logger.info("Creating search indexes...")
        
        indexes = [
            # Text search indexes
            ("idx_hearings_title_search", "CREATE INDEX IF NOT EXISTS idx_hearings_title_search ON hearings_unified(hearing_title)"),
            ("idx_hearings_keywords", "CREATE INDEX IF NOT EXISTS idx_hearings_keywords ON hearings_unified(search_keywords)"),
            ("idx_hearings_participants", "CREATE INDEX IF NOT EXISTS idx_hearings_participants ON hearings_unified(participant_list)"),
            
            # Multi-criteria search indexes
            ("idx_hearings_committee_date", "CREATE INDEX IF NOT EXISTS idx_hearings_committee_date ON hearings_unified(committee_code, hearing_date)"),
            ("idx_hearings_status_date", "CREATE INDEX IF NOT EXISTS idx_hearings_status_date ON hearings_unified(status, hearing_date)"),
            ("idx_hearings_type_committee", "CREATE INDEX IF NOT EXISTS idx_hearings_type_committee ON hearings_unified(hearing_type, committee_code)"),
            
            # Date range search indexes
            ("idx_hearings_date_range", "CREATE INDEX IF NOT EXISTS idx_hearings_date_range ON hearings_unified(hearing_date, status)"),
            
            # Full-text search preparation
            ("idx_hearings_full_text", "CREATE INDEX IF NOT EXISTS idx_hearings_full_text ON hearings_unified(full_text_content)")
        ]
        
        for index_name, sql in indexes:
            try:
                self.connection.execute(sql)
                logger.info(f"Created index: {index_name}")
            except sqlite3.OperationalError as e:
                logger.warning(f"Index creation warning for {index_name}: {e}")
    
    def _populate_search_fields(self):
        """Populate search fields with existing data"""
        logger.info("Populating search fields...")
        
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, hearing_title, committee_code, hearing_type, hearing_date FROM hearings_unified")
        hearings = cursor.fetchall()
        
        for hearing in hearings:
            hearing_id, title, committee, hearing_type, date = hearing
            
            # Generate search keywords from title
            keywords = self._extract_keywords(title)
            
            # Create participant list (will be enhanced with real participants later)
            participants = self._generate_participant_list(committee, hearing_type)
            
            # Create content summary
            summary = self._create_content_summary(title, committee, hearing_type, date)
            
            # Create full text content for search
            full_text = self._create_full_text_content(title, committee, hearing_type, participants, summary)
            
            # Update the hearing record
            update_sql = """
                UPDATE hearings_unified 
                SET search_keywords = ?, 
                    participant_list = ?, 
                    content_summary = ?, 
                    full_text_content = ?,
                    search_updated_at = ?
                WHERE id = ?
            """
            
            self.connection.execute(update_sql, (
                keywords, participants, summary, full_text, 
                datetime.now().isoformat(), hearing_id
            ))
        
        logger.info(f"Updated search fields for {len(hearings)} hearings")
    
    def _extract_keywords(self, title: str) -> str:
        """Extract searchable keywords from hearing title"""
        if not title:
            return ""
        
        # Common congressional terms and keywords
        keywords = []
        
        # Split title into words and clean
        words = title.lower().replace('-', ' ').split()
        
        # Remove common stop words but keep meaningful terms
        stop_words = {'and', 'or', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Add the meaningful words
        keywords.extend(meaningful_words)
        
        # Add specific congressional terms
        congressional_terms = {
            'oversight': ['oversight', 'supervision', 'review'],
            'nomination': ['nomination', 'confirmation', 'appointment'],
            'hearing': ['hearing', 'session', 'testimony'],
            'budget': ['budget', 'appropriation', 'funding'],
            'security': ['security', 'defense', 'intelligence'],
            'trade': ['trade', 'commerce', 'economic']
        }
        
        for term, synonyms in congressional_terms.items():
            if any(syn in title.lower() for syn in synonyms):
                keywords.append(term)
        
        return ", ".join(set(keywords))
    
    def _generate_participant_list(self, committee: str, hearing_type: str) -> str:
        """Generate likely participants based on committee and hearing type"""
        participants = []
        
        # Committee-based participants
        committee_chairs = {
            'SCOM': ['Chair Cantwell', 'Ranking Member Cruz'],
            'SSCI': ['Chair Burns', 'Ranking Member Warner'],
            'SSJU': ['Chair Durbin', 'Ranking Member Graham'],
            'SSBH': ['Chair Brown', 'Ranking Member Scott']
        }
        
        if committee in committee_chairs:
            participants.extend(committee_chairs[committee])
        
        # Add common witness types based on hearing type
        if hearing_type and 'nomination' in hearing_type.lower():
            participants.append('Nominees')
        elif hearing_type and 'oversight' in hearing_type.lower():
            participants.extend(['Agency Officials', 'Witnesses'])
        else:
            participants.append('Expert Witnesses')
        
        return ", ".join(participants)
    
    def _create_content_summary(self, title: str, committee: str, hearing_type: str, date: str) -> str:
        """Create a brief content summary for search results"""
        committee_names = {
            'SCOM': 'Senate Commerce Committee',
            'SSCI': 'Senate Intelligence Committee', 
            'SSJU': 'Senate Judiciary Committee',
            'SSBH': 'Senate Banking Committee'
        }
        
        committee_name = committee_names.get(committee, f'{committee} Committee')
        
        summary = f"{committee_name} hearing"
        if hearing_type:
            summary += f" ({hearing_type})"
        if date:
            summary += f" on {date}"
        
        return summary
    
    def _create_full_text_content(self, title: str, committee: str, hearing_type: str, 
                                 participants: str, summary: str) -> str:
        """Create comprehensive searchable content"""
        content_parts = [
            title or "",
            committee or "",
            hearing_type or "",
            participants or "",
            summary or ""
        ]
        
        return " ".join(filter(None, content_parts))
    
    def _verify_migration(self):
        """Verify the migration was successful"""
        logger.info("Verifying migration...")
        
        cursor = self.connection.cursor()
        
        # Check that all search columns exist
        cursor.execute("PRAGMA table_info(hearings_unified)")
        columns = [col[1] for col in cursor.fetchall()]
        
        required_columns = ['search_keywords', 'participant_list', 'content_summary', 
                          'full_text_content', 'search_updated_at']
        
        for col in required_columns:
            if col not in columns:
                raise Exception(f"Required search column missing: {col}")
        
        # Check that search fields are populated
        cursor.execute("SELECT COUNT(*) FROM hearings_unified WHERE search_keywords IS NOT NULL")
        populated_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM hearings_unified")
        total_count = cursor.fetchone()[0]
        
        if populated_count != total_count:
            logger.warning(f"Only {populated_count}/{total_count} hearings have search data")
        else:
            logger.info(f"All {total_count} hearings have search data populated")

def run_search_migration():
    """Main entry point for search migration"""
    migration = SearchMigration()
    return migration.run_migration()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_search_migration()
    print(f"Migration {'completed successfully' if success else 'failed'}")