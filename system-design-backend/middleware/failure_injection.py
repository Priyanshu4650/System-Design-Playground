import asyncio
import hashlib
import random
import time
from functools import wraps
from typing import Callable
from config.failure_injection import config
from exceptions.retryable import InjectedFailureException, DatabaseTimeoutException
from v1.services.observability import logger
from prometheus_client import Counter, Histogram

# Metrics
INJECTED_FAILURES = Counter('injected_failures_total', 'Total injected failures', ['operation'])
DB_LATENCY_HISTOGRAM = Histogram('db_operation_duration_seconds', 'Database operation latency')

def inject_db_latency():
    """Decorator to inject artificial database latency"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if config.DB_LATENCY_MAX_MS > 0:
                latency_ms = random.randint(config.DB_LATENCY_MIN_MS, config.DB_LATENCY_MAX_MS)
                await asyncio.sleep(latency_ms / 1000.0)
                logger.debug("injected_db_latency", latency_ms=latency_ms, operation=func.__name__)
            
            with DB_LATENCY_HISTOGRAM.time():
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if config.DB_LATENCY_MAX_MS > 0:
                latency_ms = random.randint(config.DB_LATENCY_MIN_MS, config.DB_LATENCY_MAX_MS)
                time.sleep(latency_ms / 1000.0)
                logger.debug("injected_db_latency", latency_ms=latency_ms, operation=func.__name__)
            
            with DB_LATENCY_HISTOGRAM.time():
                return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def inject_random_failure(operation_name: str):
    """Decorator to inject random failures based on request_id"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if config.FAILURE_INJECTION_ENABLED and config.FAILURE_RATE > 0:
                request_id = kwargs.get('request_id') or getattr(args[0], 'request_id', 'default')
                
                hash_value = int(hashlib.md5(f"{request_id}:{operation_name}".encode()).hexdigest()[:8], 16)
                failure_threshold = config.FAILURE_RATE * (2**32)
                
                if hash_value < failure_threshold:
                    INJECTED_FAILURES.labels(operation=operation_name).inc()
                    logger.warning("injected_failure", 
                                 operation=operation_name, 
                                 request_id=request_id,
                                 failure_rate=config.FAILURE_RATE)
                    raise InjectedFailureException(f"Injected failure in {operation_name}")
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if config.FAILURE_INJECTION_ENABLED and config.FAILURE_RATE > 0:
                request_id = kwargs.get('request_id') or getattr(args[0], 'request_id', 'default')
                
                hash_value = int(hashlib.md5(f"{request_id}:{operation_name}".encode()).hexdigest()[:8], 16)
                failure_threshold = config.FAILURE_RATE * (2**32)
                
                if hash_value < failure_threshold:
                    INJECTED_FAILURES.labels(operation=operation_name).inc()
                    logger.warning("injected_failure", 
                                 operation=operation_name, 
                                 request_id=request_id,
                                 failure_rate=config.FAILURE_RATE)
                    raise InjectedFailureException(f"Injected failure in {operation_name}")
            
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def with_timeout(timeout_seconds: float, exception_class=DatabaseTimeoutException):
    """Decorator to add timeout to operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                logger.error("operation_timeout", 
                           operation=func.__name__, 
                           timeout_seconds=timeout_seconds)
                raise exception_class(f"Operation {func.__name__} timed out after {timeout_seconds}s")
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else func
    return decorator