import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getHealth, getWatchlist, getStrategies, getReportHistory } from '../api';
import { 
  FileText, 
  TrendingUp, 
  Target, 
  Star, 
  CheckCircle, 
  AlertCircle,
  ArrowRight,
  Activity,
  BarChart3,
  Calendar
} from 'lucide-react';

function Dashboard() {
  const [health, setHealth] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [healthRes, watchlistRes, strategiesRes, reportsRes] = await Promise.allSettled([
        getHealth(),
        getWatchlist(),
        getStrategies(),
        getReportHistory()
      ]);

      if (healthRes.status === 'fulfilled') {
        setHealth(healthRes.value.data);
      }

      if (watchlistRes.status === 'fulfilled') {
        setWatchlist(watchlistRes.value.data || []);
      }

      if (strategiesRes.status === 'fulfilled') {
        setStrategies(strategiesRes.value.data || []);
      }

      if (reportsRes.status === 'fulfilled') {
        setReports(reportsRes.value.data || []);
      }
    } catch (err) {
      console.error('Dashboard load error:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="error">{error}</div>
        <button onClick={loadDashboard} className="btn btn-primary">
          Retry
        </button>
      </div>
    );
  }

  const reportsCount = reports.length;
  const watchlistCount = watchlist.length;
  const strategiesCount = strategies.length;
  const recentReports = reports.slice(0, 5);
  const recentStrategies = strategies.slice(0, 3);

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Your investment research workspace</p>
      </div>

      {/* Metrics Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <FileText size={18} style={{ color: 'var(--color-accent)' }} />
            <span className="financial-label">Research Reports</span>
          </div>
          <div className="stat-value">{reportsCount}</div>
        </div>

        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <Star size={18} style={{ color: 'var(--color-accent)' }} />
            <span className="financial-label">Watchlist</span>
          </div>
          <div className="stat-value">{watchlistCount}</div>
        </div>

        <div className="stat-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <Target size={18} style={{ color: 'var(--color-accent)' }} />
            <span className="financial-label">Strategies</span>
          </div>
          <div className="stat-value">{strategiesCount}</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
        <h2 className="section-title">Quick Actions</h2>
        <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          <Link to="/research" className="btn btn-primary">
            <FileText size={16} />
            Research a Company
          </Link>
          <Link to="/strategy" className="btn btn-secondary">
            <BarChart3 size={16} />
            Build a Strategy
          </Link>
          <Link to="/search" className="btn btn-secondary">
            <TrendingUp size={16} />
            Search Stocks
          </Link>
          <Link to="/watchlist" className="btn btn-secondary">
            <Star size={16} />
            Manage Watchlist
          </Link>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-2">
        {/* Recent Research Reports */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
            <h2 className="section-title" style={{ margin: 0 }}>Recent Reports</h2>
            {reportsCount > 0 && (
              <Link to="/reports" style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-accent)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 500 }}>
                View all <ArrowRight size={14} />
              </Link>
            )}
          </div>

          {recentReports.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {recentReports.map((report) => (
                <Link 
                  key={report.id} 
                  to={`/reports?id=${report.id}`}
                  style={{ 
                    padding: 'var(--space-3)', 
                    border: '1px solid var(--color-border)', 
                    borderRadius: 'var(--radius-md)',
                    textDecoration: 'none',
                    transition: 'background-color var(--transition-fast)',
                    display: 'block'
                  }}
                  className="list-item-hover"
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '4px', fontSize: 'var(--font-size-sm)' }}>
                        {report.report?.company_name || report.report?.ticker || 'Unknown'}
                      </div>
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        {report.report?.ticker && <span style={{ fontWeight: 600, color: 'var(--color-text-secondary)' }}>{report.report.ticker}</span>}
                        {report.report?.ticker && <span>•</span>}
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Calendar size={12} />
                          {formatDate(report.report?.generated_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div style={{ 
              padding: 'var(--space-8) var(--space-4)', 
              textAlign: 'center', 
              border: '1px dashed var(--color-border-strong)', 
              borderRadius: 'var(--radius-md)' 
            }}>
              <FileText size={32} style={{ color: 'var(--color-text-subtle)', marginBottom: 'var(--space-3)' }} />
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>
                No research reports yet
              </p>
              <Link to="/research" className="btn btn-primary btn-sm">
                Generate Your First Report
              </Link>
            </div>
          )}
        </div>

        {/* Recent Strategies */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
            <h2 className="section-title" style={{ margin: 0 }}>Saved Strategies</h2>
            {strategiesCount > 0 && (
              <Link to="/strategy" style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-accent)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 500 }}>
                View all <ArrowRight size={14} />
              </Link>
            )}
          </div>

          {recentStrategies.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {recentStrategies.map((strategy) => (
                <Link 
                  key={strategy.id} 
                  to="/strategy"
                  style={{ 
                    padding: 'var(--space-3)', 
                    border: '1px solid var(--color-border)', 
                    borderRadius: 'var(--radius-md)',
                    textDecoration: 'none',
                    transition: 'background-color var(--transition-fast)',
                    display: 'block'
                  }}
                  className="list-item-hover"
                >
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '4px', fontSize: 'var(--font-size-sm)' }}>
                      {strategy.name}
                    </div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      <span>{strategy.conditions?.length || 0} condition{(strategy.conditions?.length || 0) !== 1 ? 's' : ''}</span>
                      <span>•</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Calendar size={12} />
                        {formatDate(strategy.created_at)}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div style={{ 
              padding: 'var(--space-8) var(--space-4)', 
              textAlign: 'center', 
              border: '1px dashed var(--color-border-strong)', 
              borderRadius: 'var(--radius-md)' 
            }}>
              <Target size={32} style={{ color: 'var(--color-text-subtle)', marginBottom: 'var(--space-3)' }} />
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>
                No strategies saved
              </p>
              <Link to="/strategy" className="btn btn-primary btn-sm">
                Build Your First Strategy
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* System Status - Compact, Secondary */}
      {health && (
        <div className="card" style={{ marginTop: 'var(--space-6)' }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 'var(--space-2)',
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-muted)'
          }}>
            <Activity size={14} />
            <span style={{ fontWeight: 600 }}>System Status:</span>
            {health.services?.map((service, index) => (
              <span key={index} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                {service.available ? (
                  <CheckCircle size={14} style={{ color: 'var(--color-success)' }} />
                ) : (
                  <AlertCircle size={14} style={{ color: 'var(--color-warning)' }} />
                )}
                <span>{service.name}</span>
                {index < health.services.length - 1 && <span style={{ margin: '0 var(--space-1)' }}>•</span>}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
