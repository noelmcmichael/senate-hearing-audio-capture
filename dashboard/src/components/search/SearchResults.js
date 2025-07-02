import React, { useState } from 'react';
import StatusIndicator from '../status/StatusIndicator';
import './search.css';

const SearchResults = ({ 
  results = [], 
  totalCount = 0, 
  pageInfo = {}, 
  searchMetadata = {},
  loading = false,
  onPageChange,
  onSortChange,
  onResultClick,
  onStatusChange 
}) => {
  const [sortBy, setSortBy] = useState(searchMetadata.sort_by || 'relevance');
  const [sortOrder, setSortOrder] = useState(searchMetadata.sort_order || 'desc');

  const handleSortChange = (newSortBy) => {
    let newSortOrder = 'desc';
    if (newSortBy === sortBy) {
      newSortOrder = sortOrder === 'desc' ? 'asc' : 'desc';
    }
    setSortBy(newSortBy);
    setSortOrder(newSortOrder);
    onSortChange?.(newSortBy, newSortOrder);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'No date';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const highlightText = (text, highlights = {}) => {
    if (!text || !highlights.title) return text;
    
    try {
      const highlightHtml = highlights.title[0] || text;
      return <span dangerouslySetInnerHTML={{ __html: highlightHtml }} />;
    } catch {
      return text;
    }
  };

  const getCommitteeName = (code) => {
    const committees = {
      'SCOM': 'Senate Commerce',
      'SSCI': 'Senate Intelligence',
      'SSJU': 'Senate Judiciary', 
      'SSBH': 'Senate Banking'
    };
    return committees[code] || code;
  };

  const renderPagination = () => {
    if (!pageInfo || totalCount <= 20) return null;

    const { current_page = 1, total_pages = 1, has_prev = false, has_next = false } = pageInfo;
    
    return (
      <div className="search-pagination">
        <div className="pagination-info">
          Showing {results.length} of {totalCount} results
        </div>
        <div className="pagination-controls">
          <button 
            onClick={() => onPageChange?.(current_page - 1)}
            disabled={!has_prev}
            className="pagination-button"
          >
            Previous
          </button>
          <span className="pagination-current">
            Page {current_page} of {total_pages}
          </span>
          <button 
            onClick={() => onPageChange?.(current_page + 1)}
            disabled={!has_next}
            className="pagination-button"
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  const renderSortControls = () => (
    <div className="search-sort-controls">
      <span className="sort-label">Sort by:</span>
      {['relevance', 'date', 'title', 'committee', 'status'].map(option => (
        <button
          key={option}
          onClick={() => handleSortChange(option)}
          className={`sort-button ${sortBy === option ? 'active' : ''}`}
        >
          {option.charAt(0).toUpperCase() + option.slice(1)}
          {sortBy === option && (
            <span className="sort-indicator">
              {sortOrder === 'desc' ? ' ↓' : ' ↑'}
            </span>
          )}
        </button>
      ))}
    </div>
  );

  const renderSearchSummary = () => (
    <div className="search-summary">
      <div className="search-results-count">
        <strong>{totalCount}</strong> hearing{totalCount !== 1 ? 's' : ''} found
        {searchMetadata.query && (
          <span className="search-query"> for "{searchMetadata.query}"</span>
        )}
      </div>
      {searchMetadata.filters_applied && Object.keys(searchMetadata.filters_applied).length > 0 && (
        <div className="active-filters">
          {Object.entries(searchMetadata.filters_applied).map(([key, value]) => (
            <span key={key} className="active-filter">
              {key.replace('_', ' ')}: {value}
            </span>
          ))}
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="search-results loading">
        <div className="search-loading-spinner">
          <div className="spinner"></div>
          <p>Searching hearings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="search-results">
      {renderSearchSummary()}
      
      {totalCount > 0 && (
        <>
          {renderSortControls()}
          {renderPagination()}
        </>
      )}

      <div className="search-results-list">
        {results.length === 0 ? (
          <div className="no-results">
            <div className="no-results-icon">🔍</div>
            <h3>No hearings found</h3>
            <p>Try adjusting your search terms or filters</p>
            <div className="search-suggestions">
              <h4>Search suggestions:</h4>
              <ul>
                <li>Try broader keywords</li>
                <li>Check your spelling</li>
                <li>Remove some filters</li>
                <li>Search by committee name (SCOM, SSCI, etc.)</li>
              </ul>
            </div>
          </div>
        ) : (
          results.map((result) => (
            <div 
              key={result.id} 
              className="search-result-card"
              onClick={() => onResultClick?.(result)}
            >
              <div className="result-header">
                <div className="result-title">
                  {highlightText(result.hearing_title, result.search_highlights)}
                </div>
                <div className="result-relevance">
                  {result.relevance_score > 0 && (
                    <span className="relevance-score">
                      {Math.round(result.relevance_score * 100)}% match
                    </span>
                  )}
                </div>
              </div>

              <div className="result-metadata">
                <div className="metadata-item">
                  <span className="metadata-label">Committee:</span>
                  <span className="metadata-value committee-badge">
                    {getCommitteeName(result.committee_code)}
                  </span>
                </div>
                <div className="metadata-item">
                  <span className="metadata-label">Date:</span>
                  <span className="metadata-value">
                    {formatDate(result.hearing_date)}
                  </span>
                </div>
                {result.hearing_type && (
                  <div className="metadata-item">
                    <span className="metadata-label">Type:</span>
                    <span className="metadata-value">
                      {result.hearing_type}
                    </span>
                  </div>
                )}
              </div>

              <div className="result-status">
                <StatusIndicator 
                  status={result.status}
                  processingStage={result.processing_stage}
                  showTooltip={true}
                  onClick={(newStatus) => onStatusChange?.(result.id, newStatus)}
                />
              </div>

              {result.content_summary && (
                <div className="result-summary">
                  {highlightText(result.content_summary, result.search_highlights)}
                </div>
              )}

              {result.participant_list && (
                <div className="result-participants">
                  <span className="participants-label">Participants:</span>
                  <span className="participants-list">
                    {result.participant_list}
                  </span>
                </div>
              )}

              <div className="result-actions">
                <button 
                  className="result-action-button primary"
                  onClick={(e) => {
                    e.stopPropagation();
                    onResultClick?.(result);
                  }}
                >
                  View Details
                </button>
                <button 
                  className="result-action-button secondary"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Handle additional actions
                  }}
                >
                  Quick Actions
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {totalCount > 0 && renderPagination()}
    </div>
  );
};

export default SearchResults;