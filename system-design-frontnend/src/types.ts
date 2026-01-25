export interface LoadTestConfig {
  total_requests?: number;
  rps?: number;
  duration_sec?: number;
  concurrency_limit: number;
  enable_idempotency: boolean;
  enable_retries: boolean;
  enable_failure_injection: boolean;
  failure_injection?: {
    db_latency_ms: number;
    failure_rate: number;
    timeout_ms: number;
  };
}

export interface StartTestRequest {
  config: {
    total_requests?: number;
    rps?: number;
    duration?: number;
    concurrency_limit: number;
    payload_strategy: 'fixed' | 'randomized';
    base_payload: {
      rate_of_requests: number;
      number_of_requests: number;
      retries_enabled: boolean;
      rate_limiting: number;
      rate_limiting_algo: string;
      cache_enabled: boolean;
      cache_ttl: number;
      db_latency: number;
    };
    retries_enabled: boolean;
    idempotency_enabled: boolean;
    failure_injection?: {
      enabled: boolean;
      failure_rate: number;
      latency_min_ms: number;
      latency_max_ms: number;
      timeout_seconds: number;
    };
  };
}

export interface StartTestResponse {
  test_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: {
    message: string;
  };
}

export interface TestResult {
  test_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_requests: number;
  succeeded: number;
  failed: number;
  rate_limited: number;
  duplicates: number;
  retries_total: number;
  avg_latency_ms?: number;
  p95_latency_ms?: number;
  p99_latency_ms?: number;
  start_time?: string;
  end_time?: string;
  duration_sec?: number;
}

export interface TestStatus {
  test_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: {
    message: string;
    succeeded?: number;
    failed?: number;
  };
}