import requests
import feedparser
from typing import List, Optional
from datetime import datetime
from models import NewsArticle
from config import settings
import logging

logger = logging.getLogger(__name__)

class NewsProviderAdapter:
    """Adapter for news providers with NewsData.io and RSS fallback"""
    
    def __init__(self):
        self.newsdata_api_key = settings.newsdata_api_key
        self.newsdata_base_url = "https://newsdata.io/api/1/news"
    
    def get_company_news(self, ticker: str, company_name: Optional[str] = None) -> List[NewsArticle]:
        """Get news articles for a company"""
        # Try NewsData.io first if API key is available
        if self.newsdata_api_key:
            articles = self._get_newsdata_articles(ticker, company_name)
            if articles:
                return articles
        
        # Fallback to RSS feeds
        return self._get_rss_articles(ticker, company_name)
    
    def _get_newsdata_articles(self, ticker: str, company_name: Optional[str] = None) -> List[NewsArticle]:
        """Get articles from NewsData.io"""
        try:
            # Build search query
            query = ticker
            if company_name:
                query = f"{company_name} OR {ticker}"
            
            params = {
                'apikey': self.newsdata_api_key,
                'q': query,
                'language': 'en',
                'category': 'business',
                'size': 10
            }
            
            response = requests.get(self.newsdata_base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'success':
                logger.warning(f"NewsData.io returned non-success status: {data.get('status')}")
                return []
            
            articles = []
            seen_urls = set()
            
            for result in data.get('results', []):
                url = result.get('link')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    
                    published_at = None
                    if result.get('pubDate'):
                        try:
                            published_at = datetime.fromisoformat(result['pubDate'].replace('Z', '+00:00'))
                        except:
                            pass
                    
                    articles.append(NewsArticle(
                        title=result.get('title', 'Untitled'),
                        source=result.get('source_id', 'Unknown'),
                        published_at=published_at,
                        url=url,
                        description=result.get('description')
                    ))
            
            return articles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from NewsData.io: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error with NewsData.io: {e}")
            return []
    
    def _get_rss_articles(self, ticker: str, company_name: Optional[str] = None) -> List[NewsArticle]:
        """Get articles from RSS feeds as fallback"""
        try:
            articles = []
            seen_urls = set()
            
            # Yahoo Finance RSS feed for the ticker
            feed_urls = [
                f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
            ]
            
            for feed_url in feed_urls:
                try:
                    feed = feedparser.parse(feed_url)
                    
                    for entry in feed.entries[:10]:
                        url = entry.get('link')
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            
                            published_at = None
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                published_at = datetime(*entry.published_parsed[:6])
                            
                            articles.append(NewsArticle(
                                title=entry.get('title', 'Untitled'),
                                source='Yahoo Finance RSS',
                                published_at=published_at,
                                url=url,
                                description=entry.get('summary')
                            ))
                except Exception as e:
                    logger.error(f"Error parsing RSS feed {feed_url}: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Error with RSS fallback: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if any news provider is available"""
        return bool(self.newsdata_api_key) or True  # RSS is always available


news_provider = NewsProviderAdapter()
