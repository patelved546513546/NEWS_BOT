from groq import Groq
import logging
from config import Config
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class AIProcessor:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = Config.GROQ_MODEL
        self.fallback_models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
        self.timezone = pytz.timezone(Config.TIMEZONE)
        
    def summarize_news(self, news_articles):
        if not news_articles:
            return self._no_news_message()
        
        current_time = datetime.now(self.timezone).strftime("%I:%M %p, %d %B %Y")
        news_text = self._format_news_for_ai(news_articles)
        prompt = self._create_prompt(news_text, current_time)
        
        tried = []
        candidate_models = [self.model] + [m for m in self.fallback_models if m != self.model]

        for model_name in candidate_models:
            tried.append(model_name)
            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional news anchor creating urgent alerts. Be concise, engaging, and clear."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=600
                )

                summary = response.choices[0].message.content
                logger.info(f"✅ AI summary generated with model: {model_name}")
                return summary
            except Exception as exc:
                logger.warning(f"⚠️ AI model failed ({model_name}): {exc}")

        logger.error(f"❌ AI failed for all models: {', '.join(tried)}")
        return self._fallback_format(news_articles, current_time)

    def summarize_daily_digest(self, news_articles):
        """Generate a concise daily digest suitable for PDF export."""
        if not news_articles:
            current_time = datetime.now(self.timezone).strftime("%d %B %Y")
            return f"Daily News Digest - {current_time}\n\nNo significant news was collected in the last 24 hours."

        current_time = datetime.now(self.timezone).strftime("%d %B %Y")
        news_text = self._format_news_for_ai(news_articles)
        prompt = f"""Create a precise 24-hour news digest from these items.

RULES:
- Keep it factual and concise
- Organize in sections: Top Stories, Markets, Policy/Economy, Geopolitics, Technology
- Include 8-15 bullet points total
- Each bullet should be one line
- No URLs
- End with 3-line "What to watch next" section

DATE: {current_time}

NEWS:
{news_text}
"""

        tried = []
        candidate_models = [self.model] + [m for m in self.fallback_models if m != self.model]

        for model_name in candidate_models:
            tried.append(model_name)
            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an editor writing a professional daily digest for investors and general readers.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.4,
                    max_tokens=1200,
                )
                digest = response.choices[0].message.content
                logger.info(f"✅ AI daily digest generated with model: {model_name}")
                return digest
            except Exception as exc:
                logger.warning(f"⚠️ Daily digest model failed ({model_name}): {exc}")

        logger.error(f"❌ Daily digest failed for all models: {', '.join(tried)}")
        return self._fallback_daily_digest(news_articles, current_time)

    def _fallback_daily_digest(self, articles, current_date):
        lines = [f"Daily News Digest - {current_date}", "", "Top Stories"]
        for idx, article in enumerate(articles[:12], 1):
            lines.append(f"{idx}. {article['title']} ({article['source']})")
        lines.extend(["", "What to watch next", "- Policy signals", "- Market reaction", "- Geopolitical follow-through"])
        return "\n".join(lines)
    
    def _format_news_for_ai(self, articles):
        formatted = []
        
        for i, article in enumerate(articles, 1):
            formatted.append(
                f"{i}. **{article['title']}**\n"
                f"   {article['description'][:200]}...\n"
                f"   Source: {article['source']}"
            )
        
        return "\n\n".join(formatted)
    
    def _create_prompt(self, news_text, current_time):
        return f"""Create a breaking news alert from these articles.

    RULES:
    - Start with "🚨 BREAKING NEWS"
    - Max 280 words
    - Cover 3-5 top stories
    - Use emojis (🔥⚡🌍💥)
    - End with "⏰ {current_time}"
    - NO URLs

NEWS ARTICLES:
{news_text}

    Write the alert now:"""

    def _fallback_format(self, articles, current_time):
        logger.warning("⚠️ Using fallback formatting")

        msg = "🚨 BREAKING NEWS\n\n"

        for i, article in enumerate(articles[:4], 1):
            msg += f"{i}. {article['title']}\n"
            msg += f"   {article['source']}\n\n"

        msg += f"⏰ {current_time}"

        return msg
    
    def _get_category_emoji(self, title):
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['war', 'attack', 'military']):
            return "⚔️"
        elif any(word in title_lower for word in ['economy', 'market', 'stock']):
            return "💰"
        elif any(word in title_lower for word in ['election', 'vote', 'president']):
            return "🗳️"
        elif any(word in title_lower for word in ['earthquake', 'storm', 'flood']):
            return "🌪️"
        elif any(word in title_lower for word in ['tech', 'ai', 'google']):
            return "💻"
        else:
            return "📰"
    
    def _no_news_message(self):
        current_time = datetime.now(self.timezone).strftime("%I:%M %p")
        return f"📰 No breaking news right now.\n\n⏰ {current_time}"