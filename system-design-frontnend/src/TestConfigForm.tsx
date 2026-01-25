import React, { useState } from 'react';
import { type LoadTestConfig } from './types';

interface TestConfigFormProps {
  onStartTest: (config: LoadTestConfig) => void;
  isStarting: boolean;
}

export function TestConfigForm({ onStartTest, isStarting }: TestConfigFormProps) {
  const [config, setConfig] = useState<LoadTestConfig>({
    total_requests: 1000,
    concurrency_limit: 50,
    enable_idempotency: true,
    enable_retries: true,
    enable_failure_injection: false,
    failure_injection: {
      db_latency_ms: 50,
      failure_rate: 5,
      timeout_ms: 5000,
    },
  });

  const [testMode, setTestMode] = useState<'total' | 'rps'>('total');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateConfig = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (testMode === 'total') {
      if (!config.total_requests || config.total_requests < 1) {
        newErrors.total_requests = 'Total requests must be at least 1';
      }
    } else {
      if (!config.rps || config.rps < 1) {
        newErrors.rps = 'RPS must be at least 1';
      }
      if (!config.duration_sec || config.duration_sec < 1) {
        newErrors.duration_sec = 'Duration must be at least 1 second';
      }
    }

    if (config.concurrency_limit < 1 || config.concurrency_limit > 1000) {
      newErrors.concurrency_limit = 'Concurrency limit must be between 1 and 1000';
    }

    if (config.enable_failure_injection) {
      if (config.failure_injection!.failure_rate < 0 || config.failure_injection!.failure_rate > 100) {
        newErrors.failure_rate = 'Failure rate must be between 0 and 100';
      }
      if (config.failure_injection!.timeout_ms < 100) {
        newErrors.timeout_ms = 'Timeout must be at least 100ms';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateConfig()) {
      const finalConfig = { ...config };
      if (testMode === 'total') {
        delete finalConfig.rps;
        delete finalConfig.duration_sec;
      } else {
        delete finalConfig.total_requests;
      }
      onStartTest(finalConfig);
    }
  };

  const updateConfig = (updates: Partial<LoadTestConfig>) => {
    setConfig(prev => ({ ...prev, ...updates }));
  };

  const updateFailureInjection = (updates: Partial<NonNullable<LoadTestConfig['failure_injection']>>) => {
    setConfig(prev => ({
      ...prev,
      failure_injection: { ...prev.failure_injection!, ...updates }
    }));
  };

  return (
    <div style={{ 
      padding: '24px', 
      backgroundColor: '#f8f9fa', 
      borderRadius: '8px',
      minWidth: '400px'
    }}>
      <h2 style={{ marginBottom: '24px', fontSize: '24px', fontWeight: 'bold' }}>
        Load Test Configuration
      </h2>
      
      <form onSubmit={handleSubmit}>
        {/* Test Mode Selection */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
            Test Mode
          </label>
          <div style={{ display: 'flex', gap: '16px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="radio"
                checked={testMode === 'total'}
                onChange={() => setTestMode('total')}
              />
              Total Requests
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="radio"
                checked={testMode === 'rps'}
                onChange={() => setTestMode('rps')}
              />
              RPS + Duration
            </label>
          </div>
        </div>

        {/* Test Parameters */}
        {testMode === 'total' ? (
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
              Total Requests
            </label>
            <input
              type="number"
              value={config.total_requests || ''}
              onChange={(e) => updateConfig({ total_requests: parseInt(e.target.value) || undefined })}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: errors.total_requests ? '2px solid #ef4444' : '1px solid #d1d5db',
                borderRadius: '4px'
              }}
            />
            {errors.total_requests && (
              <div style={{ color: '#ef4444', fontSize: '14px', marginTop: '4px' }}>
                {errors.total_requests}
              </div>
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', gap: '16px', marginBottom: '20px' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                RPS
              </label>
              <input
                type="number"
                value={config.rps || ''}
                onChange={(e) => updateConfig({ rps: parseInt(e.target.value) || undefined })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: errors.rps ? '2px solid #ef4444' : '1px solid #d1d5db',
                  borderRadius: '4px'
                }}
              />
              {errors.rps && (
                <div style={{ color: '#ef4444', fontSize: '14px', marginTop: '4px' }}>
                  {errors.rps}
                </div>
              )}
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                Duration (seconds)
              </label>
              <input
                type="number"
                value={config.duration_sec || ''}
                onChange={(e) => updateConfig({ duration_sec: parseInt(e.target.value) || undefined })}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: errors.duration_sec ? '2px solid #ef4444' : '1px solid #d1d5db',
                  borderRadius: '4px'
                }}
              />
              {errors.duration_sec && (
                <div style={{ color: '#ef4444', fontSize: '14px', marginTop: '4px' }}>
                  {errors.duration_sec}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Concurrency Limit */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
            Concurrency Limit
          </label>
          <input
            type="number"
            value={config.concurrency_limit}
            onChange={(e) => updateConfig({ concurrency_limit: parseInt(e.target.value) || 1 })}
            min="1"
            max="1000"
            style={{
              width: '100%',
              padding: '8px 12px',
              border: errors.concurrency_limit ? '2px solid #ef4444' : '1px solid #d1d5db',
              borderRadius: '4px'
            }}
          />
          {errors.concurrency_limit && (
            <div style={{ color: '#ef4444', fontSize: '14px', marginTop: '4px' }}>
              {errors.concurrency_limit}
            </div>
          )}
        </div>

        {/* Feature Toggles */}
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ marginBottom: '12px', fontSize: '18px', fontWeight: '600' }}>
            Features
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                checked={config.enable_idempotency}
                onChange={(e) => updateConfig({ enable_idempotency: e.target.checked })}
              />
              Enable Idempotency
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                checked={config.enable_retries}
                onChange={(e) => updateConfig({ enable_retries: e.target.checked })}
              />
              Enable Retries
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                checked={config.enable_failure_injection}
                onChange={(e) => updateConfig({ enable_failure_injection: e.target.checked })}
              />
              Enable Failure Injection
            </label>
          </div>
        </div>

        {/* Failure Injection Settings */}
        {config.enable_failure_injection && (
          <div style={{ 
            marginBottom: '20px', 
            padding: '16px', 
            backgroundColor: '#fff3cd', 
            borderRadius: '4px',
            border: '1px solid #ffeaa7'
          }}>
            <h4 style={{ marginBottom: '12px', fontSize: '16px', fontWeight: '600' }}>
              Failure Injection Settings
            </h4>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                DB Latency: {config.failure_injection!.db_latency_ms}ms
              </label>
              <input
                type="range"
                min="10"
                max="1000"
                value={config.failure_injection!.db_latency_ms}
                onChange={(e) => updateFailureInjection({ db_latency_ms: parseInt(e.target.value) })}
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                Failure Rate: {config.failure_injection!.failure_rate}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={config.failure_injection!.failure_rate}
                onChange={(e) => updateFailureInjection({ failure_rate: parseInt(e.target.value) })}
                style={{ width: '100%' }}
              />
              {errors.failure_rate && (
                <div style={{ color: '#ef4444', fontSize: '14px', marginTop: '4px' }}>
                  {errors.failure_rate}
                </div>
              )}
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                Timeout (ms)
              </label>
              <input
                type="number"
                value={config.failure_injection!.timeout_ms}
                onChange={(e) => updateFailureInjection({ timeout_ms: parseInt(e.target.value) || 5000 })}
                min="100"
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: errors.timeout_ms ? '2px solid #ef4444' : '1px solid #d1d5db',
                  borderRadius: '4px'
                }}
              />
              {errors.timeout_ms && (
                <div style={{ color: '#ef4444', fontSize: '14px', marginTop: '4px' }}>
                  {errors.timeout_ms}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isStarting}
          style={{
            width: '100%',
            padding: '12px',
            backgroundColor: isStarting ? '#9ca3af' : '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '16px',
            fontWeight: '600',
            cursor: isStarting ? 'not-allowed' : 'pointer'
          }}
        >
          {isStarting ? 'Starting Test...' : 'Start Test'}
        </button>
      </form>
    </div>
  );
}