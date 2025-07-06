import React, { useState } from 'react';
import { 
  Play, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  ArrowRight,
  RefreshCw,
  BarChart3,
  FileText,
  Eye,
  Upload,
  RotateCcw
} from 'lucide-react';
import ChunkedProgressIndicator from './ChunkedProgressIndicator';
import TranscriptionWarnings from './TranscriptionWarnings';
import TranscriptionControls from './TranscriptionControls';

const PipelineControls = ({ hearing, onStageChange }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState(null);
  const [showProgressIndicator, setShowProgressIndicator] = useState(false);
  const [showTranscriptionWarnings, setShowTranscriptionWarnings] = useState(false);
  const [transcriptionError, setTranscriptionError] = useState(null);

  const pipelineStages = [
    { 
      id: 'discovered', 
      name: 'Discovered', 
      description: 'Hearing found and scheduled',
      icon: <AlertCircle size={20} />,
      nextAction: 'analyze',
      nextStage: 'analyzed'
    },
    { 
      id: 'analyzed', 
      name: 'Analyzed', 
      description: 'Metadata and streams analyzed',
      icon: <BarChart3 size={20} />,
      nextAction: 'capture',
      nextStage: 'captured'
    },
    { 
      id: 'captured', 
      name: 'Audio Captured', 
      description: 'Audio successfully recorded',
      icon: <Play size={20} />,
      nextAction: 'transcribe',
      nextStage: 'transcribed'
    },
    { 
      id: 'transcribed', 
      name: 'Transcribed', 
      description: 'Speech-to-text processing complete',
      icon: <FileText size={20} />,
      nextAction: 'review',
      nextStage: 'reviewed'
    },
    { 
      id: 'reviewed', 
      name: 'Reviewed', 
      description: 'Quality review and speaker identification',
      icon: <Eye size={20} />,
      nextAction: 'publish',
      nextStage: 'published'
    },
    { 
      id: 'published', 
      name: 'Published', 
      description: 'Final transcript published',
      icon: <Upload size={20} />,
      nextAction: null,
      nextStage: null
    }
  ];

  const getCurrentStageIndex = () => {
    const currentStage = hearing?.processing_stage || 'discovered';
    return pipelineStages.findIndex(stage => stage.id === currentStage);
  };

  const getStageStatus = (stageIndex) => {
    const currentIndex = getCurrentStageIndex();
    
    if (stageIndex < currentIndex) {
      return 'complete';
    } else if (stageIndex === currentIndex) {
      return processingStage === pipelineStages[stageIndex].id ? 'processing' : 'current';
    } else {
      return 'pending';
    }
  };

  const handleStageAction = async (action, stageId) => {
    if (isProcessing) return;
    
    // For transcription, show warnings/preview first
    if (action === 'transcribe') {
      setShowTranscriptionWarnings(true);
      return;
    }
    
    setIsProcessing(true);
    setProcessingStage(stageId);
    
    try {
      let endpoint;
      if (action === 'capture') {
        endpoint = `/api/hearings/${hearing.id}/capture`;
      } else {
        endpoint = `/api/hearings/${hearing.id}/pipeline/${action}`;
      }
      
      const response = await fetch(`http://localhost:8001${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      });
      
      const result = await response.json();
      
      if (result.success) {
        // For transcribe action, keep progress indicator until completion
        if (action !== 'transcribe') {
          // Refresh hearing data immediately for non-transcribe actions
          if (onStageChange) {
            onStageChange(result.current_stage);
          }
          setIsProcessing(false);
          setProcessingStage(null);
        }
        // For transcribe, the progress indicator will handle completion
      } else {
        console.error('Stage action failed:', result.error);
        alert(`Failed to ${action}: ${result.error}`);
        setIsProcessing(false);
        setProcessingStage(null);
        setShowProgressIndicator(false);
      }
    } catch (error) {
      console.error('Error performing stage action:', error);
      alert(`Error performing ${action}: ${error.message}`);
      setIsProcessing(false);
      setProcessingStage(null);
      setShowProgressIndicator(false);
    }
  };

  const handleTranscriptionComplete = (success, error) => {
    setIsProcessing(false);
    setProcessingStage(null);
    setShowProgressIndicator(false);
    
    if (success) {
      setTranscriptionError(null);
      // Refresh hearing data to show new stage
      if (onStageChange) {
        onStageChange('transcribed');
      }
    } else {
      setTranscriptionError(error || 'Unknown error');
    }
  };

  const handleWarningsProceed = async (audioInfo) => {
    setShowTranscriptionWarnings(false);
    setIsProcessing(true);
    setProcessingStage('transcribed');
    setShowProgressIndicator(true);
    setTranscriptionError(null);
    
    try {
      const response = await fetch(`http://localhost:8001/api/hearings/${hearing.id}/pipeline/transcribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ audioInfo })
      });
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Transcription failed to start');
      }
    } catch (error) {
      console.error('Error starting transcription:', error);
      setTranscriptionError(error.message);
      setIsProcessing(false);
      setProcessingStage(null);
      setShowProgressIndicator(false);
    }
  };

  const handleWarningsCancel = () => {
    setShowTranscriptionWarnings(false);
  };

  const handleCancelTranscription = async (hearingId) => {
    try {
      const response = await fetch(`http://localhost:8001/api/hearings/${hearingId}/transcription/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        setIsProcessing(false);
        setProcessingStage(null);
        setShowProgressIndicator(false);
        setTranscriptionError(null);
      } else {
        throw new Error('Failed to cancel transcription');
      }
    } catch (error) {
      console.error('Error cancelling transcription:', error);
      throw error;
    }
  };

  const handleRetryTranscription = async (hearingId) => {
    setTranscriptionError(null);
    setIsProcessing(true);
    setProcessingStage('transcribed');
    setShowProgressIndicator(true);
    
    try {
      const response = await fetch(`http://localhost:8001/api/hearings/${hearingId}/pipeline/transcribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ retry: true })
      });
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Retry failed to start');
      }
    } catch (error) {
      console.error('Error retrying transcription:', error);
      setTranscriptionError(error.message);
      setIsProcessing(false);
      setProcessingStage(null);
      setShowProgressIndicator(false);
    }
  };

  const handleReset = async (targetStage) => {
    if (isProcessing) return;
    
    const confirmed = window.confirm(`Are you sure you want to reset this hearing to "${targetStage}" stage? This will undo progress from later stages.`);
    if (!confirmed) return;
    
    setIsProcessing(true);
    
    try {
      const response = await fetch(`http://localhost:8001/api/hearings/${hearing.id}/pipeline/reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ stage: targetStage })
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Refresh hearing data
        if (onStageChange) {
          onStageChange(result.current_stage);
        }
      } else {
        console.error('Reset failed:', result.error);
        alert(`Failed to reset: ${result.error}`);
      }
    } catch (error) {
      console.error('Error resetting stage:', error);
      alert(`Error resetting: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const renderStageControls = (stage, index) => {
    const status = getStageStatus(index);
    const isCurrentStage = status === 'current';
    const isComplete = status === 'complete';
    const isProcessingThisStage = processingStage === stage.id;
    
    return (
      <div key={stage.id} className="pipeline-stage">
        <div className="stage-header">
          <div className="stage-icon">
            {isComplete ? (
              <CheckCircle className="text-green-500" size={24} />
            ) : isProcessingThisStage ? (
              <RefreshCw className="text-blue-500 animate-spin" size={24} />
            ) : (
              <div className={`stage-icon-bg ${isCurrentStage ? 'current' : 'pending'}`}>
                {stage.icon}
              </div>
            )}
          </div>
          <div className="stage-info">
            <h3 className="stage-name">{stage.name}</h3>
            <p className="stage-description">{stage.description}</p>
          </div>
          <div className="stage-status">
            {isComplete && <span className="status-badge complete">COMPLETE</span>}
            {isProcessingThisStage && <span className="status-badge processing">PROCESSING</span>}
            {isCurrentStage && !isProcessingThisStage && <span className="status-badge current">CURRENT</span>}
          </div>
        </div>
        
        <div className="stage-controls">
          {/* Next Stage Button */}
          {isCurrentStage && stage.nextAction && (
            <button
              onClick={() => handleStageAction(stage.nextAction, stage.nextStage)}
              disabled={isProcessing}
              className="btn btn-primary"
            >
              {isProcessingThisStage ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  {stage.nextAction === 'capture' ? <Play size={16} /> : <ArrowRight size={16} />}
                  {stage.nextAction.charAt(0).toUpperCase() + stage.nextAction.slice(1)}
                </>
              )}
            </button>
          )}
          
          {/* Reset Button */}
          {isComplete && (
            <button
              onClick={() => handleReset(stage.id)}
              disabled={isProcessing}
              className="btn btn-secondary"
            >
              <RotateCcw size={16} />
              Restart
            </button>
          )}
          
          {/* View Details Button */}
          <button
            onClick={() => alert(`Details for ${stage.name} stage`)}
            className="btn btn-outline"
          >
            View Details
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="pipeline-controls">
      <div className="section-header">
        <h2>Pipeline Stages</h2>
        <div className="stage-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${((getCurrentStageIndex() + 1) / pipelineStages.length) * 100}%` }}
            />
          </div>
          <span className="progress-text">
            {getCurrentStageIndex() + 1} of {pipelineStages.length} stages complete
          </span>
        </div>
      </div>
      
      <div className="stages-list">
        {pipelineStages.map((stage, index) => renderStageControls(stage, index))}
      </div>
      
      <div className="global-controls">
        <button
          onClick={() => handleReset('discovered')}
          disabled={isProcessing}
          className="btn btn-danger"
        >
          <RotateCcw size={16} />
          Reset All Pipeline
        </button>
      </div>
      
      {/* Chunked Progress Indicator */}
      {showProgressIndicator && (
        <div className="progress-indicator-section">
          <ChunkedProgressIndicator
            hearingId={hearing?.id}
            isActive={showProgressIndicator}
            onComplete={handleTranscriptionComplete}
          />
        </div>
      )}

      {/* Transcription Controls */}
      {(isProcessing || transcriptionError) && (
        <div className="transcription-controls-section">
          <TranscriptionControls
            hearingId={hearing?.id}
            isProcessing={isProcessing && processingStage === 'transcribed'}
            canCancel={isProcessing && processingStage === 'transcribed'}
            canRetry={!!transcriptionError && !isProcessing}
            onCancel={handleCancelTranscription}
            onRetry={handleRetryTranscription}
          />
        </div>
      )}

      {/* Transcription Warnings Modal */}
      <TranscriptionWarnings
        hearing={hearing}
        isVisible={showTranscriptionWarnings}
        onProceed={handleWarningsProceed}
        onCancel={handleWarningsCancel}
      />
    </div>
  );
};

export default PipelineControls;