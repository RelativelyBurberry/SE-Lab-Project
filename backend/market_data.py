import requests
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from models import Quote, HistoricalData, CompanyInfo, TechnicalIndicators, SearchResult
from config import settings
import logging
import time
from functools import lru_cache

logger = logging.getLogger(__name__)

# Custom exception for market data errors with HTTP status
class MarketDataError(Exception):
    """Market data error with HTTP status code"""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class MarketDataService:
    """Service for retrieving market data from Yahoo Finance via direct HTTP"""
    
    def __init__(self):
        self.source = "yahoo_finance_direct"
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 300  # 5 minutes
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key, 0)
            if time.time() - timestamp < self._cache_ttl:
                return self._cache[key]
        return None
    
    def _set_cached(self, key: str, value: Any):
        """Store value in cache with timestamp"""
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()
    
    def _make_request(self, url: str, params: Dict = None, timeout: int = 15) -> requests.Response:
        """Make HTTP request with proper error handling"""
        try:
            response = self._session.get(url, params=params, timeout=timeout)
            return response
        except requests.exceptions.Timeout:
            raise MarketDataError(
                "Data provider request timed out. Please try again later.",
                status_code=504
            )
        except requests.exceptions.ConnectionError:
            raise MarketDataError(
                "Unable to connect to data provider. Please check your network connection.",
                status_code=502
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {type(e).__name__}: {e}")
            raise MarketDataError(
                "Data provider request failed. Please try again later.",
                status_code=502
            )
    
    def _fetch_chart_data(self, ticker: str, range_: str = "1y", interval: str = "1d") -> Optional[Dict]:
        """Fetch chart data from Yahoo Finance v8 API"""
        cache_key = f"chart_{ticker}_{range_}_{interval}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker.upper()}"
        params = {
            'range': range_,
            'interval': interval,
            'includePrePost': 'false',
            'events': 'div,splits,capitalGains'
        }
        
        response = self._make_request(url, params)
        
        # Handle rate limiting
        if response.status_code == 429:
            raise MarketDataError(
                "Data provider rate limit reached. Please wait a few minutes before retrying.",
                status_code=429
            )
        
        # Handle other errors
        if response.status_code != 200:
            logger.error(f"Yahoo Finance returned status {response.status_code} for {ticker}")
            raise MarketDataError(
                f"Data provider returned error (HTTP {response.status_code}).",
                status_code=502
            )
        
        try:
            data = response.json()
        except ValueError as e:
            logger.error(f"Invalid JSON response for {ticker}: {e}")
            raise MarketDataError(
                "Data provider returned invalid response. Please try again later.",
                status_code=502
            )
        
        # Check if we got actual data
        result = data.get('chart', {}).get('result')
        if not result or len(result) == 0:
            # No data could mean invalid ticker or delisted
            return None
        
        self._set_cached(cache_key, data)
        return data
    
    def _parse_chart_to_dataframe(self, chart_data: Dict) -> Optional[pd.DataFrame]:
        """Parse Yahoo Finance chart data to pandas DataFrame"""
        if not chart_data:
            return None
        
        result = chart_data.get('chart', {}).get('result', [])
        if not result:
            return None
        
        result = result[0]
        timestamps = result.get('timestamp', [])
        indicators = result.get('indicators', {}).get('quote', [])
        
        if not timestamps or not indicators:
            return None
        
        quote = indicators[0]
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'Open': quote.get('open', []),
            'High': quote.get('high', []),
            'Low': quote.get('low', []),
            'Close': quote.get('close', []),
            'Volume': quote.get('volume', [])
        })
        
        # Convert timestamps to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)
        
        # Remove rows with all NaN
        df.dropna(how='all', inplace=True)
        
        return df
    
    def search_companies(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Search for companies by name, partial name, or ticker using Yahoo Finance search API"""
        if not query or not query.strip():
            return []
        
        query = query.strip()
        cache_key = f"company_search_{query}_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        url = "https://query1.finance.yahoo.com/v1/finance/search"
        params = {
            'q': query,
            'quotesCount': limit,
            'newsCount': 0
        }
        
        try:
            response = self._make_request(url, params)
            
            if response.status_code == 429:
                raise MarketDataError(
                    "Data provider rate limit reached. Please wait a few minutes before retrying.",
                    status_code=429
                )
            
            if response.status_code != 200:
                logger.error(f"Yahoo Finance search returned status {response.status_code} for query '{query}'")
                raise MarketDataError(
                    f"Data provider returned error (HTTP {response.status_code}).",
                    status_code=502
                )
            
            data = response.json()
            quotes = data.get('quotes', [])
            
            results = []
            for quote in quotes:
                quote_type = quote.get('quoteType', '')
                # Only include equity, ETF, and index quotes
                if quote_type in ['EQUITY', 'ETF', 'INDEX', 'MUTUALFUND']:
                    symbol = quote.get('symbol', '')
                    short_name = quote.get('shortname', '') or quote.get('longname', '')
                    exchange = quote.get('exchange', '')
                    
                    # Skip if no symbol or name
                    if not symbol:
                        continue
                    
                    result = SearchResult(
                        symbol=symbol,
                        name=short_name or symbol,
                        exchange=exchange if exchange else None,
                        quote_type=quote_type
                    )
                    results.append(result)
                    
                    if len(results) >= limit:
                        break
            
            self._set_cached(cache_key, results)
            return results
            
        except MarketDataError:
            raise
        except ValueError as e:
            logger.error(f"Invalid JSON response for search query '{query}': {e}")
            raise MarketDataError(
                "Data provider returned invalid response. Please try again later.",
                status_code=502
            )
        except Exception as e:
            logger.error(f"Error searching companies for '{query}': {type(e).__name__}: {e}")
            raise MarketDataError(
                "Failed to search companies. Please try again later.",
                status_code=502
            )
    
    def search_ticker(self, query: str) -> Optional[CompanyInfo]:
        """Search for a ticker using Yahoo Finance search API"""
        if not query or not query.strip():
            return None
        
        query = query.strip().upper()
        cache_key = f"search_{query}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        # First try to get chart data to validate ticker exists
        chart_data = self._fetch_chart_data(query, range_="5d")
        
        if chart_data:
            # Ticker is valid, extract metadata
            result = chart_data.get('chart', {}).get('result', [])
            if result:
                meta = result[0].get('meta', {})
                company_info = CompanyInfo(
                    ticker=meta.get('symbol', query),
                    name=meta.get('shortName', meta.get('longName', query)),
                    sector=None,
                    industry=None,
                    description=None,
                    market_cap=None,
                    pe_ratio=None,
                    dividend_yield=None,
                    beta=None,
                    source=self.source
                )
                self._set_cached(cache_key, company_info)
                return company_info
        
        # Try search API as fallback
        url = "https://query1.finance.yahoo.com/v1/finance/search"
        params = {
            'q': query,
            'quotesCount': 5,
            'newsCount': 0
        }
        
        try:
            response = self._make_request(url, params)
            
            if response.status_code == 429:
                raise MarketDataError(
                    "Data provider rate limit reached. Please wait a few minutes before retrying.",
                    status_code=429
                )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            quotes = data.get('quotes', [])
            
            for quote in quotes:
                if quote.get('quoteType') in ['EQUITY', 'ETF', 'INDEX']:
                    # Try to get actual data to confirm it's valid
                    symbol = quote.get('symbol', '').upper()
                    if symbol:
                        # Recursively call with the found symbol
                        return self.search_ticker(symbol)
            
            return None
            
        except MarketDataError:
            raise
        except Exception as e:
            logger.error(f"Error searching ticker {query}: {type(e).__name__}: {e}")
            return None
    
    def get_quote(self, ticker: str) -> Optional[Quote]:
        """Build a quote from the latest available daily bar, using provider fallbacks."""
        if not ticker or not ticker.strip():
            return None
        ticker = ticker.strip().upper()
        cache_key = f"quote_{ticker}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        history = self.get_historical_data(ticker, "5d")
        if history is None or not history.close:
            return None
        current_price = float(history.close[-1])
        previous_close = float(history.close[-2]) if len(history.close) > 1 else current_price
        change = current_price - previous_close
        change_percent = (change / previous_close * 100.0) if previous_close else 0.0
        volume = history.volume[-1] if history.volume else None
        quote = Quote(
            ticker=ticker,
            price=current_price,
            change=change,
            change_percent=change_percent,
            volume=volume,
            market_cap=None,
            pe_ratio=None,
            timestamp=datetime.utcnow(),
            source=history.source,
        )
        self._set_cached(cache_key, quote)
        return quote

    def _fetch_twelvedata_history(self, ticker: str, period: str) -> Optional[pd.DataFrame]:
        """Fetch daily OHLCV from Twelve Data when its API key is configured."""
        api_key = settings.twelvedata_api_key
        if not api_key:
            return None
        outputsize = {"1d": 1, "5d": 5, "1mo": 23, "3mo": 66, "6mo": 132,
                      "1y": 260, "2y": 520, "5y": 1300, "10y": 2600, "max": 5000}.get(period, 260)
        try:
            response = self._session.get(
                "https://api.twelvedata.com/time_series",
                params={"symbol": ticker, "interval": "1day", "outputsize": outputsize,
                        "order": "ASC", "apikey": api_key},
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") == "error" or not payload.get("values"):
                logger.warning("Twelve Data returned no history for %s: %s", ticker, payload.get("message", "no values"))
                return None
            df = pd.DataFrame(payload["values"]).rename(columns={
                "datetime": "timestamp", "open": "Open", "high": "High",
                "low": "Low", "close": "Close", "volume": "Volume",
            })
            if "timestamp" not in df.columns or "Close" not in df.columns:
                return None
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            for column in ("Open", "High", "Low", "Close", "Volume"):
                if column not in df:
                    df[column] = np.nan
                df[column] = pd.to_numeric(df[column], errors="coerce")
            df = df.dropna(subset=["timestamp", "Open", "High", "Low", "Close"]).set_index("timestamp").sort_index()
            return df if not df.empty else None
        except Exception as exc:
            logger.warning("Twelve Data history failed for %s: %s", ticker, type(exc).__name__)
            return None

    def _fetch_fmp_history(self, ticker: str, period: str) -> Optional[pd.DataFrame]:
        """Fetch daily OHLCV from Financial Modeling Prep when its key is configured."""
        api_key = settings.fmp_api_key
        if not api_key:
            return None
        days = {"1d": 3, "5d": 10, "1mo": 40, "3mo": 100, "6mo": 200,
                "1y": 400, "2y": 800, "5y": 1900, "10y": 3700, "max": 10000}.get(period, 400)
        from datetime import date
        start_date = (date.today() - timedelta(days=days)).isoformat()
        end_date = date.today().isoformat()
        endpoints = [
            ("https://financialmodelingprep.com/stable/historical-price-eod/full",
             {"symbol": ticker, "from": start_date, "to": end_date, "apikey": api_key}),
            ("https://financialmodelingprep.com/api/v3/historical-price-full/" + ticker,
             {"from": start_date, "to": end_date, "apikey": api_key}),
        ]
        for url, params in endpoints:
            try:
                response = self._session.get(url, params=params, timeout=15)
                if response.status_code in (401, 403, 404):
                    continue
                response.raise_for_status()
                payload = response.json()
                rows = payload.get("historical", []) if isinstance(payload, dict) else payload
                if not isinstance(rows, list) or not rows:
                    continue
                df = pd.DataFrame(rows).rename(columns={
                    "date": "timestamp", "open": "Open", "high": "High",
                    "low": "Low", "close": "Close", "volume": "Volume",
                })
                if "timestamp" not in df.columns or "Close" not in df.columns:
                    continue
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
                for column in ("Open", "High", "Low", "Close", "Volume"):
                    if column not in df:
                        df[column] = np.nan
                    df[column] = pd.to_numeric(df[column], errors="coerce")
                df = df.dropna(subset=["timestamp", "Open", "High", "Low", "Close"]).set_index("timestamp").sort_index()
                if not df.empty:
                    return df
            except Exception as exc:
                logger.warning("FMP history failed for %s: %s", ticker, type(exc).__name__)
        return None

    def _historical_dataframe(self, ticker: str, period: str) -> tuple[Optional[pd.DataFrame], str]:
        """Try Yahoo first, then configured Twelve Data and FMP providers."""
        try:
            chart_data = self._fetch_chart_data(ticker, range_=period)
            df = self._parse_chart_to_dataframe(chart_data) if chart_data else None
            if df is not None and not df.empty:
                return df, "yahoo_finance"
        except MarketDataError as exc:
            logger.info("Yahoo Finance unavailable for %s (%s); trying fallbacks", ticker, exc.status_code)
        except Exception as exc:
            logger.warning("Yahoo Finance history failed for %s: %s", ticker, type(exc).__name__)

        for provider_name, fetcher in (
            ("twelvedata", self._fetch_twelvedata_history),
            ("financial_modeling_prep", self._fetch_fmp_history),
        ):
            df = fetcher(ticker, period)
            if df is not None and not df.empty:
                return df, provider_name
        return None, "unavailable"

    def get_historical_data(self, ticker: str, period: str = "1y") -> Optional[HistoricalData]:
        """Get historical OHLCV using Yahoo Finance, then Twelve Data, then FMP."""
        if not ticker or not ticker.strip():
            return None
        ticker = ticker.strip().upper()
        cache_key = f"history_fallback_{ticker}_{period}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        df, provider = self._historical_dataframe(ticker, period)
        if df is None or df.empty:
            return None
        # Keep JSON-compatible values; missing volume is represented as zero.
        result = HistoricalData(
            ticker=ticker,
            dates=[date.strftime("%Y-%m-%d") for date in df.index],
            open=[float(value) for value in df["Open"]],
            high=[float(value) for value in df["High"]],
            low=[float(value) for value in df["Low"]],
            close=[float(value) for value in df["Close"]],
            volume=[0 if pd.isna(value) else int(value) for value in df["Volume"]],
            source=provider,
        )
        self._set_cached(cache_key, result)
        return result

    def get_company_info(self, ticker: str) -> Optional[CompanyInfo]:
        """Get detailed company information"""
        return self.search_ticker(ticker)
    
    def validate_ticker(self, ticker: str) -> bool:
        """Validate if a ticker exists"""
        if not ticker or not ticker.strip():
            return False
        
        try:
            chart_data = self._fetch_chart_data(ticker.strip().upper(), range_="1d")
            return chart_data is not None
        except MarketDataError as e:
            if e.status_code in [429, 502, 504]:
                # Provider issues - don't claim ticker is invalid
                logger.warning(f"Cannot validate ticker {ticker}: {e.message}")
                return False
            return False
        except Exception:
            return False


class TechnicalAnalysisService:
    """Service for calculating technical indicators"""
    
    def calculate_sma(self, prices: pd.Series, period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return None
        return float(prices.tail(period).mean())
    
    def calculate_ema(self, prices: pd.Series, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        return float(prices.ewm(span=period, adjust=False).mean().iloc[-1])
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return None
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Calculate MACD, Signal, and Histogram"""
        if len(prices) < slow:
            return None, None, None
        
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return float(macd.iloc[-1]), float(signal_line.iloc[-1]), float(histogram.iloc[-1])
    
    def calculate_all_indicators(self, ticker: str, historical_data: HistoricalData) -> Optional[TechnicalIndicators]:
        """Calculate all technical indicators"""
        try:
            closes = pd.Series(historical_data.close)
            current_price = closes.iloc[-1]
            
            macd, macd_signal, macd_hist = self.calculate_macd(closes)
            sma20 = self.calculate_sma(closes, 20)
            sma50 = self.calculate_sma(closes, 50)
            sma200 = self.calculate_sma(closes, 200)
            ema12 = self.calculate_ema(closes, 12)
            ema26 = self.calculate_ema(closes, 26)
            returns = closes.pct_change().dropna()
            roc20 = ((float(closes.iloc[-1]) / float(closes.iloc[-21]) - 1) * 100) if len(closes) >= 21 and float(closes.iloc[-21]) else None
            vol20 = float(returns.tail(20).std() * (252 ** 0.5) * 100) if len(returns) >= 20 else None
            
            return TechnicalIndicators(
                ticker=ticker.upper(),
                sma_20=sma20,
                sma_50=sma50,
                sma_200=sma200,
                ema_12=ema12,
                ema_26=ema26,
                rsi_14=self.calculate_rsi(closes, 14),
                macd=macd,
                macd_signal=macd_signal,
                macd_histogram=macd_hist,
                price_vs_sma_50=(float(current_price) / sma50 - 1) * 100 if sma50 else None,
                price_vs_sma_200=(float(current_price) / sma200 - 1) * 100 if sma200 else None,
                sma_20_vs_sma_50=(sma20 / sma50 - 1) * 100 if sma20 and sma50 else None,
                ema_12_vs_ema_26=(ema12 / ema26 - 1) * 100 if ema12 and ema26 else None,
                roc_20=roc20,
                volatility_20=vol20,
                current_volume=int(historical_data.volume[-1]) if historical_data.volume else None,
                current_price=float(current_price),
                calculated_at=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error calculating indicators for {ticker}: {e}")
            return None


# Service instances
market_data_service = MarketDataService()
technical_analysis_service = TechnicalAnalysisService()
