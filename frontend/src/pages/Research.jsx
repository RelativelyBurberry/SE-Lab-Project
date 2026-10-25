import React, { useState } from 'react';
import { generateResearchReport } from '../api';
import { Activity, TrendingUp, TrendingDown, AlertTriangle, FileText, Calendar } from 'lucide-react';
import CompanyAutocomplete from '../components/CompanyAutocomplete';
import MarkdownRenderer from '../components/MarkdownRenderer';

function Research() {
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);
  const [saved, setSaved] = useState(false);

  const handleCompanySelect = (company) => {
    setSelectedCompany(company);
    setError(null);
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    
    if (!selectedCompany) {
      setError('Please select a company from the search results');
      return;
    }

    setLoading(true);
    setError(null);
    setReport(null);
    setSaved(false);

    try {
      const response = await generateResearchReport(selectedCompany.symbol);
      setReport(response.data.report);
      setSaved(response.data.saved);
    } catch (err) {
      setError('Failed to generate report: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">AI Research</h1>
        <p className="page-subtitle">Generate comprehensive investment research reports</p>
      </div>

      {/* Generate Form */}
      <div className="card">
        <h2 className="section-title">Generate Research Report</h2>

        <form onSubmit={handleGenerate} style={{ marginTop: 'var(--space-4)' }}>
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label className="input-label">Select Company</label>
            <CompanyAutocomplete
              onSelect={handleCompanySelect}
              placeholder="Search by company name or ticker symbol..."
              disabled={loading}
            />
            <p style={{ 
              fontSize: 'var(--font-size-xs)', 
              color: 'var(--color-text-muted)', 
              marginTop: 'var(--space-2)' 
            }}>
              Start typing at least 2 characters to see suggestions
            </p>
          </div>

          <button 
            type="submit" 
            className="btn btn-primary" 
            disabled={loading || !selectedCompany}
            style={{ width: '100%' }}
          >
            <Activity size={16} />
            {loading ? 'Generating Report...' : 'Generate Research Report'}
          </button>
        </form>

        {error && (
          <div className="error" style={{ marginTop: 'var(--space-4)' }}>
            {error}
          </div>
        )}

        {loading && (
          <div className="loading" style={{ marginTop: 'var(--space-6)' }}>
            <div className="spinner"></div>
            <p style={{ marginTop: 'var(--space-3)', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
              Analyzing market data, technical indicators, and news for <strong>{selectedCompany?.symbol}</strong>...
            </p>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-subtle)', marginTop: 'var(--space-2)' }}>
              This may take 30-60 seconds
            </p>
          </div>
        )}
      </div>

      {/* Report Display */}
      {report && (
        <div>
          {/* Header */}
          <div className="card">
            <div className="flex-between">
              <div>
                <h2 className="card-title">{report.company_name}</h2>
                <p className="card-subtitle">{report.ticker}</p>
              </div>
              <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                {saved && <span className="badge badge-success">Saved</span>}
                {!saved && <span className="badge badge-warning">Not Saved</span>}
              </div>
            </div>
            
            <div style={{ marginTop: 'var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Calendar size={12} />
                Generated {new Date(report.generated_at).toLocaleString()}
              </span>
              <span>•</span>
              <span>Data as of {new Date(report.data_timestamp).toLocaleString()}</span>
            </div>
          </div>

          {/* Executive Summary */}
          <div className="card">
            <h3 className="section-title">Executive Summary</h3>
            <MarkdownRenderer content={report.executive_summary} />
          </div>

          {/* Company Overview */}
          {report.company_overview && (
            <div className="card">
              <h3 className="section-title">Company Overview</h3>
              <MarkdownRenderer content={report.company_overview} />
            </div>
          )}

          {/* Analysis Grid */}
          <div className="grid grid-2">
            {/* Technical Analysis */}
            <div className="card">
              <h3 className="section-title">Technical Analysis</h3>
              <MarkdownRenderer content={report.technical_analysis} />
            </div>

            {/* Fundamental Analysis */}
            <div className="card">
              <h3 className="section-title">Fundamental Analysis</h3>
              <MarkdownRenderer content={report.fundamental_analysis} />
            </div>
          </div>

          {/* News Analysis */}
          <div className="card">
            <h3 className="section-title">News & Sentiment Analysis</h3>
            <MarkdownRenderer content={report.news_analysis} />
          </div>

          {/* Factors Grid */}
          <div className="grid grid-2">
            {/* Bullish Factors */}
            <div className="card" style={{ borderTop: '3px solid var(--color-success)' }}>
              <h3 className="section-title" style={{ color: 'var(--color-success)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <TrendingUp size={18} />
                Bullish Factors
              </h3>
              {report.bullish_factors && report.bullish_factors.length > 0 ? (
                <ul style={{ paddingLeft: '20px', margin: 'var(--space-3) 0' }}>
                  {report.bullish_factors.map((factor, index) => (
                    <li key={index} style={{ marginBottom: 'var(--space-2)', fontSize: 'var(--font-size-sm)', lineHeight: 1.6 }}>
                      {factor}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>None identified</p>
              )}
            </div>

            {/* Bearish Factors */}
            <div className="card" style={{ borderTop: '3px solid var(--color-danger)' }}>
              <h3 className="section-title" style={{ color: 'var(--color-danger)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <TrendingDown size={18} />
                Bearish Factors
              </h3>
              {report.bearish_factors && report.bearish_factors.length > 0 ? (
                <ul style={{ paddingLeft: '20px', margin: 'var(--space-3) 0' }}>
                  {report.bearish_factors.map((factor, index) => (
                    <li key={index} style={{ marginBottom: 'var(--space-2)', fontSize: 'var(--font-size-sm)', lineHeight: 1.6 }}>
                      {factor}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>None identified</p>
              )}
            </div>
          </div>

          {/* Risk Factors */}
          <div className="card" style={{ borderTop: '3px solid var(--color-warning)' }}>
            <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <AlertTriangle size={18} style={{ color: 'var(--color-warning)' }} />
              Risk Factors & Uncertainties
            </h3>
            {report.risk_factors && report.risk_factors.length > 0 ? (
              <ul style={{ paddingLeft: '20px', margin: 'var(--space-3) 0' }}>
                {report.risk_factors.map((factor, index) => (
                  <li key={index} style={{ marginBottom: 'var(--space-2)', fontSize: 'var(--font-size-sm)', lineHeight: 1.6 }}>
                    {factor}
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>None specified</p>
            )}
          </div>

          {/* Evidence Quality & Data Warnings */}
          <div className="card">
            <h3 className="section-title">Research Quality Assessment</h3>
            
            <div style={{ marginBottom: 'var(--space-4)' }}>
              <div className="financial-label">Evidence Quality</div>
              <p style={{ fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)', lineHeight: 1.6 }}>
                {report.evidence_quality}
              </p>
            </div>

            {report.missing_data_warnings && report.missing_data_warnings.length > 0 && (
              <div style={{ marginBottom: 'var(--space-4)' }}>
                <div className="financial-label" style={{ color: 'var(--color-warning)' }}>Data Limitations</div>
                <ul style={{ paddingLeft: '20px', margin: 'var(--space-2) 0' }}>
                  {report.missing_data_warnings.map((warning, index) => (
                    <li key={index} style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-warning)', marginBottom: 'var(--space-1)' }}>
                      {warning}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {report.sources && report.sources.length > 0 && (
              <div>
                <div className="financial-label">Data Sources</div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
                  {report.sources.join(' • ')}
                </div>
              </div>
            )}
          </div>

          {/* Disclaimer */}
          <div className="card" style={{ backgroundColor: 'var(--color-warning-bg)', borderLeft: '4px solid var(--color-warning)' }}>
            <h4 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, marginBottom: 'var(--space-2)', color: '#78350f' }}>
              Investment Disclaimer
            </h4>
            <p style={{ fontSize: 'var(--font-size-xs)', lineHeight: 1.6, color: '#92400e' }}>
              This research report is generated for educational and informational purposes only. 
              It does not constitute personalized investment advice or a recommendation to buy, sell, 
              or hold any security. Past performance does not guarantee future results. All investments 
              carry risk, including potential loss of principal. Always conduct your own research and 
              consult with a qualified financial advisor before making investment decisions.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Research;
