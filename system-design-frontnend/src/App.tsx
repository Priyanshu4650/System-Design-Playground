import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TestConfigForm } from './TestConfigForm.js';
import { ResultsDashboard } from './ResultsDashboard.js';
import { useTestRunner } from './useTestRunner.js';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function LoadTestApp() {
  const [visitStats, setVisitStats] = useState({ total_visits: 0, unique_visitors: 0 });
  
  const {
    testId,
    testResult,
    testStatus,
    isStarting,
    isLoadingResult,
    startError,
    resultError,
    autoRefresh,
    startTest,
    fetchResults,
    toggleAutoRefresh,
    resetTest,
  } = useTestRunner();

  useEffect(() => {
    // Track visit on page load
    fetch('http://localhost:8000/v1/visits/track', { method: 'POST' })
      .then(() => fetch('http://localhost:8000/v1/visits/stats'))
      .then(res => res.json())
      .then(setVisitStats)
      .catch(console.error);
  }, []);

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#f3f4f6', 
      padding: '24px' 
    }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <header style={{ marginBottom: '32px', textAlign: 'center' }}>
          <h1 style={{ 
            fontSize: '32px', 
            fontWeight: 'bold', 
            color: '#111827', 
            marginBottom: '8px' 
          }}>
            Load Testing Dashboard
          </h1>
          <p style={{ fontSize: '16px', color: '#6b7280' }}>
            Configure and run backend-driven load tests
          </p>
          <div style={{ fontSize: '14px', color: '#9ca3af', marginTop: '8px' }}>
            <a href="/admin" style={{ color: '#3b82f6', textDecoration: 'none' }}>Admin</a>
          </div>
        </header>

        {/* Error Display */}
        {startError && (
          <div style={{ 
            marginBottom: '24px',
            padding: '16px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            color: '#dc2626'
          }}>
            <strong>Error starting test:</strong> {startError.message}
          </div>
        )}

        {/* Main Content */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'minmax(400px, 1fr) 2fr', 
          gap: '32px',
          alignItems: 'start'
        }}>
          {/* Left Panel - Configuration */}
          <TestConfigForm 
            onStartTest={startTest}
            isStarting={isStarting}
          />

          {/* Right Panel - Results */}
          <ResultsDashboard
            testResult={testResult}
            isLoading={isLoadingResult}
            error={resultError}
            onFetchResults={fetchResults}
            autoRefresh={autoRefresh}
            onToggleAutoRefresh={toggleAutoRefresh}
            onReset={resetTest}
          />
        </div>

        {/* Status Bar */}
        {testId && (
          <div style={{ 
            marginTop: '24px',
            padding: '16px',
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <span style={{ fontSize: '14px', color: '#6b7280' }}>
                Current Test ID: 
              </span>
              <span style={{ 
                fontSize: '14px', 
                fontFamily: 'monospace', 
                backgroundColor: '#f3f4f6', 
                padding: '2px 6px', 
                borderRadius: '4px',
                marginLeft: '8px'
              }}>
                {testId}
              </span>
            </div>
            
            {testStatus && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '14px', color: '#6b7280' }}>
                  Status:
                </span>
                <span style={{ 
                  fontSize: '14px', 
                  fontWeight: '600',
                  color: testStatus.status === 'completed' ? '#10b981' : 
                        testStatus.status === 'running' ? '#3b82f6' : 
                        testStatus.status === 'failed' ? '#ef4444' : '#f59e0b'
                }}>
                  {testStatus.status.toUpperCase()}
                </span>
                {testStatus.progress?.message && (
                  <span style={{ fontSize: '14px', color: '#6b7280' }}>
                    - {testStatus.progress.message}
                  </span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <footer style={{ 
          marginTop: '48px', 
          textAlign: 'center', 
          color: '#9ca3af', 
          fontSize: '14px' 
        }}>
          <p>
            Load Testing Dashboard - Built with React, TypeScript, and Recharts
          </p>
        </footer>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LoadTestApp />
    </QueryClientProvider>
  );
}