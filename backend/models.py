from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Market Data Models
class Quote(BaseModel):
    ticker: str
    price: float
    change: float
    change_percent: float
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    timestamp: datetime
    source: str = "yahoo_finance"

class HistoricalData(BaseModel):
    ticker: str
    dates: List[str]
    open: List[float]
    high: List[float]
    low: List[float]
    close: List[float]
    volume: List[int]
    source: str = "yahoo_finance"

class CompanyInfo(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    source: str = "yahoo_finance"

# Technical Analysis Models
class TechnicalIndicators(BaseModel):
    ticker: str
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    price_vs_sma_50: Optional[float] = None
    price_vs_sma_200: Optional[float] = None
    sma_20_vs_sma_50: Optional[float] = None
    ema_12_vs_ema_26: Optional[float] = None
    roc_20: Optional[float] = None
    volatility_20: Optional[float] = None
    current_volume: Optional[int] = None
    current_price: float
    calculated_at: datetime

# News Models
class NewsArticle(BaseModel):
    title: str
    source: str
    published_at: Optional[datetime] = None
    url: str
    description: Optional[str] = None

class NewsAnalysis(BaseModel):
    ticker: str
    articles: List[NewsArticle]
    sentiment: str
    summary: str
    source: str

# Strategy Models
class ConditionOperator(str, Enum):
    GREATER_THAN = ">"
    LESS_THAN = "<"
    EQUALS = "="
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="

class StrategyCondition(BaseModel):
    field: str
    operator: ConditionOperator
    value: float

class StrategyDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    conditions: List[StrategyCondition]

class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    natural_language_input: Optional[str] = None
    conditions: Optional[List[StrategyCondition]] = None

class StrategyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    conditions: List[Dict[str, Any]]
    created_at: datetime

# Screening Models
class ScreeningResult(BaseModel):
    ticker: str
    company_name: str
    score: float
    matched_conditions: List[str]
    failed_conditions: List[str]
    indicators: Dict[str, Any]

class ScreeningResponse(BaseModel):
    strategy_name: str
    results: List[ScreeningResult]
    total_screened: int
    total_matched: int
    timestamp: datetime

# Agent Analysis Models
class FinancialAnalysis(BaseModel):
    ticker: str
    analysis: str
    metrics: Dict[str, Any]
    missing_fields: List[str]
    timestamp: datetime

class TechnicalAnalysisReport(BaseModel):
    ticker: str
    analysis: str
    indicators: Dict[str, Any]
    trend: str
    timestamp: datetime

class NewsAnalysisReport(BaseModel):
    ticker: str
    analysis: str
    sentiment: str
    articles: List[NewsArticle]
    timestamp: datetime

# Research Report Models
class ResearchReport(BaseModel):
    ticker: str
    company_name: str
    executive_summary: str
    company_overview: str
    technical_analysis: str
    fundamental_analysis: str
    news_analysis: str
    bullish_factors: List[str]
    bearish_factors: List[str]
    risk_factors: List[str]
    evidence_quality: str
    missing_data_warnings: List[str]
    sources: List[str]
    generated_at: datetime
    data_timestamp: datetime

class ResearchReportResponse(BaseModel):
    id: Optional[int] = None
    report: ResearchReport
    saved: bool

# Watchlist Models
class WatchlistItem(BaseModel):
    ticker: str
    company_name: Optional[str] = None

class WatchlistResponse(BaseModel):
    id: int
    ticker: str
    company_name: Optional[str]
    added_at: datetime

# Health Check Models
class ServiceStatus(BaseModel):
    name: str
    available: bool
    details: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    services: List[ServiceStatus]
    timestamp: datetime


# Search Models
class SearchResult(BaseModel):
    symbol: str
    name: str
    exchange: Optional[str] = None
    quote_type: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    timestamp: datetime
