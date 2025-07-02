import React, { useState, useEffect, useCallback } from 'react';
import { StatusIndicator, StatusManager } from '../status';
import SearchBox from '../search/SearchBox';
import AdvancedSearch from '../search/AdvancedSearch';
import SearchResults from '../search/SearchResults';
import './CommitteeDetail.css';

const CommitteeDetail = ({ committee, onBack, onViewDetails }) => {
  const [hearings, setHearings] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('hearings');
  
  // Status management state
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [selectedHearing, setSelectedHearing] = useState(null);
  const [selectedHearings, setSelectedHearings] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);
  const [searchFilters, setSearchFilters] = useState({});
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [searchMetadata, setSearchMetadata] = useState({});
  const [suggestions, setSuggestions] = useState([]);

  const fetchCommitteeData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch hearings and stats in parallel
      const [hearingsResponse, statsResponse] = await Promise.all([
        fetch(`http://localhost:8001/api/committees/${committee.code}/hearings`),
        fetch(`http://localhost:8001/api/committees/${committee.code}/stats`)
      ]);

      if (!hearingsResponse.ok || !statsResponse.ok) {
        throw new Error('Failed to fetch committee data');
      }

      const hearingsData = await hearingsResponse.json();
      const statsData = await statsResponse.json();
      
      setHearings(hearingsData.hearings || []);
      setStats(statsData.stats || {});
    } catch (err) {
      console.error('Error fetching committee data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [committee]);

  useEffect(() => {
    if (committee) {
      fetchCommitteeData();
    }
  }, [committee, fetchCommitteeData]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatDateTime = (dateTimeString) => {
    return new Date(dateTimeString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return '#4CAF50';
    if (confidence >= 0.8) return '#FF9800';
    return '#f44336';
  };

  // Status management functions
  const handleStatusClick = (hearing) => {
    setSelectedHearing(hearing);
    setSelectedHearings([]);
    setStatusModalOpen(true);
  };

  const handleBulkStatusUpdate = () => {
    if (selectedHearings.length === 0) return;
    setSelectedHearing(null);
    setStatusModalOpen(true);
  };

  const handleStatusUpdate = (result) => {
    // Refresh committee data after status update
    fetchCommitteeData();
    setSelectedHearings([]);
  };

  const toggleHearingSelection = (hearingId) => {
    setSelectedHearings(prev => 
      prev.includes(hearingId) 
        ? prev.filter(id => id !== hearingId)
        : [...prev, hearingId]
    );
  };

  const getFilteredHearings = () => {
    if (statusFilter === 'all') return hearings;
    return hearings.filter(hearing => hearing.status === statusFilter);
  };

  // Search functions
  const handleSearch = async (query) => {
    if (!query.trim()) {
      setIsSearchMode(false);
      setSearchResults([]);
      return;
    }

    setSearchLoading(true);
    setIsSearchMode(true);
    setSearchQuery(query);

    try {
      // Add committee filter to search for committee-specific results
      const searchUrl = `http://localhost:8001/api/search/hearings?query=${encodeURIComponent(query)}&committee=${committee.code}&limit=20`;
      const response = await fetch(searchUrl);
      
      if (!response.ok) {
        throw new Error('Search failed');
      }
      
      const data = await response.json();
      setSearchResults(data.results || []);
      setSearchMetadata(data.search_metadata || {});
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleAdvancedSearch = async (filters) => {
    setSearchLoading(true);
    setIsSearchMode(true);
    setSearchFilters(filters);

    try {
      // Add committee filter to advanced search
      const searchBody = {
        ...filters,
        committee: committee.code,
        limit: 20
      };

      const response = await fetch('http://localhost:8001/api/search/advanced', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchBody)
      });
      
      if (!response.ok) {
        throw new Error('Advanced search failed');
      }
      
      const data = await response.json();
      setSearchResults(data.results || []);
      setSearchMetadata(data.search_metadata || {});
    } catch (error) {
      console.error('Advanced search error:', error);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSearchClear = () => {
    setSearchQuery('');
    setSearchResults([]);
    setSearchFilters({});
    setSearchMetadata({});
    setIsSearchMode(false);
    setSuggestions([]);
  };

  const handleResultClick = (result) => {
    // Handle clicking on a search result - could navigate to hearing detail
    console.log('Clicked result:', result);
  };



  const fetchSuggestions = async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`http://localhost:8001/api/search/suggest?q=${encodeURIComponent(query)}&limit=5`);
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions || []);
      }
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      setSuggestions([]);
    }
  };

  // Debounced suggestion fetching
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery) {
        fetchSuggestions(searchQuery);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  if (!committee) {
    return <div className="committee-detail">No committee selected</div>;
  }

  if (loading) {
    return (
      <div className="committee-detail">
        <div className="committee-detail-header">
          <button className="btn-back" onClick={onBack}>← Back</button>
          <h2>Loading...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="committee-detail">
        <div className="committee-detail-header">
          <button className="btn-back" onClick={onBack}>← Back</button>
          <h2>Error</h2>
        </div>
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="committee-detail">
      <div className="committee-detail-header">
        <button className="btn-back" onClick={onBack}>← Back to Committees</button>
        <div className="committee-info">
          <h2>
            <span className="committee-code">{committee.code}</span>
            {committee.name}
          </h2>
          <div className="committee-meta">
            <span className="meta-item">
              <strong>{stats.total_hearings}</strong> Total Hearings
            </span>
            <span className="meta-item">
              <strong>{stats.recent_activity}</strong> Recent Activity
            </span>
            <span className="meta-item">
              Confidence: <strong style={{color: getConfidenceColor(stats.avg_confidence)}}>
                {Math.round(stats.avg_confidence * 100)}%
              </strong>
            </span>
          </div>
        </div>
      </div>

      <div className="tab-navigation">
        <button 
          className={`tab-button ${activeTab === 'hearings' ? 'active' : ''}`}
          onClick={() => setActiveTab('hearings')}
        >
          Hearings ({hearings.length})
        </button>
        <button 
          className={`tab-button ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          Statistics
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'hearings' && (
          <div className="hearings-tab">
            {/* Search Interface */}
            <div className="search-section">
              <div className="search-header">
                <h3>Search {committee.name} Hearings</h3>
                <div className="search-actions">
                  <button 
                    className="btn-advanced-search"
                    onClick={() => setShowAdvancedSearch(true)}
                  >
                    Advanced Search
                  </button>
                  {isSearchMode && (
                    <button 
                      className="btn-clear-search"
                      onClick={handleSearchClear}
                    >
                      Clear Search
                    </button>
                  )}
                </div>
              </div>
              
              <SearchBox
                onSearch={handleSearch}
                placeholder={`Search ${committee.name} hearings...`}
                suggestions={suggestions}
                value={searchQuery}
                showSuggestions={true}
              />
            </div>

            <div className="hearings-controls">
              {!isSearchMode && (
                <div className="status-filters">
                  <label>Filter by Status:</label>
                  <select 
                    value={statusFilter} 
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="status-filter-select"
                  >
                    <option value="all">All Statuses</option>
                    <option value="new">New</option>
                    <option value="queued">Queued</option>
                    <option value="processing">Processing</option>
                    <option value="review">Review</option>
                    <option value="complete">Complete</option>
                    <option value="error">Error</option>
                  </select>
                </div>
              )}
              
              {selectedHearings.length > 0 && (
                <div className="bulk-actions">
                  <span className="selection-count">
                    {selectedHearings.length} hearing{selectedHearings.length > 1 ? 's' : ''} selected
                  </span>
                  <button 
                    className="btn-bulk-action"
                    onClick={handleBulkStatusUpdate}
                  >
                    Update Status
                  </button>
                  <button 
                    className="btn-bulk-clear"
                    onClick={() => setSelectedHearings([])}
                  >
                    Clear Selection
                  </button>
                </div>
              )}
            </div>

            {/* Search Results or Regular Hearings */}
            {isSearchMode ? (
              <SearchResults
                results={searchResults}
                totalCount={searchResults.length}
                searchMetadata={searchMetadata}
                loading={searchLoading}
                onResultClick={handleResultClick}
                onStatusChange={(hearingId, newStatus) => {
                  setSelectedHearing({ id: hearingId });
                  setStatusModalOpen(true);
                }}
              />
            ) : (
              <>
                {getFilteredHearings().length === 0 ? (
                  <div className="no-hearings">
                    {statusFilter === 'all' 
                      ? 'No hearings found for this committee' 
                      : `No hearings with status '${statusFilter}'`
                    }
                  </div>
                ) : (
                  <div className="hearings-list">
                {getFilteredHearings().map((hearing) => (
                  <div key={hearing.id} className="hearing-card">
                    <div className="hearing-selection">
                      <input
                        type="checkbox"
                        checked={selectedHearings.includes(hearing.id)}
                        onChange={() => toggleHearingSelection(hearing.id)}
                        className="hearing-checkbox"
                      />
                    </div>
                    
                    <div className="hearing-header">
                      <div className="hearing-title-row">
                        <h3 className="hearing-title">{hearing.title}</h3>
                        <div className="hearing-badges">
                          <div 
                            className="hearing-confidence"
                            style={{ backgroundColor: getConfidenceColor(hearing.sync_confidence) }}
                          >
                            {Math.round(hearing.sync_confidence * 100)}%
                          </div>
                        </div>
                      </div>
                      <div className="hearing-meta">
                        <span className="hearing-date">{formatDate(hearing.date)}</span>
                        <span className="hearing-type">{hearing.type}</span>
                      </div>
                    </div>
                    
                    <div className="hearing-status-section">
                      <StatusIndicator 
                        status={hearing.status || 'new'}
                        processing_stage={hearing.processing_stage || 'discovered'}
                        showStage={true}
                        clickable={true}
                        onClick={() => handleStatusClick(hearing)}
                      />
                      {hearing.assigned_reviewer && (
                        <div className="reviewer-info">
                          Reviewer: <span className="reviewer-name">{hearing.assigned_reviewer}</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="hearing-details">
                      <div className="detail-row">
                        <span className="detail-label">Streams:</span>
                        <span className="detail-value">
                          {Object.keys(hearing.streams || {}).join(', ') || 'None'}
                        </span>
                      </div>
                      <div className="detail-row">
                        <span className="detail-label">Status Updated:</span>
                        <span className="detail-value">
                          {hearing.status_updated_at ? formatDateTime(hearing.status_updated_at) : 'Never'}
                        </span>
                      </div>
                      {hearing.reviewer_notes && (
                        <div className="detail-row">
                          <span className="detail-label">Notes:</span>
                          <span className="detail-value">{hearing.reviewer_notes}</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="hearing-actions">
                      <button 
                        className="btn-action"
                        onClick={() => onViewDetails && onViewDetails(hearing.id)}
                      >
                        View Details
                      </button>
                      <button 
                        className="btn-action secondary"
                        onClick={() => handleStatusClick(hearing)}
                      >
                        Update Status
                      </button>
                    </div>
                  </div>
                ))}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="stats-tab">
            <div className="stats-grid">
              <div className="stat-card">
                <h4>Overview</h4>
                <div className="stat-items">
                  <div className="stat-item">
                    <span className="stat-label">Total Hearings:</span>
                    <span className="stat-value">{stats.total_hearings}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Earliest Hearing:</span>
                    <span className="stat-value">{formatDate(stats.earliest_hearing)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Latest Hearing:</span>
                    <span className="stat-value">{formatDate(stats.latest_hearing)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Avg Confidence:</span>
                    <span className="stat-value" style={{color: getConfidenceColor(stats.avg_confidence)}}>
                      {Math.round(stats.avg_confidence * 100)}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="stat-card">
                <h4>Hearing Types</h4>
                <div className="hearing-types">
                  {stats.hearing_types && stats.hearing_types.map((type, index) => (
                    <div key={index} className="hearing-type-item">
                      <span className="type-name">{type.type}</span>
                      <span className="type-count">{type.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="stat-card">
                <h4>Activity</h4>
                <div className="stat-items">
                  <div className="stat-item">
                    <span className="stat-label">Recent (30 days):</span>
                    <span className="stat-value">{stats.recent_activity}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Advanced Search Modal */}
      <AdvancedSearch
        isOpen={showAdvancedSearch}
        onClose={() => setShowAdvancedSearch(false)}
        onSearch={handleAdvancedSearch}
        initialFilters={{ committee: committee.code, ...searchFilters }}
      />

      {/* Status Management Modal */}
      <StatusManager
        isOpen={statusModalOpen}
        onClose={() => setStatusModalOpen(false)}
        hearingIds={selectedHearings}
        currentHearing={selectedHearing}
        onStatusUpdate={handleStatusUpdate}
        bulkMode={selectedHearings.length > 0}
      />
    </div>
  );
};

export default CommitteeDetail;