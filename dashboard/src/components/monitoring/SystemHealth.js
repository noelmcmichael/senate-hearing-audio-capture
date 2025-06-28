import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Database, 
  Globe, 
  Cpu, 
  Wifi,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';

const SystemHealth = ({ onResolveAlert, onViewDetails }) => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchHealthData();
    
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchHealthData, 30000); // Refresh every 30 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchHealthData = async () => {
    try {
      const response = await fetch('/api/system/health?include_details=true');
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setHealthData(data);
      setLastUpdate(new Date());
      setError(null);
      
    } catch (err) {
      console.error('Error fetching health data:', err);
      setError(err.message);
      
      // Mock data for development
      setHealthData({
        overall_status: 'healthy',
        last_updated: new Date().toISOString(),
        sync_health: {
          overall_status: 'healthy',
          components: {
            congress_api: {
              status: 'healthy',
              committees: {
                'SCOM': { status: 'healthy', last_success: new Date().toISOString() },
                'SSCI': { status: 'warning', last_success: new Date(Date.now() - 3600000).toISOString() }
              },
              last_success: new Date().toISOString(),
              error_count: 0
            },
            committee_scraper: {
              status: 'healthy',
              committees: {
                'SCOM': { status: 'healthy', last_success: new Date().toISOString() },
                'SSJU': { status: 'healthy', last_success: new Date().toISOString() }
              },
              last_success: new Date().toISOString(),
              error_count: 1
            }
          }
        },
        pipeline_health: {
          discovery_rate: 95.3,
          capture_rate: 87.6,
          review_completion_rate: 78.9,
          total_hearings: 156,
          health_status: 'healthy'
        },
        alerts_summary: {
          total: 3,
          critical: 0,
          high: 1,
          medium: 2,
          low: 0
        },
        performance_metrics: {
          quality_metrics: {
            accuracy_score: 87.3,
            review_speed: 15.2
          },
          sync_performance: {
            congress_api: { success_rate: 96.5, attempts: 48 },
            committee_scraper: { success_rate: 89.2, attempts: 37 }
          }
        },
        recent_alerts: [
          {
            alert_id: '1',
            alert_type: 'sync_failure',
            severity: 'high',
            title: 'Committee Scraper Failed for SSCI',
            description: 'Unable to connect to Senate Intelligence Committee website',
            component: 'scraper',
            created_at: new Date(Date.now() - 1800000).toISOString(),
            auto_resolvable: false
          },
          {
            alert_id: '2',
            alert_type: 'quality_degradation',
            severity: 'medium',
            title: 'Transcript Accuracy Below Threshold',
            description: 'Speaker identification accuracy dropped to 82%',
            component: 'transcription',
            created_at: new Date(Date.now() - 7200000).toISOString(),
            auto_resolvable: true
          }
        ]
      });
      setLastUpdate(new Date());
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return '#10b981';
      case 'warning': return '#f59e0b';
      case 'error': return '#ef4444';
      case 'critical': return '#dc2626';
      case 'degraded': return '#f97316';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = (status, size = 20) => {
    const color = getStatusColor(status);
    switch (status) {
      case 'healthy':
        return <CheckCircle size={size} style={{ color }} />;
      case 'warning':
      case 'degraded':
        return <AlertTriangle size={size} style={{ color }} />;
      case 'error':
      case 'critical':
        return <XCircle size={size} style={{ color }} />;
      default:
        return <Minus size={size} style={{ color }} />;
    }
  };

  const getTrendIcon = (current, baseline) => {
    if (!baseline) return <Minus size={16} style={{ color: '#6b7280' }} />;
    
    const diff = current - baseline;
    if (Math.abs(diff) < 1) return <Minus size={16} style={{ color: '#6b7280' }} />;
    
    return diff > 0 
      ? <TrendingUp size={16} style={{ color: '#10b981' }} />
      : <TrendingDown size={16} style={{ color: '#ef4444' }} />;
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMinutes = Math.floor((now - time) / 60000);
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#dc2626';
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  if (loading && !healthData) {
    return (
      <div style={{ 
        padding: '2rem', 
        textAlign: 'center', 
        backgroundColor: '#1B1C20',
        color: '#FFFFFF' 
      }}>
        <div style={{ marginBottom: '1rem' }}>
          <Activity size={48} style={{ color: '#4ECDC4' }} />
        </div>
        <h3>Loading System Health...</h3>
        <p style={{ color: '#888' }}>Checking all system components</p>
      </div>
    );
  }

  if (error && !healthData) {
    return (
      <div style={{ 
        padding: '2rem', 
        textAlign: 'center', 
        backgroundColor: '#1B1C20',
        color: '#FFFFFF' 
      }}>
        <div style={{ marginBottom: '1rem' }}>
          <XCircle size={48} style={{ color: '#ef4444' }} />
        </div>
        <h3>Error Loading System Health</h3>
        <p style={{ color: '#ef4444', marginBottom: '1rem' }}>{error}</p>
        <button
          onClick={fetchHealthData}
          style={{
            backgroundColor: '#4ECDC4',
            color: '#1B1C20',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: '#1B1C20', color: '#FFFFFF', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ 
        padding: '1.5rem',
        borderBottom: '1px solid #333',
        backgroundColor: '#2A2B2F'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {getStatusIcon(healthData?.overall_status, 28)}
              System Health
            </h1>
            <div style={{
              backgroundColor: getStatusColor(healthData?.overall_status),
              color: '#FFFFFF',
              padding: '4px 12px',
              borderRadius: '12px',
              fontSize: '0.875rem',
              fontWeight: '500'
            }}>
              {healthData?.overall_status?.toUpperCase()}
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {lastUpdate && (
              <span style={{ color: '#888', fontSize: '0.875rem' }}>
                Last updated: {formatTimeAgo(lastUpdate)}
              </span>
            )}
            
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#888' }}>
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                style={{ accentColor: '#4ECDC4' }}
              />
              Auto-refresh
            </label>
            
            <button
              onClick={fetchHealthData}
              disabled={loading}
              style={{
                backgroundColor: loading ? '#333' : '#4ECDC4',
                color: loading ? '#888' : '#1B1C20',
                border: 'none',
                padding: '8px 12px',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              <RefreshCw size={16} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div style={{ padding: '1.5rem' }}>
        {/* Overview Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          {/* Sync Health */}
          <div style={{
            backgroundColor: '#2A2B2F',
            border: '1px solid #444',
            borderRadius: '8px',
            padding: '1.5rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Globe size={20} style={{ color: '#4ECDC4' }} />
              <h3 style={{ margin: 0 }}>Data Sync</h3>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              {getStatusIcon(healthData?.sync_health?.overall_status)}
              <span style={{ fontSize: '1.25rem', fontWeight: '500' }}>
                {healthData?.sync_health?.overall_status?.toUpperCase()}
              </span>
            </div>
            <div style={{ color: '#888', fontSize: '0.875rem' }}>
              {Object.keys(healthData?.sync_health?.components || {}).length} components monitored
            </div>
          </div>

          {/* Pipeline Health */}
          <div style={{
            backgroundColor: '#2A2B2F',
            border: '1px solid #444',
            borderRadius: '8px',
            padding: '1.5rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Cpu size={20} style={{ color: '#4ECDC4' }} />
              <h3 style={{ margin: 0 }}>Pipeline</h3>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              {getStatusIcon(healthData?.pipeline_health?.health_status)}
              <span style={{ fontSize: '1.25rem', fontWeight: '500' }}>
                {Math.round(healthData?.pipeline_health?.discovery_rate || 0)}% Discovery
              </span>
            </div>
            <div style={{ color: '#888', fontSize: '0.875rem' }}>
              {healthData?.pipeline_health?.total_hearings || 0} hearings processed
            </div>
          </div>

          {/* Active Alerts */}
          <div style={{
            backgroundColor: '#2A2B2F',
            border: '1px solid #444',
            borderRadius: '8px',
            padding: '1.5rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <AlertTriangle size={20} style={{ color: '#4ECDC4' }} />
              <h3 style={{ margin: 0 }}>Alerts</h3>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: '500' }}>
                {healthData?.alerts_summary?.total || 0}
              </span>
              <span style={{ color: '#888' }}>active</span>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.75rem' }}>
              {healthData?.alerts_summary?.critical > 0 && (
                <span style={{ color: getSeverityColor('critical') }}>
                  {healthData.alerts_summary.critical} critical
                </span>
              )}
              {healthData?.alerts_summary?.high > 0 && (
                <span style={{ color: getSeverityColor('high') }}>
                  {healthData.alerts_summary.high} high
                </span>
              )}
              {healthData?.alerts_summary?.medium > 0 && (
                <span style={{ color: getSeverityColor('medium') }}>
                  {healthData.alerts_summary.medium} medium
                </span>
              )}
            </div>
          </div>

          {/* Performance */}
          <div style={{
            backgroundColor: '#2A2B2F',
            border: '1px solid #444',
            borderRadius: '8px',
            padding: '1.5rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Activity size={20} style={{ color: '#4ECDC4' }} />
              <h3 style={{ margin: 0 }}>Performance</h3>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: '500' }}>
                {Math.round(healthData?.performance_metrics?.quality_metrics?.accuracy_score || 0)}%
              </span>
              <span style={{ color: '#888' }}>accuracy</span>
              {getTrendIcon(87.3, 85.0)}
            </div>
            <div style={{ color: '#888', fontSize: '0.875rem' }}>
              {Math.round(healthData?.performance_metrics?.quality_metrics?.review_speed || 0)}min avg review
            </div>
          </div>
        </div>

        {/* Component Details */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
          {/* Sync Components */}
          <div style={{
            backgroundColor: '#2A2B2F',
            border: '1px solid #444',
            borderRadius: '8px',
            padding: '1.5rem'
          }}>
            <h3 style={{ margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Wifi size={20} style={{ color: '#4ECDC4' }} />
              Sync Components
            </h3>
            
            {Object.entries(healthData?.sync_health?.components || {}).map(([component, data]) => (
              <div key={component} style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#1B1C20', borderRadius: '4px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {getStatusIcon(data.status, 16)}
                    <span style={{ fontWeight: '500', textTransform: 'capitalize' }}>
                      {component.replace('_', ' ')}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.875rem', color: '#888' }}>
                    {data.error_count} errors
                  </div>
                </div>
                
                {data.committees && (
                  <div style={{ fontSize: '0.875rem' }}>
                    <div style={{ color: '#888', marginBottom: '0.25rem' }}>Committees:</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                      {Object.entries(data.committees).map(([committee, status]) => (
                        <span
                          key={committee}
                          style={{
                            backgroundColor: getStatusColor(status.status),
                            color: '#FFFFFF',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontSize: '0.75rem'
                          }}
                        >
                          {committee}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {data.last_success && (
                  <div style={{ fontSize: '0.75rem', color: '#888', marginTop: '0.5rem' }}>
                    Last success: {formatTimeAgo(data.last_success)}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Recent Alerts */}
          <div style={{
            backgroundColor: '#2A2B2F',
            border: '1px solid #444',
            borderRadius: '8px',
            padding: '1.5rem'
          }}>
            <h3 style={{ margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertTriangle size={20} style={{ color: '#4ECDC4' }} />
              Recent Alerts
            </h3>
            
            {healthData?.recent_alerts?.length > 0 ? (
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                {healthData.recent_alerts.slice(0, 5).map(alert => (
                  <div key={alert.alert_id} style={{
                    padding: '1rem',
                    backgroundColor: '#1B1C20',
                    borderRadius: '4px',
                    border: `1px solid ${getSeverityColor(alert.severity)}`
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div style={{
                          width: '8px',
                          height: '8px',
                          borderRadius: '50%',
                          backgroundColor: getSeverityColor(alert.severity)
                        }} />
                        <span style={{ fontWeight: '500', fontSize: '0.875rem' }}>
                          {alert.title}
                        </span>
                      </div>
                      <span style={{
                        backgroundColor: getSeverityColor(alert.severity),
                        color: '#FFFFFF',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        textTransform: 'uppercase'
                      }}>
                        {alert.severity}
                      </span>
                    </div>
                    
                    <div style={{ fontSize: '0.875rem', color: '#888', marginBottom: '0.5rem' }}>
                      {alert.description}
                    </div>
                    
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
                      <span style={{ color: '#666' }}>
                        {alert.component} • {formatTimeAgo(alert.created_at)}
                      </span>
                      
                      {alert.auto_resolvable && (
                        <button
                          onClick={() => onResolveAlert && onResolveAlert(alert.alert_id)}
                          style={{
                            backgroundColor: '#4ECDC4',
                            color: '#1B1C20',
                            border: 'none',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '0.75rem'
                          }}
                        >
                          Auto-resolve
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#888' }}>
                <CheckCircle size={32} style={{ color: '#10b981', marginBottom: '0.5rem' }} />
                <div>No recent alerts</div>
                <div style={{ fontSize: '0.875rem' }}>System operating normally</div>
              </div>
            )}
          </div>
        </div>

        {/* Performance Metrics */}
        <div style={{
          backgroundColor: '#2A2B2F',
          border: '1px solid #444',
          borderRadius: '8px',
          padding: '1.5rem'
        }}>
          <h3 style={{ margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Database size={20} style={{ color: '#4ECDC4' }} />
            Performance Metrics
          </h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            {/* Pipeline Rates */}
            <div>
              <div style={{ color: '#888', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Pipeline Success Rates</div>
              <div style={{ display: 'grid', gap: '0.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Discovery:</span>
                  <span style={{ color: '#10b981' }}>{Math.round(healthData?.pipeline_health?.discovery_rate || 0)}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Capture:</span>
                  <span style={{ color: '#f59e0b' }}>{Math.round(healthData?.pipeline_health?.capture_rate || 0)}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Review:</span>
                  <span style={{ color: '#3b82f6' }}>{Math.round(healthData?.pipeline_health?.review_completion_rate || 0)}%</span>
                </div>
              </div>
            </div>

            {/* Sync Performance */}
            <div>
              <div style={{ color: '#888', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Sync Performance</div>
              <div style={{ display: 'grid', gap: '0.25rem' }}>
                {Object.entries(healthData?.performance_metrics?.sync_performance || {}).map(([component, perf]) => (
                  <div key={component} style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ textTransform: 'capitalize' }}>{component.replace('_', ' ')}:</span>
                    <span style={{ color: perf.success_rate > 90 ? '#10b981' : perf.success_rate > 75 ? '#f59e0b' : '#ef4444' }}>
                      {Math.round(perf.success_rate)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quality Metrics */}
            <div>
              <div style={{ color: '#888', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Quality Metrics</div>
              <div style={{ display: 'grid', gap: '0.25rem' }}>
                {Object.entries(healthData?.performance_metrics?.quality_metrics || {}).map(([metric, value]) => (
                  <div key={metric} style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ textTransform: 'capitalize' }}>{metric.replace('_', ' ')}:</span>
                    <span style={{ color: '#FFFFFF' }}>
                      {metric.includes('score') ? `${Math.round(value)}%` : `${Math.round(value)}min`}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <style>
        {`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default SystemHealth;