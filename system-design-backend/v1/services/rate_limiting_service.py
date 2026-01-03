import time
from enum import Enum
from v1.services.redis_service import redis_service
from v1.services.observability import logger

class WindowType(Enum):
    FIXED = "fixed"
    SLIDING = "sliding"

class RateLimitingService:
    def __init__(self):
        self.redis = redis_service
        logger.info("rate limiting service initialized")
    
    def is_allowed(self, client_id: str, max_requests: int, time_window: int, 
                   window_type: WindowType = WindowType.FIXED) -> bool:
        if window_type == WindowType.FIXED:
            return self._fixed_window_check(client_id, max_requests, time_window)
        else:
            return self._sliding_window_check(client_id, max_requests, time_window)
    
    def _fixed_window_check(self, client_id: str, max_requests: int, time_window: int) -> bool:
        current_time = int(time.time())
        window_start = (current_time // time_window) * time_window
        redis_key = f"rate_limit:fixed:{client_id}:{window_start}"
        
        current_count = self.redis.get(redis_key) or 0
        current_count = int(current_count) if current_count else 0
        
        if current_count >= max_requests:
            logger.warning("rate_limit_exceeded", client_id=client_id, window="fixed")
            return False
        
        self.redis.set(redis_key, current_count + 1, ttl=time_window)
        return True
    
    def _sliding_window_check(self, client_id: str, max_requests: int, time_window: int) -> bool:
        current_time = time.time()
        redis_key = f"rate_limit:sliding:{client_id}"
        
        # Remove old entries
        cutoff_time = current_time - time_window
        
        # Get current requests in window (simplified - use sorted sets in production)
        requests_str = self.redis.get(redis_key) or "[]"
        import json
        requests = json.loads(requests_str)
        
        # Filter recent requests
        recent_requests = [req for req in requests if req > cutoff_time]
        
        if len(recent_requests) >= max_requests:
            logger.warning("rate_limit_exceeded", client_id=client_id, window="sliding")
            return False
        
        # Add current request
        recent_requests.append(current_time)
        self.redis.set(redis_key, json.dumps(recent_requests), ttl=time_window)
        return True

rate_limiting_service = RateLimitingService()
