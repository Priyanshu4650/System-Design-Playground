import asyncio
import uuid
import time
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
from statistics import mean, quantiles
from sqlalchemy import text

from v1.models.load_test import LoadTestConfig, TestStatus, PayloadStrategy
from v1.routes.schema import PostRequestModel
from v1.services.database_service_traced import db_service_traced as db_service
from v1.services.observability import logger
from tracing.trace_context import TraceContext
from models.tracing.trace_models import EventType
from prometheus_client import Counter, Histogram, Gauge

# Load test metrics
TESTS_STARTED = Counter('load_tests_started_total', 'Total load tests started')
TESTS_COMPLETED = Counter('load_tests_completed_total', 'Total load tests completed', ['status'])
TEST_DURATION = Histogram('load_test_duration_seconds', 'Load test duration')
TEST_REQUEST_SUCCESS = Counter('load_test_requests_success_total', 'Successful load test requests')
TEST_REQUEST_FAILED = Counter('load_test_requests_failed_total', 'Failed load test requests')
ACTIVE_LOAD_TESTS = Gauge('active_load_tests', 'Currently running load tests')

class LoadTestService:
    def __init__(self):
        self.active_tests: Dict[str, asyncio.Task] = {}
        self.test_results: Dict[str, Dict[str, Any]] = {}
        
    async def start_test(self, config: LoadTestConfig) -> str:
        """Start a new load test and return test_id"""
        test_id = str(uuid.uuid4())
        
        # Store test configuration in database
        await self._create_test_record(test_id, config)
        
        # Start test execution in background
        task = asyncio.create_task(self._execute_test(test_id, config))
        self.active_tests[test_id] = task
        
        TESTS_STARTED.inc()
        ACTIVE_LOAD_TESTS.inc()
        
        logger.info("load_test_started", test_id=test_id, config=config.dict())
        return test_id
    
    async def get_test_result(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get test result by test_id"""
        return await self._get_test_from_db(test_id)
    
    async def _create_test_record(self, test_id: str, config: LoadTestConfig):
        """Create initial test record in database"""
        try:
            with db_service.get_session() as session:
                session.execute(
                    text("""
                    INSERT INTO test_runs (test_id, config, status, total_requests)
                    VALUES (:test_id, :config, :status, :total_requests)
                    """),
                    {
                        "test_id": test_id,
                        "config": json.dumps(config.dict()),
                        "status": TestStatus.PENDING.value,
                        "total_requests": config.total_requests or (config.rps * config.duration if config.rps and config.duration else 0)
                    }
                )
                session.commit()
        except Exception as e:
            logger.error("failed_to_create_test_record", test_id=test_id, error=str(e))
            raise
    
    async def _execute_test(self, test_id: str, config: LoadTestConfig):
        """Execute the load test"""
        start_time = time.time()
        request_results = []
        
        try:
            # Update status to running
            await self._update_test_status(test_id, TestStatus.RUNNING, {"started_at": datetime.utcnow()})
            
            # Generate requests based on configuration
            if config.burst_mode or config.total_requests:
                request_results = await self._execute_burst_test(test_id, config)
            else:
                request_results = await self._execute_sustained_test(test_id, config)
            
            # Calculate final statistics
            end_time = time.time()
            duration = end_time - start_time
            
            stats = self._calculate_statistics(request_results, start_time, end_time)
            await self._finalize_test(test_id, stats, TestStatus.COMPLETED)
            
            TESTS_COMPLETED.labels(status='completed').inc()
            TEST_DURATION.observe(duration)
            
        except Exception as e:
            logger.error("load_test_failed", test_id=test_id, error=str(e))
            await self._finalize_test(test_id, {}, TestStatus.FAILED)
            TESTS_COMPLETED.labels(status='failed').inc()
        finally:
            ACTIVE_LOAD_TESTS.dec()
            if test_id in self.active_tests:
                del self.active_tests[test_id]
    
    async def _execute_burst_test(self, test_id: str, config: LoadTestConfig) -> List[Dict[str, Any]]:
        """Execute burst mode test with concurrency control"""
        semaphore = asyncio.Semaphore(config.concurrency_limit)
        total_requests = config.total_requests or 100
        
        tasks = []
        for i in range(total_requests):
            payload = self._generate_payload(config, i)
            task = self._execute_single_request(test_id, payload, semaphore, config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]
    
    async def _execute_sustained_test(self, test_id: str, config: LoadTestConfig) -> List[Dict[str, Any]]:
        """Execute sustained RPS test"""
        semaphore = asyncio.Semaphore(config.concurrency_limit)
        results = []
        
        rps = config.rps or 5
        duration = config.duration or 30
        interval = 1.0 / rps
        
        end_time = time.time() + duration
        request_count = 0
        
        while time.time() < end_time:
            payload = self._generate_payload(config, request_count)
            task = self._execute_single_request(test_id, payload, semaphore, config)
            
            # Don't await here to maintain RPS
            result_task = asyncio.create_task(task)
            results.append(result_task)
            
            request_count += 1
            await asyncio.sleep(interval)
        
        # Wait for all requests to complete
        completed_results = await asyncio.gather(*results, return_exceptions=True)
        return [r for r in completed_results if not isinstance(r, Exception)]
    
    async def _execute_single_request(self, test_id: str, payload: PostRequestModel, semaphore: asyncio.Semaphore, config: LoadTestConfig) -> Dict[str, Any]:
        """Execute a single request with proper tracing and failure scenarios"""
        async with semaphore:
            request_id = str(uuid.uuid4())
            start_time = time.time()
            
            # Store request record
            await self._store_request_record(test_id, request_id, start_time)
            
            try:
                # Simulate various failure scenarios based on config
                if config.failure_injection and config.failure_injection.enabled:
                    failure_rate = config.failure_injection.failure_rate / 100.0  # Convert percentage to decimal
                    
                    # Random failure injection
                    if random.random() < failure_rate:
                        # Simulate different types of failures
                        failure_type = random.choice(['timeout', 'db_error', 'network_error'])
                        
                        if failure_type == 'timeout':
                            await asyncio.sleep(config.failure_injection.timeout_seconds)
                            raise Exception("Request timeout")
                        elif failure_type == 'db_error':
                            raise Exception("Database connection failed")
                        else:
                            raise Exception("Network error")
                    
                    # Add artificial latency
                    if config.failure_injection.latency_min_ms > 0:
                        latency = random.randint(
                            config.failure_injection.latency_min_ms,
                            max(config.failure_injection.latency_max_ms, config.failure_injection.latency_min_ms)
                        )
                        await asyncio.sleep(latency / 1000.0)
                
                # Import here to avoid circular imports
                from v1.controllers.requests import process_request_internal
                
                # Generate duplicate requests occasionally
                if random.random() < 0.1:  # 10% chance of duplicate
                    # Use same request_id to simulate duplicate
                    existing_id = f"duplicate_{test_id}_{random.randint(1, 10)}"
                    result = await process_request_internal(payload, existing_id)
                    status_type = "duplicate"
                else:
                    result = await process_request_internal(payload, request_id)
                    status_type = "success" if result.get("status", 500) < 400 else "failed"
                
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                
                # Handle rate limiting
                if result.get("status") == 429:
                    status_type = "rate_limited"
                
                # Update request record
                await self._update_request_record(test_id, request_id, status_type, result.get("status", 200), latency_ms)
                
                if status_type == "success":
                    TEST_REQUEST_SUCCESS.inc()
                else:
                    TEST_REQUEST_FAILED.inc()
                
                return {
                    "request_id": request_id,
                    "status": status_type,
                    "latency_ms": latency_ms,
                    "status_code": result.get("status", 200)
                }
                
            except Exception as e:
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                
                await self._update_request_record(test_id, request_id, "failed", 500, latency_ms, str(e))
                
                TEST_REQUEST_FAILED.inc()
                
                return {
                    "request_id": request_id,
                    "status": "failed",
                    "latency_ms": latency_ms,
                    "error": str(e)
                }
    
    def _generate_payload(self, config: LoadTestConfig, request_index: int) -> PostRequestModel:
        """Generate request payload based on strategy"""
        base = config.base_payload.copy()
        
        if config.payload_strategy == PayloadStrategy.RANDOMIZED:
            # Add some randomization
            if "rate_of_requests" in base:
                base["rate_of_requests"] = random.randint(1, base.get("rate_of_requests", 10))
            if "number_of_requests" in base:
                base["number_of_requests"] = random.randint(1, base.get("number_of_requests", 100))
        
        return PostRequestModel(**base)
    
    def _calculate_statistics(self, results: List[Dict[str, Any]], start_time: float, end_time: float) -> Dict[str, Any]:
        """Calculate final test statistics"""
        if not results:
            return {}
        
        latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
        
        # Count different status types
        succeeded = len([r for r in results if r.get("status") == "success"])
        failed = len([r for r in results if r.get("status") == "failed"])
        rate_limited = len([r for r in results if r.get("status") == "rate_limited"])
        duplicates = len([r for r in results if r.get("status") == "duplicate"])
        
        stats = {
            "total_requests": len(results),
            "succeeded": succeeded,
            "failed": failed,
            "rate_limited": rate_limited,
            "duplicates": duplicates,
            "retries_total": 0,  # Would need retry tracking
            "start_time": datetime.fromtimestamp(start_time),
            "end_time": datetime.fromtimestamp(end_time),
            "duration_sec": end_time - start_time
        }
        
        if latencies:
            stats["avg_latency_ms"] = mean(latencies)
            percentiles = quantiles(latencies, n=100)
            stats["p95_latency_ms"] = percentiles[94] if len(percentiles) > 94 else max(latencies)
            stats["p99_latency_ms"] = percentiles[98] if len(percentiles) > 98 else max(latencies)
        
        return stats
    
    async def _store_request_record(self, test_id: str, request_id: str, start_time: float):
        """Store individual request record"""
        with db_service.get_session() as session:
            session.execute(
                text("""
                INSERT INTO test_requests (test_id, request_id, started_at, status)
                VALUES (:test_id, :request_id, :started_at, :status)
                """),
                {
                    "test_id": test_id,
                    "request_id": request_id,
                    "started_at": datetime.fromtimestamp(start_time),
                    "status": "pending"
                }
            )
            session.commit()
    
    async def _update_request_record(self, test_id: str, request_id: str, status: str, 
                                   status_code: int, latency_ms: float, error_message: str = None):
        """Update request record with results"""
        with db_service.get_session() as session:
            session.execute(
                text("""
                UPDATE test_requests 
                SET completed_at = :completed_at, status = :status, status_code = :status_code, 
                    latency_ms = :latency_ms, error_message = :error_message
                WHERE test_id = :test_id AND request_id = :request_id
                """),
                {
                    "completed_at": datetime.utcnow(),
                    "status": status,
                    "status_code": status_code,
                    "latency_ms": latency_ms,
                    "error_message": error_message,
                    "test_id": test_id,
                    "request_id": request_id
                }
            )
            session.commit()
    
    async def _update_test_status(self, test_id: str, status: TestStatus, additional_data: Dict[str, Any] = None):
        """Update test status in database"""
        with db_service.get_session() as session:
            if additional_data and "started_at" in additional_data:
                session.execute(
                    text("UPDATE test_runs SET status = :status, started_at = :started_at WHERE test_id = :test_id"),
                    {"status": status.value, "started_at": additional_data["started_at"], "test_id": test_id}
                )
            else:
                session.execute(
                    text("UPDATE test_runs SET status = :status WHERE test_id = :test_id"),
                    {"status": status.value, "test_id": test_id}
                )
            session.commit()
    
    async def _finalize_test(self, test_id: str, stats: Dict[str, Any], status: TestStatus):
        """Finalize test with computed statistics"""
        with db_service.get_session() as session:
            session.execute(
                text("""
                UPDATE test_runs SET 
                    status = :status, completed_at = :completed_at, succeeded = :succeeded, failed = :failed, 
                    rate_limited = :rate_limited, duplicates = :duplicates, retries_total = :retries_total,
                    avg_latency_ms = :avg_latency_ms, p95_latency_ms = :p95_latency_ms, 
                    p99_latency_ms = :p99_latency_ms, duration_sec = :duration_sec
                WHERE test_id = :test_id
                """),
                {
                    "status": status.value,
                    "completed_at": datetime.utcnow(),
                    "succeeded": stats.get("succeeded", 0),
                    "failed": stats.get("failed", 0),
                    "rate_limited": stats.get("rate_limited", 0),
                    "duplicates": stats.get("duplicates", 0),
                    "retries_total": stats.get("retries_total", 0),
                    "avg_latency_ms": stats.get("avg_latency_ms"),
                    "p95_latency_ms": stats.get("p95_latency_ms"),
                    "p99_latency_ms": stats.get("p99_latency_ms"),
                    "duration_sec": stats.get("duration_sec"),
                    "test_id": test_id
                }
            )
            session.commit()
    
    async def _get_test_from_db(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve test result from database"""
        with db_service.get_session() as session:
            result = session.execute(
                text("SELECT * FROM test_runs WHERE test_id = :test_id"),
                {"test_id": test_id}
            ).fetchone()
            
            if result:
                return dict(result._mapping)
            return None

load_test_service = LoadTestService()