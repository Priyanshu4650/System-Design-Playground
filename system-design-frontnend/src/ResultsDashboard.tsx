import { type TestResult } from './types';
import { Charts } from './Charts';

interface ResultsDashboardProps {
  testResult: TestResult | undefined;
  isLoading: boolean;
  error: Error | null;
  onFetchResults: () => void;
  autoRefresh: boolean;
  onToggleAutoRefresh: () => void;
  onReset: () => void;
}

export function ResultsDashboard({ 
  testResult, 
  isLoading, 
  error, 
  onFetchResults, 
  autoRefresh, 
  onToggleAutoRefresh,
  onReset 
}: ResultsDashboardProps) {
  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(1)}s`;
  };

  const formatLatency = (ms?: number) => {
    if (ms === undefined || ms === null) return 'N/A';
    return `${ms.toFixed(1)}ms`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#10b981';
      case 'running': return '#3b82f6';
      case 'pending': return '#f59e0b';
      case 'failed': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return 'Completed';
      case 'running': return 'Running';
      case 'pending': return 'Pending';
      case 'failed': return 'Failed';
      default: return 'Unknown';
    }
  };

  if (error) {
    return (
      <div style={{ 
        padding: '24px', 
        backgroundColor: '#fef2f2', 
        borderRadius: '8px',
        border: '1px solid #fecaca',
        flex: 1
      }}>
        <h2 style={{ color: '#dc2626', marginBottom: '16px', fontSize: '20px', fontWeight: 'bold' }}>
          Error Loading Results
        </h2>
        <p style={{ color: '#7f1d1d', marginBottom: '16px' }}>
          {error.message}
        </p>
        <button
          onClick={onFetchResults}
          style={{
            padding: '8px 16px',
            backgroundColor: '#dc2626',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!testResult) {
    return (
      <div style={{ 
        padding: '24px', 
        backgroundColor: '#f9fafb', 
        borderRadius: '8px',
        border: '2px dashed #d1d5db',
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '400px'
      }}>
        <div style={{ textAlign: 'center', color: '#6b7280' }}>
          <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>No Test Results</h3>
          <p>Start a test to see results here</p>
        </div>
      </div>
    );
  }

  const successRate = testResult.total_requests > 0 
    ? ((testResult.succeeded / testResult.total_requests) * 100).toFixed(1)
    : '0';

  return (
    <div style={{ flex: 1, padding: '24px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '24px' 
      }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '8px' }}>
            Test Results
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '14px', color: '#6b7280' }}>
              Test ID: {testResult.test_id}
            </span>
            <span 
              style={{ 
                padding: '4px 8px', 
                borderRadius: '12px', 
                fontSize: '12px', 
                fontWeight: '600',
                backgroundColor: getStatusColor(testResult.status) + '20',
                color: getStatusColor(testResult.status)
              }}
            >
              {getStatusText(testResult.status)}
            </span>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={onToggleAutoRefresh}
            style={{
              padding: '8px 16px',
              backgroundColor: autoRefresh ? '#10b981' : '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </button>
          <button
            onClick={onFetchResults}
            disabled={isLoading}
            style={{
              padding: '8px 16px',
              backgroundColor: isLoading ? '#9ca3af' : '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontSize: '14px'
            }}
          >
            {isLoading ? 'Loading...' : 'Refresh'}
          </button>
          <button
            onClick={onReset}
            style={{
              padding: '8px 16px',
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            New Test
          </button>
          <button
            onClick={() => window.open(`http://localhost:8000/v1/tests/${testResult.test_id}/download`)}
            style={{
              padding: '8px 16px',
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Download
          </button>
          <button
            onClick={() => {
              const email = prompt('Enter email address:');
              if (email) {
                fetch(`http://localhost:8000/v1/tests/${testResult.test_id}/email?email=${encodeURIComponent(email)}`, { method: 'POST' })
                  .then(() => alert('Result sent to email!'))
                  .catch(() => alert('Failed to send email'));
              }
            }}
            style={{
              padding: '8px 16px',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Email
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '16px', 
        marginBottom: '24px' 
      }}>
        <div style={{ 
          backgroundColor: 'white', 
          padding: '20px', 
          borderRadius: '8px', 
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)' 
        }}>
          <h3 style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Total Requests</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827' }}>
            {testResult.total_requests.toLocaleString()}
          </p>
        </div>

        <div style={{ 
          backgroundColor: 'white', 
          padding: '20px', 
          borderRadius: '8px', 
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)' 
        }}>
          <h3 style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Success Rate</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>
            {successRate}%
          </p>
          <p style={{ fontSize: '12px', color: '#6b7280' }}>
            {testResult.succeeded.toLocaleString()} succeeded
          </p>
        </div>

        <div style={{ 
          backgroundColor: 'white', 
          padding: '20px', 
          borderRadius: '8px', 
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)' 
        }}>
          <h3 style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Failures</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#ef4444' }}>
            {testResult.failed.toLocaleString()}
          </p>
          <p style={{ fontSize: '12px', color: '#6b7280' }}>
            {testResult.rate_limited} rate limited
          </p>
        </div>

        <div style={{ 
          backgroundColor: 'white', 
          padding: '20px', 
          borderRadius: '8px', 
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)' 
        }}>
          <h3 style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Duration</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827' }}>
            {formatDuration(testResult.duration_sec)}
          </p>
          <p style={{ fontSize: '12px', color: '#6b7280' }}>
            {testResult.retries_total} retries
          </p>
        </div>
      </div>

      {/* Latency Panel */}
      <div style={{ 
        backgroundColor: 'white', 
        padding: '20px', 
        borderRadius: '8px', 
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        marginBottom: '24px'
      }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
          Latency Metrics
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
          <div style={{ textAlign: 'center' }}>
            <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>Average</p>
            <p style={{ fontSize: '20px', fontWeight: 'bold', color: '#3b82f6' }}>
              {formatLatency(testResult.avg_latency_ms)}
            </p>
          </div>
          <div style={{ textAlign: 'center' }}>
            <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>95th Percentile</p>
            <p style={{ fontSize: '20px', fontWeight: 'bold', color: '#8b5cf6' }}>
              {formatLatency(testResult.p95_latency_ms)}
            </p>
          </div>
          <div style={{ textAlign: 'center' }}>
            <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>99th Percentile</p>
            <p style={{ fontSize: '20px', fontWeight: 'bold', color: '#ef4444' }}>
              {formatLatency(testResult.p99_latency_ms)}
            </p>
          </div>
        </div>
      </div>

      {/* Charts */}
      <Charts testResult={testResult} />

      {/* Table View */}
      <div style={{ 
        backgroundColor: 'white', 
        padding: '20px', 
        borderRadius: '8px', 
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        marginTop: '24px'
      }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
          Detailed Statistics
        </h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f9fafb' }}>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>
                  Metric
                </th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #e5e7eb' }}>
                  Value
                </th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ padding: '12px', borderBottom: '1px solid #f3f4f6' }}>Total Requests</td>
                <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #f3f4f6' }}>
                  {testResult.total_requests.toLocaleString()}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '12px', borderBottom: '1px solid #f3f4f6' }}>Succeeded</td>
                <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #f3f4f6', color: '#10b981' }}>
                  {testResult.succeeded.toLocaleString()}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '12px', borderBottom: '1px solid #f3f4f6' }}>Failed</td>
                <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #f3f4f6', color: '#ef4444' }}>
                  {testResult.failed.toLocaleString()}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '12px', borderBottom: '1px solid #f3f4f6' }}>Rate Limited</td>
                <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #f3f4f6', color: '#f59e0b' }}>
                  {testResult.rate_limited.toLocaleString()}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '12px', borderBottom: '1px solid #f3f4f6' }}>Duplicates</td>
                <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #f3f4f6' }}>
                  {testResult.duplicates.toLocaleString()}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '12px', borderBottom: '1px solid #f3f4f6' }}>Total Retries</td>
                <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #f3f4f6' }}>
                  {testResult.retries_total.toLocaleString()}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '12px', borderBottom: '1px solid #f3f4f6' }}>Duration</td>
                <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #f3f4f6' }}>
                  {formatDuration(testResult.duration_sec)}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '12px', borderBottom: '1px solid #f3f4f6' }}>Start Time</td>
                <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #f3f4f6' }}>
                  {testResult.start_time ? new Date(testResult.start_time).toLocaleString() : 'N/A'}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '12px' }}>End Time</td>
                <td style={{ padding: '12px', textAlign: 'right' }}>
                  {testResult.end_time ? new Date(testResult.end_time).toLocaleString() : 'N/A'}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}