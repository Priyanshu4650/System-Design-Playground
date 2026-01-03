import contextvars
from typing import Optional, Dict, Any
from models.tracing.trace_models import EventType
from tracing.trace_storage import trace_storage

# Context variable for request tracing
_request_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('request_id', default=None)

class TraceContext:
    """Context manager for request tracing"""
    
    @classmethod
    def get_request_id(cls) -> Optional[str]:
        """Get current request ID from context"""
        return _request_context.get()
    
    @classmethod
    def set_request_id(cls, request_id: str):
        """Set request ID in context"""
        _request_context.set(request_id)
    
    @classmethod
    def trace_event(cls, event_type: EventType, metadata: Dict[str, Any] = None):
        """Add event to current trace"""
        request_id = cls.get_request_id()
        if request_id:
            trace_storage.append_event(request_id, event_type, metadata)
    
    def __init__(self, request_id: str, request_metadata: Dict[str, Any] = None):
        self.request_id = request_id
        self.request_metadata = request_metadata or {}
        self.token = None
    
    def __enter__(self):
        # Set context and create trace
        self.token = _request_context.set(self.request_id)
        trace_storage.create_trace(self.request_id, self.request_metadata)
        trace_storage.append_event(self.request_id, EventType.REQUEST_RECEIVED, self.request_metadata)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Complete trace
        if exc_type:
            trace_storage.append_event(
                self.request_id, 
                EventType.REQUEST_COMPLETED,
                {"error": str(exc_val), "error_type": exc_type.__name__}
            )
        
        # Reset context
        if self.token:
            _request_context.reset(self.token)