"""
Status Management API for Phase 7C Milestone 2
Provides endpoints for hearing status workflow management, reviewer assignment, and bulk operations.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import sqlite3

from .database_enhanced import get_enhanced_db

logger = logging.getLogger(__name__)

# Pydantic models for request/response
class StatusUpdateRequest(BaseModel):
    status: str = Field(..., description="New status (new|queued|processing|review|complete|error)")
    processing_stage: Optional[str] = Field(None, description="Processing stage (discovered|analyzed|captured|transcribed|reviewed|published)")
    reviewer_notes: Optional[str] = Field(None, description="Notes about the status change")

class ReviewerAssignmentRequest(BaseModel):
    assigned_reviewer: str = Field(..., description="Reviewer identifier/username")
    priority: Optional[int] = Field(0, description="Assignment priority (0-10)")
    notes: Optional[str] = Field(None, description="Assignment notes")

class BulkStatusUpdateRequest(BaseModel):
    hearing_ids: List[int] = Field(..., description="List of hearing IDs to update")
    status: str = Field(..., description="New status to apply")
    processing_stage: Optional[str] = Field(None, description="New processing stage")
    assigned_reviewer: Optional[str] = Field(None, description="Reviewer to assign")
    notes: Optional[str] = Field(None, description="Bulk operation notes")

class StatusUpdateResponse(BaseModel):
    success: bool
    hearing_id: int
    previous_status: Optional[str]
    new_status: str
    updated_at: str
    message: Optional[str] = None

class StatusSummaryResponse(BaseModel):
    total_hearings: int
    status_distribution: Dict[str, int]
    stage_distribution: Dict[str, int]
    recent_updates: List[Dict[str, Any]]

def setup_status_management_routes(app):
    """Setup status management routes on the FastAPI app"""
    
    router = APIRouter(prefix="/api", tags=["status-management"])
    
    # Valid status and stage values for validation
    VALID_STATUSES = {"new", "queued", "processing", "review", "complete", "error"}
    VALID_STAGES = {"discovered", "analyzed", "captured", "transcribed", "reviewed", "published"}
    
    def validate_status(status: str) -> bool:
        return status in VALID_STATUSES
    
    def validate_stage(stage: str) -> bool:
        return stage in VALID_STAGES
    
    @router.put("/hearings/{hearing_id}/status", response_model=StatusUpdateResponse)
    async def update_hearing_status(hearing_id: int, request: StatusUpdateRequest):
        """Update the status of a specific hearing"""
        
        # Validate inputs
        if not validate_status(request.status):
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
        
        if request.processing_stage and not validate_stage(request.processing_stage):
            raise HTTPException(status_code=400, detail=f"Invalid processing stage. Must be one of: {', '.join(VALID_STAGES)}")
        
        db = get_enhanced_db()
        try:
            # Get current status
            cursor = db.connection.execute(
                "SELECT status, processing_stage FROM hearings_unified WHERE id = ?",
                (hearing_id,)
            )
            current = cursor.fetchone()
            
            if not current:
                raise HTTPException(status_code=404, detail=f"Hearing {hearing_id} not found")
            
            previous_status = current['status']
            
            # Build update query
            update_fields = ["status = ?", "status_updated_at = datetime('now')"]
            params = [request.status]
            
            if request.processing_stage:
                update_fields.append("processing_stage = ?")
                params.append(request.processing_stage)
            
            if request.reviewer_notes:
                update_fields.append("reviewer_notes = ?")
                params.append(request.reviewer_notes)
            
            params.append(hearing_id)
            
            # Execute update
            cursor = db.connection.execute(
                f"UPDATE hearings_unified SET {', '.join(update_fields)} WHERE id = ?",
                params
            )
            
            db.connection.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=500, detail="Failed to update hearing status")
            
            return StatusUpdateResponse(
                success=True,
                hearing_id=hearing_id,
                previous_status=previous_status,
                new_status=request.status,
                updated_at=datetime.now().isoformat(),
                message=f"Status updated from '{previous_status}' to '{request.status}'"
            )
            
        except sqlite3.Error as e:
            logger.error(f"Database error updating hearing {hearing_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            db.close()
    
    @router.put("/hearings/{hearing_id}/reviewer")
    async def assign_reviewer(hearing_id: int, request: ReviewerAssignmentRequest):
        """Assign a reviewer to a hearing"""
        
        db = get_enhanced_db()
        try:
            # Check if hearing exists
            cursor = db.connection.execute(
                "SELECT id, assigned_reviewer FROM hearings_unified WHERE id = ?",
                (hearing_id,)
            )
            current = cursor.fetchone()
            
            if not current:
                raise HTTPException(status_code=404, detail=f"Hearing {hearing_id} not found")
            
            previous_reviewer = current['assigned_reviewer']
            
            # Update reviewer assignment
            update_fields = ["assigned_reviewer = ?", "status_updated_at = datetime('now')"]
            params = [request.assigned_reviewer]
            
            if request.notes:
                update_fields.append("reviewer_notes = ?")
                params.append(request.notes)
            
            params.append(hearing_id)
            
            cursor = db.connection.execute(
                f"UPDATE hearings_unified SET {', '.join(update_fields)} WHERE id = ?",
                params
            )
            
            db.connection.commit()
            
            return {
                "success": True,
                "hearing_id": hearing_id,
                "previous_reviewer": previous_reviewer,
                "new_reviewer": request.assigned_reviewer,
                "updated_at": datetime.now().isoformat()
            }
            
        except sqlite3.Error as e:
            logger.error(f"Database error assigning reviewer to hearing {hearing_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            db.close()
    
    @router.post("/hearings/bulk-status")
    async def bulk_update_status(request: BulkStatusUpdateRequest, background_tasks: BackgroundTasks):
        """Update status for multiple hearings"""
        
        # Validate inputs
        if not validate_status(request.status):
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
        
        if request.processing_stage and not validate_stage(request.processing_stage):
            raise HTTPException(status_code=400, detail=f"Invalid processing stage. Must be one of: {', '.join(VALID_STAGES)}")
        
        if len(request.hearing_ids) > 50:
            raise HTTPException(status_code=400, detail="Bulk operations limited to 50 hearings at once")
        
        db = get_enhanced_db()
        try:
            # Build bulk update query
            update_fields = ["status = ?", "status_updated_at = datetime('now')"]
            params = [request.status]
            
            if request.processing_stage:
                update_fields.append("processing_stage = ?")
                params.append(request.processing_stage)
            
            if request.assigned_reviewer:
                update_fields.append("assigned_reviewer = ?")
                params.append(request.assigned_reviewer)
            
            if request.notes:
                update_fields.append("reviewer_notes = ?")
                params.append(request.notes)
            
            # Create placeholders for hearing IDs
            id_placeholders = ",".join("?" * len(request.hearing_ids))
            params.extend(request.hearing_ids)
            
            # Execute bulk update
            cursor = db.connection.execute(
                f"""UPDATE hearings_unified 
                    SET {', '.join(update_fields)} 
                    WHERE id IN ({id_placeholders})""",
                params
            )
            
            db.connection.commit()
            updated_count = cursor.rowcount
            
            return {
                "success": True,
                "updated_count": updated_count,
                "requested_count": len(request.hearing_ids),
                "new_status": request.status,
                "updated_at": datetime.now().isoformat(),
                "message": f"Updated {updated_count} of {len(request.hearing_ids)} hearings"
            }
            
        except sqlite3.Error as e:
            logger.error(f"Database error in bulk status update: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            db.close()
    
    @router.get("/hearings/by-status/{status}")
    async def get_hearings_by_status(status: str, limit: int = 50):
        """Get hearings filtered by status"""
        
        if not validate_status(status):
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
        
        db = get_enhanced_db()
        try:
            cursor = db.connection.execute("""
                SELECT id, committee_code, hearing_title, hearing_date, 
                       status, processing_stage, assigned_reviewer, 
                       status_updated_at, reviewer_notes, sync_confidence
                FROM hearings_unified 
                WHERE status = ?
                ORDER BY status_updated_at DESC
                LIMIT ?
            """, (status, limit))
            
            hearings = [dict(row) for row in cursor.fetchall()]
            
            return {
                "status": status,
                "count": len(hearings),
                "hearings": hearings
            }
            
        except sqlite3.Error as e:
            logger.error(f"Database error filtering by status {status}: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            db.close()
    
    @router.get("/status/summary", response_model=StatusSummaryResponse)
    async def get_status_summary():
        """Get overall status summary and statistics"""
        
        db = get_enhanced_db()
        try:
            # Get total count
            cursor = db.connection.execute("SELECT COUNT(*) as total FROM hearings_unified")
            total = cursor.fetchone()['total']
            
            # Get status distribution
            cursor = db.connection.execute("""
                SELECT status, COUNT(*) as count 
                FROM hearings_unified 
                GROUP BY status
            """)
            status_dist = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Get stage distribution
            cursor = db.connection.execute("""
                SELECT processing_stage, COUNT(*) as count 
                FROM hearings_unified 
                GROUP BY processing_stage
            """)
            stage_dist = {row['processing_stage']: row['count'] for row in cursor.fetchall()}
            
            # Get recent updates (last 10)
            cursor = db.connection.execute("""
                SELECT id, committee_code, hearing_title, status, 
                       processing_stage, status_updated_at
                FROM hearings_unified 
                ORDER BY status_updated_at DESC
                LIMIT 10
            """)
            recent_updates = [dict(row) for row in cursor.fetchall()]
            
            return StatusSummaryResponse(
                total_hearings=total,
                status_distribution=status_dist,
                stage_distribution=stage_dist,
                recent_updates=recent_updates
            )
            
        except sqlite3.Error as e:
            logger.error(f"Database error getting status summary: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            db.close()
    
    # Add router to the app
    app.include_router(router)
    
    logger.info("Status management routes configured successfully")
    
    return router