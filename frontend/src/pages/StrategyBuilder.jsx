import React, { useState, useEffect } from 'react';
import { getStrategies, createStrategy, deleteStrategy, screenStocks, getWatchlist, addToWatchlist } from '../api';
import { Zap, Plus, Trash2, Play, ChevronDown, ChevronUp, BookmarkPlus, Check, Search, ExternalLink, BookOpen, Sparkles } from 'lucide-react';


const INDICATORS = [
  { field: 'price', label: 'Price', group: 'Price & trend', description: 'The latest available market price.', interpretation: 'Compare it with moving averages or a defined price level. Price alone has no universal good or bad value.', example: 'Price > 50', url: 'https://www.investor.gov/introduction-investing/investing-basics/investment-products/stocks' },
  { field: 'sma_20', label: 'SMA 20', group: 'Price & trend', description: 'Average closing price over the last 20 trading sessions (about one month).', interpretation: 'Price above a rising SMA can indicate short-term strength; below a falling SMA can indicate weakness. Sideways markets create whipsaws.', example: 'Price > SMA 20', url: 'https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/moving-averages-simple-and-exponential' },
  { field: 'sma_50', label: 'SMA 50', group: 'Price & trend', description: 'Average closing price over the last 50 trading sessions (about one quarter).', interpretation: 'Often used as a medium-term trend filter. Above is not automatically a buy signal; context matters.', example: 'Price > SMA 50', url: 'https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/moving-averages-simple-and-exponential' },
  { field: 'sma_200', label: 'SMA 200', group: 'Price & trend', description: 'Average closing price over roughly 200 trading sessions (about one year).', interpretation: 'Price above a rising 200-day average is commonly used as a long-term uptrend filter. It is lagging and may react slowly to reversals.', example: 'Price > SMA 200', url: 'https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/moving-averages-simple-and-exponential' },
  { field: 'ema_12', label: 'EMA 12', group: 'Price & trend', description: 'A 12-session moving average that weights recent prices more heavily.', interpretation: 'Moves faster than an SMA. Useful for short-term trend and crossover rules, but can generate more false signals.', example: 'EMA 12 > EMA 26', url: 'https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/moving-averages-simple-and-exponential' },
  { field: 'ema_26', label: 'EMA 26', group: 'Price & trend', description: 'A 26-session exponentially weighted moving average.', interpretation: 'Often paired with EMA 12 in MACD-style trend rules. Its value is a price level, not a standalone rating.', example: 'EMA 12 > EMA 26', url: 'https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/moving-averages-simple-and-exponential' },
  { field: 'rsi_14', label: 'RSI 14', group: 'Momentum', description: 'A 0–100 oscillator measuring the speed and magnitude of recent price moves.', interpretation: 'Below 30 is often called oversold; above 70 overbought. In strong trends RSI can stay extreme, so these are not automatic reversal signals.', example: 'RSI 14 < 30', url: 'https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi' },
  { field: 'macd', label: 'MACD', group: 'Momentum', description: 'Difference between the 12-period and 26-period exponential moving averages.', interpretation: 'Positive MACD means the shorter EMA is above the longer EMA. Rising/positive can reflect momentum, but MACD is lagging and is not directionally reliable in every regime.', example: 'MACD > 0', url: 'https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/macd-moving-average-convergence-divergence-oscillator' },
  { field: 'macd_signal', label: 'MACD Signal', group: 'Momentum', description: 'Nine-period EMA of the MACD line.', interpretation: 'MACD crossing above its signal line is commonly treated as improving momentum; crossovers can whipsaw in sideways markets.', example: 'MACD > MACD Signal', url: 'https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/macd-moving-average-convergence-divergence-oscillator' },
  { field: 'macd_histogram', label: 'MACD Histogram', group: 'Momentum', description: 'Difference between MACD and its signal line.', interpretation: 'Above zero means MACD is above its signal line. A rising histogram can suggest strengthening momentum, not guaranteed future gains.', example: 'MACD Histogram > 0', url: 'https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/macd-moving-average-convergence-divergence-oscillator' },
  { field: 'price_vs_sma_50', label: 'Price vs SMA 50 (%)', group: 'Price & trend', description: 'Percentage distance between current price and the 50-session simple moving average.', interpretation: 'Above 0 means price is above its 50-session average; below 0 means it is below. The magnitude is the percentage distance.', example: 'Price vs SMA 50 (%) > 0', url: 'https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/moving-averages-simple-and-exponential' },
  { field: 'price_vs_sma_200', label: 'Price vs SMA 200 (%)', group: 'Price & trend', description: 'Percentage distance between current price and the 200-session simple moving average.', interpretation: 'Above 0 means price is above its long-term average. It is a trend filter, not a guarantee of future performance.', example: 'Price vs SMA 200 (%) > 0', url: 'https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/moving-averages-simple-and-exponential' },
  { field: 'sma_20_vs_sma_50', label: 'SMA 20 vs SMA 50 (%)', group: 'Price & trend', description: 'Percentage difference between the 20-session and 50-session moving averages.', interpretation: 'Above 0 means the shorter average is above the medium-term average, a commonly used bullish trend signal. It can lag and whipsaw.', example: 'SMA 20 vs SMA 50 (%) > 0', url: 'https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/moving-averages-simple-and-exponential' },
  { field: 'ema_12_vs_ema_26', label: 'EMA 12 vs EMA 26 (%)', group: 'Momentum', description: 'Percentage difference between the 12-session and 26-session exponential moving averages.', interpretation: 'Above 0 means EMA 12 is above EMA 26, consistent with positive short-term momentum. It is similar in spirit to MACD.', example: 'EMA 12 vs EMA 26 (%) > 0', url: 'https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/macd-moving-average-convergence-divergence-oscillator' },
  { field: 'roc_20', label: 'ROC 20 (%)', group: 'Momentum', description: 'Percentage price change over the last 20 trading sessions.', interpretation: 'Positive means price rose over the lookback; negative means it fell. Momentum can persist, but sharp reversals are possible.', example: 'ROC 20 (%) > 0', url: 'https://www.quantconnect.com/research' },
  { field: 'volatility_20', label: 'Volatility 20 (annualized %)', group: 'Risk', description: 'Annualized standard deviation of daily returns over the last 20 sessions.', interpretation: 'Higher means larger historical fluctuations, not necessarily bearish direction. It is backward-looking and can jump after events.', example: 'Volatility 20 < 40', url: 'https://www.investor.gov/introduction-investing/investing-basics/investment-products' },
  { field: 'volume', label: 'Volume', group: 'Trading activity', description: 'Most recent available trading-session volume.', interpretation: 'High volume can confirm that a move has participation, but volume levels differ greatly between securities. Compare with the same ticker’s own history.', example: 'Volume > 1000000', url: 'https://www.investor.gov/introduction-investing/investing-basics/glossary/volume' },
  { field: 'market_cap', label: 'Market cap', group: 'Fundamentals', description: 'Share price multiplied by shares outstanding; a rough measure of company size.', interpretation: 'Higher market cap generally means a larger company, not necessarily a better investment. Values are provider-reported and may be missing.', example: 'Market cap > 10000000000', url: 'https://www.investor.gov/introduction-investing/investing-basics/glossary/market-capitalization' },
  { field: 'pe_ratio', label: 'P/E ratio', group: 'Fundamentals', description: 'Share price divided by earnings per share, where earnings are positive and available.', interpretation: 'Lower P/E may mean cheaper valuation or weaker growth prospects. Compare within similar industries and check earnings quality; negative/absent earnings make it unhelpful.', example: 'P/E < 25', url: 'https://www.investor.gov/introduction-investing/investing-basics/glossary/price-earnings-ratio' },
  { field: 'beta', label: 'Beta', group: 'Risk', description: 'Provider-reported estimate of sensitivity to broad market movements.', interpretation: 'Above 1 usually indicates greater historical market sensitivity; below 1 lower sensitivity. Beta is backward-looking and does not capture all risks.', example: 'Beta < 1', url: 'https://www.investor.gov/introduction-investing/investing-basics/glossary/beta' },
  { field: 'dividend_yield', label: 'Dividend yield', group: 'Fundamentals', description: 'Annual dividend relative to share price, as reported by the data provider.', interpretation: 'Higher yield can increase income but may also reflect a falling share price or an unsustainable dividend. Check units and payout sustainability.', example: 'Dividend yield > 0.02', url: 'https://www.investor.gov/introduction-investing/investing-basics/investment-products/stocks' },
];

const STRATEGY_TEMPLATES = [
  { id: 'trend-200', name: 'Long-term trend filter', category: 'Trend following', difficulty: 'Beginner', description: 'Find stocks trading above their long-term average. Commonly used to avoid taking bullish positions against a weak primary trend.', conditions: [{ field: 'price_vs_sma_200', operator: '>', value: 0 }], natural: 'Find stocks where price is above the 200-day moving average', refs: [{ label: 'Moving averages', url: INDICATORS.find(x => x.field === 'sma_200').url }], limitation: 'This checks price relative to the 200-session average, but does not confirm that the average itself is rising. It does not backtest returns.' },
  { id: 'rsi-reversion', name: 'RSI oversold watch', category: 'Mean reversion', difficulty: 'Beginner', description: 'Surface stocks with low 14-session RSI for further review. Oversold conditions can persist during strong downtrends.', conditions: [{ field: 'rsi_14', operator: '<', value: 30 }], natural: 'Find stocks with RSI below 30', refs: [{ label: 'RSI reference', url: INDICATORS.find(x => x.field === 'rsi_14').url }], limitation: 'An RSI reading below 30 is not a buy signal by itself; no exit or holding-period test is performed.' },
  { id: 'macd-positive', name: 'Positive MACD momentum', category: 'Momentum', difficulty: 'Beginner', description: 'Look for stocks whose short-term EMA is above their longer-term EMA, indicating positive MACD.', conditions: [{ field: 'macd', operator: '>', value: 0 }], natural: 'Find stocks with positive MACD', refs: [{ label: 'MACD reference', url: INDICATORS.find(x => x.field === 'macd').url }], limitation: 'Positive MACD is a lagging momentum measure and may underperform in sideways markets.' },
  { id: 'value-screen', name: 'Lower P/E screen', category: 'Value factor', difficulty: 'Beginner', description: 'Filter for stocks below a chosen P/E threshold. This is a valuation screen, not a complete value strategy.', conditions: [{ field: 'pe_ratio', operator: '>', value: 0 }, { field: 'pe_ratio', operator: '<', value: 25 }], natural: 'Find stocks with positive earnings and P/E below 25', refs: [{ label: 'P/E ratio', url: INDICATORS.find(x => x.field === 'pe_ratio').url }], limitation: 'P/E varies by sector and can be distorted by one-off earnings. Fundamentals may be unavailable for some tickers.' },
  { id: 'low-beta', name: 'Lower-beta candidates', category: 'Risk-aware screen', difficulty: 'Beginner', description: 'Find stocks with provider-reported beta below one as a rough market-sensitivity filter.', conditions: [{ field: 'beta', operator: '>', value: 0 }, { field: 'beta', operator: '<', value: 1 }], natural: 'Find stocks with beta below 1', refs: [{ label: 'Beta reference', url: INDICATORS.find(x => x.field === 'beta').url }], limitation: 'Beta is historical, can change over time, and does not measure company-specific or tail risk.' },
  { id: 'sma-crossover-proxy', name: 'Price above medium-term average', category: 'Trend following', difficulty: 'Beginner', description: 'A simple trend filter used to shortlist stocks above their 50-session average.', conditions: [{ field: 'price_vs_sma_50', operator: '>', value: 0 }], natural: 'Find stocks where price is above the 50-day moving average', refs: [{ label: 'Moving averages', url: INDICATORS.find(x => x.field === 'sma_50').url }], limitation: 'This uses the price-to-average relationship as a trend filter, not a full crossover backtest. Signals can whipsaw in sideways markets.' },
  { id: 'sma-cross', name: 'Short-term trend confirmation', category: 'Trend following', difficulty: 'Beginner', description: 'Find stocks where the 20-session average is above the 50-session average.', conditions: [{ field: 'sma_20_vs_sma_50', operator: '>', value: 0 }], natural: 'Find stocks where the 20-day moving average is above the 50-day moving average', refs: [{ label: 'Moving averages', url: INDICATORS.find(x => x.field === 'sma_20').url }], limitation: 'A moving-average relationship is lagging and is not a substitute for transaction-cost-aware backtesting.' },
  { id: 'roc-momentum', name: 'One-month price momentum', category: 'Momentum', difficulty: 'Beginner', description: 'Find stocks with positive price change over the last 20 trading sessions.', conditions: [{ field: 'roc_20', operator: '>', value: 0 }], natural: 'Find stocks with positive 20-day rate of change', refs: [{ label: 'QuantConnect Research', url: 'https://www.quantconnect.com/research' }], limitation: 'A positive recent return does not establish that momentum will continue. This simple screen ignores costs and portfolio construction.' },
  { id: 'low-volatility', name: 'Lower realized volatility', category: 'Risk-aware screen', difficulty: 'Intermediate', description: 'Shortlist stocks whose recent annualized volatility is below a chosen threshold.', conditions: [{ field: 'volatility_20', operator: '<', value: 40 }], natural: 'Find stocks with 20-day annualized volatility below 40 percent', refs: [{ label: 'QuantConnect Research', url: 'https://www.quantconnect.com/research' }], limitation: 'Volatility is backward-looking, can rise quickly, and is not the same as total investment risk.' },
  { id: 'ema-momentum', name: 'EMA momentum alignment', category: 'Momentum', difficulty: 'Beginner', description: 'Find stocks where the 12-session EMA is above the 26-session EMA.', conditions: [{ field: 'ema_12_vs_ema_26', operator: '>', value: 0 }], natural: 'Find stocks where EMA 12 is above EMA 26', refs: [{ label: 'MACD reference', url: INDICATORS.find(x => x.field === 'macd').url }], limitation: 'This is a trend/momentum filter, not a predictive guarantee; whipsaws are common in choppy markets.' },
];

function StrategyBuilder() {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [useAI, setUseAI] = useState(true);
  
  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [naturalLanguage, setNaturalLanguage] = useState('');
  const [conditions, setConditions] = useState([]);
  
  // Screening results
  const [screeningResults, setScreeningResults] = useState(null);
  const [screening, setScreening] = useState(false);
  const [expandedStrategy, setExpandedStrategy] = useState(null);
  const [indicatorSearch, setIndicatorSearch] = useState('');
  const [activeIndicator, setActiveIndicator] = useState('rsi_14');
  const [templateFilter, setTemplateFilter] = useState('All');
  const [watchlistTickers, setWatchlistTickers] = useState(new Set());
  const [watchlistBusy, setWatchlistBusy] = useState(new Set());
  const [watchlistMessage, setWatchlistMessage] = useState({});

  useEffect(() => {
    loadStrategies();
    getWatchlist().then(r => setWatchlistTickers(new Set((r.data || []).map(x => x.ticker.toUpperCase())))).catch(() => {});
  }, []);

  const loadStrategies = async () => {
    try {
      const response = await getStrategies();
      setStrategies(response.data);
      setError(null);
    } catch (err) {
      if (err.response?.status === 503) {
        setError('Strategy storage requires database configuration.');
      } else {
        setError('Failed to load strategies: ' + err.message);
      }
    }
  };

  const handleAddCondition = (field = 'rsi_14', operator = '<', value = 70) => {
    setConditions(prev => [...prev, { field, operator, value }]);
  };

  const applyTemplate = (template) => {
    setName(template.name);
    setDescription(template.description + ' Research-inspired template; review assumptions before use.');
    setConditions(template.conditions.map(c => ({ ...c })));
    setNaturalLanguage(template.natural);
    setUseAI(false);
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const addResultToWatchlist = async (result) => {
    const ticker = result.ticker.toUpperCase();
    if (watchlistTickers.has(ticker)) return;
    setWatchlistBusy(prev => new Set(prev).add(ticker));
    setWatchlistMessage(prev => ({ ...prev, [ticker]: '' }));
    try {
      await addToWatchlist(ticker, result.company_name);
      setWatchlistTickers(prev => new Set(prev).add(ticker));
      setWatchlistMessage(prev => ({ ...prev, [ticker]: 'Added to Watchlist' }));
    } catch (err) {
      if (err.response?.status === 400) {
        setWatchlistTickers(prev => new Set(prev).add(ticker));
        setWatchlistMessage(prev => ({ ...prev, [ticker]: 'Already in Watchlist' }));
      } else {
        setWatchlistMessage(prev => ({ ...prev, [ticker]: err.response?.data?.detail || 'Could not add. Try again.' }));
      }
    } finally {
      setWatchlistBusy(prev => { const next = new Set(prev); next.delete(ticker); return next; });
    }
  };

  const handleRemoveCondition = (index) => {
    setConditions(conditions.filter((_, i) => i !== index));
  };

  const handleConditionChange = (index, field, value) => {
    const updated = [...conditions];
    updated[index][field] = value;
    setConditions(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = {
        name,
        description,
      };

      if (useAI && naturalLanguage) {
        data.natural_language_input = naturalLanguage;
      } else {
        data.conditions = conditions;
      }

      await createStrategy(data);
      await loadStrategies();
      
      // Reset form
      setName('');
      setDescription('');
      setNaturalLanguage('');
      setConditions([]);
      setShowForm(false);
    } catch (err) {
      if (err.response?.status === 503) {
        setError('Strategy creation requires AI services or database configuration.');
      } else {
        setError('Failed to create strategy: ' + err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this strategy?')) return;

    try {
      await deleteStrategy(id);
      await loadStrategies();
    } catch (err) {
      alert('Failed to delete strategy: ' + err.message);
    }
  };

  const handleScreen = async (strategy) => {
    setScreening(true);
    setScreeningResults(null);
    setError(null);

    try {
      const response = await screenStocks({
        name: strategy.name,
        conditions: strategy.conditions
      });
      setScreeningResults(response.data);
      setExpandedStrategy(strategy.id);
    } catch (err) {
      setError('Failed to screen stocks: ' + err.message);
    } finally {
      setScreening(false);
    }
  };

  const fieldOptions = INDICATORS.map(({ field, label }) => ({ value: field, label }));

  const operatorOptions = [
    { value: '>', label: '>' },
    { value: '<', label: '<' },
    { value: '>=', label: '>=' },
    { value: '<=', label: '<=' },
    { value: '=', label: '=' },
  ];

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">Strategy Builder</h1>
        <p className="page-subtitle">Create quantitative stock screening strategies</p>
      </div>

      {/* Research-inspired strategy library */}
      <div className="card" style={{ marginBottom: 'var(--space-5)' }}>
        <div className="flex-between" style={{ alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
          <div><h2 className="section-title" style={{ marginBottom: 4 }}><Sparkles size={18} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: 7 }} />Strategy Library</h2><p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>Research-inspired starting points from widely used quant concepts. These are screening templates, not proven profitable systems.</p></div>
          <select className="select" aria-label="Filter strategy templates" value={templateFilter} onChange={e => setTemplateFilter(e.target.value)} style={{ maxWidth: 190 }}><option>All</option>{[...new Set(STRATEGY_TEMPLATES.map(t => t.category))].map(c => <option key={c}>{c}</option>)}</select>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(245px, 1fr))', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
          {STRATEGY_TEMPLATES.filter(t => templateFilter === 'All' || t.category === templateFilter).map(template => <article key={template.id} style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: 'var(--space-4)', background: 'var(--color-surface)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}><span style={{ fontSize: 10, fontWeight: 700, color: '#0369a1', background: '#e0f2fe', padding: '4px 7px', borderRadius: 999 }}>{template.category}</span><span style={{ color: 'var(--color-text-muted)', fontSize: 11 }}>{template.difficulty}</span></div>
            <h3 style={{ fontSize: 'var(--font-size-base)', margin: '12px 0 6px' }}>{template.name}</h3><p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', lineHeight: 1.5 }}>{template.description}</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, margin: '10px 0' }}>{[...new Set(template.conditions.map(c => c.field))].map(f => <span key={f} style={{ fontSize: 11, background: 'var(--color-surface-tertiary)', padding: '3px 6px', borderRadius: 4 }}>{INDICATORS.find(i => i.field === f)?.label || f}</span>)}</div>
            <details style={{ margin: '10px 0', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}><summary style={{ cursor: 'pointer', fontWeight: 600 }}>Limitations & sources</summary><p style={{ marginTop: 6 }}>{template.limitation}</p><div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 7 }}>{template.refs.map(ref => <a key={ref.url} href={ref.url} target="_blank" rel="noreferrer">{ref.label} <ExternalLink size={10} style={{ display: 'inline' }} /></a>)}</div></details>
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => applyTemplate(template)} style={{ width: '100%', justifyContent: 'center' }}>Use this strategy <ChevronDown size={14} /></button>
          </article>)}
        </div>
        <p style={{ marginTop: 12, fontSize: 11, color: 'var(--color-text-muted)' }}>Background reading: <a href="https://github.com/skavvathas/Equities-quant-strategies" target="_blank" rel="noreferrer">Equities quant strategies</a> · <a href="https://www.quantconnect.com/research" target="_blank" rel="noreferrer">QuantConnect Research</a> · <a href="https://github.com/efJerry/WorldQuant-Brain-Operators" target="_blank" rel="noreferrer">WorldQuant BRAIN operator reference (community-maintained)</a>. These links are learning resources, not endorsements.</p>
      </div>

      {/* Create Strategy Card */}
      <div className="card">
        <div className="flex-between">
          <div>
            <h2 className="section-title" style={{ margin: 0 }}>Create Strategy</h2>
          </div>
          <button 
            onClick={() => setShowForm(!showForm)}
            className="btn btn-primary"
          >
            <Plus size={16} />
            New Strategy
          </button>
        </div>

        {/* Strategy Form */}
        {showForm && (
          <form onSubmit={handleSubmit} style={{ marginTop: 'var(--space-6)' }}>
            <div className="input-group">
              <label className="input-label">Strategy Name</label>
              <input
                type="text"
                className="input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="e.g., Momentum Breakout"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Description (Optional)</label>
              <textarea
                className="input textarea"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description of the strategy"
              />
            </div>

            <div className="input-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={useAI}
                  onChange={(e) => setUseAI(e.target.checked)}
                  style={{ width: '16px', height: '16px' }}
                />
                <span className="input-label" style={{ margin: 0 }}>
                  Use AI to parse natural language (requires Groq API)
                </span>
              </label>
            </div>

            {useAI ? (
              <div className="input-group">
                <label className="input-label">Natural Language Strategy</label>
                <textarea
                  className="input textarea"
                  value={naturalLanguage}
                  onChange={(e) => setNaturalLanguage(e.target.value)}
                  required={useAI}
                  placeholder="e.g., Find stocks where RSI is below 30 and price is above 50-day moving average"
                />
                <div style={{ marginTop: 'var(--space-3)', padding: 'var(--space-4)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', background: 'var(--color-surface-secondary)' }}>
                  <div className="flex-between" style={{ gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                    <div><h4 style={{ margin: 0, fontSize: 'var(--font-size-sm)' }}><BookOpen size={15} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: 6 }} />Indicator explorer</h4><p style={{ margin: '4px 0 0', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>Hover or focus a tag to learn what it means. Click to add an example to your strategy text.</p></div>
                    <div style={{ position: 'relative', minWidth: 180 }}><Search size={14} style={{ position: 'absolute', left: 9, top: 10, color: 'var(--color-text-muted)' }} /><input aria-label="Search indicators" className="input" value={indicatorSearch} onChange={e => setIndicatorSearch(e.target.value)} placeholder="Search indicators" style={{ paddingLeft: 30, minHeight: 34 }} /></div>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 'var(--space-3)' }}>
                    {INDICATORS.filter(ind => `${ind.label} ${ind.group} ${ind.description}`.toLowerCase().includes(indicatorSearch.toLowerCase())).map(ind => <button key={ind.field} type="button" title={`${ind.description}

Interpretation: ${ind.interpretation}
Example: ${ind.example}`} onMouseEnter={() => setActiveIndicator(ind.field)} onFocus={() => setActiveIndicator(ind.field)} onClick={() => setNaturalLanguage(prev => `${prev.trim()}${prev.trim() ? ' and ' : ''}${ind.example}`)} style={{ border: '1px solid #bfdbfe', background: '#eff6ff', color: '#1d4ed8', borderRadius: 999, padding: '6px 10px', fontSize: 12, cursor: 'pointer' }} aria-label={`${ind.label}. ${ind.description} Interpretation: ${ind.interpretation}`}>
                      {ind.label} <span style={{ opacity: .65 }}>ⓘ</span>
                    </button>)}
                  </div>
                  <div style={{ marginTop: 'var(--space-3)', display: 'grid', gap: 8 }}>
                    {(() => { const ind = INDICATORS.find(item => item.field === activeIndicator) || INDICATORS[0]; return <div key={ind.field} style={{ fontSize: 'var(--font-size-xs)', padding: '12px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 6 }}><strong>{ind.label} · {ind.group}</strong><div style={{ color: 'var(--color-text-secondary)', marginTop: 4 }}>{ind.description}</div><div style={{ color: 'var(--color-text-muted)', marginTop: 5 }}><strong>How to interpret it:</strong> {ind.interpretation}</div><div style={{ marginTop: 5 }}><strong>Example:</strong> <code>{ind.example}</code></div><a href={ind.url} target="_blank" rel="noreferrer" style={{ display: 'inline-flex', gap: 4, alignItems: 'center', marginTop: 7 }}>Read reference <ExternalLink size={11} /></a></div>; })()}
                  </div>
                </div>
              </div>
            ) : (
              <div>
                <div className="flex-between" style={{ marginBottom: 'var(--space-3)' }}>
                  <label className="input-label" style={{ margin: 0 }}>Conditions</label>
                  <button 
                    type="button"
                    onClick={handleAddCondition}
                    className="btn btn-secondary btn-sm"
                  >
                    <Plus size={14} />
                    Add Condition
                  </button>
                </div>

                {conditions.map((condition, index) => (
                  <div key={index} style={{ display: 'flex', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                    <select
                      className="select"
                      value={condition.field}
                      onChange={(e) => handleConditionChange(index, 'field', e.target.value)}
                      style={{ flex: 2 }}
                    >
                      {fieldOptions.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>

                    <select
                      className="select"
                      value={condition.operator}
                      onChange={(e) => handleConditionChange(index, 'operator', e.target.value)}
                      style={{ flex: 1 }}
                    >
                      {operatorOptions.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>

                    <input
                      type="number"
                      className="input"
                      value={condition.value}
                      onChange={(e) => handleConditionChange(index, 'value', parseFloat(e.target.value))}
                      step="0.01"
                      required
                      style={{ flex: 2 }}
                    />

                    <button
                      type="button"
                      onClick={() => handleRemoveCondition(index)}
                      className="btn btn-danger btn-sm"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}

                {conditions.length === 0 && (
                  <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                    Click "Add Condition" to define screening rules
                  </p>
                )}
              </div>
            )}

            <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-5)' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Creating...' : 'Create Strategy'}
              </button>
              <button 
                type="button" 
                onClick={() => setShowForm(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>

      {error && <div className="error">{error}</div>}

      {/* Saved Strategies */}
      {strategies.length > 0 && (
        <div className="card">
          <h2 className="section-title">Saved Strategies ({strategies.length})</h2>
          
          {strategies.map((strategy) => (
            <div key={strategy.id} style={{ 
              padding: 'var(--space-4)', 
              border: '1px solid var(--color-border)', 
              borderRadius: 'var(--radius-md)', 
              marginBottom: 'var(--space-3)',
              backgroundColor: 'var(--color-surface)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: expandedStrategy === strategy.id ? 'var(--space-3)' : 0 }}>
                <div style={{ flex: 1 }}>
                  <h4 style={{ fontWeight: 600, marginBottom: 'var(--space-1)', fontSize: 'var(--font-size-base)' }}>{strategy.name}</h4>
                  {strategy.description && (
                    <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-2)' }}>
                      {strategy.description}
                    </p>
                  )}
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-subtle)' }}>
                    {strategy.conditions.length} condition{strategy.conditions.length !== 1 ? 's' : ''} • Created {new Date(strategy.created_at).toLocaleDateString()}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                  <button
                    onClick={() => handleScreen(strategy)}
                    className="btn btn-primary btn-sm"
                    disabled={screening}
                  >
                    <Play size={14} />
                    Screen
                  </button>
                  <button
                    onClick={() => handleDelete(strategy.id)}
                    className="btn btn-danger btn-sm"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              {/* Screening Results */}
              {expandedStrategy === strategy.id && screeningResults && (
                <div style={{ marginTop: 'var(--space-4)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-border)' }}>
                  <h4 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, marginBottom: 'var(--space-3)' }}>
                    Screening Results
                  </h4>
                  <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>
                    {screeningResults.strategy_name} • {screeningResults.total_matched} matches out of {screeningResults.total_screened} stocks screened
                  </p>

                  {screeningResults.results.length === 0 ? (
                    <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', padding: 'var(--space-4)', textAlign: 'center', backgroundColor: 'var(--color-surface-secondary)', borderRadius: 'var(--radius-md)' }}>
                      No stocks matched the strategy criteria
                    </p>
                  ) : (
                    <div style={{ overflowX: 'auto' }}>
                      <table className="table">
                        <thead>
                          <tr>
                            <th>Rank</th>
                            <th>Ticker</th>
                            <th>Company</th>
                            <th style={{ textAlign: 'right' }}>Score</th>
                            <th>Matched Conditions</th>
                            <th>Watchlist</th>
                          </tr>
                        </thead>
                        <tbody>
                          {screeningResults.results.map((result, index) => (
                            <tr key={result.ticker}>
                              <td className="tabular-nums">{index + 1}</td>
                              <td style={{ fontWeight: 600 }} className="tabular-nums">{result.ticker}</td>
                              <td>{result.company_name}</td>
                              <td style={{ textAlign: 'right' }}>
                                <span className="badge badge-success">
                                  {result.score.toFixed(0)}%
                                </span>
                              </td>
                              <td style={{ fontSize: 'var(--font-size-xs)' }}>
                                {result.matched_conditions.map((cond, i) => (
                                  <div key={i} style={{ color: 'var(--color-success)' }}>✓ {cond}</div>
                                ))}
                              </td>
                              <td style={{ minWidth: 150 }}>
                                <button type="button" className={`btn btn-sm ${watchlistTickers.has(result.ticker.toUpperCase()) ? 'btn-secondary' : 'btn-primary'}`} disabled={watchlistTickers.has(result.ticker.toUpperCase()) || watchlistBusy.has(result.ticker.toUpperCase())} onClick={() => addResultToWatchlist(result)}>
                                  {watchlistTickers.has(result.ticker.toUpperCase()) ? <Check size={13} /> : <BookmarkPlus size={13} />}
                                  {watchlistBusy.has(result.ticker.toUpperCase()) ? 'Adding…' : watchlistTickers.has(result.ticker.toUpperCase()) ? 'In Watchlist' : 'Add to Watchlist'}
                                </button>
                                {watchlistMessage[result.ticker.toUpperCase()] && <div style={{ fontSize: 10, marginTop: 4, color: watchlistTickers.has(result.ticker.toUpperCase()) ? 'var(--color-success)' : 'var(--color-danger)' }}>{watchlistMessage[result.ticker.toUpperCase()]}</div>}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Screening Loading */}
      {screening && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Screening stocks...</p>
        </div>
      )}
    </div>
  );
}

export default StrategyBuilder;
