import structlog
import logging
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import os

# Configure file logging only (no terminal output)
log_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logs.txt')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path)
    ]
)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() 
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Existing metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration', 
                           buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])

# Enhanced metrics for failure injection
TOTAL_REQUESTS = Counter('http_requests_total_enhanced', 'Total HTTP requests', ['method', 'endpoint', 'status'])
FAILED_REQUESTS = Counter('http_requests_failed_total', 'Failed HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_latency_seconds', 'Request latency with percentiles',
                          buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
ACTIVE_REQUESTS = Gauge('http_requests_active', 'Currently active requests')

# Rate limiting metrics
RATE_LIMIT_EXCEEDED = Counter('rate_limit_exceeded_total', 'Rate limit exceeded', ['client_id', 'window_type'])

logger = structlog.get_logger()

def log_request(request_id: str, endpoint: str, method: str, status_code: int, duration: float):
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
    REQUEST_DURATION.observe(duration)
    
    logger.info(
        "request_processed",
        request_id=request_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        duration=duration
    )

def log_request_with_metrics(request_id: str, endpoint: str, method: str, status_code: int, duration: float):
    REQUEST_LATENCY.observe(duration)
    TOTAL_REQUESTS.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
    
    if status_code >= 400:
        FAILED_REQUESTS.labels(method=method, endpoint=endpoint).inc()
    
    logger.info(
        "request_completed",
        request_id=request_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        duration=duration
    )

def log_rate_limit_exceeded(client_id: str, window_type: str):
    RATE_LIMIT_EXCEEDED.labels(client_id=client_id, window_type=window_type).inc()
    logger.warning("rate_limit_exceeded", client_id=client_id, window_type=window_type)

# Start Prometheus HTTP server only if not already running
try:
    start_http_server(8001)
except OSError as e:
    if "Address already in use" in str(e):
        logger.info("prometheus server already running on port 8001")
    else:
        raise