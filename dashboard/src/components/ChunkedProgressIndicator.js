import React, { useState, useEffect } from 'react';
import { 
  Progress, 
  Clock, 
  FileAudio, 
  Loader, 
  CheckCircle, 
  AlertCircle,
  Play,
  RefreshCw
} from 'lucide-react';
import './ChunkedProgressIndicator.css';

const ChunkedProgressIndicator = ({ hearingId, isActive = false, onComplete = null }) => {
  const [progress, setProgress] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Poll for progress updates when active
  useEffect(() => {
    if (!isActive || !hearingId) return;

    const pollProgress = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(`http://localhost:8001/api/hearings/${hearingId}/transcription/progress`);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        
        if (data.success && data.detailed_progress) {
          setProgress(data.detailed_progress);
          setError(null);
          
          // Check if completed
          if (data.detailed_progress.stage === 'completed' && onComplete) {
            onComplete(true);
          } else if (data.detailed_progress.stage === 'failed' && onComplete) {
            onComplete(false, data.detailed_progress.error);
          }
        } else {
          setError(data.error || 'Failed to get progress data');
        }
      } catch (err) {
        setError(`Failed to fetch progress: ${err.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    // Initial poll
    pollProgress();
    
    // Set up polling interval
    const interval = setInterval(pollProgress, 3000); // Poll every 3 seconds
    
    return () => clearInterval(interval);
  }, [isActive, hearingId, onComplete]);

  const formatTime = (seconds) => {
    if (!seconds || seconds < 0) return null;
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes === 0) {
      return `${remainingSeconds}s`;
    } else if (minutes < 60) {
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      return `${hours}h ${remainingMinutes}m`;
    }
  };

  const getStageIcon = (stage) => {
    switch (stage) {
      case 'analyzing':
        return <FileAudio size={16} className="text-blue-500" />;
      case 'chunking':
        return <Play size={16} className="text-orange-500" />;
      case 'processing':
      case stage?.startsWith('processing_chunk') && stage:
        return <Loader size={16} className="text-blue-500 animate-spin" />;
      case 'merging':
        return <RefreshCw size={16} className="text-purple-500" />;
      case 'cleanup':
        return <CheckCircle size={16} className="text-green-500" />;
      case 'completed':
        return <CheckCircle size={16} className="text-green-500" />;
      case 'failed':
        return <AlertCircle size={16} className="text-red-500" />;
      default:
        return <Clock size={16} className="text-gray-500" />;
    }
  };

  const getStageDisplayName = (stage) => {
    if (stage?.startsWith('processing_chunk')) {
      return 'Processing Audio Chunks';
    }
    
    switch (stage) {
      case 'analyzing':
        return 'Analyzing Audio File';
      case 'chunking':
        return 'Creating Audio Chunks';
      case 'processing':
        return 'Transcribing Audio';
      case 'merging':
        return 'Merging Transcripts';
      case 'cleanup':
        return 'Cleaning Up';
      case 'completed':
        return 'Transcription Complete';
      case 'failed':
        return 'Transcription Failed';
      default:
        return stage || 'Unknown Stage';
    }
  };

  if (!isActive) {
    return null;
  }

  if (error) {
    return (
      <div className="chunked-progress-indicator error">
        <div className="flex items-center gap-2 text-red-600">
          <AlertCircle size={16} />
          <span className="font-medium">Progress Error</span>
        </div>
        <p className="text-sm text-red-500 mt-1">{error}</p>
      </div>
    );
  }

  if (!progress && isLoading) {
    return (
      <div className="chunked-progress-indicator loading">
        <div className="flex items-center gap-2 text-gray-600">
          <Loader size={16} className="animate-spin" />
          <span>Loading progress...</span>
        </div>
      </div>
    );
  }

  if (!progress) {
    return null;
  }

  const isChunkedProcessing = progress.is_chunked_processing || progress.chunk_progress;

  return (
    <div className="chunked-progress-indicator">
      {/* Overall Progress Header */}
      <div className="progress-header">
        <div className="flex items-center gap-2">
          {getStageIcon(progress.stage)}
          <span className="font-medium text-gray-800">
            {getStageDisplayName(progress.stage)}
          </span>
        </div>
        
        <div className="flex items-center gap-3 text-sm text-gray-600">
          <span className="font-medium">{progress.overall_progress}%</span>
          {progress.estimated_time_remaining && (
            <div className="flex items-center gap-1">
              <Clock size={14} />
              <span>{formatTime(progress.estimated_time_remaining)} remaining</span>
            </div>
          )}
        </div>
      </div>

      {/* Overall Progress Bar */}
      <div className="progress-bar-container">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${Math.max(0, Math.min(100, progress.overall_progress))}%` }}
          />
        </div>
      </div>

      {/* Progress Message */}
      <div className="progress-message">
        <p className="text-sm text-gray-600">{progress.message}</p>
      </div>

      {/* Chunked Processing Details */}
      {isChunkedProcessing && progress.chunk_progress && (
        <div className="chunk-progress">
          <div className="chunk-header">
            <span className="text-sm font-medium text-gray-700">
              Chunk Progress
            </span>
            <span className="text-sm text-gray-600">
              {progress.chunk_progress.current_chunk} of {progress.chunk_progress.total_chunks} chunks
            </span>
          </div>
          
          {/* Chunk Grid Visualization */}
          <div className="chunk-grid">
            {Array.from({ length: progress.chunk_progress.total_chunks }, (_, index) => {
              const chunkNum = index + 1;
              const isCurrentChunk = chunkNum === progress.chunk_progress.current_chunk;
              const isCompleted = chunkNum < progress.chunk_progress.current_chunk;
              
              let chunkStatus;
              if (isCompleted) {
                chunkStatus = 'completed';
              } else if (isCurrentChunk) {
                chunkStatus = 'processing';
              } else {
                chunkStatus = 'pending';
              }
              
              return (
                <div
                  key={chunkNum}
                  className={`chunk-indicator ${chunkStatus}`}
                  title={`Chunk ${chunkNum}: ${chunkStatus}`}
                >
                  <span className="chunk-number">{chunkNum}</span>
                  {isCurrentChunk && (
                    <div 
                      className="chunk-progress-fill"
                      style={{ width: `${progress.chunk_progress.chunk_progress}%` }}
                    />
                  )}
                </div>
              );
            })}
          </div>

          {/* Current Chunk Progress Bar */}
          {progress.chunk_progress.current_chunk <= progress.chunk_progress.total_chunks && (
            <div className="current-chunk-progress">
              <div className="flex justify-between items-center text-xs text-gray-600 mb-1">
                <span>Current Chunk {progress.chunk_progress.current_chunk}</span>
                <span>{progress.chunk_progress.chunk_progress}%</span>
              </div>
              <div className="chunk-progress-bar">
                <div 
                  className="chunk-progress-fill"
                  style={{ width: `${progress.chunk_progress.chunk_progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {progress.error && (
        <div className="error-display">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle size={14} />
            <span className="font-medium text-sm">Error</span>
          </div>
          <p className="text-sm text-red-500 mt-1">{progress.error}</p>
        </div>
      )}
    </div>
  );
};

export default ChunkedProgressIndicator;