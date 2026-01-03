from fastapi import APIRouter, Request as FastAPIRequest, status, HTTPException
from v1.routes.schema import PostRequestModel, PostResponseModel
import uuid
import time
from datetime import datetime
import hashlib
import json
from typing import List, Optional
from v1.services.database_service_traced import db_service_traced as db_service
from v1.services.idempotency_service import idempotency_service
from v1.services.cache_service import cache_service
from v1.models.request import Request
from v1.services.observability import logger, log_request_with_metrics, ACTIVE_REQUESTS
from v1.services.rate_limiting_service import rate_limiting_service, WindowType
from tracing.trace_context import TraceContext
from models.tracing.trace_models import EventType
from config.failure_injection import config as failure_config
from pydantic import BaseModel
import asyncio

router = APIRouter(prefix="/requests")

@router.post("/")
async def post_request(request_body: PostRequestModel, request: FastAPIRequest):
    request_uuid = str(uuid.uuid4())
    start_time = time.time()
    
    # Extract request metadata for tracing
    request_metadata_trace = {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "idempotency_key": request.headers.get("idempotency-key")
    }
    
    ACTIVE_REQUESTS.inc()
    
    # Start tracing context
    with TraceContext(request_uuid, request_metadata_trace):
        try:
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
                log_request_with_metrics(request_uuid, str(request.url.path), request.method, 429, duration)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            # Enhanced caching with read-through pattern and tracing
            existing_response = idempotency_service.get_response_with_read_through(
                idempotency_key,
                cache_enabled=request_body.cache_enabled,
                cache_ttl=request_body.cache_ttl
            )
            
            if existing_response:
                if request_body.cache_enabled:
                    TraceContext.trace_event(EventType.CACHE_HIT, {"key": idempotency_key})
                else:
                    TraceContext.trace_event(EventType.CACHE_MISS, {"key": idempotency_key, "reason": "cache_disabled"})
                return PostResponseModel(**existing_response)
            else:
                TraceContext.trace_event(EventType.CACHE_MISS, {"key": idempotency_key})
            
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
            
            # Database operations with automatic tracing via decorators
            db_service.create(request_metadata, request_id=request_uuid)
            
            duration = time.time() - start_time
            request_metadata.latency_ms = int(duration * 1000)
            
            response_data = {
                "status": status.HTTP_200_OK,
                "status_message": "received",
                "request_id": request_uuid
            }
            
            # Cache with enhanced failure handling
            idempotency_service.cache_response(
                idempotency_key, 
                response_data,
                cache_enabled=request_body.cache_enabled,
                cache_ttl=request_body.cache_ttl
            )
            
            TraceContext.trace_event(
                EventType.RESPONSE_SENT,
                {"status_code": 200, "latency_ms": duration * 1000}
            )
            
            log_request_with_metrics(request_uuid, str(request.url.path), request.method, status.HTTP_200_OK, duration)
            return PostResponseModel(**response_data)
            
        except HTTPException:
            # Re-raise HTTP exceptions (like 400, 429)
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error("request_failed", request_id=request_uuid, error=str(e))
            log_request_with_metrics(request_uuid, str(request.url.path), request.method, status.HTTP_500_INTERNAL_SERVER_ERROR, duration)
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Request processing failed: {str(e)}"
            )
        finally:
            ACTIVE_REQUESTS.dec()

# Models
class TrafficRequest(BaseModel):
    mode: str  # 'single', 'burst', 'sustained'
    count: Optional[int] = None
    rps: Optional[int] = None
    duration: Optional[int] = None
    payload: PostRequestModel

class TrafficResult(BaseModel):
    request_id: str
    status: str
    latency_ms: float
    timestamp: str

class FailureConfigModel(BaseModel):
    failure_injection_enabled: bool
    failure_rate: float
    db_latency_min_ms: int
    db_latency_max_ms: int
    db_timeout_seconds: float
    redis_timeout_seconds: float
    max_retries: int

# Traffic generation routes
@router.post("/generate")
async def generate_traffic(traffic_request: TrafficRequest):
    """Generate traffic for testing"""
    results = []
    
    if traffic_request.mode == "single":
        result = await _execute_single_request(traffic_request.payload)
        results.append(result)
        
    elif traffic_request.mode == "burst":
        tasks = []
        for _ in range(traffic_request.count or 10):
            task = _execute_single_request(traffic_request.payload)
            tasks.append(task)
        
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        # Filter out exceptions and convert to proper results
        for result in raw_results:
            if isinstance(result, Exception):
                results.append(TrafficResult(
                    request_id=str(uuid.uuid4()),
                    status="failure",
                    latency_ms=0.0,
                    timestamp=datetime.utcnow().isoformat()
                ))
            else:
                results.append(result)
        
    elif traffic_request.mode == "sustained":
        rps = traffic_request.rps or 5
        duration = traffic_request.duration or 30
        interval = 1.0 / rps
        
        end_time = time.time() + duration
        while time.time() < end_time:
            result = await _execute_single_request(traffic_request.payload)
            results.append(result)
            await asyncio.sleep(interval)
    
    return {"results": results, "count": len(results)}

async def _execute_single_request(payload: PostRequestModel) -> TrafficResult:
    """Execute a real HTTP request to the system"""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        # Make actual HTTP request to our own endpoint
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/requests/",
                json=payload.dict(),
                headers={"Idempotency-Key": request_id}
            )
            
        duration = (time.time() - start_time) * 1000
        return TrafficResult(
            request_id=request_id,
            status="success" if response.status_code < 400 else "failure",
            latency_ms=duration,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        return TrafficResult(
            request_id=request_id,
            status="failure",
            latency_ms=duration,
            timestamp=datetime.utcnow().isoformat()
        )

# Configuration routes
@router.get("/recent")
async def get_recent_requests(limit: int = 50):
    """Get recent requests from actual database"""
    try:
        # Query actual database for recent requests
        recent_requests = db_service.get_recent_requests(limit)
        return [{
            "request_id": req.request_id,
            "status": 200,  # Default success status
            "latency_ms": req.latency_ms or 0,
            "retry_count": 0,  # Would need to track retries
            "timestamp": req.received_at.isoformat(),
            "endpoint": req.endpoint,
            "method": req.method
        } for req in recent_requests]
    except Exception as e:
        logger.error("failed_to_get_recent_requests", error=str(e))
        return []