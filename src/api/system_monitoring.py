"""
System Monitoring API for Phase 7B Enhanced UI.
Provides real-time system health, sync status, pipeline monitoring,
and error management endpoints.
"""

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json
import asyncio
from pydantic import BaseModel

from .database_enhanced import get_enhanced_db
from ..sync.sync_orchestrator import SyncOrchestrator

logger = logging.getLogger(__name__)

# Pydantic models
class AlertResolution(BaseModel):
    alert_id: str
    resolution_notes: Optional[str] = None

class SystemHealthFilter(BaseModel):
    component: Optional[str] = None
    severity: Optional[str] = None
    include_resolved: bool = False

class PipelineStatusRequest(BaseModel):
    hearing_ids: Optional[List[str]] = None
    stages: Optional[List[str]] = None  # 'discovery', 'capture', 'transcription', 'review'

class SystemMonitoringAPI:
    """API class for system monitoring operations"""
    
    def __init__(self):
        self.db = get_enhanced_db()
        self.sync_orchestrator = SyncOrchestrator()
        self.active_connections: List[WebSocket] = []
    
    async def connect_websocket(self, websocket: WebSocket):
        """Connect WebSocket for real-time updates"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect_websocket(self, websocket: WebSocket):
        """Disconnect WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast_update(self, message: Dict[str, Any]):
        """Broadcast update to all connected WebSockets"""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect_websocket(connection)
    
    def get_system_health(self, include_details: bool = True) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        
        try:
            # Get sync health from database
            sync_health = self.db.get_sync_health()
            
            # Get active alerts
            alerts = self.db.get_active_alerts()
            critical_alerts = [a for a in alerts if a['severity'] == 'critical']
            high_alerts = [a for a in alerts if a['severity'] == 'high']
            
            # Determine overall system status
            overall_status = sync_health['overall_status']
            if critical_alerts:
                overall_status = 'critical'
            elif high_alerts:
                overall_status = 'degraded'
            elif sync_health['overall_status'] == 'error':
                overall_status = 'degraded'
            
            # Get pipeline metrics
            pipeline_health = self._get_pipeline_health()
            
            # Calculate uptime and performance metrics
            performance_metrics = self._calculate_performance_metrics()
            
            health_summary = {
                'overall_status': overall_status,
                'last_updated': datetime.now().isoformat(),
                'sync_health': sync_health,
                'pipeline_health': pipeline_health,
                'alerts_summary': {
                    'total': len(alerts),
                    'critical': len(critical_alerts),
                    'high': len(high_alerts),
                    'medium': len([a for a in alerts if a['severity'] == 'medium']),
                    'low': len([a for a in alerts if a['severity'] == 'low'])
                },
                'performance_metrics': performance_metrics
            }
            
            if include_details:
                health_summary['component_details'] = self._get_component_details()
                health_summary['recent_alerts'] = alerts[:10]  # Last 10 alerts
            
            return health_summary
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Health check error: {str(e)}")
    
    def get_sync_status(self, component: Optional[str] = None,
                       committee_code: Optional[str] = None) -> Dict[str, Any]:
        """Get real-time sync status"""
        
        try:
            conditions = []
            params = []
            
            if component:
                conditions.append("component = ?")
                params.append(component)
            
            if committee_code:
                conditions.append("committee_code = ?")
                params.append(committee_code)
            
            where_clause = " AND " + " AND ".join(conditions) if conditions else ""
            
            cursor = self.db.connection.execute(f"""
                SELECT component, committee_code, status, last_success, 
                       last_attempt, error_count, error_message, 
                       performance_metrics, updated_at
                FROM sync_status
                WHERE updated_at >= datetime('now', '-6 hours') {where_clause}
                ORDER BY updated_at DESC
            """, params)
            
            sync_statuses = []
            component_summary = {}
            
            for row in cursor.fetchall():
                status_data = dict(row)
                
                # Parse performance metrics
                if status_data['performance_metrics']:
                    status_data['performance_metrics'] = json.loads(status_data['performance_metrics'])
                
                # Calculate status age
                last_update = datetime.fromisoformat(status_data['updated_at'])
                status_data['age_minutes'] = (datetime.now() - last_update).total_seconds() / 60
                
                # Determine health indicator
                if status_data['status'] == 'healthy' and status_data['age_minutes'] < 60:
                    status_data['health_indicator'] = 'healthy'
                elif status_data['status'] == 'healthy' and status_data['age_minutes'] < 120:
                    status_data['health_indicator'] = 'stale'
                elif status_data['status'] == 'warning':
                    status_data['health_indicator'] = 'warning'
                else:
                    status_data['health_indicator'] = 'error'
                
                sync_statuses.append(status_data)
                
                # Build component summary
                comp = status_data['component']
                if comp not in component_summary:
                    component_summary[comp] = {
                        'status': status_data['status'],
                        'committees': {},
                        'total_errors': 0,
                        'last_success': status_data['last_success']
                    }
                
                if status_data['committee_code']:
                    component_summary[comp]['committees'][status_data['committee_code']] = {
                        'status': status_data['status'],
                        'health_indicator': status_data['health_indicator'],
                        'error_count': status_data['error_count'],
                        'last_success': status_data['last_success']
                    }
                
                component_summary[comp]['total_errors'] += status_data['error_count']
            
            return {
                'sync_statuses': sync_statuses,
                'component_summary': component_summary,
                'last_updated': datetime.now().isoformat(),
                'filters_applied': {
                    'component': component,
                    'committee_code': committee_code
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting sync status: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Sync status error: {str(e)}")
    
    def get_pipeline_status(self, hearing_ids: Optional[List[str]] = None,
                           stages: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get pipeline status for hearings"""
        
        try:
            # Default stages if not specified
            if not stages:
                stages = ['discovery', 'capture', 'transcription', 'review']
            
            # Get hearing pipeline status
            conditions = []
            params = []
            
            if hearing_ids:
                placeholders = ','.join(['?' for _ in hearing_ids])
                conditions.append(f"h.id IN ({placeholders})")
                params.extend(hearing_ids)
            else:
                # Get recent hearings by default
                conditions.append("h.created_at >= datetime('now', '-7 days')")
            
            where_clause = " AND " + " AND ".join(conditions) if conditions else ""
            
            cursor = self.db.connection.execute(f"""
                SELECT h.id, h.hearing_title, h.committee_code, h.hearing_date,
                       h.source_api, h.source_website, h.streams,
                       ra.status as review_status, ra.priority as review_priority,
                       ra.started_at as review_started, ra.completed_at as review_completed,
                       h.created_at, h.updated_at
                FROM hearings_unified h
                LEFT JOIN review_assignments ra ON CAST(h.id AS TEXT) = ra.hearing_id
                WHERE 1=1 {where_clause}
                ORDER BY h.hearing_date DESC, h.created_at DESC
                LIMIT 100
            """, params)
            
            pipeline_data = []
            stage_summary = {stage: {'total': 0, 'completed': 0, 'in_progress': 0, 'failed': 0} 
                           for stage in stages}
            
            for row in cursor.fetchall():
                hearing_data = dict(row)
                
                # Determine stage status for each hearing
                stage_status = {}
                
                # Discovery stage
                if 'discovery' in stages:
                    if hearing_data['source_api'] or hearing_data['source_website']:
                        stage_status['discovery'] = 'completed'
                        stage_summary['discovery']['completed'] += 1
                    else:
                        stage_status['discovery'] = 'failed'
                        stage_summary['discovery']['failed'] += 1
                    stage_summary['discovery']['total'] += 1
                
                # Capture stage
                if 'capture' in stages:
                    has_streams = hearing_data['streams'] and hearing_data['streams'] != '{}'
                    if has_streams:
                        stage_status['capture'] = 'completed'
                        stage_summary['capture']['completed'] += 1
                    else:
                        hearing_date = datetime.fromisoformat(hearing_data['hearing_date'])
                        if hearing_date > datetime.now():
                            stage_status['capture'] = 'pending'
                        else:
                            stage_status['capture'] = 'failed'
                            stage_summary['capture']['failed'] += 1
                    stage_summary['capture']['total'] += 1
                
                # Transcription stage  
                if 'transcription' in stages:
                    # TODO: Integrate with actual transcription status
                    # For now, simulate based on review assignment
                    if hearing_data['review_status']:
                        stage_status['transcription'] = 'completed'
                        stage_summary['transcription']['completed'] += 1
                    elif has_streams:
                        stage_status['transcription'] = 'in_progress'
                        stage_summary['transcription']['in_progress'] += 1
                    else:
                        stage_status['transcription'] = 'pending'
                    stage_summary['transcription']['total'] += 1
                
                # Review stage
                if 'review' in stages:
                    if hearing_data['review_status'] == 'completed':
                        stage_status['review'] = 'completed'
                        stage_summary['review']['completed'] += 1
                    elif hearing_data['review_status'] == 'in_progress':
                        stage_status['review'] = 'in_progress'
                        stage_summary['review']['in_progress'] += 1
                    elif hearing_data['review_status'] == 'pending':
                        stage_status['review'] = 'pending'
                    else:
                        stage_status['review'] = 'not_started'
                    stage_summary['review']['total'] += 1
                
                # Calculate overall progress
                completed_stages = sum(1 for status in stage_status.values() if status == 'completed')
                total_stages = len(stage_status)
                progress_percentage = (completed_stages / total_stages * 100) if total_stages > 0 else 0
                
                hearing_data['stage_status'] = stage_status
                hearing_data['progress_percentage'] = progress_percentage
                hearing_data['current_stage'] = self._get_current_stage(stage_status)
                
                pipeline_data.append(hearing_data)
            
            # Calculate overall pipeline health
            overall_efficiency = self._calculate_pipeline_efficiency(stage_summary)
            
            return {
                'pipeline_data': pipeline_data,
                'stage_summary': stage_summary,
                'overall_efficiency': overall_efficiency,
                'last_updated': datetime.now().isoformat(),
                'stages_tracked': stages
            }
            
        except Exception as e:
            logger.error(f"Error getting pipeline status: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Pipeline status error: {str(e)}")
    
    def get_active_alerts(self, severity: Optional[str] = None,
                         component: Optional[str] = None,
                         limit: int = 100) -> Dict[str, Any]:
        """Get active system alerts"""
        
        try:
            alerts = self.db.get_active_alerts(severity=severity, component=component)
            
            # Limit results
            alerts = alerts[:limit]
            
            # Add additional context to alerts
            for alert in alerts:
                alert['age_hours'] = (datetime.now() - datetime.fromisoformat(alert['created_at'])).total_seconds() / 3600
                alert['urgency_score'] = self._calculate_alert_urgency(alert)
            
            # Sort by urgency
            alerts.sort(key=lambda x: x['urgency_score'], reverse=True)
            
            # Get alert statistics
            alert_stats = self._get_alert_statistics()
            
            return {
                'alerts': alerts,
                'total_active': len(alerts),
                'statistics': alert_stats,
                'filters_applied': {
                    'severity': severity,
                    'component': component
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Alerts error: {str(e)}")
    
    def resolve_alert(self, alert_id: str, user_id: str, 
                     resolution_notes: str = None) -> Dict[str, Any]:
        """Resolve a system alert"""
        
        try:
            # Get alert details before resolving
            cursor = self.db.connection.execute("""
                SELECT alert_type, severity, title, component, auto_resolvable
                FROM system_alerts
                WHERE alert_id = ? AND resolved = FALSE
            """, (alert_id,))
            
            alert = cursor.fetchone()
            if not alert:
                raise HTTPException(status_code=404, detail="Alert not found or already resolved")
            
            # Resolve the alert
            success = self.db.resolve_alert(alert_id, resolved_by=user_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Alert not found or already resolved")
            
            # Record resolution in preferences if notes provided
            if resolution_notes:
                self.db.set_user_preference(
                    user_id=user_id,
                    key=f"alert_resolution_{alert_id}",
                    value=resolution_notes
                )
            
            # Log resolution
            logger.info(f"Alert {alert_id} resolved by {user_id}: {alert['title']}")
            
            # Broadcast update to connected clients
            asyncio.create_task(self.broadcast_update({
                'type': 'alert_resolved',
                'alert_id': alert_id,
                'resolved_by': user_id,
                'timestamp': datetime.now().isoformat()
            }))
            
            return {
                'alert_id': alert_id,
                'resolved': True,
                'resolved_by': user_id,
                'resolved_at': datetime.now().isoformat(),
                'resolution_notes': resolution_notes,
                'alert_details': dict(alert)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Resolution error: {str(e)}")
    
    def _get_pipeline_health(self) -> Dict[str, Any]:
        """Get pipeline health metrics"""
        
        try:
            # Get recent hearing processing metrics
            cursor = self.db.connection.execute("""
                SELECT 
                    COUNT(*) as total_hearings,
                    SUM(CASE WHEN (source_api = 1 OR source_website = 1) THEN 1 ELSE 0 END) as discovered,
                    SUM(CASE WHEN streams IS NOT NULL AND streams != '{}' THEN 1 ELSE 0 END) as captured,
                    COUNT(ra.hearing_id) as in_review,
                    SUM(CASE WHEN ra.status = 'completed' THEN 1 ELSE 0 END) as completed
                FROM hearings_unified h
                LEFT JOIN review_assignments ra ON CAST(h.id AS TEXT) = ra.hearing_id
                WHERE h.created_at >= datetime('now', '-7 days')
            """)
            
            metrics = dict(cursor.fetchone())
            
            # Calculate success rates
            total = metrics['total_hearings']
            if total > 0:
                discovery_rate = (metrics['discovered'] / total) * 100
                capture_rate = (metrics['captured'] / total) * 100
                review_rate = (metrics['completed'] / total) * 100 if metrics['completed'] else 0
            else:
                discovery_rate = capture_rate = review_rate = 0
            
            return {
                'discovery_rate': discovery_rate,
                'capture_rate': capture_rate,
                'review_completion_rate': review_rate,
                'total_hearings': total,
                'processing_metrics': metrics,
                'health_status': 'healthy' if discovery_rate > 80 else 'degraded' if discovery_rate > 60 else 'poor'
            }
            
        except Exception as e:
            logger.error(f"Error getting pipeline health: {str(e)}")
            return {'health_status': 'unknown', 'error': str(e)}
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate system performance metrics"""
        
        try:
            # Get quality metrics from last 24 hours
            cursor = self.db.connection.execute("""
                SELECT metric_type, AVG(metric_value) as avg_value, COUNT(*) as count
                FROM quality_metrics
                WHERE recorded_at >= datetime('now', '-24 hours')
                GROUP BY metric_type
            """)
            
            quality_metrics = {row['metric_type']: row['avg_value'] for row in cursor.fetchall()}
            
            # Calculate sync performance
            cursor = self.db.connection.execute("""
                SELECT component, 
                       COUNT(*) as attempts,
                       SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as successes
                FROM sync_status
                WHERE updated_at >= datetime('now', '-24 hours')
                GROUP BY component
            """)
            
            sync_performance = {}
            for row in cursor.fetchall():
                component = row['component']
                success_rate = (row['successes'] / row['attempts'] * 100) if row['attempts'] > 0 else 0
                sync_performance[component] = {
                    'success_rate': success_rate,
                    'attempts': row['attempts']
                }
            
            return {
                'quality_metrics': quality_metrics,
                'sync_performance': sync_performance,
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {'error': str(e)}
    
    def _get_component_details(self) -> Dict[str, Any]:
        """Get detailed component status information"""
        
        components = {
            'congress_api': self._get_api_component_details(),
            'committee_scraper': self._get_scraper_component_details(),
            'transcription': self._get_transcription_component_details(),
            'review_system': self._get_review_component_details(),
            'database': self._get_database_component_details()
        }
        
        return components
    
    def _get_api_component_details(self) -> Dict[str, Any]:
        """Get Congress.gov API component details"""
        # TODO: Integrate with actual API monitoring
        return {
            'status': 'healthy',
            'last_request': datetime.now().isoformat(),
            'rate_limit_remaining': 85,
            'response_time_ms': 245
        }
    
    def _get_scraper_component_details(self) -> Dict[str, Any]:
        """Get committee scraper component details"""
        # TODO: Integrate with actual scraper monitoring
        return {
            'status': 'healthy',
            'active_scrapers': 5,
            'last_scrape': datetime.now().isoformat(),
            'success_rate': 92.3
        }
    
    def _get_transcription_component_details(self) -> Dict[str, Any]:
        """Get transcription component details"""
        # TODO: Integrate with actual transcription monitoring
        return {
            'status': 'healthy',
            'queue_length': 3,
            'average_processing_time': 45,
            'accuracy_rate': 87.6
        }
    
    def _get_review_component_details(self) -> Dict[str, Any]:
        """Get review system component details"""
        
        cursor = self.db.connection.execute("""
            SELECT status, COUNT(*) as count
            FROM review_assignments
            WHERE created_at >= datetime('now', '-24 hours')
            GROUP BY status
        """)
        
        review_stats = {row['status']: row['count'] for row in cursor.fetchall()}
        
        return {
            'status': 'healthy',
            'review_queue': review_stats,
            'active_reviewers': 2,  # TODO: Track actual active reviewers
            'average_review_time': 35
        }
    
    def _get_database_component_details(self) -> Dict[str, Any]:
        """Get database component details"""
        
        try:
            # Check database connectivity and performance
            start_time = datetime.now()
            cursor = self.db.connection.execute("SELECT COUNT(*) FROM hearings_unified")
            total_hearings = cursor.fetchone()[0]
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                'status': 'healthy',
                'total_hearings': total_hearings,
                'response_time_ms': response_time,
                'connection_pool': 'healthy'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_current_stage(self, stage_status: Dict[str, str]) -> str:
        """Determine current stage based on stage status"""
        
        stage_order = ['discovery', 'capture', 'transcription', 'review']
        
        for stage in stage_order:
            if stage in stage_status:
                if stage_status[stage] in ['pending', 'in_progress']:
                    return stage
                elif stage_status[stage] in ['failed', 'error']:
                    return f"{stage}_failed"
        
        # If all stages completed
        return 'completed'
    
    def _calculate_pipeline_efficiency(self, stage_summary: Dict) -> Dict[str, float]:
        """Calculate overall pipeline efficiency metrics"""
        
        efficiency = {}
        
        for stage, stats in stage_summary.items():
            if stats['total'] > 0:
                completion_rate = (stats['completed'] / stats['total']) * 100
                success_rate = ((stats['completed'] + stats['in_progress']) / stats['total']) * 100
                
                efficiency[stage] = {
                    'completion_rate': completion_rate,
                    'success_rate': success_rate,
                    'failure_rate': (stats['failed'] / stats['total']) * 100
                }
            else:
                efficiency[stage] = {
                    'completion_rate': 0,
                    'success_rate': 0,
                    'failure_rate': 0
                }
        
        # Calculate overall efficiency
        if efficiency:
            overall_completion = sum(e['completion_rate'] for e in efficiency.values()) / len(efficiency)
            overall_success = sum(e['success_rate'] for e in efficiency.values()) / len(efficiency)
            
            efficiency['overall'] = {
                'completion_rate': overall_completion,
                'success_rate': overall_success,
                'efficiency_score': (overall_completion + overall_success) / 2
            }
        
        return efficiency
    
    def _calculate_alert_urgency(self, alert: Dict) -> float:
        """Calculate alert urgency score"""
        
        urgency = 0
        
        # Severity weight
        severity_weights = {'critical': 100, 'high': 75, 'medium': 50, 'low': 25}
        urgency += severity_weights.get(alert['severity'], 0)
        
        # Age penalty (older alerts are less urgent)
        age_hours = alert['age_hours']
        if age_hours < 1:
            urgency += 50  # Very recent
        elif age_hours < 6:
            urgency += 25  # Recent
        elif age_hours > 24:
            urgency -= 25  # Old
        
        # Auto-resolvable bonus
        if alert['auto_resolvable']:
            urgency += 20
        
        # Component impact
        critical_components = ['database', 'api']
        if alert['component'] in critical_components:
            urgency += 30
        
        return max(0, urgency)
    
    def _get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics for dashboard"""
        
        cursor = self.db.connection.execute("""
            SELECT 
                COUNT(*) as total_alerts,
                SUM(CASE WHEN resolved = FALSE THEN 1 ELSE 0 END) as active_alerts,
                SUM(CASE WHEN resolved = TRUE AND resolved_at >= datetime('now', '-24 hours') THEN 1 ELSE 0 END) as resolved_today,
                AVG(CASE WHEN resolved = TRUE THEN julianday(resolved_at) - julianday(created_at) ELSE NULL END) * 24 as avg_resolution_hours
            FROM system_alerts
            WHERE created_at >= datetime('now', '-7 days')
        """)
        
        stats = dict(cursor.fetchone())
        
        # Get alert trends
        cursor = self.db.connection.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM system_alerts
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        
        daily_trend = [dict(row) for row in cursor.fetchall()]
        
        return {
            'total_alerts': stats['total_alerts'],
            'active_alerts': stats['active_alerts'],
            'resolved_today': stats['resolved_today'],
            'avg_resolution_hours': stats['avg_resolution_hours'] or 0,
            'daily_trend': daily_trend
        }

# FastAPI route integration
def setup_system_monitoring_routes(app: FastAPI):
    """Setup system monitoring routes"""
    
    api = SystemMonitoringAPI()
    
    @app.get("/api/system/health")
    async def get_system_health(
        include_details: bool = Query(True, description="Include detailed component information")
    ):
        """Get comprehensive system health status"""
        return api.get_system_health(include_details=include_details)
    
    @app.get("/api/system/sync-status")
    async def get_sync_status(
        component: Optional[str] = Query(None, description="Filter by component"),
        committee_code: Optional[str] = Query(None, description="Filter by committee")
    ):
        """Get real-time sync status"""
        return api.get_sync_status(component=component, committee_code=committee_code)
    
    @app.get("/api/system/pipeline-status")
    async def get_pipeline_status(
        hearing_ids: Optional[str] = Query(None, description="Comma-separated hearing IDs"),
        stages: Optional[str] = Query(None, description="Comma-separated stages to track")
    ):
        """Get pipeline status for hearings"""
        
        hearing_id_list = hearing_ids.split(',') if hearing_ids else None
        stages_list = stages.split(',') if stages else None
        
        return api.get_pipeline_status(hearing_ids=hearing_id_list, stages=stages_list)
    
    @app.get("/api/system/alerts")
    async def get_active_alerts(
        severity: Optional[str] = Query(None, description="Filter by severity"),
        component: Optional[str] = Query(None, description="Filter by component"),
        limit: int = Query(100, ge=1, le=500, description="Maximum alerts to return")
    ):
        """Get active system alerts"""
        return api.get_active_alerts(severity=severity, component=component, limit=limit)
    
    @app.post("/api/system/alerts/{alert_id}/resolve")
    async def resolve_alert(
        alert_id: str,
        resolution: AlertResolution,
        user_id: str = Query(..., description="User ID for audit trail")
    ):
        """Resolve a system alert"""
        return api.resolve_alert(
            alert_id=alert_id,
            user_id=user_id,
            resolution_notes=resolution.resolution_notes
        )
    
    @app.websocket("/ws/system-updates")
    async def websocket_system_updates(websocket: WebSocket):
        """WebSocket endpoint for real-time system updates"""
        await api.connect_websocket(websocket)
        try:
            while True:
                # Keep connection alive and handle incoming messages
                await websocket.receive_text()
        except WebSocketDisconnect:
            api.disconnect_websocket(websocket)
    
    # Health check endpoint for load balancers
    @app.get("/health")
    async def health_check():
        """Simple health check endpoint"""
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}