import React, { useState, useEffect, useCallback } from 'react';
import { RequestSummary, TraceResponse, TraceEvent } from '../types/api';
import { apiService } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';

export const RequestExplorer: React.FC = () => {
  const [requests, setRequests] = useState<RequestSummary[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<TraceResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingTrace, setIsLoadingTrace] = useState(false);
  const [error, setError] = useState<string>();

  // Load recent requests
  const loadRequests = useCallback(async () => {
    try {
      const response = await apiService.getRecentRequests(50);
      if (response.success && response.data && Array.isArray(response.data)) {
        setRequests(response.data);
        setError(undefined);
      } else {
        console.warn('API returned non-array data:', response.data);
        setRequests([]); // Ensure requests is always an array
        setError(response.error || 'Failed to load requests - endpoint may not exist');
      }
    } catch (err) {
      console.error('Network error:', err);
      setRequests([]); // Ensure requests is always an array
      setError('Network error loading requests');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle real-time request updates
  const handleWebSocketMessage = useCallback((message: any) => {
    if (message.type === 'request_update' && message.data) {
      setRequests(prev => {
        // Ensure prev is always an array
        const currentRequests = Array.isArray(prev) ? prev : [];
        const updated = [message.data, ...currentRequests];
        return updated.slice(0, 50); // Keep only latest 50
      });
    }
  }, []);

  const { isConnected } = useWebSocket({
    onMessage: handleWebSocketMessage
  });

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  // Load trace for selected request
  const loadTrace = useCallback(async (requestId: string) => {
    setIsLoadingTrace(true);
    try {
      const response = await apiService.getTrace(requestId);
      if (response.success && response.data) {
        setSelectedTrace(response.data);
      } else {
        console.error('Failed to load trace:', response.error);
      }
    } catch (err) {
      console.error('Error loading trace:', err);
    } finally {
      setIsLoadingTrace(false);
    }
  }, []);

  const closeTrace = () => {
    setSelectedTrace(null);
  };

  if (isLoading) {
    return <div className="request-explorer loading">Loading requests...</div>;
  }

  return (
    <div className="request-explorer">
      <div className="explorer-header">
        <h2>Request Explorer</h2>
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          <div className="status-dot"></div>
          {isConnected ? 'Live Updates' : 'Static'}
        </div>
      </div>

      {error && (
        <div className="error-banner">
          ⚠️ {error}
          <button onClick={loadRequests}>Retry</button>
        </div>
      )}

      <div className="requests-table">
        <div className="table-header">
          <div className="col-id">Request ID</div>
          <div className="col-status">Status</div>
          <div className="col-latency">Latency</div>
          <div className="col-retries">Retries</div>
          <div className="col-timestamp">Timestamp</div>
          <div className="col-endpoint">Endpoint</div>
        </div>

        <div className="table-body">
          {Array.isArray(requests) && requests.length > 0 ? (
            requests.map((request) => (
              <div 
                key={request.request_id} 
                className={`table-row ${getStatusClass(request.status)}`}
                onClick={() => loadTrace(request.request_id)}
              >
                <div className="col-id">
                  <span className="request-id">{request.request_id.slice(0, 8)}...</span>
                </div>
                <div className="col-status">
                  <span className={`status-badge status-${request.status}`}>
                    {request.status}
                  </span>
                </div>
                <div className="col-latency">
                  <span className={`latency ${getLatencyClass(request.latency_ms)}`}>
                    {request.latency_ms}ms
                  </span>
                </div>
                <div className="col-retries">
                  {request.retry_count > 0 && (
                    <span className="retry-badge">{request.retry_count}</span>
                  )}
                </div>
                <div className="col-timestamp">
                  {new Date(request.timestamp).toLocaleTimeString()}
                </div>
                <div className="col-endpoint">
                  <span className="method">{request.method}</span>
                  <span className="path">{request.endpoint}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="no-requests">
              {error ? 'Failed to load requests' : 'No requests found'}
            </div>
          )}
        </div>
      </div>

      {/* Trace Timeline Modal */}
      {selectedTrace && (
        <TraceTimeline 
          trace={selectedTrace} 
          isLoading={isLoadingTrace}
          onClose={closeTrace}
        />
      )}
    </div>
  );
};

// Trace Timeline Component
interface TraceTimelineProps {
  trace: TraceResponse;
  isLoading: boolean;
  onClose: () => void;
}

const TraceTimeline: React.FC<TraceTimelineProps> = ({ trace, isLoading, onClose }) => {
  if (isLoading) {
    return (
      <div className="trace-modal">
        <div className="trace-content loading">
          Loading trace timeline...
        </div>
      </div>
    );
  }

  const events = trace.trace.events.sort((a, b) => 
    new Date(a.timestamp_wall).getTime() - new Date(b.timestamp_wall).getTime()
  );

  return (
    <div className="trace-modal" onClick={onClose}>
      <div className="trace-content" onClick={(e) => e.stopPropagation()}>
        <div className="trace-header">
          <h3>Request Trace: {trace.trace.request_id}</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="trace-summary">
          <div className="summary-item">
            <span className="label">Total Latency:</span>
            <span className="value">{trace.trace.total_latency_ms?.toFixed(1)}ms</span>
          </div>
          <div className="summary-item">
            <span className="label">Status:</span>
            <span className={`value status-${trace.trace.status_code}`}>
              {trace.trace.status_code}
            </span>
          </div>
          <div className="summary-item">
            <span className="label">Events:</span>
            <span className="value">{trace.event_count}</span>
          </div>
          <div className="summary-item">
            <span className="label">Failures:</span>
            <span className="value failure">{trace.failure_points.length}</span>
          </div>
          <div className="summary-item">
            <span className="label">Retries:</span>
            <span className="value retry">{trace.retry_attempts.length}</span>
          </div>
        </div>

        <div className="timeline">
          {events.map((event, index) => (
            <TimelineEvent 
              key={event.event_id} 
              event={event} 
              isFirst={index === 0}
              isLast={index === events.length - 1}
              previousEvent={index > 0 ? events[index - 1] : undefined}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

// Timeline Event Component
interface TimelineEventProps {
  event: TraceEvent;
  isFirst: boolean;
  isLast: boolean;
  previousEvent?: TraceEvent;
}

const TimelineEvent: React.FC<TimelineEventProps> = ({ 
  event, 
  isFirst, 
  isLast, 
  previousEvent 
}) => {
  const duration = previousEvent 
    ? new Date(event.timestamp_wall).getTime() - new Date(previousEvent.timestamp_wall).getTime()
    : 0;

  const eventClass = getEventTypeClass(event.event_type);

  return (
    <div className={`timeline-event ${eventClass}`}>
      <div className="event-marker">
        <div className="event-dot"></div>
        {!isLast && <div className="event-line"></div>}
      </div>
      
      <div className="event-content">
        <div className="event-header">
          <span className="event-type">{event.event_type}</span>
          <span className="event-time">
            {new Date(event.timestamp_wall).toLocaleTimeString()}
          </span>
          {!isFirst && duration > 0 && (
            <span className="duration">+{duration}ms</span>
          )}
        </div>
        
        {Object.keys(event.metadata).length > 0 && (
          <div className="event-metadata">
            {Object.entries(event.metadata).map(([key, value]) => (
              <div key={key} className="metadata-item">
                <span className="key">{key}:</span>
                <span className="value">{JSON.stringify(value)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Helper functions
const getStatusClass = (status: number): string => {
  if (status >= 200 && status < 300) return 'success';
  if (status >= 400 && status < 500) return 'client-error';
  if (status >= 500) return 'server-error';
  return 'unknown';
};

const getLatencyClass = (latency: number): string => {
  if (latency < 100) return 'fast';
  if (latency < 500) return 'medium';
  return 'slow';
};

const getEventTypeClass = (eventType: string): string => {
  if (eventType.includes('failed') || eventType.includes('error')) return 'error';
  if (eventType.includes('retry')) return 'retry';
  if (eventType.includes('completed') || eventType.includes('success')) return 'success';
  return 'info';
};