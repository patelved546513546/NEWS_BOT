import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from config import Config
from datetime import datetime
import html

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

        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

        if self.sender_email and self.sender_password and self.recipients:
            logger.info(f"✅ Email initialized - {len(self.recipients)} recipient(s)")
        else:
            logger.error("❌ Email credentials missing!")
    
    def send_news(self, message):
        """Send email to all recipients"""

        if not self.sender_email or not self.sender_password or not self.recipients:
            logger.error("❌ Email not configured!")
            return False
        
        try:
            msg = self._create_email(message)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)

                for recipient in self.recipients:
                    try:
                        server.send_message(msg, to_addrs=[recipient])
                        logger.info(f"✅ Email sent to {recipient}")
                    except Exception as e:
                        logger.error(f"❌ Failed for {recipient}: {e}")

            logger.info(f"✅ Email batch completed - {len(self.recipients)} sent")
            return True

        except Exception as e:
            logger.error(f"❌ Email error: {e}")
            return False
    
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
        return bool(self.sender_email and self.sender_password and self.recipients)