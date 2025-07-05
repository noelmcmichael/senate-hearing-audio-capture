import React, { useState, useEffect } from 'react';
import { Activity, Database, Server, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';

const AdminPage = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [bootstrapping, setBootstrapping] = useState(false);

  const fetchStatus = async () => {
    try {
      const response = await fetch('/admin/status');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching admin status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBootstrap = async () => {
    setBootstrapping(true);
    try {
      const response = await fetch('/admin/bootstrap', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Refresh status after successful bootstrap
        await fetchStatus();
        alert(`Bootstrap successful! Added ${data.committees_added} committees.`);
      } else {
        alert('Bootstrap failed: ' + (data.message || 'Unknown error'));
      }
    } catch (err) {
      alert('Bootstrap failed: ' + err.message);
    } finally {
      setBootstrapping(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        backgroundColor: '#1B1C20',
        color: '#FFFFFF'
      }}>
        <div style={{ textAlign: 'center' }}>
          <RefreshCw size={48} style={{ animation: 'spin 2s linear infinite', marginBottom: '16px' }} />
          <p>Loading admin status...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: '#1B1C20',
      color: '#FFFFFF',
      minHeight: '100vh',
      padding: '20px'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{
          marginBottom: '30px',
          textAlign: 'center',
          borderBottom: '2px solid #333',
          paddingBottom: '20px'
        }}>
          <h1 style={{
            fontSize: '2.5rem',
            fontWeight: '700',
            margin: '0 0 10px 0',
            color: '#4ECDC4'
          }}>
            Admin Dashboard
          </h1>
          <p style={{
            fontSize: '1.1rem',
            color: '#888',
            margin: '0'
          }}>
            System Status and Management
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div style={{
            backgroundColor: '#ff4444',
            color: '#fff',
            padding: '15px',
            borderRadius: '8px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}>
            <AlertCircle size={20} />
            <span>Error: {error}</span>
          </div>
        )}

        {/* Status Cards */}
        {status && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '20px',
            marginBottom: '30px'
          }}>
            {/* System Status Card */}
            <div style={{
              backgroundColor: '#2A2B32',
              border: '1px solid #444',
              borderRadius: '12px',
              padding: '20px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                <Server size={24} color="#4ECDC4" />
                <h3 style={{ margin: '0', color: '#4ECDC4' }}>System Status</h3>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle size={16} color={status.status === 'healthy' ? '#4CAF50' : '#FF6B6B'} />
                <span style={{ 
                  fontSize: '1.2rem',
                  fontWeight: '600',
                  color: status.status === 'healthy' ? '#4CAF50' : '#FF6B6B'
                }}>
                  {status.status || 'Unknown'}
                </span>
              </div>
            </div>

            {/* Database Status Card */}
            <div style={{
              backgroundColor: '#2A2B32',
              border: '1px solid #444',
              borderRadius: '12px',
              padding: '20px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                <Database size={24} color="#4ECDC4" />
                <h3 style={{ margin: '0', color: '#4ECDC4' }}>Database</h3>
              </div>
              <div style={{ color: '#888', fontSize: '14px', lineHeight: '1.5' }}>
                <div>Committees: <span style={{ color: '#FFFFFF', fontWeight: '600' }}>{status.committees || 0}</span></div>
                <div>Hearings: <span style={{ color: '#FFFFFF', fontWeight: '600' }}>{status.hearings || 0}</span></div>
                <div>Tables: <span style={{ color: status.tables_exist ? '#4CAF50' : '#FF6B6B', fontWeight: '600' }}>
                  {status.tables_exist ? 'Exist' : 'Missing'}
                </span></div>
              </div>
            </div>

            {/* Bootstrap Status Card */}
            <div style={{
              backgroundColor: '#2A2B32',
              border: '1px solid #444',
              borderRadius: '12px',
              padding: '20px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                <Activity size={24} color="#4ECDC4" />
                <h3 style={{ margin: '0', color: '#4ECDC4' }}>Bootstrap</h3>
              </div>
              <div style={{ color: '#888', fontSize: '14px', marginBottom: '15px' }}>
                Status: <span style={{ 
                  color: status.bootstrap_needed ? '#FF6B6B' : '#4CAF50',
                  fontWeight: '600'
                }}>
                  {status.bootstrap_needed ? 'Needed' : 'Complete'}
                </span>
              </div>
              <button
                onClick={handleBootstrap}
                disabled={bootstrapping}
                style={{
                  backgroundColor: status.bootstrap_needed ? '#4CAF50' : '#666',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '8px 16px',
                  fontSize: '14px',
                  cursor: bootstrapping ? 'not-allowed' : 'pointer',
                  opacity: bootstrapping ? 0.7 : 1,
                  transition: 'all 0.2s ease'
                }}
              >
                {bootstrapping ? 'Bootstrapping...' : 'Bootstrap System'}
              </button>
            </div>
          </div>
        )}

        {/* Actions */}
        <div style={{
          backgroundColor: '#2A2B32',
          border: '1px solid #444',
          borderRadius: '12px',
          padding: '20px'
        }}>
          <h3 style={{ margin: '0 0 15px 0', color: '#4ECDC4' }}>Actions</h3>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button
              onClick={fetchStatus}
              disabled={loading}
              style={{
                backgroundColor: '#333',
                color: '#FFFFFF',
                border: '1px solid #555',
                borderRadius: '6px',
                padding: '10px 20px',
                fontSize: '14px',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1,
                transition: 'all 0.2s ease'
              }}
            >
              {loading ? 'Refreshing...' : 'Refresh Status'}
            </button>
            
            <button
              onClick={() => window.location.href = '/'}
              style={{
                backgroundColor: '#4ECDC4',
                color: '#1B1C20',
                border: 'none',
                borderRadius: '6px',
                padding: '10px 20px',
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              Return to Dashboard
            </button>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          textAlign: 'center',
          marginTop: '30px',
          paddingTop: '20px',
          borderTop: '1px solid #333',
          color: '#888',
          fontSize: '14px'
        }}>
          <p>Senate Hearing Audio Capture - Admin Interface</p>
          <p>Last updated: {new Date().toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;