# 🚀 Twitter Financial Signal Monitor

An MVP application that monitors Twitter accounts for financial signals, uses Google Gemini to summarize tweets, and sends structured alerts via Telegram.

## ✨ Features

- 🐦 **Twitter Scraping**: Monitors 10-15 Twitter accounts using authenticated scraping (no expensive API required)
- 🤖 **AI Summarization**: Uses Google Gemini to extract financial signals from tweets
- 📊 **Ticker Detection**: Regex-based extraction of stock/crypto tickers ($TSLA, BTC, etc.)
- 📱 **Telegram Alerts**: Sends formatted notifications with summaries, tickers, and action items
- 🔄 **Background Polling**: Automatically checks for new tweets every 60-90 seconds
- 🛡️ **Deduplication**: Never sends duplicate alerts for the same tweet
- 💾 **SQLite Storage**: Persists state, session cookies, and processed tweets
- 🌐 **REST API**: FastAPI endpoints for managing tracked handles
- ⌨️ **CLI Tool**: Command-line interface for quick operations

## 📋 Prerequisites

- Python 3.11 or higher
- Twitter account (dedicated account recommended)
- Telegram bot token and chat ID
- Google AI API key (for Gemini)

## 🔧 Installation

### Option A: GitHub Codespaces (Recommended) ☁️

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/pharmbro23/XScr)

1. **Click the badge above** or create a new Codespace from your repository
2. **Install dependencies** (automatic in Codespaces):
   ```bash
   pip install -r requirements.txt
   playwright install chromium --with-deps
   ```

3. **Configure environment** (see Configuration section below)

> **Note**: Codespaces runs in a headless environment. Playwright will use headless mode automatically. If Twitter requires 2FA, you may need to run authentication locally first and copy the database file, or disable 2FA on your dedicated Twitter account.

### Option B: Local Setup 💻

#### 1. Clone and Setup

```bash
cd XScr
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

#### 2. Install Playwright Browsers

```bash
# Local machine (GUI available)
playwright install chromium

# Server/headless environment
playwright install chromium --with-deps
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
# On Windows
copy .env.example .env

# On macOS/Linux/Codespaces
cp .env.example .env
```

Edit `.env` and fill in your credentials (use `nano .env` or the built-in editor in Codespaces):

```env
TWITTER_USERNAME=your_twitter_username
TWITTER_PASSWORD=your_twitter_password
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
GOOGLE_API_KEY=your_gemini_api_key
```

#### Getting Credentials:

**Twitter**: Use a dedicated account that follows your target accounts

**Telegram Bot Token**:
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the token provided

**Telegram Chat ID**:
1. Message your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find your `chat.id` in the response

**Google AI API Key**:
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key

## 🚀 Usage

### Option 1: Run the FastAPI Server (Recommended)

Start the server with automatic background polling:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**On Local Machine:**
- API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

**On GitHub Codespaces:**
- Codespaces will automatically forward port 8000
- Click the "Ports" tab in VS Code, then click the globe icon next to port 8000
- Or use the auto-generated URL: `https://<your-codespace-name>-8000.preview.app.github.dev`
- Access API docs at: `https://<your-codespace-name>-8000.preview.app.github.dev/docs`

### Option 2: Use the CLI

The CLI works the same in both local and Codespaces environments:

```bash
# Add a handle to track
python -m app.cli.commands add elonmusk

# List all tracked handles
python -m app.cli.commands list

# Remove a handle
python -m app.cli.commands remove elonmusk

# Manually trigger a poll
python -m app.cli.commands poll
```

## 🌐 API Endpoints

### Add a handle
```bash
curl -X POST http://localhost:8000/api/v1/tracks \
  -H "Content-Type: application/json" \
  -d '{"handle": "elonmusk"}'
```

### List handles
```bash
curl http://localhost:8000/api/v1/tracks
```

### Remove a handle
```bash
curl -X DELETE http://localhost:8000/api/v1/tracks/elonmusk
```

### Trigger manual poll
```bash
curl -X POST http://localhost:8000/api/v1/manual-poll
```

## 📊 How It Works

1. **Authentication**: On first run, Playwright opens a browser to log into Twitter
   - Supports 2FA and verification challenges
   - Session cookies are saved to SQLite for reuse

2. **Polling**: Every 60 seconds (configurable), the app:
   - Fetches the "Following" timeline from Twitter
   - Filters tweets from tracked handles
   - Checks for new tweets not yet processed

3. **Processing**: For each new tweet:
   - Extracts tickers using regex (fallback)
   - Sends tweet to Gemini for AI summarization
   - Formats a structured message
   - Sends alert to Telegram
   - Saves to database to prevent duplicates

4. **Summarization**: Gemini provides:
   - Summary bullets (up to 5 key points)
   - Detected tickers
   - Action type (buy/sell/watch/etc.)
   - Time horizon
   - Confidence level
   - Risks and verification checklist

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## 📁 Project Structure

```
XScr/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database/            # SQLite models and operations
│   ├── twitter/             # Twitter scraper and auth
│   ├── summarizer/          # Gemini LLM + ticker extraction
│   ├── telegram/            # Telegram notification client
│   ├── scheduler/           # Background polling job
│   ├── api/                 # FastAPI routes
│   └── cli/                 # CLI commands
├── tests/                   # Unit tests
├── data/                    # SQLite database (auto-created)
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
└── README.md               # This file
```

## ⚠️ Important Notes

### Twitter Scraping Considerations

- **Fragility**: Twitter's HTML structure can change, breaking the scraper
- **Rate Limits**: Aggressive polling may trigger account limits or CAPTCHAs
- **Terms of Service**: Scraping may violate Twitter's ToS (use at your own risk)
- **Mitigation**: The app uses respectful polling intervals (60s+) and graceful error handling

### Recommendations

- Use a dedicated Twitter account (not your primary)
- Start with 5-10 tracked handles
- Monitor logs for rate limit warnings
- Consider upgrading to official Twitter API if scaling up

## 🐛 Troubleshooting

### GitHub Codespaces Specific

**Playwright Authentication Issues**
- Codespaces runs headless by default (no GUI browser)
- Twitter 2FA may not work in headless mode
- **Solution 1**: Disable 2FA on your dedicated Twitter account
- **Solution 2**: Run authentication locally first:
  ```bash
  # On local machine
  python -m app.cli.commands poll  # This will trigger auth
  # Copy data/app.db to Codespaces
  ```
- **Solution 3**: Modify `app/twitter/auth.py` line 26 to force headless mode with:
  ```python
  browser: Browser = p.chromium.launch(headless=True)
  ```

**Port Not Accessible**
- Ensure you're using `--host 0.0.0.0` when running uvicorn
- Check the "Ports" tab in VS Code to see forwarded ports
- Port visibility should be "Public" for external access

**Environment Variables Not Loading**
- Verify `.env` file exists in the workspace root
- Check file encoding is UTF-8
- Restart the Codespace if needed

### General Issues

**Session Expires**
- Delete `data/app.db` to force re-authentication
- Check Twitter account isn't locked

**No Tweets Found**
- Verify tracked accounts have tweeted recently
- Check that your Twitter account follows the targets
- Review logs for HTML parsing errors

**Telegram Not Sending**
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
- Test with: `curl "https://api.telegram.org/bot<TOKEN>/getMe"`

**Gemini API Errors**
- Check `GOOGLE_API_KEY` is valid
- Verify you have API quota remaining
- Review Gemini API [pricing and limits](https://ai.google.dev/pricing)

## 📝 Example Telegram Message

```
🚨 New Tweet from @elonmusk
🔗 View Tweet

📝 Raw Tweet:
Tesla (TSLA) deliveries exceeded expectations in Q4. Strong demand continues.

🤖 AI Summary:
• Tesla Q4 deliveries beat expectations
• Indicates strong ongoing demand
• Positive signal for TSLA stock

📊 Tickers: $TSLA
⚡ Action: WATCH
⏱️ Horizon: weeks
🟢 Confidence: high

⚠️ Risks:
• Need to verify actual delivery numbers
• Macro headwinds could impact demand

✅ Verify:
• Check official Tesla delivery report
• Compare to analyst estimates
```

## 🔧 Configuration

Key settings in `.env`:

- `POLL_INTERVAL_SECONDS`: How often to check (default: 60)
- `LLM_MODEL`: Gemini model to use (default: `gemini-1.5-flash`)
- `LOG_LEVEL`: Logging verbosity (default: `INFO`)

## 📜 License

MIT License - feel free to modify and use as needed.

## 🤝 Contributing

This is an MVP. Contributions welcome for:
- More robust Twitter scraping
- Better ticker extraction
- Enhanced LLM prompts
- Error recovery improvements
- Migration to official Twitter API

---

Built with ❤️ using FastAPI, Playwright, Google Gemini, and Telegram
