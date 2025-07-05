import React, { useState, useEffect } from 'react';
import './ProcessingStatus.css';

const ProcessingStatus = ({ 
  hearingId, 
  progress, 
  onCancel, 
  compact = false 
}) => {
  const [timeElapsed, setTimeElapsed] = useState(0);

  useEffect(() => {
    if (!progress) return;

    const startTime = new Date(progress.started_at);
    const updateElapsed = () => {
      const now = new Date();
      const elapsed = Math.floor((now - startTime) / 1000);
      setTimeElapsed(elapsed);
    };

    updateElapsed();
    const interval = setInterval(updateElapsed, 1000);

    return () => clearInterval(interval);
  }, [progress]);

  if (!progress) return null;

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStageIcon = (stage) => {
    const icons = {
      'capture_requested': '⏳',
      'capturing': '🎥',
      'converting': '🔄',
      'trimming': '✂️',
      'transcribing': '📝',
      'speaker_labeling': '👥',
      'completed': '✅',
      'failed': '❌'
    };
    return icons[stage] || '⏳';
  };

  const getStageLabel = (stage) => {
    const labels = {
      'capture_requested': 'Capture Requested',
      'capturing': 'Capturing Audio',
      'converting': 'Converting Audio',
      'trimming': 'Trimming Audio',
      'transcribing': 'Transcribing Audio',
      'speaker_labeling': 'Adding Speaker Labels',
      'completed': 'Completed',
      'failed': 'Failed'
    };
    return labels[stage] || stage.replace('_', ' ').toUpperCase();
  };

  const getProgressColor = (stage) => {
    const colors = {
      'capture_requested': '#FF9800',
      'capturing': '#2196F3',
      'converting': '#9C27B0',
      'trimming': '#3F51B5',
      'transcribing': '#FF5722',
      'speaker_labeling': '#795548',
      'completed': '#4CAF50',
      'failed': '#F44336'
    };
    return colors[stage] || '#9E9E9E';
  };

  if (compact) {
    return (
      <div className="processing-status compact">
        <div className="status-header">
          <div className="status-icon">
            {getStageIcon(progress.stage)}
          </div>
          <div className="status-info">
            <div className="status-stage">{getStageLabel(progress.stage)}</div>
            <div className="status-message">{progress.message}</div>
          </div>
        </div>
        
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ 
              width: `${progress.progress_percent}%`,
              backgroundColor: getProgressColor(progress.stage)
            }}
          />
        </div>
        
        <div className="status-details">
          <span className="time-elapsed">{formatTime(timeElapsed)}</span>
          <span className="progress-percent">{progress.progress_percent.toFixed(1)}%</span>
        </div>
      </div>
    );
  }

  return (
    <div className="processing-status">
      <div className="status-card">
        <div className="status-header">
          <div className="status-icon">
            {getStageIcon(progress.stage)}
          </div>
          <div className="status-info">
            <div className="status-title">
              Processing: {hearingId}
            </div>
            <div className="status-stage">
              {getStageLabel(progress.stage)}
            </div>
          </div>
          <div className="status-actions">
            {onCancel && progress.stage !== 'completed' && progress.stage !== 'failed' && (
              <button 
                className="btn-cancel-processing"
                onClick={onCancel}
                title="Cancel Processing"
              >
                Cancel
              </button>
            )}
          </div>
        </div>

        <div className="progress-section">
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ 
                width: `${progress.progress_percent}%`,
                backgroundColor: getProgressColor(progress.stage)
              }}
            />
          </div>
          <div className="progress-text">
            {progress.progress_percent.toFixed(1)}%
          </div>
        </div>

        <div className="status-message">
          {progress.message}
        </div>

        <div className="status-details">
          <div className="detail-item">
            <span className="detail-label">Started:</span>
            <span className="detail-value">
              {new Date(progress.started_at).toLocaleTimeString()}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Elapsed:</span>
            <span className="detail-value">{formatTime(timeElapsed)}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Stage Started:</span>
            <span className="detail-value">
              {new Date(progress.stage_started_at).toLocaleTimeString()}
            </span>
          </div>
          {progress.estimated_completion && (
            <div className="detail-item">
              <span className="detail-label">ETA:</span>
              <span className="detail-value">
                {new Date(progress.estimated_completion).toLocaleTimeString()}
              </span>
            </div>
          )}
        </div>

        {progress.details && (
          <div className="status-technical-details">
            <h4>Technical Details</h4>
            <pre>{JSON.stringify(progress.details, null, 2)}</pre>
          </div>
        )}

        {progress.error_message && (
          <div className="status-error">
            <h4>Error</h4>
            <div className="error-message">{progress.error_message}</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProcessingStatus;