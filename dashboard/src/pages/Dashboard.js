import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  SortAsc, 
  SortDesc, 
  Calendar, 
  Users, 
  FileText, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  PlayCircle,
  X
} from 'lucide-react';

const Dashboard = () => {
  const navigate = useNavigate();
  const [hearings, setHearings] = useState([]);
  const [filteredHearings, setFilteredHearings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filter and sort state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCommittees, setSelectedCommittees] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showFilters, setShowFilters] = useState(false);

  // Available committees
  const committees = [
    { code: 'SCOM', name: 'Senate Commerce' },
    { code: 'SSCI', name: 'Senate Intelligence' },
    { code: 'HJUD', name: 'House Judiciary' },
    { code: 'SSJU', name: 'Senate Judiciary' },
    { code: 'SBAN', name: 'Senate Banking' },
    { code: 'SSAF', name: 'Senate Armed Forces' },
    { code: 'SSHR', name: 'Senate Health' },
    { code: 'SSBE', name: 'Senate Budget' }
  ];

  const statusOptions = [
    { value: 'all', label: 'All Hearings' },
    { value: 'has_transcript', label: 'Has Transcript' },
    { value: 'needs_review', label: 'Needs Speaker Review' },
    { value: 'reviewed', label: 'Speaker Review Complete' },
    { value: 'published', label: 'Published' },
    { value: 'in_progress', label: 'In Progress' }
  ];

  const sortOptions = [
    { value: 'date', label: 'Date' },
    { value: 'title', label: 'Title' },
    { value: 'committee', label: 'Committee' },
    { value: 'status', label: 'Status' },
    { value: 'transcript_status', label: 'Transcript Status' }
  ];

  useEffect(() => {
    fetchHearings();
  }, []);

  useEffect(() => {
    applyFiltersAndSort();
  }, [hearings, searchQuery, selectedCommittees, statusFilter, sortBy, sortOrder]);

  const fetchHearings = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch all hearings from multiple committees
      const committeePromises = committees.map(async (committee) => {
        try {
          const response = await fetch(`http://localhost:8001/api/committees/${committee.code}/hearings`);
          if (response.ok) {
            const data = await response.json();
            return data.hearings || [];
          }
        } catch (error) {
          console.warn(`Failed to fetch ${committee.code} hearings:`, error);
          return [];
        }
        return [];
      });

      const allHearings = await Promise.all(committeePromises);
      const flattenedHearings = allHearings.flat();
      
      // Remove duplicates by ID
      const uniqueHearings = flattenedHearings.filter((hearing, index, self) => 
        index === self.findIndex(h => h.id === hearing.id)
      );

      // Check transcript availability
      const transcriptResponse = await fetch('http://localhost:8001/api/transcript-browser/hearings');
      const transcriptData = transcriptResponse.ok ? await transcriptResponse.json() : { transcripts: [] };
      
      // Enhance hearings with transcript information
      const enhancedHearings = uniqueHearings.map(hearing => {
        const transcript = transcriptData.transcripts.find(t => t.hearing_id === hearing.id);
        return {
          ...hearing,
          has_transcript: !!transcript,
          transcript_confidence: transcript?.confidence || 0,
          transcript_segments: transcript?.segments?.length || 0,
          speaker_review_status: calculateSpeakerReviewStatus(transcript)
        };
      });

      setHearings(enhancedHearings);
      
    } catch (error) {
      console.error('Error fetching hearings:', error);
      setError('Failed to load hearings');
    } finally {
      setLoading(false);
    }
  };

  const calculateSpeakerReviewStatus = (transcript) => {
    if (!transcript?.segments) return 'no_transcript';
    
    const segments = transcript.segments;
    const unknownSpeakers = segments.filter(s => 
      s.speaker === 'UNKNOWN' || s.speaker === 'Speaker' || !s.speaker
    ).length;
    
    if (unknownSpeakers === 0) return 'complete';
    if (unknownSpeakers < segments.length / 2) return 'partial';
    return 'needs_review';
  };

  const applyFiltersAndSort = () => {
    let filtered = [...hearings];

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(hearing =>
        hearing.hearing_title?.toLowerCase().includes(query) ||
        hearing.committee_code?.toLowerCase().includes(query) ||
        hearing.participant_list?.toLowerCase().includes(query)
      );
    }

    // Apply committee filter
    if (selectedCommittees.length > 0) {
      filtered = filtered.filter(hearing =>
        selectedCommittees.includes(hearing.committee_code)
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(hearing => {
        switch (statusFilter) {
          case 'has_transcript':
            return hearing.has_transcript;
          case 'needs_review':
            return hearing.speaker_review_status === 'needs_review';
          case 'reviewed':
            return hearing.speaker_review_status === 'complete';
          case 'published':
            return hearing.processing_stage === 'published';
          case 'in_progress':
            return ['discovered', 'analyzed', 'captured', 'transcribed'].includes(hearing.processing_stage);
          default:
            return true;
        }
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue, bValue;
      
      switch (sortBy) {
        case 'date':
          aValue = new Date(a.hearing_date || 0);
          bValue = new Date(b.hearing_date || 0);
          break;
        case 'title':
          aValue = a.hearing_title || '';
          bValue = b.hearing_title || '';
          break;
        case 'committee':
          aValue = a.committee_code || '';
          bValue = b.committee_code || '';
          break;
        case 'status':
          aValue = a.processing_stage || '';
          bValue = b.processing_stage || '';
          break;
        case 'transcript_status':
          aValue = a.speaker_review_status || '';
          bValue = b.speaker_review_status || '';
          break;
        default:
          aValue = a.hearing_date || 0;
          bValue = b.hearing_date || 0;
      }

      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (sortOrder === 'desc') {
        return bValue > aValue ? 1 : -1;
      } else {
        return aValue > bValue ? 1 : -1;
      }
    });

    setFilteredHearings(filtered);
  };

  const handleHearingClick = (hearing) => {
    if (hearing.has_transcript) {
      navigate(`/hearings/${hearing.id}`);
    } else {
      navigate(`/hearings/${hearing.id}/status`);
    }
  };

  const toggleCommitteeFilter = (committeeCode) => {
    setSelectedCommittees(prev => 
      prev.includes(committeeCode)
        ? prev.filter(c => c !== committeeCode)
        : [...prev, committeeCode]
    );
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedCommittees([]);
    setStatusFilter('all');
    setSortBy('date');
    setSortOrder('desc');
  };

  const getStatusIcon = (hearing) => {
    if (hearing.has_transcript) {
      switch (hearing.speaker_review_status) {
        case 'complete':
          return <CheckCircle size={16} color="#00FF00" />;
        case 'partial':
          return <Clock size={16} color="#FFA500" />;
        case 'needs_review':
          return <AlertCircle size={16} color="#FF4444" />;
        default:
          return <FileText size={16} color="#4ECDC4" />;
      }
    } else {
      switch (hearing.processing_stage) {
        case 'published':
          return <CheckCircle size={16} color="#00FF00" />;
        case 'transcribed':
        case 'reviewed':
          return <Clock size={16} color="#FFA500" />;
        case 'captured':
          return <PlayCircle size={16} color="#4169E1" />;
        default:
          return <AlertCircle size={16} color="#888" />;
      }
    }
  };

  const getStatusText = (hearing) => {
    if (hearing.has_transcript) {
      switch (hearing.speaker_review_status) {
        case 'complete':
          return 'Speaker Review Complete';
        case 'partial':
          return 'Partial Speaker Review';
        case 'needs_review':
          return 'Needs Speaker Review';
        default:
          return 'Transcript Available';
      }
    } else {
      switch (hearing.processing_stage) {
        case 'published':
          return 'Published';
        case 'reviewed':
          return 'Under Review';
        case 'transcribed':
          return 'Transcribed';
        case 'captured':
          return 'Audio Captured';
        case 'analyzed':
          return 'Analyzed';
        case 'discovered':
          return 'Discovered';
        default:
          return 'Unknown Status';
      }
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'No date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        backgroundColor: '#1B1C20',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ color: '#FFFFFF', fontSize: '18px' }}>Loading hearings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        backgroundColor: '#1B1C20',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ color: '#FF4444', fontSize: '18px' }}>Error: {error}</div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#1B1C20' }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#2A2B32',
        padding: '20px',
        borderBottom: '1px solid #444'
      }}>
        <h1 style={{ color: '#FFFFFF', margin: '0 0 20px 0', fontSize: '24px' }}>
          Senate Hearing Audio Capture
        </h1>
        
        {/* Search and Filter Controls */}
        <div style={{ 
          display: 'flex', 
          gap: '16px', 
          alignItems: 'center',
          flexWrap: 'wrap'
        }}>
          {/* Search */}
          <div style={{ position: 'relative', minWidth: '300px' }}>
            <Search size={20} style={{ 
              position: 'absolute', 
              left: '12px', 
              top: '50%', 
              transform: 'translateY(-50%)',
              color: '#888'
            }} />
            <input
              type="text"
              placeholder="Search hearings..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 10px 10px 40px',
                backgroundColor: '#1B1C20',
                border: '1px solid #444',
                borderRadius: '6px',
                color: '#FFFFFF',
                fontSize: '14px'
              }}
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            style={{
              backgroundColor: showFilters ? '#4ECDC4' : 'transparent',
              color: showFilters ? '#1B1C20' : '#4ECDC4',
              border: '1px solid #4ECDC4',
              padding: '10px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <Filter size={16} />
            Filters
          </button>

          {/* Sort Controls */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{
                backgroundColor: '#1B1C20',
                border: '1px solid #444',
                color: '#FFFFFF',
                padding: '10px',
                borderRadius: '6px'
              }}
            >
              {sortOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              style={{
                backgroundColor: 'transparent',
                border: '1px solid #444',
                color: '#FFFFFF',
                padding: '10px',
                borderRadius: '6px',
                cursor: 'pointer'
              }}
            >
              {sortOrder === 'asc' ? <SortAsc size={16} /> : <SortDesc size={16} />}
            </button>
          </div>

          {/* Results count */}
          <div style={{ color: '#888', fontSize: '14px' }}>
            {filteredHearings.length} of {hearings.length} hearings
          </div>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div style={{
            backgroundColor: '#1B1C20',
            border: '1px solid #444',
            borderRadius: '8px',
            padding: '20px',
            marginTop: '16px'
          }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '20px'
            }}>
              {/* Committee Filter */}
              <div>
                <h4 style={{ color: '#4ECDC4', margin: '0 0 12px 0', fontSize: '14px' }}>
                  Committees
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {committees.map(committee => (
                    <button
                      key={committee.code}
                      onClick={() => toggleCommitteeFilter(committee.code)}
                      style={{
                        backgroundColor: selectedCommittees.includes(committee.code) 
                          ? '#4ECDC4' : 'transparent',
                        color: selectedCommittees.includes(committee.code) 
                          ? '#1B1C20' : '#FFFFFF',
                        border: '1px solid #4ECDC4',
                        padding: '6px 12px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      {committee.code}
                    </button>
                  ))}
                </div>
              </div>

              {/* Status Filter */}
              <div>
                <h4 style={{ color: '#4ECDC4', margin: '0 0 12px 0', fontSize: '14px' }}>
                  Status
                </h4>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{
                    backgroundColor: '#1B1C20',
                    border: '1px solid #444',
                    color: '#FFFFFF',
                    padding: '8px',
                    borderRadius: '4px',
                    width: '100%'
                  }}
                >
                  {statusOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Clear Filters */}
              <div style={{ display: 'flex', alignItems: 'end' }}>
                <button
                  onClick={clearFilters}
                  style={{
                    backgroundColor: 'transparent',
                    color: '#888',
                    border: '1px solid #444',
                    padding: '8px 16px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <X size={14} />
                  Clear All
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Hearings Grid */}
      <div style={{ padding: '20px' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))',
          gap: '20px'
        }}>
          {filteredHearings.map(hearing => (
            <div
              key={hearing.id}
              onClick={() => handleHearingClick(hearing)}
              style={{
                backgroundColor: '#2A2B32',
                border: '1px solid #444',
                borderRadius: '8px',
                padding: '20px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                '&:hover': {
                  borderColor: '#4ECDC4',
                  backgroundColor: '#34353C'
                }
              }}
              onMouseEnter={(e) => {
                e.target.style.borderColor = '#4ECDC4';
                e.target.style.backgroundColor = '#34353C';
              }}
              onMouseLeave={(e) => {
                e.target.style.borderColor = '#444';
                e.target.style.backgroundColor = '#2A2B32';
              }}
            >
              {/* Header */}
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'flex-start',
                marginBottom: '12px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{
                    backgroundColor: '#4ECDC4',
                    color: '#1B1C20',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 'bold'
                  }}>
                    {hearing.committee_code}
                  </span>
                  <span style={{ color: '#888', fontSize: '12px' }}>
                    {formatDate(hearing.hearing_date)}
                  </span>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {getStatusIcon(hearing)}
                  <span style={{ color: '#888', fontSize: '12px' }}>
                    {getStatusText(hearing)}
                  </span>
                </div>
              </div>

              {/* Title */}
              <h3 style={{
                color: '#FFFFFF',
                margin: '0 0 12px 0',
                fontSize: '16px',
                lineHeight: '1.4'
              }}>
                {hearing.hearing_title}
              </h3>

              {/* Metadata */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                gap: '8px',
                fontSize: '12px',
                color: '#888'
              }}>
                <div>
                  <strong>Type:</strong> {hearing.hearing_type || 'N/A'}
                </div>
                {hearing.has_transcript && (
                  <div>
                    <strong>Segments:</strong> {hearing.transcript_segments}
                  </div>
                )}
                <div>
                  <strong>Stage:</strong> {hearing.processing_stage || 'unknown'}
                </div>
              </div>

              {/* Transcript indicator */}
              {hearing.has_transcript && (
                <div style={{
                  marginTop: '12px',
                  padding: '8px',
                  backgroundColor: '#1B1C20',
                  borderRadius: '4px',
                  fontSize: '12px',
                  color: '#4ECDC4'
                }}>
                  📄 Transcript Available • Click to view
                </div>
              )}
            </div>
          ))}
        </div>

        {filteredHearings.length === 0 && (
          <div style={{
            textAlign: 'center',
            color: '#888',
            padding: '60px 20px',
            fontSize: '16px'
          }}>
            No hearings found matching your criteria.
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;