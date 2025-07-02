import React, { useState, useEffect, useRef } from 'react';
import './search.css';

const SearchBox = ({ 
  onSearch, 
  placeholder = "Search hearings...", 
  suggestions = [],
  value = "",
  autoFocus = false,
  showSuggestions = true 
}) => {
  const [query, setQuery] = useState(value);
  const [showSuggestionsList, setShowSuggestionsList] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  useEffect(() => {
    setQuery(value);
  }, [value]);

  const handleInputChange = async (e) => {
    const newQuery = e.target.value;
    setQuery(newQuery);
    setActiveSuggestion(-1);

    if (newQuery.length >= 2 && showSuggestions) {
      setLoadingSuggestions(true);
      try {
        const response = await fetch(`/api/search/suggest?q=${encodeURIComponent(newQuery)}&limit=8`);
        if (response.ok) {
          const data = await response.json();
          // Store suggestions for display
          if (data.suggestions && data.suggestions.length > 0) {
            setShowSuggestionsList(true);
          }
        }
      } catch (error) {
        console.error('Error fetching suggestions:', error);
      } finally {
        setLoadingSuggestions(false);
      }
    } else {
      setShowSuggestionsList(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
      setShowSuggestionsList(false);
      setActiveSuggestion(-1);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion.text);
    onSearch(suggestion.text);
    setShowSuggestionsList(false);
    setActiveSuggestion(-1);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (!showSuggestionsList || suggestions.length === 0) {
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveSuggestion(prev => 
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveSuggestion(prev => 
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (activeSuggestion >= 0 && suggestions[activeSuggestion]) {
          handleSuggestionClick(suggestions[activeSuggestion]);
        } else {
          handleSubmit(e);
        }
        break;
      case 'Escape':
        setShowSuggestionsList(false);
        setActiveSuggestion(-1);
        break;
      default:
        break;
    }
  };

  const handleBlur = (e) => {
    // Delay hiding suggestions to allow click events
    setTimeout(() => {
      if (!suggestionsRef.current?.contains(e.relatedTarget)) {
        setShowSuggestionsList(false);
        setActiveSuggestion(-1);
      }
    }, 150);
  };

  const getSuggestionIcon = (type) => {
    switch (type) {
      case 'hearing': return '📄';
      case 'committee': return '🏛️';
      case 'member': return '👤';
      case 'keyword': return '🔍';
      default: return '💡';
    }
  };

  return (
    <div className="search-box-container">
      <form onSubmit={handleSubmit} className="search-box-form">
        <div className="search-input-container">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onBlur={handleBlur}
            placeholder={placeholder}
            className="search-input"
            autoComplete="off"
          />
          <button 
            type="submit" 
            className="search-button"
            disabled={!query.trim()}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
            </svg>
          </button>
          
          {loadingSuggestions && (
            <div className="search-loading">
              <div className="search-spinner"></div>
            </div>
          )}
        </div>

        {showSuggestionsList && suggestions.length > 0 && (
          <div 
            ref={suggestionsRef}
            className="search-suggestions"
            onMouseDown={(e) => e.preventDefault()} // Prevent blur on click
          >
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                className={`search-suggestion ${index === activeSuggestion ? 'active' : ''}`}
                onClick={() => handleSuggestionClick(suggestion)}
                onMouseEnter={() => setActiveSuggestion(index)}
              >
                <span className="suggestion-icon">
                  {getSuggestionIcon(suggestion.type)}
                </span>
                <span className="suggestion-text">
                  {suggestion.text}
                </span>
                <span className="suggestion-type">
                  {suggestion.type}
                </span>
              </div>
            ))}
          </div>
        )}
      </form>
    </div>
  );
};

export default SearchBox;