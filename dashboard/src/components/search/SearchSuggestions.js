import React, { useState, useEffect } from 'react';
import './search.css';

const SearchSuggestions = ({
  query = '',
  onSuggestionClick,
  onClose,
  visible = false,
  maxSuggestions = 10
}) => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (query.length >= 2 && visible) {
      fetchSuggestions(query);
    } else {
      setSuggestions([]);
    }
  }, [query, visible]);

  const fetchSuggestions = async (searchQuery) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/search/suggest?q=${encodeURIComponent(searchQuery)}&limit=${maxSuggestions}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch suggestions');
      }
      
      const data = await response.json();
      setSuggestions(data.suggestions || []);
    } catch (err) {
      console.error('Error fetching suggestions:', err);
      setError(err.message);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    onSuggestionClick(suggestion);
    onClose?.();
  };

  const getSuggestionIcon = (type) => {
    const icons = {
      hearing: '📄',
      committee: '🏛️',
      member: '👤',
      keyword: '🔍',
      topic: '💡',
      participant: '👥'
    };
    return icons[type] || '💡';
  };

  const getSuggestionTypeColor = (type) => {
    const colors = {
      hearing: '#3b82f6',
      committee: '#059669',
      member: '#7c3aed',
      keyword: '#6b7280',
      topic: '#f59e0b',
      participant: '#db2777'
    };
    return colors[type] || '#6b7280';
  };

  const renderSuggestionsByCategory = () => {
    const categorized = suggestions.reduce((acc, suggestion) => {
      const category = suggestion.type || 'other';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(suggestion);
      return acc;
    }, {});

    const categoryOrder = ['hearing', 'committee', 'member', 'keyword', 'topic'];
    const orderedCategories = [
      ...categoryOrder.filter(cat => categorized[cat]),
      ...Object.keys(categorized).filter(cat => !categoryOrder.includes(cat))
    ];

    return orderedCategories.map(category => (
      <div key={category} className="suggestion-category">
        <div className="suggestion-category-header">
          {getSuggestionIcon(category)}
          <span className="suggestion-category-title">
            {category.charAt(0).toUpperCase() + category.slice(1)}s
          </span>
          <span className="suggestion-category-count">
            ({categorized[category].length})
          </span>
        </div>
        <div className="suggestion-category-items">
          {categorized[category].map((suggestion, index) => (
            <div
              key={`${category}-${index}`}
              className="suggestion-item"
              onClick={() => handleSuggestionClick(suggestion)}
            >
              <div className="suggestion-content">
                <span className="suggestion-text">
                  {highlightQuery(suggestion.text, query)}
                </span>
                {suggestion.score && (
                  <span className="suggestion-score">
                    {Math.round(suggestion.score * 100)}%
                  </span>
                )}
              </div>
              {suggestion.description && (
                <div className="suggestion-description">
                  {suggestion.description}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    ));
  };

  const highlightQuery = (text, searchQuery) => {
    if (!searchQuery) return text;
    
    const regex = new RegExp(`(${searchQuery})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="suggestion-highlight">{part}</mark>
      ) : (
        part
      )
    );
  };

  const renderPopularSuggestions = () => {
    const popularSuggestions = [
      { text: 'Oversight hearings', type: 'keyword' },
      { text: 'SCOM', type: 'committee' },
      { text: 'Intelligence briefing', type: 'keyword' },
      { text: 'Judicial nominations', type: 'keyword' },
      { text: 'Banking oversight', type: 'keyword' }
    ];

    return (
      <div className="popular-suggestions">
        <div className="suggestion-category-header">
          <span className="suggestion-category-title">Popular Searches</span>
        </div>
        <div className="suggestion-category-items">
          {popularSuggestions.map((suggestion, index) => (
            <div
              key={`popular-${index}`}
              className="suggestion-item popular"
              onClick={() => handleSuggestionClick(suggestion)}
            >
              <span className="suggestion-icon">
                {getSuggestionIcon(suggestion.type)}
              </span>
              <span className="suggestion-text">
                {suggestion.text}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (!visible) return null;

  return (
    <div className="search-suggestions-container">
      <div className="search-suggestions-content">
        {loading && (
          <div className="suggestions-loading">
            <div className="suggestions-spinner"></div>
            <span>Finding suggestions...</span>
          </div>
        )}

        {error && (
          <div className="suggestions-error">
            <span className="error-icon">⚠️</span>
            <span>Error loading suggestions</span>
          </div>
        )}

        {!loading && !error && suggestions.length > 0 && (
          <div className="suggestions-list">
            {renderSuggestionsByCategory()}
          </div>
        )}

        {!loading && !error && suggestions.length === 0 && query.length >= 2 && (
          <div className="no-suggestions">
            <div className="no-suggestions-content">
              <span className="no-suggestions-icon">🔍</span>
              <span className="no-suggestions-text">
                No suggestions found for "{query}"
              </span>
            </div>
            {renderPopularSuggestions()}
          </div>
        )}

        {!loading && !error && query.length < 2 && (
          renderPopularSuggestions()
        )}
      </div>

      <div className="suggestions-footer">
        <div className="suggestions-tips">
          <span className="tip">💡 Tip: Try searching by committee, member name, or topic</span>
        </div>
      </div>
    </div>
  );
};

export default SearchSuggestions;