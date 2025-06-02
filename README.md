# Peptide Scheduler Telegram Bot

A Telegram bot that manages peptide cycle reminders with natural language parsing.

## 📝 Schedule Format

Send your peptide schedule in natural language:
```
[Peptide Name] [Dosage] [Frequency] for [Duration]
```

### Examples:
- `GHK-Cu 1.5mg daily for 5 weeks`
- `Thymosin 1.2mg twice weekly for 10 weeks`
- `BPC-157 500mcg daily for 7 weeks`
- `TB-500 2mg weekly for 10 weeks`

See [schedule_example.md](schedule_example.md) for more formats.

## 🚀 Deployment

### Railway (Recommended)
1. Fork this repository
2. Go to [railway.app](https://railway.app)
3. Create new project → Deploy from GitHub
4. Add environment variable: `TELEGRAM_BOT_TOKEN`
5. Both web and worker services will start automatically

### Local Development
```bash
# Install dependencies
pip3 install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your bot token

# Run tests
python3 -m pytest tests/ -v

# Start bot (will fail on macOS due to SSL)
python3 main.py
```

## 🔒 Security

- All inputs sanitized and validated
- No SQL injection vulnerabilities
- Environment-based configuration
- See [SECURITY.md](SECURITY.md) for details

## ✅ Tested Examples

All these formats are tested and working:
- ✅ Decimal dosages (1.5mg, 2.5mg)
- ✅ Multiple units (mg, mcg, iu)
- ✅ Various frequencies (daily, weekly, EOD)
- ✅ Different durations (days, weeks, months)

## Features

- Natural language schedule parsing ("GHK-Cu 1mg daily for 6 weeks")
- Daily 8:00 AM reminders
- Cycle duration tracking
- SQLite database storage 