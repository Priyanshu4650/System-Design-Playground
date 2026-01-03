import React, { useState } from 'react';
import { TrafficGenerator } from './components/TrafficGenerator';
import { FailureToggles } from './components/FailureToggles';
import { MetricsCharts } from './components/MetricsCharts';
import { RequestExplorer } from './components/RequestExplorer';
import { TrafficResult } from './types/api';
import './App.css';

type ActiveTab = 'traffic' | 'failures' | 'metrics' | 'explorer';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('traffic');
  const [recentResults, setRecentResults] = useState<TrafficResult[]>([]);

  const handleTrafficResults = (results: TrafficResult[]) => {
    setRecentResults(results);
    // Auto-switch to metrics after generating traffic
    if (results.length > 0) {
      setTimeout(() => setActiveTab('metrics'), 1000);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>System Design Control Plane</h1>
        <div className="header-status">
          <div className="status-item">
            <span className="label">Recent Requests:</span>
            <span className="value">{recentResults.length}</span>
          </div>
          <div className="status-item">
            <span className="label">Success Rate:</span>
            <span className="value">
              {recentResults.length > 0 
                ? `${((recentResults.filter(r => r.status === 'success').length / recentResults.length) * 100).toFixed(1)}%`
                : 'N/A'
              }
            </span>
          </div>
        </div>
      </header>

      <nav className="app-nav">
        <button 
          className={`nav-tab ${activeTab === 'traffic' ? 'active' : ''}`}
          onClick={() => setActiveTab('traffic')}
        >
          <span className="tab-icon">🚀</span>
          Traffic Control
        </button>
        
        <button 
          className={`nav-tab ${activeTab === 'failures' ? 'active' : ''}`}
          onClick={() => setActiveTab('failures')}
        >
          <span className="tab-icon">⚠️</span>
          Failure Injection
        </button>
        
        <button 
          className={`nav-tab ${activeTab === 'metrics' ? 'active' : ''}`}
          onClick={() => setActiveTab('metrics')}
        >
          <span className="tab-icon">📊</span>
          Metrics
        </button>
        
        <button 
          className={`nav-tab ${activeTab === 'explorer' ? 'active' : ''}`}
          onClick={() => setActiveTab('explorer')}
        >
          <span className="tab-icon">🔍</span>
          Request Explorer
        </button>
      </nav>

      <main className="app-main">
        <div className={`tab-content ${activeTab === 'traffic' ? 'active' : ''}`}>
          <TrafficGenerator onResults={handleTrafficResults} />
        </div>

        <div className={`tab-content ${activeTab === 'failures' ? 'active' : ''}`}>
          <FailureToggles />
        </div>

        <div className={`tab-content ${activeTab === 'metrics' ? 'active' : ''}`}>
          <MetricsCharts />
        </div>

        <div className={`tab-content ${activeTab === 'explorer' ? 'active' : ''}`}>
          <RequestExplorer />
        </div>
      </main>

      {/* Global Status Bar */}
      <footer className="app-footer">
        <div className="footer-content">
          <div className="connection-indicators">
            <div className="indicator">
              <span className="dot backend"></span>
              Backend API
            </div>
            <div className="indicator">
              <span className="dot websocket"></span>
              Real-time Updates
            </div>
          </div>
          
          <div className="footer-actions">
            <button 
              className="emergency-stop"
              onClick={() => {
                // Emergency stop all traffic
                console.log('Emergency stop triggered');
              }}
            >
              🛑 Emergency Stop
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;