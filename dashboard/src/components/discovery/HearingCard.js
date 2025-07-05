import React, { useState } from 'react';
import ProcessingStatus from './ProcessingStatus';
import './HearingCard.css';

const HearingCard = ({ 
  hearing, 
  onCapture, 
  onCancel, 
  processingProgress, 
  statusColor 
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);

  const handleCapture = async () => {
    setIsCapturing(true);
    try {
      await onCapture();
    } finally {
      setIsCapturing(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Date TBD';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  const formatTime = (timeString) => {
    if (!timeString) return '';
    return timeString;
  };

  const getMediaIndicators = () => {
    const indicators = [];
    if (hearing.isvp_compatible) indicators.push('ISVP');
    if (hearing.media_indicators?.youtube_url) indicators.push('YouTube');
    if (hearing.audio_available) indicators.push('Audio');
    return indicators;
  };

  const getQualityBadge = () => {
    const score = hearing.quality_score || 0;
    if (score >= 0.8) return { label: 'Excellent', color: '#4CAF50' };
    if (score >= 0.6) return { label: 'Good', color: '#FF9800' };
    if (score >= 0.4) return { label: 'Fair', color: '#FF5722' };
    return { label: 'Poor', color: '#F44336' };
  };

  const canCapture = hearing.status === 'discovered' && !processingProgress;
  const isProcessing = processingProgress || 
    ['capture_requested', 'capturing', 'processing'].includes(hearing.status);

  return (
    <div className="hearing-card">
      <div className="hearing-card-header">
        <div className="hearing-status-indicator" style={{ backgroundColor: statusColor }}>
          {hearing.status.replace('_', ' ').toUpperCase()}
        </div>
        <div className="hearing-committee-badge">
          {hearing.committee_code}
        </div>
      </div>

      <div className="hearing-card-content">
        <h3 className="hearing-title">{hearing.title}</h3>
        
        <div className="hearing-committee">
          {hearing.committee_name}
        </div>

        <div className="hearing-metadata">
          <div className="hearing-date">
            <span className="metadata-label">Date:</span>
            <span className="metadata-value">
              {formatDate(hearing.date)}
              {hearing.time && ` at ${formatTime(hearing.time)}`}
            </span>
          </div>

          <div className="hearing-quality">
            <span className="metadata-label">Quality:</span>
            <span 
              className="quality-badge"
              style={{ backgroundColor: getQualityBadge().color }}
            >
              {getQualityBadge().label}
            </span>
          </div>
        </div>

        <div className="hearing-media-indicators">
          {getMediaIndicators().map(indicator => (
            <span key={indicator} className="media-indicator">
              {indicator}
            </span>
          ))}
        </div>

        {hearing.description && (
          <div className="hearing-description">
            {hearing.description}
          </div>
        )}

        {hearing.witnesses && hearing.witnesses.length > 0 && (
          <div className="hearing-witnesses">
            <span className="metadata-label">Witnesses:</span>
            <div className="witness-count">{hearing.witnesses.length} witnesses</div>
          </div>
        )}

        {hearing.estimated_duration && (
          <div className="hearing-duration">
            <span className="metadata-label">Est. Duration:</span>
            <span className="metadata-value">{hearing.estimated_duration} minutes</span>
          </div>
        )}
      </div>

      {/* Processing Status */}
      {isProcessing && (
        <div className="hearing-processing">
          <ProcessingStatus
            hearingId={hearing.id}
            progress={processingProgress}
            onCancel={onCancel}
            compact={true}
          />
        </div>
      )}

      {/* Action Buttons */}
      <div className="hearing-card-actions">
        <button
          className="btn-details"
          onClick={() => setShowDetails(!showDetails)}
        >
          {showDetails ? 'Hide Details' : 'Show Details'}
        </button>

        {canCapture && (
          <button
            className="btn-capture"
            onClick={handleCapture}
            disabled={isCapturing}
          >
            {isCapturing ? 'Starting...' : 'Capture Hearing'}
          </button>
        )}

        {isProcessing && (
          <button
            className="btn-cancel"
            onClick={onCancel}
          >
            Cancel Processing
          </button>
        )}

        {hearing.status === 'completed' && (
          <button
            className="btn-view"
            onClick={() => window.open(`/hearings/${hearing.id}`, '_blank')}
          >
            View Results
          </button>
        )}
      </div>

      {/* Detailed Information */}
      {showDetails && (
        <div className="hearing-details">
          <div className="details-section">
            <h4>Technical Details</h4>
            <div className="detail-item">
              <span className="detail-label">URL:</span>
              <span className="detail-value">
                {hearing.url ? (
                  <a href={hearing.url} target="_blank" rel="noopener noreferrer">
                    {hearing.url}
                  </a>
                ) : 'Not available'}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Discovery Date:</span>
              <span className="detail-value">
                {formatDate(hearing.discovery_date)}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Processing Priority:</span>
              <span className="detail-value">{hearing.processing_priority}/10</span>
            </div>
          </div>

          {hearing.media_indicators && (
            <div className="details-section">
              <h4>Media Sources</h4>
              <div className="media-sources">
                {hearing.media_indicators.isvp_url && (
                  <div className="media-source">
                    <span className="source-type">ISVP:</span>
                    <span className="source-status">Available</span>
                  </div>
                )}
                {hearing.media_indicators.youtube_url && (
                  <div className="media-source">
                    <span className="source-type">YouTube:</span>
                    <span className="source-status">Available</span>
                  </div>
                )}
                {hearing.media_indicators.transcript_url && (
                  <div className="media-source">
                    <span className="source-type">Transcript:</span>
                    <span className="source-status">Available</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {hearing.witnesses && hearing.witnesses.length > 0 && (
            <div className="details-section">
              <h4>Witnesses</h4>
              <div className="witness-list">
                {hearing.witnesses.slice(0, 5).map((witness, index) => (
                  <div key={index} className="witness-item">
                    {witness}
                  </div>
                ))}
                {hearing.witnesses.length > 5 && (
                  <div className="witness-item">
                    +{hearing.witnesses.length - 5} more witnesses
                  </div>
                )}
              </div>
            </div>
          )}

          {hearing.topics && hearing.topics.length > 0 && (
            <div className="details-section">
              <h4>Topics</h4>
              <div className="topics-list">
                {hearing.topics.map((topic, index) => (
                  <span key={index} className="topic-tag">
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {hearing.error_message && (
            <div className="details-section">
              <h4>Error Information</h4>
              <div className="error-message">
                {hearing.error_message}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default HearingCard;