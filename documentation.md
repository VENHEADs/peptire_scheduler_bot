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

## Change Log

### Step 1 ✅
- Created documentation.md with project structure and setup instructions

### Step 4 ✅
- Added Telegram bot token configuration and environment setup

### Step 8 ✅
- Added local testing instructions with nohup for background execution
- Implemented daily reminder engine with 8:00 AM notifications
- Added SSL certificate fix instructions for macOS
- Added Heroku deployment as primary testing method 