from typing import Optional, Dict, Any
from v1.services.database_service import db_service
from v1.services.cache_service import cache_service
from v1.services.observability import logger

class IdempotencyService:
    def __init__(self):
        self.cache = cache_service
        self.db = db_service
        logger.info("idempotency service initialized")

    def _get_cache_key(self, idempotency_key: str) -> str:
        """Generate cache key for idempotency"""
        return self.cache._generate_cache_key("idempotency", idempotency_key)

    def get_cached_response(self, idempotency_key: str, cache_enabled: bool = True) -> Optional[Dict[str, Any]]:
        """Check Redis cache for existing response"""
        if not cache_enabled:
            return None
        
        cache_key = self._get_cache_key(idempotency_key)
        cached_response = self.cache.get(cache_key, cache_type="idempotency")
        
        if cached_response:
            logger.info("request_served_from_cache", idempotency_key=idempotency_key)
            return cached_response
        return None
    
    def get_response_with_read_through(self, idempotency_key: str, cache_enabled: bool = True, 
                                     cache_ttl: int = 300) -> Optional[Dict[str, Any]]:
        """Get response using read-through cache pattern"""
        if not cache_enabled:
            # Direct database lookup if cache disabled
            existing_request = self.db.get_by_idempotency_key(idempotency_key)
            if existing_request:
                return {
                    "status": 200,
                    "status_message": "received",
                    "request_id": existing_request.request_id
                }
            return None
        
        cache_key = self._get_cache_key(idempotency_key)
        
        def fetch_from_db():
            """Fetch function for read-through cache"""
            existing_request = self.db.get_by_idempotency_key(idempotency_key)
            if existing_request:
                logger.info("request_served_from_database", idempotency_key=idempotency_key)
                return {
                    "status": 200,
                    "status_message": "received", 
                    "request_id": existing_request.request_id
                }
            return None
        
        return self.cache.read_through(
            key=cache_key,
            fetch_function=fetch_from_db,
            ttl=cache_ttl,
            cache_type="idempotency"
        )
    
    def cache_response(self, idempotency_key: str, response_data: Dict[str, Any], 
                      cache_enabled: bool = True, cache_ttl: int = 300):
        """Cache response data with failure handling"""
        if not cache_enabled:
            return
        
        cache_key = self._get_cache_key(idempotency_key)
        success = self.cache.set(cache_key, response_data, ttl=cache_ttl)
        
        if not success:
            logger.warning("failed_to_cache_response", idempotency_key=idempotency_key)
    
    def invalidate_response(self, idempotency_key: str) -> bool:
        """Invalidate cached response for specific idempotency key"""
        cache_key = self._get_cache_key(idempotency_key)
        return self.cache.delete(cache_key)
    
    def invalidate_all_responses(self) -> int:
        """Invalidate all cached idempotency responses"""
        pattern = "idempotency:*"
        return self.cache.invalidate_pattern(pattern)

idempotency_service = IdempotencyService()