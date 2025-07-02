"""
Search Management API for Phase 7C Milestone 3: Search & Discovery System
Provides comprehensive search functionality with multiple search modalities,
advanced filtering, auto-complete, and search analytics
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
import sqlite3
import logging
import re
import json
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Request/Response Models
class SearchQuery(BaseModel):
    """Basic search query model"""
    query: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="relevance", pattern="^(relevance|date|title|committee)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

class AdvancedSearchQuery(BaseModel):
    """Advanced search with multiple filters"""
    query: Optional[str] = None
    committee: Optional[str] = None
    status: Optional[str] = None
    processing_stage: Optional[str] = None
    hearing_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    participants: Optional[str] = None
    assigned_reviewer: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="relevance", pattern="^(relevance|date|title|committee|status)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

class MemberSearchQuery(BaseModel):
    """Member/participant search model"""
    name: Optional[str] = None
    committee: Optional[str] = None
    role: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)

class SearchResult(BaseModel):
    """Single search result model"""
    id: int
    hearing_title: str
    committee_code: str
    hearing_date: str
    hearing_type: Optional[str]
    status: Optional[str]
    processing_stage: Optional[str]
    content_summary: Optional[str]
    participant_list: Optional[str]
    relevance_score: float
    search_highlights: Dict[str, List[str]]

class SearchResponse(BaseModel):
    """Search response with results and metadata"""
    results: List[SearchResult]
    total_count: int
    page_info: Dict[str, Any]
    search_metadata: Dict[str, Any]
    took_ms: int

class AutoCompleteResponse(BaseModel):
    """Auto-complete suggestions response"""
    suggestions: List[Dict[str, Any]]
    categories: Dict[str, List[str]]

class SearchHistoryItem(BaseModel):
    """Search history item"""
    query: str
    timestamp: str
    result_count: int
    filters_applied: Dict[str, Any]

class SearchStatsResponse(BaseModel):
    """Search analytics and statistics"""
    total_searches: int
    popular_queries: List[Dict[str, Any]]
    search_trends: Dict[str, Any]
    committee_search_distribution: Dict[str, int]

# Database connection utility
def get_search_db():
    """Get database connection for search operations"""
    return sqlite3.connect("data/demo_enhanced_ui.db")

class SearchManager:
    """Main search functionality manager"""
    
    def __init__(self):
        self.db_path = "data/demo_enhanced_ui.db"
    
    def search_hearings(self, query: SearchQuery) -> SearchResponse:
        """Basic text search across hearings"""
        start_time = datetime.now()
        
        conn = get_search_db()
        cursor = conn.cursor()
        
        try:
            # Build SQL query
            where_clauses = []
            params = []
            
            if query.query:
                # Full-text search across multiple fields
                search_sql = """
                    (hearing_title LIKE ? OR 
                     search_keywords LIKE ? OR 
                     participant_list LIKE ? OR 
                     content_summary LIKE ? OR
                     full_text_content LIKE ?)
                """
                search_term = f"%{query.query}%"
                where_clauses.append(search_sql)
                params.extend([search_term] * 5)
            
            # Build main query
            base_sql = """
                SELECT id, hearing_title, committee_code, hearing_date, hearing_type,
                       status, processing_stage, content_summary, participant_list,
                       search_keywords, full_text_content
                FROM hearings_unified
            """
            
            if where_clauses:
                base_sql += " WHERE " + " AND ".join(where_clauses)
            
            # Add sorting
            sort_column = self._get_sort_column(query.sort_by)
            base_sql += f" ORDER BY {sort_column} {query.sort_order.upper()}"
            
            # Add pagination
            base_sql += " LIMIT ? OFFSET ?"
            params.extend([query.limit, query.offset])
            
            # Execute query
            cursor.execute(base_sql, params)
            rows = cursor.fetchall()
            
            # Get total count
            count_sql = "SELECT COUNT(*) FROM hearings_unified"
            if where_clauses:
                count_sql += " WHERE " + " AND ".join(where_clauses)
            cursor.execute(count_sql, params[:-2])  # Exclude LIMIT/OFFSET params
            total_count = cursor.fetchone()[0]
            
            # Process results
            results = []
            for row in rows:
                relevance_score = self._calculate_relevance(row, query.query)
                highlights = self._generate_highlights(row, query.query)
                
                result = SearchResult(
                    id=row[0],
                    hearing_title=row[1],
                    committee_code=row[2],
                    hearing_date=row[3],
                    hearing_type=row[4],
                    status=row[5],
                    processing_stage=row[6],
                    content_summary=row[7],
                    participant_list=row[8],
                    relevance_score=relevance_score,
                    search_highlights=highlights
                )
                results.append(result)
            
            # Calculate timing
            took_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return SearchResponse(
                results=results,
                total_count=total_count,
                page_info={
                    "current_page": (query.offset // query.limit) + 1,
                    "total_pages": (total_count + query.limit - 1) // query.limit,
                    "has_next": query.offset + query.limit < total_count,
                    "has_prev": query.offset > 0
                },
                search_metadata={
                    "query": query.query,
                    "filters_applied": {},
                    "sort_by": query.sort_by,
                    "sort_order": query.sort_order
                },
                took_ms=took_ms
            )
            
        finally:
            conn.close()
    
    def advanced_search(self, query: AdvancedSearchQuery) -> SearchResponse:
        """Advanced search with multiple filters"""
        start_time = datetime.now()
        
        conn = get_search_db()
        cursor = conn.cursor()
        
        try:
            where_clauses = []
            params = []
            filters_applied = {}
            
            # Text search
            if query.query:
                search_sql = """
                    (hearing_title LIKE ? OR 
                     search_keywords LIKE ? OR 
                     participant_list LIKE ? OR 
                     content_summary LIKE ?)
                """
                search_term = f"%{query.query}%"
                where_clauses.append(search_sql)
                params.extend([search_term] * 4)
                filters_applied["text_query"] = query.query
            
            # Committee filter
            if query.committee:
                where_clauses.append("committee_code = ?")
                params.append(query.committee)
                filters_applied["committee"] = query.committee
            
            # Status filters
            if query.status:
                where_clauses.append("status = ?")
                params.append(query.status)
                filters_applied["status"] = query.status
            
            if query.processing_stage:
                where_clauses.append("processing_stage = ?")
                params.append(query.processing_stage)
                filters_applied["processing_stage"] = query.processing_stage
            
            # Hearing type filter
            if query.hearing_type:
                where_clauses.append("hearing_type LIKE ?")
                params.append(f"%{query.hearing_type}%")
                filters_applied["hearing_type"] = query.hearing_type
            
            # Date range filters
            if query.date_from:
                where_clauses.append("hearing_date >= ?")
                params.append(query.date_from)
                filters_applied["date_from"] = query.date_from
            
            if query.date_to:
                where_clauses.append("hearing_date <= ?")
                params.append(query.date_to)
                filters_applied["date_to"] = query.date_to
            
            # Participant filter
            if query.participants:
                where_clauses.append("participant_list LIKE ?")
                params.append(f"%{query.participants}%")
                filters_applied["participants"] = query.participants
            
            # Reviewer filter
            if query.assigned_reviewer:
                where_clauses.append("assigned_reviewer = ?")
                params.append(query.assigned_reviewer)
                filters_applied["assigned_reviewer"] = query.assigned_reviewer
            
            # Build main query
            base_sql = """
                SELECT id, hearing_title, committee_code, hearing_date, hearing_type,
                       status, processing_stage, content_summary, participant_list,
                       search_keywords, full_text_content
                FROM hearings_unified
            """
            
            if where_clauses:
                base_sql += " WHERE " + " AND ".join(where_clauses)
            
            # Add sorting
            sort_column = self._get_sort_column(query.sort_by)
            base_sql += f" ORDER BY {sort_column} {query.sort_order.upper()}"
            
            # Add pagination
            base_sql += " LIMIT ? OFFSET ?"
            params.extend([query.limit, query.offset])
            
            # Execute query
            cursor.execute(base_sql, params)
            rows = cursor.fetchall()
            
            # Get total count
            count_sql = "SELECT COUNT(*) FROM hearings_unified"
            if where_clauses:
                count_sql += " WHERE " + " AND ".join(where_clauses)
            cursor.execute(count_sql, params[:-2])
            total_count = cursor.fetchone()[0]
            
            # Process results
            results = []
            for row in rows:
                relevance_score = self._calculate_relevance(row, query.query)
                highlights = self._generate_highlights(row, query.query)
                
                result = SearchResult(
                    id=row[0],
                    hearing_title=row[1],
                    committee_code=row[2],
                    hearing_date=row[3],
                    hearing_type=row[4],
                    status=row[5],
                    processing_stage=row[6],
                    content_summary=row[7],
                    participant_list=row[8],
                    relevance_score=relevance_score,
                    search_highlights=highlights
                )
                results.append(result)
            
            took_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return SearchResponse(
                results=results,
                total_count=total_count,
                page_info={
                    "current_page": (query.offset // query.limit) + 1,
                    "total_pages": (total_count + query.limit - 1) // query.limit,
                    "has_next": query.offset + query.limit < total_count,
                    "has_prev": query.offset > 0
                },
                search_metadata={
                    "query": query.query,
                    "filters_applied": filters_applied,
                    "sort_by": query.sort_by,
                    "sort_order": query.sort_order
                },
                took_ms=took_ms
            )
            
        finally:
            conn.close()
    
    def search_members(self, query: MemberSearchQuery) -> List[Dict[str, Any]]:
        """Search for committee members and participants"""
        conn = get_search_db()
        cursor = conn.cursor()
        
        try:
            where_clauses = []
            params = []
            
            if query.name:
                where_clauses.append("participant_list LIKE ?")
                params.append(f"%{query.name}%")
            
            if query.committee:
                where_clauses.append("committee_code = ?")
                params.append(query.committee)
            
            sql = """
                SELECT DISTINCT committee_code, participant_list, hearing_title, hearing_date
                FROM hearings_unified
            """
            
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
            
            sql += " LIMIT ?"
            params.append(query.limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # Process participant data
            results = []
            for row in rows:
                committee, participants, title, date = row
                if participants:
                    participant_list = participants.split(", ")
                    for participant in participant_list:
                        if not query.name or query.name.lower() in participant.lower():
                            results.append({
                                "name": participant,
                                "committee": committee,
                                "hearing_title": title,
                                "hearing_date": date,
                                "role": self._extract_role(participant)
                            })
            
            return results[:query.limit]
            
        finally:
            conn.close()
    
    def get_autocomplete_suggestions(self, partial_query: str, limit: int = 10) -> AutoCompleteResponse:
        """Get auto-complete suggestions for search queries"""
        conn = get_search_db()
        cursor = conn.cursor()
        
        try:
            suggestions = []
            categories = {
                "hearings": [],
                "committees": [],
                "participants": [],
                "keywords": []
            }
            
            # Hearing title suggestions
            cursor.execute(
                "SELECT DISTINCT hearing_title FROM hearings_unified WHERE hearing_title LIKE ? LIMIT ?",
                (f"%{partial_query}%", limit)
            )
            for row in cursor.fetchall():
                title = row[0]
                suggestions.append({
                    "text": title,
                    "type": "hearing",
                    "category": "hearings",
                    "score": self._calculate_suggestion_score(title, partial_query)
                })
                categories["hearings"].append(title)
            
            # Committee suggestions
            cursor.execute(
                "SELECT DISTINCT committee_code FROM hearings_unified WHERE committee_code LIKE ? LIMIT ?",
                (f"%{partial_query}%", limit)
            )
            for row in cursor.fetchall():
                committee = row[0]
                suggestions.append({
                    "text": committee,
                    "type": "committee",
                    "category": "committees",
                    "score": self._calculate_suggestion_score(committee, partial_query)
                })
                categories["committees"].append(committee)
            
            # Keyword suggestions
            cursor.execute(
                "SELECT DISTINCT search_keywords FROM hearings_unified WHERE search_keywords LIKE ? LIMIT ?",
                (f"%{partial_query}%", limit)
            )
            for row in cursor.fetchall():
                keywords = row[0]
                if keywords:
                    for keyword in keywords.split(", "):
                        if partial_query.lower() in keyword.lower():
                            suggestions.append({
                                "text": keyword,
                                "type": "keyword",
                                "category": "keywords",
                                "score": self._calculate_suggestion_score(keyword, partial_query)
                            })
                            categories["keywords"].append(keyword)
            
            # Sort by relevance score
            suggestions.sort(key=lambda x: x["score"], reverse=True)
            
            return AutoCompleteResponse(
                suggestions=suggestions[:limit],
                categories=categories
            )
            
        finally:
            conn.close()
    
    def _get_sort_column(self, sort_by: str) -> str:
        """Get SQL column name for sorting"""
        sort_mapping = {
            "relevance": "hearing_date",  # Default to date for relevance
            "date": "hearing_date",
            "title": "hearing_title",
            "committee": "committee_code",
            "status": "status"
        }
        return sort_mapping.get(sort_by, "hearing_date")
    
    def _calculate_relevance(self, row: tuple, query: Optional[str]) -> float:
        """Calculate relevance score for search result"""
        if not query:
            return 1.0
        
        score = 0.0
        query_lower = query.lower()
        
        # Title match (highest weight)
        if query_lower in row[1].lower():
            score += 0.4
        
        # Keywords match
        if row[9] and query_lower in row[9].lower():
            score += 0.3
        
        # Participants match
        if row[8] and query_lower in row[8].lower():
            score += 0.2
        
        # Content summary match
        if row[7] and query_lower in row[7].lower():
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_highlights(self, row: tuple, query: Optional[str]) -> Dict[str, List[str]]:
        """Generate search result highlights"""
        highlights = {}
        
        if not query:
            return highlights
        
        query_lower = query.lower()
        
        # Highlight title
        if query_lower in row[1].lower():
            highlights["title"] = [self._highlight_text(row[1], query)]
        
        # Highlight content summary
        if row[7] and query_lower in row[7].lower():
            highlights["summary"] = [self._highlight_text(row[7], query)]
        
        return highlights
    
    def _highlight_text(self, text: str, query: str) -> str:
        """Add highlighting markers to text"""
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(f"<mark>{query}</mark>", text)
    
    def _extract_role(self, participant: str) -> str:
        """Extract role from participant string"""
        if "Chair" in participant:
            return "Committee Chair"
        elif "Ranking" in participant:
            return "Ranking Member"
        elif "Sen." in participant or "Senator" in participant:
            return "Senator"
        elif "Rep." in participant or "Representative" in participant:
            return "Representative"
        else:
            return "Witness"
    
    def _calculate_suggestion_score(self, suggestion: str, query: str) -> float:
        """Calculate relevance score for auto-complete suggestions"""
        if query.lower() == suggestion.lower():
            return 1.0
        elif suggestion.lower().startswith(query.lower()):
            return 0.8
        elif query.lower() in suggestion.lower():
            return 0.6
        else:
            return 0.3

# Initialize search manager
search_manager = SearchManager()

# API Router
router = APIRouter(prefix="/api/search", tags=["search"])

@router.get("/hearings", response_model=SearchResponse)
async def search_hearings(
    query: Optional[str] = Query(None, description="Search query text"),
    limit: int = Query(20, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_by: str = Query("relevance", pattern="^(relevance|date|title|committee)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$")
):
    """Basic text search across hearings"""
    try:
        search_query = SearchQuery(
            query=query,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return search_manager.search_hearings(search_query)
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/advanced", response_model=SearchResponse)
async def advanced_search(query: AdvancedSearchQuery):
    """Advanced search with multiple filters"""
    try:
        return search_manager.advanced_search(query)
    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        raise HTTPException(status_code=500, detail=f"Advanced search failed: {str(e)}")

@router.get("/members")
async def search_members(
    name: Optional[str] = Query(None, description="Member name to search"),
    committee: Optional[str] = Query(None, description="Committee code filter"),
    role: Optional[str] = Query(None, description="Role filter"),
    limit: int = Query(10, ge=1, le=50, description="Number of results")
):
    """Search for committee members and participants"""
    try:
        query = MemberSearchQuery(name=name, committee=committee, role=role, limit=limit)
        return search_manager.search_members(query)
    except Exception as e:
        logger.error(f"Member search error: {e}")
        raise HTTPException(status_code=500, detail=f"Member search failed: {str(e)}")

@router.get("/suggest", response_model=AutoCompleteResponse)
async def get_suggestions(
    q: str = Query(..., description="Partial query for suggestions"),
    limit: int = Query(10, ge=1, le=20, description="Number of suggestions")
):
    """Get auto-complete suggestions"""
    try:
        return search_manager.get_autocomplete_suggestions(q, limit)
    except Exception as e:
        logger.error(f"Suggestion error: {e}")
        raise HTTPException(status_code=500, detail=f"Suggestions failed: {str(e)}")

@router.get("/stats", response_model=SearchStatsResponse)
async def get_search_stats():
    """Get search analytics and statistics"""
    try:
        # For now, return mock data - can be enhanced with real analytics
        return SearchStatsResponse(
            total_searches=0,
            popular_queries=[],
            search_trends={},
            committee_search_distribution={}
        )
    except Exception as e:
        logger.error(f"Search stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Search stats failed: {str(e)}")

def setup_search_routes(app):
    """Setup search routes in the main FastAPI app"""
    app.include_router(router)