import schedule
import time
import signal
import sys
from datetime import datetime
from news_fetcher import NewsFetcher
from ai_processor import AIProcessor
from email_sender import EmailSender
from telegram_sender import TelegramSender
from whatsapp_sender import WhatsAppSender
from pdf_generator import PDFGenerator
from config import Config
from flask import Flask, jsonify
from threading import Thread
import logging
import os

# Avoid Unicode logging crashes on Windows terminals that default to cp1252.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/newsbot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class _SafeLogFilter(logging.Filter):
    def filter(self, record):
        try:
            message = record.getMessage()
            safe_message = message.encode("cp1252", errors="replace").decode("cp1252")
            record.msg = safe_message
            record.args = ()
        except Exception:
            pass
        return True


for _handler in logging.getLogger().handlers:
    _handler.addFilter(_SafeLogFilter())

app = Flask(__name__)

bot_status = {
    "status": "starting",
    "last_update": None,
    "total_updates": 0,
    "errors": 0,
    "uptime_start": datetime.now().isoformat()
}

@app.route('/')
def home():
    return """
    <h1>📱 News Bot</h1>
    <p>✅ Bot is running!</p>
    <p><a href="/health">Health Status</a></p>
    """

@app.route('/health')
def health():
    return jsonify(bot_status)

@app.route('/trigger')
def trigger():
    try:
        bot.send_news_update()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def run_flask():
    app.run(host='0.0.0.0', port=Config.PORT, debug=False, use_reloader=False)

class NewsBot:
    def __init__(self):
        self.fetcher = NewsFetcher()
        self.ai = AIProcessor()
        self.email = EmailSender()
        self.telegram = TelegramSender()
        self.whatsapp = WhatsAppSender()
        self.pdf = PDFGenerator(output_dir="logs")
        self.running = True
        self.error_count = 0
        
    def send_news_update(self):
        """Main update function"""
        global bot_status
        
        try:
            logger.info("⏰ Starting update...")
            bot_status["status"] = "fetching"
            
            news = self.fetcher.get_latest_news(max_articles=Config.MAX_ARTICLES)
            
            if not news:
                logger.warning("⚠️ No news found")
                return
            
            logger.info("🤖 Generating summary...")
            summary = self.ai.summarize_news(news)

            send_results = []

            logger.info("📧 Sending email...")
            send_results.append(self.email.send_news(summary))

            if self.telegram.health_check():
                logger.info("📨 Sending telegram...")
                send_results.append(self.telegram.send_news(summary))

            if self.whatsapp.health_check():
                logger.info("📱 Sending WhatsApp...")
                send_results.append(self.whatsapp.send_news(summary))

            success = any(send_results)
            
            bot_status["total_updates"] += 1
            bot_status["last_update"] = datetime.now().isoformat()
            
            if success:
                self.error_count = 0
                bot_status["status"] = "running"
                logger.info("✅ Update completed!")
            else:
                self.error_count += 1
                bot_status["errors"] += 1
                
        except Exception as e:
            logger.error(f"💥 Error: {e}")
            self.error_count += 1
            bot_status["errors"] += 1

    def send_daily_pdf_digest(self):
        """Send one precise 24h digest as a PDF attachment."""
        global bot_status

        try:
            logger.info("📄 Starting daily PDF digest...")
            bot_status["status"] = "digesting"

            news = self.fetcher.get_news_for_window(
                hours=Config.DAILY_DIGEST_HOURS,
                max_articles=Config.DAILY_DIGEST_MAX_ARTICLES,
                entries_per_feed=20,
            )

            if not news:
                logger.warning("⚠️ No news found for daily digest")
                return

            digest_text = self.ai.summarize_daily_digest(news)
            pdf_path = self.pdf.create_daily_digest_pdf(digest_text, category=Config.NEWS_CATEGORY)

            subject = f"📰 Daily News PDF Digest - {datetime.now().strftime('%d %b %Y')}"
            intro = (
                f"Attached is your 24-hour news digest PDF for category: {Config.NEWS_CATEGORY}.\n\n"
                f"Articles analyzed: {len(news)}\n"
                f"Window: last {Config.DAILY_DIGEST_HOURS} hours"
            )

            success = self.email.send_news(intro, subject=subject, attachment_path=pdf_path)

            bot_status["total_updates"] += 1
            bot_status["last_update"] = datetime.now().isoformat()

            if success:
                self.error_count = 0
                bot_status["status"] = "running"
                logger.info("✅ Daily PDF digest sent")
            else:
                self.error_count += 1
                bot_status["errors"] += 1

        except Exception as e:
            logger.error(f"💥 Daily digest error: {e}")
            self.error_count += 1
            bot_status["errors"] += 1
    
    def graceful_shutdown(self, signum, frame):
        logger.info("🛑 Shutting down...")
        self.running = False
        sys.exit(0)
    
    def run_continuous(self):
        """Main loop"""
        signal.signal(signal.SIGINT, self.graceful_shutdown)
        signal.signal(signal.SIGTERM, self.graceful_shutdown)

        logger.info("🤖 News Bot Starting...")
        logger.info(f"⏰ Update interval: {Config.UPDATE_INTERVAL} minutes")
        logger.info(f"📦 Delivery mode: {Config.DELIVERY_MODE}")

        if not self.email.health_check():
            logger.warning("⚠️ Email sender not fully configured. Bot may not deliver alerts.")

        flask_thread = Thread(target=run_flask, daemon=True)
        flask_thread.start()

        time.sleep(2)
        logger.info(f"✅ Health server running on port {Config.PORT}")

        if self.email.health_check():
            self.email.send_startup_notification()

        if Config.DELIVERY_MODE == "daily_pdf":
            schedule.every().day.at(Config.DIGEST_SEND_TIME).do(self.send_daily_pdf_digest)
            logger.info(f"📄 Daily PDF digest scheduled at {Config.DIGEST_SEND_TIME}")
            self.send_daily_pdf_digest()
        else:
            self.send_news_update()
            schedule.every(Config.UPDATE_INTERVAL).minutes.do(self.send_news_update)

        bot_status["status"] = "running"

        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"💥 Error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    try:
        Config.validate()
        bot = NewsBot()
        bot.run_continuous()
    except ValueError as e:
        logger.error(f"❌ Config error: {e}")
        sys.exit(1)