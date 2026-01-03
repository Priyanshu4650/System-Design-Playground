import json
from typing import Optional, Any, Callable
from v1.services.redis_service import redis_service
from v1.services.observability import logger
from prometheus_client import Counter, Histogram
import hashlib
import time

# Cache metrics
CACHE_HITS = Counter('cache_hits_total', 'Cache hits', ['cache_type'])
CACHE_MISSES = Counter('cache_misses_total', 'Cache misses', ['cache_type'])
CACHE_FAILURES = Counter('cache_failures_total', 'Cache operation failures', ['operation'])
CACHE_LATENCY = Histogram('cache_operation_duration_seconds', 'Cache operation latency')

class CacheService:
    def __init__(self):
        self.redis = redis_service
        self.default_ttl = 300  # 5 minutes
        logger.info("cache service initialized", default_ttl=self.default_ttl)
    
    def _generate_cache_key(self, prefix: str, identifier: str) -> str:
        """Generate consistent cache key"""
        return f"{prefix}:{hashlib.md5(identifier.encode()).hexdigest()}"
    
    def get(self, key: str, cache_type: str = "generic") -> Optional[Any]:
        """Get value from cache with metrics"""
        try:
            with CACHE_LATENCY.time():
                value = self.redis.get(key)
            
            if value is not None:
                CACHE_HITS.labels(cache_type=cache_type).inc()
                logger.debug("cache_hit", key=key, cache_type=cache_type)
                return json.loads(value) if isinstance(value, str) else value
            else:
                CACHE_MISSES.labels(cache_type=cache_type).inc()
                logger.debug("cache_miss", key=key, cache_type=cache_type)
                return None
                
        except Exception as e:
            CACHE_FAILURES.labels(operation="get").inc()
            logger.error("cache_get_failed", key=key, error=str(e))
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with failure handling"""
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            
            with CACHE_LATENCY.time():
                result = self.redis.set(key, serialized_value, ttl=ttl)
            
            logger.debug("cache_set", key=key, ttl=ttl)
            return result
            
        except Exception as e:
            CACHE_FAILURES.labels(operation="set").inc()
            logger.error("cache_set_failed", key=key, error=str(e))
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache (cache invalidation)"""
        try:
            with CACHE_LATENCY.time():
                result = self.redis.r.delete(key)
            
            logger.info("cache_invalidated", key=key)
            return bool(result)
            
        except Exception as e:
            CACHE_FAILURES.labels(operation="delete").inc()
            logger.error("cache_delete_failed", key=key, error=str(e))
            return False
    
    def read_through(self, key: str, fetch_function: Callable, ttl: int = None, 
                    cache_type: str = "read_through") -> Any:
        """Read-through cache pattern"""
        # Try cache first
        cached_value = self.get(key, cache_type)
        if cached_value is not None:
            return cached_value
        
        # Cache miss - fetch from source
        try:
            logger.debug("cache_read_through_fetch", key=key)
            value = fetch_function()
            
            # Cache the result (even if None, to prevent repeated calls)
            if value is not None:
                self.set(key, value, ttl)
            
            return value
            
        except Exception as e:
            logger.error("read_through_fetch_failed", key=key, error=str(e))
            raise
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate multiple keys matching pattern"""
        try:
            # Note: In production, use Redis SCAN for large datasets
            keys = self.redis.r.keys(pattern)
            if keys:
                deleted = self.redis.r.delete(*keys)
                logger.info("cache_pattern_invalidated", pattern=pattern, count=deleted)
                return deleted
            return 0
            
        except Exception as e:
            CACHE_FAILURES.labels(operation="invalidate_pattern").inc()
            logger.error("cache_pattern_invalidation_failed", pattern=pattern, error=str(e))
            return 0

cache_service = CacheService()