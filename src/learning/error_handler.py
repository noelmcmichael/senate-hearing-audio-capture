#!/usr/bin/env python3
"""
Enhanced Error Handling for Phase 6C Learning System

Provides robust error handling, circuit breaker patterns,
and graceful degradation capabilities for learning components.
"""

import logging
import time
import functools
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class ComponentStatus(Enum):
    """Component operational status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"     # Normal operation
    OPEN = "open"         # Failures detected, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for external service calls."""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Exception = Exception):
        """Initialize circuit breaker."""
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"Circuit breaker half-open for {func.__name__}")
                else:
                    logger.warning(f"Circuit breaker open for {func.__name__}")
                    raise Exception(f"Circuit breaker open for {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True
        return (datetime.now() - self.last_failure_time).total_seconds() > self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            logger.info("Circuit breaker closed - service recovered")
        self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")


class ComponentHealthMonitor:
    """Monitor health status of learning components."""
    
    def __init__(self):
        """Initialize health monitor."""
        self.component_status = defaultdict(lambda: ComponentStatus.HEALTHY)
        self.error_counts = defaultdict(int)
        self.last_error_times = defaultdict(lambda: None)
        self.component_metrics = defaultdict(dict)
    
    def record_error(self, component: str, error: Exception, context: Dict[str, Any] = None):
        """Record error for a component."""
        self.error_counts[component] += 1
        self.last_error_times[component] = datetime.now()
        
        # Update component status based on error frequency
        if self.error_counts[component] >= 5:
            self.component_status[component] = ComponentStatus.FAILED
        elif self.error_counts[component] >= 2:
            self.component_status[component] = ComponentStatus.DEGRADED
        
        logger.error(f"Component {component} error: {error}")
        if context:
            logger.error(f"Error context: {context}")
    
    def record_success(self, component: str, metrics: Dict[str, Any] = None):
        """Record successful operation for a component."""
        if self.component_status[component] != ComponentStatus.HEALTHY:
            self.component_status[component] = ComponentStatus.RECOVERING
            logger.info(f"Component {component} recovering")
        
        # Reset error count after successful operation
        if self.component_status[component] == ComponentStatus.RECOVERING:
            self.error_counts[component] = max(0, self.error_counts[component] - 1)
            if self.error_counts[component] == 0:
                self.component_status[component] = ComponentStatus.HEALTHY
                logger.info(f"Component {component} fully recovered")
        
        if metrics:
            self.component_metrics[component].update(metrics)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        total_components = len(self.component_status)
        if total_components == 0:
            return {'status': 'unknown', 'components': {}}
        
        healthy_count = sum(1 for status in self.component_status.values() 
                          if status == ComponentStatus.HEALTHY)
        degraded_count = sum(1 for status in self.component_status.values() 
                           if status == ComponentStatus.DEGRADED)
        failed_count = sum(1 for status in self.component_status.values() 
                         if status == ComponentStatus.FAILED)
        
        # Determine overall system health
        if failed_count > 0:
            overall_status = "critical"
        elif degraded_count > total_components * 0.5:
            overall_status = "degraded"
        elif degraded_count > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            'status': overall_status,
            'total_components': total_components,
            'healthy': healthy_count,
            'degraded': degraded_count,
            'failed': failed_count,
            'components': dict(self.component_status),
            'error_counts': dict(self.error_counts),
            'metrics': dict(self.component_metrics)
        }
    
    def is_component_healthy(self, component: str) -> bool:
        """Check if a specific component is healthy."""
        return self.component_status[component] in [ComponentStatus.HEALTHY, ComponentStatus.RECOVERING]


def with_error_handling(component_name: str, 
                       health_monitor: ComponentHealthMonitor,
                       fallback_result: Any = None,
                       max_retries: int = 3,
                       retry_delay: float = 1.0):
    """Decorator for robust error handling with retries and health monitoring."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    health_monitor.record_success(component_name)
                    return result
                
                except Exception as e:
                    last_exception = e
                    context = {
                        'function': func.__name__,
                        'attempt': attempt + 1,
                        'max_retries': max_retries,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    }
                    
                    health_monitor.record_error(component_name, e, context)
                    
                    if attempt < max_retries:
                        logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}")
                        time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    else:
                        logger.error(f"All retries exhausted for {func.__name__}: {e}")
            
            # If all retries failed, return fallback result
            if fallback_result is not None:
                logger.warning(f"Using fallback result for {func.__name__}")
                return fallback_result
            
            # Re-raise the last exception if no fallback
            raise last_exception
        
        return wrapper
    return decorator


def safe_database_operation(func: Callable) -> Callable:
    """Decorator for safe database operations with connection management."""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Database operation failed in {func.__name__}: {e}")
            
            # Return empty result based on expected return type
            func_name = func.__name__
            if 'get' in func_name.lower() or 'fetch' in func_name.lower():
                if 'list' in func_name.lower() or 'data' in func_name.lower():
                    return []
                else:
                    return {}
            elif 'count' in func_name.lower():
                return 0
            elif 'exists' in func_name.lower():
                return False
            else:
                return None
    
    return wrapper


class GracefulDegradation:
    """Handles graceful degradation when components fail."""
    
    def __init__(self, health_monitor: ComponentHealthMonitor):
        """Initialize graceful degradation handler."""
        self.health_monitor = health_monitor
        self.fallback_strategies = {}
    
    def register_fallback(self, component: str, fallback_func: Callable):
        """Register a fallback function for a component."""
        self.fallback_strategies[component] = fallback_func
    
    def execute_with_fallback(self, component: str, primary_func: Callable, *args, **kwargs):
        """Execute function with fallback if component is unhealthy."""
        if self.health_monitor.is_component_healthy(component):
            try:
                return primary_func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Primary function failed for {component}: {e}")
                self.health_monitor.record_error(component, e)
        
        # Use fallback strategy
        if component in self.fallback_strategies:
            logger.info(f"Using fallback strategy for {component}")
            try:
                return self.fallback_strategies[component](*args, **kwargs)
            except Exception as e:
                logger.error(f"Fallback also failed for {component}: {e}")
                return None
        
        logger.warning(f"No fallback available for {component}")
        return None


# Global health monitor instance
health_monitor = ComponentHealthMonitor()

# Pre-configured circuit breakers for common operations
database_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
ml_model_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
file_io_circuit_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=15)