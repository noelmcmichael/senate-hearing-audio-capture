import React, { useState, useEffect } from 'react';
import { useOutletContext, useNavigate, useParams } from 'react-router-dom';
import { 
  ChevronLeft, 
  ChevronRight, 
  Save, 
  Users, 
  CheckCircle, 
  AlertCircle,
  Plus,
  Edit,
  Trash2
} from 'lucide-react';
import config from '../config';

const HearingReview = () => {
  const { hearing, transcript, refreshData } = useOutletContext();
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(0);
  const [segments, setSegments] = useState([]);
  const [customSpeakers, setCustomSpeakers] = useState([]);
  const [newSpeakerName, setNewSpeakerName] = useState('');
  const [showAddSpeaker, setShowAddSpeaker] = useState(false);
  const [saveStatus, setSaveStatus] = useState('saved'); // 'saved', 'saving', 'unsaved'

  // Common speaker roles
  const commonSpeakers = [
    { id: 'CHAIR', name: 'CHAIR', description: 'Committee Chair' },
    { id: 'RANKING', name: 'RANKING', description: 'Ranking Member' },
    { id: 'MEMBER', name: 'MEMBER', description: 'Committee Member' },
    { id: 'WITNESS', name: 'WITNESS', description: 'Witness/Testifier' },
    { id: 'STAFF', name: 'STAFF', description: 'Committee Staff' }
  ];

  useEffect(() => {
    if (transcript?.segments) {
      setSegments([...transcript.segments]);
      
      // Find first segment that needs review
      const firstUnknown = transcript.segments.findIndex(s => 
        s.speaker === 'UNKNOWN' || s.speaker === 'Speaker' || !s.speaker
      );
      if (firstUnknown !== -1) {
        setCurrentSegmentIndex(firstUnknown);
      }
    }
  }, [transcript]);

  const formatTimestamp = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSpeakerColor = (speaker) => {
    const colors = {
      'CHAIR': '#4ECDC4',
      'RANKING': '#9B59B6',
      'MEMBER': '#8A2BE2',
      'WITNESS': '#FFA500',
      'STAFF': '#3498DB',
      'UNKNOWN': '#FF4444',
      'Speaker': '#FF4444'
    };
    return colors[speaker] || '#888';
  };

  const getReviewProgress = () => {
    if (!segments.length) return { current: 0, total: 0, percentage: 0 };
    
    const reviewed = segments.filter(s => 
      s.speaker && s.speaker !== 'UNKNOWN' && s.speaker !== 'Speaker'
    ).length;
    
    return {
      current: reviewed,
      total: segments.length,
      percentage: Math.round((reviewed / segments.length) * 100)
    };
  };

  const handleSpeakerAssignment = (speakerName) => {
    if (!segments[currentSegmentIndex]) return;

    const updatedSegments = [...segments];
    updatedSegments[currentSegmentIndex] = {
      ...updatedSegments[currentSegmentIndex],
      speaker: speakerName
    };
    
    setSegments(updatedSegments);
    setSaveStatus('unsaved');
    
    // Auto-advance to next unknown speaker
    const nextUnknown = segments.findIndex((s, index) => 
      index > currentSegmentIndex && 
      (s.speaker === 'UNKNOWN' || s.speaker === 'Speaker' || !s.speaker)
    );
    
    if (nextUnknown !== -1) {
      setCurrentSegmentIndex(nextUnknown);
    } else {
      // If no more unknown speakers, go to next segment
      if (currentSegmentIndex < segments.length - 1) {
        setCurrentSegmentIndex(currentSegmentIndex + 1);
      }
    }
  };

  const handleAddCustomSpeaker = () => {
    if (!newSpeakerName.trim()) return;
    
    const speakerName = newSpeakerName.trim().toUpperCase();
    if (!customSpeakers.find(s => s.id === speakerName)) {
      setCustomSpeakers([...customSpeakers, {
        id: speakerName,
        name: speakerName,
        description: 'Custom Speaker'
      }]);
    }
    
    setNewSpeakerName('');
    setShowAddSpeaker(false);
    handleSpeakerAssignment(speakerName);
  };

  const handleSaveChanges = async () => {
    setSaveStatus('saving');
    
    try {
      const response = await fetch(`${config.apiUrl}/hearings/${id}/transcript`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ segments })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to save: ${response.status}`);
      }
      
      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Save failed');
      }
      
      setSaveStatus('saved');
      
      // Refresh the data to show updated transcript
      if (refreshData) {
        await refreshData();
      }
      
    } catch (error) {
      console.error('Error saving changes:', error);
      setSaveStatus('unsaved');
      alert('Failed to save changes. Please try again.');
    }
  };

  const navigateToSegment = (direction) => {
    if (direction === 'next' && currentSegmentIndex < segments.length - 1) {
      setCurrentSegmentIndex(currentSegmentIndex + 1);
    } else if (direction === 'prev' && currentSegmentIndex > 0) {
      setCurrentSegmentIndex(currentSegmentIndex - 1);
    }
  };

  const jumpToNextUnknown = () => {
    const nextUnknown = segments.findIndex((s, index) => 
      index > currentSegmentIndex && 
      (s.speaker === 'UNKNOWN' || s.speaker === 'Speaker' || !s.speaker)
    );
    
    if (nextUnknown !== -1) {
      setCurrentSegmentIndex(nextUnknown);
    }
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

  if (!transcript || !segments.length) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '60px 20px'
      }}>
        <div style={{
          backgroundColor: '#2A2B32',
          border: '1px solid #444',
          borderRadius: '8px',
          padding: '40px',
          maxWidth: '500px',
          margin: '0 auto'
        }}>
          <Users size={48} color="#888" style={{ marginBottom: '20px' }} />
          <h3 style={{ color: '#FFFFFF', margin: '0 0 16px 0' }}>
            No Transcript to Review
          </h3>
          <p style={{ color: '#888', margin: '0 0 24px 0', lineHeight: '1.6' }}>
            This hearing needs to be transcribed before speaker review can begin.
          </p>
          <button
            onClick={() => navigate(`/hearings/${id}/status`)}
            style={{
              backgroundColor: '#4ECDC4',
              color: '#1B1C20',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: 'bold'
            }}
          >
            View Status
          </button>
        </div>
      </div>
    );
  }

  const currentSegment = segments[currentSegmentIndex];
  const progress = getReviewProgress();
  const allSpeakers = [...commonSpeakers, ...customSpeakers];

  return (
    <div>
      {/* Header */}
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
          marginBottom: '16px'
        }}>
          <div>
            <h2 style={{ color: '#FFFFFF', margin: '0 0 8px 0', fontSize: '20px' }}>
              Speaker Review
            </h2>
            <div style={{ color: '#888', fontSize: '14px' }}>
              Segment {currentSegmentIndex + 1} of {segments.length} • 
              {progress.current}/{progress.total} reviewed ({progress.percentage}%)
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            {progress.percentage < 100 && (
              <button
                onClick={jumpToNextUnknown}
                style={{
                  backgroundColor: 'transparent',
                  color: '#FFA500',
                  border: '1px solid #FFA500',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Next Unknown
              </button>
            )}
            
            <button
              onClick={handleSaveChanges}
              disabled={saveStatus === 'saved' || saveStatus === 'saving'}
              style={{
                backgroundColor: saveStatus === 'unsaved' ? '#4ECDC4' : '#444',
                color: saveStatus === 'unsaved' ? '#1B1C20' : '#888',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: saveStatus === 'unsaved' ? 'pointer' : 'not-allowed',
                fontSize: '14px',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Save size={16} />
              {saveStatus === 'saving' ? 'Saving...' : 
               saveStatus === 'unsaved' ? 'Save Changes' : 'Saved'}
            </button>

            <button
              onClick={() => navigate(`/hearings/${id}`)}
              style={{
                backgroundColor: 'transparent',
                color: '#4ECDC4',
                border: '1px solid #4ECDC4',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Back to Transcript
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div style={{
          backgroundColor: '#1B1C20',
          borderRadius: '4px',
          height: '8px',
          overflow: 'hidden',
          marginBottom: '16px'
        }}>
          <div style={{
            backgroundColor: progress.percentage === 100 ? '#00FF00' : '#4ECDC4',
            height: '100%',
            width: `${progress.percentage}%`,
            transition: 'width 0.3s ease'
          }} />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '20px' }}>
        {/* Current Segment */}
        <div style={{
          backgroundColor: '#2A2B32',
          border: '1px solid #444',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '20px'
          }}>
            <h3 style={{ color: '#FFFFFF', margin: 0, fontSize: '18px' }}>
              Current Segment
            </h3>
            
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => navigateToSegment('prev')}
                disabled={currentSegmentIndex === 0}
                style={{
                  backgroundColor: 'transparent',
                  color: currentSegmentIndex === 0 ? '#666' : '#4ECDC4',
                  border: `1px solid ${currentSegmentIndex === 0 ? '#666' : '#4ECDC4'}`,
                  padding: '8px',
                  borderRadius: '4px',
                  cursor: currentSegmentIndex === 0 ? 'not-allowed' : 'pointer'
                }}
              >
                <ChevronLeft size={16} />
              </button>
              
              <button
                onClick={() => navigateToSegment('next')}
                disabled={currentSegmentIndex === segments.length - 1}
                style={{
                  backgroundColor: 'transparent',
                  color: currentSegmentIndex === segments.length - 1 ? '#666' : '#4ECDC4',
                  border: `1px solid ${currentSegmentIndex === segments.length - 1 ? '#666' : '#4ECDC4'}`,
                  padding: '8px',
                  borderRadius: '4px',
                  cursor: currentSegmentIndex === segments.length - 1 ? 'not-allowed' : 'pointer'
                }}
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

          {/* Segment Details */}
          <div style={{
            backgroundColor: '#1B1C20',
            borderRadius: '6px',
            padding: '20px',
            marginBottom: '20px'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              marginBottom: '12px'
            }}>
              <span style={{
                color: '#888',
                fontSize: '14px',
                fontFamily: 'monospace'
              }}>
                {formatTimestamp(currentSegment.start)}
              </span>
              
              <span style={{
                backgroundColor: getSpeakerColor(currentSegment.speaker),
                color: currentSegment.speaker === 'UNKNOWN' || currentSegment.speaker === 'Speaker' ? '#FFFFFF' : '#1B1C20',
                padding: '4px 12px',
                borderRadius: '4px',
                fontSize: '14px',
                fontWeight: 'bold'
              }}>
                {currentSegment.speaker}
              </span>
              
              {(currentSegment.speaker === 'UNKNOWN' || currentSegment.speaker === 'Speaker') && (
                <span style={{
                  color: '#FFA500',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  <AlertCircle size={14} />
                  Needs identification
                </span>
              )}
            </div>
            
            <p style={{
              color: '#FFFFFF',
              fontSize: '16px',
              lineHeight: '1.6',
              margin: 0
            }}>
              "{currentSegment.text}"
            </p>
          </div>
        </div>

        {/* Speaker Assignment Panel */}
        <div style={{
          backgroundColor: '#2A2B32',
          border: '1px solid #444',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h3 style={{ color: '#FFFFFF', margin: '0 0 20px 0', fontSize: '18px' }}>
            Assign Speaker
          </h3>

          {/* Common Speakers */}
          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ color: '#4ECDC4', margin: '0 0 12px 0', fontSize: '14px' }}>
              Common Roles
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {commonSpeakers.map(speaker => (
                <button
                  key={speaker.id}
                  onClick={() => handleSpeakerAssignment(speaker.name)}
                  style={{
                    backgroundColor: currentSegment.speaker === speaker.name ? '#4ECDC4' : 'transparent',
                    color: currentSegment.speaker === speaker.name ? '#1B1C20' : '#FFFFFF',
                    border: `1px solid ${currentSegment.speaker === speaker.name ? '#4ECDC4' : '#444'}`,
                    padding: '12px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (currentSegment.speaker !== speaker.name) {
                      e.target.style.borderColor = '#4ECDC4';
                      e.target.style.backgroundColor = '#1B1C20';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (currentSegment.speaker !== speaker.name) {
                      e.target.style.borderColor = '#444';
                      e.target.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
                    {speaker.name}
                  </div>
                  <div style={{ 
                    fontSize: '12px', 
                    opacity: 0.8,
                    color: currentSegment.speaker === speaker.name ? '#1B1C20' : '#888'
                  }}>
                    {speaker.description}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Custom Speakers */}
          {customSpeakers.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ color: '#4ECDC4', margin: '0 0 12px 0', fontSize: '14px' }}>
                Custom Speakers
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {customSpeakers.map(speaker => (
                  <button
                    key={speaker.id}
                    onClick={() => handleSpeakerAssignment(speaker.name)}
                    style={{
                      backgroundColor: currentSegment.speaker === speaker.name ? '#4ECDC4' : 'transparent',
                      color: currentSegment.speaker === speaker.name ? '#1B1C20' : '#FFFFFF',
                      border: `1px solid ${currentSegment.speaker === speaker.name ? '#4ECDC4' : '#444'}`,
                      padding: '12px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      textAlign: 'left'
                    }}
                  >
                    {speaker.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Add Custom Speaker */}
          <div>
            <h4 style={{ color: '#4ECDC4', margin: '0 0 12px 0', fontSize: '14px' }}>
              Add New Speaker
            </h4>
            
            {!showAddSpeaker ? (
              <button
                onClick={() => setShowAddSpeaker(true)}
                style={{
                  backgroundColor: 'transparent',
                  color: '#4ECDC4',
                  border: '1px solid #4ECDC4',
                  padding: '12px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px'
                }}
              >
                <Plus size={16} />
                Add Speaker
              </button>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <input
                  type="text"
                  value={newSpeakerName}
                  onChange={(e) => setNewSpeakerName(e.target.value)}
                  placeholder="Enter speaker name"
                  style={{
                    backgroundColor: '#1B1C20',
                    border: '1px solid #444',
                    color: '#FFFFFF',
                    padding: '12px',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleAddCustomSpeaker();
                    }
                  }}
                  autoFocus
                />
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={handleAddCustomSpeaker}
                    disabled={!newSpeakerName.trim()}
                    style={{
                      backgroundColor: newSpeakerName.trim() ? '#4ECDC4' : '#444',
                      color: newSpeakerName.trim() ? '#1B1C20' : '#888',
                      border: 'none',
                      padding: '8px 12px',
                      borderRadius: '4px',
                      cursor: newSpeakerName.trim() ? 'pointer' : 'not-allowed',
                      fontSize: '12px',
                      flex: 1
                    }}
                  >
                    Add & Assign
                  </button>
                  <button
                    onClick={() => {
                      setShowAddSpeaker(false);
                      setNewSpeakerName('');
                    }}
                    style={{
                      backgroundColor: 'transparent',
                      color: '#888',
                      border: '1px solid #444',
                      padding: '8px 12px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HearingReview;