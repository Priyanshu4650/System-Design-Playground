import React, { useState, useEffect, useCallback } from 'react';
import { MetricsData } from '../types/api';
import { apiService } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';

interface MetricsChartsProps {
  className?: string;
}

export const MetricsCharts: React.FC<MetricsChartsProps> = ({ className }) => {
  const [metrics, setMetrics] = useState<MetricsData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>();

  // Load initial metrics
  const loadMetrics = useCallback(async () => {
    try {
      const response = await apiService.getMetrics();
      if (response.success && response.data) {
        setMetrics(response.data);
        setError(undefined);
      } else {
        setError(response.error || 'Failed to load metrics');
      }
    } catch (err) {
      setError('Network error loading metrics');
    } finally {
      setIsLoading(false);
    }
  }, []); // Empty dependency array to prevent recreation

  // Handle real-time updates
  const handleWebSocketMessage = useCallback((message: any) => {
    try {
      if (message.type === 'metrics') {
        setMetrics(prev => {
          const newMetrics = [...prev, message.data];
          // Keep only last 100 data points
          return newMetrics.slice(-100);
        });
      }
    } catch (error) {
      console.error('Error processing WebSocket message:', error);
    }
  }, []);

  const { isConnected } = { isConnected: false }; // Disable WebSocket temporarily
  // const { isConnected } = useWebSocket({
  //   onMessage: handleWebSocketMessage
  // });

  useEffect(() => {
    loadMetrics();
  }, []); // Remove loadMetrics and isConnected from dependencies

  useEffect(() => {
    // Fallback polling if WebSocket fails - reduce frequency for production
    const interval = setInterval(() => {
      if (!isConnected) {
        loadMetrics();
      }
    }, 30000); // Changed from 5000ms to 30000ms (30 seconds)

    return () => clearInterval(interval);
  }, [isConnected]); // Only depend on isConnected

  const latest = metrics[metrics.length - 1];

  if (isLoading) {
    return <div className={`metrics-charts loading ${className}`}>Loading metrics...</div>;
  }

  if (error) {
    return (
      <div className={`metrics-charts error ${className}`}>
        <div className="error-message">⚠️ {error}</div>
        <button onClick={loadMetrics}>Retry</button>
      </div>
    );
  }

  return (
    <div className={`metrics-charts ${className}`}>
      <div className="charts-header">
        <h2>Real-Time Metrics</h2>
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          <div className="status-dot"></div>
          {isConnected ? 'Live' : 'Polling'}
        </div>
      </div>

      <div className="metrics-grid">
        {/* Current Values */}
        <div className="metric-card current-values">
          <h3>Current</h3>
          {latest ? (
            <div className="values">
              <div className="value">
                <span className="label">Request Rate</span>
                <span className="number">{latest.request_rate.toFixed(1)} RPS</span>
              </div>
              <div className="value error">
                <span className="label">Error Rate</span>
                <span className="number">{(latest.error_rate * 100).toFixed(1)}%</span>
              </div>
              <div className="value">
                <span className="label">Retries</span>
                <span className="number">{latest.retry_count}</span>
              </div>
            </div>
          ) : (
            <div className="no-data">No data available</div>
          )}
        </div>

        {/* Request Rate Chart */}
        <div className="metric-card chart">
          <h3>Request Rate (RPS)</h3>
          <div className="chart-container">
            <MiniChart 
              data={metrics.map(m => m.request_rate)} 
              color="#4CAF50"
              max={Math.max(...metrics.map(m => m.request_rate), 1)}
            />
          </div>
        </div>

        {/* Error Rate Chart */}
        <div className="metric-card chart">
          <h3>Error Rate (%)</h3>
          <div className="chart-container">
            <MiniChart 
              data={metrics.map(m => m.error_rate * 100)} 
              color="#F44336"
              max={100}
            />
          </div>
        </div>

        {/* Latency Chart */}
        <div className="metric-card chart">
          <h3>Latency (ms)</h3>
          <div className="chart-container">
            <div className="latency-lines">
              <MiniChart 
                data={metrics.map(m => m.p95_latency)} 
                color="#FF9800"
                max={Math.max(...metrics.map(m => Math.max(m.p95_latency, m.p99_latency)), 1)}
                label="P95"
              />
              <MiniChart 
                data={metrics.map(m => m.p99_latency)} 
                color="#E91E63"
                max={Math.max(...metrics.map(m => Math.max(m.p95_latency, m.p99_latency)), 1)}
                label="P99"
              />
            </div>
          </div>
        </div>

        {/* Retry Count Chart */}
        <div className="metric-card chart">
          <h3>Retry Count</h3>
          <div className="chart-container">
            <MiniChart 
              data={metrics.map(m => m.retry_count)} 
              color="#9C27B0"
              max={Math.max(...metrics.map(m => m.retry_count), 1)}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// Simple SVG line chart component
interface MiniChartProps {
  data: number[];
  color: string;
  max: number;
  label?: string;
}

const MiniChart: React.FC<MiniChartProps> = ({ data, color, max, label }) => {
  const width = 200;
  const height = 60;
  const padding = 5;

  if (data.length === 0 || !data.some(d => !isNaN(d))) {
    return <div className="no-chart-data">No data</div>;
  }

  // Filter out NaN values and ensure we have valid numbers
  const validData = data.filter(d => !isNaN(d) && isFinite(d));
  if (validData.length === 0) {
    return <div className="no-chart-data">No valid data</div>;
  }

  const points = validData.map((value, index) => {
    const x = padding + (index / Math.max(validData.length - 1, 1)) * (width - 2 * padding);
    const y = height - padding - (value / Math.max(max, 1)) * (height - 2 * padding);
    return `${x},${y}`;
  }).join(' ');

  const lastValue = validData[validData.length - 1];
  const lastX = padding + ((validData.length - 1) / Math.max(validData.length - 1, 1)) * (width - 2 * padding);
  const lastY = height - padding - (lastValue / Math.max(max, 1)) * (height - 2 * padding);

  return (
    <div className="mini-chart">
      {label && <div className="chart-label">{label}</div>}
      <svg width={width} height={height}>
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Current value dot - only render if coordinates are valid */}
        {validData.length > 0 && !isNaN(lastX) && !isNaN(lastY) && (
          <circle
            cx={lastX}
            cy={lastY}
            r="3"
            fill={color}
          />
        )}
      </svg>
      <div className="current-value">{lastValue?.toFixed(1) || '0'}</div>
    </div>
  );
};