import os
from v1.services.observability import logger

class FailureInjectionConfig:
    def __init__(self):
        # Artificial DB latency
        self.DB_LATENCY_MIN_MS: int = int(os.getenv("DB_LATENCY_MIN_MS", "0"))
        self.DB_LATENCY_MAX_MS: int = int(os.getenv("DB_LATENCY_MAX_MS", "0"))
        
        # Random failure injection
        self.FAILURE_RATE: float = float(os.getenv("FAILURE_RATE", "0.0"))
        self.FAILURE_INJECTION_ENABLED: bool = os.getenv("FAILURE_INJECTION_ENABLED", "false").lower() == "true"
        
        # Timeout configuration
        self.DB_TIMEOUT_SECONDS: float = float(os.getenv("DB_TIMEOUT_SECONDS", "5.0"))
        self.REDIS_TIMEOUT_SECONDS: float = float(os.getenv("REDIS_TIMEOUT_SECONDS", "2.0"))
        
        # Retry configuration
        self.MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
        self.RETRY_BASE_DELAY: float = float(os.getenv("RETRY_BASE_DELAY", "0.1"))
        self.RETRY_MAX_DELAY: float = float(os.getenv("RETRY_MAX_DELAY", "10.0"))
        
        logger.info("failure injection config loaded", 
                   enabled=self.FAILURE_INJECTION_ENABLED,
                   failure_rate=self.FAILURE_RATE,
                   db_latency_range=f"{self.DB_LATENCY_MIN_MS}-{self.DB_LATENCY_MAX_MS}ms",
                   max_retries=self.MAX_RETRIES)

config = FailureInjectionConfig()