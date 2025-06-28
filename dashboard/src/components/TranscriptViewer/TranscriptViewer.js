import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipBack, SkipForward, Save, Download, AlertCircle } from 'lucide-react';
import AudioPlayer from './AudioPlayer';
import SpeakerAssigner from './SpeakerAssigner';
import BulkOperations from './BulkOperations';
import './TranscriptViewer.css';

const TranscriptViewer = ({ transcriptId }) => {
  const [transcript, setTranscript] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentSegment, setCurrentSegment] = useState(0);
  const [selectedSegments, setSelectedSegments] = useState(new Set());
  const [saveStatus, setSaveStatus] = useState('saved'); // 'saved', 'saving', 'unsaved'
  const [reviewProgress, setReviewProgress] = useState(0);

  const audioRef = useRef(null);
  const segmentRefs = useRef({});

  useEffect(() => {
    loadTranscript();
  }, [transcriptId]);

  const loadTranscript = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8001/transcripts/${transcriptId}`);
      if (!response.ok) throw new Error('Failed to load transcript');
      
      const data = await response.json();
      setTranscript(data.transcript);
      calculateReviewProgress(data.transcript);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const calculateReviewProgress = (transcriptData) => {
    const segments = transcriptData.transcription?.segments || [];
    const needsReview = segments.filter(s => s.review_metadata?.needs_review).length;
    const corrected = segments.filter(s => s.review_metadata?.has_correction).length;
    
    const progress = needsReview > 0 ? (corrected / needsReview) * 100 : 100;
    setReviewProgress(Math.round(progress));
  };

  const handleSpeakerAssignment = async (segmentId, speakerName, confidence = 1.0) => {
    try {
      setSaveStatus('saving');
      
      const response = await fetch(`http://localhost:8001/transcripts/${transcriptId}/corrections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          segment_id: segmentId,
          speaker_name: speakerName,
          confidence: confidence,
          reviewer_id: 'current_user' // TODO: Get from auth context
        })
      });

      if (!response.ok) throw new Error('Failed to save correction');

      // Update local transcript data
      const updatedTranscript = { ...transcript };
      const segments = updatedTranscript.transcription.segments;
      const segmentIndex = segments.findIndex(s => s.id === segmentId);
      
      if (segmentIndex !== -1) {
        segments[segmentIndex].speaker = speakerName;
        segments[segmentIndex].review_metadata.has_correction = true;
        segments[segmentIndex].review_metadata.correction = {
          speaker_name: speakerName,
          confidence: confidence
        };
      }

      setTranscript(updatedTranscript);
      calculateReviewProgress(updatedTranscript);
      setSaveStatus('saved');

    } catch (err) {
      console.error('Error saving speaker assignment:', err);
      setSaveStatus('unsaved');
    }
  };

  const handleBulkAssignment = async (segmentIds, speakerName) => {
    try {
      setSaveStatus('saving');
      
      const response = await fetch(`http://localhost:8001/transcripts/${transcriptId}/bulk-corrections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          segment_ids: Array.from(segmentIds),
          speaker_name: speakerName,
          confidence: 1.0,
          reviewer_id: 'current_user'
        })
      });

      if (!response.ok) throw new Error('Failed to save bulk corrections');

      // Update local transcript data
      const updatedTranscript = { ...transcript };
      const segments = updatedTranscript.transcription.segments;
      
      segmentIds.forEach(segmentId => {
        const segmentIndex = segments.findIndex(s => s.id === segmentId);
        if (segmentIndex !== -1) {
          segments[segmentIndex].speaker = speakerName;
          segments[segmentIndex].review_metadata.has_correction = true;
          segments[segmentIndex].review_metadata.correction = {
            speaker_name: speakerName,
            confidence: 1.0
          };
        }
      });

      setTranscript(updatedTranscript);
      calculateReviewProgress(updatedTranscript);
      setSelectedSegments(new Set());
      setSaveStatus('saved');

    } catch (err) {
      console.error('Error saving bulk assignment:', err);
      setSaveStatus('unsaved');
    }
  };

  const handleExportTranscript = async () => {
    try {
      const response = await fetch(`http://localhost:8001/transcripts/${transcriptId}/export`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('Failed to export transcript');
      
      const result = await response.json();
      alert(`Transcript exported to: ${result.export_path}`);
      
    } catch (err) {
      console.error('Error exporting transcript:', err);
      alert('Failed to export transcript');
    }
  };

  const onTimeUpdate = (currentTime) => {
    // Find current segment based on audio time
    const segments = transcript?.transcription?.segments || [];
    const current = segments.findIndex(segment => 
      currentTime >= segment.start && currentTime <= segment.end
    );
    
    if (current !== -1 && current !== currentSegment) {
      setCurrentSegment(current);
      
      // Scroll to current segment
      const segmentElement = segmentRefs.current[current];
      if (segmentElement) {
        segmentElement.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        });
      }
    }
  };

  const seekToSegment = (segmentIndex) => {
    const segment = transcript?.transcription?.segments[segmentIndex];
    if (segment && audioRef.current) {
      audioRef.current.currentTime = segment.start;
      setCurrentSegment(segmentIndex);
    }
  };

  const toggleSegmentSelection = (segmentId) => {
    const newSelection = new Set(selectedSegments);
    if (newSelection.has(segmentId)) {
      newSelection.delete(segmentId);
    } else {
      newSelection.add(segmentId);
    }
    setSelectedSegments(newSelection);
  };

  const getSegmentStatus = (segment) => {
    if (segment.review_metadata?.has_correction) return 'corrected';
    if (segment.review_metadata?.needs_review) return 'needs-review';
    return 'reviewed';
  };

  if (loading) {
    return (
      <div className="transcript-viewer loading">
        <div className="loading-spinner">Loading transcript...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="transcript-viewer error">
        <AlertCircle className="error-icon" />
        <div className="error-message">Error: {error}</div>
        <button onClick={loadTranscript} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  if (!transcript) {
    return (
      <div className="transcript-viewer empty">
        <div className="empty-message">No transcript data available</div>
      </div>
    );
  }

  const segments = transcript.transcription?.segments || [];
  const speakerOptions = segments[0]?.review_metadata?.speaker_options || [];

  return (
    <div className="transcript-viewer">
      {/* Header */}
      <div className="transcript-header">
        <div className="transcript-info">
          <h2>{transcript.hearing_id}</h2>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${reviewProgress}%` }}
            />
            <span className="progress-text">{reviewProgress}% Complete</span>
          </div>
        </div>
        
        <div className="header-actions">
          <div className={`save-status ${saveStatus}`}>
            {saveStatus === 'saving' && 'Saving...'}
            {saveStatus === 'saved' && 'Saved'}
            {saveStatus === 'unsaved' && 'Unsaved changes'}
          </div>
          
          <button 
            onClick={handleExportTranscript}
            className="export-button"
            disabled={saveStatus === 'saving'}
          >
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {/* Audio Player */}
      <AudioPlayer
        ref={audioRef}
        audioFile={transcript.audio_file}
        onTimeUpdate={onTimeUpdate}
        currentSegment={currentSegment}
        segments={segments}
      />

      {/* Bulk Operations */}
      {selectedSegments.size > 0 && (
        <BulkOperations
          selectedCount={selectedSegments.size}
          speakerOptions={speakerOptions}
          onBulkAssign={handleBulkAssignment}
          selectedSegments={selectedSegments}
          onClearSelection={() => setSelectedSegments(new Set())}
        />
      )}

      {/* Transcript Segments */}
      <div className="transcript-content">
        <div className="segments-list">
          {segments.map((segment, index) => (
            <div
              key={segment.id}
              ref={el => segmentRefs.current[index] = el}
              className={`transcript-segment ${getSegmentStatus(segment)} ${
                currentSegment === index ? 'current' : ''
              } ${selectedSegments.has(segment.id) ? 'selected' : ''}`}
            >
              {/* Segment Header */}
              <div className="segment-header">
                <div className="segment-time">
                  <span className="start-time">
                    {formatTime(segment.start)}
                  </span>
                  <span className="duration">
                    ({formatDuration(segment.end - segment.start)})
                  </span>
                </div>
                
                <div className="segment-actions">
                  <input
                    type="checkbox"
                    checked={selectedSegments.has(segment.id)}
                    onChange={() => toggleSegmentSelection(segment.id)}
                  />
                  
                  <button
                    onClick={() => seekToSegment(index)}
                    className="play-segment-button"
                  >
                    <Play size={14} />
                  </button>
                </div>
              </div>

              {/* Segment Content */}
              <div className="segment-content">
                <div className="segment-text">
                  "{segment.text}"
                </div>
                
                <SpeakerAssigner
                  segment={segment}
                  speakerOptions={speakerOptions}
                  onAssign={(speakerName, confidence) => 
                    handleSpeakerAssignment(segment.id, speakerName, confidence)
                  }
                />
              </div>

              {/* Segment Metadata */}
              <div className="segment-metadata">
                <div className="confidence-indicator">
                  Confidence: {segment.review_metadata?.confidence_level || 'unknown'}
                </div>
                
                {segment.review_metadata?.likely_speaker_change && (
                  <div className="speaker-change-indicator">
                    Likely speaker change
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Helper functions
const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

const formatDuration = (seconds) => {
  return `${seconds.toFixed(1)}s`;
};

export default TranscriptViewer;