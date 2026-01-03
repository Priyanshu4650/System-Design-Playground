from fastapi import APIRouter, HTTPException, status
from typing import List
from models.tracing.trace_models import TraceResponse, TraceReplayRequest, EventType
from tracing.trace_storage import trace_storage
from tracing.trace_context import TraceContext
from v1.services.observability import logger
from prometheus_client import Counter, CollectorRegistry, REGISTRY
import uuid

router = APIRouter(prefix="/v1/trace")

# Prevent duplicate metric registration
try:
    REPLAY_ATTEMPTS = Counter('replay_attempts_total', 'Total replay attempts', ['status'])
except ValueError:
    # Metric already exists, get it from registry
    for collector in REGISTRY._collector_to_names:
        if hasattr(collector, '_name') and collector._name == 'replay_attempts_total':
            REPLAY_ATTEMPTS = collector
            break

@router.get("/{request_id}", response_model=TraceResponse)
async def get_trace(request_id: str):
    """Get complete trace for a request"""
    trace = trace_storage.get_trace(request_id)
    
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace not found for request_id: {request_id}"
        )
    
    # Identify failure points and retry attempts
    failure_points = [
        event for event in trace.events 
        if event.event_type in [
            EventType.VALIDATION_FAILED,
            EventType.RATE_LIMIT_EXCEEDED,
            EventType.DB_CALL_FAILED,
            EventType.CACHE_FAILURE,
            EventType.FAILURE_INJECTED
        ]
    ]
    
    retry_attempts = [
        event for event in trace.events 
        if event.event_type == EventType.RETRY_ATTEMPTED
    ]
    
    return TraceResponse(
        trace=trace,
        event_count=len(trace.events),
        failure_points=failure_points,
        retry_attempts=retry_attempts
    )

@router.post("/{request_id}/replay")
async def replay_request(request_id: str, replay_request: TraceReplayRequest):
    """Replay a request with new request_id"""
    
    # Get original trace
    original_trace = trace_storage.get_trace(request_id)
    if not original_trace:
        REPLAY_ATTEMPTS.labels(status="not_found").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Original trace not found for request_id: {request_id}"
        )
    
    # Generate new request ID for replay
    new_request_id = str(uuid.uuid4())
    
    try:
        # Create new trace linked to original
        replay_metadata = {
            **original_trace.request_metadata,
            "is_replay": True,
            "original_request_id": request_id,
            "replay_metadata": replay_request.replay_metadata
        }
        
        # Start new trace context
        with TraceContext(new_request_id, replay_metadata):
            TraceContext.trace_event(
                EventType.REQUEST_RECEIVED,
                {
                    "replay_of": request_id,
                    "original_trace_id": original_trace.trace_id
                }
            )
            
            # Here you would re-execute the original request logic
            # For now, we'll just create a placeholder trace
            
            TraceContext.trace_event(
                EventType.RESPONSE_SENT,
                {"status_code": 200, "replayed": True}
            )
            
            trace_storage.complete_trace(new_request_id, 200, 0)
        
        REPLAY_ATTEMPTS.labels(status="success").inc()
        logger.info("request_replayed", 
                   original_request_id=request_id,
                   new_request_id=new_request_id)
        
        return {
            "success": True,
            "new_request_id": new_request_id,
            "original_request_id": request_id,
            "message": "Request replayed successfully"
        }
        
    except Exception as e:
        REPLAY_ATTEMPTS.labels(status="failed").inc()
        logger.error("request_replay_failed", 
                    original_request_id=request_id,
                    error=str(e))
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Replay failed: {str(e)}"
        )

@router.get("/{request_id}/timeline")
async def get_trace_timeline(request_id: str):
    """Get simplified timeline view of trace events"""
    trace = trace_storage.get_trace(request_id)
    
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace not found for request_id: {request_id}"
        )
    
    timeline = []
    for event in trace.events:
        timeline.append({
            "timestamp": event.timestamp_wall.isoformat(),
            "event_type": event.event_type,
            "metadata": event.metadata
        })
    
    return {
        "request_id": request_id,
        "total_events": len(timeline),
        "total_latency_ms": trace.total_latency_ms,
        "status_code": trace.status_code,
        "timeline": timeline
    }