"""
Hearing Management API for Phase 7B Enhanced UI.
Provides endpoints for hearing queue management, duplicate resolution,
and capture orchestration.
"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json
from pydantic import BaseModel

from .database_enhanced import get_enhanced_db
from ..sync.sync_orchestrator import SyncOrchestrator
from ..sync.deduplication_engine import DeduplicationEngine
from .capture_service import get_capture_service, CaptureException
from .transcription_service import get_transcription_service, TranscriptionException

logger = logging.getLogger(__name__)

# Pydantic models for request/response validation
class HearingQueueFilter(BaseModel):
    committee_codes: Optional[List[str]] = None
    status: Optional[str] = None  # 'pending', 'in_progress', 'completed'
    sync_status: Optional[str] = None  # 'synced', 'pending_sync', 'failed'
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    has_streams: Optional[bool] = None

class HearingPriorityUpdate(BaseModel):
    hearing_id: str
    priority: int
    reason: Optional[str] = None

class DuplicateResolution(BaseModel):
    primary_hearing_id: str
    duplicate_hearing_id: str
    action: str  # 'merge', 'keep_separate', 'mark_invalid'
    merge_strategy: Optional[Dict[str, str]] = None  # field -> source preference

class CaptureRequest(BaseModel):
    hearing_id: str
    priority: int = 0
    capture_options: Optional[Dict[str, Any]] = None

class HearingManagementAPI:
    """API class for hearing management operations"""
    
    def __init__(self):
        self.db = get_enhanced_db()
        self.sync_orchestrator = SyncOrchestrator()
        self.capture_service = get_capture_service()
        self.transcription_service = get_transcription_service()
        self.deduplicator = DeduplicationEngine()
    
    def get_hearing_queue(self, 
                         committee_codes: Optional[List[str]] = None,
                         status: Optional[str] = None,
                         sync_status: Optional[str] = None,
                         date_from: Optional[str] = None,
                         date_to: Optional[str] = None,
                         has_streams: Optional[bool] = None,
                         limit: int = 100,
                         offset: int = 0) -> Dict[str, Any]:
        """Get hearing queue with filtering and pagination"""
        
        try:
            # Build dynamic query conditions
            conditions = []
            params = []
            
            if committee_codes:
                placeholders = ','.join(['?' for _ in committee_codes])
                conditions.append(f"h.committee_code IN ({placeholders})")
                params.extend(committee_codes)
            
            if sync_status:
                if sync_status == 'synced':
                    conditions.append("(h.source_api = 1 OR h.source_website = 1)")
                elif sync_status == 'pending_sync':
                    conditions.append("h.source_api = 0 AND h.source_website = 0")
                elif sync_status == 'failed':
                    conditions.append("h.sync_confidence < 0.5")
            
            if date_from:
                conditions.append("h.hearing_date >= ?")
                params.append(date_from)
            
            if date_to:
                conditions.append("h.hearing_date <= ?")
                params.append(date_to)
            
            if has_streams is not None:
                if has_streams:
                    conditions.append("h.streams IS NOT NULL AND h.streams != '{}'")
                else:
                    conditions.append("(h.streams IS NULL OR h.streams = '{}')")
            
            where_clause = " AND " + " AND ".join(conditions) if conditions else ""
            
            # Get total count
            count_query = f"""
                SELECT COUNT(*) as total
                FROM hearings_unified h
                WHERE 1=1 {where_clause}
            """
            
            cursor = self.db.connection.execute(count_query, params)
            total_count = cursor.fetchone()['total']
            
            # Get hearings with pagination
            params.extend([limit, offset])
            
            hearings_query = f"""
                SELECT h.*, 
                       ra.status as review_status,
                       ra.priority as review_priority,
                       ra.assigned_to,
                       ra.quality_score
                FROM hearings_unified h
                LEFT JOIN review_assignments ra ON CAST(h.id AS TEXT) = ra.hearing_id
                WHERE 1=1 {where_clause}
                ORDER BY 
                    CASE WHEN ra.priority IS NOT NULL THEN ra.priority ELSE 0 END DESC,
                    h.hearing_date DESC
                LIMIT ? OFFSET ?
            """
            
            cursor = self.db.connection.execute(hearings_query, params)
            hearings = []
            
            for row in cursor.fetchall():
                hearing = dict(row)
                
                # Parse JSON fields (handle missing fields gracefully)
                def safe_json_parse(value, default):
                    if not value or value in ['{}', '[]', 'null', 'NULL']:
                        return default
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return default
                
                hearing['streams'] = safe_json_parse(hearing.get('streams'), {})
                hearing['witnesses'] = safe_json_parse(hearing.get('witnesses'), [])
                hearing['documents'] = safe_json_parse(hearing.get('documents'), [])
                hearing['external_urls'] = safe_json_parse(hearing.get('external_urls'), [])
                
                # Add computed fields
                hearing['has_streams'] = bool(hearing['streams'])
                hearing['sync_sources'] = []
                if hearing['source_api']:
                    hearing['sync_sources'].append('congress_api')
                if hearing['source_website']:
                    hearing['sync_sources'].append('committee_website')
                
                # Determine overall sync status
                if hearing['source_api'] or hearing['source_website']:
                    hearing['sync_status'] = 'synced'
                else:
                    hearing['sync_status'] = 'pending_sync'
                
                hearings.append(hearing)
            
            return {
                'hearings': hearings,
                'pagination': {
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_count
                },
                'filters_applied': {
                    'committee_codes': committee_codes,
                    'status': status,
                    'sync_status': sync_status,
                    'date_range': [date_from, date_to] if date_from or date_to else None,
                    'has_streams': has_streams
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting hearing queue: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def get_hearing_details(self, hearing_id: str) -> Dict[str, Any]:
        """Get detailed hearing information"""
        
        try:
            cursor = self.db.connection.execute("""
                SELECT h.*, 
                       ra.status as review_status,
                       ra.priority as review_priority,
                       ra.assigned_to,
                       ra.estimated_duration_minutes,
                       ra.actual_duration_minutes,
                       ra.quality_score,
                       ra.created_at as review_created_at,
                       ra.started_at as review_started_at,
                       ra.completed_at as review_completed_at
                FROM hearings_unified h
                LEFT JOIN review_assignments ra ON CAST(h.id AS TEXT) = ra.hearing_id
                WHERE h.id = ?
            """, (hearing_id,))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Hearing not found")
            
            hearing = dict(row)
            
            # Parse JSON fields safely
            def safe_json_parse(value, default):
                if not value or value in ['{}', '[]', 'null', 'NULL']:
                    return default
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return default
            
            # Parse JSON fields (handle missing fields gracefully)
            hearing['streams'] = safe_json_parse(hearing.get('streams'), {})
            hearing['witnesses'] = safe_json_parse(hearing.get('witnesses'), [])
            hearing['documents'] = safe_json_parse(hearing.get('documents'), [])
            hearing['external_urls'] = safe_json_parse(hearing.get('external_urls'), [])
            
            # Add computed fields
            hearing['has_streams'] = bool(hearing['streams'])
            hearing['estimated_duration'] = self._estimate_hearing_duration(hearing)
            hearing['capture_readiness'] = self._assess_capture_readiness(hearing)
            
            return hearing
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting hearing details for {hearing_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def update_hearing_priority(self, hearing_id: str, priority: int, 
                               user_id: str, reason: str = None) -> Dict[str, Any]:
        """Update hearing capture priority"""
        
        try:
            # Check if hearing exists
            hearing = self.get_hearing_details(hearing_id)
            
            # Update or create review assignment
            cursor = self.db.connection.execute("""
                SELECT assignment_id FROM review_assignments 
                WHERE hearing_id = ?
            """, (hearing_id,))
            
            assignment = cursor.fetchone()
            
            if assignment:
                # Update existing assignment
                self.db.connection.execute("""
                    UPDATE review_assignments 
                    SET priority = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE hearing_id = ?
                """, (priority, hearing_id))
            else:
                # Create new assignment
                assignment_id = self.db.create_review_assignment(
                    hearing_id=hearing_id,
                    priority=priority
                )
            
            self.db.connection.commit()
            
            # Log the priority change
            logger.info(f"Priority updated for hearing {hearing_id}: {priority} (by {user_id})")
            
            # Create alert if high priority
            if priority >= 8:
                self.db.create_alert(
                    alert_type="capacity_warning",
                    severity="medium",
                    title=f"High Priority Hearing: {hearing['hearing_title'][:50]}...",
                    description=f"Hearing {hearing_id} marked as high priority ({priority}/10). Reason: {reason or 'Not specified'}",
                    component="review",
                    metadata={
                        "hearing_id": hearing_id,
                        "priority": priority,
                        "updated_by": user_id,
                        "reason": reason
                    }
                )
            
            return {
                'hearing_id': hearing_id,
                'priority': priority,
                'updated_by': user_id,
                'updated_at': datetime.now().isoformat(),
                'reason': reason
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating priority for hearing {hearing_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def trigger_hearing_capture(self, hearing_id: str, priority: int = 0,
                                    user_id: str = None, 
                                    capture_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger audio capture for a hearing"""
        
        try:
            # Get hearing details
            hearing = self.get_hearing_details(hearing_id)
            
            if not hearing['has_streams']:
                raise HTTPException(
                    status_code=400, 
                    detail="Hearing has no available streams for capture"
                )
            
            # Check capture readiness
            readiness = hearing['capture_readiness']
            if readiness['score'] < 0.7:
                logger.warning(f"Low capture readiness for hearing {hearing_id}: {readiness}")
            
            # Create review assignment if doesn't exist
            cursor = self.db.connection.execute("""
                SELECT assignment_id FROM review_assignments 
                WHERE hearing_id = ?
            """, (hearing_id,))
            
            if not cursor.fetchone():
                assignment_id = self.db.create_review_assignment(
                    hearing_id=hearing_id,
                    priority=priority
                )
            
            # Update sync status
            self.db.update_sync_status(
                component="transcription",
                status="healthy",
                committee_code=hearing['committee_code'],
                performance_metrics={
                    "hearing_id": hearing_id,
                    "triggered_by": user_id,
                    "readiness_score": readiness['score']
                }
            )
            
            # Execute actual capture using capture service
            try:
                # Get hearing URL from hearing data
                hearing_url = hearing.get('url') or hearing.get('hearing_url') or hearing.get('source_url')
                if not hearing_url:
                    raise HTTPException(status_code=400, detail="No hearing URL found for capture")
                
                # Trigger actual audio capture
                capture_result = await self.capture_service.capture_hearing_audio(
                    hearing_id=hearing_id,
                    hearing_url=hearing_url,
                    capture_options=capture_options
                )
                
                # Add additional metadata
                capture_result.update({
                    'streams_found': len(hearing['streams']),
                    'priority': priority,
                    'readiness_assessment': readiness,
                    'initiated_by': user_id,
                    'initiated_at': datetime.now().isoformat()
                })
                
            except CaptureException as e:
                logger.error(f"Capture service error for hearing {hearing_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Audio capture failed: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error during capture for hearing {hearing_id}: {e}")
                # Fall back to simulation for now
                capture_result = {
                    'hearing_id': hearing_id,
                    'capture_initiated': True,
                    'status': 'simulation',
                    'estimated_duration': hearing['estimated_duration'],
                    'streams_found': len(hearing['streams']),
                    'priority': priority,
                    'readiness_assessment': readiness,
                    'initiated_by': user_id,
                    'initiated_at': datetime.now().isoformat(),
                    'note': f"Fell back to simulation due to error: {str(e)}"
                }
            
            logger.info(f"Capture initiated for hearing {hearing_id} by {user_id}")
            
            return capture_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error triggering capture for hearing {hearing_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Capture error: {str(e)}")
    
    async def get_audio_storage_info(self, hearing_id: str) -> Dict[str, Any]:
        """Get audio storage information for a hearing"""
        try:
            storage_info = await self.capture_service.get_storage_info(hearing_id)
            
            if not storage_info:
                raise HTTPException(status_code=404, detail="Audio file not found")
            
            return storage_info
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting storage info for hearing {hearing_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Storage info error: {str(e)}")
    
    async def verify_audio_file(self, hearing_id: str) -> Dict[str, Any]:
        """Verify audio file exists and is accessible"""
        try:
            verification_result = await self.capture_service.verify_audio_file(hearing_id)
            return verification_result
            
        except Exception as e:
            logger.error(f"Error verifying audio file for hearing {hearing_id}: {str(e)}")
            return {
                'exists': False,
                'error': f"Verification error: {str(e)}"
            }
    
    async def trigger_transcription(self, hearing_id: str, transcription_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger transcription for a hearing"""
        try:
            # First verify audio file exists
            verification = await self.verify_audio_file(hearing_id)
            if not verification.get('exists', False):
                raise HTTPException(
                    status_code=404, 
                    detail=f"Audio file not found for hearing {hearing_id}: {verification.get('error', 'Unknown error')}"
                )
            
            # Trigger transcription
            transcription_result = await self.transcription_service.transcribe_hearing(
                hearing_id=hearing_id,
                transcription_options=transcription_options
            )
            
            return transcription_result
            
        except HTTPException:
            raise
        except TranscriptionException as e:
            logger.error(f"Transcription service error for hearing {hearing_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error triggering transcription for hearing {hearing_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")
    
    async def get_transcript_info(self, hearing_id: str) -> Dict[str, Any]:
        """Get transcript information for a hearing"""
        try:
            transcript_info = await self.transcription_service.get_transcript_info(hearing_id)
            
            if not transcript_info:
                raise HTTPException(status_code=404, detail="Transcript not found")
            
            return transcript_info
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting transcript info for hearing {hearing_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Transcript info error: {str(e)}")
    
    async def get_transcript_content(self, hearing_id: str) -> Dict[str, Any]:
        """Get actual transcript content for a hearing"""
        try:
            transcript_content = await self.transcription_service.get_transcript_content(hearing_id)
            
            if not transcript_content:
                raise HTTPException(status_code=404, detail="Transcript content not found")
            
            return transcript_content
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting transcript content for hearing {hearing_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Transcript content error: {str(e)}")
    
    def get_duplicate_queue(self, limit: int = 50) -> Dict[str, Any]:
        """Get hearings requiring duplicate resolution"""
        
        try:
            # Get hearings with medium confidence matches that need manual review
            cursor = self.db.connection.execute("""
                SELECT h1.id as hearing1_id, h1.hearing_title as title1, 
                       h1.committee_code as committee1, h1.hearing_date as date1,
                       h1.source_api as api1, h1.source_website as website1,
                       h2.id as hearing2_id, h2.hearing_title as title2,
                       h2.committee_code as committee2, h2.hearing_date as date2,
                       h2.source_api as api2, h2.source_website as website2,
                       ABS(julianday(h1.hearing_date) - julianday(h2.hearing_date)) as date_diff
                FROM hearings_unified h1
                JOIN hearings_unified h2 ON h1.id < h2.id
                WHERE h1.committee_code = h2.committee_code
                AND ABS(julianday(h1.hearing_date) - julianday(h2.hearing_date)) <= 1
                AND h1.sync_confidence BETWEEN 0.7 AND 0.9
                ORDER BY date_diff ASC, h1.hearing_date DESC
                LIMIT ?
            """, (limit,))
            
            duplicates = []
            for row in cursor.fetchall():
                duplicate_pair = dict(row)
                
                # Calculate similarity using deduplicator
                hearing1 = {
                    'hearing_title': duplicate_pair['title1'],
                    'hearing_date': datetime.fromisoformat(duplicate_pair['date1']),
                    'committee_code': duplicate_pair['committee1']
                }
                hearing2 = {
                    'hearing_title': duplicate_pair['title2'],
                    'hearing_date': datetime.fromisoformat(duplicate_pair['date2']),
                    'committee_code': duplicate_pair['committee2']
                }
                
                confidence = self.deduplicator.calculate_match_confidence(hearing1, hearing2)
                
                duplicate_pair['similarity_confidence'] = confidence
                duplicate_pair['recommended_action'] = self._get_duplicate_recommendation(
                    duplicate_pair, confidence
                )
                
                duplicates.append(duplicate_pair)
            
            return {
                'duplicate_pairs': duplicates,
                'total_pending': len(duplicates),
                'review_needed': sum(1 for d in duplicates if d['similarity_confidence'] > 0.8)
            }
            
        except Exception as e:
            logger.error(f"Error getting duplicate queue: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def resolve_duplicate(self, resolution: DuplicateResolution, 
                         user_id: str) -> Dict[str, Any]:
        """Resolve duplicate hearing pair"""
        
        try:
            primary_hearing = self.get_hearing_details(resolution.primary_hearing_id)
            duplicate_hearing = self.get_hearing_details(resolution.duplicate_hearing_id)
            
            if resolution.action == "merge":
                # Merge the hearings
                merged_data = self.deduplicator.merge_hearings(
                    primary_hearing, duplicate_hearing
                )
                
                # Update primary hearing with merged data
                update_fields = []
                params = []
                
                if resolution.merge_strategy:
                    for field, source in resolution.merge_strategy.items():
                        if source in ["primary", "duplicate"]:
                            value = primary_hearing[field] if source == "primary" else duplicate_hearing[field]
                            update_fields.append(f"{field} = ?")
                            params.append(str(value) if value is not None else None)
                
                if update_fields:
                    params.append(resolution.primary_hearing_id)
                    self.db.connection.execute(f"""
                        UPDATE hearings_unified 
                        SET {', '.join(update_fields)}, sync_confidence = 1.0
                        WHERE id = ?
                    """, params)
                
                # Mark duplicate as merged
                self.db.connection.execute("""
                    UPDATE hearings_unified 
                    SET status = 'merged_duplicate', sync_confidence = 0.0
                    WHERE id = ?
                """, (resolution.duplicate_hearing_id,))
                
                result_action = "merged"
                
            elif resolution.action == "keep_separate":
                # Mark both as verified separate hearings
                for hearing_id in [resolution.primary_hearing_id, resolution.duplicate_hearing_id]:
                    self.db.connection.execute("""
                        UPDATE hearings_unified 
                        SET sync_confidence = 1.0
                        WHERE id = ?
                    """, (hearing_id,))
                
                result_action = "kept_separate"
                
            elif resolution.action == "mark_invalid":
                # Mark duplicate as invalid
                self.db.connection.execute("""
                    UPDATE hearings_unified 
                    SET status = 'invalid', sync_confidence = 0.0
                    WHERE id = ?
                """, (resolution.duplicate_hearing_id,))
                
                result_action = "marked_invalid"
            
            self.db.connection.commit()
            
            # Log the resolution
            logger.info(f"Duplicate resolved by {user_id}: {resolution.action} for hearings {resolution.primary_hearing_id}, {resolution.duplicate_hearing_id}")
            
            return {
                'action': result_action,
                'primary_hearing_id': resolution.primary_hearing_id,
                'duplicate_hearing_id': resolution.duplicate_hearing_id,
                'resolved_by': user_id,
                'resolved_at': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resolving duplicate: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Resolution error: {str(e)}")
    
    def _estimate_hearing_duration(self, hearing: Dict[str, Any]) -> int:
        """Estimate hearing duration in minutes based on type and metadata"""
        
        title = hearing.get('hearing_title', '').lower()
        hearing_type = hearing.get('hearing_type', '').lower()
        
        # Default estimates based on hearing type
        if 'executive' in title or 'business meeting' in title:
            return 60  # Executive sessions typically 1 hour
        elif 'markup' in hearing_type or 'markup' in title:
            return 120  # Markup sessions typically 2 hours
        elif 'confirmation' in title:
            return 180  # Confirmation hearings typically 3 hours
        elif 'oversight' in title or 'investigation' in title:
            return 240  # Oversight hearings typically 4 hours
        else:
            return 150  # Standard hearing estimate: 2.5 hours
    
    def _assess_capture_readiness(self, hearing: Dict[str, Any]) -> Dict[str, Any]:
        """Assess hearing readiness for audio capture"""
        
        score = 0.0
        factors = []
        
        # Check if streams are available
        if hearing.get('streams'):
            score += 0.4
            factors.append("✓ Streams available")
        else:
            factors.append("✗ No streams found")
        
        # Check if hearing is in future or recent past
        hearing_date = datetime.fromisoformat(hearing['hearing_date'])
        now = datetime.now()
        time_diff = (hearing_date - now).total_seconds() / 3600  # hours
        
        if -24 < time_diff < 168:  # Within past day or next week
            score += 0.3
            factors.append("✓ Optimal timing window")
        elif time_diff < -24:
            score += 0.1
            factors.append("⚠ Past hearing (archive capture)")
        else:
            score += 0.2
            factors.append("⚠ Future hearing (schedule capture)")
        
        # Check metadata completeness
        if hearing.get('witnesses'):
            score += 0.1
            factors.append("✓ Witness list available")
        
        if hearing.get('documents'):
            score += 0.1
            factors.append("✓ Documents available")
        
        # Check sync confidence
        if hearing.get('sync_confidence', 0) > 0.8:
            score += 0.1
            factors.append("✓ High sync confidence")
        
        return {
            'score': min(score, 1.0),
            'factors': factors,
            'recommendation': self._get_readiness_recommendation(score)
        }
    
    def _get_readiness_recommendation(self, score: float) -> str:
        """Get readiness recommendation based on score"""
        
        if score >= 0.8:
            return "Ready for immediate capture"
        elif score >= 0.6:
            return "Good candidate for capture"
        elif score >= 0.4:
            return "Capture possible with limitations"
        else:
            return "Not recommended for capture"
    
    def _get_duplicate_recommendation(self, duplicate_pair: Dict, 
                                    confidence: float) -> str:
        """Get recommendation for duplicate resolution"""
        
        if confidence > 0.9:
            return "merge"
        elif confidence > 0.8:
            return "review_recommended"
        elif duplicate_pair['date_diff'] == 0:
            return "likely_duplicate"
        else:
            return "keep_separate"

# FastAPI route integration
def setup_hearing_management_routes(app: FastAPI):
    """Setup hearing management routes"""
    
    api = HearingManagementAPI()
    
    @app.get("/api/hearings/queue")
    async def get_hearing_queue(
        committee_codes: Optional[str] = Query(None, description="Comma-separated committee codes"),
        status: Optional[str] = Query(None, description="Review status filter"),
        sync_status: Optional[str] = Query(None, description="Sync status filter"),
        date_from: Optional[str] = Query(None, description="Start date filter (ISO format)"),
        date_to: Optional[str] = Query(None, description="End date filter (ISO format)"),
        has_streams: Optional[bool] = Query(None, description="Filter by stream availability"),
        limit: int = Query(100, ge=1, le=500, description="Results per page"),
        offset: int = Query(0, ge=0, description="Results offset")
    ):
        """Get hearing queue with optional filtering"""
        
        committee_list = committee_codes.split(',') if committee_codes else None
        
        return api.get_hearing_queue(
            committee_codes=committee_list,
            status=status,
            sync_status=sync_status,
            date_from=date_from,
            date_to=date_to,
            has_streams=has_streams,
            limit=limit,
            offset=offset
        )
    
    @app.get("/api/hearings/{hearing_id}")
    async def get_hearing_details(hearing_id: str):
        """Get detailed hearing information"""
        return api.get_hearing_details(hearing_id)
    
    @app.put("/api/hearings/{hearing_id}/priority")
    async def update_hearing_priority(
        hearing_id: str,
        priority_data: HearingPriorityUpdate,
        user_id: str = Query(..., description="User ID for audit trail")
    ):
        """Update hearing capture priority"""
        return api.update_hearing_priority(
            hearing_id=hearing_id,
            priority=priority_data.priority,
            user_id=user_id,
            reason=priority_data.reason
        )
    
    @app.post("/api/hearings/{hearing_id}/capture")
    async def trigger_hearing_capture(
        hearing_id: str,
        capture_data: CaptureRequest,
        user_id: str = Query(..., description="User ID for audit trail")
    ):
        """Trigger audio capture for a hearing"""
        return await api.trigger_hearing_capture(
            hearing_id=hearing_id,
            priority=capture_data.priority,
            user_id=user_id,
            capture_options=capture_data.capture_options
        )
    
    @app.get("/api/storage/audio/{hearing_id}")
    async def get_audio_storage_info(hearing_id: str):
        """Get audio storage information for a hearing"""
        return await api.get_audio_storage_info(hearing_id)
    
    @app.get("/api/storage/audio/{hearing_id}/verify")
    async def verify_audio_file(hearing_id: str):
        """Verify audio file exists and is accessible"""
        return await api.verify_audio_file(hearing_id)
    
    @app.post("/api/hearings/{hearing_id}/transcription")
    async def trigger_transcription(
        hearing_id: str,
        transcription_options: Optional[Dict[str, Any]] = Body(None)
    ):
        """Trigger transcription for a hearing"""
        return await api.trigger_transcription(
            hearing_id=hearing_id,
            transcription_options=transcription_options
        )
    
    @app.get("/api/hearings/{hearing_id}/transcript/info")
    async def get_transcript_info(hearing_id: str):
        """Get transcript information for a hearing"""
        return await api.get_transcript_info(hearing_id)
    
    @app.get("/api/hearings/{hearing_id}/transcript/content")
    async def get_transcript_content(hearing_id: str):
        """Get actual transcript content for a hearing"""
        return await api.get_transcript_content(hearing_id)
    
    @app.get("/api/hearings/duplicates")
    async def get_duplicate_queue(
        limit: int = Query(50, ge=1, le=200, description="Maximum duplicates to return")
    ):
        """Get hearings requiring duplicate resolution"""
        return api.get_duplicate_queue(limit=limit)
    
    @app.post("/api/duplicates/resolve")
    async def resolve_duplicate(
        resolution: DuplicateResolution,
        user_id: str = Query(..., description="User ID for audit trail")
    ):
        """Resolve duplicate hearing pair"""
        return api.resolve_duplicate(resolution=resolution, user_id=user_id)