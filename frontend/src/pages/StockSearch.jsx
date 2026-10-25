import React, { useState, useEffect, useRef, useCallback } from 'react';
import { searchStock, searchCompanies, getQuote, getTechnicalIndicators, getCompanyNews, addToWatchlist } from '../api';
import { Search, TrendingUp, TrendingDown, Plus, Loader, Building2 } from 'lucide-react';

// Utility function to safely format numbers
const formatNumber = (value, decimals = 2, fallback = '—') => {
  if (value === null || value === undefined || isNaN(value) || !isFinite(value)) {
    return fallback;
  }
  return value.toFixed(decimals);
};

// Format large numbers (market cap, volume)
const formatLargeNumber = (value) => {
  if (value === null || value === undefined || isNaN(value) || !isFinite(value)) {
    return '—';
  }
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toFixed(2)}`;
};

function StockSearch() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [companyInfo, setCompanyInfo] = useState(null);
  const [quote, setQuote] = useState(null);
  const [indicators, setIndicators] = useState(null);
  const [news, setNews] = useState(null);
  
  // Autocomplete state
  const [suggestions, setSuggestions] = useState([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [suggestionsError, setSuggestionsError] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  
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
    if (query.length >= 2) {
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
  }, [query, fetchSuggestions]);

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

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!showSuggestions || suggestions.length === 0) {
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          handleSelectSuggestion(suggestions[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedIndex(-1);
        break;
      default:
        break;
    }
  };

  const handleSelectSuggestion = (suggestion) => {
    setQuery(suggestion.symbol);
    setSelectedSymbol(suggestion.symbol);
    setShowSuggestions(false);
    setSuggestions([]);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    setSelectedSymbol(null); // Reset selected symbol when user types
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    // Close suggestions dropdown
    setShowSuggestions(false);

    setLoading(true);
    setError(null);
    setCompanyInfo(null);
    setQuote(null);
    setIndicators(null);
    setNews(null);

    try {
      // Determine the symbol to use
      let symbolToUse = selectedSymbol;
      
      // If no symbol was explicitly selected, try to resolve via company search
      if (!symbolToUse) {
        try {
          const searchResponse = await searchCompanies(query, 1);
          if (searchResponse.data.results && searchResponse.data.results.length > 0) {
            // Multiple matches - show error if ambiguous
            if (searchResponse.data.results.length > 1) {
              setError('Multiple matches found. Please select from the suggestions.');
              setLoading(false);
              return;
            }
            symbolToUse = searchResponse.data.results[0].symbol;
          } else {
            setError('Stock not found. Please check the company name or ticker.');
            setLoading(false);
            return;
          }
        } catch (searchErr) {
          const status = searchErr.response?.status;
          if (status === 429) {
            setError('Rate limit reached. Please wait a moment.');
          } else if (status === 502 || status === 504) {
            setError('Data provider temporarily unavailable.');
          } else {
            setError('Stock not found. Please check the company name or ticker.');
          }
          setLoading(false);
          return;
        }
      }

      // Fetch all data in parallel using the resolved symbol
      const [companyRes, quoteRes, indicatorsRes, newsRes] = await Promise.allSettled([
        searchStock(symbolToUse),
        getQuote(symbolToUse),
        getTechnicalIndicators(symbolToUse),
        getCompanyNews(symbolToUse)
      ]);

      if (companyRes.status === 'fulfilled') {
        setCompanyInfo(companyRes.value.data);
      }

      if (quoteRes.status === 'fulfilled') {
        setQuote(quoteRes.value.data);
      }

      if (indicatorsRes.status === 'fulfilled') {
        setIndicators(indicatorsRes.value.data);
      }

      if (newsRes.status === 'fulfilled') {
        setNews(newsRes.value.data);
      }

      if (companyRes.status === 'rejected' && quoteRes.status === 'rejected') {
        setError('Stock not found. Please check the ticker symbol.');
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch stock data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToWatchlist = async () => {
    if (!companyInfo) return;

    try {
      await addToWatchlist(companyInfo.ticker, companyInfo.name);
      alert(`${companyInfo.ticker} added to watchlist`);
    } catch (err) {
      if (err.response?.status === 503) {
        alert('Watchlist feature requires database configuration');
      } else if (err.response?.status === 400) {
        alert('Stock already in watchlist');
      } else {
        alert('Failed to add to watchlist: ' + err.message);
      }
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">Stock Search</h1>
        <p className="page-subtitle">Search for stocks and view detailed market information</p>
      </div>

      {/* Search Card */}
      <div className="card">
        <form onSubmit={handleSearch} className="search-container" style={{ position: 'relative' }}>
          <input
            ref={inputRef}
            type="text"
            className="input"
            placeholder="Enter company name or ticker (e.g., AAPL, MSFT)"
            value={query}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => {
              if (query.length >= 2 && suggestions.length > 0) {
                setShowSuggestions(true);
              }
            }}
            style={{ flex: 1 }}
            autoComplete="off"
            aria-label="Search for stocks"
            aria-autocomplete="list"
            aria-controls="suggestions-list"
            aria-expanded={showSuggestions}
          />
          <button type="submit" className="btn btn-primary" disabled={loading}>
            <Search size={16} />
            {loading ? 'Searching...' : 'Search'}
          </button>

          {/* Autocomplete Dropdown */}
          {showSuggestions && (
            <div
              ref={suggestionsRef}
              id="suggestions-list"
              role="listbox"
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 'auto',
                width: 'calc(100% - 120px)',
                maxHeight: '300px',
                overflowY: 'auto',
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: 'var(--shadow-lg)',
                zIndex: 1000,
                marginTop: '4px'
              }}
            >
              {suggestionsLoading && (
                <div style={{ padding: 'var(--space-3) var(--space-4)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                  <Loader size={16} className="spin" />
                  Searching...
                </div>
              )}

              {suggestionsError && !suggestionsLoading && (
                <div style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)' }}>
                  {suggestionsError}
                </div>
              )}

              {!suggestionsLoading && !suggestionsError && suggestions.length === 0 && query.length >= 2 && (
                <div style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                  No results found
                </div>
              )}

              {!suggestionsLoading && !suggestionsError && suggestions.map((suggestion, index) => (
                <div
                  key={suggestion.symbol}
                  role="option"
                  aria-selected={index === selectedIndex}
                  onClick={() => handleSelectSuggestion(suggestion)}
                  style={{
                    padding: 'var(--space-3) var(--space-4)',
                    cursor: 'pointer',
                    backgroundColor: index === selectedIndex ? 'var(--color-surface-tertiary)' : 'var(--color-surface)',
                    borderBottom: index < suggestions.length - 1 ? '1px solid var(--color-border)' : 'none',
                    transition: 'background-color var(--transition-fast)'
                  }}
                  onMouseEnter={() => setSelectedIndex(index)}
                  onMouseLeave={() => setSelectedIndex(-1)}
                >
                  <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', fontSize: 'var(--font-size-sm)' }}>
                    {suggestion.name}
                  </div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                    {suggestion.symbol}
                    {suggestion.exchange && ` • ${suggestion.exchange}`}
                  </div>
                </div>
              ))}
            </div>
          )}
        </form>

        {error && <div className="error" style={{ marginTop: 'var(--space-4)' }}>{error}</div>}
      </div>

      {/* Company Info Card */}
      {companyInfo && (
        <div className="card">
          <div className="flex-between">
            <div>
              <h2 className="card-title">{companyInfo.name}</h2>
              <p className="card-subtitle">{companyInfo.ticker}</p>
            </div>
            <button onClick={handleAddToWatchlist} className="btn btn-primary btn-sm">
              <Plus size={14} />
              Add to Watchlist
            </button>
          </div>

          {(companyInfo.sector || companyInfo.industry) && (
            <div style={{ marginTop: 'var(--space-3)', display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
              {companyInfo.sector && (
                <span className="badge badge-info">
                  {companyInfo.sector}
                </span>
              )}
              {companyInfo.industry && (
                <span className="badge badge-info">{companyInfo.industry}</span>
              )}
            </div>
          )}

          {companyInfo.description && (
            <p style={{ marginTop: 'var(--space-4)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
              {companyInfo.description}
            </p>
          )}
        </div>
      )}

      {/* Quote Card */}
      {quote && (
        <div className="card">
          <h3 className="section-title">Current Quote</h3>
          
          <div className="stats-grid">
            <div>
              <div className="financial-label">Price</div>
              <div className="financial-value" style={{ fontSize: 'var(--font-size-2xl)', marginTop: 'var(--space-1)' }}>
                ${formatNumber(quote.price)}
              </div>
              {quote.change !== null && quote.change !== undefined && (
                <div className={`stat-change ${quote.change >= 0 ? 'positive' : 'negative'}`} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {quote.change >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  {quote.change >= 0 ? '+' : ''}{formatNumber(quote.change)} ({formatNumber(quote.change_percent)}%)
                </div>
              )}
            </div>

            {quote.volume && (
              <div>
                <div className="financial-label">Volume</div>
                <div className="financial-value" style={{ fontSize: 'var(--font-size-lg)', marginTop: 'var(--space-1)' }}>
                  {(quote.volume / 1000000).toFixed(2)}M
                </div>
              </div>
            )}

            {quote.market_cap && (
              <div>
                <div className="financial-label">Market Cap</div>
                <div className="financial-value" style={{ fontSize: 'var(--font-size-lg)', marginTop: 'var(--space-1)' }}>
                  {formatLargeNumber(quote.market_cap)}
                </div>
              </div>
            )}

            {quote.pe_ratio && (
              <div>
                <div className="financial-label">P/E Ratio</div>
                <div className="financial-value" style={{ fontSize: 'var(--font-size-lg)', marginTop: 'var(--space-1)' }}>
                  {formatNumber(quote.pe_ratio)}
                </div>
              </div>
            )}
          </div>

          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-3)' }}>
            Source: {quote.source} • Last updated: {new Date(quote.timestamp).toLocaleString()}
          </p>
        </div>
      )}

      {/* Technical Indicators */}
      {indicators && (
        <div className="card">
          <h3 className="section-title">Technical Indicators</h3>
          
          <table className="table">
            <thead>
              <tr>
                <th>Indicator</th>
                <th>Value</th>
                <th>Signal</th>
              </tr>
            </thead>
            <tbody>
              {indicators.sma_20 && (
                <tr>
                  <td style={{ fontWeight: 500 }}>SMA(20)</td>
                  <td className="tabular-nums">${indicators.sma_20.toFixed(2)}</td>
                  <td>
                    {indicators.current_price > indicators.sma_20 ? (
                      <span className="badge badge-success">Above</span>
                    ) : (
                      <span className="badge badge-danger">Below</span>
                    )}
                  </td>
                </tr>
              )}
              {indicators.sma_50 && (
                <tr>
                  <td style={{ fontWeight: 500 }}>SMA(50)</td>
                  <td className="tabular-nums">${indicators.sma_50.toFixed(2)}</td>
                  <td>
                    {indicators.current_price > indicators.sma_50 ? (
                      <span className="badge badge-success">Above</span>
                    ) : (
                      <span className="badge badge-danger">Below</span>
                    )}
                  </td>
                </tr>
              )}
              {indicators.sma_200 && (
                <tr>
                  <td style={{ fontWeight: 500 }}>SMA(200)</td>
                  <td className="tabular-nums">${indicators.sma_200.toFixed(2)}</td>
                  <td>
                    {indicators.current_price > indicators.sma_200 ? (
                      <span className="badge badge-success">Above</span>
                    ) : (
                      <span className="badge badge-danger">Below</span>
                    )}
                  </td>
                </tr>
              )}
              {indicators.rsi_14 !== null && (
                <tr>
                  <td style={{ fontWeight: 500 }}>RSI(14)</td>
                  <td className="tabular-nums">{indicators.rsi_14.toFixed(2)}</td>
                  <td>
                    {indicators.rsi_14 > 70 ? (
                      <span className="badge badge-danger">Overbought</span>
                    ) : indicators.rsi_14 < 30 ? (
                      <span className="badge badge-success">Oversold</span>
                    ) : (
                      <span className="badge badge-info">Neutral</span>
                    )}
                  </td>
                </tr>
              )}
              {indicators.macd !== null && (
                <tr>
                  <td style={{ fontWeight: 500 }}>MACD</td>
                  <td className="tabular-nums">{indicators.macd.toFixed(4)}</td>
                  <td>
                    {indicators.macd > 0 ? (
                      <span className="badge badge-success">Positive</span>
                    ) : (
                      <span className="badge badge-danger">Negative</span>
                    )}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* News */}
      {news && news.articles && news.articles.length > 0 && (
        <div className="card">
          <h3 className="section-title">Recent News</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {news.articles.map((article, index) => (
              <div key={index} style={{ 
                padding: 'var(--space-4) 0', 
                borderBottom: index < news.articles.length - 1 ? '1px solid var(--color-border)' : 'none' 
              }}>
                <a 
                  href={article.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ fontWeight: 500, color: 'var(--color-text-primary)', textDecoration: 'none', fontSize: 'var(--font-size-sm)' }}
                >
                  {article.title}
                </a>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
                  {article.source} • {article.published_at ? new Date(article.published_at).toLocaleDateString() : 'Recent'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default StockSearch;
