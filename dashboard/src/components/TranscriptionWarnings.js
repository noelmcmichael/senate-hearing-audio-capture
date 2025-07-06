import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Clock, 
  FileAudio, 
  Info,
  CheckCircle,
  X
} from 'lucide-react';
import './TranscriptionWarnings.css';

const TranscriptionWarnings = ({ hearing, onProceed, onCancel, isVisible = false }) => {
  const [audioInfo, setAudioInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isVisible && hearing?.id) {
      fetchAudioInfo();
    }
  }, [isVisible, hearing?.id]);

  const fetchAudioInfo = async () => {
    if (!hearing?.id) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Check if audio file exists and get size information
      const response = await fetch(`http://localhost:8001/api/hearings/${hearing.id}/audio/info`);
      
      if (response.ok) {
        const data = await response.json();
        setAudioInfo(data);
      } else {
        // If specific endpoint doesn't exist, make educated guess based on hearing data
        setAudioInfo(estimateAudioInfo(hearing));
      }
    } catch (err) {
      console.error('Failed to fetch audio info:', err);
      setAudioInfo(estimateAudioInfo(hearing));
    } finally {
      setIsLoading(false);
    }
  };

  const estimateAudioInfo = (hearing) => {
    // Make educated guesses based on hearing data
    const title = hearing?.hearing_title || '';
    const isLongHearing = title.toLowerCase().includes('full') || 
                         title.toLowerCase().includes('complete') ||
                         title.toLowerCase().includes('hearing');
    
    return {
      estimated: true,
      file_size_mb: isLongHearing ? 85 : 25, // Estimate based on title
      duration_minutes: isLongHearing ? 120 : 45,
      will_be_chunked: isLongHearing,
      estimated_chunks: isLongHearing ? 5 : 1,
      estimated_processing_time: isLongHearing ? 15 : 5
    };
  };

  const formatFileSize = (sizeMB) => {
    if (sizeMB >= 1000) {
      return `${(sizeMB / 1000).toFixed(1)} GB`;
    }
    return `${sizeMB.toFixed(1)} MB`;
  };

  const formatDuration = (minutes) => {
    if (minutes >= 60) {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      return `${hours}h ${remainingMinutes}m`;
    }
    return `${minutes}m`;
  };

  const getWarningLevel = () => {
    if (!audioInfo) return 'info';
    
    if (audioInfo.file_size_mb > 100) return 'high';
    if (audioInfo.file_size_mb > 50) return 'medium';
    if (audioInfo.will_be_chunked) return 'low';
    return 'info';
  };

  const getWarningIcon = (level) => {
    switch (level) {
      case 'high':
        return <AlertTriangle size={20} className="text-red-500" />;
      case 'medium':
        return <AlertTriangle size={20} className="text-orange-500" />;
      case 'low':
        return <Info size={20} className="text-blue-500" />;
      default:
        return <CheckCircle size={20} className="text-green-500" />;
    }
  };

  const getWarningMessage = (level) => {
    switch (level) {
      case 'high':
        return 'Large file detected - Extended processing time expected';
      case 'medium':
        return 'Medium file size - Chunked processing will be used';
      case 'low':
        return 'File will be processed in chunks for optimal results';
      default:
        return 'File size is optimal for direct processing';
    }
  };

  if (!isVisible) return null;

  return (
    <div className="transcription-warnings-overlay">
      <div className="transcription-warnings-modal">
        <div className="modal-header">
          <h3 className="modal-title">Transcription Preview</h3>
          <button 
            onClick={onCancel}
            className="modal-close"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        <div className="modal-content">
          {isLoading ? (
            <div className="loading-section">
              <div className="loading-spinner" />
              <p>Analyzing audio file...</p>
            </div>
          ) : error ? (
            <div className="error-section">
              <AlertTriangle size={20} className="text-red-500" />
              <p>Unable to analyze audio file: {error}</p>
            </div>
          ) : audioInfo ? (
            <>
              {/* File Information */}
              <div className="file-info-section">
                <div className="section-header">
                  <FileAudio size={18} />
                  <h4>Audio File Information</h4>
                  {audioInfo.estimated && (
                    <span className="estimated-badge">Estimated</span>
                  )}
                </div>
                
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">File Size:</span>
                    <span className="info-value">{formatFileSize(audioInfo.file_size_mb)}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Duration:</span>
                    <span className="info-value">{formatDuration(audioInfo.duration_minutes)}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Processing Method:</span>
                    <span className="info-value">
                      {audioInfo.will_be_chunked ? 'Chunked Processing' : 'Direct Processing'}
                    </span>
                  </div>
                  {audioInfo.will_be_chunked && (
                    <div className="info-item">
                      <span className="info-label">Expected Chunks:</span>
                      <span className="info-value">{audioInfo.estimated_chunks} chunks</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Warning Section */}
              <div className={`warning-section ${getWarningLevel()}`}>
                <div className="warning-header">
                  {getWarningIcon(getWarningLevel())}
                  <span>{getWarningMessage(getWarningLevel())}</span>
                </div>
                
                {audioInfo.will_be_chunked && (
                  <div className="chunking-details">
                    <h5>Chunked Processing Details:</h5>
                    <ul>
                      <li>Audio will be split into {audioInfo.estimated_chunks} chunks</li>
                      <li>Each chunk processed separately for reliability</li>
                      <li>Real-time progress tracking available</li>
                      <li>Automatic retry for failed chunks</li>
                    </ul>
                  </div>
                )}
              </div>

              {/* Time Estimate */}
              <div className="time-estimate-section">
                <div className="section-header">
                  <Clock size={18} />
                  <h4>Processing Time Estimate</h4>
                </div>
                
                <div className="time-details">
                  <div className="time-item">
                    <span className="time-label">Estimated Duration:</span>
                    <span className="time-value">
                      {formatDuration(audioInfo.estimated_processing_time)}
                    </span>
                  </div>
                  <div className="time-note">
                    <p className="text-sm text-gray-600">
                      Actual processing time may vary based on server load and audio complexity.
                      You can monitor progress in real-time during transcription.
                    </p>
                  </div>
                </div>
              </div>

              {/* Features Available */}
              <div className="features-section">
                <h4>Available Features:</h4>
                <div className="features-list">
                  <div className="feature-item">
                    <CheckCircle size={16} className="text-green-500" />
                    <span>Real-time progress tracking</span>
                  </div>
                  <div className="feature-item">
                    <CheckCircle size={16} className="text-green-500" />
                    <span>Automatic error recovery</span>
                  </div>
                  <div className="feature-item">
                    <CheckCircle size={16} className="text-green-500" />
                    <span>Chunk-level retry capability</span>
                  </div>
                  <div className="feature-item">
                    <CheckCircle size={16} className="text-green-500" />
                    <span>Cancellation support</span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="no-info-section">
              <Info size={20} className="text-blue-500" />
              <p>No audio information available. Proceeding with default settings.</p>
            </div>
          )}
        </div>

        <div className="modal-actions">
          <button 
            onClick={onCancel}
            className="btn btn-secondary"
          >
            Cancel
          </button>
          <button 
            onClick={() => onProceed(audioInfo)}
            className="btn btn-primary"
            disabled={isLoading}
          >
            {isLoading ? 'Analyzing...' : 'Start Transcription'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TranscriptionWarnings;