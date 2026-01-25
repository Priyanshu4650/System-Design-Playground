import { type LoadTestConfig, type StartTestRequest, type StartTestResponse, type TestResult, type TestStatus } from './types';

const API_BASE_URL = 'http://localhost:8000';

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new ApiError(response.status, `API Error: ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  async startTest(config: LoadTestConfig): Promise<StartTestResponse> {
    const request: StartTestRequest = {
      config: {
        total_requests: config.total_requests,
        rps: config.rps,
        duration: config.duration_sec,
        concurrency_limit: config.concurrency_limit,
        payload_strategy: 'fixed',
        base_payload: {
          rate_of_requests: 10,
          number_of_requests: 100,
          retries_enabled: config.enable_retries,
          rate_limiting: 100,
          rate_limiting_algo: 'sliding_window',
          cache_enabled: true,
          cache_ttl: 300,
          db_latency: config.enable_failure_injection ? config.failure_injection?.db_latency_ms || 50 : 50,
        },
        retries_enabled: config.enable_retries,
        idempotency_enabled: config.enable_idempotency,
        failure_injection: config.enable_failure_injection ? {
          enabled: true,
          failure_rate: (config.failure_injection?.failure_rate || 0) / 100,
          latency_min_ms: config.failure_injection?.db_latency_ms || 10,
          latency_max_ms: (config.failure_injection?.db_latency_ms || 10) * 2,
          timeout_seconds: (config.failure_injection?.timeout_ms || 5000) / 1000,
        } : undefined,
      },
    };

    return apiRequest<StartTestResponse>('/v1/tests/start', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  async getTestResult(testId: string): Promise<TestResult> {
    return apiRequest<TestResult>(`/v1/tests/${testId}/result`);
  },

  async getTestStatus(testId: string): Promise<TestStatus> {
    return apiRequest<TestStatus>(`/v1/tests/${testId}/status`);
  },
};