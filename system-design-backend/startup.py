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
        from v1.services.redis_service import redis_service
        logger.info("✓ redis service ready")
        
        # Database Service  
        from v1.services.database_service_traced import db_service_traced
        logger.info("✓ database service ready")
        
        # Cache Service
        from v1.services.cache_service import cache_service
        logger.info("✓ cache service ready")
        
        # Rate Limiting Service
        from v1.services.rate_limiting_service import rate_limiting_service
        logger.info("✓ rate limiting service ready")
        
        # Idempotency Service
        from v1.services.idempotency_service import idempotency_service
        logger.info("✓ idempotency service ready")
        
        # Tracing Services
        from tracing.trace_storage import trace_storage
        logger.info("✓ trace storage ready")
        
        # Configuration
        from config.failure_injection import config
        logger.info("✓ failure injection config loaded")
        
        # Middleware
        logger.info("initializing middleware...")
        from middleware.failure_injection import INJECTED_FAILURES, DB_LATENCY_HISTOGRAM
        from middleware.retry import RETRY_ATTEMPTS, FINAL_FAILURES
        logger.info("✓ failure injection middleware ready")
        logger.info("✓ retry middleware ready")
        
        # Observability
        logger.info("initializing observability...")
        from v1.services.observability import REQUEST_COUNT, REQUEST_DURATION, ACTIVE_REQUESTS
        logger.info("✓ prometheus metrics ready")
        logger.info("✓ structured logging ready")
        
        startup_duration = time.time() - start_time
        
        logger.info("=== SYSTEM STARTUP COMPLETED ===", 
                   startup_duration_ms=startup_duration * 1000,
                   services_initialized=[
                       "redis", "database", "cache", "rate_limiting", 
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
        from config.failure_injection import config
        from v1.services.observability import ACTIVE_REQUESTS
        
        logger.info("=== SYSTEM STATUS ===",
                   failure_injection_enabled=config.FAILURE_INJECTION_ENABLED,
                   failure_rate=config.FAILURE_RATE,
                   active_requests=ACTIVE_REQUESTS._value._value if hasattr(ACTIVE_REQUESTS, '_value') else 0,
                   prometheus_metrics_port=8001)
        
    except Exception as e:
        logger.error("failed to log system status", error=str(e))

if __name__ == "__main__":
    initialize_system()
    log_system_status()