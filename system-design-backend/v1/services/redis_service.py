import redis
import json
import hashlib
import os
from v1.services.observability import logger

class RedisService():
    def __init__(self):
        self.r = None
        self.connected = False
        
        # Get Redis URL from environment or use default
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        try:
            self.r = redis.from_url(redis_url)
            # Test connection
            self.r.ping()
            self.connected = True
            logger.info("redis service initialized", redis_url=redis_url)
        except Exception as e:
            logger.warning("redis connection failed, running without cache", error=str(e))
            self.connected = False

    def hash_key(self, key):
        return hashlib.sha256(key.encode()).hexdigest()

    def get(self, key):
        if not self.connected:
            return None
        try:
            hashed_key = self.hash_key(key)
            value = self.r.get(hashed_key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning("redis get failed", error=str(e))
            return None

    def set(self, key, value, ttl=30): 
        if not self.connected:
            return False
        try:
            hashed_key = self.hash_key(key)
            self.r.setex(hashed_key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.warning("redis set failed", error=str(e))
            return False

redis_service = RedisService()
