from typing import List, Dict, Any, Optional
from models import StrategyCondition, ScreeningResult, TechnicalIndicators, CompanyInfo, ConditionOperator
from market_data import market_data_service, technical_analysis_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ScreeningEngine:
    """Stock screening and ranking engine"""
    
    ALLOWED_FIELDS = {
        'price', 'sma_20', 'sma_50', 'sma_200', 'rsi_14', 'macd',
        'volume', 'market_cap', 'pe_ratio', 'beta', 'dividend_yield',
        'ema_12', 'ema_26', 'macd_signal', 'macd_histogram',
        'price_vs_sma_50', 'price_vs_sma_200', 'sma_20_vs_sma_50',
        'ema_12_vs_ema_26', 'roc_20', 'volatility_20'
    }
    
    def validate_condition(self, condition: StrategyCondition) -> bool:
        """Validate a screening condition"""
        if condition.field not in self.ALLOWED_FIELDS:
            return False
        if condition.operator not in [op.value for op in ConditionOperator]:
            return False
        return True
    
    def evaluate_condition(
        self,
        condition: StrategyCondition,
        indicators: Optional[TechnicalIndicators],
        company_info: Optional[CompanyInfo]
    ) -> tuple[bool, Optional[Any]]:
        """Evaluate a single condition against stock data"""
        
        # Get field value
        field_value = None
        
        if condition.field == 'price' and indicators:
            field_value = indicators.current_price
        elif condition.field == 'sma_20' and indicators:
            field_value = indicators.sma_20
        elif condition.field == 'sma_50' and indicators:
            field_value = indicators.sma_50
        elif condition.field == 'sma_200' and indicators:
            field_value = indicators.sma_200
        elif condition.field == 'rsi_14' and indicators:
            field_value = indicators.rsi_14
        elif condition.field == 'macd' and indicators:
            field_value = indicators.macd
        elif condition.field == 'volume' and indicators:
            field_value = indicators.current_volume
        elif condition.field == 'ema_12' and indicators:
            field_value = indicators.ema_12
        elif condition.field == 'ema_26' and indicators:
            field_value = indicators.ema_26
        elif condition.field == 'macd_signal' and indicators:
            field_value = indicators.macd_signal
        elif condition.field == 'macd_histogram' and indicators:
            field_value = indicators.macd_histogram
        elif condition.field == 'price_vs_sma_50' and indicators:
            field_value = indicators.price_vs_sma_50
        elif condition.field == 'price_vs_sma_200' and indicators:
            field_value = indicators.price_vs_sma_200
        elif condition.field == 'sma_20_vs_sma_50' and indicators:
            field_value = indicators.sma_20_vs_sma_50
        elif condition.field == 'ema_12_vs_ema_26' and indicators:
            field_value = indicators.ema_12_vs_ema_26
        elif condition.field == 'roc_20' and indicators:
            field_value = indicators.roc_20
        elif condition.field == 'volatility_20' and indicators:
            field_value = indicators.volatility_20
        elif condition.field == 'market_cap' and company_info:
            field_value = company_info.market_cap
        elif condition.field == 'pe_ratio' and company_info:
            field_value = company_info.pe_ratio
        elif condition.field == 'beta' and company_info:
            field_value = company_info.beta
        elif condition.field == 'dividend_yield' and company_info:
            field_value = company_info.dividend_yield
        
        if field_value is None:
            return False, None
        
        # Evaluate condition
        try:
            if condition.operator == ">":
                result = field_value > condition.value
            elif condition.operator == "<":
                result = field_value < condition.value
            elif condition.operator == ">=":
                result = field_value >= condition.value
            elif condition.operator == "<=":
                result = field_value <= condition.value
            elif condition.operator == "=":
                result = abs(field_value - condition.value) < 0.01
            else:
                result = False
            
            return result, field_value
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False, field_value
    
    def screen_stock(
        self,
        ticker: str,
        conditions: List[StrategyCondition]
    ) -> Optional[ScreeningResult]:
        """Screen a single stock against strategy conditions"""
        
        try:
            # Get market data
            company_info = market_data_service.get_company_info(ticker)
            if not company_info:
                return None
            
            historical_data = market_data_service.get_historical_data(ticker, "1y")
            if not historical_data:
                return None
            
            indicators = technical_analysis_service.calculate_all_indicators(ticker, historical_data)
            if not indicators:
                return None
            
            # Evaluate all conditions
            matched_conditions = []
            failed_conditions = []
            match_count = 0
            
            for condition in conditions:
                if not self.validate_condition(condition):
                    continue
                
                passed, field_value = self.evaluate_condition(condition, indicators, company_info)
                
                condition_str = f"{condition.field} {condition.operator} {condition.value}"
                if field_value is not None:
                    condition_str += f" (actual: {field_value:.2f})"
                
                if passed:
                    matched_conditions.append(condition_str)
                    match_count += 1
                else:
                    failed_conditions.append(condition_str)
            
            # Only return if stock matches all conditions
            if len(failed_conditions) > 0:
                return None
            
            # Calculate score (percentage of conditions matched)
            score = (match_count / len(conditions) * 100) if conditions else 0
            
            # Collect indicator values
            indicator_dict = {
                'price': indicators.current_price,
                'sma_20': indicators.sma_20,
                'sma_50': indicators.sma_50,
                'rsi_14': indicators.rsi_14,
                'macd': indicators.macd,
                'macd_signal': indicators.macd_signal,
                'macd_histogram': indicators.macd_histogram,
                'price_vs_sma_50': indicators.price_vs_sma_50,
                'price_vs_sma_200': indicators.price_vs_sma_200,
                'sma_20_vs_sma_50': indicators.sma_20_vs_sma_50,
                'ema_12_vs_ema_26': indicators.ema_12_vs_ema_26,
                'roc_20': indicators.roc_20,
                'volatility_20': indicators.volatility_20,
                'volume': indicators.current_volume,
                'ema_12': indicators.ema_12,
                'ema_26': indicators.ema_26,
                'market_cap': company_info.market_cap,
                'pe_ratio': company_info.pe_ratio
            }
            
            return ScreeningResult(
                ticker=ticker,
                company_name=company_info.name,
                score=score,
                matched_conditions=matched_conditions,
                failed_conditions=failed_conditions,
                indicators={k: v for k, v in indicator_dict.items() if v is not None}
            )
            
        except Exception as e:
            logger.error(f"Error screening {ticker}: {e}")
            return None
    
    def screen_universe(
        self,
        tickers: List[str],
        conditions: List[StrategyCondition],
        max_results: int = 50
    ) -> List[ScreeningResult]:
        """Screen a universe of stocks"""
        
        results = []
        
        for ticker in tickers[:max_results]:  # Limit for performance
            result = self.screen_stock(ticker, conditions)
            if result:
                results.append(result)
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results


# Default stock universe for screening (popular stocks)
DEFAULT_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "WMT",
    "JNJ", "PG", "MA", "HD", "DIS", "BAC", "XOM", "KO", "PFE", "CSCO",
    "NFLX", "INTC", "AMD", "PYPL", "ORCL", "CRM", "ADBE", "NKE", "T", "VZ"
]


screening_engine = ScreeningEngine()
