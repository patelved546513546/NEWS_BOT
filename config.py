"""
Configuration management for the news bot.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Email Settings
    GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
    EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS", "").split(",")

    # Optional: HTTPS email provider (recommended on Render if SMTP is blocked)
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL")

    # AI Settings
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # Bot Settings
    UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL_MINUTES", 15))
    MAX_ARTICLES = int(os.getenv("MAX_NEWS_ARTICLES", 5))
    TIMEZONE = os.getenv("TIMEZONE", "UTC")
    PORT = int(os.getenv("PORT", 8080))
    NEWS_CATEGORY = os.getenv("NEWS_CATEGORY", "world").strip().lower()
    STOCK_REGIONS = ["india", "us"]

    # RSS Feeds by category
    CATEGORY_FEEDS = {
        "world": [
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "http://rss.cnn.com/rss/edition_world.rss",
            "https://www.aljazeera.com/xml/rss/all.xml",
            "https://feeds.reuters.com/reuters/topNews",
            "https://www.reddit.com/r/worldnews/.rss",
        ],
        "science": [
            "https://www.sciencedaily.com/rss/all.xml",
            "https://www.sciencenews.org/feed",
            "https://www.reddit.com/r/science/.rss",
        ],
        "technology": [
            "https://feeds.arstechnica.com/arstechnica/index",
            "https://www.theverge.com/rss/index.xml",
            "https://techcrunch.com/feed/",
            "https://www.reddit.com/r/technology/.rss",
            "https://news.ycombinator.com/rss",
        ],
        "politics": [
            "https://www.politico.com/rss/politics08.xml",
            "https://feeds.bbci.co.uk/news/politics/rss.xml",
            "https://www.reddit.com/r/politics/.rss",
            "http://rss.cnn.com/rss/cnn_allpolitics.rss",
        ],
        "stock_market": [
            "https://feeds.reuters.com/reuters/businessNews",
            "https://feeds.reuters.com/news/usmarkets",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
            "https://www.moneycontrol.com/rss/business.xml",
            "https://www.reddit.com/r/stocks/.rss",
            "https://www.reddit.com/r/investing/.rss",
            "https://www.reddit.com/r/IndianStreetBets/.rss",
        ],
        "stock_market_impact": [
            "https://feeds.reuters.com/reuters/businessNews",
            "https://feeds.reuters.com/news/usmarkets",
            "https://www.ft.com/markets?format=rss",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
            "https://www.moneycontrol.com/rss/business.xml",
            "https://www.reddit.com/r/economics/.rss",
            "https://www.reddit.com/r/IndianStreetBets/.rss",
        ],
    }

    @classmethod
    def get_active_feeds(cls):
        """Return feed list for selected category, fallback to world."""
        if cls.NEWS_CATEGORY in cls.CATEGORY_FEEDS:
            return cls.CATEGORY_FEEDS[cls.NEWS_CATEGORY]
        return cls.CATEGORY_FEEDS["world"]

    # Optional: Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # Optional: WhatsApp
    WHATSAPP_NUMBER = os.getenv("YOUR_WHATSAPP_NUMBER")
    CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")

    @classmethod
    def validate(cls):
        email_provider_ok = (
            bool(cls.GMAIL_ADDRESS and cls.GMAIL_APP_PASSWORD)
            or bool(cls.RESEND_API_KEY and cls.RESEND_FROM_EMAIL)
        )

        required = [
            ("GROQ_API_KEY", cls.GROQ_API_KEY),
        ]

        missing = [name for name, value in required if not value]
        if not email_provider_ok:
            missing.append("EMAIL_PROVIDER(GMAIL_* or RESEND_*)")

        if missing:
            raise ValueError(f"Missing config: {', '.join(missing)}")

        return True
