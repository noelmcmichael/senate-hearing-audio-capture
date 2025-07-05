"""
Health check endpoints for Senate Hearing Audio Capture
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio
import asyncpg
import redis
import time
from datetime import datetime
from google.cloud import storage
try:
    from src.config.production import config
except ImportError:
    config = None

try:
    from src.monitoring.metrics import metrics_collector
except ImportError:
    metrics_collector = None

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": config.ENV if config else "unknown"
    }

@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with component status"""
    start_time = time.time()
    
    # Check all components
    checks = await asyncio.gather(
        _check_database(),
        _check_redis(),
        _check_storage(),
        _check_processing_capability(),
        return_exceptions=True
    )
    
    database_health, redis_health, storage_health, processing_health = checks
    
    # Determine overall health
    all_healthy = all(
        isinstance(check, dict) and check.get('status') == 'healthy'
        for check in checks
    )
    
    total_time = time.time() - start_time
    
    result = {
        "overall_status": "healthy" if all_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "total_check_time": round(total_time, 3),
        "checks": {
            "database": database_health if isinstance(database_health, dict) else {"status": "unhealthy", "error": str(database_health)},
            "redis": redis_health if isinstance(redis_health, dict) else {"status": "unhealthy", "error": str(redis_health)},
            "storage": storage_health if isinstance(storage_health, dict) else {"status": "unhealthy", "error": str(storage_health)},
            "processing": processing_health if isinstance(processing_health, dict) else {"status": "unhealthy", "error": str(processing_health)}
        }
    }
    
    # Update metrics
    if metrics_collector:
        await metrics_collector.update_system_health('application', all_healthy)
    
    return result

@router.get("/health/database")
async def database_health_check() -> Dict[str, Any]:
    """Database health check endpoint"""
    return await _check_database()

@router.get("/health/redis")
async def redis_health_check() -> Dict[str, Any]:
    """Redis health check endpoint"""
    return await _check_redis()

@router.get("/health/storage")
async def storage_health_check() -> Dict[str, Any]:
    """Storage health check endpoint"""
    return await _check_storage()

@router.get("/health/processing")
async def processing_health_check() -> Dict[str, Any]:
    """Processing capability health check endpoint"""
    return await _check_processing_capability()

async def _check_database() -> Dict[str, Any]:
    """Check database connectivity and health"""
    try:
        start_time = time.time()
        
        # Parse database URL
        db_url = config.DATABASE_URL if config else None
        if not db_url:
            raise Exception("Database URL not configured")
            
        # Simple connection test
        conn = await asyncpg.connect(db_url)
        await conn.execute("SELECT 1")
        await conn.close()
        
        response_time = time.time() - start_time
        
        # Update metrics
        if metrics_collector:
            await metrics_collector.update_system_health('database', True)
        
        return {
            "status": "healthy",
            "response_time": round(response_time, 3),
            "message": "Database connection successful"
        }
        
    except Exception as e:
        if metrics_collector:
            await metrics_collector.update_system_health('database', False)
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Database connection failed"
        }

async def _check_redis() -> Dict[str, Any]:
    """Check Redis connectivity and health"""
    try:
        start_time = time.time()
        
        redis_url = config.REDIS_URL if config else None
        if not redis_url:
            raise Exception("Redis URL not configured")
            
        # Simple connection test
        r = redis.from_url(redis_url)
        r.ping()
        
        response_time = time.time() - start_time
        
        # Update metrics
        if metrics_collector:
            await metrics_collector.update_system_health('redis', True)
        
        return {
            "status": "healthy",
            "response_time": round(response_time, 3),
            "message": "Redis connection successful"
        }
        
    except Exception as e:
        if metrics_collector:
            await metrics_collector.update_system_health('redis', False)
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Redis connection failed"
        }

async def _check_storage() -> Dict[str, Any]:
    """Check Google Cloud Storage connectivity and health"""
    try:
        start_time = time.time()
        
        audio_bucket = config.AUDIO_BUCKET if config else None
        if not audio_bucket:
            raise Exception("Audio bucket not configured")
            
        # Simple storage test
        client = storage.Client()
        bucket = client.bucket(audio_bucket)
        
        # Check if bucket exists and is accessible
        bucket.reload()
        
        response_time = time.time() - start_time
        
        # Update metrics
        if metrics_collector:
            await metrics_collector.update_system_health('storage', True)
        
        return {
            "status": "healthy",
            "response_time": round(response_time, 3),
            "message": "Storage connection successful",
            "bucket": audio_bucket
        }
        
    except Exception as e:
        if metrics_collector:
            await metrics_collector.update_system_health('storage', False)
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Storage connection failed"
        }

async def _check_processing_capability() -> Dict[str, Any]:
    """Check processing capability health"""
    try:
        start_time = time.time()
        
        # Simple processing capability test
        # This would test the processing pipeline without actually processing
        
        # Check if required components are available
        components = {
            'whisper': True,  # Would check if Whisper is available
            'ffmpeg': True,   # Would check if FFmpeg is available
            'congress_api': bool(config.CONGRESS_API_KEY if config else False),
            'storage': bool(config.AUDIO_BUCKET if config else False)
        }
        
        all_components_healthy = all(components.values())
        
        response_time = time.time() - start_time
        
        # Update metrics
        if metrics_collector:
            await metrics_collector.update_system_health('processing', all_components_healthy)
        
        return {
            "status": "healthy" if all_components_healthy else "unhealthy",
            "response_time": round(response_time, 3),
            "message": "Processing capability check completed",
            "components": components
        }
        
    except Exception as e:
        if metrics_collector:
            await metrics_collector.update_system_health('processing', False)
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Processing capability check failed"
        }

@router.get("/readiness")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check for Kubernetes/Cloud Run"""
    # This should check if the application is ready to receive traffic
    detailed_health = await detailed_health_check()
    
    if detailed_health["overall_status"] == "healthy":
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Application not ready")

@router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check for Kubernetes/Cloud Run"""
    # This should check if the application is alive (simpler than readiness)
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": time.time() - (metrics_collector.start_time if metrics_collector else time.time())
    }