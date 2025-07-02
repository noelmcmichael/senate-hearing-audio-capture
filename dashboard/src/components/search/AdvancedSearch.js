import React, { useState, useEffect } from 'react';
import './search.css';

const AdvancedSearch = ({ 
  isOpen, 
  onClose, 
  onSearch, 
  initialFilters = {},
  committees = [],
  statuses = ['new', 'queued', 'processing', 'review', 'complete', 'error'],
  processingStages = ['discovered', 'analyzed', 'captured', 'transcribed', 'reviewed', 'published']
}) => {
  const [filters, setFilters] = useState({
    query: '',
    committee: '',
    status: '',
    processing_stage: '',
    hearing_type: '',
    date_from: '',
    date_to: '',
    participants: '',
    assigned_reviewer: '',
    ...initialFilters
  });

  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    setFilters(prev => ({ ...prev, ...initialFilters }));
  }, [initialFilters]);

  const handleInputChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSearch = async () => {
    setIsSearching(true);
    try {
      // Filter out empty values
      const activeFilters = Object.entries(filters).reduce((acc, [key, value]) => {
        if (value && value.trim() !== '') {
          acc[key] = value;
        }
        return acc;
      }, {});

      await onSearch(activeFilters);
      onClose();
    } catch (error) {
      console.error('Advanced search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleReset = () => {
    setFilters({
      query: '',
      committee: '',
      status: '',
      processing_stage: '',
      hearing_type: '',
      date_from: '',
      date_to: '',
      participants: '',
      assigned_reviewer: ''
    });
  };

  const hasActiveFilters = Object.values(filters).some(value => value && value.trim() !== '');

  if (!isOpen) return null;

  return (
    <div className="advanced-search-overlay">
      <div className="advanced-search-modal">
        <div className="advanced-search-header">
          <h3>Advanced Search</h3>
          <button 
            onClick={onClose} 
            className="close-button"
            aria-label="Close advanced search"
          >
            ×
          </button>
        </div>

        <div className="advanced-search-content">
          <div className="filter-grid">
            {/* Text Search */}
            <div className="filter-group">
              <label htmlFor="adv-query">Search Terms</label>
              <input
                id="adv-query"
                type="text"
                value={filters.query}
                onChange={(e) => handleInputChange('query', e.target.value)}
                placeholder="Enter keywords, titles, or phrases"
                className="filter-input"
              />
            </div>

            {/* Committee Filter */}
            <div className="filter-group">
              <label htmlFor="adv-committee">Committee</label>
              <select
                id="adv-committee"
                value={filters.committee}
                onChange={(e) => handleInputChange('committee', e.target.value)}
                className="filter-select"
              >
                <option value="">All Committees</option>
                <option value="SCOM">Senate Commerce</option>
                <option value="SSCI">Senate Intelligence</option>
                <option value="SSJU">Senate Judiciary</option>
                <option value="SSBH">Senate Banking</option>
              </select>
            </div>

            {/* Status Filter */}
            <div className="filter-group">
              <label htmlFor="adv-status">Status</label>
              <select
                id="adv-status"
                value={filters.status}
                onChange={(e) => handleInputChange('status', e.target.value)}
                className="filter-select"
              >
                <option value="">Any Status</option>
                {statuses.map(status => (
                  <option key={status} value={status}>
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* Processing Stage Filter */}
            <div className="filter-group">
              <label htmlFor="adv-stage">Processing Stage</label>
              <select
                id="adv-stage"
                value={filters.processing_stage}
                onChange={(e) => handleInputChange('processing_stage', e.target.value)}
                className="filter-select"
              >
                <option value="">Any Stage</option>
                {processingStages.map(stage => (
                  <option key={stage} value={stage}>
                    {stage.charAt(0).toUpperCase() + stage.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* Hearing Type */}
            <div className="filter-group">
              <label htmlFor="adv-type">Hearing Type</label>
              <input
                id="adv-type"
                type="text"
                value={filters.hearing_type}
                onChange={(e) => handleInputChange('hearing_type', e.target.value)}
                placeholder="e.g., Oversight, Nomination, Executive Session"
                className="filter-input"
              />
            </div>

            {/* Participants */}
            <div className="filter-group">
              <label htmlFor="adv-participants">Participants</label>
              <input
                id="adv-participants"
                type="text"
                value={filters.participants}
                onChange={(e) => handleInputChange('participants', e.target.value)}
                placeholder="Search by member or witness names"
                className="filter-input"
              />
            </div>

            {/* Date Range */}
            <div className="filter-group date-range">
              <label>Date Range</label>
              <div className="date-inputs">
                <input
                  type="date"
                  value={filters.date_from}
                  onChange={(e) => handleInputChange('date_from', e.target.value)}
                  className="filter-input date-input"
                  placeholder="From date"
                />
                <span className="date-separator">to</span>
                <input
                  type="date"
                  value={filters.date_to}
                  onChange={(e) => handleInputChange('date_to', e.target.value)}
                  className="filter-input date-input"
                  placeholder="To date"
                />
              </div>
            </div>

            {/* Assigned Reviewer */}
            <div className="filter-group">
              <label htmlFor="adv-reviewer">Assigned Reviewer</label>
              <input
                id="adv-reviewer"
                type="text"
                value={filters.assigned_reviewer}
                onChange={(e) => handleInputChange('assigned_reviewer', e.target.value)}
                placeholder="Reviewer name or ID"
                className="filter-input"
              />
            </div>
          </div>

          {/* Filter Summary */}
          {hasActiveFilters && (
            <div className="filter-summary">
              <h4>Active Filters:</h4>
              <div className="filter-tags">
                {Object.entries(filters).map(([key, value]) => {
                  if (!value || value.trim() === '') return null;
                  return (
                    <span key={key} className="filter-tag">
                      <span className="filter-tag-label">
                        {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                      </span>
                      <span className="filter-tag-value">{value}</span>
                      <button
                        onClick={() => handleInputChange(key, '')}
                        className="filter-tag-remove"
                        aria-label={`Remove ${key} filter`}
                      >
                        ×
                      </button>
                    </span>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <div className="advanced-search-footer">
          <div className="search-actions">
            <button 
              onClick={handleReset}
              className="reset-button"
              disabled={!hasActiveFilters}
            >
              Reset All
            </button>
            <div className="primary-actions">
              <button 
                onClick={onClose}
                className="cancel-button"
              >
                Cancel
              </button>
              <button 
                onClick={handleSearch}
                className="search-button primary"
                disabled={isSearching || !hasActiveFilters}
              >
                {isSearching ? (
                  <>
                    <div className="button-spinner"></div>
                    Searching...
                  </>
                ) : (
                  'Search'
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedSearch;