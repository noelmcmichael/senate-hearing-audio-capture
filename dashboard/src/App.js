import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Activity, CheckCircle, Clock, HardDrive, Zap, TrendingUp } from 'lucide-react';

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      // For development, use mock data if API not available
      const mockData = {
        summary: {
          total_extractions: 5,
          successful_extractions: 5,
          success_rate: 100.0,
          total_duration_hours: 8.2,
          total_size_gb: 0.85,
          avg_compression_ratio: 86.3
        },
        committee_stats: {
          'Commerce': 5
        },
        recent_extractions: [
          {
            timestamp: '20250627_144654',
            hearing_name: 'Finding Nemo S Future Conflicts Over Ocean Resources',
            committee: 'Commerce',
            duration_minutes: 110.6,
            file_size_mb: 151.9,
            format: 'mp3',
            success: true
          },
          {
            timestamp: '20250627_144128',
            hearing_name: 'On The Right Track Modernizing Americas Rail Network',
            committee: 'Commerce',
            duration_minutes: 101.9,
            file_size_mb: 139.9,
            format: 'mp3',
            success: true
          },
          {
            timestamp: '20250627_143443',
            hearing_name: 'Executive Session 12',
            committee: 'Commerce',
            duration_minutes: 46.9,
            file_size_mb: 64.5,
            format: 'mp3',
            success: true
          }
        ],
        last_updated: new Date().toISOString()
      };

      setData(mockData);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp || timestamp === 'unknown') return 'Unknown';
    
    const year = timestamp.substring(0, 4);
    const month = timestamp.substring(4, 6);
    const day = timestamp.substring(6, 8);
    const hour = timestamp.substring(9, 11);
    const minute = timestamp.substring(11, 13);
    
    return `${month}/${day}/${year} ${hour}:${minute}`;
  };

  const formatDuration = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  if (loading) {
    return (
      <div className="container">
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <Activity size={48} style={{ color: '#10b981', marginBottom: '1rem' }} />
          <h2>Loading Dashboard...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <h2 style={{ color: '#ef4444' }}>Error Loading Dashboard</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const { summary, committee_stats, recent_extractions } = data;

  // Prepare chart data
  const committeeChartData = Object.entries(committee_stats).map(([name, count]) => ({
    name,
    extractions: count
  }));

  const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444'];

  return (
    <div className="container">
      <div className="header">
        <h1>🏛️ Senate Hearing Audio Capture</h1>
        <p>Real-time monitoring of ISVP stream extractions</p>
        <p style={{ fontSize: '0.9rem', color: '#64748b' }}>
          Last updated: {new Date(data.last_updated).toLocaleString()}
        </p>
      </div>

      {/* Summary Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{summary.total_extractions}</div>
          <div className="stat-label">
            <Activity size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
            Total Extractions
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: '#10b981' }}>{summary.success_rate}%</div>
          <div className="stat-label">
            <CheckCircle size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
            Success Rate
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{summary.total_duration_hours}h</div>
          <div className="stat-label">
            <Clock size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
            Total Audio
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{summary.total_size_gb} GB</div>
          <div className="stat-label">
            <HardDrive size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
            Storage Used
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: '#a78bfa' }}>{summary.avg_compression_ratio}%</div>
          <div className="stat-label">
            <Zap size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
            Compression
          </div>
        </div>
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="card">
          <h3 style={{ margin: '0 0 1rem 0', color: '#f1f5f9' }}>
            <TrendingUp size={20} style={{ display: 'inline', marginRight: '0.5rem' }} />
            Extractions by Committee
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={committeeChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: '1px solid #334155', 
                  borderRadius: '8px',
                  color: '#e2e8f0'
                }} 
              />
              <Bar dataKey="extractions" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 style={{ margin: '0 0 1rem 0', color: '#f1f5f9' }}>Committee Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={committeeChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="extractions"
              >
                {committeeChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: '1px solid #334155', 
                  borderRadius: '8px',
                  color: '#e2e8f0'
                }} 
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Extractions Table */}
      <div className="card">
        <h3 style={{ margin: '0 0 1rem 0', color: '#f1f5f9' }}>Recent Extractions</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Hearing</th>
              <th>Committee</th>
              <th>Duration</th>
              <th>Size</th>
              <th>Format</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {recent_extractions.map((extraction, index) => (
              <tr key={index}>
                <td className="duration">{formatTimestamp(extraction.timestamp)}</td>
                <td>{extraction.hearing_name}</td>
                <td>
                  <span className="committee-tag">{extraction.committee}</span>
                </td>
                <td className="duration">{formatDuration(extraction.duration_minutes)}</td>
                <td className="file-size">{extraction.file_size_mb} MB</td>
                <td>{extraction.format.toUpperCase()}</td>
                <td>
                  <span className={extraction.success ? 'status-success' : 'status-error'}>
                    {extraction.success ? '✅ Success' : '❌ Failed'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Dashboard;