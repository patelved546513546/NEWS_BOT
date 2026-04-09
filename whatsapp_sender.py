import requests
import urllib.parse
import logging
from config import Config
import time

logger = logging.getLogger(__name__)

class WhatsAppSender:
    def __init__(self):
        self.phone_number = Config.WHATSAPP_NUMBER
        self.api_key = Config.CALLMEBOT_API_KEY
        self.base_url = "https://api.callmebot.com/whatsapp.php"
        self.retry_count = 3
        self.retry_delay = 5
        
    def send_news(self, message):
        if not self.phone_number or not self.api_key:
            logger.error("❌ WhatsApp credentials not configured!")
            return False
        
        for attempt in range(1, self.retry_count + 1):
            try:
                success = self._send_message(message)
                if success:
                    return True
                    
                if attempt < self.retry_count:
                    logger.warning(f"⚠️ Attempt {attempt} failed, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                logger.error(f"❌ Attempt {attempt} error: {e}")
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay)
        
        logger.error(f"❌ Failed after {self.retry_count} attempts")
        return False

    def health_check(self):
        """Check if WhatsApp is configured"""
        if not self.phone_number or not self.api_key:
            return False

        phone = self.phone_number.strip().lower()
        api_key = self.api_key.strip().lower()
        invalid_markers = ["your_", "callmebot_key", "placeholder", "api_key"]

        return not any(marker in phone for marker in invalid_markers) and not any(
            marker in api_key for marker in invalid_markers
        )
    
    def _send_message(self, message):
        encoded_message = urllib.parse.quote(message)
        
        url = (
            f"{self.base_url}"
            f"?phone={self.phone_number}"
            f"&text={encoded_message}"
            f"&apikey={self.api_key}"
        )
        
        logger.info(f"📱 Sending message to {self.phone_number[:4]}****")
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            logger.info("✅ Message sent successfully!")
            return True
        else:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            return False
    
    def send_test_message(self):
        test_msg = """✅ *WhatsApp News Bot Test*

Your bot is configured correctly!

📱 Phone: Working
🔑 API Key: Valid
🤖 Bot Status: Online

You will start receiving news updates automatically."""
        
        return self.send_news(test_msg)
    
    def send_startup_notification(self):
        startup_msg = f"""✅ *News Bot Started Successfully!*

⏰ Updates every {Config.UPDATE_INTERVAL} minutes
📰 Top {Config.MAX_ARTICLES} breaking news stories
🤖 Powered by AI

🚀 First update coming now!"""
        
        return self.send_news(startup_msg)
    
    def send_error_alert(self, error_message):
        alert = f"""🚨 *BOT ERROR ALERT*

{error_message}

Please check the logs immediately!

⏰ {time.strftime('%I:%M %p')}"""
        
        return self.send_news(alert)