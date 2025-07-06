"""
Main FastAPI application for Phase 7B Enhanced UI.
Integrates all API endpoints and serves the React dashboard.
"""

from fastapi import FastAPI, Request, HTTPException, Body, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any

# Import API modules
from hearing_management import setup_hearing_management_routes
from system_monitoring import setup_system_monitoring_routes
from status_management import setup_status_management_routes
from search_management import setup_search_routes
from transcript_management import setup_transcript_routes
from discovery_management import setup_discovery_management_routes
from database_enhanced import get_enhanced_db
try:
    from .health import router as health_router
except ImportError as e:
    logger.warning(f"Health router import failed: {e}")
    health_router = None

# Import existing dashboard data API
from .dashboard_data import DashboardDataAPI

# Production imports
import os
try:
    from ..config.production import config
except ImportError:
    config = None

try:
    from ..monitoring.metrics import start_metrics_server, metrics_collector
except ImportError:
    start_metrics_server = None
    metrics_collector = None

PRODUCTION_MODE = os.getenv('ENV', 'development') == 'production'

logger = logging.getLogger(__name__)

class EnhancedUIApp:
    """Main application class for Phase 7B Enhanced UI"""
    
    def __init__(self):
        self.app = FastAPI(
            title="Senate Hearing Audio Capture - Enhanced UI",
            description="Phase 7B Enhanced UI with automated hearing discovery and management",
            version="7B.1.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc"
        )
        
        self.db = get_enhanced_db()
        self.dashboard_api = DashboardDataAPI()
        
        self._setup_middleware()
        self._setup_startup_events()
        self._setup_routes()
        self._setup_static_files()
        self._initialize_demo_data()
    
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        
        # CORS middleware for React development
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React dev server
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Gzip compression for better performance
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        # Request logging middleware
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = datetime.now()
            response = await call_next(request)
            process_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            return response
    
    def _setup_startup_events(self):
        """Setup startup events for automatic database bootstrap"""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Auto-bootstrap database on every startup"""
            try:
                logger.info("Checking database state on startup...")
                
                # Force database creation and get connection
                db = get_enhanced_db()
                db._create_schema()
                
                # Always ensure bootstrap data exists (Cloud Run containers are ephemeral)
                logger.info("Ensuring bootstrap data exists...")
                
                # Default committees for bootstrap
                DEFAULT_COMMITTEES = [
                        {
                            'committee_code': 'SCOM',
                            'committee_name': 'Senate Committee on Commerce, Science, and Transportation',
                        },
                        {
                            'committee_code': 'SSCI',
                            'committee_name': 'Senate Select Committee on Intelligence',
                        },
                        {
                            'committee_code': 'SSJU',
                            'committee_name': 'Senate Committee on the Judiciary',
                        }
                ]
                
                # Bootstrap committees
                committees_added = 0
                for committee in DEFAULT_COMMITTEES:
                    try:
                        # Create a sample hearing for each committee to bootstrap the system
                        hearing_id = f"{committee['committee_code']}-BOOTSTRAP-{datetime.now().strftime('%Y%m%d')}"
                        
                        db.connection.execute("""
                            INSERT OR REPLACE INTO hearings_unified 
                            (committee_code, hearing_title, hearing_date, hearing_type, 
                             sync_confidence, streams, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            committee['committee_code'],
                            f"Bootstrap Entry for {committee['committee_name']}",
                            datetime.now().strftime('%Y-%m-%d'),
                            'Setup',
                            1.0,
                            '{}',
                            datetime.now().isoformat(),
                            datetime.now().isoformat()
                        ))
                        
                        committees_added += 1
                        logger.info(f"Added bootstrap entry for {committee['committee_code']}")
                        
                    except Exception as e:
                        logger.error(f"Error adding bootstrap entry for {committee['committee_code']}: {e}")
                
                db.connection.commit()
                logger.info(f"Auto-bootstrap completed: {committees_added} committees added")
                
            except Exception as e:
                logger.error(f"Error during startup bootstrap: {e}")
                # Don't fail the startup if bootstrap fails
                pass
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        # Root route is now handled by static file serving in _setup_static_files()
        
        @self.app.get("/api")
        async def api_info():
            """API information endpoint"""
            return {
                "name": "Senate Hearing Audio Capture API",
                "version": "7B.1.0",
                "phase": "Phase 7B - Enhanced UI/UX Workflows",
                "features": [
                    "Automated hearing discovery and synchronization",
                    "Real-time system monitoring",
                    "Enhanced transcript review workflows",
                    "Duplicate resolution management",
                    "Quality metrics and analytics"
                ],
                "endpoints": {
                    "hearings": "/api/hearings/*",
                    "system": "/api/system/*",
                    "transcripts": "/api/transcripts/*",
                    "websocket": "/ws/*"
                },
                "documentation": "/api/docs",
                "timestamp": datetime.now().isoformat()
            }
        
        # Legacy dashboard data endpoints (maintain backwards compatibility)
        @self.app.get("/dashboard-data")
        async def get_dashboard_data():
            """Legacy dashboard data endpoint"""
            return self.dashboard_api.get_dashboard_data()
        
        @self.app.get("/transcripts")
        async def get_transcripts():
            """Legacy transcripts endpoint"""
            return self.dashboard_api.get_transcripts()
        
        @self.app.get("/transcript/{transcript_id}")
        async def get_transcript_content(transcript_id: str):
            """Legacy transcript content endpoint"""
            return self.dashboard_api.get_transcript_content(transcript_id)
        
        # Enhanced API endpoints (with /api prefix)
        @self.app.get("/api/transcripts")
        async def get_api_transcripts():
            """Get list of transcripts (API version)"""
            try:
                return self.dashboard_api.get_transcripts()
            except Exception as e:
                logger.error(f"Error getting transcripts: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Failed to load transcripts", "detail": str(e)}
                )
        
        @self.app.get("/api/transcripts/{transcript_id}")
        async def get_api_transcript_content(transcript_id: str):
            """Get specific transcript content (API version)"""
            try:
                return self.dashboard_api.get_transcript_content(transcript_id)
            except Exception as e:
                logger.error(f"Error getting transcript {transcript_id}: {e}")
                return JSONResponse(
                    status_code=404,
                    content={"error": "Transcript not found", "detail": str(e)}
                )
        
        @self.app.get("/api/committees")
        async def get_committees():
            """Get committee statistics and hearing counts"""
            try:
                # Get committee stats from database
                cursor = self.db.connection.execute("""
                    SELECT 
                        committee_code,
                        COUNT(*) as hearing_count,
                        MAX(hearing_date) as latest_hearing,
                        AVG(sync_confidence) as avg_confidence
                    FROM hearings_unified 
                    GROUP BY committee_code
                    ORDER BY hearing_count DESC
                """)
                
                committees = []
                committee_names = {
                    'SCOM': 'Commerce, Science, and Transportation',
                    'SSCI': 'Intelligence', 
                    'SBAN': 'Banking, Housing, and Urban Affairs',
                    'SSJU': 'Judiciary',
                    'HJUD': 'House Judiciary'
                }
                
                for row in cursor.fetchall():
                    committees.append({
                        'code': row[0],
                        'name': committee_names.get(row[0], row[0]),
                        'hearing_count': row[1],
                        'latest_hearing': row[2],
                        'avg_confidence': round(row[3], 2) if row[3] else 0
                    })
                
                return {
                    'committees': committees,
                    'total_committees': len(committees),
                    'total_hearings': sum(c['hearing_count'] for c in committees)
                }
                
            except Exception as e:
                logger.error(f"Error getting committees: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Failed to load committees", "detail": str(e)}
                )
        
        @self.app.get("/api/committees/{committee_code}/hearings")
        async def get_committee_hearings(committee_code: str):
            """Get all hearings for a specific committee"""
            try:
                cursor = self.db.connection.execute("""
                    SELECT 
                        id,
                        committee_code,
                        hearing_title,
                        hearing_date,
                        hearing_type,
                        sync_confidence,
                        streams,
                        created_at,
                        updated_at
                    FROM hearings_unified 
                    WHERE committee_code = ?
                    ORDER BY hearing_date DESC
                """, (committee_code.upper(),))
                
                hearings = []
                for row in cursor.fetchall():
                    hearings.append({
                        'id': row[0],
                        'committee_code': row[1],
                        'title': row[2],
                        'date': row[3],
                        'type': row[4],
                        'sync_confidence': row[5],
                        'streams': json.loads(row[6]) if row[6] else {},
                        'created_at': row[7],
                        'updated_at': row[8]
                    })
                
                committee_names = {
                    'SCOM': 'Commerce, Science, and Transportation',
                    'SSCI': 'Intelligence', 
                    'SBAN': 'Banking, Housing, and Urban Affairs',
                    'SSJU': 'Judiciary',
                    'HJUD': 'House Judiciary'
                }
                
                return {
                    'committee': {
                        'code': committee_code.upper(),
                        'name': committee_names.get(committee_code.upper(), committee_code.upper())
                    },
                    'hearings': hearings,
                    'total_hearings': len(hearings)
                }
                
            except Exception as e:
                logger.error(f"Error getting hearings for committee {committee_code}: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Failed to load hearings for {committee_code}", "detail": str(e)}
                )
        
        @self.app.get("/api/hearings/{hearing_id}")
        async def get_hearing_details(hearing_id: int):
            """Get details for a specific hearing"""
            try:
                cursor = self.db.connection.execute("""
                    SELECT 
                        id,
                        committee_code,
                        hearing_title,
                        hearing_date,
                        hearing_type,
                        sync_confidence,
                        streams,
                        created_at,
                        updated_at,
                        status,
                        processing_stage,
                        assigned_reviewer,
                        status_updated_at,
                        reviewer_notes,
                        search_keywords,
                        participant_list,
                        content_summary
                    FROM hearings_unified 
                    WHERE id = ?
                """, (hearing_id,))
                
                row = cursor.fetchone()
                if not row:
                    return JSONResponse(
                        status_code=404,
                        content={"error": "Hearing not found", "hearing_id": hearing_id}
                    )
                
                hearing_data = {
                    'id': row[0],
                    'committee_code': row[1],
                    'hearing_title': row[2],
                    'hearing_date': row[3],
                    'hearing_type': row[4],
                    'sync_confidence': row[5],
                    'streams': json.loads(row[6]) if row[6] else {},
                    'created_at': row[7],
                    'updated_at': row[8],
                    'status': row[9],
                    'processing_stage': row[10],
                    'assigned_reviewer': row[11],
                    'status_updated_at': row[12],
                    'reviewer_notes': row[13],
                    'search_keywords': row[14],
                    'participant_list': row[15],
                    'content_summary': row[16],
                    'has_streams': bool(json.loads(row[6]) if row[6] else {})
                }
                
                return {
                    'hearing': hearing_data
                }
                
            except Exception as e:
                logger.error(f"Error getting hearing {hearing_id}: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Failed to load hearing {hearing_id}", "detail": str(e)}
                )

        @self.app.post("/api/hearings/{hearing_id}/capture")
        async def capture_hearing_audio(hearing_id: int, request_data: dict = Body(...), user_id: str = Query(None)):
            """Capture audio for a specific hearing"""
            try:
                # Get hearing details first
                cursor = self.db.connection.execute("""
                    SELECT hearing_title, streams, status, processing_stage 
                    FROM hearings_unified 
                    WHERE id = ?
                """, (hearing_id,))
                
                row = cursor.fetchone()
                if not row:
                    return JSONResponse(
                        status_code=404,
                        content={"error": "Hearing not found", "hearing_id": hearing_id}
                    )
                
                hearing_title, streams_json, status, processing_stage = row
                streams = json.loads(streams_json) if streams_json else {}
                
                # Check if hearing can be captured
                if not streams or 'isvp' not in streams:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "No ISVP stream available for this hearing", "hearing_id": hearing_id}
                    )
                
                # Update hearing status to indicate capture started
                self.db.connection.execute("""
                    UPDATE hearings_unified 
                    SET status = 'processing', 
                        processing_stage = 'captured',
                        status_updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), hearing_id))
                self.db.connection.commit()
                
                # Return success response (in production, this would trigger actual capture)
                return {
                    "capture_id": hearing_id,
                    "status": "initiated",
                    "hearing_title": hearing_title,
                    "stream_url": streams.get('isvp'),
                    "message": f"Audio capture initiated for '{hearing_title}'"
                }
                
            except Exception as e:
                logger.error(f"Error capturing hearing {hearing_id}: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Failed to initiate capture for hearing {hearing_id}", "detail": str(e)}
                )

        @self.app.get("/api/hearings/{hearing_id}/status")
        async def get_hearing_status(hearing_id: int):
            """Get processing status for a specific hearing"""
            try:
                cursor = self.db.connection.execute("""
                    SELECT 
                        id, hearing_title, status, processing_stage, 
                        status_updated_at, assigned_reviewer, reviewer_notes
                    FROM hearings_unified 
                    WHERE id = ?
                """, (hearing_id,))
                
                row = cursor.fetchone()
                if not row:
                    return JSONResponse(
                        status_code=404,
                        content={"error": "Hearing not found", "hearing_id": hearing_id}
                    )
                
                return {
                    "hearing_id": row[0],
                    "hearing_title": row[1],
                    "status": row[2],
                    "processing_stage": row[3],
                    "status_updated_at": row[4],
                    "assigned_reviewer": row[5],
                    "reviewer_notes": row[6],
                    "progress_percentage": {
                        'discovered': 10,
                        'analyzed': 20,
                        'captured': 40,
                        'transcribed': 70,
                        'reviewed': 90,
                        'published': 100
                    }.get(row[3], 0)
                }
                
            except Exception as e:
                logger.error(f"Error getting status for hearing {hearing_id}: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Failed to get status for hearing {hearing_id}", "detail": str(e)}
                )

        @self.app.get("/api/committees/{committee_code}/stats")
        async def get_committee_stats(committee_code: str):
            """Get detailed statistics for a specific committee"""
            try:
                # Basic stats
                cursor = self.db.connection.execute("""
                    SELECT 
                        COUNT(*) as total_hearings,
                        MIN(hearing_date) as earliest_hearing,
                        MAX(hearing_date) as latest_hearing,
                        AVG(sync_confidence) as avg_confidence,
                        COUNT(DISTINCT hearing_type) as hearing_types
                    FROM hearings_unified 
                    WHERE committee_code = ?
                """, (committee_code.upper(),))
                
                stats_row = cursor.fetchone()
                
                # Hearing types breakdown
                cursor = self.db.connection.execute("""
                    SELECT 
                        hearing_type,
                        COUNT(*) as count
                    FROM hearings_unified 
                    WHERE committee_code = ?
                    GROUP BY hearing_type
                    ORDER BY count DESC
                """, (committee_code.upper(),))
                
                hearing_types = []
                for row in cursor.fetchall():
                    hearing_types.append({
                        'type': row[0],
                        'count': row[1]
                    })
                
                # Recent activity (last 30 days)
                cursor = self.db.connection.execute("""
                    SELECT COUNT(*) as recent_hearings
                    FROM hearings_unified 
                    WHERE committee_code = ? 
                    AND hearing_date >= date('now', '-30 days')
                """, (committee_code.upper(),))
                
                recent_activity = cursor.fetchone()[0]
                
                committee_names = {
                    'SCOM': 'Commerce, Science, and Transportation',
                    'SSCI': 'Intelligence', 
                    'SBAN': 'Banking, Housing, and Urban Affairs',
                    'SSJU': 'Judiciary',
                    'HJUD': 'House Judiciary'
                }
                
                return {
                    'committee': {
                        'code': committee_code.upper(),
                        'name': committee_names.get(committee_code.upper(), committee_code.upper())
                    },
                    'stats': {
                        'total_hearings': stats_row[0],
                        'earliest_hearing': stats_row[1],
                        'latest_hearing': stats_row[2],
                        'avg_confidence': round(stats_row[3], 2) if stats_row[3] else 0,
                        'hearing_types': hearing_types,
                        'recent_activity': recent_activity
                    }
                }
                
            except Exception as e:
                logger.error(f"Error getting stats for committee {committee_code}: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Failed to load stats for {committee_code}", "detail": str(e)}
                )
        
        # Direct capture endpoint for compatibility
        @self.app.post("/api/capture")
        async def direct_capture(request_data: dict):
            """Direct capture endpoint for compatibility with test scripts"""
            from .capture_service import get_capture_service, CaptureException
            
            try:
                hearing_id = request_data.get('hearing_id')
                hearing_url = request_data.get('hearing_url')
                
                if not hearing_id or not hearing_url:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Missing hearing_id or hearing_url"}
                    )
                
                capture_service = get_capture_service()
                result = await capture_service.capture_hearing_audio(
                    hearing_id=hearing_id,
                    hearing_url=hearing_url,
                    capture_options=request_data.get('capture_options', {})
                )
                
                return {
                    "capture_id": result.get('hearing_id'),
                    "status": "initiated",
                    "result": result
                }
                
            except CaptureException as e:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Capture failed: {str(e)}"}
                )
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Unexpected error: {str(e)}"}
                )
        
        # Direct transcription endpoint
        @self.app.post("/api/transcription")
        async def direct_transcription(request_data: dict):
            """Direct transcription endpoint for compatibility with test scripts"""
            from .transcription_service import get_transcription_service, TranscriptionException
            
            try:
                hearing_id = request_data.get('hearing_id')
                
                if not hearing_id:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Missing hearing_id"}
                    )
                
                transcription_service = get_transcription_service()
                result = await transcription_service.transcribe_hearing(
                    hearing_id=hearing_id,
                    transcription_options=request_data.get('transcription_options', {})
                )
                
                return {
                    "transcription_id": result.get('hearing_id'),
                    "status": "initiated",
                    "result": result
                }
                
            except TranscriptionException as e:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Transcription failed: {str(e)}"}
                )
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Unexpected error: {str(e)}"}
                )

        # Congress API test endpoint
        @self.app.get("/api/test/congress")
        async def test_congress_api():
            """Test Congress API connectivity and functionality"""
            import requests
            
            # Get API key from environment
            congress_api_key = os.environ.get('CONGRESS_API_KEY')
            if not congress_api_key:
                return JSONResponse(
                    status_code=500,
                    content={"error": "Congress API key not configured"}
                )
            
            results = {
                "api_key_configured": True,
                "api_key_preview": congress_api_key[:10] + "..." if len(congress_api_key) > 10 else congress_api_key,
                "tests": {}
            }
            
            try:
                # Test 1: Basic API connectivity
                url = "https://api.congress.gov/v3/member"
                params = {
                    'api_key': congress_api_key,
                    'format': 'json',
                    'limit': 3
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    members = data.get('members', [])
                    results["tests"]["basic_connectivity"] = {
                        "success": True,
                        "message": f"Retrieved {len(members)} members successfully",
                        "sample_member": members[0].get('name', 'Unknown') if members else None
                    }
                else:
                    results["tests"]["basic_connectivity"] = {
                        "success": False,
                        "message": f"API call failed with status {response.status_code}",
                        "error": response.text
                    }
                
                # Test 2: Committee data
                committee_url = "https://api.congress.gov/v3/committee/senate/scom"
                committee_params = {
                    'api_key': congress_api_key,
                    'format': 'json'
                }
                
                committee_response = requests.get(committee_url, params=committee_params, timeout=30)
                
                if committee_response.status_code == 200:
                    committee_data = committee_response.json()
                    committee = committee_data.get('committee', {})
                    results["tests"]["committee_data"] = {
                        "success": True,
                        "message": f"Retrieved committee: {committee.get('name', 'Unknown')}",
                        "committee_code": committee.get('systemCode', 'Unknown')
                    }
                else:
                    results["tests"]["committee_data"] = {
                        "success": False,
                        "message": f"Committee API call failed with status {committee_response.status_code}",
                        "error": committee_response.text
                    }
                
                # Test 3: Recent hearings
                hearings_url = "https://api.congress.gov/v3/hearing"
                hearings_params = {
                    'api_key': congress_api_key,
                    'format': 'json',
                    'limit': 2
                }
                
                hearings_response = requests.get(hearings_url, params=hearings_params, timeout=30)
                
                if hearings_response.status_code == 200:
                    hearings_data = hearings_response.json()
                    hearings = hearings_data.get('hearings', [])
                    results["tests"]["hearing_data"] = {
                        "success": True,
                        "message": f"Retrieved {len(hearings)} hearings successfully",
                        "sample_hearing": hearings[0].get('title', 'Unknown') if hearings else None
                    }
                else:
                    results["tests"]["hearing_data"] = {
                        "success": False,
                        "message": f"Hearings API call failed with status {hearings_response.status_code}",
                        "error": hearings_response.text
                    }
                
                # Overall status
                successful_tests = sum(1 for test in results["tests"].values() if test["success"])
                total_tests = len(results["tests"])
                results["overall_status"] = {
                    "success": successful_tests == total_tests,
                    "successful_tests": successful_tests,
                    "total_tests": total_tests,
                    "ready_for_sync": successful_tests >= 2
                }
                
                return results
                
            except Exception as e:
                logger.error(f"Error testing Congress API: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Congress API test failed", "detail": str(e)}
                )

        # Enhanced API endpoints
        @self.app.get("/api/overview")
        async def get_system_overview():
            """Get system overview combining multiple data sources"""
            
            try:
                # Get hearing queue summary
                hearing_queue = self._get_hearing_queue_summary()
                
                # Get system health summary
                health_summary = self._get_health_summary()
                
                # Get recent activity
                recent_activity = self._get_recent_activity()
                
                # Get performance metrics
                performance = self._get_performance_summary()
                
                return {
                    "overview": {
                        "hearing_queue": hearing_queue,
                        "system_health": health_summary,
                        "recent_activity": recent_activity,
                        "performance": performance
                    },
                    "last_updated": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting system overview: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Overview error: {str(e)}")
        
        @self.app.get("/api/stats")
        async def get_enhanced_stats():
            """Get enhanced statistics for dashboard"""
            
            try:
                # Get hearing statistics
                cursor = self.db.connection.execute("""
                    SELECT 
                        COUNT(*) as total_hearings,
                        SUM(CASE WHEN source_api = 1 THEN 1 ELSE 0 END) as api_synced,
                        SUM(CASE WHEN source_website = 1 THEN 1 ELSE 0 END) as website_synced,
                        SUM(CASE WHEN streams IS NOT NULL AND streams != '{}' THEN 1 ELSE 0 END) as has_streams,
                        COUNT(DISTINCT committee_code) as active_committees
                    FROM hearings_unified
                    WHERE created_at >= datetime('now', '-30 days')
                """)
                
                hearing_stats = dict(cursor.fetchone())
                
                # Get review statistics
                cursor = self.db.connection.execute("""
                    SELECT 
                        COUNT(*) as total_assignments,
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                        AVG(CASE WHEN status = 'completed' AND actual_duration_minutes IS NOT NULL 
                               THEN actual_duration_minutes ELSE NULL END) as avg_review_time
                    FROM review_assignments
                    WHERE created_at >= datetime('now', '-30 days')
                """)
                
                review_stats = dict(cursor.fetchone())
                
                # Get alert statistics
                cursor = self.db.connection.execute("""
                    SELECT 
                        COUNT(*) as total_alerts,
                        SUM(CASE WHEN resolved = FALSE THEN 1 ELSE 0 END) as active_alerts,
                        SUM(CASE WHEN severity = 'critical' AND resolved = FALSE THEN 1 ELSE 0 END) as critical_alerts
                    FROM system_alerts
                    WHERE created_at >= datetime('now', '-7 days')
                """)
                
                alert_stats = dict(cursor.fetchone())
                
                return {
                    "hearings": hearing_stats,
                    "reviews": review_stats,
                    "alerts": alert_stats,
                    "sync_efficiency": {
                        "discovery_rate": (hearing_stats['api_synced'] + hearing_stats['website_synced']) / max(hearing_stats['total_hearings'], 1) * 100,
                        "capture_rate": hearing_stats['has_streams'] / max(hearing_stats['total_hearings'], 1) * 100,
                        "review_completion": review_stats['completed'] / max(review_stats['total_assignments'], 1) * 100
                    },
                    "last_updated": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting enhanced stats: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")
        
        # Setup admin bootstrap endpoints
        self._setup_admin_routes()
        
        # Setup component API routes
        setup_hearing_management_routes(self.app)
        setup_system_monitoring_routes(self.app)
        setup_status_management_routes(self.app)
        setup_search_routes(self.app)
        setup_transcript_routes(self.app, self.db)
        setup_discovery_management_routes(self.app)
        
        # Add health check routes
        if health_router:
            self.app.include_router(health_router, tags=["health"])
        else:
            # Basic health endpoint if full health module fails to import
            @self.app.get("/health")
            async def basic_health():
                return {"status": "ok", "message": "Basic health check"}
        
        # Add metrics endpoint for production
        if PRODUCTION_MODE:
            try:
                from prometheus_client import generate_latest
                @self.app.get("/metrics")
                async def metrics():
                    """Prometheus metrics endpoint"""
                    return Response(
                        content=generate_latest(),
                        media_type="text/plain"
                    )
                    
                # Start metrics server
                if start_metrics_server:
                    start_metrics_server(9090)
            except ImportError:
                logger.warning("Prometheus client not available, metrics endpoint disabled")
    
    def _setup_admin_routes(self):
        """Setup admin bootstrap endpoints"""
        
        # Default committees for bootstrap
        DEFAULT_COMMITTEES = [
            {
                'committee_code': 'SCOM',
                'committee_name': 'Senate Committee on Commerce, Science, and Transportation',
                'chamber': 'Senate',
                'total_members': 28,
                'majority_party': 'Democrat',
                'minority_party': 'Republican',
                'metadata': {
                    'description': 'Committee with jurisdiction over commerce, science, and transportation',
                    'website': 'https://www.commerce.senate.gov',
                    'isvp_compatible': True
                }
            },
            {
                'committee_code': 'SSCI',
                'committee_name': 'Senate Select Committee on Intelligence',
                'chamber': 'Senate',
                'total_members': 21,
                'majority_party': 'Democrat',
                'minority_party': 'Republican',
                'metadata': {
                    'description': 'Select committee overseeing intelligence community',
                    'website': 'https://www.intelligence.senate.gov',
                    'isvp_compatible': True
                }
            },
            {
                'committee_code': 'SSJU',
                'committee_name': 'Senate Committee on the Judiciary',
                'chamber': 'Senate',
                'total_members': 22,
                'majority_party': 'Democrat',
                'minority_party': 'Republican',
                'metadata': {
                    'description': 'Committee with jurisdiction over federal judiciary',
                    'website': 'https://www.judiciary.senate.gov',
                    'isvp_compatible': True
                }
            }
        ]
        
        @self.app.get("/admin/status")
        async def admin_status():
            """Check system status for admin purposes"""
            try:
                # Get database connection
                db = get_enhanced_db()
                
                # Check if hearings_unified table exists
                cursor = db.connection.execute("""
                    SELECT name FROM sqlite_master WHERE type='table' AND name='hearings_unified'
                """)
                table_exists = cursor.fetchone() is not None
                
                if not table_exists:
                    return {
                        "status": "needs_initialization",
                        "committees": 0,
                        "hearings": 0,
                        "bootstrap_needed": True,
                        "tables_exist": False,
                        "message": "hearings_unified table does not exist"
                    }
                
                # Check committees (from hearings_unified table)
                cursor = db.connection.execute("SELECT COUNT(DISTINCT committee_code) FROM hearings_unified")
                committee_count = cursor.fetchone()[0]
                
                # Check hearings
                cursor = db.connection.execute("SELECT COUNT(*) FROM hearings_unified")
                hearing_count = cursor.fetchone()[0]
                
                return {
                    "status": "healthy",
                    "committees": committee_count,
                    "hearings": hearing_count,
                    "bootstrap_needed": committee_count == 0,
                    "tables_exist": True
                }
                
            except Exception as e:
                logger.error(f"Admin status error: {e}")
                return {"error": str(e), "details": "Check if database is properly initialized"}
        
        @self.app.post("/admin/bootstrap")
        async def bootstrap_system():
            """Bootstrap the system with default committees by adding sample hearings"""
            try:
                # Get database connection
                db = get_enhanced_db()
                
                # Force creation of the schema if it doesn't exist
                db._create_schema()
                
                # Add sample hearings to create committees in the hearings_unified table
                committees_added = 0
                errors = []
                
                for committee in DEFAULT_COMMITTEES:
                    try:
                        # Create a sample hearing for each committee to bootstrap the system
                        hearing_id = f"{committee['committee_code']}-BOOTSTRAP-{datetime.now().strftime('%Y%m%d')}"
                        
                        db.connection.execute("""
                            INSERT OR REPLACE INTO hearings_unified 
                            (committee_code, hearing_title, hearing_date, hearing_type, 
                             sync_confidence, streams, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            committee['committee_code'],
                            f"Bootstrap Entry for {committee['committee_name']}",
                            datetime.now().strftime('%Y-%m-%d'),
                            'Setup',
                            1.0,
                            '{}',
                            datetime.now().isoformat(),
                            datetime.now().isoformat()
                        ))
                        committees_added += 1
                        logger.info(f"Added bootstrap entry for {committee['committee_code']}")
                        
                    except Exception as e:
                        error_msg = f"Error adding committee {committee['committee_code']}: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
                # Commit changes
                db.connection.commit()
                
                # Get final count
                cursor = db.connection.execute("SELECT COUNT(DISTINCT committee_code) FROM hearings_unified")
                total_committees = cursor.fetchone()[0]
                
                cursor = db.connection.execute("SELECT COUNT(*) FROM hearings_unified")
                total_hearings = cursor.fetchone()[0]
                
                return {
                    "success": True,
                    "committees_added": committees_added,
                    "total_committees": total_committees,
                    "total_hearings": total_hearings,
                    "errors": errors,
                    "message": f"Bootstrap completed: {committees_added} committees added, {total_committees} total committees, {total_hearings} total hearings"
                }
                
            except Exception as e:
                logger.error(f"Bootstrap error: {e}")
                raise HTTPException(status_code=500, detail=f"Bootstrap failed: {str(e)}")
    
    def _setup_static_files(self):
        """Setup static file serving for React app"""
        
        # Check if React build exists
        dashboard_build = Path("dashboard/build")
        
        # Debug logging to check directory structure
        logger.info(f"Current working directory: {Path.cwd()}")
        logger.info(f"Looking for React build at: {dashboard_build.absolute()}")
        logger.info(f"Dashboard directory exists: {Path('dashboard').exists()}")
        if Path('dashboard').exists():
            dashboard_contents = list(Path('dashboard').iterdir())
            logger.info(f"Dashboard directory contents: {dashboard_contents}")
        
        if dashboard_build.exists():
            logger.info(f"React build found at: {dashboard_build.absolute()}")
            # Serve React app static files
            self.app.mount("/static", StaticFiles(directory="dashboard/build/static"), name="static")
            
            # Catch-all route for React Router (including root)
            @self.app.get("/{path:path}")
            async def serve_react_app(path: str):
                """Serve React app for client-side routing"""
                # Handle root path
                if path == "":
                    return FileResponse(dashboard_build / "index.html")
                    
                file_path = dashboard_build / path
                
                if file_path.exists() and file_path.is_file():
                    return FileResponse(file_path)
                else:
                    # Return index.html for client-side routing
                    return FileResponse(dashboard_build / "index.html")
        else:
            logger.warning("React build not found. Run 'npm run build' in dashboard directory.")
            
            # Fallback API-only mode
            @self.app.get("/")
            async def api_only_root():
                """API-only root endpoint when React build not available"""
                return {
                    "name": "Senate Hearing Audio Capture API",
                    "version": "7B.1.0",
                    "status": "API-only mode",
                    "message": "Frontend not available in this deployment",
                    "health_check": "/health",
                    "api_info": "/api"
                }
    
    def _initialize_demo_data(self):
        """Initialize demo data for development"""
        
        try:
            # Create a demo user session
            session_id = self.db.create_user_session(user_id="demo_user", role="admin")
            logger.info(f"Demo user session created: {session_id}")
            
            # Create some demo alerts for testing (disabled to avoid confusion)
            # self.db.create_alert(
            #     alert_type="system_error",
            #     severity="medium", 
            #     title="Demo Alert: API Rate Limit Approaching",
            #     description="Congress.gov API usage at 85% of daily limit",
            #     component="api",
            #     metadata={"current_usage": 850, "daily_limit": 1000},
            #     auto_resolvable=True
            # )
            
            # Record some demo quality metrics
            self.db.record_quality_metric(
                metric_type="accuracy_score",
                metric_value=87.3,
                baseline_value=85.0
            )
            
            self.db.record_quality_metric(
                metric_type="review_speed",
                metric_value=15.2,
                baseline_value=18.5
            )
            
            logger.info("Demo data initialized successfully")
            
        except Exception as e:
            logger.warning(f"Could not initialize demo data: {str(e)}")
    
    def _get_hearing_queue_summary(self) -> Dict[str, Any]:
        """Get hearing queue summary"""
        
        cursor = self.db.connection.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN ra.status = 'pending' THEN 1 ELSE 0 END) as pending_review,
                SUM(CASE WHEN ra.status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN h.streams IS NOT NULL AND h.streams != '{}' THEN 1 ELSE 0 END) as ready_for_capture
            FROM hearings_unified h
            LEFT JOIN review_assignments ra ON CAST(h.id AS TEXT) = ra.hearing_id
            WHERE h.created_at >= datetime('now', '-14 days')
        """)
        
        return dict(cursor.fetchone())
    
    def _get_health_summary(self) -> Dict[str, Any]:
        """Get system health summary"""
        
        alerts = self.db.get_active_alerts()
        critical_count = sum(1 for a in alerts if a['severity'] == 'critical')
        high_count = sum(1 for a in alerts if a['severity'] == 'high')
        
        if critical_count > 0:
            status = "critical"
        elif high_count > 0:
            status = "degraded"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "active_alerts": len(alerts),
            "critical_alerts": critical_count,
            "high_alerts": high_count
        }
    
    def _get_recent_activity(self) -> Dict[str, Any]:
        """Get recent system activity"""
        
        # Get recent hearings discovered
        cursor = self.db.connection.execute("""
            SELECT committee_code, hearing_title, created_at
            FROM hearings_unified
            WHERE created_at >= datetime('now', '-24 hours')
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        recent_hearings = [dict(row) for row in cursor.fetchall()]
        
        # Get recent review completions
        cursor = self.db.connection.execute("""
            SELECT ra.completed_at, h.hearing_title, h.committee_code
            FROM review_assignments ra
            JOIN hearings_unified h ON CAST(h.id AS TEXT) = ra.hearing_id
            WHERE ra.completed_at >= datetime('now', '-24 hours')
            ORDER BY ra.completed_at DESC
            LIMIT 5
        """)
        
        recent_reviews = [dict(row) for row in cursor.fetchall()]
        
        return {
            "new_hearings": recent_hearings,
            "completed_reviews": recent_reviews
        }
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        
        # Get average quality metrics from last 7 days
        cursor = self.db.connection.execute("""
            SELECT metric_type, AVG(metric_value) as avg_value
            FROM quality_metrics
            WHERE recorded_at >= datetime('now', '-7 days')
            GROUP BY metric_type
        """)
        
        quality_metrics = {row['metric_type']: row['avg_value'] for row in cursor.fetchall()}
        
        return {
            "average_accuracy": quality_metrics.get('accuracy_score', 0),
            "average_review_speed": quality_metrics.get('review_speed', 0),
            "quality_trend": "improving"  # TODO: Calculate actual trend
        }

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create the enhanced UI app
    enhanced_app = EnhancedUIApp()
    
    logger.info("Phase 7B Enhanced UI application created successfully")
    
    return enhanced_app.app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )