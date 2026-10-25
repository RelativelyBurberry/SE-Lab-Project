from groq import Groq
from typing import Dict, Any, List, Optional
from datetime import datetime
from models import (
    FinancialAnalysis, TechnicalAnalysisReport, NewsAnalysisReport,
    ResearchReport, CompanyInfo, TechnicalIndicators, NewsArticle
)
from config import settings
import json
import logging

logger = logging.getLogger(__name__)

class AIOrchestrator:
    """Multi-agent AI orchestration system using Groq"""
    
    def __init__(self):
        self.client = None
        if settings.has_groq:
            try:
                # Groq client doesn't accept proxies argument
                self.client = Groq(api_key=settings.groq_api_key)
                logger.info("Groq client initialized successfully")
            except TypeError as e:
                logger.error(f"Groq client initialization error (argument mismatch): {e}")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
    
    def is_available(self) -> bool:
        """Check if AI services are available"""
        return self.client is not None
    
    def financial_analysis_agent(
        self,
        ticker: str,
        company_info: Optional[CompanyInfo]
    ) -> FinancialAnalysis:
        """Financial Analysis Agent - analyzes company fundamentals"""
        
        metrics = {}
        missing_fields = []
        
        if company_info:
            # Market cap - check for None explicitly
            if company_info.market_cap is not None and company_info.market_cap > 0:
                metrics['market_cap'] = company_info.market_cap
            else:
                missing_fields.append('market_cap')
            
            # P/E ratio - check for None explicitly
            if company_info.pe_ratio is not None and company_info.pe_ratio > 0:
                metrics['pe_ratio'] = company_info.pe_ratio
            else:
                missing_fields.append('pe_ratio')
            
            # Dividend yield - check for None explicitly (can be 0.0 legitimately)
            if company_info.dividend_yield is not None:
                metrics['dividend_yield'] = company_info.dividend_yield
            else:
                missing_fields.append('dividend_yield')
            
            # Beta - check for None explicitly
            if company_info.beta is not None and company_info.beta > 0:
                metrics['beta'] = company_info.beta
            else:
                missing_fields.append('beta')
            
            # Sector and industry - distinguish between None and actual value
            if company_info.sector:
                metrics['sector'] = company_info.sector
            else:
                metrics['sector'] = 'Unavailable'
                missing_fields.append('sector')
            
            if company_info.industry:
                metrics['industry'] = company_info.industry
            else:
                metrics['industry'] = 'Unavailable'
                missing_fields.append('industry')
        else:
            missing_fields = ['all_fundamental_data']
        
        # Generate analysis
        if self.is_available() and company_info:
            analysis_text = self._generate_financial_analysis(ticker, company_info, metrics, missing_fields)
        else:
            analysis_text = self._fallback_financial_analysis(ticker, metrics, missing_fields)
        
        return FinancialAnalysis(
            ticker=ticker,
            analysis=analysis_text,
            metrics=metrics,
            missing_fields=missing_fields,
            timestamp=datetime.utcnow()
        )
    
    def technical_analysis_agent(
        self,
        ticker: str,
        indicators: Optional[TechnicalIndicators]
    ) -> TechnicalAnalysisReport:
        """Technical Analysis Agent - analyzes price trends and indicators"""
        
        if not indicators:
            return TechnicalAnalysisReport(
                ticker=ticker,
                analysis="Technical analysis unavailable - insufficient historical data.",
                indicators={},
                trend="Unknown",
                timestamp=datetime.utcnow()
            )
        
        indicator_dict = {
            'current_price': indicators.current_price,
            'sma_20': indicators.sma_20,
            'sma_50': indicators.sma_50,
            'sma_200': indicators.sma_200,
            'rsi_14': indicators.rsi_14,
            'macd': indicators.macd,
            'macd_signal': indicators.macd_signal
        }
        
        # Determine trend
        trend = self._determine_trend(indicators)
        
        # Generate analysis
        if self.is_available():
            analysis_text = self._generate_technical_analysis(ticker, indicators, trend)
        else:
            analysis_text = self._fallback_technical_analysis(ticker, indicators, trend)
        
        return TechnicalAnalysisReport(
            ticker=ticker,
            analysis=analysis_text,
            indicators=indicator_dict,
            trend=trend,
            timestamp=datetime.utcnow()
        )
    
    def news_analysis_agent(
        self,
        ticker: str,
        articles: List[NewsArticle]
    ) -> NewsAnalysisReport:
        """News Analysis Agent - analyzes company news and sentiment"""
        
        if not articles:
            return NewsAnalysisReport(
                ticker=ticker,
                analysis="No recent news articles found for this company.",
                sentiment="Neutral",
                articles=[],
                timestamp=datetime.utcnow()
            )
        
        # Generate analysis
        if self.is_available():
            analysis_text, sentiment = self._generate_news_analysis(ticker, articles)
        else:
            analysis_text, sentiment = self._fallback_news_analysis(ticker, articles)
        
        return NewsAnalysisReport(
            ticker=ticker,
            analysis=analysis_text,
            sentiment=sentiment,
            articles=articles[:5],  # Include top 5 articles
            timestamp=datetime.utcnow()
        )
    
    def generate_research_report(
        self,
        ticker: str,
        company_info: Optional[CompanyInfo],
        technical_indicators: Optional[TechnicalIndicators],
        news_articles: List[NewsArticle]
    ) -> ResearchReport:
        """Orchestrate all agents and generate comprehensive research report"""
        
        # Run all agents
        financial_analysis = self.financial_analysis_agent(ticker, company_info)
        technical_analysis = self.technical_analysis_agent(ticker, technical_indicators)
        news_analysis = self.news_analysis_agent(ticker, news_articles)
        
        # Synthesize final report
        if self.is_available():
            report = self._synthesize_report_with_ai(
                ticker,
                company_info,
                financial_analysis,
                technical_analysis,
                news_analysis
            )
        else:
            report = self._synthesize_report_fallback(
                ticker,
                company_info,
                financial_analysis,
                technical_analysis,
                news_analysis
            )
        
        return report
    
    def _generate_financial_analysis(self, ticker: str, company_info: CompanyInfo, metrics: Dict, missing_fields: List[str]) -> str:
        """Generate AI-powered financial analysis"""
        try:
            # Build metrics section with proper handling of missing values
            metrics_lines = []
            
            # Sector and Industry
            sector = metrics.get('sector', 'Unavailable')
            industry = metrics.get('industry', 'Unavailable')
            metrics_lines.append(f"Sector: {sector}")
            metrics_lines.append(f"Industry: {industry}")
            
            # Market Cap - only show if available
            if 'market_cap' in metrics and metrics['market_cap']:
                metrics_lines.append(f"Market Cap: ${metrics['market_cap']:,.0f}")
            else:
                metrics_lines.append("Market Cap: Unavailable")
            
            # P/E Ratio - only show if available
            if 'pe_ratio' in metrics:
                metrics_lines.append(f"P/E Ratio: {metrics['pe_ratio']:.2f}")
            else:
                metrics_lines.append("P/E Ratio: Unavailable")
            
            # Dividend Yield - only show if available
            if 'dividend_yield' in metrics:
                metrics_lines.append(f"Dividend Yield: {metrics['dividend_yield']:.2f}%")
            else:
                metrics_lines.append("Dividend Yield: Unavailable")
            
            # Beta - only show if available
            if 'beta' in metrics:
                metrics_lines.append(f"Beta: {metrics['beta']:.2f}")
            else:
                metrics_lines.append("Beta: Unavailable")
            
            metrics_text = "\n".join(metrics_lines)
            
            # Build missing data section
            if missing_fields:
                missing_text = f"\n\nNote: The following data is unavailable: {', '.join(missing_fields)}"
            else:
                missing_text = ""
            
            prompt = f"""Analyze the following financial metrics for {ticker} ({company_info.name}):

{metrics_text}
{missing_text}

Provide a brief, factual analysis of the company's financial position. Focus only on the available metrics. Be clear about data limitations. Do not speculate about missing data."""

            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating financial analysis: {e}")
            return self._fallback_financial_analysis(ticker, metrics, missing_fields)
    
    def _fallback_financial_analysis(self, ticker: str, metrics: Dict, missing_fields: List[str]) -> str:
        """Fallback financial analysis without AI"""
        parts = [f"Financial analysis for {ticker}:"]
        
        # Market cap - only show if available
        if 'market_cap' in metrics and metrics.get('market_cap'):
            mc = metrics['market_cap']
            if mc > 200e9:
                parts.append(f"Large-cap stock with market capitalization of ${mc/1e9:.1f}B.")
            elif mc > 10e9:
                parts.append(f"Mid-cap stock with market capitalization of ${mc/1e9:.1f}B.")
            else:
                parts.append(f"Small-cap stock with market capitalization of ${mc/1e9:.1f}B.")
        
        # P/E ratio - only show if available
        if 'pe_ratio' in metrics and metrics.get('pe_ratio'):
            pe = metrics['pe_ratio']
            if pe > 30:
                parts.append(f"P/E ratio of {pe:.2f} suggests premium valuation.")
            elif pe > 15:
                parts.append(f"P/E ratio of {pe:.2f} indicates moderate valuation.")
            else:
                parts.append(f"P/E ratio of {pe:.2f} suggests value territory.")
        
        # Dividend yield - only show if available (can be 0.0 legitimately)
        if 'dividend_yield' in metrics and metrics.get('dividend_yield') is not None:
            dy = metrics['dividend_yield']
            if dy > 0:
                parts.append(f"Dividend yield of {dy:.2f}%.")
            else:
                parts.append("No dividend currently paid.")
        
        # Beta - only show if available
        if 'beta' in metrics and metrics.get('beta'):
            beta = metrics['beta']
            if beta > 1.5:
                parts.append(f"Beta of {beta:.2f} indicates high volatility relative to the market.")
            elif beta > 0.8:
                parts.append(f"Beta of {beta:.2f} indicates moderate volatility.")
            else:
                parts.append(f"Beta of {beta:.2f} indicates lower volatility relative to the market.")
        
        # Sector and industry
        sector = metrics.get('sector', 'Unavailable')
        industry = metrics.get('industry', 'Unavailable')
        if sector != 'Unavailable' or industry != 'Unavailable':
            parts.append(f"Sector: {sector}, Industry: {industry}.")
        
        # List missing data
        if missing_fields:
            parts.append(f"Note: The following data is unavailable: {', '.join(missing_fields)}.")
        
        return " ".join(parts)
    
    def _determine_trend(self, indicators: TechnicalIndicators) -> str:
        """Determine overall trend from indicators"""
        signals = []
        
        # Price vs Moving Averages
        if indicators.sma_50 and indicators.current_price > indicators.sma_50:
            signals.append(1)
        elif indicators.sma_50 and indicators.current_price < indicators.sma_50:
            signals.append(-1)
        
        # RSI
        if indicators.rsi_14:
            if indicators.rsi_14 > 70:
                signals.append(-1)  # Overbought
            elif indicators.rsi_14 < 30:
                signals.append(1)  # Oversold
        
        # MACD
        if indicators.macd and indicators.macd_signal:
            if indicators.macd > indicators.macd_signal:
                signals.append(1)
            else:
                signals.append(-1)
        
        avg_signal = sum(signals) / len(signals) if signals else 0
        
        if avg_signal > 0.3:
            return "Bullish"
        elif avg_signal < -0.3:
            return "Bearish"
        else:
            return "Neutral"
    
    def _generate_technical_analysis(self, ticker: str, indicators: TechnicalIndicators, trend: str) -> str:
        """Generate AI-powered technical analysis"""
        try:
            prompt = f"""Analyze these technical indicators for {ticker}:

Current Price: ${indicators.current_price:.2f}
SMA(20): {f'${indicators.sma_20:.2f}' if indicators.sma_20 else 'N/A'}
SMA(50): {f'${indicators.sma_50:.2f}' if indicators.sma_50 else 'N/A'}
SMA(200): {f'${indicators.sma_200:.2f}' if indicators.sma_200 else 'N/A'}
RSI(14): {f'{indicators.rsi_14:.2f}' if indicators.rsi_14 else 'N/A'}
MACD: {f'{indicators.macd:.4f}' if indicators.macd else 'N/A'}
MACD Signal: {f'{indicators.macd_signal:.4f}' if indicators.macd_signal else 'N/A'}

Overall Trend: {trend}

Provide a brief technical analysis explaining the price action, momentum, and what these indicators suggest."""

            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating technical analysis: {e}")
            return self._fallback_technical_analysis(ticker, indicators, trend)
    
    def _fallback_technical_analysis(self, ticker: str, indicators: TechnicalIndicators, trend: str) -> str:
        """Fallback technical analysis without AI"""
        parts = [f"Technical analysis for {ticker} shows a {trend} trend."]
        
        if indicators.sma_50:
            if indicators.current_price > indicators.sma_50:
                parts.append("Price is above the 50-day moving average, indicating positive momentum.")
            else:
                parts.append("Price is below the 50-day moving average, indicating weakness.")
        
        if indicators.rsi_14:
            if indicators.rsi_14 > 70:
                parts.append(f"RSI at {indicators.rsi_14:.1f} suggests overbought conditions.")
            elif indicators.rsi_14 < 30:
                parts.append(f"RSI at {indicators.rsi_14:.1f} suggests oversold conditions.")
            else:
                parts.append(f"RSI at {indicators.rsi_14:.1f} is in neutral territory.")
        
        return " ".join(parts)
    
    def _generate_news_analysis(self, ticker: str, articles: List[NewsArticle]) -> tuple:
        """Generate AI-powered news analysis"""
        try:
            headlines = "\n".join([f"- {article.title}" for article in articles[:10]])
            
            prompt = f"""Analyze these recent news headlines for {ticker}:

{headlines}

Provide:
1. A brief summary of the key themes
2. Overall sentiment (Positive/Negative/Mixed/Neutral)
3. Notable developments or concerns

Format: First line should be just the sentiment word, then the analysis."""

            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            lines = content.split('\n', 1)
            sentiment = lines[0].strip()
            analysis = lines[1].strip() if len(lines) > 1 else content
            
            # Validate sentiment
            valid_sentiments = ['Positive', 'Negative', 'Mixed', 'Neutral']
            if sentiment not in valid_sentiments:
                sentiment = 'Mixed'
            
            return analysis, sentiment
        except Exception as e:
            logger.error(f"Error generating news analysis: {e}")
            return self._fallback_news_analysis(ticker, articles)
    
    def _fallback_news_analysis(self, ticker: str, articles: List[NewsArticle]) -> tuple:
        """Fallback news analysis without AI"""
        analysis = f"Found {len(articles)} recent news articles about {ticker}. "
        analysis += f"Recent headlines include: {articles[0].title}" if articles else "No specific themes identified."
        return analysis, "Neutral"
    
    def _synthesize_report_with_ai(
        self,
        ticker: str,
        company_info: Optional[CompanyInfo],
        financial: FinancialAnalysis,
        technical: TechnicalAnalysisReport,
        news: NewsAnalysisReport
    ) -> ResearchReport:
        """Synthesize comprehensive report using AI"""
        try:
            company_name = company_info.name if company_info else ticker
            
            prompt = f"""Create a comprehensive investment research report for {ticker} ({company_name}).

FINANCIAL ANALYSIS:
{financial.analysis}

TECHNICAL ANALYSIS:
{technical.analysis}
Trend: {technical.trend}

NEWS ANALYSIS:
{news.analysis}
Sentiment: {news.sentiment}

Generate a structured report with:
1. Executive Summary (2-3 sentences)
2. Company Overview (if available)
3. Key Bullish Factors (list 3-5)
4. Key Bearish Factors (list 3-5)
5. Risk Factors (list 3-5)
6. Evidence Quality Assessment

Be factual and acknowledge data limitations. Format as JSON with keys: executive_summary, company_overview, bullish_factors (array), bearish_factors (array), risk_factors (array), evidence_quality."""

            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                # Remove markdown code blocks if present
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                    content = content.strip()
                
                report_data = json.loads(content)
            except:
                # Fallback to creating structure
                report_data = {
                    "executive_summary": content[:500],
                    "company_overview": company_info.description[:500] if company_info and company_info.description else "Limited information available.",
                    "bullish_factors": ["Positive technical momentum", "Active news coverage"],
                    "bearish_factors": ["Market volatility", "Limited fundamental data"],
                    "risk_factors": ["Market risk", "Data completeness", "Timing uncertainty"],
                    "evidence_quality": "Moderate - based on available technical and market data"
                }
            
            missing_warnings = []
            if financial.missing_fields:
                missing_warnings.append(f"Financial data incomplete: {', '.join(financial.missing_fields)}")
            if not news.articles:
                missing_warnings.append("No recent news articles available")
            
            sources = ["Yahoo Finance (market data)"]
            if news.articles:
                sources.append(f"{news.articles[0].source} (news)")
            
            return ResearchReport(
                ticker=ticker,
                company_name=company_name,
                executive_summary=report_data.get("executive_summary", "Analysis completed."),
                company_overview=report_data.get("company_overview", company_info.description if company_info else ""),
                technical_analysis=technical.analysis,
                fundamental_analysis=financial.analysis,
                news_analysis=news.analysis,
                bullish_factors=report_data.get("bullish_factors", []),
                bearish_factors=report_data.get("bearish_factors", []),
                risk_factors=report_data.get("risk_factors", []),
                evidence_quality=report_data.get("evidence_quality", "Moderate"),
                missing_data_warnings=missing_warnings,
                sources=sources,
                generated_at=datetime.utcnow(),
                data_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error synthesizing report with AI: {e}")
            return self._synthesize_report_fallback(ticker, company_info, financial, technical, news)
    
    def _synthesize_report_fallback(
        self,
        ticker: str,
        company_info: Optional[CompanyInfo],
        financial: FinancialAnalysis,
        technical: TechnicalAnalysisReport,
        news: NewsAnalysisReport
    ) -> ResearchReport:
        """Fallback report synthesis without AI"""
        company_name = company_info.name if company_info else ticker
        
        executive_summary = f"Research report for {company_name} ({ticker}). "
        executive_summary += f"Technical trend is {technical.trend}. "
        executive_summary += f"News sentiment is {news.sentiment}."
        
        bullish_factors = []
        bearish_factors = []
        
        if technical.trend == "Bullish":
            bullish_factors.append("Positive technical momentum")
        elif technical.trend == "Bearish":
            bearish_factors.append("Negative technical trend")
        
        if news.sentiment in ["Positive", "Mixed"]:
            bullish_factors.append("Favorable news coverage")
        elif news.sentiment == "Negative":
            bearish_factors.append("Negative news sentiment")
        
        bullish_factors.append("Available market data for analysis")
        bearish_factors.append("Limited AI synthesis")
        
        risk_factors = [
            "Market volatility and systematic risk",
            "Data completeness and timeliness",
            "Analysis limitations without full AI processing"
        ]
        
        missing_warnings = []
        if financial.missing_fields:
            missing_warnings.append(f"Financial data incomplete: {', '.join(financial.missing_fields)}")
        if not news.articles:
            missing_warnings.append("No recent news articles available")
        missing_warnings.append("AI synthesis unavailable - using rule-based analysis")
        
        return ResearchReport(
            ticker=ticker,
            company_name=company_name,
            executive_summary=executive_summary,
            company_overview=company_info.description[:500] if company_info and company_info.description else "Company information limited.",
            technical_analysis=technical.analysis,
            fundamental_analysis=financial.analysis,
            news_analysis=news.analysis,
            bullish_factors=bullish_factors,
            bearish_factors=bearish_factors,
            risk_factors=risk_factors,
            evidence_quality="Limited - rule-based analysis without AI synthesis",
            missing_data_warnings=missing_warnings,
            sources=["Yahoo Finance (market data)", news.articles[0].source if news.articles else "No news source"],
            generated_at=datetime.utcnow(),
            data_timestamp=datetime.utcnow()
        )
    
    def parse_strategy_from_natural_language(self, natural_language: str) -> Dict[str, Any]:
        """Parse natural language strategy description into structured conditions
        
        Returns:
            Dict with 'name', 'description', 'conditions' on success
            Dict with 'error' key on failure (never raises)
        """
        if not self.is_available():
            return {"error": "AI services unavailable for natural language parsing. Please configure GROQ_API_KEY."}
        
        if not natural_language or not natural_language.strip():
            return {"error": "Empty strategy description provided"}
        
        try:
            prompt = f"""Convert this stock screening strategy into structured conditions:

"{natural_language}"

Available fields: price, sma_20, sma_50, sma_200, rsi_14, macd, volume, market_cap, pe_ratio
Available operators: >, <, >=, <=, =

Return JSON with format:
{{
  "name": "strategy name",
  "description": "brief description",
  "conditions": [
    {{"field": "field_name", "operator": ">", "value": number}}
  ]
}}"""

            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=500
            )
            
            # Validate response structure
            if not response.choices:
                logger.error("Groq returned empty choices array")
                return {"error": "AI model returned empty response. Please try again."}
            
            content = response.choices[0].message.content
            
            if not content or not content.strip():
                logger.error("Groq returned empty message content")
                return {"error": "AI model returned empty content. Please try again."}
            
            content = content.strip()
            
            # Remove markdown code blocks
            if content.startswith('```'):
                parts = content.split('```')
                if len(parts) >= 2:
                    content = parts[1]
                    if content.startswith('json'):
                        content = content[4:]
                    content = content.strip()
            
            # Parse JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}\nContent: {content[:200]}")
                return {"error": f"AI returned invalid JSON. Please rephrase your strategy and try again."}
            
            # Validate required fields
            if not isinstance(result, dict):
                logger.error(f"AI returned non-object result: {type(result)}")
                return {"error": "AI returned invalid structure. Expected a strategy object."}
            
            if "conditions" not in result:
                logger.error("AI response missing 'conditions' field")
                return {"error": "AI did not generate any screening conditions. Please provide a clearer strategy description."}
            
            if not isinstance(result.get("conditions"), list):
                logger.error("AI 'conditions' is not a list")
                return {"error": "AI returned invalid conditions format."}
            
            # Validate and sanitize each condition
            validated_conditions = []
            allowed_fields = {'price', 'sma_20', 'sma_50', 'sma_200', 'rsi_14', 'macd', 'volume', 'market_cap', 'pe_ratio'}
            allowed_operators = {'>', '<', '>=', '<=', '='}
            
            for i, cond in enumerate(result.get("conditions", [])):
                if not isinstance(cond, dict):
                    logger.warning(f"Condition {i} is not an object, skipping")
                    continue
                
                field = cond.get("field")
                operator = cond.get("operator")
                value = cond.get("value")
                
                if not field or not operator or value is None:
                    logger.warning(f"Condition {i} missing required fields, skipping")
                    continue
                
                if field not in allowed_fields:
                    logger.warning(f"Condition {i} has invalid field '{field}', skipping")
                    continue
                
                if operator not in allowed_operators:
                    logger.warning(f"Condition {i} has invalid operator '{operator}', skipping")
                    continue
                
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    logger.warning(f"Condition {i} has non-numeric value '{value}', skipping")
                    continue
                
                validated_conditions.append({
                    "field": field,
                    "operator": operator,
                    "value": value
                })
            
            if not validated_conditions:
                logger.error("No valid conditions after validation")
                return {"error": "Could not extract valid screening conditions from your description. Please be more specific."}
            
            # Return sanitized result
            return {
                "name": result.get("name", "Custom Strategy"),
                "description": result.get("description", natural_language[:100]),
                "conditions": validated_conditions
            }
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Check for specific error types
            if "404" in error_msg or "model_not_found" in error_msg.lower():
                logger.error(f"Groq model not found: {settings.groq_model}")
                return {"error": f"AI model '{settings.groq_model}' not found. Please contact support."}
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                logger.error("Groq API key invalid or expired")
                return {"error": "AI service authentication failed. Please check API key configuration."}
            elif "429" in error_msg or "rate" in error_msg.lower():
                logger.error("Groq rate limit exceeded")
                return {"error": "AI service rate limit reached. Please wait a moment and try again."}
            else:
                logger.error(f"Error parsing natural language strategy: {error_type}: {e}")
                return {"error": f"Failed to parse strategy: {error_type}. Please try again."}


# Service instance
ai_orchestrator = AIOrchestrator()
