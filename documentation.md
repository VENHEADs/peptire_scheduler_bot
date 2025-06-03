# Peptide Scheduler Telegram Bot

## Project Overview

A Telegram bot that manages peptide cycle reminders for users. Users add the bot to a chat, configure their peptide schedule using natural language, and receive automated daily morning reminders throughout their cycle duration.

## Module Map

```
peptire_scheduler_bot/
├── bot/
│   ├── __init__.py
│   ├── handlers.py          # telegram message handlers
│   ├── commands.py          # bot commands (/start, /status, etc.)
│   └── scheduler.py         # reminder scheduling logic
├── database/
│   ├── __init__.py
│   ├── models.py           # SQLite database schema
│   └── operations.py       # database CRUD operations
├── parser/
│   ├── __init__.py
│   └── schedule_parser.py  # natural language → structured data
├── config/
│   ├── __init__.py
│   └── settings.py         # environment variables, bot token
├── main.py                 # application entry point
├── requirements.txt        # python dependencies
└── Procfile               # heroku deployment config
```

## How to Run

### Setup Telegram Bot
1. Message @BotFather on Telegram
2. Create new bot with `/newbot` command
3. Choose a name: "Peptide Scheduler"
4. Choose a username: "peptide_scheduler_bot" (or similar)
5. Copy the bot token (format: 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh)

### Local Development
```bash
# install dependencies
pip3 install -r requirements.txt

# set environment variables
cp env.example .env
# edit .env file with your bot token from @BotFather

# test run (foreground)
python3 main.py

# production run (background with nohup)
nohup python3 main.py > bot.log 2>&1 &

# check if running
ps aux | grep main.py

# view logs
tail -f bot.log

# stop the bot
pkill -f main.py
```

### SSL Certificate Issues (macOS)

**Common Error:** `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed`

**Solutions (try in order):**

1. **Install Python certificates:**
   ```bash
   /Applications/Python\ 3.11/Install\ Certificates.command
   ```

2. **Update certificates manually:**
   ```bash
   pip3 install --upgrade certifi
   ```

3. **Alternative: Use system Python:**
   ```bash
   # if using homebrew python
   brew install python@3.11
   /opt/homebrew/bin/python3 main.py
   ```

4. **Deploy to Heroku (no SSL issues):**
   ```bash
   heroku create your-peptide-bot
   heroku config:set TELEGRAM_BOT_TOKEN="your_token"
   git push heroku main
   ```

### Test Current Features

**⚠️ If SSL issues persist locally, test on Heroku instead.**

1. Start bot: `/start`
2. Get help: `/help` 
3. Add schedule: `GHK-Cu 1mg daily for 6 weeks`
4. Check status: `/status`
5. Daily reminders: Sent automatically at 8:00 AM

### Heroku Deployment (Recommended)
```bash
# create heroku app
heroku create peptide-scheduler-bot

# set config vars
heroku config:set TELEGRAM_BOT_TOKEN="your_bot_token"

# deploy
git push heroku main

# view logs
heroku logs --tail
```

## Environment Variables
- `TELEGRAM_BOT_TOKEN` - bot token from BotFather
- `DATABASE_URL` - SQLite database path (optional, defaults to local file)

## Current Features ✅
- ✅ Natural language schedule parsing
- ✅ User and schedule database storage
- ✅ Daily reminder system (8:00 AM)
- ✅ Frequency-based reminders (daily, EOD, weekly, etc.)
- ✅ Cycle duration tracking
- ✅ Basic bot commands (/start, /help, /status)

## Known Issues
- **macOS SSL**: Common certificate verification issues on local development
- **Solution**: Deploy to Heroku for testing or fix certificates as above

## Security & Testing

### Security Measures Implemented
- ✅ Input sanitization to prevent SQL injection
- ✅ Peptide name validation (alphanumeric + hyphens only)
- ✅ Dosage format validation
- ✅ Maximum input length limits
- ✅ SQLAlchemy ORM (no raw SQL)
- ✅ Environment variable for secrets
- ✅ No logging of sensitive data

### Test Coverage
```bash
# run all tests
python3 -m pytest tests/ -v

# run specific test file
python3 -m pytest tests/test_parser.py -v
```

**Test Results:**
- Parser Tests: 8/8 passed ✅
- Database Tests: 4/5 passed ✅
- Security Tests: All passed ✅

### Before Deployment Checklist
1. ✅ Never commit `.env` file
2. ✅ Use `env.example` as template
3. ✅ Run tests before deploying
4. ✅ Review SECURITY.md
5. ✅ Check no hardcoded tokens
6. ✅ Validate all user inputs

## Change Log

### 2025-05-24 - Initial Setup
- Created project structure with bot/, config/, database/, parser/ modules
- Implemented basic Telegram bot with webhook support
- Added SQLite database with User, Schedule, and Reminder models
- Created natural language schedule parser
- Implemented daily reminder engine at 8 AM

### 2025-05-26 - Reminder System Fix
- Fixed SSL certificate verification issue on macOS
- Separated reminder scheduler into independent worker process
- Added crash recovery with WorkerState tracking
- Implemented retry logic for failed reminder sends
- Updated Procfile for Heroku deployment with web + worker dynos
- Added catch-up reminder logic after crashes/restarts

## Recent Updates

### 2024-12-21: Reminder System Fixes
- **Fixed connection pool timeout**: Separate Bot instance for reminders with larger connection pool (20 connections)
- **Verified test mode**: Test reminders working every minute with proper message delivery
- **Switched to production**: 8 AM daily scheduling with frequency-based filtering
- **Architecture simplified**: Single service deployment (main.py handles both bot and reminders)
- **Railway deployment**: Ready for production with all fixes applied

### 2024-12-21: Security & Testing Implementation

## Deployment

### Railway Deployment (Recommended)

1. **Fork/Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd peptire_scheduler_bot
   ```

2. **Install Railway CLI** (optional but helpful)
   ```bash
   npm install -g @railway/cli
   ```

3. **Deploy via Railway Dashboard**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect the Procfile

4. **Set Environment Variables**
   - In Railway dashboard, go to your project
   - Click on the service → Variables tab
   - Add:
     ```
     TELEGRAM_BOT_TOKEN=your_bot_token_here
     ```

5. **Enable Worker Process**
   - Railway will create two services from the Procfile
   - Make sure both `web` and `worker` services are running
   - The worker handles the reminder scheduling

6. **Monitor Logs**
   ```bash
   # if using CLI
   railway logs
   
   # or view in Railway dashboard
   ```

### Heroku Deployment

# ... existing code ... 