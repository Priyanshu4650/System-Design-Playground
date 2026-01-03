from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    REQUEST_RECEIVED = "request_received"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    RATE_LIMIT_CHECK = "rate_limit_check"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    CACHE_FAILURE = "cache_failure"
    DB_CALL_STARTED = "db_call_started"
    DB_CALL_COMPLETED = "db_call_completed"
    DB_CALL_FAILED = "db_call_failed"
    RETRY_ATTEMPTED = "retry_attempted"
    FAILURE_INJECTED = "failure_injected"
    RESPONSE_SENT = "response_sent"
    REQUEST_COMPLETED = "request_completed"

class TraceEvent(BaseModel):
    event_id: str
    request_id: str
    timestamp_monotonic: float  # time.monotonic()
    timestamp_wall: datetime    # datetime.utcnow()
    event_type: EventType
    metadata: Dict[str, Any] = {}
    
    class Config:
        use_enum_values = True

class RequestTrace(BaseModel):
    trace_id: str
    request_id: str
    original_request_id: Optional[str] = None  # For replays
    start_time: datetime
    end_time: Optional[datetime] = None
    total_latency_ms: Optional[float] = None
    status_code: Optional[int] = None
    events: List[TraceEvent] = []
    request_metadata: Dict[str, Any] = {}
    
class TraceReplayRequest(BaseModel):
    original_request_id: str
    replay_metadata: Dict[str, Any] = {}

class TraceResponse(BaseModel):
    trace: RequestTrace
    event_count: int
    failure_points: List[TraceEvent]
    retry_attempts: List[TraceEvent]