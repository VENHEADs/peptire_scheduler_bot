# Peptide Scheduler Telegram Bot

A Telegram bot that manages peptide cycle reminders with natural language parsing.

## Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/peptide-scheduler-bot)

## Manual Setup

See [documentation.md](documentation.md) for detailed setup instructions.

## Environment Variables Required

- `TELEGRAM_BOT_TOKEN` - Get from @BotFather on Telegram

## Features

- Natural language schedule parsing ("GHK-Cu 1mg daily for 6 weeks")
- Daily 8:00 AM reminders
- Cycle duration tracking
- SQLite database storage 