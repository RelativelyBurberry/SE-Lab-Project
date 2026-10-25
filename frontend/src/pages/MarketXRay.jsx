import React, { useEffect, useMemo, useState } from 'react';
import { Activity, Network, RefreshCw, Wallet, Zap, PieChart } from 'lucide-react';
import { Link } from 'react-router-dom';
import { analyzePortfolio, getWatchlist } from '../api';

const DEFAULT_WEIGHTS = { AAPL: 20, MSFT: 15, NVDA: 15, AMD: 10, AMZN: 10, GOOGL: 10, JPM: 5, XOM: 5, GLD: 5, KO: 5 };
const COLORS = ['#4776e6', '#1b9a78', '#d97706', '#9b59b6', '#d94f70', '#0891b2', '#64748b', '#b45309'];
const fmt = (n, digits = 2) => Number.isFinite(Number(n)) ? Number(n).toFixed(digits) : '—';

function Metric({ label, value, detail }) {
  return <div className="stat-card"><div className="financial-label">{label}</div><div className="stat-value">{value}</div>{detail && <div className="page-subtitle" style={{ fontSize: 12, marginTop: 4 }}>{detail}</div>}</div>;
}

const SECTOR_BY_TICKER = {
  AAPL: 'Technology', MSFT: 'Technology', 'MSFT.TO': 'Technology', NVDA: 'Technology', AMD: 'Technology',
  AMZN: 'Consumer & Retail', WMT: 'Consumer & Retail', KO: 'Consumer Staples', PG: 'Consumer Staples',
  GOOGL: 'Communication Services', META: 'Communication Services', NFLX: 'Communication Services',
  JPM: 'Financials', 'RY.TO': 'Financials', 'SBIN.NS': 'Financials', BAC: 'Financials', GS: 'Financials',
  XOM: 'Energy', 'OIL.NS': 'Energy', 'ONGC.NS': 'Energy', CVX: 'Energy',
  GLD: 'Gold / Commodity ETF', SPY: 'Broad Market ETF', QQQ: 'Technology ETF',
  'HFG.DE': 'Consumer & Retail', 'TSLA': 'Consumer & Retail', 'LLY': 'Healthcare', 'JNJ': 'Healthcare',
};
const SECTOR_COLORS = ['#4776e6', '#1b9a78', '#d97706', '#9b59b6', '#d94f70', '#0891b2', '#64748b', '#b45309'];

function SectorTreeMap({ result }) {
  const grouped = {};
  Object.entries(result.normalized_weights || {}).forEach(([ticker, weight]) => {
    const sector = SECTOR_BY_TICKER[ticker] || 'Sector not classified';
    if (!grouped[sector]) grouped[sector] = [];
    grouped[sector].push({ ticker, weight: Number(weight) });
  });
  const sectors = Object.entries(grouped).map(([name, holdings]) => ({
    name, holdings, weight: holdings.reduce((sum, item) => sum + item.weight, 0),
  })).sort((a, b) => b.weight - a.weight);
  return <div>
    <p className="page-subtitle" style={{ fontSize: 13, marginBottom: 12 }}>Each block represents part of your portfolio. Bigger blocks mean more of your money is allocated there. Sector labels are shown only where the app has a known mapping; unmatched tickers stay unclassified rather than being guessed.</p>
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'stretch' }}>
      {sectors.map((sector, i) => <div key={sector.name} style={{ flex: `${Math.max(sector.weight, 4)} 1 180px`, minWidth: 160, borderRadius: 10, overflow: 'hidden', border: '1px solid var(--color-border)', background: `${SECTOR_COLORS[i % SECTOR_COLORS.length]}12` }}>
        <div style={{ padding: '10px 12px', background: `${SECTOR_COLORS[i % SECTOR_COLORS.length]}20`, borderBottom: '1px solid var(--color-border)' }}><div style={{ fontWeight: 700 }}>{sector.name}</div><div style={{ fontSize: 12, marginTop: 3, color: 'var(--color-text-secondary)' }}>{fmt(sector.weight)}% of portfolio</div></div>
        <div style={{ padding: 8, display: 'flex', flexWrap: 'wrap', gap: 5 }}>
          {sector.holdings.sort((a, b) => b.weight - a.weight).map(item => <div key={item.ticker} title={`${item.ticker}: ${fmt(item.weight)}% of portfolio`} style={{ flex: `${Math.max(item.weight, 3)} 1 75px`, minHeight: 52, padding: 8, borderRadius: 6, background: SECTOR_COLORS[i % SECTOR_COLORS.length], color: '#fff', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}><strong style={{ fontSize: 12 }}>{item.ticker}</strong><span style={{ fontSize: 11 }}>{fmt(item.weight)}%</span></div>)}
        </div>
      </div>)}
    </div>
  </div>;
}

function getSector(ticker) { return SECTOR_BY_TICKER[ticker] || 'Other / unclassified'; }

function buildInsights(result, suggestedMix) {
  const weights = result?.normalized_weights || {};
  const sectors = Object.entries(weights).reduce((acc, [ticker, weight]) => {
    const sector = getSector(ticker);
    acc[sector] = (acc[sector] || 0) + Number(weight || 0);
    return acc;
  }, {});
  const sectorEntries = Object.entries(sectors).sort((a, b) => b[1] - a[1]);
  const topSector = sectorEntries[0];
  const strongest = (result?.relationships || []).slice().sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation))[0];
  const highCluster = (result?.clusters || []).slice().sort((a, b) => b.portfolio_weight_pct - a.portfolio_weight_pct)[0];
  const insights = [];
  if (topSector) {
    insights.push({
      tone: topSector[1] >= 40 ? 'amber' : 'blue',
      title: topSector[1] >= 40 ? `${topSector[0]} concentration is high` : `${topSector[0]} is your largest sector`,
      value: `${topSector[1].toFixed(1)}% of portfolio`,
      body: topSector[1] >= 40
        ? `Nearly ${topSector[1].toFixed(0)}% of the portfolio is classified in ${topSector[0]}. A sector-specific shock could affect a large share of your holdings. Review whether this concentration is intentional.`
        : `${topSector[0]} is the largest classified sector exposure. Compare it with your other holdings and check whether the concentration matches your intended risk.`
    });
  }
  if (highCluster) {
    insights.push({
      tone: highCluster.tickers.length > 1 ? 'purple' : 'teal',
      title: highCluster.tickers.length > 1 ? 'Several holdings move together' : 'Most capital sits in a separate co-movement group',
      value: `${highCluster.portfolio_weight_pct.toFixed(1)}% in ${highCluster.tickers.length} holding${highCluster.tickers.length === 1 ? '' : 's'}`,
      body: highCluster.tickers.length > 1
        ? `${highCluster.tickers.join(', ')} form a positive-correlation group at your selected threshold. Holding several names may provide less diversification than the count suggests.`
        : `${highCluster.tickers[0]} is not linked to another holding by the selected positive-correlation threshold. Check the relationship graph for its strongest positive and negative links.`
    });
  }
  if (strongest) {
    insights.push({
      tone: strongest.correlation < 0 ? 'green' : Math.abs(strongest.correlation) >= 0.8 ? 'rose' : 'blue',
      title: strongest.correlation < 0 ? 'Potential offsetting relationship' : 'Strongest co-movement pair',
      value: `${strongest.source} ↔ ${strongest.target}: ${strongest.correlation.toFixed(2)}`,
      body: strongest.correlation < -0.4
        ? `These holdings historically moved in opposite directions over the selected window. That relationship can change and is not a guaranteed hedge.`
        : `These holdings historically moved ${strongest.correlation >= 0 ? 'in the same direction' : 'in opposite directions'} over the selected window. Correlation is historical co-movement, not causation.`
    });
  }
  if (suggestedMix) {
    insights.push({
      tone: 'green',
      title: 'A small weight change lowered historical volatility',
      value: `${suggestedMix.ticker}: ${suggestedMix.from.toFixed(1)}% → ${suggestedMix.to.toFixed(1)}%`,
      body: `In this historical covariance estimate, reweighting ${suggestedMix.ticker} and proportionally scaling the other holdings changes estimated annualized volatility from ${suggestedMix.before.toFixed(2)}% to ${suggestedMix.after.toFixed(2)}%. This is a what-if, not an investment recommendation or expected-return forecast.`
    });
  }
  const regime = result?.market_regimes;
  if (regime?.available && Number.isFinite(Number(regime.average_stress_day_return_pct))) {
    insights.push({
      tone: 'rose',
      title: 'How your portfolio behaved on its roughest days',
      value: `${Number(regime.average_stress_day_return_pct).toFixed(2)}% average daily return`,
      body: `On the worst 20% of days in this sample, the portfolio averaged ${Number(regime.average_stress_day_return_pct).toFixed(2)}% per day, compared with ${Number(regime.average_ordinary_day_return_pct).toFixed(2)}% on the remaining days. This describes the selected history, not a future-loss forecast.`
    });
  }
  const changedPair = regime?.relationships_that_changed_most?.find(pair => Math.abs(Number(pair.absolute_change)) >= 0.2);
  if (changedPair) {
    insights.push({
      tone: 'blue',
      title: 'A relationship worth a closer look',
      value: `${changedPair.source} ↔ ${changedPair.target}`,
      body: `Their correlation changed from ${Number(changedPair.ordinary_correlation).toFixed(2)} on ordinary days to ${Number(changedPair.stress_correlation).toFixed(2)} on rough days. A relationship measured across the full period may not describe behaviour during market stress; check other periods before relying on it.`
    });
  }
  return insights;
}

function InsightCards({ insights }) {
  const accent = {
    amber: '#b45309', blue: '#315eaa', purple: '#7e4aa8',
    teal: '#0f766e', green: '#18734b', rose: '#be4455'
  };
  return <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
    {insights.map((item, i) => <article key={`${item.title}-${i}`} className="xray-insight-row" style={{ display: 'grid', gridTemplateColumns: 'minmax(170px, 0.85fr) minmax(210px, 1fr) minmax(280px, 2fr)', gap: 20, alignItems: 'start', padding: '18px 4px', borderBottom: i === insights.length - 1 ? 'none' : '1px solid var(--color-border)' }}>
      <div style={{ borderLeft: `3px solid ${accent[item.tone] || accent.blue}`, paddingLeft: 12 }}>
        <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.045em', color: 'var(--color-text-secondary, #64748b)', lineHeight: 1.5 }}>{item.title}</div>
      </div>
      <div style={{ fontSize: 18, fontWeight: 700, lineHeight: 1.35, color: 'var(--color-text, #111827)' }}>{item.value}</div>
      <p style={{ fontSize: 13, lineHeight: 1.65, color: 'var(--color-text-secondary, #64748b)', margin: 0 }}>{item.body}</p>
    </article>)}
    {insights.length === 0 && <p className="page-subtitle">No notable findings were detected for this selection and historical window.</p>}
    <style>{`@media (max-width: 760px) { .xray-insight-row { grid-template-columns: 1fr !important; } }`}</style>
  </div>;
}
function findLowerVolatilityMix(result) {
  const weights = result?.normalized_weights || {};
  const covariance = result?.annualized_covariance || {};
  const tickers = Object.keys(weights);
  if (tickers.length < 2) return null;
  const volatility = candidate => {
    let variance = 0;
    for (const a of tickers) for (const b of tickers) {
      variance += (candidate[a] || 0) * (candidate[b] || 0) * Number(covariance[a]?.[b] || 0);
    }
    return Math.sqrt(Math.max(0, variance)) * 100;
  };
  const before = Number(result.annualized_volatility_pct);
  let best = null;
  // Explore modest +/- 5 and 10 percentage-point changes; keep every holding.
  for (const ticker of tickers) {
    const from = Number(weights[ticker] || 0);
    for (const delta of [-10, -5, 5, 10]) {
      const to = Math.max(0, Math.min(60, from + delta));
      if (Math.abs(to - from) < 1 || to >= 100) continue;
      const otherTotal = tickers.reduce((sum, t) => sum + (t === ticker ? 0 : Number(weights[t] || 0)), 0);
      if (otherTotal <= 0) continue;
      const candidate = {};
      for (const t of tickers) candidate[t] = t === ticker ? to / 100 : (Number(weights[t] || 0) / otherTotal) * (100 - to) / 100;
      const after = volatility(candidate);
      if (Number.isFinite(after) && (!best || after < best.after)) best = { ticker, from, to, before, after };
    }
  }
  return best && best.after < before - 0.1 ? best : null;
}


function RelationshipGraph({ result, threshold }) {
  const tickers = Object.keys(result.correlation_matrix || {});
  const [selected, setSelected] = useState(null);
  const [view, setView] = useState('strongest');
  const width = 1000, height = 500, cx = width / 2, cy = height / 2;
  const clusterByTicker = {};
  (result.clusters || []).forEach((cluster, i) => cluster.tickers.forEach(t => { clusterByTicker[t] = i; }));
  const positions = Object.fromEntries(tickers.map((ticker, i) => {
    const angle = -Math.PI / 2 + (2 * Math.PI * i / Math.max(tickers.length, 1));
    const radius = Math.min(width * 0.36, height * 0.37);
    return [ticker, { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) }];
  }));
  const allEdges = (result.relationships || []).slice().sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));
  const visibleEdges = view === 'all'
    ? allEdges
    : view === 'threshold'
      ? allEdges.filter(e => Math.abs(e.correlation) >= Number(threshold))
      : allEdges.slice(0, Math.min(12, allEdges.length));
  const edges = selected ? visibleEdges.filter(e => e.source === selected || e.target === selected) : visibleEdges;
  const selectedConnections = allEdges.filter(e => e.source === selected || e.target === selected);
  const topConnection = selectedConnections[0];

  return <div>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
      <div><strong>Hidden relationships between your holdings</strong><div className="page-subtitle" style={{ fontSize: 12 }}>The default view shows the strongest positive AND negative relationships, even below the threshold.</div></div>
      {selected && <button type="button" className="btn btn-secondary btn-sm" onClick={() => setSelected(null)}>Clear {selected} selection</button>}
    </div>
    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8, marginBottom: 12 }}>
      <span className="financial-label">Connections</span>
      {[['strongest', 'Strongest 12'], ['threshold', `Above |${fmt(threshold, 2)}|`], ['all', 'All pairs']].map(([value, label]) => <button key={value} type="button" className={`btn btn-sm ${view === value ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setView(value)}>{label}</button>)}
      <span style={{ fontSize: 12, color: 'var(--color-text-secondary, #64748b)' }}>{edges.length} connection{edges.length === 1 ? '' : 's'} shown</span>
    </div>
    <div style={{ width: '100%', overflowX: 'auto', border: '1px solid var(--color-border)', borderRadius: 12, background: 'var(--color-surface, #fbfcff)' }}>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Interactive portfolio return relationship graph" style={{ width: '100%', minWidth: 600, display: 'block' }}>
        {edges.map(edge => {
          const a = positions[edge.source], b = positions[edge.target];
          if (!a || !b) return null;
          const strong = Math.abs(edge.correlation) >= Number(threshold);
          const active = !selected || edge.source === selected || edge.target === selected;
          const positive = edge.correlation >= 0;
          return <g key={`${edge.source}-${edge.target}`} opacity={active ? (strong ? 0.95 : 0.55) : 0.07}>
            <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={positive ? '#16865f' : '#d9485f'} strokeWidth={1 + Math.abs(edge.correlation) * 5} strokeDasharray={strong ? undefined : '5 5'} />
            <title>{`${edge.source} ↔ ${edge.target}: ${positive ? 'positive' : 'negative'} correlation ${fmt(edge.correlation, 3)}${strong ? ' (above threshold)' : ' (below threshold)'}`}</title>
          </g>;
        })}
        {tickers.map(ticker => {
          const p = positions[ticker];
          const active = !selected || ticker === selected || edges.some(e => (e.source === selected && e.target === ticker) || (e.target === selected && e.source === ticker));
          const color = COLORS[(clusterByTicker[ticker] ?? 0) % COLORS.length];
          return <g key={ticker} onClick={() => setSelected(current => current === ticker ? null : ticker)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') setSelected(current => current === ticker ? null : ticker); }} tabIndex={0} role="button" aria-label={`Inspect ${ticker} relationships`} style={{ cursor: 'pointer' }} opacity={active ? 1 : 0.28}>
            <circle cx={p.x} cy={p.y} r={selected === ticker ? 27 : 22} fill={color} stroke={selected === ticker ? '#111827' : '#fff'} strokeWidth={selected === ticker ? 4 : 2} />
            <text x={p.x} y={p.y + 4} fill="#fff" fontSize={ticker.length > 6 ? 10 : 12} fontWeight="700" textAnchor="middle">{ticker}</text>
            <title>{`${ticker}: ${fmt(result.normalized_weights?.[ticker] || 0, 1)}% portfolio weight. Click to inspect its strongest relationships.`}</title>
          </g>;
        })}
        {tickers.length < 2 && <text x={cx} y={cy} textAnchor="middle" fill="currentColor">Select at least two holdings.</text>}
      </svg>
    </div>
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginTop: 10, fontSize: 12 }}>
      <span><span style={{ color: '#16865f', fontWeight: 700 }}>━━</span> Move together (positive)</span>
      <span><span style={{ color: '#d9485f', fontWeight: 700 }}>━━</span> Move oppositely (negative)</span>
      <span>Dashed = below threshold</span>
    </div>
    {selected && <div className="stat-card" style={{ marginTop: 12 }}><strong>{selected}: relationship profile</strong><p className="page-subtitle" style={{ fontSize: 13, marginTop: 6 }}>{selectedConnections.length ? `Its strongest measured relationship is with ${topConnection.source === selected ? topConnection.target : topConnection.source} (correlation ${fmt(topConnection.correlation, 3)}).` : 'No pairwise return data is available for this holding.'}</p><div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>{selectedConnections.slice(0, 5).map(edge => <span key={`${edge.source}-${edge.target}`} style={{ border: '1px solid var(--color-border)', borderRadius: 20, padding: '5px 9px', fontSize: 12 }}>{edge.source === selected ? edge.target : edge.source}: <strong style={{ color: edge.correlation < 0 ? '#d9485f' : '#16865f' }}>{fmt(edge.correlation, 3)}</strong></span>)}</div></div>}
    <p className="page-subtitle" style={{ fontSize: 12, marginTop: 10 }}>Connections are computed from historical daily returns over {result.start_date} to {result.end_date}. Correlation measures co-movement, not causation.</p>
  </div>;
}

export default function MarketXRay() {
  const [watchlist, setWatchlist] = useState([]);
  const [watchlistLoading, setWatchlistLoading] = useState(true);
  const [watchlistError, setWatchlistError] = useState('');
  const [selectedTickers, setSelectedTickers] = useState([]);
  const [weights, setWeights] = useState({});
  const [period, setPeriod] = useState('1y');
  const [threshold, setThreshold] = useState(0.65);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    getWatchlist().then(response => {
      if (cancelled) return;
      const items = (response.data || []).filter(item => item.ticker).sort((a, b) => a.ticker.localeCompare(b.ticker));
      setWatchlist(items);
      setSelectedTickers(items.map(item => item.ticker));
      setWeights(Object.fromEntries(items.map(item => [item.ticker, DEFAULT_WEIGHTS[item.ticker] ?? 10])));
      setWatchlistError('');
    }).catch(err => {
      if (!cancelled) setWatchlistError(err.response?.data?.detail || 'Could not load your watchlist. Check the backend and database connection.');
    }).finally(() => { if (!cancelled) setWatchlistLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const selectedHoldings = useMemo(() => selectedTickers.map(ticker => ({ ticker, weight: Number(weights[ticker] || 0) })), [selectedTickers, weights]);
  const weightTotal = selectedHoldings.reduce((sum, item) => sum + item.weight, 0);

  function toggleTicker(ticker) {
    setSelectedTickers(current => current.includes(ticker) ? current.filter(t => t !== ticker) : [...current, ticker]);
    setResult(null);
  }

  async function runAnalysis(event) {
    event?.preventDefault();
    if (selectedHoldings.length < 2) { setError('Select at least two stocks from your watchlist.'); return; }
    if (selectedHoldings.some(item => !Number.isFinite(item.weight) || item.weight < 0) || weightTotal <= 0) { setError('Enter valid, non-negative weights with a total greater than zero.'); return; }
    if (selectedHoldings.filter(item => item.weight > 0).length < 2) { setError('At least two selected stocks must have a positive portfolio weight.'); return; }
    setLoading(true); setError('');
    try {
      const response = await analyzePortfolio({ holdings: selectedHoldings, period, correlation_threshold: Number(threshold) });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Portfolio analysis failed. Check the backend and market-data providers.');
    } finally { setLoading(false); }
  }

  const suggestedMix = useMemo(() => result ? findLowerVolatilityMix(result) : null, [result]);

  return <div>
    <div className="page-header"><h1 className="page-title">Market X-Ray</h1><p className="page-subtitle">Explore how your holdings move together, see your sector exposure, and review portfolio risks surfaced by historical data.</p></div>
    <form className="card" onSubmit={runAnalysis} style={{ marginBottom: 'var(--space-5)' }}>
      <h2 className="section-title"><Wallet size={18} style={{ verticalAlign: 'middle', marginRight: 8 }} />Build your portfolio from Watchlist</h2>
      <p className="page-subtitle" style={{ fontSize: 13, marginTop: -4 }}>Select holdings and enter their relative weights. Only stocks already in your watchlist can be selected.</p>
      {watchlistLoading ? <p className="page-subtitle">Loading your watchlist…</p> : watchlistError ? <div className="error" role="alert">{watchlistError} <Link to="/watchlist">Open Watchlist</Link></div> : watchlist.length === 0 ? <div className="empty-state"><Wallet size={36} /><h3>Your watchlist is empty</h3><p>Add stocks to your watchlist first. They'll appear here as portfolio choices.</p><Link className="btn btn-primary" to="/search">Find stocks</Link></div> : <>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8, margin: '12px 0' }}><span className="financial-label">{selectedTickers.length} of {watchlist.length} stocks selected</span><div style={{ display: 'flex', gap: 8 }}><button type="button" className="btn btn-secondary btn-sm" onClick={() => { setSelectedTickers(watchlist.map(item => item.ticker)); setResult(null); }}>Select all</button><button type="button" className="btn btn-secondary btn-sm" onClick={() => { setSelectedTickers([]); setResult(null); }}>Clear</button></div></div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 10 }}>{watchlist.map(item => { const checked = selectedTickers.includes(item.ticker); return <div key={item.ticker} style={{ border: `1px solid ${checked ? 'var(--color-primary, #2563eb)' : 'var(--color-border)'}`, borderRadius: 10, padding: 12, display: 'flex', alignItems: 'center', gap: 10, background: checked ? 'rgba(37,99,235,0.045)' : 'transparent' }}><input type="checkbox" checked={checked} onChange={() => toggleTicker(item.ticker)} aria-label={`Include ${item.ticker}`} /><div style={{ flex: 1, minWidth: 0 }}><strong>{item.ticker}</strong><div className="page-subtitle" style={{ fontSize: 12 }}>{item.company_name || 'Watchlist holding'}</div></div><label style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12 }}><span>Weight</span><input aria-label={`${item.ticker} portfolio weight`} type="number" min="0" max="100" step="0.5" disabled={!checked} value={weights[item.ticker] ?? 10} onChange={e => setWeights(current => ({ ...current, [item.ticker]: e.target.value }))} style={{ width: 76, padding: '6px 7px', border: '1px solid var(--color-border)', borderRadius: 6, background: 'var(--color-background, white)', color: 'inherit' }} /><span>%</span></label></div>; })}</div>
        <div className="page-subtitle" style={{ fontSize: 12, marginTop: 10 }}>Entered weights total {weightTotal.toFixed(1)}%; they are normalized to 100% for analysis.</div>
      </>}
      <div className="grid grid-2" style={{ alignItems: 'end', gap: 16, marginTop: 18 }}><div><label className="financial-label" htmlFor="xray-period">Historical window</label><select id="xray-period" className="select" value={period} onChange={e => setPeriod(e.target.value)} style={{ display: 'block', width: '100%', marginTop: 8 }}><option value="3mo">3 months</option><option value="6mo">6 months</option><option value="1y">1 year</option><option value="2y">2 years</option><option value="5y">5 years</option></select></div><div><label className="financial-label" htmlFor="xray-threshold">Strong-link threshold: {Number(threshold).toFixed(2)}</label><input id="xray-threshold" type="range" min="0.4" max="0.9" step="0.05" value={threshold} onChange={e => setThreshold(Number(e.target.value))} style={{ display: 'block', width: '100%', marginTop: 14 }} /></div></div>
      <button type="submit" className="btn btn-primary" disabled={loading || watchlistLoading || !!watchlistError || watchlist.length === 0} style={{ marginTop: 16 }}>{loading ? <><RefreshCw size={16} className="spin" /> Analyzing history…</> : <><Activity size={16} /> Run Market X-Ray</>}</button>
      {error && <div className="error" role="alert" style={{ marginTop: 12 }}>{error}</div>}
    </form>

    {result && <>
      <div className="stats-grid"><Metric label="Annualized volatility" value={`${fmt(result.annualized_volatility_pct)}%`} detail="Historical portfolio estimate" /><Metric label="Trading days analyzed" value={result.observations} detail={`${result.start_date} to ${result.end_date}`} /><Metric label="Strong links found" value={result.relationships.filter(e => Math.abs(e.correlation) >= Number(threshold)).length} detail="Positive and negative relationships" /></div>
      <div className="card" style={{ marginTop: 20 }}><h2 className="section-title"><Network size={18} style={{ verticalAlign: 'middle', marginRight: 8 }} />Portfolio relationship map</h2><RelationshipGraph result={result} threshold={threshold} /></div>
      <div className="card" style={{ marginTop: 20 }}><h2 className="section-title"><PieChart size={18} style={{ verticalAlign: 'middle', marginRight: 8 }} />Where is your money invested?</h2><SectorTreeMap result={result} /></div>
      <div className="card" style={{ marginTop: 20 }}><h2 className="section-title">What should you pay attention to?</h2><p className="page-subtitle" style={{ fontSize: 13, marginTop: -2, marginBottom: 4 }}>Findings from your selected holdings and historical window.</p><InsightCards insights={buildInsights(result, suggestedMix)} /><p className="page-subtitle" style={{ fontSize: 12, marginTop: 12 }}>Historical observations and hypothetical allocation comparisons are not buy/sell instructions or forecasts.</p></div>

      <div className="card" style={{ marginTop: 20 }}><h2 className="section-title">Co-movement groups</h2><p className="page-subtitle" style={{ fontSize: 13 }}>Groups are formed from positive correlations above the selected threshold. Stocks without a strong positive link remain separate here, but their strongest positive or negative connections are still visible in the graph.</p>{result.clusters.map((cluster, i) => <div key={cluster.id} style={{ border: '1px solid var(--color-border)', borderRadius: 10, padding: 14, marginBottom: 10 }}><div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}><strong>{cluster.tickers.join(' · ')}</strong><span className="financial-label">{fmt(cluster.portfolio_weight_pct)}% of portfolio</span></div><div style={{ height: 8, background: 'var(--color-border)', borderRadius: 20, marginTop: 10, overflow: 'hidden' }}><div style={{ height: '100%', width: `${Math.min(100, Math.max(0, cluster.portfolio_weight_pct))}%`, background: COLORS[i % COLORS.length], borderRadius: 20 }} /></div><p className="page-subtitle" style={{ fontSize: 12, marginTop: 8 }}>Estimated variance contribution: {fmt(cluster.risk_contribution_pct)}%</p></div>)}</div>
    </>}
  </div>;
}
