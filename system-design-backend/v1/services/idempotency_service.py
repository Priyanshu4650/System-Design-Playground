from typing import Optional, Dict, Any
from v1.services.redis_service import redis_service
from v1.services.database_service import db_service
from v1.services.observability import logger

class IdempotencyService:
    def __init__(self):
        self.redis = redis_service
        self.db = db_service
    
    def get_cached_response(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Check Redis cache for existing response"""
        cached_response = self.redis.get(idempotency_key)
        if cached_response:
            logger.info("request_served_from_cache", idempotency_key=idempotency_key)
            return cached_response
        return None
    
    def get_database_response(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Check database for existing request and cache result"""
        existing_request = self.db.get_by_idempotency_key(idempotency_key)
        if existing_request:
            response_data = {
                "status": 200,
                "status_message": "received",
                "request_id": existing_request.request_id
            }
            self.redis.set(idempotency_key, response_data)
            logger.info("request_served_from_database", idempotency_key=idempotency_key)
            return response_data
        return None
    
    def cache_response(self, idempotency_key: str, response_data: Dict[str, Any]):
        """Cache response data"""
        self.redis.set(idempotency_key, response_data)

idempotency_service = IdempotencyService()
