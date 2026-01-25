import React, { useState } from 'react';

interface AdminStats {
  visit_stats: {
    total_visits: number;
    unique_visitors: number;
  };
  recent_visits: Array<{
    ip: string;
    user_agent: string;
    visited_at: string;
  }>;
  test_stats: {
    total_tests: number;
    completed_tests: number;
  };
}

export function AdminPage() {
  const [password, setPassword] = useState('');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`http://localhost:8000/v1/visits/admin?password=${encodeURIComponent(password)}`);
      const data = await response.json();
      
      if (data.error) {
        setError('Invalid password');
        setStats(null);
      } else {
        setStats(data);
        setError('');
      }
    } catch (err) {
      setError('Failed to fetch admin data');
    } finally {
      setLoading(false);
    }
  };

  if (!stats) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        backgroundColor: '#f3f4f6', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center' 
      }}>
        <div style={{ 
          backgroundColor: 'white', 
          padding: '32px', 
          borderRadius: '8px', 
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          minWidth: '400px'
        }}>
          <h1 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '24px', textAlign: 'center' }}>
            Admin Access
          </h1>
          
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600' }}>
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '16px'
                }}
                placeholder="Enter admin password"
              />
            </div>
            
            {error && (
              <div style={{ color: '#ef4444', fontSize: '14px', marginBottom: '16px' }}>
                {error}
              </div>
            )}
            
            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: loading ? '#9ca3af' : '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? 'Loading...' : 'Access Admin Panel'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#f3f4f6', 
      padding: '24px' 
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: 'bold', color: '#111827' }}>
            Admin Dashboard
          </h1>
          <button
            onClick={() => setStats(null)}
            style={{
              padding: '8px 16px',
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
          <button
            onClick={() => {
              const url = `http://localhost:8000/v1/visits/admin/download?password=${encodeURIComponent('admin123')}`;
              window.open(url);
            }}
            style={{
              padding: '8px 16px',
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Download Database
          </button>
        </div>

        {/* Stats Cards */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
          gap: '24px', 
          marginBottom: '32px' 
        }}>
          <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Visit Statistics</h3>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#3b82f6', marginBottom: '8px' }}>
              {stats.visit_stats.total_visits}
            </div>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>
              Total Visits
            </div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981', marginTop: '16px', marginBottom: '8px' }}>
              {stats.visit_stats.unique_visitors}
            </div>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>
              Unique Visitors
            </div>
          </div>

          <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Load Test Statistics</h3>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#8b5cf6', marginBottom: '8px' }}>
              {stats.test_stats.total_tests}
            </div>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>
              Total Tests
            </div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981', marginTop: '16px', marginBottom: '8px' }}>
              {stats.test_stats.completed_tests}
            </div>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>
              Completed Tests
            </div>
          </div>
        </div>

        {/* Recent Visits Table */}
        <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Recent Visits</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f9fafb' }}>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>IP Address</th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>User Agent</th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>Visit Time</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_visits.map((visit, index) => (
                  <tr key={index}>
                    <td style={{ padding: '12px', borderBottom: '1px solid #f3f4f6', fontFamily: 'monospace' }}>
                      {visit.ip}
                    </td>
                    <td style={{ padding: '12px', borderBottom: '1px solid #f3f4f6', fontSize: '14px' }}>
                      {visit.user_agent.length > 60 ? visit.user_agent.substring(0, 60) + '...' : visit.user_agent}
                    </td>
                    <td style={{ padding: '12px', borderBottom: '1px solid #f3f4f6' }}>
                      {new Date(visit.visited_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}