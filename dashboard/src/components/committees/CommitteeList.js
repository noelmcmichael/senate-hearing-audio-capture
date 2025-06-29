import React, { useState, useEffect } from 'react';
import './CommitteeList.css';

const CommitteeList = ({ onSelectCommittee }) => {
  const [committees, setCommittees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCommittees();
  }, []);

  const fetchCommittees = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8001/api/committees');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setCommittees(data.committees || []);
    } catch (err) {
      console.error('Error fetching committees:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return '#4CAF50'; // Green
    if (confidence >= 0.8) return '#FF9800'; // Orange
    return '#f44336'; // Red
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="committee-list">
        <div className="committee-list-header">
          <h2>Congressional Committees</h2>
        </div>
        <div className="loading">Loading committees...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="committee-list">
        <div className="committee-list-header">
          <h2>Congressional Committees</h2>
        </div>
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="committee-list">
      <div className="committee-list-header">
        <h2>Congressional Committees</h2>
        <div className="summary-stats">
          <span className="stat">
            <strong>{committees.length}</strong> Committees
          </span>
          <span className="stat">
            <strong>{committees.reduce((sum, c) => sum + c.hearing_count, 0)}</strong> Total Hearings
          </span>
        </div>
      </div>
      
      <div className="committee-grid">
        {committees.map((committee) => (
          <div
            key={committee.code}
            className="committee-card"
            onClick={() => onSelectCommittee && onSelectCommittee(committee)}
          >
            <div className="committee-header">
              <h3 className="committee-code">{committee.code}</h3>
              <div 
                className="confidence-indicator"
                style={{ backgroundColor: getConfidenceColor(committee.avg_confidence) }}
              >
                {Math.round(committee.avg_confidence * 100)}%
              </div>
            </div>
            
            <h4 className="committee-name">{committee.name}</h4>
            
            <div className="committee-stats">
              <div className="stat-row">
                <span className="stat-label">Hearings:</span>
                <span className="stat-value">{committee.hearing_count}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Latest:</span>
                <span className="stat-value">{formatDate(committee.latest_hearing)}</span>
              </div>
            </div>
            
            <div className="committee-actions">
              <button className="btn-primary">View Hearings</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CommitteeList;