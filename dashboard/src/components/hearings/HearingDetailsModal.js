import React, { useState, useEffect } from 'react';
import { 
  X, 
  Calendar, 
  Clock, 
  Users, 
  FileText, 
  ExternalLink, 
  CheckCircle, 
  AlertTriangle,
  PlayCircle,
  Download
} from 'lucide-react';
import PipelineStatusIndicator from '../status/PipelineStatusIndicator';

const HearingDetailsModal = ({ hearing, isOpen, onClose, onCapture, onViewTranscript }) => {
  const [isCapturing, setIsCapturing] = useState(false);
  const [captureResult, setCaptureResult] = useState(null);
  const [transcriptAvailable, setTranscriptAvailable] = useState(false);

  useEffect(() => {
    if (hearing && hearing.processing_stage) {
      // Check if transcript should be available based on pipeline stage
      setTranscriptAvailable(['transcribed', 'reviewed', 'published'].includes(hearing.processing_stage));
    }
  }, [hearing]);

  if (!isOpen || !hearing) {
    return null;
  }

  const handleCapture = async () => {
    if (!onCapture) {
      alert('Capture functionality not available');
      return;
    }

    setIsCapturing(true);
    setCaptureResult(null);

    try {
      const result = await onCapture(hearing.id);
      setCaptureResult({ success: true, message: 'Capture initiated successfully' });
    } catch (error) {
      setCaptureResult({ success: false, message: error.message || 'Capture failed' });
    } finally {
      setIsCapturing(false);
    }
  };

  const getStatusBadge = (status, stage) => {
    const statusColors = {
      'discovered': '#FFA500',
      'analyzed': '#4169E1', 
      'captured': '#32CD32',
      'transcribed': '#8A2BE2',
      'reviewed': '#00CED1',
      'published': '#00FF00'
    };

    const color = statusColors[stage] || '#888';
    
    return (
      <span style={{
        backgroundColor: color,
        color: '#FFFFFF',
        padding: '4px 12px',
        borderRadius: '16px',
        fontSize: '12px',
        fontWeight: 'bold'
      }}>
        {stage ? stage.charAt(0).toUpperCase() + stage.slice(1) : status}
      </span>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Not specified';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'Not specified';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return '#00FF00';
    if (confidence >= 0.7) return '#FFA500';
    return '#FF4444';
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: '#2A2B32',
        borderRadius: '12px',
        border: '1px solid #444',
        maxWidth: '800px',
        width: '100%',
        maxHeight: '90vh',
        overflow: 'auto',
        position: 'relative'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '20px',
          borderBottom: '1px solid #444'
        }}>
          <h2 style={{
            color: '#FFFFFF',
            margin: 0,
            fontSize: '18px',
            fontWeight: 'bold'
          }}>
            Hearing Details
          </h2>
          <button
            onClick={onClose}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              color: '#888',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '20px' }}>
          {/* Title and Status */}
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{
              color: '#FFFFFF',
              margin: '0 0 12px 0',
              fontSize: '16px',
              lineHeight: '1.4'
            }}>
              {hearing.hearing_title}
            </h3>
            <div style={{
              display: 'flex',
              gap: '12px',
              flexWrap: 'wrap',
              alignItems: 'center'
            }}>
              {getStatusBadge(hearing.status, hearing.processing_stage)}
              <span style={{
                color: '#888',
                fontSize: '14px'
              }}>
                ID: {hearing.id}
              </span>
            </div>
          </div>

          {/* Basic Information Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '20px',
            marginBottom: '24px'
          }}>
            {/* Committee */}
            <div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '8px'
              }}>
                <Users size={16} color="#4ECDC4" />
                <span style={{ color: '#4ECDC4', fontSize: '14px', fontWeight: 'bold' }}>
                  Committee
                </span>
              </div>
              <div style={{ color: '#FFFFFF', fontSize: '14px' }}>
                {hearing.committee_code}
              </div>
            </div>

            {/* Date */}
            <div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '8px'
              }}>
                <Calendar size={16} color="#4ECDC4" />
                <span style={{ color: '#4ECDC4', fontSize: '14px', fontWeight: 'bold' }}>
                  Hearing Date
                </span>
              </div>
              <div style={{ color: '#FFFFFF', fontSize: '14px' }}>
                {formatDate(hearing.hearing_date)}
              </div>
            </div>

            {/* Type */}
            <div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '8px'
              }}>
                <FileText size={16} color="#4ECDC4" />
                <span style={{ color: '#4ECDC4', fontSize: '14px', fontWeight: 'bold' }}>
                  Type
                </span>
              </div>
              <div style={{ color: '#FFFFFF', fontSize: '14px' }}>
                {hearing.hearing_type || 'Not specified'}
              </div>
            </div>

            {/* Duration */}
            {hearing.estimated_duration && (
              <div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '8px'
                }}>
                  <Clock size={16} color="#4ECDC4" />
                  <span style={{ color: '#4ECDC4', fontSize: '14px', fontWeight: 'bold' }}>
                    Duration
                  </span>
                </div>
                <div style={{ color: '#FFFFFF', fontSize: '14px' }}>
                  {Math.floor(hearing.estimated_duration / 60)}h {hearing.estimated_duration % 60}m (estimated)
                </div>
              </div>
            )}
          </div>

          {/* Participants */}
          {hearing.participant_list && (
            <div style={{ marginBottom: '24px' }}>
              <h4 style={{
                color: '#4ECDC4',
                fontSize: '14px',
                fontWeight: 'bold',
                margin: '0 0 8px 0'
              }}>
                Participants
              </h4>
              <div style={{ color: '#FFFFFF', fontSize: '14px', lineHeight: '1.4' }}>
                {hearing.participant_list}
              </div>
            </div>
          )}

          {/* Content Summary */}
          {hearing.content_summary && (
            <div style={{ marginBottom: '24px' }}>
              <h4 style={{
                color: '#4ECDC4',
                fontSize: '14px',
                fontWeight: 'bold',
                margin: '0 0 8px 0'
              }}>
                Summary
              </h4>
              <div style={{ color: '#FFFFFF', fontSize: '14px', lineHeight: '1.4' }}>
                {hearing.content_summary}
              </div>
            </div>
          )}

          {/* Pipeline Status */}
          <div style={{ marginBottom: '24px' }}>
            <h4 style={{
              color: '#4ECDC4',
              fontSize: '14px',
              fontWeight: 'bold',
              margin: '0 0 12px 0'
            }}>
              Processing Pipeline Status
            </h4>
            <PipelineStatusIndicator hearingId={hearing.id} />
          </div>

          {/* Technical Details */}
          <div style={{
            backgroundColor: '#1E1F25',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px'
          }}>
            <h4 style={{
              color: '#4ECDC4',
              fontSize: '14px',
              fontWeight: 'bold',
              margin: '0 0 12px 0'
            }}>
              Technical Information
            </h4>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px'
            }}>
              {/* Sync Confidence */}
              <div>
                <div style={{ color: '#888', fontSize: '12px', marginBottom: '4px' }}>
                  Sync Confidence
                </div>
                <div style={{
                  color: getConfidenceColor(hearing.sync_confidence),
                  fontSize: '14px',
                  fontWeight: 'bold'
                }}>
                  {Math.round(hearing.sync_confidence * 100)}%
                </div>
              </div>

              {/* Streams Available */}
              <div>
                <div style={{ color: '#888', fontSize: '12px', marginBottom: '4px' }}>
                  Streams Available
                </div>
                <div style={{
                  color: hearing.has_streams ? '#00FF00' : '#FF4444',
                  fontSize: '14px',
                  fontWeight: 'bold'
                }}>
                  {hearing.has_streams ? 'Yes' : 'No'}
                </div>
              </div>

              {/* Created */}
              <div>
                <div style={{ color: '#888', fontSize: '12px', marginBottom: '4px' }}>
                  Created
                </div>
                <div style={{ color: '#FFFFFF', fontSize: '14px' }}>
                  {formatDateTime(hearing.created_at)}
                </div>
              </div>

              {/* Last Updated */}
              <div>
                <div style={{ color: '#888', fontSize: '12px', marginBottom: '4px' }}>
                  Last Updated
                </div>
                <div style={{ color: '#FFFFFF', fontSize: '14px' }}>
                  {formatDateTime(hearing.updated_at)}
                </div>
              </div>
            </div>

            {/* Capture Readiness */}
            {hearing.capture_readiness && (
              <div style={{ marginTop: '16px' }}>
                <div style={{ color: '#888', fontSize: '12px', marginBottom: '8px' }}>
                  Capture Readiness
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <span style={{ 
                    backgroundColor: hearing.capture_readiness.score >= 0.7 ? '#00FF00' : '#FFA500',
                    color: '#000',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: 'bold'
                  }}>
                    Score: {Math.round(hearing.capture_readiness.score * 100)}%
                  </span>
                </div>
                <div style={{ color: '#FFFFFF', fontSize: '13px' }}>
                  {hearing.capture_readiness.factors.map((factor, index) => (
                    <div key={index} style={{ marginBottom: '2px' }}>
                      {factor}
                    </div>
                  ))}
                </div>
                <div style={{ 
                  color: '#4ECDC4', 
                  fontSize: '13px', 
                  fontStyle: 'italic',
                  marginTop: '8px'
                }}>
                  {hearing.capture_readiness.recommendation}
                </div>
              </div>
            )}
          </div>

          {/* Review Information */}
          {hearing.review_priority && (
            <div style={{
              backgroundColor: '#1E1F25',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '24px'
            }}>
              <h4 style={{
                color: '#4ECDC4',
                fontSize: '14px',
                fontWeight: 'bold',
                margin: '0 0 12px 0'
              }}>
                Review Information
              </h4>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: '16px'
              }}>
                <div>
                  <div style={{ color: '#888', fontSize: '12px', marginBottom: '4px' }}>
                    Priority
                  </div>
                  <div style={{ color: '#FFFFFF', fontSize: '14px' }}>
                    {hearing.review_priority}/10
                  </div>
                </div>
                
                {hearing.assigned_to && (
                  <div>
                    <div style={{ color: '#888', fontSize: '12px', marginBottom: '4px' }}>
                      Assigned To
                    </div>
                    <div style={{ color: '#FFFFFF', fontSize: '14px' }}>
                      {hearing.assigned_to}
                    </div>
                  </div>
                )}
                
                <div>
                  <div style={{ color: '#888', fontSize: '12px', marginBottom: '4px' }}>
                    Status
                  </div>
                  <div style={{ color: '#FFFFFF', fontSize: '14px' }}>
                    {hearing.review_status || 'Pending'}
                  </div>
                </div>
              </div>

              {hearing.reviewer_notes && (
                <div style={{ marginTop: '12px' }}>
                  <div style={{ color: '#888', fontSize: '12px', marginBottom: '4px' }}>
                    Notes
                  </div>
                  <div style={{ color: '#FFFFFF', fontSize: '14px', lineHeight: '1.4' }}>
                    {hearing.reviewer_notes}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Capture Result Feedback */}
          {captureResult && (
            <div style={{
              backgroundColor: captureResult.success ? '#00FF0020' : '#FF444420',
              borderRadius: '8px',
              padding: '12px',
              marginTop: '16px',
              border: `1px solid ${captureResult.success ? '#00FF00' : '#FF4444'}`
            }}>
              <div style={{
                color: captureResult.success ? '#00FF00' : '#FF4444',
                fontSize: '14px',
                fontWeight: 'bold'
              }}>
                {captureResult.success ? '✅ Success' : '❌ Error'}
              </div>
              <div style={{
                color: '#FFFFFF',
                fontSize: '13px',
                marginTop: '4px'
              }}>
                {captureResult.message}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div style={{
            display: 'flex',
            gap: '12px',
            justifyContent: 'flex-end',
            marginTop: '24px',
            borderTop: '1px solid #444',
            paddingTop: '16px'
          }}>
            {transcriptAvailable && (
              <button
                onClick={() => onViewTranscript && onViewTranscript(hearing.id)}
                style={{
                  backgroundColor: '#8A2BE2',
                  color: '#FFFFFF',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <FileText size={16} />
                View Transcript
              </button>
            )}

            {hearing.has_streams && hearing.processing_stage !== 'published' && (
              <button 
                onClick={handleCapture}
                disabled={isCapturing}
                style={{
                  backgroundColor: isCapturing ? '#666' : '#4ECDC4',
                  color: '#1B1C20',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  cursor: isCapturing ? 'not-allowed' : 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  opacity: isCapturing ? 0.7 : 1
                }}
              >
                <PlayCircle size={16} />
                {isCapturing ? 'Capturing...' : 'Capture Audio'}
              </button>
            )}

            {hearing.processing_stage === 'published' && (
              <div style={{
                color: '#00FF00',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <CheckCircle size={16} />
                Already Published
              </div>
            )}
            
            <button
              onClick={onClose}
              style={{
                backgroundColor: 'transparent',
                color: '#888',
                border: '1px solid #444',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HearingDetailsModal;