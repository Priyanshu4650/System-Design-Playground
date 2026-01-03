import time
from v1.services.redis_service import redis_service
from v1.services.observability import logger

class RateLimitingService:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.redis = redis_service
        logger.info("rate_limiting_service_initialized")
    
    def is_allowed(self, request_id: str) -> bool:
        current_time = int(time.time())
        window_start = current_time - self.time_window
        
        redis_key = f"rate_limit:{window_start // self.time_window}"
        
        current_count = self.redis.get(redis_key)
        if current_count is None:
            current_count = 0
        else:
            current_count = int(current_count)
        
        if current_count >= self.max_requests:
            return False
        
        self.redis.set(redis_key, current_count + 1, ttl=self.time_window)
        return True

rate_limiting_service = RateLimitingService(max_requests=100, time_window=60)
