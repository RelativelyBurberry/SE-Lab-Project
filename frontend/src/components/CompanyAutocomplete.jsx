import React, { useState, useEffect, useRef, useCallback } from 'react';
import { searchCompanies } from '../api';
import { Search, Loader, X } from 'lucide-react';

/**
 * Reusable company autocomplete component with debounced search
 * 
 * @param {Object} props
 * @param {Function} props.onSelect - Callback when a company is selected (receives {symbol, name, exchange})
 * @param {string} props.placeholder - Input placeholder text
 * @param {string} props.initialValue - Initial search value
 * @param {boolean} props.disabled - Disable the input
 */
function CompanyAutocomplete({ 
  onSelect, 
  placeholder = "Search by company name or ticker...", 
  initialValue = "",
  disabled = false 
}) {
  const [query, setQuery] = useState(initialValue);
  const [suggestions, setSuggestions] = useState([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [suggestionsError, setSuggestionsError] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [selectedCompany, setSelectedCompany] = useState(null);
  
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);
  const debounceTimerRef = useRef(null);
  const abortControllerRef = useRef(null);
  const currentQueryRef = useRef(null);

  // Debounced search for autocomplete
  const fetchSuggestions = useCallback(async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setSuggestionsLoading(true);
    setSuggestionsError(null);
    setShowSuggestions(true);

    try {
      const response = await searchCompanies(searchQuery, 5);
      
      // Check if this request is still relevant (not stale)
      if (searchQuery === currentQueryRef.current) {
        setSuggestions(response.data.results || []);
        setSelectedIndex(-1);
      }
    } catch (err) {
      // Don't show error for cancelled requests
      if (err.name === 'AbortError' || err.code === 'ERR_CANCELED') {
        return;
      }
      
      const status = err.response?.status;
      if (status === 429) {
        setSuggestionsError('Rate limit reached. Please wait a moment.');
      } else if (status === 502 || status === 504) {
        setSuggestionsError('Data provider temporarily unavailable.');
      } else {
        setSuggestionsError('Failed to search. Please try again.');
      }
      setSuggestions([]);
    } finally {
      setSuggestionsLoading(false);
    }
  }, []);

  // Debounce effect
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Update ref for stale request detection
    currentQueryRef.current = query;

    // Only search after 2 characters
    if (query.length >= 2 && !selectedCompany) {
      debounceTimerRef.current = setTimeout(() => {
        fetchSuggestions(query);
      }, 300);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [query, selectedCompany, fetchSuggestions]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        suggestionsRef.current && 
        !suggestionsRef.current.contains(event.target) &&
        inputRef.current &&
        !inputRef.current.contains(event.target)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (!showSuggestions || suggestions.length === 0) {
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && suggestions[selectedIndex]) {
          handleSelectSuggestion(suggestions[selectedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setShowSuggestions(false);
        setSelectedIndex(-1);
        break;
      default:
        break;
    }
  };

  const handleSelectSuggestion = (suggestion) => {
    const companyData = {
      symbol: suggestion.symbol,
      name: suggestion.name,
      exchange: suggestion.exchange,
      quote_type: suggestion.quote_type
    };
    
    setSelectedCompany(companyData);
    setQuery(`${suggestion.symbol} - ${suggestion.name}`);
    setShowSuggestions(false);
    setSuggestions([]);
    setSelectedIndex(-1);
    
    if (onSelect) {
      onSelect(companyData);
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    
    // Clear selection if user modifies the input
    if (selectedCompany) {
      setSelectedCompany(null);
      if (onSelect) {
        onSelect(null);
      }
    }
  };

  const handleClearSelection = () => {
    setSelectedCompany(null);
    setQuery('');
    setSuggestions([]);
    setShowSuggestions(false);
    if (onSelect) {
      onSelect(null);
    }
    inputRef.current?.focus();
  };

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <div style={{ position: 'relative' }}>
        <input
          ref={inputRef}
          type="text"
          className="input"
          placeholder={placeholder}
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (suggestions.length > 0) {
              setShowSuggestions(true);
            }
          }}
          disabled={disabled}
          style={{ 
            width: '100%',
            paddingRight: selectedCompany ? '80px' : '40px'
          }}
          aria-label="Search for a company"
          aria-autocomplete="list"
          aria-expanded={showSuggestions}
          role="combobox"
        />
        
        <div style={{ 
          position: 'absolute', 
          right: '12px', 
          top: '50%', 
          transform: 'translateY(-50%)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-2)'
        }}>
          {suggestionsLoading && <Loader size={16} className="spin" style={{ color: 'var(--color-text-muted)' }} />}
          {!suggestionsLoading && !selectedCompany && <Search size={16} style={{ color: 'var(--color-text-subtle)' }} />}
          {selectedCompany && (
            <button
              type="button"
              onClick={handleClearSelection}
              className="btn-sm"
              style={{
                padding: '4px 8px',
                fontSize: 'var(--font-size-xs)',
                background: 'var(--color-surface-tertiary)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                color: 'var(--color-text-secondary)',
                fontWeight: 500
              }}
              aria-label="Clear selection"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Selected company badge */}
      {selectedCompany && (
        <div style={{
          marginTop: 'var(--space-2)',
          padding: 'var(--space-2) var(--space-3)',
          background: 'var(--color-success-bg)',
          border: '1px solid var(--color-success)',
          borderRadius: 'var(--radius-md)',
          fontSize: 'var(--font-size-sm)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <strong style={{ color: 'var(--color-success)' }}>{selectedCompany.symbol}</strong>
            {' '}<span style={{ color: 'var(--color-text-secondary)' }}>• {selectedCompany.name}</span>
            {selectedCompany.exchange && (
              <span style={{ color: 'var(--color-text-muted)', marginLeft: 'var(--space-2)', fontSize: 'var(--font-size-xs)' }}>
                ({selectedCompany.exchange})
              </span>
            )}
          </div>
        </div>
      )}

      {/* Suggestions dropdown */}
      {showSuggestions && (suggestions.length > 0 || suggestionsError) && (
        <div 
          ref={suggestionsRef}
          role="listbox"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            marginTop: '4px',
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-lg)',
            zIndex: 1000,
            maxHeight: '300px',
            overflowY: 'auto'
          }}
        >
          {suggestionsError && (
            <div style={{ 
              padding: 'var(--space-3)', 
              color: 'var(--color-danger)', 
              fontSize: 'var(--font-size-sm)',
              borderBottom: '1px solid var(--color-danger-bg)'
            }}>
              {suggestionsError}
            </div>
          )}
          
          {suggestions.map((suggestion, index) => (
            <div
              key={`${suggestion.symbol}-${index}`}
              onClick={() => handleSelectSuggestion(suggestion)}
              onMouseEnter={() => setSelectedIndex(index)}
              role="option"
              aria-selected={index === selectedIndex}
              tabIndex={-1}
              style={{
                padding: 'var(--space-3) var(--space-4)',
                cursor: 'pointer',
                backgroundColor: index === selectedIndex ? 'var(--color-surface-tertiary)' : 'transparent',
                borderBottom: index < suggestions.length - 1 ? '1px solid var(--color-border)' : 'none',
                transition: 'background-color var(--transition-fast)'
              }}
            >
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                gap: 'var(--space-3)'
              }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ 
                    fontSize: 'var(--font-size-sm)', 
                    fontWeight: 600, 
                    color: 'var(--color-text-primary)',
                    marginBottom: '2px'
                  }}>
                    {suggestion.symbol}
                  </div>
                  <div style={{ 
                    fontSize: 'var(--font-size-xs)', 
                    color: 'var(--color-text-muted)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {suggestion.name}
                  </div>
                </div>
                <div style={{ 
                  fontSize: 'var(--font-size-xs)', 
                  color: 'var(--color-text-subtle)',
                  flexShrink: 0
                }}>
                  {suggestion.exchange && suggestion.exchange}
                  {suggestion.quote_type && ` • ${suggestion.quote_type}`}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default CompanyAutocomplete;
