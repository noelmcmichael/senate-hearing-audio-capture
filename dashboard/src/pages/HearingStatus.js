import React, { useState, useEffect } from 'react';
import { useOutletContext, useNavigate, useParams } from 'react-router-dom';
import { 
  Play, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  ArrowRight,
  RefreshCw,
  BarChart3
} from 'lucide-react';
import config from '../config';
import PipelineControls from '../components/PipelineControls';
import TranscriptDisplay from '../components/TranscriptDisplay';
import '../components/PipelineControls.css';

const HearingStatus = () => {
  const { hearing, transcript, refreshData } = useOutletContext();
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [isCapturing, setIsCapturing] = useState(false);
  const [captureResult, setCaptureResult] = useState(null);

  const pipelineStages = [
    { 
      id: 'discovered', 
      name: 'Discovered', 
      description: 'Hearing found and scheduled',
      icon: <AlertCircle size={20} />
    },
    { 
      id: 'analyzed', 
      name: 'Analyzed', 
      description: 'Metadata and streams analyzed',
      icon: <BarChart3 size={20} />
    },
    { 
      id: 'captured', 
      name: 'Audio Captured', 
      description: 'Audio successfully recorded',
      icon: <Play size={20} />
    },
    { 
      id: 'transcribed', 
      name: 'Transcribed', 
      description: 'Speech-to-text processing complete',
      icon: <Clock size={20} />
    },
    { 
      id: 'reviewed', 
      name: 'Reviewed', 
      description: 'Quality review and speaker identification',
      icon: <Clock size={20} />
    },
    { 
      id: 'published', 
      name: 'Published', 
      description: 'Final transcript published',
      icon: <CheckCircle size={20} />
    }
  ];

  const getStageStatus = (stageId) => {
    const currentStageIndex = pipelineStages.findIndex(s => s.id === hearing?.processing_stage);
    const stageIndex = pipelineStages.findIndex(s => s.id === stageId);
    
    if (stageIndex < currentStageIndex) return 'complete';
    if (stageIndex === currentStageIndex) return 'current';
    return 'pending';
  };

  const getStageColor = (status) => {
    switch (status) {
      case 'complete':
        return '#00FF00';
      case 'current':
        return '#4ECDC4';
      default:
        return '#444';
    }
  };

  const handleTriggerCapture = async () => {
    setIsCapturing(true);
    setCaptureResult(null);

    try {
      const response = await fetch(`${config.apiUrl}/hearings/${id}/capture?user_id=ui_user`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          hearing_id: String(id),
          priority: 1,
          user_id: 'ui_user'
        })
      });

      if (response.ok) {
        const result = await response.json();
        setCaptureResult({ 
          success: true, 
          message: 'Audio capture initiated successfully. Processing will begin shortly.' 
        });
        
        // Refresh data after a short delay
        setTimeout(() => {
          refreshData();
        }, 2000);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Capture request failed');
      }
    } catch (error) {
      setCaptureResult({ 
        success: false, 
        message: error.message || 'Failed to initiate capture' 
      });
    } finally {
      setIsCapturing(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'No date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return '#00FF00';
    if (confidence >= 0.7) return '#FFA500';
    return '#FF4444';
  };

  if (!hearing) {
    return (
      <div style={{ 
        textAlign: 'center', 
        color: '#888', 
        padding: '60px 20px',
        fontSize: '18px'
      }}>
        Loading hearing data...
      </div>
    );
  }

  const currentStageIndex = pipelineStages.findIndex(s => s.id === hearing.processing_stage);
  const progress = currentStageIndex >= 0 ? ((currentStageIndex + 1) / pipelineStages.length) * 100 : 0;

  return (
    <div>
      {/* Status Overview */}
      <div style={{
        backgroundColor: '#2A2B32',
        border: '1px solid #444',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '20px'
        }}>
          <div>
            <h2 style={{ color: '#FFFFFF', margin: '0 0 8px 0', fontSize: '20px' }}>
              Processing Status
            </h2>
            <div style={{ color: '#888', fontSize: '14px' }}>
              Current Stage: {hearing.processing_stage || 'Unknown'} • 
              {Math.round(progress)}% Complete
            </div>
          </div>

          <button
            onClick={refreshData}
            style={{
              backgroundColor: 'transparent',
              color: '#4ECDC4',
              border: '1px solid #4ECDC4',
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>

        {/* Progress Bar */}
        <div style={{
          backgroundColor: '#1B1C20',
          borderRadius: '4px',
          height: '12px',
          overflow: 'hidden',
          marginBottom: '20px'
        }}>
          <div style={{
            backgroundColor: '#4ECDC4',
            height: '100%',
            width: `${progress}%`,
            transition: 'width 0.3s ease'
          }} />
        </div>

        {/* Quick Actions */}
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {(hearing.has_streams || (hearing.streams && Object.keys(hearing.streams).length > 0)) && !['captured', 'transcribed', 'reviewed', 'published'].includes(hearing.processing_stage) && (
            <button
              onClick={handleTriggerCapture}
              disabled={isCapturing}
              style={{
                backgroundColor: isCapturing ? '#666' : '#4ECDC4',
                color: '#1B1C20',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '6px',
                cursor: isCapturing ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                opacity: isCapturing ? 0.7 : 1
              }}
            >
              <Play size={16} />
              {isCapturing ? 'Capturing...' : 'Trigger Capture'}
            </button>
          )}

          {transcript && (
            <button
              onClick={() => navigate(`/hearings/${id}`)}
              style={{
                backgroundColor: 'transparent',
                color: '#4ECDC4',
                border: '1px solid #4ECDC4',
                padding: '10px 20px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              View Transcript
              <ArrowRight size={16} />
            </button>
          )}
        </div>

        {/* Capture Result */}
        {captureResult && (
          <div style={{
            marginTop: '16px',
            padding: '12px',
            backgroundColor: captureResult.success ? '#00FF0020' : '#FF444420',
            border: `1px solid ${captureResult.success ? '#00FF00' : '#FF4444'}`,
            borderRadius: '6px'
          }}>
            <div style={{
              color: captureResult.success ? '#00FF00' : '#FF4444',
              fontSize: '14px',
              fontWeight: 'bold',
              marginBottom: '4px'
            }}>
              {captureResult.success ? '✅ Success' : '❌ Error'}
            </div>
            <div style={{ color: '#FFFFFF', fontSize: '14px' }}>
              {captureResult.message}
            </div>
          </div>
        )}
      </div>

      {/* Pipeline Controls - Enhanced Manual Controls */}
      <div style={{
        backgroundColor: '#2A2B32',
        border: '1px solid #444',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px'
      }}>
        <PipelineControls 
          hearing={hearing} 
          onStageChange={(newStage) => {
            // Refresh the hearing data when stage changes
            refreshData();
          }}
        />
      </div>

      {/* Technical Details */}
      <div style={{
        backgroundColor: '#2A2B32',
        border: '1px solid #444',
        borderRadius: '8px',
        padding: '20px'
      }}>
        <h3 style={{ color: '#FFFFFF', margin: '0 0 20px 0', fontSize: '18px' }}>
          Technical Details
        </h3>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '20px'
        }}>
          {/* Basic Info */}
          <div>
            <h4 style={{ color: '#4ECDC4', margin: '0 0 8px 0', fontSize: '14px' }}>
              Basic Information
            </h4>
            <div style={{ color: '#888', fontSize: '12px', lineHeight: '1.6' }}>
              <div><strong>ID:</strong> {hearing.id}</div>
              <div><strong>Type:</strong> {hearing.hearing_type || 'N/A'}</div>
              <div><strong>Date:</strong> {formatDate(hearing.hearing_date)}</div>
            </div>
          </div>

          {/* Sync Info */}
          <div>
            <h4 style={{ color: '#4ECDC4', margin: '0 0 8px 0', fontSize: '14px' }}>
              Synchronization
            </h4>
            <div style={{ color: '#888', fontSize: '12px', lineHeight: '1.6' }}>
              <div>
                <strong>Confidence:</strong> 
                <span style={{ 
                  color: getConfidenceColor(hearing.sync_confidence),
                  marginLeft: '4px'
                }}>
                  {Math.round((hearing.sync_confidence || 0) * 100)}%
                </span>
              </div>
              <div>
                <strong>Streams:</strong> {hearing.has_streams ? 'Available' : 'Not Available'}
              </div>
            </div>
          </div>

          {/* Timestamps */}
          <div>
            <h4 style={{ color: '#4ECDC4', margin: '0 0 8px 0', fontSize: '14px' }}>
              Timestamps
            </h4>
            <div style={{ color: '#888', fontSize: '12px', lineHeight: '1.6' }}>
              <div><strong>Created:</strong> {new Date(hearing.created_at).toLocaleString()}</div>
              <div><strong>Updated:</strong> {new Date(hearing.updated_at).toLocaleString()}</div>
            </div>
          </div>

          {/* Transcript Info */}
          {transcript && (
            <div>
              <h4 style={{ color: '#4ECDC4', margin: '0 0 8px 0', fontSize: '14px' }}>
                Transcript
              </h4>
              <div style={{ color: '#888', fontSize: '12px', lineHeight: '1.6' }}>
                <div><strong>Segments:</strong> {transcript.segments?.length || 0}</div>
                <div>
                  <strong>Confidence:</strong> 
                  <span style={{ 
                    color: getConfidenceColor(transcript.confidence),
                    marginLeft: '4px'
                  }}>
                    {Math.round((transcript.confidence || 0) * 100)}%
                  </span>
                </div>
                <div><strong>Processed:</strong> {new Date(transcript.processed_at).toLocaleString()}</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Transcript Display */}
      <TranscriptDisplay hearing={hearing} />
    </div>
  );
};

export default HearingStatus;