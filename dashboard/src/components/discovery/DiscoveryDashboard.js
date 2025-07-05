import React, { useState, useEffect } from 'react';
import HearingCard from './HearingCard';
import ProcessingStatus from './ProcessingStatus';
import DiscoveryControls from './DiscoveryControls';
import { useHearingDiscovery } from '../../hooks/useHearingDiscovery';
import { useHearingCapture } from '../../hooks/useHearingCapture';
import './DiscoveryDashboard.css';

const DiscoveryDashboard = () => {
  const [selectedCommittees, setSelectedCommittees] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds

  const {
    hearings,
    stats,
    isLoading,
    error,
    discoverHearings,
    refreshHearings,
    lastDiscovery
  } = useHearingDiscovery(selectedCommittees, statusFilter, refreshInterval);

  const {
    captureHearing,
    cancelProcessing,
    getProcessingProgress,
    activeProcesses
  } = useHearingCapture();

  const handleDiscoveryRun = async () => {
    try {
      await discoverHearings(selectedCommittees);
    } catch (err) {
      console.error('Discovery failed:', err);
    }
  };

  const handleCaptureHearing = async (hearingId) => {
    try {
      await captureHearing(hearingId);
    } catch (err) {
      console.error('Capture failed:', err);
    }
  };

  const handleCancelProcessing = async (hearingId) => {
    try {
      await cancelProcessing(hearingId);
    } catch (err) {
      console.error('Cancel failed:', err);
    }
  };

  const filteredHearings = hearings.filter(hearing => {
    if (statusFilter === 'all') return true;
    return hearing.status === statusFilter;
  });

  const getStatusColor = (status) => {
    const colors = {
      'discovered': '#4CAF50',
      'capture_requested': '#FF9800',
      'capturing': '#2196F3',
      'processing': '#9C27B0',
      'completed': '#4CAF50',
      'failed': '#F44336'
    };
    return colors[status] || '#9E9E9E';
  };

  return (
    <div className="discovery-dashboard">
      <div className="dashboard-header">
        <h1>Senate Hearing Discovery Dashboard</h1>
        <div className="dashboard-subtitle">
          Automated discovery with selective processing
        </div>
      </div>

      {/* Discovery Controls */}
      <DiscoveryControls
        selectedCommittees={selectedCommittees}
        onCommitteeChange={setSelectedCommittees}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        onDiscoveryRun={handleDiscoveryRun}
        onRefresh={refreshHearings}
        isLoading={isLoading}
        lastDiscovery={lastDiscovery}
      />

      {/* Stats Summary */}
      <div className="stats-summary">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-number">{stats.total_hearings || 0}</div>
            <div className="stat-label">Total Hearings</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.status_counts?.discovered || 0}</div>
            <div className="stat-label">Ready to Capture</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.active_processes || 0}</div>
            <div className="stat-label">Currently Processing</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.isvp_compatible || 0}</div>
            <div className="stat-label">ISVP Compatible</div>
          </div>
        </div>
      </div>

      {/* Processing Status */}
      {activeProcesses && Object.keys(activeProcesses).length > 0 && (
        <div className="processing-status-section">
          <h3>Active Processing</h3>
          <div className="processing-grid">
            {Object.entries(activeProcesses).map(([hearingId, progress]) => (
              <ProcessingStatus
                key={hearingId}
                hearingId={hearingId}
                progress={progress}
                onCancel={() => handleCancelProcessing(hearingId)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-banner">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Hearings Grid */}
      <div className="hearings-section">
        <div className="hearings-header">
          <h3>Discovered Hearings ({filteredHearings.length})</h3>
          <div className="hearings-filters">
            <select 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value)}
              className="status-filter"
            >
              <option value="all">All Status</option>
              <option value="discovered">Ready to Capture</option>
              <option value="capture_requested">Capture Requested</option>
              <option value="capturing">Capturing</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>

        {isLoading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <div>Loading hearings...</div>
          </div>
        ) : filteredHearings.length === 0 ? (
          <div className="no-hearings">
            <div className="no-hearings-message">
              {hearings.length === 0 
                ? "No hearings discovered yet. Click 'Run Discovery' to find hearings."
                : "No hearings match the current filter."}
            </div>
          </div>
        ) : (
          <div className="hearings-grid">
            {filteredHearings.map(hearing => (
              <HearingCard
                key={hearing.id}
                hearing={hearing}
                onCapture={() => handleCaptureHearing(hearing.id)}
                onCancel={() => handleCancelProcessing(hearing.id)}
                processingProgress={activeProcesses[hearing.id]}
                statusColor={getStatusColor(hearing.status)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DiscoveryDashboard;