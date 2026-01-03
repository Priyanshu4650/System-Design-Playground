import redis
import json
import hashlib
from v1.services.observability import logger

class RedisService():
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, db=0)
        logger.info("redis_service_initialized")

    def hash_key(self, key):
        return hashlib.sha256(key.encode()).hexdigest()

    def get(self, key):
        hashed_key = self.hash_key(key)
        value = self.r.get(hashed_key)
        return json.loads(value) if value else None

    def set(self, key, value, ttl=30): 
        hashed_key = self.hash_key(key)
        self.r.setex(hashed_key, ttl, json.dumps(value))
        return True

redis_service = RedisService()
