"""
Telegram Sender - Sends news via Telegram Bot API
"""

import logging
import requests
from config import Config

logger = logging.getLogger(__name__)


class TelegramSender:
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.base_url = "https://api.telegram.org"

    def send_news(self, message):
        """Send message to configured Telegram chat"""
        if not self.health_check():
            logger.error("❌ Telegram not configured!")
            return False

        url = f"{self.base_url}/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "disable_web_page_preview": True,
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                logger.info("✅ Telegram message sent")
                return True

            logger.error(f"❌ Telegram HTTP error: {response.status_code} - {response.text}")
            return False
        except Exception as exc:
            logger.error(f"❌ Telegram error: {exc}")
            return False

    def health_check(self):
        """Check if Telegram is configured"""
        if not self.bot_token or not self.chat_id:
            return False

        token = self.bot_token.strip().lower()
        chat_id = self.chat_id.strip().lower()
        invalid_markers = ["your_", "telegram_bot_token", "telegram_chat_id", "placeholder"]

        return not any(marker in token for marker in invalid_markers) and not any(
            marker in chat_id for marker in invalid_markers
        )
