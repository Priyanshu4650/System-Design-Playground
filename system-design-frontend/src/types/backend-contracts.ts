import { TrafficResult } from './api';

// Strict backend contract types
export interface BackendTrafficResponse {
  results: TrafficResult[];
  count: number;
}

export interface BackendFailureConfig {
  failure_injection_enabled: boolean;
  failure_rate: number;
  db_latency_min_ms: number;
  db_latency_max_ms: number;
  db_timeout_seconds: number;
  redis_timeout_seconds: number;
  max_retries: number;
}

export interface BackendMetricsData {
  timestamp: number;
  request_rate: number;
  error_rate: number;
  retry_count: number;
  p95_latency: number;
  p99_latency: number;
  active_requests: number;
}

// Runtime validation helpers
export const validateTrafficResponse = (data: any): data is BackendTrafficResponse => {
  return data && 
         Array.isArray(data.results) && 
         typeof data.count === 'number';
};

export const validateMetricsData = (data: any): data is BackendMetricsData => {
  return data &&
         typeof data.timestamp === 'number' &&
         typeof data.request_rate === 'number' &&
         typeof data.error_rate === 'number';
};