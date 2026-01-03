# API Contracts

## Traffic Generation

### POST /v1/traffic/generate
```typescript
interface TrafficRequest {
  mode: 'single' | 'burst' | 'sustained';
  count?: number;        // For burst mode
  rps?: number;          // For sustained mode  
  duration?: number;     // For sustained mode (seconds)
  payload: RequestPayload;
}

interface RequestPayload {
  rate_of_requests: number;
  number_of_requests: number;
  retries_enabled: boolean;
  rate_limiting: number;
  rate_limiting_algo: string;
  cache_enabled: boolean;
  cache_ttl: number;
  db_latency: number;
}

// Response
interface TrafficResult {
  request_id: string;
  status: 'success' | 'failure';
  latency_ms: number;
  timestamp: string;
}
```

### GET /v1/traffic/status
```typescript
interface TrafficStatus {
  active: boolean;
  count: number;
}
```

## Failure Configuration

### GET /v1/config/failure
### PUT /v1/config/failure
```typescript
interface FailureConfig {
  failure_injection_enabled: boolean;
  failure_rate: number;              // 0.0 - 1.0
  db_latency_min_ms: number;
  db_latency_max_ms: number;
  db_timeout_seconds: number;
  redis_timeout_seconds: number;
  max_retries: number;
}
```

## Metrics

### GET /metrics/json
```typescript
interface MetricsData {
  timestamp: number;
  request_rate: number;
  error_rate: number;        // 0.0 - 1.0
  retry_count: number;
  p95_latency: number;
  p99_latency: number;
}
```

## Request Explorer

### GET /v1/requests/recent?limit=100
```typescript
interface RequestSummary {
  request_id: string;
  status: number;            // HTTP status code
  latency_ms: number;
  retry_count: number;
  timestamp: string;         // ISO 8601
  endpoint: string;
  method: string;
}
```

## Tracing

### GET /v1/trace/{request_id}
```typescript
interface TraceResponse {
  trace: RequestTrace;
  event_count: number;
  failure_points: TraceEvent[];
  retry_attempts: TraceEvent[];
}

interface RequestTrace {
  trace_id: string;
  request_id: string;
  start_time: string;
  end_time?: string;
  total_latency_ms?: number;
  status_code?: number;
  events: TraceEvent[];
}

interface TraceEvent {
  event_id: string;
  request_id: string;
  timestamp_wall: string;
  event_type: string;
  metadata: Record<string, any>;
}
```

## WebSocket Messages

### Connection: ws://localhost:8000/ws
```typescript
interface WebSocketMessage {
  type: 'metrics' | 'request_update' | 'trace_update';
  data: any;
}

// Examples:
{
  "type": "metrics",
  "data": {
    "timestamp": 1640995200000,
    "request_rate": 45.2,
    "error_rate": 0.05,
    "retry_count": 12,
    "p95_latency": 234.5,
    "p99_latency": 456.7
  }
}

{
  "type": "request_update", 
  "data": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": 200,
    "latency_ms": 123.4,
    "retry_count": 0,
    "timestamp": "2024-01-15T10:30:00.123Z",
    "endpoint": "/v1/requests",
    "method": "POST"
  }
}
```