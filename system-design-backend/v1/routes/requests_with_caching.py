from fastapi import APIRouter, Request as FastAPIRequest, status, HTTPException
from v1.routes.schema import PostRequestModel, PostResponseModel
import uuid
import time
from datetime import datetime
import hashlib
import json
from v1.services.database_service import db_service
from v1.services.idempotency_service_enhanced import idempotency_service
from v1.models.request import Request
from v1.services.observability import logger, log_request
from v1.services.rate_limiting_service import rate_limiting_service, WindowType

router = APIRouter(prefix="/requests")

@router.post("/")
def post_request(request_body: PostRequestModel, request: FastAPIRequest):
    request_uuid = str(uuid.uuid4())
    start_time = time.time()
    
    headers = request.headers   
    if "Idempotency-Key" not in headers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is missing"
        )

    idempotency_key = headers["Idempotency-Key"]
    
    # Rate limiting check
    client_id = headers.get("X-Client-ID", "default")
    window_type = WindowType.SLIDING if request_body.rate_limiting_algo == "sliding_window" else WindowType.FIXED
    
    if not rate_limiting_service.is_allowed(
        client_id=client_id,
        max_requests=request_body.rate_limiting,
        time_window=60, 
        window_type=window_type
    ):
        duration = time.time() - start_time
        log_request(request_uuid, str(request.url.path), request.method, 429, duration)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    # Use read-through cache pattern for idempotency check
    existing_response = idempotency_service.get_response_with_read_through(
        idempotency_key,
        cache_enabled=request_body.cache_enabled,
        cache_ttl=request_body.cache_ttl
    )
    
    if existing_response:
        logger.info("duplicate_request_handled", idempotency_key=idempotency_key)
        return PostResponseModel(**existing_response)
    
    # Process new request
    payload_str = json.dumps(request_body.dict(), sort_keys=True)
    payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()
    
    request_metadata = Request(
        request_id=request_uuid,
        received_at=datetime.utcnow(),
        endpoint=str(request.url.path),
        method=request.method,
        payload_hash=payload_hash,
        idempotency_key=idempotency_key,
        status="received"
    )
    
    try:
        # Simulate database latency from request
        db_service.create(request_metadata)
        
        duration = time.time() - start_time
        request_metadata.latency_ms = int(duration * 1000)
        
        response_data = {
            "status": status.HTTP_200_OK,
            "status_message": "received",
            "request_id": request_uuid
        }
        
        # Cache the response with failure handling
        idempotency_service.cache_response(
            idempotency_key, 
            response_data,
            cache_enabled=request_body.cache_enabled,
            cache_ttl=request_body.cache_ttl
        )
        
        log_request(request_uuid, str(request.url.path), request.method, status.HTTP_200_OK, duration)
        return PostResponseModel(**response_data)
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error("request_failed", request_id=request_uuid, error=str(e))
        log_request(request_uuid, str(request.url.path), request.method, status.HTTP_500_INTERNAL_SERVER_ERROR, duration)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Request processing failed: {str(e)}"
        )