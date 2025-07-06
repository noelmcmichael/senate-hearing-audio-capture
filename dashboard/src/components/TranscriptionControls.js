import React, { useState } from 'react';
import { 
  StopCircle, 
  RefreshCw, 
  AlertTriangle,
  CheckCircle,
  Play,
  Pause
} from 'lucide-react';
import './TranscriptionControls.css';

const TranscriptionControls = ({ 
  hearingId, 
  isProcessing = false, 
  canCancel = true,
  canRetry = false,
  onCancel,
  onRetry,
  progress = null
}) => {
  const [isCancelling, setIsCancelling] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  const handleCancel = async () => {
    if (!hearingId || !onCancel || isCancelling) return;
    
    const confirmed = window.confirm(
      'Are you sure you want to cancel the transcription? This will stop the current process.'
    );
    
    if (!confirmed) return;
    
    setIsCancelling(true);
    
    try {
      await onCancel(hearingId);
    } catch (error) {
      console.error('Failed to cancel transcription:', error);
      alert('Failed to cancel transcription: ' + error.message);
    } finally {
      setIsCancelling(false);
    }
  };

  const handleRetry = async () => {
    if (!hearingId || !onRetry || isRetrying) return;
    
    setIsRetrying(true);
    
    try {
      await onRetry(hearingId);
    } catch (error) {
      console.error('Failed to retry transcription:', error);
      alert('Failed to retry transcription: ' + error.message);
    } finally {
      setIsRetrying(false);
    }
  };

  const getControlsMessage = () => {
    if (isCancelling) return 'Cancelling transcription...';
    if (isRetrying) return 'Retrying transcription...';
    if (isProcessing) return 'Transcription in progress - You can cancel if needed';
    if (canRetry) return 'Transcription failed - Click retry to try again';
    return 'Transcription controls';
  };

  const getStatusIcon = () => {
    if (isCancelling) {
      return <RefreshCw size={16} className="animate-spin text-orange-500" />;
    }
    if (isRetrying) {
      return <RefreshCw size={16} className="animate-spin text-blue-500" />;
    }
    if (isProcessing) {
      return <Play size={16} className="text-blue-500" />;
    }
    if (canRetry) {
      return <AlertTriangle size={16} className="text-red-500" />;
    }
    return <CheckCircle size={16} className="text-green-500" />;
  };

  // Don't show controls if no actions are available
  if (!isProcessing && !canRetry && !canCancel) {
    return null;
  }

  return (
    <div className="transcription-controls">
      <div className="controls-header">
        <div className="controls-status">
          {getStatusIcon()}
          <span className="status-message">{getControlsMessage()}</span>
        </div>
      </div>

      <div className="controls-actions">
        {/* Cancel Button */}
        {isProcessing && canCancel && (
          <button
            onClick={handleCancel}
            disabled={isCancelling || isRetrying}
            className="control-btn cancel-btn"
            title="Cancel transcription"
          >
            {isCancelling ? (
              <>
                <RefreshCw size={16} className="animate-spin" />
                Cancelling...
              </>
            ) : (
              <>
                <StopCircle size={16} />
                Cancel
              </>
            )}
          </button>
        )}

        {/* Retry Button */}
        {canRetry && !isProcessing && (
          <button
            onClick={handleRetry}
            disabled={isCancelling || isRetrying}
            className="control-btn retry-btn"
            title="Retry transcription"
          >
            {isRetrying ? (
              <>
                <RefreshCw size={16} className="animate-spin" />
                Retrying...
              </>
            ) : (
              <>
                <RefreshCw size={16} />
                Retry
              </>
            )}
          </button>
        )}

        {/* Pause Button (if supported) */}
        {isProcessing && progress?.stage?.startsWith('processing_chunk') && (
          <button
            onClick={() => alert('Pause functionality coming soon')}
            disabled={true}
            className="control-btn pause-btn disabled"
            title="Pause transcription (coming soon)"
          >
            <Pause size={16} />
            Pause
          </button>
        )}
      </div>

      {/* Progress-specific controls */}
      {progress && progress.chunk_progress && progress.error && (
        <div className="chunk-error-controls">
          <div className="error-message">
            <AlertTriangle size={14} className="text-red-500" />
            <span>Chunk {progress.chunk_progress.current_chunk} failed: {progress.error}</span>
          </div>
          
          <div className="chunk-actions">
            <button
              onClick={() => handleRetry()}
              className="chunk-retry-btn"
              disabled={isRetrying}
            >
              {isRetrying ? (
                <RefreshCw size={14} className="animate-spin" />
              ) : (
                <RefreshCw size={14} />
              )}
              Retry Chunk
            </button>
            
            <button
              onClick={() => alert('Skip chunk functionality coming soon')}
              className="chunk-skip-btn"
              disabled={true}
            >
              Skip Chunk
            </button>
          </div>
        </div>
      )}

      {/* Usage Tips */}
      {isProcessing && (
        <div className="usage-tips">
          <h5>💡 Tips:</h5>
          <ul>
            <li>Transcription can safely run in the background</li>
            <li>You can navigate away and return to check progress</li>
            <li>Large files are automatically processed in chunks</li>
            <li>Failed chunks will be automatically retried</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default TranscriptionControls;