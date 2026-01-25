from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TestMode(str, Enum):
    TOTAL_REQUESTS = "total_requests"
    RPS_DURATION = "rps_duration"

class PayloadStrategy(str, Enum):
    FIXED = "fixed"
    RANDOMIZED = "randomized"

class TestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class FailureInjectionConfig(BaseModel):
    enabled: bool = False
    failure_rate: float = Field(0.0, ge=0.0, le=100.0)  # Allow 0-100 percentage
    latency_min_ms: int = Field(0, ge=0)
    latency_max_ms: int = Field(0, ge=0)
    timeout_seconds: float = Field(5.0, gt=0)

class LoadTestConfig(BaseModel):
    # Test parameters
    total_requests: Optional[int] = Field(None, gt=0)
    rps: Optional[int] = Field(None, gt=0)
    duration: Optional[int] = Field(None, gt=0)  # Changed from duration to match frontend
    
    # Execution settings
    burst_mode: bool = False
    concurrency_limit: int = Field(10, gt=0, le=1000)
    
    # Payload settings
    payload_strategy: PayloadStrategy = PayloadStrategy.FIXED
    base_payload: Dict[str, Any]
    
    # Feature toggles
    retries_enabled: bool = True
    idempotency_enabled: bool = True
    
    # Failure injection
    failure_injection: Optional[FailureInjectionConfig] = None

class LoadTestRequest(BaseModel):
    config: LoadTestConfig

class LoadTestResult(BaseModel):
    test_id: str
    status: TestStatus
    total_requests: int
    succeeded: int
    failed: int
    rate_limited: int
    duplicates: int
    retries_total: int
    avg_latency_ms: Optional[float]
    p95_latency_ms: Optional[float]
    p99_latency_ms: Optional[float]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_sec: Optional[float]

class LoadTestStatus(BaseModel):
    test_id: str
    status: TestStatus
    progress: Optional[Dict[str, Any]] = None