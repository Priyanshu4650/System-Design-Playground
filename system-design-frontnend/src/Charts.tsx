import React from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { type TestResult } from './types';

interface ChartsProps {
  testResult: TestResult;
}

const COLORS = {
  succeeded: '#10b981',
  failed: '#ef4444',
  rate_limited: '#f59e0b',
  duplicates: '#8b5cf6',
};

export function Charts({ testResult }: ChartsProps) {
  const statusData = [
    { name: 'Succeeded', value: testResult.succeeded, color: COLORS.succeeded },
    { name: 'Failed', value: testResult.failed, color: COLORS.failed },
    { name: 'Rate Limited', value: testResult.rate_limited, color: COLORS.rate_limited },
    { name: 'Duplicates', value: testResult.duplicates, color: COLORS.duplicates },
  ].filter(item => item.value > 0);

  const latencyData = [
    { name: 'Average', value: testResult.avg_latency_ms || 0 },
    { name: 'P95', value: testResult.p95_latency_ms || 0 },
    { name: 'P99', value: testResult.p99_latency_ms || 0 },
  ].filter(item => item.value > 0);

  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
    if (percent < 0.05) return null; // Don't show labels for slices < 5%
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize="12"
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '24px' }}>
      {/* Status Distribution Chart */}
      <div style={{ 
        backgroundColor: 'white', 
        padding: '20px', 
        borderRadius: '8px', 
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)' 
      }}>
        <h3 style={{ marginBottom: '16px', fontSize: '18px', fontWeight: '600', textAlign: 'center' }}>
          Request Status Distribution
        </h3>
        {statusData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderCustomizedLabel}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {statusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value: number) => [value.toLocaleString(), 'Requests']}
              />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ 
            height: '300px', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            color: '#6b7280'
          }}>
            No data available
          </div>
        )}
        
        {/* Legend */}
        <div style={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          justifyContent: 'center', 
          gap: '16px', 
          marginTop: '16px' 
        }}>
          {statusData.map((item) => (
            <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div 
                style={{ 
                  width: '12px', 
                  height: '12px', 
                  backgroundColor: item.color, 
                  borderRadius: '2px' 
                }} 
              />
              <span style={{ fontSize: '14px' }}>
                {item.name}: {item.value.toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Latency Chart */}
      <div style={{ 
        backgroundColor: 'white', 
        padding: '20px', 
        borderRadius: '8px', 
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)' 
      }}>
        <h3 style={{ marginBottom: '16px', fontSize: '18px', fontWeight: '600', textAlign: 'center' }}>
          Latency Distribution
        </h3>
        {latencyData.length > 0 && latencyData.some(d => d.value > 0) ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={latencyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis 
                tickFormatter={(value) => `${value}ms`}
              />
              <Tooltip 
                formatter={(value: number) => [`${value.toFixed(1)}ms`, 'Latency']}
              />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ 
            height: '300px', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            color: '#6b7280'
          }}>
            No latency data available
          </div>
        )}
      </div>
    </div>
  );
}