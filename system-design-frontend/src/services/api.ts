import { 
  ApiResponse, 
  TrafficRequest, 
  TrafficResult, 
  FailureConfig, 
  MetricsData, 
  RequestSummary, 
  TraceResponse 
} from '../types/api';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }

  // Traffic Generation
  async generateTraffic(request: TrafficRequest): Promise<ApiResponse<{results: TrafficResult[], count: number}>> {
    return this.request('/requests/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getTrafficStatus(): Promise<ApiResponse<{ active: boolean; count: number }>> {
    return this.request('/v1/traffic/status');
  }

  async stopTraffic(): Promise<ApiResponse<void>> {
    return this.request('/v1/traffic/stop', { method: 'POST' });
  }

  // Failure Configuration
  async getFailureConfig(): Promise<ApiResponse<FailureConfig>> {
    return this.request('/v1/config/failure');
  }

  async updateFailureConfig(config: Partial<FailureConfig>): Promise<ApiResponse<FailureConfig>> {
    return this.request('/v1/config/failure', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  // Metrics
  async getMetrics(): Promise<ApiResponse<MetricsData[]>> {
    return this.request('/metrics/json');
  }

  // Request Explorer
  async getRecentRequests(limit = 100): Promise<ApiResponse<RequestSummary[]>> {
    return this.request(`/requests/recent?limit=${limit}`);
  }

  // Tracing
  async getTrace(requestId: string): Promise<ApiResponse<TraceResponse>> {
    return this.request(`/v1/trace/${requestId}`);
  }

  async getTraceTimeline(requestId: string): Promise<ApiResponse<any>> {
    return this.request(`/v1/trace/${requestId}/timeline`);
  }

  // WebSocket connection
  createWebSocket(): WebSocket {
    const wsUrl = API_BASE.replace('http', 'ws') + '/ws';
    return new WebSocket(wsUrl);
  }
}

export const apiService = new ApiService();