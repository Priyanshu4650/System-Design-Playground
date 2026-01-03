import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from tracing.trace_context import TraceContext
from tracing.trace_storage import trace_storage
from models.tracing.trace_models import EventType
from v1.services.observability import logger

class TracingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for request tracing"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Extract request metadata
        request_metadata = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "idempotency_key": request.headers.get("idempotency-key")
        }
        
        start_time = time.monotonic()
        
        # Start tracing context
        with TraceContext(request_id, request_metadata):
            try:
                # Process request
                response = await call_next(request)
                
                # Calculate latency
                end_time = time.monotonic()
                total_latency_ms = (end_time - start_time) * 1000
                
                # Add response event
                TraceContext.trace_event(
                    EventType.RESPONSE_SENT,
                    {
                        "status_code": response.status_code,
                        "latency_ms": total_latency_ms
                    }
                )
                
                # Complete trace
                trace_storage.complete_trace(request_id, response.status_code, total_latency_ms)
                
                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id
                
                return response
                
            except Exception as e:
                # Handle errors
                end_time = time.monotonic()
                total_latency_ms = (end_time - start_time) * 1000
                
                TraceContext.trace_event(
                    EventType.REQUEST_COMPLETED,
                    {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "latency_ms": total_latency_ms
                    }
                )
                
                # Complete trace with error
                trace_storage.complete_trace(request_id, 500, total_latency_ms)
                
                logger.error("request_failed_in_middleware", 
                           request_id=request_id, 
                           error=str(e))
                
                raise