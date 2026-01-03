from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from config.failure_injection import config as failure_config
from v1.services.observability import logger

router = APIRouter(prefix="/v1/config")

class FailureConfigModel(BaseModel):
    failure_injection_enabled: bool
    failure_rate: float
    db_latency_min_ms: int
    db_latency_max_ms: int
    db_timeout_seconds: float
    redis_timeout_seconds: float
    max_retries: int

@router.get("/failure")
async def get_failure_config():
    """Get current failure injection configuration"""
    return {
        "failure_injection_enabled": failure_config.FAILURE_INJECTION_ENABLED,
        "failure_rate": failure_config.FAILURE_RATE,
        "db_latency_min_ms": failure_config.DB_LATENCY_MIN_MS,
        "db_latency_max_ms": failure_config.DB_LATENCY_MAX_MS,
        "db_timeout_seconds": failure_config.DB_TIMEOUT_SECONDS,
        "redis_timeout_seconds": failure_config.REDIS_TIMEOUT_SECONDS,
        "max_retries": failure_config.MAX_RETRIES
    }

@router.put("/failure")
async def update_failure_config(config_update: dict):
    """Update failure injection configuration with runtime propagation"""
    try:
        # Get current config and update only provided fields
        current_config = {
            "failure_injection_enabled": failure_config.FAILURE_INJECTION_ENABLED,
            "failure_rate": failure_config.FAILURE_RATE,
            "db_latency_min_ms": failure_config.DB_LATENCY_MIN_MS,
            "db_latency_max_ms": failure_config.DB_LATENCY_MAX_MS,
            "db_timeout_seconds": failure_config.DB_TIMEOUT_SECONDS,
            "redis_timeout_seconds": failure_config.REDIS_TIMEOUT_SECONDS,
            "max_retries": failure_config.MAX_RETRIES
        }
        
        # Update with provided values
        current_config.update(config_update)
        
        # Validate the complete config
        validated_config = FailureConfigModel(**current_config)
        
        # Update runtime configuration
        failure_config.FAILURE_INJECTION_ENABLED = validated_config.failure_injection_enabled
        failure_config.FAILURE_RATE = validated_config.failure_rate
        failure_config.DB_LATENCY_MIN_MS = validated_config.db_latency_min_ms
        failure_config.DB_LATENCY_MAX_MS = validated_config.db_latency_max_ms
        failure_config.DB_TIMEOUT_SECONDS = validated_config.db_timeout_seconds
        failure_config.REDIS_TIMEOUT_SECONDS = validated_config.redis_timeout_seconds
        failure_config.MAX_RETRIES = validated_config.max_retries
        
        logger.info("failure_config_updated_runtime", 
                   enabled=validated_config.failure_injection_enabled,
                   failure_rate=validated_config.failure_rate)
        
        return validated_config.dict()
        
    except Exception as e:
        logger.error("config_update_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid configuration: {str(e)}"
        )