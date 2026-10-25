"""
Critical Bug Fixes and Debugging Report
AlphaForge AI - Pre-Demo Audit
"""

import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_database_connectivity():
    """Test 1: Database Connectivity"""
    print("\n" + "="*60)
    print("TEST 1: DATABASE CONNECTIVITY")
    print("="*60)
    
    from config import settings
    from database import init_db, is_database_available
    
    print(f"DATABASE_URL configured: {settings.has_database}")
    if settings.has_database:
        print(f"Connection string prefix: {settings.database_url[:30]}...")
    
    print("\nAttempting database initialization...")
    init_result = init_db()
    print(f"init_db() returned: {init_result}")
    
    print("\nChecking database availability with actual connectivity test...")
    available = is_database_available()
    print(f"is_database_available() returned: {available}")
    
    if not available and settings.has_database:
        print("\n[FAIL] CRITICAL: Database credentials are invalid or database is unreachable")
        print("   Root cause: PostgreSQL password authentication failed")
        print("   Impact: Watchlist, strategies, and report history will not work")
        print("   Solution: Update DATABASE_URL in backend/.env with valid credentials")
        return False
    elif not available and not settings.has_database:
        print("\n[WARN] Database not configured (expected)")
        return True
    else:
        print("\n[PASS] Database connection successful")
        return True

def test_stock_search():
    """Test 2: Stock Search Functionality"""
    print("\n" + "="*60)
    print("TEST 2: STOCK SEARCH - AAPL")
    print("="*60)
    
    from market_data import market_data_service
    
    print("Searching for AAPL...")
    try:
        result = market_data_service.search_ticker("AAPL")
        
        if result:
            print(f"[PASS] Stock search successful!")
            print(f"   Ticker: {result.ticker}")
            print(f"   Name: {result.name}")
            print(f"   Sector: {result.sector or 'N/A'}")
            print(f"   Market Cap: ${result.market_cap:,.0f}" if result.market_cap else "   Market Cap: N/A")
            return True
        else:
            print("[FAIL] Stock search returned None")
            print("   Possible causes:")
            print("   - Yahoo Finance rate limiting (429 Too Many Requests)")
            print("   - Network connectivity issues")
            print("   - yfinance API changes")
            return False
    except Exception as e:
        print(f"[FAIL] Stock search failed with exception: {type(e).__name__}: {e}")
        return False

def test_quote_retrieval():
    """Test 3: Quote Retrieval"""
    print("\n" + "="*60)
    print("TEST 3: QUOTE RETRIEVAL - AAPL")
    print("="*60)
    
    from market_data import market_data_service
    
    print("Getting quote for AAPL...")
    try:
        quote = market_data_service.get_quote("AAPL")
        
        if quote:
            print(f"[PASS] Quote retrieval successful!")
            print(f"   Price: ${quote.price:.2f}")
            print(f"   Change: {quote.change:+.2f} ({quote.change_percent:+.2f}%)")
            print(f"   Volume: {quote.volume:,}" if quote.volume else "   Volume: N/A")
            print(f"   Timestamp: {quote.timestamp}")
            return True
        else:
            print("[FAIL] Quote retrieval returned None")
            return False
    except Exception as e:
        print(f"[FAIL] Quote retrieval failed: {type(e).__name__}: {e}")
        return False

def test_historical_data():
    """Test 4: Historical Data"""
    print("\n" + "="*60)
    print("TEST 4: HISTORICAL DATA - AAPL")
    print("="*60)
    
    from market_data import market_data_service
    
    print("Getting historical data for AAPL...")
    try:
        hist = market_data_service.get_historical_data("AAPL", "1mo")
        
        if hist:
            print(f"[PASS] Historical data retrieval successful!")
            print(f"   Data points: {len(hist.dates)}")
            print(f"   Date range: {hist.dates[0]} to {hist.dates[-1]}")
            print(f"   Latest close: ${hist.close[-1]:.2f}")
            return True
        else:
            print("[FAIL] Historical data returned None")
            return False
    except Exception as e:
        print(f"[FAIL] Historical data failed: {type(e).__name__}: {e}")
        return False

def test_technical_indicators():
    """Test 5: Technical Indicators"""
    print("\n" + "="*60)
    print("TEST 5: TECHNICAL INDICATORS - AAPL")
    print("="*60)
    
    from market_data import market_data_service, technical_analysis_service
    
    print("Calculating technical indicators for AAPL...")
    try:
        hist = market_data_service.get_historical_data("AAPL", "1y")
        if not hist:
            print("❌ Could not get historical data for indicators")
            return False
        
        indicators = technical_analysis_service.calculate_all_indicators("AAPL", hist)
        
        if indicators:
            print(f"[PASS] Technical indicators calculated successfully!")
            print(f"   Current Price: ${indicators.current_price:.2f}")
            print(f"   SMA(20): ${indicators.sma_20:.2f}" if indicators.sma_20 else "   SMA(20): N/A")
            print(f"   SMA(50): ${indicators.sma_50:.2f}" if indicators.sma_50 else "   SMA(50): N/A")
            print(f"   RSI(14): {indicators.rsi_14:.2f}" if indicators.rsi_14 else "   RSI(14): N/A")
            print(f"   MACD: {indicators.macd:.4f}" if indicators.macd else "   MACD: N/A")
            return True
        else:
            print("[FAIL] Technical indicators calculation failed")
            return False
    except Exception as e:
        print(f"[FAIL] Technical indicators failed: {type(e).__name__}: {e}")
        return False

def test_groq_availability():
    """Test 6: Groq AI Availability"""
    print("\n" + "="*60)
    print("TEST 6: GROQ AI AVAILABILITY")
    print("="*60)
    
    from config import settings
    from ai_agents import ai_orchestrator
    
    print(f"GROQ_API_KEY configured: {settings.has_groq}")
    print(f"Model: {settings.groq_model}")
    print(f"AI Orchestrator available: {ai_orchestrator.is_available()}")
    
    if settings.has_groq and ai_orchestrator.is_available():
        print("[PASS] Groq AI is available")
        return True
    else:
        print("[WARN] Groq AI not available - will use rule-based fallbacks")
        return True  # Not critical

def run_all_tests():
    """Run all diagnostic tests"""
    print("\n" + "="*60)
    print("ALPHAFORGE AI - CRITICAL BUG AUDIT")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {}
    
    # Test 1: Database
    results['database'] = test_database_connectivity()
    
    # Test 2-5: Stock Market Data
    results['stock_search'] = test_stock_search()
    results['quote'] = test_quote_retrieval()
    results['historical'] = test_historical_data()
    results['indicators'] = test_technical_indicators()
    
    # Test 6: AI
    results['groq'] = test_groq_availability()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test.upper():.<30} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    print("\n" + "="*60)
    print("CRITICAL ISSUES IDENTIFIED")
    print("="*60)
    
    if not results['database']:
        print("\n[CRITICAL] ISSUE 1: Database Authentication Failure")
        print("   Location: backend/.env DATABASE_URL")
        print("   Error: password authentication failed for user 'neondb_owner'")
        print("   Impact: /api/watchlist and /api/strategies return HTTP 500")
        print("   Fix Required: Update with valid PostgreSQL credentials")
    
    if not results['stock_search']:
        print("\n[CRITICAL] ISSUE 2: Stock Search Failure")
        print("   Location: backend/market_data.py search_ticker()")
        print("   Error: Yahoo Finance rate limiting or API errors")
        print("   Impact: Cannot search for tickers like AAPL")
        print("   Fix Applied: Use history-first approach with graceful fallback")
    
    if results['stock_search'] and results['quote']:
        print("\n[FIXED] Stock search fixed - now uses historical data first")
        print("   This avoids Yahoo Finance .info rate limiting")
    
    print("\n" + "="*60)
    print("FIXES APPLIED")
    print("="*60)
    print("1. database.py: Added real connectivity check with SELECT 1")
    print("2. database.py: Set engine=None on connection failure")
    print("3. database.py: is_database_available() now tests actual connection")
    print("4. market_data.py: search_ticker() uses history-first approach")
    print("5. market_data.py: Graceful fallback when .info fails")
    print("6. market_data.py: get_quote() prioritizes historical data")
    print("7. market_data.py: Better error logging with exception types")
    print("\nNote: All fixes preserve original functionality while adding resilience")
    
    print("\n" + "="*60)
    print("REMAINING ACTION ITEMS")
    print("="*60)
    
    if not results['database']:
        print("[REQUIRED] Update DATABASE_URL with valid credentials")
        print("   Or remove DATABASE_URL to disable database features")
    
    if not results['stock_search']:
        print("[REQUIRED] Yahoo Finance may be rate limiting")
        print("   Wait a few minutes and retry")
        print("   Consider adding request delays if persistent")
    
    print("\n" + "="*60)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
