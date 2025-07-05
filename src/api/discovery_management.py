"""
Discovery Management API
Provides endpoints for hearing discovery and selective processing
"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pydantic import BaseModel

from .discovery_service import get_discovery_service
from .pipeline_controller import get_pipeline_controller

logger = logging.getLogger(__name__)

# Request/Response Models
class DiscoveryRequest(BaseModel):
    committee_codes: Optional[List[str]] = None

class CaptureRequest(BaseModel):
    hearing_id: str
    options: Optional[Dict[str, Any]] = None

class HearingFilter(BaseModel):
    committee_codes: Optional[List[str]] = None
    status: Optional[str] = None
    limit: int = 50

def setup_discovery_management_routes(app: FastAPI):
    """Setup discovery management routes"""
    
    discovery_service = get_discovery_service()
    pipeline_controller = get_pipeline_controller()
    
    @app.post("/api/hearings/discover")
    async def discover_hearings(request: DiscoveryRequest):
        """
        Run hearing discovery
        
        Args:
            request: Discovery request with optional committee codes
            
        Returns:
            Discovery results
        """
        try:
            logger.info(f"Starting hearing discovery for committees: {request.committee_codes}")
            
            result = await discovery_service.discover_hearings(request.committee_codes)
            
            return JSONResponse(content={
                "success": True,
                "data": result,
                "message": f"Discovery completed: {result['new_hearings']} new hearings found"
            })
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": "Discovery failed",
                    "message": str(e)
                }
            )
    
    @app.get("/api/hearings/discovered")
    async def get_discovered_hearings(
        committee_codes: Optional[List[str]] = Query(None),
        status: Optional[str] = Query(None),
        limit: int = Query(50, ge=1, le=200)
    ):
        """
        Get discovered hearings with optional filtering
        
        Args:
            committee_codes: Filter by committee codes
            status: Filter by status
            limit: Maximum number of results
            
        Returns:
            List of discovered hearings
        """
        try:
            logger.info(f"Getting discovered hearings - committees: {committee_codes}, status: {status}")
            
            hearings = discovery_service.get_discovered_hearings(
                committee_codes=committee_codes,
                status=status,
                limit=limit
            )
            
            # Convert to dict for JSON response
            hearings_data = []
            for hearing in hearings:
                hearing_dict = hearing.__dict__.copy()
                hearings_data.append(hearing_dict)
            
            return JSONResponse(content={
                "success": True,
                "data": {
                    "hearings": hearings_data,
                    "total": len(hearings_data),
                    "filters": {
                        "committee_codes": committee_codes,
                        "status": status,
                        "limit": limit
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting discovered hearings: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": "Failed to get discovered hearings",
                    "message": str(e)
                }
            )
    
    @app.post("/api/hearings/{hearing_id}/capture")
    async def capture_hearing(hearing_id: str, request: CaptureRequest):
        """
        Trigger capture and processing pipeline for a hearing
        
        Args:
            hearing_id: Hearing ID to process
            request: Capture request with options
            
        Returns:
            Processing start confirmation
        """
        try:
            logger.info(f"Starting capture for hearing {hearing_id}")
            
            # Validate hearing_id matches request
            if hearing_id != request.hearing_id:
                raise HTTPException(
                    status_code=400,
                    detail="Hearing ID mismatch"
                )
            
            result = await pipeline_controller.start_processing(hearing_id, request.options)
            
            return JSONResponse(content={
                "success": True,
                "data": result,
                "message": f"Processing started for hearing {hearing_id}"
            })
            
        except ValueError as e:
            logger.error(f"Validation error for hearing {hearing_id}: {e}")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "Validation failed",
                    "message": str(e)
                }
            )
        except Exception as e:
            logger.error(f"Error starting capture for hearing {hearing_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": "Failed to start capture",
                    "message": str(e)
                }
            )
    
    @app.get("/api/hearings/{hearing_id}/progress")
    async def get_processing_progress(hearing_id: str):
        """
        Get processing progress for a hearing
        
        Args:
            hearing_id: Hearing ID
            
        Returns:
            Processing progress
        """
        try:
            progress = pipeline_controller.get_processing_progress(hearing_id)
            
            if progress is None:
                return JSONResponse(content={
                    "success": True,
                    "data": {
                        "hearing_id": hearing_id,
                        "status": "not_processing",
                        "message": "No active processing for this hearing"
                    }
                })
            
            return JSONResponse(content={
                "success": True,
                "data": {
                    "hearing_id": hearing_id,
                    "progress": progress.__dict__
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting progress for hearing {hearing_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": "Failed to get progress",
                    "message": str(e)
                }
            )
    
    @app.post("/api/hearings/{hearing_id}/cancel")
    async def cancel_processing(hearing_id: str):
        """
        Cancel active processing for a hearing
        
        Args:
            hearing_id: Hearing ID
            
        Returns:
            Cancellation confirmation
        """
        try:
            logger.info(f"Cancelling processing for hearing {hearing_id}")
            
            success = await pipeline_controller.cancel_processing(hearing_id)
            
            if success:
                return JSONResponse(content={
                    "success": True,
                    "data": {
                        "hearing_id": hearing_id,
                        "status": "cancelled"
                    },
                    "message": f"Processing cancelled for hearing {hearing_id}"
                })
            else:
                return JSONResponse(content={
                    "success": False,
                    "error": "No active processing to cancel",
                    "message": f"No active processing found for hearing {hearing_id}"
                })
                
        except Exception as e:
            logger.error(f"Error cancelling processing for hearing {hearing_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": "Failed to cancel processing",
                    "message": str(e)
                }
            )
    
    @app.get("/api/hearings/stats")
    async def get_discovery_stats():
        """
        Get discovery statistics
        
        Returns:
            Discovery statistics
        """
        try:
            stats = discovery_service.get_discovery_stats()
            
            # Add active processing stats
            active_processes = pipeline_controller.get_active_processes()
            stats["active_processes"] = len(active_processes)
            stats["active_hearings"] = list(active_processes.keys())
            
            return JSONResponse(content={
                "success": True,
                "data": stats
            })
            
        except Exception as e:
            logger.error(f"Error getting discovery stats: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": "Failed to get statistics",
                    "message": str(e)
                }
            )
    
    @app.get("/api/hearings/processing")
    async def get_active_processing():
        """
        Get all active processing activities
        
        Returns:
            Active processing information
        """
        try:
            active_processes = pipeline_controller.get_active_processes()
            
            # Convert to serializable format
            processes_data = {}
            for hearing_id, progress in active_processes.items():
                processes_data[hearing_id] = progress.__dict__
            
            return JSONResponse(content={
                "success": True,
                "data": {
                    "active_count": len(active_processes),
                    "processes": processes_data
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting active processing: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": "Failed to get active processing",
                    "message": str(e)
                }
            )
    
    @app.get("/api/hearings/{hearing_id}")
    async def get_hearing_details(hearing_id: str):
        """
        Get detailed information about a specific hearing
        
        Args:
            hearing_id: Hearing ID
            
        Returns:
            Hearing details
        """
        try:
            # Get from discovered hearings
            hearings = discovery_service.get_discovered_hearings()
            hearing = next((h for h in hearings if h.id == hearing_id), None)
            
            if not hearing:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "success": False,
                        "error": "Hearing not found",
                        "message": f"Hearing {hearing_id} not found"
                    }
                )
            
            # Get processing progress if active
            progress = pipeline_controller.get_processing_progress(hearing_id)
            
            return JSONResponse(content={
                "success": True,
                "data": {
                    "hearing": hearing.__dict__,
                    "progress": progress.__dict__ if progress else None
                }
            })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting hearing details for {hearing_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": "Failed to get hearing details",
                    "message": str(e)
                }
            )

    logger.info("Discovery management routes configured")