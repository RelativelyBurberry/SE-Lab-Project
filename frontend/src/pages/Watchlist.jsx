import React, { useState, useEffect } from 'react';
import { getWatchlist, removeFromWatchlist, getQuote } from '../api';
import { Star, Trash2, TrendingUp, TrendingDown } from 'lucide-react';

// Utility function to safely format numbers
const formatNumber = (value, decimals = 2, fallback = '—') => {
  if (value === null || value === undefined || isNaN(value) || !isFinite(value)) {
    return fallback;
  }
  return value.toFixed(decimals);
};

function Watchlist() {
  const [watchlist, setWatchlist] = useState([]);
  const [quotes, setQuotes] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadWatchlist();
  }, []);

  const loadWatchlist = async () => {
    try {
      const response = await getWatchlist();
      const items = response.data;
      setWatchlist(items);

      // Fetch quotes for all items
      const quotePromises = items.map(item => 
        getQuote(item.ticker).catch(() => null)
      );
      const quoteResults = await Promise.all(quotePromises);
      
      const quotesMap = {};
      quoteResults.forEach((result, index) => {
        if (result && result.data) {
          quotesMap[items[index].ticker] = result.data;
        }
      });
      setQuotes(quotesMap);

      setError(null);
    } catch (err) {
      if (err.response?.status === 503) {
        setError('Watchlist feature requires database configuration. Please configure DATABASE_URL in backend/.env');
      } else {
        setError('Failed to load watchlist: ' + err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (ticker) => {
    if (!confirm(`Remove ${ticker} from watchlist?`)) return;

    try {
      await removeFromWatchlist(ticker);
      await loadWatchlist();
    } catch (err) {
      alert('Failed to remove from watchlist: ' + err.message);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading watchlist...</p>
      </div>
    );
  }

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">Watchlist</h1>
        <p className="page-subtitle">Track your favorite stocks</p>
      </div>

      {/* Summary Card */}
      <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
        <div className="flex-between">
          <div>
            <span className="financial-label">Total Stocks</span>
            <div className="stat-value" style={{ fontSize: 'var(--font-size-2xl)', marginTop: 'var(--space-1)' }}>
              {watchlist.length}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="error">{error}</div>
      )}

      {!error && watchlist.length === 0 && (
        <div className="card">
          <div className="empty-state">
            <Star size={48} />
            <h3>No stocks in watchlist</h3>
            <p>Search for stocks and add them to your watchlist</p>
            <a href="/search" className="btn btn-primary">
              Search Stocks
            </a>
          </div>
        </div>
      )}

      {!error && watchlist.length > 0 && (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Company</th>
                <th style={{ textAlign: 'right' }}>Price</th>
                <th style={{ textAlign: 'right' }}>Change</th>
                <th>Added</th>
                <th style={{ width: '60px' }}></th>
              </tr>
            </thead>
            <tbody>
              {watchlist.map((item) => {
                const quote = quotes[item.ticker];
                return (
                  <tr key={item.id}>
                    <td style={{ fontWeight: 600 }} className="tabular-nums">{item.ticker}</td>
                    <td>{item.company_name || '—'}</td>
                    <td style={{ textAlign: 'right' }} className="tabular-nums">
                      {quote && quote.price !== null && quote.price !== undefined 
                        ? `$${formatNumber(quote.price)}` 
                        : '—'}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      {quote && quote.change !== null && quote.change !== undefined ? (
                        <span className={`stat-change ${quote.change >= 0 ? 'positive' : 'negative'}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          {quote.change >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                          {quote.change >= 0 ? '+' : ''}{formatNumber(quote.change)} ({formatNumber(quote.change_percent)}%)
                        </span>
                      ) : '—'}
                    </td>
                    <td className="tabular-nums" style={{ fontSize: 'var(--font-size-xs)' }}>
                      {new Date(item.added_at).toLocaleDateString()}
                    </td>
                    <td>
                      <button 
                        onClick={() => handleRemove(item.ticker)}
                        className="btn btn-danger btn-sm"
                        aria-label={`Remove ${item.ticker} from watchlist`}
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Watchlist;
