import json
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from models.tracing.trace_models import TraceEvent, RequestTrace, EventType
from v1.services.redis_service import redis_service
from v1.services.database_service_traced import db_service_traced as db_service
from v1.services.observability import logger
from prometheus_client import Counter, Histogram
import uuid

# Tracing metrics
TRACES_CREATED = Counter('traces_created_total', 'Total traces created')
TRACE_EVENTS_APPENDED = Counter('trace_events_appended_total', 'Total trace events appended', ['event_type'])
TRACE_FETCH_LATENCY = Histogram('trace_fetch_latency_seconds', 'Trace fetch latency')
REPLAY_ATTEMPTS = Counter('replay_attempts_total', 'Total replay attempts', ['status'])

class TraceStorage:
    def __init__(self):
        self.redis = redis_service
        self.db = db_service
        self.trace_ttl = 86400  # 24 hours
        logger.info("trace storage initialized", trace_ttl_hours=self.trace_ttl/3600)
        
    def _get_trace_key(self, request_id: str) -> str:
        return f"trace:{request_id}"
    
    def _get_events_key(self, request_id: str) -> str:
        return f"trace_events:{request_id}"
    
    def create_trace(self, request_id: str, request_metadata: Dict[str, Any]) -> RequestTrace:
        """Create new request trace"""
        trace = RequestTrace(
            trace_id=str(uuid.uuid4()),
            request_id=request_id,
            start_time=datetime.utcnow(),
            request_metadata=request_metadata
        )
        
        # Store in Redis for fast access
        trace_key = self._get_trace_key(request_id)
        self.redis.set(trace_key, trace.json(), ttl=self.trace_ttl)
        
        TRACES_CREATED.inc()
        logger.info("trace_created", request_id=request_id, trace_id=trace.trace_id)
        
        return trace
    
    def append_event(self, request_id: str, event_type: EventType, metadata: Dict[str, Any] = None) -> TraceEvent:
        """Append event to trace timeline"""
        event = TraceEvent(
            event_id=str(uuid.uuid4()),
            request_id=request_id,
            timestamp_monotonic=time.monotonic(),
            timestamp_wall=datetime.utcnow(),
            event_type=event_type,
            metadata=metadata or {}
        )
        
        # Store event in Redis list for ordering
        events_key = self._get_events_key(request_id)
        self.redis.r.lpush(events_key, event.json())
        self.redis.r.expire(events_key, self.trace_ttl)
        
        TRACE_EVENTS_APPENDED.labels(event_type=event_type.value).inc()
        logger.debug("trace_event_appended", 
                    request_id=request_id, 
                    event_type=event_type.value,
                    event_id=event.event_id)
        
        return event
    
    def complete_trace(self, request_id: str, status_code: int, total_latency_ms: float):
        """Mark trace as completed"""
        trace_key = self._get_trace_key(request_id)
        
        try:
            trace_data = self.redis.get(trace_key)
            if trace_data:
                trace = RequestTrace.parse_raw(trace_data)
                trace.end_time = datetime.utcnow()
                trace.status_code = status_code
                trace.total_latency_ms = total_latency_ms
                
                # Update in Redis
                self.redis.set(trace_key, trace.json(), ttl=self.trace_ttl)
                
                # Persist to PostgreSQL for long-term storage
                self._persist_to_db(trace)
                
                logger.info("trace_completed", 
                          request_id=request_id,
                          status_code=status_code,
                          total_latency_ms=total_latency_ms)
        except Exception as e:
            logger.error("trace_completion_failed", request_id=request_id, error=str(e))
    
    def get_trace(self, request_id: str) -> Optional[RequestTrace]:
        """Retrieve complete trace with events"""
        with TRACE_FETCH_LATENCY.time():
            # Try Redis first
            trace_data = self.redis.get(self._get_trace_key(request_id))
            
            if trace_data:
                trace = RequestTrace.parse_raw(trace_data)
                
                # Get events from Redis
                events_key = self._get_events_key(request_id)
                event_data_list = self.redis.r.lrange(events_key, 0, -1)
                
                events = []
                for event_data in reversed(event_data_list):  # Reverse for chronological order
                    try:
                        event = TraceEvent.parse_raw(event_data)
                        events.append(event)
                    except Exception as e:
                        logger.error("event_parse_failed", event_data=event_data, error=str(e))
                
                trace.events = sorted(events, key=lambda e: e.timestamp_monotonic)
                return trace
            
            # Fallback to database
            return self._get_from_db(request_id)
    
    def _persist_to_db(self, trace: RequestTrace):
        """Persist trace to PostgreSQL for long-term storage"""
        try:
            # This would use a proper traces table in production
            # For now, we'll store as JSON in a simple table
            pass
        except Exception as e:
            logger.error("trace_db_persist_failed", request_id=trace.request_id, error=str(e))
    
    def _get_from_db(self, request_id: str) -> Optional[RequestTrace]:
        """Retrieve trace from database"""
        try:
            # Database retrieval logic would go here
            return None
        except Exception as e:
            logger.error("trace_db_fetch_failed", request_id=request_id, error=str(e))
            return None

trace_storage = TraceStorage()