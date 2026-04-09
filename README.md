# Automated News Alert Bot

Send breaking news updates automatically to Email, with optional Telegram and WhatsApp delivery.

## Features

- RSS news ingestion from BBC, CNN, Al Jazeera, Reuters, and Reddit WorldNews
- AI summary generation using Groq
- Primary delivery via Gmail SMTP
- Optional delivery via Telegram Bot API and CallMeBot WhatsApp
- Scheduler-based updates every 15 minutes (configurable)
- Flask health endpoint for monitoring and uptime checks
- Render.com compatible deployment

## Project Structure

```
whatsapp-news-bot/
├── logs/
├── .env
├── .env.example
├── .gitignore
├── config.py
├── news_fetcher.py
├── ai_processor.py
├── email_sender.py
├── telegram_sender.py
├── whatsapp_sender.py
├── main.py
├── requirements.txt
├── render.yaml
├── Dockerfile
└── README.md
```

## Prerequisites

1. Python 3.11
2. Gmail account with App Password enabled
3. Groq API key
4. Optional: Telegram bot token/chat ID and CallMeBot credentials

## Local Setup

```bash
# 1) Create and activate a virtual environment
python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# 2) Install dependencies
pip install -r requirements.txt

# 3) Create env file from template
copy .env.example .env

# 4) Edit .env with your real values

# 5) Run
python main.py
```

## Required Environment Variables

```
GMAIL_ADDRESS=your.email@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
EMAIL_RECIPIENTS=you@example.com,friend@example.com
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxx
UPDATE_INTERVAL_MINUTES=15
MAX_NEWS_ARTICLES=5
TIMEZONE=Asia/Kolkata
PORT=8080
```

## Optional Variables

```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
YOUR_WHATSAPP_NUMBER=919876543210
CALLMEBOT_API_KEY=...
```

## API Endpoints

- GET / : Basic status page
- GET /health : JSON health information
- GET /trigger : Manually trigger one update cycle

## Deploy to Render

1. Push repository to GitHub
2. Create a new Web Service in Render
3. Use build command: `pip install -r requirements.txt`
4. Use start command: `python main.py`
5. Set all required env vars in Render dashboard
6. Set `PYTHON_VERSION=3.11.9` in Render environment variables
7. Verify `healthCheckPath` is `/health`

## Keep Free Service Awake

This repo includes a GitHub Actions workflow at `.github/workflows/render-keepalive.yml`
that sends an external visitor request every 10 minutes.

Setup steps:

1. Open your GitHub repository settings
2. Go to Secrets and variables, then Actions
3. Add a new repository secret named `RENDER_HEALTHCHECK_URL`
4. Set it to your Render URL, for example:

	`https://your-service-name.onrender.com/health`

5. Ensure GitHub Actions is enabled for the repository

Optional: you can still use UptimeRobot as a backup monitor.

## Troubleshooting

- Email not sending: verify Gmail App Password, not your account password
- AI errors: verify Groq key and rate limits
- No updates: check logs/newsbot.log and `/health` output
- Timezone issues: set a valid pytz timezone string in TIMEZONE

## License

MIT