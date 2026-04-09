import feedparser
import requests
from datetime import datetime, timedelta
import logging
from config import Config
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class NewsFetcher:
    def __init__(self):
        self.category = Config.NEWS_CATEGORY
        self.rss_feeds = Config.get_active_feeds()
        self.stock_regions = getattr(Config, "STOCK_REGIONS", ["india", "us"])
        
    def get_latest_news(self, max_articles=5):
        all_news = []

        logger.info(f"📰 Fetching '{self.category}' news from {len(self.rss_feeds)} sources...")
        
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                source_name = self._get_source_name(feed, feed_url)
                
                for entry in feed.entries[:3]:
                    try:
                        article = {
                            'title': self._clean_text(entry.title),
                            'description': self._get_description(entry),
                            'link': entry.link,
                            'published': self._parse_date(entry),
                            'source': source_name
                        }
                        
                        if len(article['title']) > 10 and self._is_relevant_for_category(article):
                            all_news.append(article)
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error parsing entry: {e}")
                        continue
                
                logger.info(f"✅ Fetched from {source_name}")
                
            except Exception as e:
                logger.error(f"❌ Error fetching {feed_url}: {e}")
                continue
        
        unique_news = self._remove_duplicates(all_news)
        unique_news.sort(key=lambda x: x['published'], reverse=True)
        recent_news = self._filter_recent(unique_news, hours=4)
        
        logger.info(f"📊 Total: {len(all_news)}, Unique: {len(unique_news)}, Recent: {len(recent_news)}")
        
        return recent_news[:max_articles] if recent_news else unique_news[:max_articles]
    
    def _get_source_name(self, feed, url):
        try:
            if hasattr(feed.feed, 'title') and feed.feed.title:
                return feed.feed.title
        except:
            pass
        
        if 'bbc' in url.lower():
            return 'BBC News'
        elif 'cnn' in url.lower():
            return 'CNN'
        elif 'aljazeera' in url.lower():
            return 'Al Jazeera'
        elif 'reuters' in url.lower():
            return 'Reuters'
        elif 'reddit' in url.lower():
            return 'Reddit WorldNews'
        else:
            return 'News'
    
    def _get_description(self, entry):
        description = ""
        
        if hasattr(entry, 'summary'):
            description = entry.summary
        elif hasattr(entry, 'description'):
            description = entry.description
        elif hasattr(entry, 'content'):
            description = entry.content[0].value if entry.content else ""
        
        description = self._clean_text(description)
        return description[:300] if description else ""
    
    def _clean_text(self, text):
        if not text:
            return ""

        if "<" in text and ">" in text:
            soup = BeautifulSoup(text, 'html.parser')
            text = soup.get_text()

        text = re.sub(r'\s+', ' ', text).strip()
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        return text
    
    def _parse_date(self, entry):
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
        except:
            pass
        
        return datetime.now()
    
    def _filter_recent(self, news_list, hours=4):
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [news for news in news_list if news['published'] > cutoff_time]
    
    def _remove_duplicates(self, news_list):
        unique = []
        seen_titles = set()
        
        for article in news_list:
            title_hash = article['title'][:50].lower()
            
            if title_hash not in seen_titles:
                seen_titles.add(title_hash)
                unique.append(article)
        
        return unique

    def _is_relevant_for_category(self, article):
        """Apply stricter filtering for categories that need impact-focused coverage."""
        if self.category not in {"stock_market", "stock_market_impact"}:
            return True

        text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        market_keywords = [
            "stock",
            "stocks",
            "market",
            "markets",
            "nasdaq",
            "dow",
            "s&p",
            "sp500",
            "sensex",
            "nifty",
            "nse",
            "bse",
            "equity",
            "share",
            "shares",
            "index",
            "indices",
        ]
        region_keywords = [
            "india",
            "indian",
            "mumbai",
            "new delhi",
            "nse",
            "bse",
            "sensex",
            "nifty",
            "us",
            "u.s.",
            "united states",
            "wall street",
            "nyse",
            "nasdaq",
            "dow",
            "s&p",
            "federal reserve",
            "fed",
        ]
        impact_keywords = [
            "interest rate",
            "fed",
            "inflation",
            "earnings",
            "tariff",
            "oil",
            "bond",
            "recession",
            "gdp",
            "currency",
            "treasury",
            "futures",
            "guidance",
            "profit warning",
            "policy",
            "rate cut",
            "rate hike",
        ]

        has_market_signal = any(keyword in text for keyword in market_keywords)
        has_region_signal = any(keyword in text for keyword in region_keywords)

        if self.category == "stock_market":
            return has_market_signal and has_region_signal

        has_impact_signal = any(keyword in text for keyword in impact_keywords)
        return has_market_signal and has_region_signal and has_impact_signal
    
    def get_trending_keywords(self):
        try:
            url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
            feed = feedparser.parse(url)
            trends = [entry.title for entry in feed.entries[:5]]
            logger.info(f"📈 Trending: {trends}")
            return trends
        except Exception as e:
            logger.error(f"Error fetching trends: {e}")
            return []