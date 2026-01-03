from fastapi import APIRouter, HTTPException, status
from v1.services.cache_service import cache_service
from v1.services.idempotency_service_enhanced import idempotency_service
from v1.services.observability import logger
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/cache")

class CacheInvalidationRequest(BaseModel):
    key: Optional[str] = None
    pattern: Optional[str] = None
    idempotency_key: Optional[str] = None

class CacheInvalidationResponse(BaseModel):
    success: bool
    message: str
    keys_deleted: int = 0

@router.delete("/invalidate")
def invalidate_cache(request: CacheInvalidationRequest):
    """Invalidate cache entries"""
    
    if request.idempotency_key:
        # Invalidate specific idempotency response
        success = idempotency_service.invalid#ate_response(request.idempotency_key)
        return CacheInvalidationResponse(
            success=success,
            message=f"Idempotency key {'invalidated' if success else 'not found'}",
            keys_deleted=1 if success else 0
        )
    
    elif request.key:
        # Invalidate specific key
        success = cache_service.delete(request.key)
        return CacheInvalidationResponse(
            success=success,
            message=f"Key {'invalidated' if success else 'not found'}",
            keys_deleted=1 if success else 0
        )
    
    elif request.pattern:
        # Invalidate pattern
        deleted_count = cache_service.invalidate_pattern(request.pattern)
        return CacheInvalidationResponse(
            success=True,
            message=f"Pattern invalidated",
            keys_deleted=deleted_count
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide key, pattern, or idempotency_key"
        )

@router.delete("/invalidate/all")
def invalidate_all_cache():
    """Invalidate all cache entries (use with caution)"""
    deleted_count = cache_service.invalidate_pattern("*")
    logger.warning("cache_full_invalidation", keys_deleted=deleted_count)
    
    return CacheInvalidationResponse(
        success=True,
        message="All cache entries invalidated",
        keys_deleted=deleted_count
    )

@router.get("/stats")
def get_cache_stats():
    """Get cache statistics"""
    # This would require Redis INFO command in production
    return {
        "cache_service": "active",
        "default_ttl": cache_service.default_ttl,
        "message": "Check Prometheus metrics at /metrics for detailed stats"
    }