import asyncio
import random
import time
from functools import wraps
from typing import Callable, Type, Tuple
from config.failure_injection import config
from exceptions.retryable import RetryableException
from v1.services.observability import logger
from prometheus_client import Counter

RETRY_ATTEMPTS = Counter('retry_attempts_total', 'Total retry attempts', ['operation', 'attempt'])
FINAL_FAILURES = Counter('final_failures_total', 'Final failures after all retries', ['operation'])

def with_retry(retryable_exceptions: Tuple[Type[Exception], ...] = (RetryableException,)):
    """Decorator to add retry logic with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.MAX_RETRIES + 1):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info("retry_success", 
                                  operation=func.__name__, 
                                  attempt=attempt,
                                  total_attempts=attempt + 1)
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    if not isinstance(e, retryable_exceptions):
                        logger.error("non_retryable_failure", 
                                   operation=func.__name__, 
                                   error=str(e),
                                   error_type=type(e).__name__)
                        raise
                    
                    if attempt >= config.MAX_RETRIES:
                        break
                    
                    delay = min(
                        config.RETRY_BASE_DELAY * (2 ** attempt),
                        config.RETRY_MAX_DELAY
                    )
                    jitter = random.uniform(0, delay * 0.1)
                    total_delay = delay + jitter
                    
                    RETRY_ATTEMPTS.labels(operation=func.__name__, attempt=attempt + 1).inc()
                    
                    logger.warning("retry_attempt", 
                                 operation=func.__name__, 
                                 attempt=attempt + 1,
                                 delay_seconds=total_delay,
                                 error=str(e),
                                 error_type=type(e).__name__)
                    
                    await asyncio.sleep(total_delay)
            
            FINAL_FAILURES.labels(operation=func.__name__).inc()
            logger.error("retry_exhausted", 
                       operation=func.__name__, 
                       total_attempts=config.MAX_RETRIES + 1,
                       final_error=str(last_exception))
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.MAX_RETRIES + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info("retry_success", 
                                  operation=func.__name__, 
                                  attempt=attempt,
                                  total_attempts=attempt + 1)
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    if not isinstance(e, retryable_exceptions):
                        logger.error("non_retryable_failure", 
                                   operation=func.__name__, 
                                   error=str(e),
                                   error_type=type(e).__name__)
                        raise
                    
                    if attempt >= config.MAX_RETRIES:
                        break
                    
                    delay = min(
                        config.RETRY_BASE_DELAY * (2 ** attempt),
                        config.RETRY_MAX_DELAY
                    )
                    jitter = random.uniform(0, delay * 0.1)
                    total_delay = delay + jitter
                    
                    RETRY_ATTEMPTS.labels(operation=func.__name__, attempt=attempt + 1).inc()
                    
                    logger.warning("retry_attempt", 
                                 operation=func.__name__, 
                                 attempt=attempt + 1,
                                 delay_seconds=total_delay,
                                 error=str(e),
                                 error_type=type(e).__name__)
                    
                    time.sleep(total_delay)
            
            FINAL_FAILURES.labels(operation=func.__name__).inc()
            logger.error("retry_exhausted", 
                       operation=func.__name__, 
                       total_attempts=config.MAX_RETRIES + 1,
                       final_error=str(last_exception))
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator