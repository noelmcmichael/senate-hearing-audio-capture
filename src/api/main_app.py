"""
Main FastAPI application for Phase 7B Enhanced UI.
Integrates all API endpoints and serves the React dashboard.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any

# Import API modules
from .hearing_management import setup_hearing_management_routes
from .system_monitoring import setup_system_monitoring_routes
from .status_management import setup_status_management_routes
from .search_management import setup_search_routes
from .transcript_management import setup_transcript_routes
from .database_enhanced import get_enhanced_db

# Import existing dashboard data API
from .dashboard_data import DashboardDataAPI

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
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        # Health check endpoint
        @self.app.get("/")
        async def root():
            """Root endpoint - serve React app"""
            return FileResponse("dashboard/build/index.html")
        
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
        
        # Setup component API routes
        setup_hearing_management_routes(self.app)
        setup_system_monitoring_routes(self.app)
        setup_status_management_routes(self.app)
        setup_search_routes(self.app)
        setup_transcript_routes(self.app, self.db)
    
    def _setup_static_files(self):
        """Setup static file serving for React app"""
        
        # Check if React build exists
        dashboard_build = Path("dashboard/build")
        if dashboard_build.exists():
            # Serve React app static files
            self.app.mount("/static", StaticFiles(directory="dashboard/build/static"), name="static")
            
            # Catch-all route for React Router
            @self.app.get("/{path:path}")
            async def serve_react_app(path: str):
                """Serve React app for client-side routing"""
                file_path = dashboard_build / path
                
                if file_path.exists() and file_path.is_file():
                    return FileResponse(file_path)
                else:
                    # Return index.html for client-side routing
                    return FileResponse(dashboard_build / "index.html")
        else:
            logger.warning("React build not found. Run 'npm run build' in dashboard directory.")
    
    def _initialize_demo_data(self):
        """Initialize demo data for development"""
        
        try:
            # Create a demo user session
            session_id = self.db.create_user_session(user_id="demo_user", role="admin")
            logger.info(f"Demo user session created: {session_id}")
            
            # Create some demo alerts for testing
            self.db.create_alert(
                alert_type="system_error",
                severity="medium",
                title="Demo Alert: API Rate Limit Approaching",
                description="Congress.gov API usage at 85% of daily limit",
                component="api",
                metadata={"current_usage": 850, "daily_limit": 1000},
                auto_resolvable=True
            )
            
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