// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// Traffic Generator Types
export interface TrafficRequest {
  mode: 'single' | 'burst' | 'sustained';
  count?: number;
  rps?: number;
  duration?: number;
  payload: RequestPayload;
}

export interface RequestPayload {
  rate_of_requests: number;
  number_of_requests: number;
  retries_enabled: boolean;
  rate_limiting: number;
  rate_limiting_algo: string;
  cache_enabled: boolean;
  cache_ttl: number;
  db_latency: number;
}

export interface TrafficResult {
  request_id: string;
  status: 'success' | 'failure';
  latency_ms: number;
  timestamp: string;
}

// Failure Injection Types
export interface FailureConfig {
  failure_injection_enabled: boolean;
  failure_rate: number;
  db_latency_min_ms: number;
  db_latency_max_ms: number;
  db_timeout_seconds: number;
  redis_timeout_seconds: number;
  max_retries: number;
}

// Metrics Types
export interface MetricsData {
  timestamp: number;
  request_rate: number;
  error_rate: number;
  retry_count: number;
  p95_latency: number;
  p99_latency: number;
}

// Request Explorer Types
export interface RequestSummary {
  request_id: string;
  status: number;
  latency_ms: number;
  retry_count: number;
  timestamp: string;
  endpoint: string;
  method: string;
}

// Trace Types
export interface TraceEvent {
  event_id: string;
  request_id: string;
  timestamp_wall: string;
  event_type: string;
  metadata: Record<string, any>;
}

export interface RequestTrace {
  trace_id: string;
  request_id: string;
  start_time: string;
  end_time?: string;
  total_latency_ms?: number;
  status_code?: number;
  events: TraceEvent[];
}

export interface TraceResponse {
  trace: RequestTrace;
  event_count: number;
  failure_points: TraceEvent[];
  retry_attempts: TraceEvent[];
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'metrics' | 'request_update' | 'trace_update';
  data: any;
}

// UI State Types
export interface UIState {
  isConnected: boolean;
  lastUpdate: number;
  error?: string;
}