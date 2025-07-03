"""
Prometheus metrics for Senate Hearing Audio Capture
"""

from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server
from functools import wraps
import time
import asyncio
from typing import Callable, Any

# HTTP Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Processing metrics
processing_queue_size = Gauge(
    'processing_queue_size',
    'Number of items in processing queue'
)

processing_failures_total = Counter(
    'processing_failures_total',
    'Total processing failures',
    ['type', 'reason']
)

processing_duration_seconds = Histogram(
    'processing_duration_seconds',
    'Processing duration in seconds',
    ['type']
)

transcription_quality_score = Gauge(
    'transcription_quality_score',
    'Current transcription quality score'
)

# Database metrics
database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

database_queries_total = Counter(
    'database_queries_total',
    'Total database queries',
    ['operation']
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation']
)

# Cache metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['type']
)

# Audio processing metrics
audio_files_processed_total = Counter(
    'audio_files_processed_total',
    'Total audio files processed',
    ['committee', 'status']
)

audio_processing_duration_seconds = Histogram(
    'audio_processing_duration_seconds',
    'Audio processing duration in seconds',
    ['committee']
)

# Voice recognition metrics
voice_recognition_accuracy = Gauge(
    'voice_recognition_accuracy',
    'Voice recognition accuracy score'
)

speaker_identification_success_rate = Gauge(
    'speaker_identification_success_rate',
    'Speaker identification success rate'
)

# System metrics
system_health_status = Gauge(
    'system_health_status',
    'System health status (1=healthy, 0=unhealthy)',
    ['component']
)

# Decorators for automatic metrics collection
def track_requests(func: Callable) -> Callable:
    """Decorator to track HTTP requests"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        status = 200
        method = kwargs.get('method', 'GET')
        endpoint = kwargs.get('endpoint', 'unknown')
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status = getattr(e, 'status_code', 500)
            raise
        finally:
            duration = time.time() - start_time
            http_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    return wrapper

def track_processing(processing_type: str):
    """Decorator to track processing operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                processing_failures_total.labels(type=processing_type, reason=type(e).__name__).inc()
                raise
            finally:
                duration = time.time() - start_time
                processing_duration_seconds.labels(type=processing_type).observe(duration)
        
        return wrapper
    return decorator

def track_database_query(operation: str):
    """Decorator to track database queries"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                database_queries_total.labels(operation=operation).inc()
                database_query_duration_seconds.labels(operation=operation).observe(duration)
        
        return wrapper
    return decorator

class MetricsCollector:
    """Metrics collector for application metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        
    async def update_system_health(self, component: str, is_healthy: bool):
        """Update system health status"""
        system_health_status.labels(component=component).set(1 if is_healthy else 0)
        
    async def update_processing_queue_size(self, size: int):
        """Update processing queue size"""
        processing_queue_size.set(size)
        
    async def update_transcription_quality(self, score: float):
        """Update transcription quality score"""
        transcription_quality_score.set(score)
        
    async def update_voice_recognition_accuracy(self, accuracy: float):
        """Update voice recognition accuracy"""
        voice_recognition_accuracy.set(accuracy)
        
    async def update_speaker_identification_success_rate(self, rate: float):
        """Update speaker identification success rate"""
        speaker_identification_success_rate.set(rate)
        
    async def record_audio_processing(self, committee: str, status: str, duration: float):
        """Record audio processing completion"""
        audio_files_processed_total.labels(committee=committee, status=status).inc()
        audio_processing_duration_seconds.labels(committee=committee).observe(duration)
        
    async def record_cache_hit(self, cache_type: str):
        """Record cache hit"""
        cache_hits_total.labels(type=cache_type).inc()
        
    async def record_cache_miss(self, cache_type: str):
        """Record cache miss"""
        cache_misses_total.labels(type=cache_type).inc()
        
    async def update_database_connections(self, active_connections: int):
        """Update active database connections"""
        database_connections_active.set(active_connections)

# Global metrics collector instance
metrics_collector = MetricsCollector()

def start_metrics_server(port: int = 9090):
    """Start Prometheus metrics server"""
    start_http_server(port)
    print(f"Metrics server started on port {port}")

# Health check metrics
async def update_health_metrics():
    """Update health metrics periodically"""
    while True:
        try:
            # Update system health for various components
            # This would typically check actual component health
            await metrics_collector.update_system_health('application', True)
            await metrics_collector.update_system_health('database', True)
            await metrics_collector.update_system_health('redis', True)
            await metrics_collector.update_system_health('storage', True)
            
            # Sleep for 30 seconds before next update
            await asyncio.sleep(30)
        except Exception as e:
            print(f"Error updating health metrics: {e}")
            await asyncio.sleep(30)