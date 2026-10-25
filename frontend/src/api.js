import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach the signed-in user's bearer token to API requests.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('alphaforge_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Authentication
export const login = (email, password) => api.post('/auth/login', { email, password });
export const register = (email, password) => api.post('/auth/register', { email, password });
export const getCurrentUser = () => api.get('/auth/me');

// Health Check
export const getHealth = () => api.get('/health');

// Market Data
export const searchStock = (query) => api.get(`/api/market/search/${query}`);
export const searchCompanies = (query, limit = 5) => 
  api.get('/api/market/search', { params: { q: query, limit } });
export const getQuote = (ticker) => api.get(`/api/market/quote/${ticker}`);
export const getCompanyInfo = (ticker) => api.get(`/api/market/company/${ticker}`);
export const getTechnicalIndicators = (ticker) => api.get(`/api/market/indicators/${ticker}`);
export const getCompanyNews = (ticker, companyName) => 
  api.get(`/api/market/news/${ticker}`, { params: { company_name: companyName } });

// Portfolio risk analysis (Market X-Ray)
export const analyzePortfolio = (payload) => api.post("/api/portfolio/xray", payload);

// Watchlist
export const getWatchlist = () => api.get('/api/watchlist');
export const addToWatchlist = (ticker, companyName) => 
  api.post('/api/watchlist', { ticker, company_name: companyName });
export const removeFromWatchlist = (ticker) => api.delete(`/api/watchlist/${ticker}`);

// Strategies
export const getStrategies = () => api.get('/api/strategies');
export const createStrategy = (data) => api.post('/api/strategies', data);
export const deleteStrategy = (id) => api.delete(`/api/strategies/${id}`);

// Screening
export const screenStocks = (strategy) => api.post('/api/screen', strategy);

// Research Reports
export const generateResearchReport = (ticker) => api.post(`/api/research/${ticker}`);
export const getReportHistory = () => api.get('/api/research/history');
export const getSavedReport = (id) => api.get(`/api/research/${id}`);

export default api;
