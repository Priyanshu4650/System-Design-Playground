from fastapi import APIRouter, Request as FastAPIRequest, status, HTTPException
from v1.routes.schema import PostRequestModel, PostResponseModel
import uuid
import time
from datetime import datetime
import hashlib
import json
from v1.services.database_service_traced import db_service_traced
from v1.services.idempotency_service import idempotency_service
from v1.models.request import Request
from v1.services.observability import logger
from v1.services.rate_limiting_service import rate_limiting_service, WindowType
from tracing.trace_context import TraceContext
from models.tracing.trace_models import EventType

router = APIRouter(prefix="/requests")

@router.post("/")
async def post_request_with_tracing(request_body: PostRequestModel, request: FastAPIRequest):
    start_time = time.time()
    
    # Validation with tracing
    headers = request.headers   
    if "Idempotency-Key" not in headers:
        TraceContext.trace_event(
            EventType.VALIDATION_FAILED,
            {"reason": "missing_idempotency_key"}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is missing"
        )
    
    TraceContext.trace_event(EventType.VALIDATION_PASSED, {"validation": "idempotency_key"})
    
    idempotency_key = headers["Idempotency-Key"]
    request_id = TraceContext.get_request_id()
    
    # Rate limiting check with tracing
    client_id = headers.get("X-Client-ID", "default")
    window_type = WindowType.SLIDING if request_body.rate_limiting_algo == "sliding_window" else WindowType.FIXED
    
    TraceContext.trace_event(
        EventType.RATE_LIMIT_CHECK,
        {
            "client_id": client_id,
            "max_requests": request_body.rate_limiting,
            "window_type": window_type.value
        }
    )
    
    if not rate_limiting_service.is_allowed(
        client_id=client_id,
        max_requests=request_body.rate_limiting,
        time_window=60, 
        window_type=window_type
    ):
        TraceContext.trace_event(
            EventType.RATE_LIMIT_EXCEEDED,
            {"client_id": client_id, "limit": request_body.rate_limiting}
        )
        
        duration = time.time() - start_time
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    # Cache check with tracing
    cached_response = idempotency_service.get_cached_response(
        idempotency_key, 
        cache_enabled=request_body.cache_enabled
    )
    
    if cached_response:
        TraceContext.trace_event(EventType.CACHE_HIT, {"key": idempotency_key})
        return PostResponseModel(**cached_response)
    else:
        TraceContext.trace_event(EventType.CACHE_MISS, {"key": idempotency_key})
    
    # Database check with automatic tracing via decorators
    existing_request = db_service_traced.get_by_idempotency_key(
        idempotency_key,
        request_id=request_id
    )
    
    if existing_request:
        response_data = {
            "status": status.HTTP_200_OK,
            "status_message": "received",
            "request_id": existing_request.request_id
        }
        
        # Cache the response
        idempotency_service.cache_response(
            idempotency_key, 
            response_data,
            cache_enabled=request_body.cache_enabled,
            cache_ttl=request_body.cache_ttl
        )
        
        return PostResponseModel(**response_data)
    
    # Process new request
    payload_str = json.dumps(request_body.dict(), sort_keys=True)
    payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()
    
    request_metadata = Request(
        request_id=request_id,
        received_at=datetime.utcnow(),
        endpoint=str(request.url.path),
        method=request.method,
        payload_hash=payload_hash,
        idempotency_key=idempotency_key,
        status="received"
    )
    
    try:
        # Create with automatic tracing via decorators
        db_service_traced.create(request_metadata, request_id=request_id)
        
        duration = time.time() - start_time
        request_metadata.latency_ms = int(duration * 1000)
        
        response_data = {
            "status": status.HTTP_200_OK,
            "status_message": "received",
            "request_id": request_id
        }
        
        # Cache with tracing
        idempotency_service.cache_response(
            idempotency_key, 
            response_data,
            cache_enabled=request_body.cache_enabled,
            cache_ttl=request_body.cache_ttl
        )
        
        return PostResponseModel(**response_data)
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error("request_failed", request_id=request_id, error=str(e))
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Request processing failed: {str(e)}"
        )