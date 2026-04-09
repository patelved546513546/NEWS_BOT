import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from config import Config
from datetime import datetime
import html
import time
import socket
import requests

logger = logging.getLogger(__name__)

class EmailSender:
    """
    Email Sender - 100% FREE, UNLIMITED emails
    Uses Gmail SMTP
    """
    
    def __init__(self):
        self.sender_email = Config.GMAIL_ADDRESS
        self.sender_password = Config.GMAIL_APP_PASSWORD
        self.recipients = [r.strip() for r in Config.EMAIL_RECIPIENTS if r.strip()]
        self.resend_api_key = Config.RESEND_API_KEY
        self.resend_from_email = Config.RESEND_FROM_EMAIL

        self.smtp_server = "smtp.gmail.com"
        self.smtp_port_tls = 587
        self.smtp_port_ssl = 465
        self.max_retries = 3
        self.retry_backoff_seconds = 5
        self.smtp_timeout_seconds = 30

        if self.recipients and self._has_any_provider():
            logger.info(f"✅ Email initialized - {len(self.recipients)} recipient(s)")
        else:
            logger.error("❌ Email credentials missing!")
    
    def send_news(self, message):
        """Send email to all recipients"""

        if not self.recipients:
            logger.error("❌ Email not configured!")
            return False

        # Prefer HTTPS provider on restricted platforms like Render.
        if self._has_resend_provider():
            if self._send_with_resend(message):
                return True
            logger.warning("⚠️ Resend failed, trying SMTP fallback...")

        if not self._has_smtp_provider():
            logger.error("❌ No SMTP provider configured for fallback")
            return False
        
        msg = self._create_email(message)

        for attempt in range(1, self.max_retries + 1):
            try:
                sent_count = self._send_with_fallback_modes(msg)

                if sent_count > 0:
                    logger.info(f"✅ Email batch completed - {sent_count}/{len(self.recipients)} sent")
                    return True

                logger.error("❌ Email batch failed - no recipients were sent")
            except (smtplib.SMTPException, OSError, socket.error) as exc:
                logger.error(f"❌ Email attempt {attempt}/{self.max_retries} failed: {exc}")

            if attempt < self.max_retries:
                delay = self.retry_backoff_seconds * attempt
                logger.warning(f"⚠️ Retrying email in {delay}s...")
                time.sleep(delay)

        logger.error("❌ Email failed after retries")
        return False

    def _has_any_provider(self):
        return self._has_resend_provider() or self._has_smtp_provider()

    def _has_smtp_provider(self):
        return bool(self.sender_email and self.sender_password)

    def _has_resend_provider(self):
        return bool(self.resend_api_key and self.resend_from_email)

    def _send_with_resend(self, message):
        """Send using Resend API over HTTPS (port 443)."""
        try:
            payload = {
                "from": self.resend_from_email,
                "to": self.recipients,
                "subject": f"📰 Breaking News - {datetime.now().strftime('%I:%M %p')}",
                "text": message,
                "html": self._convert_to_html(message),
            }
            headers = {
                "Authorization": f"Bearer {self.resend_api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code in (200, 201):
                logger.info(f"✅ Email sent via Resend to {len(self.recipients)} recipient(s)")
                return True

            logger.error(f"❌ Resend API error: {response.status_code} - {response.text}")
            return False
        except Exception as exc:
            logger.error(f"❌ Resend send error: {exc}")
            return False

    def _send_with_fallback_modes(self, msg):
        """Try STARTTLS first, then SSL as fallback."""
        sent_count = self._send_with_starttls(msg)
        if sent_count > 0:
            return sent_count

        logger.warning("⚠️ STARTTLS send failed, trying SMTP SSL fallback...")
        return self._send_with_ssl(msg)

    def _send_with_starttls(self, msg):
        sent_count = 0
        with smtplib.SMTP(self.smtp_server, self.smtp_port_tls, timeout=self.smtp_timeout_seconds) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.sender_email, self.sender_password)

            for recipient in self.recipients:
                try:
                    server.send_message(msg, to_addrs=[recipient])
                    logger.info(f"✅ Email sent to {recipient}")
                    sent_count += 1
                except Exception as exc:
                    logger.error(f"❌ Failed for {recipient}: {exc}")

        return sent_count

    def _send_with_ssl(self, msg):
        sent_count = 0
        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port_ssl, timeout=self.smtp_timeout_seconds) as server:
            server.login(self.sender_email, self.sender_password)

            for recipient in self.recipients:
                try:
                    server.send_message(msg, to_addrs=[recipient])
                    logger.info(f"✅ Email sent to {recipient}")
                    sent_count += 1
                except Exception as exc:
                    logger.error(f"❌ Failed for {recipient}: {exc}")

        return sent_count
    
    def _create_email(self, message):
        """Create formatted email"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📰 Breaking News - {datetime.now().strftime('%I:%M %p')}"
        msg['From'] = f"News Bot <{self.sender_email}>"
        msg['To'] = ", ".join(self.recipients)

        part1 = MIMEText(message, 'plain')
        part2 = MIMEText(self._convert_to_html(message), 'html')

        msg.attach(part1)
        msg.attach(part2)

        return msg
    
    def _convert_to_html(self, message):
        """Convert plain text to HTML"""
        safe_text = html.escape(message).replace('\n', '<br>')

        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .content {{
            background: #f9f9f9;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 0 0 10px 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📰 Breaking News</h1>
        <p>{datetime.now().strftime('%A, %d %B %Y - %I:%M %p')}</p>
    </div>
    <div class="content">
        {safe_text}
    </div>
</body>
</html>
"""
    
    def send_test_message(self):
        """Send test email"""
        test_msg = """✅ Email News Bot Test

    Your bot is working!

📧 Platform: Email (Gmail SMTP)
    💰 Cost: FREE
    📊 Messages: UNLIMITED

    You'll receive news updates automatically."""
        
        return self.send_news(test_msg)
    
    def send_startup_notification(self):
        """Send startup notification"""
        startup_msg = f"""✅ News Bot Started!

⏰ Updates every {Config.UPDATE_INTERVAL} minutes
    📰 Top {Config.MAX_ARTICLES} stories
🤖 Powered by AI

🚀 First update coming now!"""
        
        return self.send_news(startup_msg)
    
    def send_error_alert(self, error_message):
        """Send error alert"""
        alert = f"""🚨 BOT ERROR

{error_message}

    Time: {datetime.now().strftime('%I:%M %p')}"""
        
        return self.send_news(alert)
    
    def health_check(self):
        """Check if email is configured"""
        return bool(self.recipients and self._has_any_provider())