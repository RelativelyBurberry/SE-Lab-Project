import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Search, Star, Zap, Activity, FileText, Menu, X, ScanSearch, LogOut, UserRound
} from 'lucide-react';
import './index.css';

// Import pages
import Dashboard from './pages/Dashboard';
import StockSearch from './pages/StockSearch';
import Watchlist from './pages/Watchlist';
import StrategyBuilder from './pages/StrategyBuilder';
import Research from './pages/Research';
import ReportHistory from './pages/ReportHistory';
import MarketXRay from './pages/MarketXRay';
import AuthPage from './pages/AuthPage';
import { getCurrentUser } from './api';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/search', icon: Search, label: 'Stock Search' },
  { path: '/watchlist', icon: Star, label: 'Watchlist' },
  { path: '/strategy', icon: Zap, label: 'Strategy Builder' },
  { path: '/research', icon: Activity, label: 'AI Research' },
  { path: '/reports', icon: FileText, label: 'Reports' },
  { path: '/market-xray', icon: ScanSearch, label: 'Market X-Ray' },
];

function Sidebar({ isOpen, onNavigate, user, onSignOut }) {
  const location = useLocation();

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`} aria-label="Main navigation">
      <div className="sidebar-header">
        <h1>AlphaForge AI</h1>
        <p>Investment Intelligence</p>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${isActive ? 'active' : ''}`}
              aria-current={isActive ? 'page' : undefined}
              onClick={onNavigate}
            >
              <item.icon />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="sidebar-account">
        <div className="sidebar-account-avatar"><UserRound size={17} /></div>
        <div className="sidebar-account-copy"><strong>{user?.email?.split('@')[0] || 'Your account'}</strong><span>{user?.email || ''}</span></div>
        <button className="sidebar-signout" onClick={onSignOut} title="Sign out" aria-label="Sign out"><LogOut size={17} /></button>
      </div>
    </aside>
  );
}

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('alphaforge_user') || 'null'); } catch { return null; }
  });
  const [authReady, setAuthReady] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const token = localStorage.getItem('alphaforge_token');
    if (!token) { setUser(null); setAuthReady(true); return; }
    getCurrentUser().then(({ data }) => {
      setUser(data);
      localStorage.setItem('alphaforge_user', JSON.stringify(data));
    }).catch(() => {
      localStorage.removeItem('alphaforge_token');
      localStorage.removeItem('alphaforge_user');
      setUser(null);
    }).finally(() => setAuthReady(true));
  }, []);

  const signOut = () => {
    localStorage.removeItem('alphaforge_token');
    localStorage.removeItem('alphaforge_user');
    setUser(null);
  };

  // Close mobile sidebar on route change
  useEffect(() => {
    setSidebarOpen(false);
    // Scroll to top on navigation
    window.scrollTo(0, 0);
  }, [location.pathname]);

  if (!authReady) return <div className="auth-loading"><div className="auth-loading-mark"><Activity size={24} /></div><span>Opening your workspace…</span></div>;
  if (!user) return <AuthPage onAuthenticated={(nextUser) => setUser(nextUser)} />;

  return (
    <div className="app-container">
      <Sidebar isOpen={sidebarOpen} onNavigate={() => setSidebarOpen(false)} user={user} onSignOut={signOut} />

      {/* Mobile top bar with menu toggle */}
      <div className="mobile-topbar">
        <button
          className="mobile-menu-btn"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          aria-label={sidebarOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={sidebarOpen}
        >
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        <span className="mobile-topbar-title">AlphaForge AI</span>
      </div>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/search" element={<StockSearch />} />
          <Route path="/watchlist" element={<Watchlist />} />
          <Route path="/strategy" element={<StrategyBuilder />} />
          <Route path="/research" element={<Research />} />
          <Route path="/reports" element={<ReportHistory />} />
          <Route path="/market-xray" element={<MarketXRay />} />
        </Routes>
      </main>
    </div>
  );
}

function AppShell() {
  return (
    <Router>
      <App />
    </Router>
  );
}

export default AppShell;
