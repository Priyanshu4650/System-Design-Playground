import uuid
import time
import json
import hashlib
from datetime import datetime
from typing import Dict, Any

from v1.routes.schema import PostRequestModel
from v1.services.database_service_traced import db_service_traced as db_service
from v1.services.idempotency_service import idempotency_service
from v1.services.rate_limiting_service import rate_limiting_service, WindowType
from v1.models.request import Request
from v1.services.observability import logger
from tracing.trace_context import TraceContext
from models.tracing.trace_models import EventType

async def process_request_internal(payload: PostRequestModel, request_id: str = None) -> Dict[str, Any]:
    """
    Internal request processing function that can be called directly
    without HTTP overhead. Used by load testing service.
    """
    if not request_id:
        request_id = str(uuid.uuid4())
    
    start_time = time.time()
    
    # Generate idempotency key for load test requests
    idempotency_key = f"load_test_{request_id}"
    
    # Create minimal request metadata for tracing
    request_metadata = {
        "method": "POST",
        "endpoint": "/v1/requests/",
        "idempotency_key": idempotency_key,
        "source": "load_test"
    }
    
    # Start tracing context
    with TraceContext(request_id, request_metadata):
        try:
            TraceContext.trace_event(EventType.VALIDATION_PASSED, {"validation": "load_test_request"})
            
            # Rate limiting check
            client_id = "load_test_client"
            window_type = WindowType.SLIDING if payload.rate_limiting_algo == "sliding_window" else WindowType.FIXED
            
            TraceContext.trace_event(
                EventType.RATE_LIMIT_CHECK,
                {
                    "client_id": client_id,
                    "max_requests": payload.rate_limiting,
                    "window_type": window_type.value
                }
            )
            
            if not rate_limiting_service.is_allowed(
                client_id=client_id,
                max_requests=payload.rate_limiting,
                time_window=60,
                window_type=window_type
            ):
                TraceContext.trace_event(
                    EventType.RATE_LIMIT_EXCEEDED,
                    {"client_id": client_id, "limit": payload.rate_limiting}
                )
                return {
                    "status": 429,
                    "status_message": "rate_limited",
                    "request_id": request_id
                }
            
            # Check for existing response (idempotency)
            existing_response = idempotency_service.get_response_with_read_through(
                idempotency_key,
                cache_enabled=payload.cache_enabled,
                cache_ttl=payload.cache_ttl
            )
            
            if existing_response:
                TraceContext.trace_event(EventType.CACHE_HIT, {"key": idempotency_key})
                return existing_response
            else:
                TraceContext.trace_event(EventType.CACHE_MISS, {"key": idempotency_key})
            
            # Process new request
            payload_str = json.dumps(payload.dict(), sort_keys=True)
            payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()
            
            request_metadata_db = Request(
                request_id=request_id,
                received_at=datetime.utcnow(),
                endpoint="/v1/requests/",
                method="POST",
                payload_hash=payload_hash,
                idempotency_key=idempotency_key,
                status="received"
            )
            
            # Database operations
            db_service.create(request_metadata_db, request_id=request_id)
            
            duration = time.time() - start_time
            request_metadata_db.latency_ms = int(duration * 1000)
            
            response_data = {
                "status": 200,
                "status_message": "received",
                "request_id": request_id
            }
            
            # Cache response
            idempotency_service.cache_response(
                idempotency_key,
                response_data,
                cache_enabled=payload.cache_enabled,
                cache_ttl=payload.cache_ttl
            )
            
            TraceContext.trace_event(
                EventType.RESPONSE_SENT,
                {"status_code": 200, "latency_ms": duration * 1000}
            )
            
            return response_data
            
        except Exception as e:
            logger.error("internal_request_failed", request_id=request_id, error=str(e))
            return {
                "status": 500,
                "status_message": "internal_error",
                "request_id": request_id,
                "error": str(e)
            }