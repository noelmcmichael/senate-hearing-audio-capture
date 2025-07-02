import React, { useState, useEffect } from 'react';
import './search.css';

const SearchFilters = ({
  onFilterChange,
  activeFilters = {},
  showAdvanced = false,
  onToggleAdvanced,
  committees = [],
  hearingTypes = [],
  onClearAll
}) => {
  const [filters, setFilters] = useState({
    committee: '',
    status: '',
    processing_stage: '',
    hearing_type: '',
    date_range: 'all',
    ...activeFilters
  });

  const statusOptions = [
    { value: 'new', label: 'New', color: '#6b7280' },
    { value: 'queued', label: 'Queued', color: '#3b82f6' },
    { value: 'processing', label: 'Processing', color: '#f59e0b' },
    { value: 'review', label: 'Review', color: '#8b5cf6' },
    { value: 'complete', label: 'Complete', color: '#10b981' },
    { value: 'error', label: 'Error', color: '#ef4444' }
  ];

  const processingStageOptions = [
    { value: 'discovered', label: 'Discovered' },
    { value: 'analyzed', label: 'Analyzed' },
    { value: 'captured', label: 'Captured' },
    { value: 'transcribed', label: 'Transcribed' },
    { value: 'reviewed', label: 'Reviewed' },
    { value: 'published', label: 'Published' }
  ];

  const dateRangeOptions = [
    { value: 'all', label: 'All time' },
    { value: 'today', label: 'Today' },
    { value: 'week', label: 'This week' },
    { value: 'month', label: 'This month' },
    { value: 'quarter', label: 'This quarter' },
    { value: 'year', label: 'This year' },
    { value: 'custom', label: 'Custom range' }
  ];

  const committeeOptions = [
    { value: 'SCOM', label: 'Commerce, Science, and Transportation' },
    { value: 'SSCI', label: 'Intelligence' },
    { value: 'SSJU', label: 'Judiciary' },
    { value: 'SSBH', label: 'Banking, Housing, and Urban Affairs' }
  ];

  useEffect(() => {
    setFilters(prev => ({ ...prev, ...activeFilters }));
  }, [activeFilters]);

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    
    // Remove empty filters
    const cleanFilters = Object.entries(newFilters).reduce((acc, [k, v]) => {
      if (v && v !== 'all' && v !== '') {
        acc[k] = v;
      }
      return acc;
    }, {});
    
    onFilterChange(cleanFilters);
  };

  const handleClearAll = () => {
    const clearedFilters = {
      committee: '',
      status: '',
      processing_stage: '',
      hearing_type: '',
      date_range: 'all'
    };
    setFilters(clearedFilters);
    onClearAll?.();
  };

  const getActiveFilterCount = () => {
    return Object.values(filters).filter(v => v && v !== 'all' && v !== '').length;
  };

  const renderQuickFilters = () => (
    <div className="quick-filters">
      <h4>Quick Filters</h4>
      
      {/* Status Pills */}
      <div className="filter-section">
        <label className="filter-label">Status</label>
        <div className="filter-pills">
          {statusOptions.map(option => (
            <button
              key={option.value}
              onClick={() => handleFilterChange('status', 
                filters.status === option.value ? '' : option.value
              )}
              className={`filter-pill status-pill ${
                filters.status === option.value ? 'active' : ''
              }`}
              style={{
                '--status-color': option.color,
                backgroundColor: filters.status === option.value ? option.color : 'transparent',
                borderColor: option.color,
                color: filters.status === option.value ? 'white' : option.color
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Committee Filter */}
      <div className="filter-section">
        <label className="filter-label">Committee</label>
        <select
          value={filters.committee}
          onChange={(e) => handleFilterChange('committee', e.target.value)}
          className="filter-select compact"
        >
          <option value="">All Committees</option>
          {committeeOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Date Range */}
      <div className="filter-section">
        <label className="filter-label">Date Range</label>
        <select
          value={filters.date_range}
          onChange={(e) => handleFilterChange('date_range', e.target.value)}
          className="filter-select compact"
        >
          {dateRangeOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );

  const renderAdvancedFilters = () => (
    <div className="advanced-filters">
      <h4>Advanced Filters</h4>
      
      {/* Processing Stage */}
      <div className="filter-section">
        <label className="filter-label">Processing Stage</label>
        <div className="filter-pills">
          {processingStageOptions.map(option => (
            <button
              key={option.value}
              onClick={() => handleFilterChange('processing_stage', 
                filters.processing_stage === option.value ? '' : option.value
              )}
              className={`filter-pill stage-pill ${
                filters.processing_stage === option.value ? 'active' : ''
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Hearing Type */}
      <div className="filter-section">
        <label className="filter-label">Hearing Type</label>
        <input
          type="text"
          value={filters.hearing_type}
          onChange={(e) => handleFilterChange('hearing_type', e.target.value)}
          placeholder="e.g., Oversight, Nomination"
          className="filter-input"
        />
      </div>
    </div>
  );

  return (
    <div className="search-filters">
      <div className="filters-header">
        <h3>
          Filters
          {getActiveFilterCount() > 0 && (
            <span className="filter-count">({getActiveFilterCount()})</span>
          )}
        </h3>
        <div className="filters-actions">
          {getActiveFilterCount() > 0 && (
            <button onClick={handleClearAll} className="clear-filters-button">
              Clear All
            </button>
          )}
          <button 
            onClick={onToggleAdvanced}
            className="toggle-advanced-button"
          >
            {showAdvanced ? 'Basic' : 'Advanced'}
          </button>
        </div>
      </div>

      <div className="filters-content">
        {renderQuickFilters()}
        
        {showAdvanced && renderAdvancedFilters()}
      </div>

      {/* Active Filters Summary */}
      {getActiveFilterCount() > 0 && (
        <div className="active-filters-summary">
          <h4>Active Filters:</h4>
          <div className="active-filter-tags">
            {Object.entries(filters).map(([key, value]) => {
              if (!value || value === 'all' || value === '') return null;
              
              let displayValue = value;
              if (key === 'status') {
                const status = statusOptions.find(s => s.value === value);
                displayValue = status?.label || value;
              } else if (key === 'committee') {
                const committee = committeeOptions.find(c => c.value === value);
                displayValue = committee?.label || value;
              } else if (key === 'processing_stage') {
                const stage = processingStageOptions.find(s => s.value === value);
                displayValue = stage?.label || value;
              }
              
              return (
                <span key={key} className="active-filter-tag">
                  <span className="filter-tag-label">
                    {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                  </span>
                  <span className="filter-tag-value">{displayValue}</span>
                  <button
                    onClick={() => handleFilterChange(key, '')}
                    className="remove-filter-button"
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
  );
};

export default SearchFilters;