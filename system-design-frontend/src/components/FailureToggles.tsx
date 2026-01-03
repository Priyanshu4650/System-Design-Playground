import React, { useState, useEffect, useCallback } from 'react';
import { FailureConfig } from '../types/api';
import { apiService } from '../services/api';

export const FailureToggles: React.FC = () => {
  const [config, setConfig] = useState<FailureConfig>({
    failure_injection_enabled: false,
    failure_rate: 0,
    db_latency_min_ms: 0,
    db_latency_max_ms: 0,
    db_timeout_seconds: 5,
    redis_timeout_seconds: 2,
    max_retries: 3
  });
  
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string>();

  // Load current config from backend
  const loadConfig = useCallback(async () => {
    setIsLoading(true);
    setError(undefined);
    
    try {
      const response = await apiService.getFailureConfig();
      if (response.success && response.data) {
        setConfig(response.data);
      } else {
        setError(response.error || 'Failed to load config');
      }
    } catch (err) {
      setError('Network error loading config');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save config to backend
  const saveConfig = useCallback(async (updates: Partial<FailureConfig>) => {
    setIsSaving(true);
    setError(undefined);
    
    try {
      const response = await apiService.updateFailureConfig(updates);
      if (response.success && response.data) {
        setConfig(response.data);
      } else {
        setError(response.error || 'Failed to save config');
      }
    } catch (err) {
      setError('Network error saving config');
    } finally {
      setIsSaving(false);
    }
  }, []);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  const handleToggle = (field: keyof FailureConfig, value: any) => {
    const updates = { [field]: value };
    setConfig(prev => ({ ...prev, ...updates }));
    saveConfig(updates);
  };

  if (isLoading) {
    return <div className="failure-toggles loading">Loading failure configuration...</div>;
  }

  return (
    <div className="failure-toggles">
      <h2>Failure Injection Controls</h2>
      
      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={loadConfig}>Retry</button>
        </div>
      )}

      <div className="controls-grid">
        {/* Master Toggle */}
        <div className="control-group master">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={config.failure_injection_enabled}
              onChange={(e) => handleToggle('failure_injection_enabled', e.target.checked)}
              disabled={isSaving}
            />
            <span className="toggle-switch"></span>
            <span className="label-text">
              Failure Injection {config.failure_injection_enabled ? 'ENABLED' : 'DISABLED'}
            </span>
          </label>
        </div>

        {/* Failure Rate */}
        <div className="control-group">
          <label>
            Failure Rate: {(config.failure_rate * 100).toFixed(1)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={config.failure_rate}
            onChange={(e) => handleToggle('failure_rate', Number(e.target.value))}
            disabled={isSaving || !config.failure_injection_enabled}
            className="slider failure-rate"
          />
          <div className="range-labels">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>

        {/* DB Latency */}
        <div className="control-group">
          <label>
            DB Latency: {config.db_latency_min_ms}ms - {config.db_latency_max_ms}ms
          </label>
          <div className="dual-range">
            <input
              type="range"
              min="0"
              max="5000"
              step="50"
              value={config.db_latency_min_ms}
              onChange={(e) => handleToggle('db_latency_min_ms', Number(e.target.value))}
              disabled={isSaving || !config.failure_injection_enabled}
              className="slider latency-min"
            />
            <input
              type="range"
              min="0"
              max="5000"
              step="50"
              value={config.db_latency_max_ms}
              onChange={(e) => handleToggle('db_latency_max_ms', Number(e.target.value))}
              disabled={isSaving || !config.failure_injection_enabled}
              className="slider latency-max"
            />
          </div>
          <div className="range-labels">
            <span>0ms</span>
            <span>2.5s</span>
            <span>5s</span>
          </div>
        </div>

        {/* Timeouts */}
        <div className="control-group">
          <label>
            DB Timeout: {config.db_timeout_seconds}s
          </label>
          <input
            type="range"
            min="1"
            max="30"
            step="1"
            value={config.db_timeout_seconds}
            onChange={(e) => handleToggle('db_timeout_seconds', Number(e.target.value))}
            disabled={isSaving}
            className="slider timeout"
          />
        </div>

        <div className="control-group">
          <label>
            Redis Timeout: {config.redis_timeout_seconds}s
          </label>
          <input
            type="range"
            min="0.5"
            max="10"
            step="0.5"
            value={config.redis_timeout_seconds}
            onChange={(e) => handleToggle('redis_timeout_seconds', Number(e.target.value))}
            disabled={isSaving}
            className="slider timeout"
          />
        </div>

        {/* Max Retries */}
        <div className="control-group">
          <label>
            Max Retries: {config.max_retries}
          </label>
          <input
            type="range"
            min="0"
            max="10"
            step="1"
            value={config.max_retries}
            onChange={(e) => handleToggle('max_retries', Number(e.target.value))}
            disabled={isSaving}
            className="slider retries"
          />
        </div>
      </div>

      {/* Status Indicator */}
      <div className={`status-indicator ${config.failure_injection_enabled ? 'active' : 'inactive'}`}>
        <div className="status-dot"></div>
        <span>
          {config.failure_injection_enabled 
            ? `Failures active at ${(config.failure_rate * 100).toFixed(1)}% rate`
            : 'No failure injection'
          }
        </span>
      </div>

      {isSaving && (
        <div className="saving-indicator">
          Saving configuration...
        </div>
      )}
    </div>
  );
};