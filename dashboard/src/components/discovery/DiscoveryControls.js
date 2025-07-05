import React, { useState } from 'react';
import './DiscoveryControls.css';

const DiscoveryControls = ({
  selectedCommittees,
  onCommitteeChange,
  statusFilter,
  onStatusFilterChange,
  onDiscoveryRun,
  onRefresh,
  isLoading,
  lastDiscovery
}) => {
  const [showCommitteeSelect, setShowCommitteeSelect] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  const availableCommittees = [
    { code: 'SCOM', name: 'Commerce, Science, and Transportation' },
    { code: 'SSCI', name: 'Intelligence' },
    { code: 'SBAN', name: 'Banking, Housing, and Urban Affairs' },
    { code: 'SSJU', name: 'Judiciary' },
    { code: 'HELP', name: 'Health, Education, Labor and Pensions' },
    { code: 'SFRC', name: 'Foreign Relations' },
    { code: 'SAPP', name: 'Appropriations' },
    { code: 'SSVA', name: 'Veterans Affairs' }
  ];

  const handleCommitteeToggle = (committeeCode) => {
    if (selectedCommittees.includes(committeeCode)) {
      onCommitteeChange(selectedCommittees.filter(c => c !== committeeCode));
    } else {
      onCommitteeChange([...selectedCommittees, committeeCode]);
    }
  };

  const handleSelectAll = () => {
    if (selectedCommittees.length === availableCommittees.length) {
      onCommitteeChange([]);
    } else {
      onCommitteeChange(availableCommittees.map(c => c.code));
    }
  };

  const handleDiscoveryRun = async () => {
    setIsRunning(true);
    try {
      await onDiscoveryRun();
    } finally {
      setIsRunning(false);
    }
  };

  const formatLastDiscovery = (dateString) => {
    if (!dateString) return 'Never';
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMinutes = Math.floor((now - date) / (1000 * 60));
      
      if (diffMinutes < 1) return 'Just now';
      if (diffMinutes < 60) return `${diffMinutes} minutes ago`;
      if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)} hours ago`;
      return date.toLocaleDateString();
    } catch {
      return 'Unknown';
    }
  };

  return (
    <div className="discovery-controls">
      <div className="controls-section">
        <div className="control-group">
          <label className="control-label">Committee Selection</label>
          <div className="committee-selector">
            <button 
              className="committee-select-btn"
              onClick={() => setShowCommitteeSelect(!showCommitteeSelect)}
            >
              {selectedCommittees.length === 0 
                ? 'All Committees' 
                : selectedCommittees.length === 1 
                  ? `${selectedCommittees[0]}`
                  : `${selectedCommittees.length} Committees`
              }
              <span className="dropdown-arrow">▼</span>
            </button>
            
            {showCommitteeSelect && (
              <div className="committee-dropdown">
                <div className="committee-header">
                  <button 
                    className="select-all-btn"
                    onClick={handleSelectAll}
                  >
                    {selectedCommittees.length === availableCommittees.length 
                      ? 'Deselect All' 
                      : 'Select All'}
                  </button>
                </div>
                <div className="committee-options">
                  {availableCommittees.map(committee => (
                    <label key={committee.code} className="committee-option">
                      <input
                        type="checkbox"
                        checked={selectedCommittees.includes(committee.code)}
                        onChange={() => handleCommitteeToggle(committee.code)}
                      />
                      <span className="committee-code">{committee.code}</span>
                      <span className="committee-name">{committee.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="control-group">
          <label className="control-label">Status Filter</label>
          <select 
            value={statusFilter} 
            onChange={(e) => onStatusFilterChange(e.target.value)}
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

        <div className="control-group">
          <label className="control-label">Discovery Actions</label>
          <div className="action-buttons">
            <button
              className="btn-discovery"
              onClick={handleDiscoveryRun}
              disabled={isRunning || isLoading}
            >
              {isRunning ? 'Running Discovery...' : 'Run Discovery'}
            </button>
            <button
              className="btn-refresh"
              onClick={onRefresh}
              disabled={isLoading}
            >
              {isLoading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>
      </div>

      <div className="discovery-info">
        <div className="info-item">
          <span className="info-label">Last Discovery:</span>
          <span className="info-value">{formatLastDiscovery(lastDiscovery)}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Selected Committees:</span>
          <span className="info-value">
            {selectedCommittees.length === 0 
              ? 'All' 
              : selectedCommittees.join(', ')}
          </span>
        </div>
      </div>

      {/* Loading Indicator */}
      {isLoading && (
        <div className="discovery-loading">
          <div className="loading-spinner"></div>
          <div className="loading-text">
            {isRunning ? 'Running discovery...' : 'Loading hearings...'}
          </div>
        </div>
      )}
    </div>
  );
};

export default DiscoveryControls;