import React, { useState, useCallback } from 'react';
import { TrafficRequest, TrafficResult, RequestPayload } from '../types/api';
import { BackendTrafficResponse, validateTrafficResponse } from '../types/backend-contracts';
import { apiService } from '../services/api';

interface TrafficGeneratorProps {
  onResults: (results: TrafficResult[]) => void;
}

export const TrafficGenerator: React.FC<TrafficGeneratorProps> = ({ onResults }) => {
  const [mode, setMode] = useState<'single' | 'burst' | 'sustained'>('single');
  const [count, setCount] = useState(10);
  const [rps, setRps] = useState(5);
  const [duration, setDuration] = useState(30);
  const [isGenerating, setIsGenerating] = useState(false);
  const [results, setResults] = useState<TrafficResult[]>([]);
  const [error, setError] = useState<string>();

  const defaultPayload: RequestPayload = {
    rate_of_requests: 100,
    number_of_requests: 1000,
    retries_enabled: true,
    rate_limiting: 50,
    rate_limiting_algo: 'token_bucket',
    cache_enabled: true,
    cache_ttl: 300,
    db_latency: 50
  };

  const generateTraffic = useCallback(async () => {
    setIsGenerating(true);
    setResults([]);

    const request: TrafficRequest = {
      mode,
      ...(mode === 'burst' && { count }),
      ...(mode === 'sustained' && { rps, duration }),
      payload: defaultPayload
    };

    try {
      const response = await apiService.generateTraffic(request);
      
      if (response.success && response.data && validateTrafficResponse(response.data)) {
        const trafficResults = response.data.results;
        setResults(trafficResults);
        onResults(trafficResults);
        setError(undefined);
      } else {
        const errorMsg = response.error || 'Invalid response format from server';
        setError(errorMsg);
        console.error('Traffic generation failed:', errorMsg);
      }
    } catch (error) {
      const errorMsg = 'Network error during traffic generation';
      setError(errorMsg);
      console.error('Traffic generation error:', error);
    } finally {
      setIsGenerating(false);
    }
  }, [mode, count, rps, duration, onResults]);

  const stopTraffic = useCallback(async () => {
    try {
      await apiService.stopTraffic();
      setIsGenerating(false);
    } catch (error) {
      console.error('Failed to stop traffic:', error);
    }
  }, []);

  const successCount = Array.isArray(results) ? results.filter(r => r.status === 'success').length : 0;
  const failureCount = Array.isArray(results) ? results.filter(r => r.status === 'failure').length : 0;

  return (
    <div className="traffic-generator">
      <h2>Traffic Generator</h2>
      
      <div className="controls">
        <div className="mode-selector">
          <label>Mode:</label>
          <select value={mode} onChange={(e) => setMode(e.target.value as any)}>
            <option value="single">Single Request</option>
            <option value="burst">Burst Mode</option>
            <option value="sustained">Sustained Load</option>
          </select>
        </div>

        {mode === 'burst' && (
          <div className="burst-controls">
            <label>
              Count:
              <input 
                type="number" 
                value={count} 
                onChange={(e) => setCount(Number(e.target.value))}
                min="1"
                max="1000"
              />
            </label>
          </div>
        )}

        {mode === 'sustained' && (
          <div className="sustained-controls">
            <label>
              RPS:
              <input 
                type="number" 
                value={rps} 
                onChange={(e) => setRps(Number(e.target.value))}
                min="1"
                max="100"
              />
            </label>
            <label>
              Duration (s):
              <input 
                type="number" 
                value={duration} 
                onChange={(e) => setDuration(Number(e.target.value))}
                min="1"
                max="300"
              />
            </label>
          </div>
        )}

        <div className="action-buttons">
          <button 
            onClick={generateTraffic} 
            disabled={isGenerating}
            className="generate-btn"
          >
            {isGenerating ? 'Generating...' : 'Generate Traffic'}
          </button>
          
          {isGenerating && (
            <button onClick={stopTraffic} className="stop-btn">
              Stop
            </button>
          )}
        </div>
      </div>

      {Array.isArray(results) && results.length > 0 && (
        <div className="results">
          <h3>Results</h3>
          <div className="stats">
            <div className="stat success">
              <span className="label">Success:</span>
              <span className="value">{successCount}</span>
            </div>
            <div className="stat failure">
              <span className="label">Failure:</span>
              <span className="value">{failureCount}</span>
            </div>
            <div className="stat total">
              <span className="label">Total:</span>
              <span className="value">{results.length}</span>
            </div>
          </div>
          
          <div className="request-ids">
            <h4>Generated Request IDs:</h4>
            <div className="id-list">
              {results.slice(0, 10).map((result, index) => (
                <div key={index} className={`request-id ${result.status}`}>
                  <span className="id">{result.request_id}</span>
                  <span className="latency">{result.latency_ms}ms</span>
                </div>
              ))}
              {results.length > 10 && (
                <div className="more">... and {results.length - 10} more</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};