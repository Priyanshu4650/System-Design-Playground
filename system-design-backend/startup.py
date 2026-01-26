"""
System startup initialization with comprehensive logging
"""
import time
from v1.services.observability import logger

def initialize_system():
    """Initialize all system components with logging"""
    start_time = time.time()
    
    logger.info("=== SYSTEM STARTUP INITIATED ===")
    
    try:
        # Initialize core services
        logger.info("initializing core services...")
        
        # Redis Service
        try:
            from v1.services.redis_service import redis_service
            if redis_service.connected:
                logger.info("✓ redis service ready")
            else:
                logger.warning("⚠ redis service unavailable, running without cache")
        except Exception as e:
            logger.warning("⚠ redis service failed to initialize, running without cache", error=str(e))
        
        # Database Service  
        from v1.services.database_service_traced import db_service_traced
        logger.info("✓ database service ready")
        
        # Cache Service
        # from v1.services.cache_service import cache_service
        # logger.info("✓ cache service ready")
        
        # Rate Limiting Service
        try:
            from v1.services.rate_limiting_service import rate_limiting_service
            logger.info("✓ rate limiting service ready")
        except Exception as e:
            logger.warning("⚠ rate limiting service failed, running without rate limiting", error=str(e))
        
        # Idempotency Service
        try:
            from v1.services.idempotency_service import idempotency_service
            logger.info("✓ idempotency service ready")
        except Exception as e:
            logger.warning("⚠ idempotency service failed, running without idempotency", error=str(e))
        
        # Tracing Services
        try:
            from tracing.trace_storage import trace_storage
            logger.info("✓ trace storage ready")
        except Exception as e:
            logger.warning("⚠ trace storage failed, running without tracing", error=str(e))
        
        # Configuration
        try:
            from config.failure_injection import config
            logger.info("✓ failure injection config loaded")
        except Exception as e:
            logger.warning("⚠ failure injection config failed, running without failure injection", error=str(e))
        
        # Middleware
        logger.info("initializing middleware...")
        try:
            from middleware.failure_injection import INJECTED_FAILURES, DB_LATENCY_HISTOGRAM
            from middleware.retry import RETRY_ATTEMPTS, FINAL_FAILURES
            logger.info("✓ failure injection middleware ready")
            logger.info("✓ retry middleware ready")
        except Exception as e:
            logger.warning("⚠ middleware failed, running without middleware", error=str(e))
        
        # Observability
        logger.info("initializing observability...")
        try:
            from v1.services.observability import REQUEST_COUNT, REQUEST_DURATION, ACTIVE_REQUESTS
            logger.info("✓ prometheus metrics ready")
        except Exception as e:
            logger.warning("⚠ prometheus metrics failed, running without metrics", error=str(e))
        logger.info("✓ structured logging ready")
        
        startup_duration = time.time() - start_time
        
        logger.info("=== SYSTEM STARTUP COMPLETED ===", 
                   startup_duration_ms=startup_duration * 1000,
                   services_initialized=[
                       "redis", "database", "rate_limiting", 
                       "idempotency", "tracing", "failure_injection",
                       "retry", "observability"
                   ])
        
        return True
        
    except Exception as e:
        startup_duration = time.time() - start_time
        logger.error("=== SYSTEM STARTUP FAILED ===", 
                    error=str(e),
                    startup_duration_ms=startup_duration * 1000)
        raise

def log_system_status():
    """Log current system status"""
    try:
        logger.info("=== SYSTEM STATUS ===", status="ready")
    except Exception as e:
        logger.error("failed to log system status", error=str(e))

if __name__ == "__main__":
    initialize_system()
    log_system_status()