import React, { useState, useEffect } from 'react';
import { StatusIndicator, StatusManager } from '../status';
import './CommitteeDetail.css';

const CommitteeDetail = ({ committee, onBack }) => {
  const [hearings, setHearings] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('hearings');
  
  // Status management state
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [selectedHearing, setSelectedHearing] = useState(null);
  const [selectedHearings, setSelectedHearings] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    if (committee) {
      fetchCommitteeData();
    }
  }, [committee]);

  const fetchCommitteeData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch hearings and stats in parallel
      const [hearingsResponse, statsResponse] = await Promise.all([
        fetch(`http://localhost:8001/api/committees/${committee.code}/hearings`),
        fetch(`http://localhost:8001/api/committees/${committee.code}/stats`)
      ]);

      if (!hearingsResponse.ok || !statsResponse.ok) {
        throw new Error('Failed to fetch committee data');
      }

      const hearingsData = await hearingsResponse.json();
      const statsData = await statsResponse.json();
      
      setHearings(hearingsData.hearings || []);
      setStats(statsData.stats || {});
    } catch (err) {
      console.error('Error fetching committee data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatDateTime = (dateTimeString) => {
    return new Date(dateTimeString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return '#4CAF50';
    if (confidence >= 0.8) return '#FF9800';
    return '#f44336';
  };

  // Status management functions
  const handleStatusClick = (hearing) => {
    setSelectedHearing(hearing);
    setSelectedHearings([]);
    setStatusModalOpen(true);
  };

  const handleBulkStatusUpdate = () => {
    if (selectedHearings.length === 0) return;
    setSelectedHearing(null);
    setStatusModalOpen(true);
  };

  const handleStatusUpdate = (result) => {
    // Refresh committee data after status update
    fetchCommitteeData();
    setSelectedHearings([]);
  };

  const toggleHearingSelection = (hearingId) => {
    setSelectedHearings(prev => 
      prev.includes(hearingId) 
        ? prev.filter(id => id !== hearingId)
        : [...prev, hearingId]
    );
  };

  const getFilteredHearings = () => {
    if (statusFilter === 'all') return hearings;
    return hearings.filter(hearing => hearing.status === statusFilter);
  };

  if (!committee) {
    return <div className="committee-detail">No committee selected</div>;
  }

  if (loading) {
    return (
      <div className="committee-detail">
        <div className="committee-detail-header">
          <button className="btn-back" onClick={onBack}>← Back</button>
          <h2>Loading...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="committee-detail">
        <div className="committee-detail-header">
          <button className="btn-back" onClick={onBack}>← Back</button>
          <h2>Error</h2>
        </div>
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="committee-detail">
      <div className="committee-detail-header">
        <button className="btn-back" onClick={onBack}>← Back to Committees</button>
        <div className="committee-info">
          <h2>
            <span className="committee-code">{committee.code}</span>
            {committee.name}
          </h2>
          <div className="committee-meta">
            <span className="meta-item">
              <strong>{stats.total_hearings}</strong> Total Hearings
            </span>
            <span className="meta-item">
              <strong>{stats.recent_activity}</strong> Recent Activity
            </span>
            <span className="meta-item">
              Confidence: <strong style={{color: getConfidenceColor(stats.avg_confidence)}}>
                {Math.round(stats.avg_confidence * 100)}%
              </strong>
            </span>
          </div>
        </div>
      </div>

      <div className="tab-navigation">
        <button 
          className={`tab-button ${activeTab === 'hearings' ? 'active' : ''}`}
          onClick={() => setActiveTab('hearings')}
        >
          Hearings ({hearings.length})
        </button>
        <button 
          className={`tab-button ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          Statistics
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'hearings' && (
          <div className="hearings-tab">
            <div className="hearings-controls">
              <div className="status-filters">
                <label>Filter by Status:</label>
                <select 
                  value={statusFilter} 
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="status-filter-select"
                >
                  <option value="all">All Statuses</option>
                  <option value="new">New</option>
                  <option value="queued">Queued</option>
                  <option value="processing">Processing</option>
                  <option value="review">Review</option>
                  <option value="complete">Complete</option>
                  <option value="error">Error</option>
                </select>
              </div>
              
              {selectedHearings.length > 0 && (
                <div className="bulk-actions">
                  <span className="selection-count">
                    {selectedHearings.length} hearing{selectedHearings.length > 1 ? 's' : ''} selected
                  </span>
                  <button 
                    className="btn-bulk-action"
                    onClick={handleBulkStatusUpdate}
                  >
                    Update Status
                  </button>
                  <button 
                    className="btn-bulk-clear"
                    onClick={() => setSelectedHearings([])}
                  >
                    Clear Selection
                  </button>
                </div>
              )}
            </div>

            {getFilteredHearings().length === 0 ? (
              <div className="no-hearings">
                {statusFilter === 'all' 
                  ? 'No hearings found for this committee' 
                  : `No hearings with status '${statusFilter}'`
                }
              </div>
            ) : (
              <div className="hearings-list">
                {getFilteredHearings().map((hearing) => (
                  <div key={hearing.id} className="hearing-card">
                    <div className="hearing-selection">
                      <input
                        type="checkbox"
                        checked={selectedHearings.includes(hearing.id)}
                        onChange={() => toggleHearingSelection(hearing.id)}
                        className="hearing-checkbox"
                      />
                    </div>
                    
                    <div className="hearing-header">
                      <div className="hearing-title-row">
                        <h3 className="hearing-title">{hearing.title}</h3>
                        <div className="hearing-badges">
                          <div 
                            className="hearing-confidence"
                            style={{ backgroundColor: getConfidenceColor(hearing.sync_confidence) }}
                          >
                            {Math.round(hearing.sync_confidence * 100)}%
                          </div>
                        </div>
                      </div>
                      <div className="hearing-meta">
                        <span className="hearing-date">{formatDate(hearing.date)}</span>
                        <span className="hearing-type">{hearing.type}</span>
                      </div>
                    </div>
                    
                    <div className="hearing-status-section">
                      <StatusIndicator 
                        status={hearing.status || 'new'}
                        processing_stage={hearing.processing_stage || 'discovered'}
                        showStage={true}
                        clickable={true}
                        onClick={() => handleStatusClick(hearing)}
                      />
                      {hearing.assigned_reviewer && (
                        <div className="reviewer-info">
                          Reviewer: <span className="reviewer-name">{hearing.assigned_reviewer}</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="hearing-details">
                      <div className="detail-row">
                        <span className="detail-label">Streams:</span>
                        <span className="detail-value">
                          {Object.keys(hearing.streams || {}).join(', ') || 'None'}
                        </span>
                      </div>
                      <div className="detail-row">
                        <span className="detail-label">Status Updated:</span>
                        <span className="detail-value">
                          {hearing.status_updated_at ? formatDateTime(hearing.status_updated_at) : 'Never'}
                        </span>
                      </div>
                      {hearing.reviewer_notes && (
                        <div className="detail-row">
                          <span className="detail-label">Notes:</span>
                          <span className="detail-value">{hearing.reviewer_notes}</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="hearing-actions">
                      <button className="btn-action">View Details</button>
                      <button 
                        className="btn-action secondary"
                        onClick={() => handleStatusClick(hearing)}
                      >
                        Update Status
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="stats-tab">
            <div className="stats-grid">
              <div className="stat-card">
                <h4>Overview</h4>
                <div className="stat-items">
                  <div className="stat-item">
                    <span className="stat-label">Total Hearings:</span>
                    <span className="stat-value">{stats.total_hearings}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Earliest Hearing:</span>
                    <span className="stat-value">{formatDate(stats.earliest_hearing)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Latest Hearing:</span>
                    <span className="stat-value">{formatDate(stats.latest_hearing)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Avg Confidence:</span>
                    <span className="stat-value" style={{color: getConfidenceColor(stats.avg_confidence)}}>
                      {Math.round(stats.avg_confidence * 100)}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="stat-card">
                <h4>Hearing Types</h4>
                <div className="hearing-types">
                  {stats.hearing_types && stats.hearing_types.map((type, index) => (
                    <div key={index} className="hearing-type-item">
                      <span className="type-name">{type.type}</span>
                      <span className="type-count">{type.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="stat-card">
                <h4>Activity</h4>
                <div className="stat-items">
                  <div className="stat-item">
                    <span className="stat-label">Recent (30 days):</span>
                    <span className="stat-value">{stats.recent_activity}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Status Management Modal */}
      <StatusManager
        isOpen={statusModalOpen}
        onClose={() => setStatusModalOpen(false)}
        hearingIds={selectedHearings}
        currentHearing={selectedHearing}
        onStatusUpdate={handleStatusUpdate}
        bulkMode={selectedHearings.length > 0}
      />
    </div>
  );
};

export default CommitteeDetail;