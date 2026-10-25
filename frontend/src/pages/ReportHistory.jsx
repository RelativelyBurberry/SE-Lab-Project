import React, { useState, useEffect } from 'react';
import { getReportHistory, getSavedReport } from '../api';
import { FileText, Eye, ArrowLeft, Calendar } from 'lucide-react';
import MarkdownRenderer from '../components/MarkdownRenderer';

function ReportHistory() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);
  const [viewLoading, setViewLoading] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const response = await getReportHistory();
      setReports(response.data);
      setError(null);
    } catch (err) {
      if (err.response?.status === 503) {
        setError('Report history requires database configuration.');
      } else {
        setError('Failed to load report history: ' + err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleView = async (reportId) => {
    setViewLoading(true);
    try {
      const response = await getSavedReport(reportId);
      setSelectedReport(response.data.report);
    } catch (err) {
      alert('Failed to load report: ' + err.message);
    } finally {
      setViewLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading report history...</p>
      </div>
    );
  }

  if (selectedReport) {
    return (
      <div>
        {/* Back Button */}
        <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
          <button 
            onClick={() => setSelectedReport(null)}
            className="btn btn-secondary btn-sm"
          >
            <ArrowLeft size={14} />
            Back to History
          </button>
        </div>

        {/* Report Header */}
        <div className="card">
          <div className="flex-between">
            <div>
              <h2 className="card-title">{selectedReport.company_name}</h2>
              <p className="card-subtitle">{selectedReport.ticker}</p>
            </div>
          </div>
          
          <div style={{ marginTop: 'var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Calendar size={12} />
            Generated {new Date(selectedReport.generated_at).toLocaleString()}
          </div>
        </div>

        {/* Executive Summary */}
        <div className="card">
          <h3 className="section-title">Executive Summary</h3>
          <MarkdownRenderer content={selectedReport.executive_summary} />
        </div>

        {/* Analysis Grid */}
        <div className="grid grid-2">
          <div className="card">
            <h3 className="section-title">Technical Analysis</h3>
            <MarkdownRenderer content={selectedReport.technical_analysis} />
          </div>

          <div className="card">
            <h3 className="section-title">Fundamental Analysis</h3>
            <MarkdownRenderer content={selectedReport.fundamental_analysis} />
          </div>
        </div>

        {/* News Analysis */}
        <div className="card">
          <h3 className="section-title">News Analysis</h3>
          <MarkdownRenderer content={selectedReport.news_analysis} />
        </div>

        {/* Factors Grid */}
        <div className="grid grid-2">
          <div className="card" style={{ borderTop: '3px solid var(--color-success)' }}>
            <h3 className="section-title" style={{ color: 'var(--color-success)' }}>Bullish Factors</h3>
            <ul style={{ paddingLeft: '20px', margin: 'var(--space-3) 0' }}>
              {selectedReport.bullish_factors?.map((factor, index) => (
                <li key={index} style={{ marginBottom: 'var(--space-2)', fontSize: 'var(--font-size-sm)' }}>
                  {factor}
                </li>
              ))}
            </ul>
          </div>

          <div className="card" style={{ borderTop: '3px solid var(--color-danger)' }}>
            <h3 className="section-title" style={{ color: 'var(--color-danger)' }}>Bearish Factors</h3>
            <ul style={{ paddingLeft: '20px', margin: 'var(--space-3) 0' }}>
              {selectedReport.bearish_factors?.map((factor, index) => (
                <li key={index} style={{ marginBottom: 'var(--space-2)', fontSize: 'var(--font-size-sm)' }}>
                  {factor}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">Report History</h1>
        <p className="page-subtitle">Previously generated investment research reports</p>
      </div>

      {error && <div className="error">{error}</div>}

      {!error && reports.length === 0 && (
        <div className="card">
          <div className="empty-state">
            <FileText size={48} />
            <h3>No research reports yet</h3>
            <p>Generate AI-powered research reports to see them here</p>
            <a href="/research" className="btn btn-primary">
              Generate Report
            </a>
          </div>
        </div>
      )}

      {!error && reports.length > 0 && (
        <div className="card">
          <table className="table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Company</th>
                <th>Generated</th>
                <th>Summary</th>
                <th style={{ width: '80px' }}></th>
              </tr>
            </thead>
            <tbody>
              {reports.map((reportData) => {
                const report = reportData.report;
                return (
                  <tr key={reportData.id}>
                    <td style={{ fontWeight: 600 }} className="tabular-nums">{report.ticker}</td>
                    <td>{report.company_name}</td>
                    <td className="tabular-nums" style={{ fontSize: 'var(--font-size-xs)' }}>
                      {new Date(report.generated_at).toLocaleDateString()}
                    </td>
                    <td style={{ maxWidth: '400px' }}>
                      <div style={{ 
                        fontSize: 'var(--font-size-xs)', 
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        color: 'var(--color-text-muted)'
                      }}>
                        {report.executive_summary}
                      </div>
                    </td>
                    <td>
                      <button
                        onClick={() => handleView(reportData.id)}
                        className="btn btn-primary btn-sm"
                        disabled={viewLoading}
                      >
                        <Eye size={14} />
                        View
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

export default ReportHistory;
