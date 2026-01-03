import structlog
import logging
from prometheus_client import Counter, Histogram, start_http_server

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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

REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration')

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

RATE_LIMIT_EXCEEDED = Counter('rate_limit_exceeded_total', 'Rate limit exceeded', ['client_id', 'window_type'])

def log_rate_limit_exceeded(client_id: str, window_type: str):
    RATE_LIMIT_EXCEEDED.labels(client_id=client_id, window_type=window_type).inc()
    logger.warning("rate_limit_exceeded", client_id=client_id, window_type=window_type)

start_http_server(8001)
