import React, { useState, useEffect } from 'react';
import { FileText, Download, Search, Calendar, Building, Eye, Clock } from 'lucide-react';

const TranscriptBrowser = ({ onViewTranscript, onBack }) => {
  const [transcripts, setTranscripts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTranscript, setSelectedTranscript] = useState(null);

  useEffect(() => {
    fetchTranscripts();
  }, []);

  const fetchTranscripts = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8001/api/transcripts');
      if (response.ok) {
        const data = await response.json();
        // Combine existing transcripts with hearing-based transcripts
        const processedTranscripts = data.transcripts || [];
        
        // Also fetch hearing transcripts from the new format
        const hearingTranscripts = await fetchHearingTranscripts();
        
        setTranscripts([...processedTranscripts, ...hearingTranscripts]);
      } else {
        throw new Error('Failed to fetch transcripts');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchHearingTranscripts = async () => {
    // Fetch hearing-based transcripts (hearing_X_transcript.json files)
    try {
      const response = await fetch('http://localhost:8001/api/hearings/transcripts');
      if (response.ok) {
        const data = await response.json();
        return data.transcripts || [];
      }
    } catch (err) {
      console.log('No hearing transcripts endpoint available');
    }
    return [];
  };

  const handleViewTranscript = (transcript) => {
    setSelectedTranscript(transcript);
    if (onViewTranscript) {
      onViewTranscript(transcript);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'Unknown';
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    }
    return `${minutes}m`;
  };

  const getTranscriptType = (transcript) => {
    if (transcript.hearing_id) return 'Hearing Transcript';
    if (transcript.filename && transcript.filename.includes('complete')) return 'Complete Session';
    return 'Transcript';
  };

  const getTranscriptTitle = (transcript) => {
    if (transcript.title) return transcript.title;
    if (transcript.hearing_title) return transcript.hearing_title;
    if (transcript.filename) {
      return transcript.filename.replace(/\.(json|txt)$/, '').replace(/_/g, ' ');
    }
    return 'Untitled Transcript';
  };

  const filteredTranscripts = transcripts.filter(transcript => {
    const title = getTranscriptTitle(transcript).toLowerCase();
    const committee = (transcript.committee || transcript.committee_code || '').toLowerCase();
    const query = searchQuery.toLowerCase();
    return title.includes(query) || committee.includes(query);
  });

  if (loading) {
    return (
      <div style={{ 
        padding: '40px',
        textAlign: 'center',
        color: '#FFFFFF'
      }}>
        <Clock size={48} style={{ marginBottom: '16px', opacity: 0.6 }} />
        <div>Loading transcripts...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        padding: '40px',
        textAlign: 'center',
        color: '#f44336'
      }}>
        <div>Error loading transcripts: {error}</div>
        <button 
          onClick={fetchTranscripts}
          style={{
            marginTop: '16px',
            padding: '8px 16px',
            backgroundColor: '#4ECDC4',
            color: '#1B1C20',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ 
      minHeight: '100vh',
      backgroundColor: '#1B1C20',
      color: '#FFFFFF',
      padding: '20px'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '24px',
        paddingBottom: '16px',
        borderBottom: '1px solid #333'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <FileText size={24} />
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: '600' }}>
            Transcript Browser
          </h1>
          <span style={{ 
            backgroundColor: '#4ECDC4',
            color: '#1B1C20',
            padding: '4px 8px',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: '500'
          }}>
            {filteredTranscripts.length} transcripts
          </span>
        </div>
        {onBack && (
          <button
            onClick={onBack}
            style={{
              backgroundColor: 'transparent',
              color: '#4ECDC4',
              border: '1px solid #4ECDC4',
              padding: '8px 16px',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            ← Back to Dashboard
          </button>
        )}
      </div>

      {/* Search */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '24px',
        padding: '12px',
        backgroundColor: '#2A2B2F',
        borderRadius: '8px',
        border: '1px solid #444'
      }}>
        <Search size={20} style={{ color: '#888' }} />
        <input
          type="text"
          placeholder="Search transcripts by title or committee..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            flex: 1,
            backgroundColor: 'transparent',
            border: 'none',
            outline: 'none',
            color: '#FFFFFF',
            fontSize: '14px'
          }}
        />
      </div>

      {/* Transcripts Grid */}
      {filteredTranscripts.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '60px',
          color: '#888'
        }}>
          <FileText size={48} style={{ marginBottom: '16px', opacity: 0.4 }} />
          <div>No transcripts found</div>
          {searchQuery && (
            <div style={{ marginTop: '8px', fontSize: '14px' }}>
              Try adjusting your search terms
            </div>
          )}
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))',
          gap: '20px'
        }}>
          {filteredTranscripts.map((transcript, index) => (
            <div
              key={index}
              style={{
                backgroundColor: '#2A2B2F',
                border: '1px solid #444',
                borderRadius: '8px',
                padding: '20px',
                transition: 'all 0.2s ease',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#4ECDC4';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#444';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              {/* Transcript Header */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                marginBottom: '12px'
              }}>
                <FileText size={24} style={{ color: '#4ECDC4', marginTop: '2px' }} />
                <div style={{ flex: 1 }}>
                  <h3 style={{
                    margin: '0 0 8px 0',
                    fontSize: '16px',
                    fontWeight: '600',
                    lineHeight: '1.3'
                  }}>
                    {getTranscriptTitle(transcript)}
                  </h3>
                  <div style={{
                    fontSize: '12px',
                    color: '#4ECDC4',
                    backgroundColor: 'rgba(78, 205, 196, 0.1)',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    display: 'inline-block'
                  }}>
                    {getTranscriptType(transcript)}
                  </div>
                </div>
              </div>

              {/* Transcript Details */}
              <div style={{ marginBottom: '16px' }}>
                {transcript.committee && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '8px',
                    fontSize: '14px',
                    color: '#CCCCCC'
                  }}>
                    <Building size={16} />
                    <span>{transcript.committee}</span>
                  </div>
                )}
                
                {(transcript.processed_at || transcript.created_at) && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '8px',
                    fontSize: '14px',
                    color: '#CCCCCC'
                  }}>
                    <Calendar size={16} />
                    <span>{formatDate(transcript.processed_at || transcript.created_at)}</span>
                  </div>
                )}

                {(transcript.confidence || transcript.total_duration) && (
                  <div style={{
                    display: 'flex',
                    gap: '16px',
                    fontSize: '12px',
                    color: '#888'
                  }}>
                    {transcript.confidence && (
                      <span>Confidence: {Math.round(transcript.confidence * 100)}%</span>
                    )}
                    {transcript.total_duration && (
                      <span>Duration: {formatDuration(transcript.total_duration)}</span>
                    )}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div style={{
                display: 'flex',
                gap: '8px'
              }}>
                <button
                  onClick={() => handleViewTranscript(transcript)}
                  style={{
                    flex: 1,
                    backgroundColor: '#4ECDC4',
                    color: '#1B1C20',
                    border: 'none',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    fontWeight: '500'
                  }}
                >
                  <Eye size={16} />
                  View Transcript
                </button>
                
                {transcript.file_path && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      // Handle download
                      console.log('Download transcript:', transcript.file_path);
                    }}
                    style={{
                      backgroundColor: 'transparent',
                      color: '#4ECDC4',
                      border: '1px solid #4ECDC4',
                      padding: '8px 12px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <Download size={16} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TranscriptBrowser;