from fastapi import FastAPI, HTTPException, Depends, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
import logging
from dateutil import parser as date_parser

from config import settings
from database import init_db, get_db, is_database_available, Watchlist, Strategy, ResearchReport as DBResearchReport, User
from models import (
    HealthResponse, ServiceStatus, Quote, CompanyInfo, TechnicalIndicators,
    WatchlistItem, WatchlistResponse, StrategyCreate, StrategyResponse, StrategyDefinition,
    ScreeningResponse, ResearchReport, ResearchReportResponse, NewsAnalysis,
    SearchResponse, SearchResult, StrategyCondition
)
from market_data import market_data_service, technical_analysis_service
from news_provider import news_provider
from ai_agents import ai_orchestrator
from screening import screening_engine, DEFAULT_UNIVERSE
from portfolio_risk import analyze_portfolio, PortfolioAnalysisError
from auth import hash_password, verify_password, create_access_token, decode_access_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AlphaForge AI API",
    description="Multi-Agent Quantitative Research & Intelligent Stock Screening Platform",
    version="1.0.0"
)

# Authentication: all application API routes require a valid bearer token.
@app.middleware("http")
async def require_api_session(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"detail": "Please sign in to continue"})
        try:
            payload = decode_access_token(authorization[7:])
            request.state.user_id = int(payload["sub"])
            request.state.user_email = payload.get("email", "")
        except HTTPException as exc:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return await call_next(request)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuthCredentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

@app.post("/auth/register")
async def register(credentials: AuthCredentials, db: Session = Depends(get_db)):
    if not is_database_available() or db is None:
        raise HTTPException(status_code=503, detail="Database unavailable. Configure DATABASE_URL to enable accounts.")
    email = credentials.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists. Sign in instead.")
    user = User(email=email, password_hash=hash_password(credentials.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user.id, user.email), "token_type": "bearer", "user": {"id": user.id, "email": user.email}}

@app.post("/auth/login")
async def login(credentials: AuthCredentials, db: Session = Depends(get_db)):
    if not is_database_available() or db is None:
        raise HTTPException(status_code=503, detail="Database unavailable. Configure DATABASE_URL to enable accounts.")
    email = credentials.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    return {"access_token": create_access_token(user.id, user.email), "token_type": "bearer", "user": {"id": user.id, "email": user.email}}

@app.get("/auth/me")
async def current_user(request: Request, db: Session = Depends(get_db)):
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please sign in")
    payload = decode_access_token(authorization[7:])
    if not is_database_available() or db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="Account no longer exists")
    return {"id": user.id, "email": user.email}

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting AlphaForge AI API")
    init_db()
    logger.info(f"Groq available: {settings.has_groq}")
    logger.info(f"Database available: {is_database_available()}")
    logger.info(f"News provider available: {news_provider.is_available()}")


# Health Check Endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check health status of all services"""
    services = [
        ServiceStatus(
            name="API Server",
            available=True,
            details="Running"
        ),
        ServiceStatus(
            name="Groq AI",
            available=settings.has_groq,
            details=f"Model: {settings.groq_model}" if settings.has_groq else "API key not configured"
        ),
        ServiceStatus(
            name="Database",
            available=is_database_available(),
            details="PostgreSQL connected" if is_database_available() else "Not configured"
        ),
        ServiceStatus(
            name="Market Data",
            available=True,
            details="Yahoo Finance primary; Twelve Data and FMP fallbacks "
                    + ("configured" if settings.has_twelvedata or settings.has_fmp else "not configured")
        ),
        ServiceStatus(
            name="News Provider",
            available=news_provider.is_available(),
            details="NewsData.io or RSS fallback"
        )
    ]
    
    overall_status = "healthy" if all(s.available or s.name in ["Database", "News Provider"] for s in services) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        services=services,
        timestamp=datetime.utcnow()
    )


# Market X-Ray: portfolio risk analysis
@app.post("/api/portfolio/xray")
async def portfolio_xray(payload: dict = Body(...)):
    """Analyze historical co-movement and estimated portfolio risk contributions."""
    holdings = payload.get("holdings", [])
    period = payload.get("period", "1y")
    threshold = payload.get("correlation_threshold", 0.65)
    if period not in {"3mo", "6mo", "1y", "2y", "5y"}:
        raise HTTPException(status_code=422, detail="period must be one of: 3mo, 6mo, 1y, 2y, 5y")
    try:
        parsed_threshold = float(threshold)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="correlation_threshold must be a number")
    try:
        return analyze_portfolio(holdings, period=period, correlation_threshold=parsed_threshold)
    except PortfolioAnalysisError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Market X-Ray analysis failed")
        raise HTTPException(status_code=502, detail="Unable to analyze this portfolio with the available market data.")


# Market Data Endpoints
@app.get("/api/market/search/{query}", response_model=CompanyInfo)
async def search_stock(query: str):
    """Search for a stock ticker"""
    try:
        result = market_data_service.search_ticker(query)
        if not result:
            # Genuine invalid ticker or no match
            raise HTTPException(status_code=404, detail=f"Ticker '{query}' not found or no data available")
        return result
    except HTTPException:
        raise
    except Exception as e:
        # Check if it's a MarketDataError with specific status
        from market_data import MarketDataError
        if isinstance(e, MarketDataError):
            # 429 -> rate limit, 502/504 -> upstream failure
            raise HTTPException(status_code=e.status_code, detail=e.message)
        # Unknown error
        logger.error(f"Unexpected error in search_stock: {type(e).__name__}: {e}")
        raise HTTPException(status_code=502, detail="Market data service temporarily unavailable")


@app.get("/api/market/search", response_model=SearchResponse)
async def search_companies(q: str, limit: int = 5):
    """Search for companies by name, partial name, or ticker. Returns up to 5 real results."""
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    
    # Limit max results to 5
    limit = min(limit, 5)
    
    try:
        results = market_data_service.search_companies(q, limit)
        return SearchResponse(
            results=results,
            query=q,
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        from market_data import MarketDataError
        if isinstance(e, MarketDataError):
            raise HTTPException(status_code=e.status_code, detail=e.message)
        logger.error(f"Unexpected error in search_companies: {type(e).__name__}: {e}")
        raise HTTPException(status_code=502, detail="Market data service temporarily unavailable")


@app.get("/api/market/quote/{ticker}", response_model=Quote)
async def get_quote(ticker: str):
    """Get current quote for a ticker"""
    try:
        result = market_data_service.get_quote(ticker)
        if not result:
            raise HTTPException(status_code=404, detail=f"No quote data available for '{ticker}'")
        return result
    except HTTPException:
        raise
    except Exception as e:
        from market_data import MarketDataError
        if isinstance(e, MarketDataError):
            raise HTTPException(status_code=e.status_code, detail=e.message)
        logger.error(f"Unexpected error in get_quote: {type(e).__name__}: {e}")
        raise HTTPException(status_code=502, detail="Market data service temporarily unavailable")


@app.get("/api/market/company/{ticker}", response_model=CompanyInfo)
async def get_company_info(ticker: str):
    """Get company information"""
    try:
        result = market_data_service.get_company_info(ticker)
        if not result:
            raise HTTPException(status_code=404, detail=f"Company info not available for '{ticker}'")
        return result
    except HTTPException:
        raise
    except Exception as e:
        from market_data import MarketDataError
        if isinstance(e, MarketDataError):
            raise HTTPException(status_code=e.status_code, detail=e.message)
        logger.error(f"Unexpected error in get_company_info: {type(e).__name__}: {e}")
        raise HTTPException(status_code=502, detail="Market data service temporarily unavailable")


@app.get("/api/market/indicators/{ticker}", response_model=TechnicalIndicators)
async def get_technical_indicators(ticker: str):
    """Get technical indicators for a ticker"""
    try:
        historical_data = market_data_service.get_historical_data(ticker, "1y")
        if not historical_data:
            raise HTTPException(status_code=404, detail=f"No historical data available for '{ticker}'")
        
        indicators = technical_analysis_service.calculate_all_indicators(ticker, historical_data)
        if not indicators:
            raise HTTPException(status_code=500, detail=f"Failed to calculate indicators for '{ticker}'")
        
        return indicators
    except HTTPException:
        raise
    except Exception as e:
        from market_data import MarketDataError
        if isinstance(e, MarketDataError):
            raise HTTPException(status_code=e.status_code, detail=e.message)
        logger.error(f"Unexpected error in get_technical_indicators: {type(e).__name__}: {e}")
        raise HTTPException(status_code=502, detail="Market data service temporarily unavailable")


@app.get("/api/market/news/{ticker}", response_model=NewsAnalysis)
async def get_company_news(ticker: str, company_name: Optional[str] = None):
    """Get company news"""
    articles = news_provider.get_company_news(ticker, company_name)
    
    # Simple sentiment analysis based on article count
    sentiment = "Neutral"
    if len(articles) > 5:
        sentiment = "Mixed"
    
    summary = f"Found {len(articles)} recent articles about {ticker}."
    if articles:
        summary += f" Latest: {articles[0].title}"
    
    return NewsAnalysis(
        ticker=ticker,
        articles=articles,
        sentiment=sentiment,
        summary=summary,
        source=articles[0].source if articles else "None"
    )


# Watchlist Endpoints
@app.get("/api/watchlist", response_model=List[WatchlistResponse])
async def get_watchlist(request: Request, db: Session = Depends(get_db)):
    """Get user's watchlist"""
    if not is_database_available():
        raise HTTPException(status_code=503, detail="Database not available")
    
    items = db.query(Watchlist).filter(Watchlist.user_id == request.state.user_id).order_by(Watchlist.added_at.desc()).all()
    return [
        WatchlistResponse(
            id=item.id,
            ticker=item.ticker,
            company_name=item.company_name,
            added_at=item.added_at
        )
        for item in items
    ]


@app.post("/api/watchlist", response_model=WatchlistResponse)
async def add_to_watchlist(item: WatchlistItem, request: Request, db: Session = Depends(get_db)):
    """Add stock to watchlist"""
    if not is_database_available():
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Check if already exists
    existing = db.query(Watchlist).filter(Watchlist.user_id == request.state.user_id, Watchlist.ticker == item.ticker.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Stock already in watchlist")
    
    # Create new watchlist item
    db_item = Watchlist(
        user_id=request.state.user_id,
        ticker=item.ticker.upper(),
        company_name=item.company_name
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return WatchlistResponse(
        id=db_item.id,
        ticker=db_item.ticker,
        company_name=db_item.company_name,
        added_at=db_item.added_at
    )


@app.delete("/api/watchlist/{ticker}")
async def remove_from_watchlist(ticker: str, request: Request, db: Session = Depends(get_db)):
    """Remove stock from watchlist"""
    if not is_database_available():
        raise HTTPException(status_code=503, detail="Database not available")
    
    item = db.query(Watchlist).filter(Watchlist.user_id == request.state.user_id, Watchlist.ticker == ticker.upper()).first()
    if not item:
        raise HTTPException(status_code=404, detail="Stock not in watchlist")
    
    db.delete(item)
    db.commit()
    
    return {"message": "Stock removed from watchlist"}


# Strategy Endpoints
@app.get("/api/strategies", response_model=List[StrategyResponse])
async def get_strategies(request: Request, db: Session = Depends(get_db)):
    """Get all saved strategies"""
    if not is_database_available():
        raise HTTPException(status_code=503, detail="Database not available")
    
    strategies = db.query(Strategy).filter(Strategy.user_id == request.state.user_id).order_by(Strategy.created_at.desc()).all()
    return [
        StrategyResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            conditions=s.conditions,
            created_at=s.created_at
        )
        for s in strategies
    ]


@app.post("/api/strategies", response_model=StrategyResponse)
async def create_strategy(strategy: StrategyCreate, request: Request, db: Session = Depends(get_db)):
    """Create a new screening strategy"""
    if not is_database_available():
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Parse natural language if provided
    if strategy.natural_language_input and not strategy.conditions:
        if not ai_orchestrator.is_available():
            raise HTTPException(
                status_code=503,
                detail="AI services required for natural language parsing but not available"
            )
        
        parsed = ai_orchestrator.parse_strategy_from_natural_language(strategy.natural_language_input)
        if "error" in parsed:
            raise HTTPException(status_code=400, detail=parsed["error"])
        
        strategy.name = parsed.get("name", strategy.name)
        strategy.description = parsed.get("description", strategy.description)
        strategy.conditions = [
            StrategyCondition(**cond) for cond in parsed.get("conditions", [])
        ]
    
    if not strategy.conditions:
        raise HTTPException(status_code=400, detail="Strategy must have at least one condition")
    
    # Create database entry
    db_strategy = Strategy(
        user_id=request.state.user_id,
        name=strategy.name,
        description=strategy.description,
        conditions=[cond.dict() for cond in strategy.conditions]
    )
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    
    return StrategyResponse(
        id=db_strategy.id,
        name=db_strategy.name,
        description=db_strategy.description,
        conditions=db_strategy.conditions,
        created_at=db_strategy.created_at
    )


@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(strategy_id: int, request: Request, db: Session = Depends(get_db)):
    """Delete a strategy"""
    if not is_database_available():
        raise HTTPException(status_code=503, detail="Database not available")
    
    strategy = db.query(Strategy).filter(Strategy.user_id == request.state.user_id, Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    db.delete(strategy)
    db.commit()
    
    return {"message": "Strategy deleted"}


# Screening Endpoint
@app.post("/api/screen", response_model=ScreeningResponse)
async def screen_stocks(strategy: StrategyDefinition):
    """Screen stocks using a strategy"""
    
    if not strategy.conditions:
        raise HTTPException(status_code=400, detail="Strategy must have conditions")
    
    # Screen the default universe
    results = screening_engine.screen_universe(DEFAULT_UNIVERSE, strategy.conditions)
    
    return ScreeningResponse(
        strategy_name=strategy.name,
        results=results,
        total_screened=len(DEFAULT_UNIVERSE),
        total_matched=len(results),
        timestamp=datetime.utcnow()
    )


# Research Report Endpoints
@app.post("/api/research/{ticker}", response_model=ResearchReportResponse)
async def generate_research_report(ticker: str, request: Request, db: Optional[Session] = Depends(get_db)):
    """Generate AI-powered research report"""
    
    # Gather data
    company_info = market_data_service.get_company_info(ticker)
    if not company_info:
        raise HTTPException(status_code=404, detail=f"Company data not available for {ticker}")
    
    historical_data = market_data_service.get_historical_data(ticker, "1y")
    indicators = None
    if historical_data:
        indicators = technical_analysis_service.calculate_all_indicators(ticker, historical_data)
    
    news_articles = news_provider.get_company_news(ticker, company_info.name)
    
    # Generate report using AI orchestrator
    report = ai_orchestrator.generate_research_report(
        ticker,
        company_info,
        indicators,
        news_articles
    )
    
    # Save to database if available
    saved = False
    report_id = None
    
    if is_database_available() and db:
        try:
            # Serialize report to JSON-compatible dict (convert datetime to ISO strings)
            report_dict = report.model_dump(mode='json')
            
            db_report = DBResearchReport(
                user_id=request.state.user_id,
                ticker=ticker.upper(),
                company_name=company_info.name,
                report_data=report_dict,
                data_timestamp=report.data_timestamp
            )
            db.add(db_report)
            db.commit()
            db.refresh(db_report)
            saved = True
            report_id = db_report.id
            logger.info(f"Report saved successfully with ID {report_id}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            db.rollback()
    
    return ResearchReportResponse(
        id=report_id,
        report=report,
        saved=saved
    )


@app.get("/api/research/history", response_model=List[ResearchReportResponse])
async def get_report_history(request: Request, db: Session = Depends(get_db)):
    """Get research report history"""
    if not is_database_available():
        raise HTTPException(status_code=503, detail="Database not available")
    
    reports = db.query(DBResearchReport).filter(DBResearchReport.user_id == request.state.user_id).order_by(DBResearchReport.generated_at.desc()).limit(20).all()
    
    result = []
    for r in reports:
        try:
            # Parse datetime strings from JSON back to datetime objects
            report_data = r.report_data.copy()
            if 'generated_at' in report_data and isinstance(report_data['generated_at'], str):
                report_data['generated_at'] = date_parser.parse(report_data['generated_at'])
            if 'data_timestamp' in report_data and isinstance(report_data['data_timestamp'], str):
                report_data['data_timestamp'] = date_parser.parse(report_data['data_timestamp'])
            
            result.append(ResearchReportResponse(
                id=r.id,
                report=ResearchReport(**report_data),
                saved=True
            ))
        except Exception as e:
            logger.error(f"Failed to deserialize report {r.id}: {str(e)}")
            continue
    
    return result


@app.get("/api/research/{report_id}", response_model=ResearchReportResponse)
async def get_saved_report(report_id: int, request: Request, db: Session = Depends(get_db)):
    """Get a saved research report"""
    if not is_database_available():
        raise HTTPException(status_code=503, detail="Database not available")
    
    report = db.query(DBResearchReport).filter(DBResearchReport.user_id == request.state.user_id, DBResearchReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Parse datetime strings from JSON back to datetime objects
    report_data = report.report_data.copy()
    if 'generated_at' in report_data and isinstance(report_data['generated_at'], str):
        report_data['generated_at'] = date_parser.parse(report_data['generated_at'])
    if 'data_timestamp' in report_data and isinstance(report_data['data_timestamp'], str):
        report_data['data_timestamp'] = date_parser.parse(report_data['data_timestamp'])
    
    return ResearchReportResponse(
        id=report.id,
        report=ResearchReport(**report_data),
        saved=True
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
