import time
from functools import wraps
from typing import Callable, Dict, Any
from models.tracing.trace_models import EventType
from tracing.trace_context import TraceContext

def trace_operation(event_type: EventType, metadata_func: Callable = None):
    """Decorator to automatically trace operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            request_id = TraceContext.get_request_id()
            if not request_id:
                return await func(*args, **kwargs)
            
            start_time = time.monotonic()
            metadata = {"operation": func.__name__}
            
            if metadata_func:
                try:
                    extra_metadata = metadata_func(*args, **kwargs)
                    metadata.update(extra_metadata)
                except Exception:
                    pass
            
            # Start event
            TraceContext.trace_event(event_type, metadata)
            
            try:
                result = await func(*args, **kwargs)
                
                # Success event
                end_time = time.monotonic()
                success_metadata = {
                    **metadata,
                    "latency_ms": (end_time - start_time) * 1000,
                    "success": True
                }
                
                if event_type == EventType.DB_CALL_STARTED:
                    TraceContext.trace_event(EventType.DB_CALL_COMPLETED, success_metadata)
                
                return result
                
            except Exception as e:
                # Failure event
                end_time = time.monotonic()
                failure_metadata = {
                    **metadata,
                    "latency_ms": (end_time - start_time) * 1000,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                
                if event_type == EventType.DB_CALL_STARTED:
                    TraceContext.trace_event(EventType.DB_CALL_FAILED, failure_metadata)
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            request_id = TraceContext.get_request_id()
            if not request_id:
                return func(*args, **kwargs)
            
            start_time = time.monotonic()
            metadata = {"operation": func.__name__}
            
            if metadata_func:
                try:
                    extra_metadata = metadata_func(*args, **kwargs)
                    metadata.update(extra_metadata)
                except Exception:
                    pass
            
            TraceContext.trace_event(event_type, metadata)
            
            try:
                result = func(*args, **kwargs)
                
                end_time = time.monotonic()
                success_metadata = {
                    **metadata,
                    "latency_ms": (end_time - start_time) * 1000,
                    "success": True
                }
                
                if event_type == EventType.DB_CALL_STARTED:
                    TraceContext.trace_event(EventType.DB_CALL_COMPLETED, success_metadata)
                
                return result
                
            except Exception as e:
                end_time = time.monotonic()
                failure_metadata = {
                    **metadata,
                    "latency_ms": (end_time - start_time) * 1000,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                
                if event_type == EventType.DB_CALL_STARTED:
                    TraceContext.trace_event(EventType.DB_CALL_FAILED, failure_metadata)
                
                raise
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    return decorator

def trace_retry(attempt: int, delay: float, error: Exception):
    """Helper function to trace retry attempts"""
    TraceContext.trace_event(
        EventType.RETRY_ATTEMPTED,
        {
            "attempt": attempt,
            "delay_seconds": delay,
            "error": str(error),
            "error_type": type(error).__name__
        }
    )

def trace_failure_injection(operation: str, failure_rate: float):
    """Helper function to trace injected failures"""
    TraceContext.trace_event(
        EventType.FAILURE_INJECTED,
        {
            "operation": operation,
            "failure_rate": failure_rate
        }
    )