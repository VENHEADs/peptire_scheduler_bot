#!/usr/bin/env python3

import logging
import threading
import os
import ssl
import certifi
import time
import asyncio
from datetime import datetime
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import TELEGRAM_BOT_TOKEN, logger
from database.operations import init_database, get_or_create_user, create_schedule, get_active_schedules, SessionLocal
from database.models import WorkerState
from parser.schedule_parser import parse_schedule
from bot.scheduler import reminder_scheduler

# configure SSL for macOS
if os.name == 'posix' and os.uname().sysname == 'Darwin':
    ssl._create_default_https_context = ssl._create_unverified_context

def update_last_run_time():
    """update the last successful reminder run time"""
    db = SessionLocal()
    try:
        state = db.query(WorkerState).filter(WorkerState.worker_name == "reminder_scheduler").first()
        if not state:
            state = WorkerState(worker_name="reminder_scheduler")
            db.add(state)
        
        state.last_run_time = datetime.utcnow()
        db.commit()
        logger.info("updated last run time")
    except Exception as e:
        logger.exception(f"failed to update last run time: {e}")
        db.rollback()
    finally:
        db.close()

async def run_reminder_with_retry(max_retries=3):
    """run reminder with retry logic"""
    for attempt in range(max_retries):
        try:
            await reminder_scheduler.process_daily_reminders()
            update_last_run_time()
            return True
        except Exception as e:
            logger.exception(f"reminder attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(60 * (attempt + 1))  # exponential backoff
    return False

def reminder_worker():
    """reminder worker function that runs in background thread"""
    logger.info("starting embedded TEST reminder worker - sending reminders every minute...")
    
    # run first reminder immediately
    logger.info("running initial reminder check...")
    asyncio.run(run_reminder_with_retry())
    
    while True:
        try:
            # TEST MODE: wait 1 minute instead of until 8 AM
            logger.info("sleeping 1 minute until next reminder check...")
            time.sleep(60)  # 1 minute
            
            # execute daily reminders with retry
            logger.info("waking up to send reminders...")
            success = asyncio.run(run_reminder_with_retry())
            
            if not success:
                logger.error("failed to send reminders after all retries")
            else:
                logger.info("reminder check completed successfully")
                
        except Exception as e:
            logger.exception(f"unexpected error in reminder worker: {e}")
            # sleep 1 minute on error in test mode
            time.sleep(60)

async def start(update, context):
    """handle /start command"""
    # create user in database
    user = get_or_create_user(
        telegram_id=update.effective_user.id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name
    )
    
    await update.message.reply_text(
        "Welcome to Peptide Scheduler Bot! 🧬\n\n"
        "Send me your peptide schedule and I'll remind you when to take them.\n"
        "Use /help for more information."
    )

async def help_command(update, context):
    """handle /help command"""
    await update.message.reply_text(
        "📋 Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/status - Check your current schedule\n\n"
        "💊 To add a schedule, just send me text like:\n"
        "GHK-Cu 1mg daily for 6 weeks\n"
        "BPC-157 500mcg twice weekly for 8 weeks"
    )

async def status_command(update, context):
    """handle /status command"""
    schedules = get_active_schedules(update.effective_user.id)
    
    if not schedules:
        await update.message.reply_text("You have no active schedules.")
        return
    
    response = "📊 Your active schedules:\n\n"
    for schedule in schedules:
        response += f"💊 {schedule.peptide_name}\n"
        response += f"   Dosage: {schedule.dosage}\n"
        response += f"   Frequency: {schedule.frequency}\n"
        response += f"   Duration: {schedule.cycle_duration_days} days\n\n"
    
    await update.message.reply_text(response)

async def handle_message(update, context):
    """handle all text messages"""
    message_text = update.message.text
    logger.info(f"received message: {message_text}")
    
    # try to parse as schedule
    parsed = parse_schedule(message_text)
    
    if parsed:
        # get or create user
        user = get_or_create_user(
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name
        )
        
        # create schedule
        schedule = create_schedule(
            user_id=user.id,
            peptide_name=parsed.peptide_name,
            dosage=parsed.dosage,
            frequency=parsed.frequency,
            cycle_duration_days=parsed.cycle_duration_days,
            rest_period_days=parsed.rest_period_days,
            notes=parsed.notes
        )
        
        await update.message.reply_text(
            f"✅ Schedule created!\n\n"
            f"💊 Peptide: {parsed.peptide_name}\n"
            f"📏 Dosage: {parsed.dosage}\n"
            f"⏰ Frequency: {parsed.frequency}\n"
            f"📅 Cycle: {parsed.cycle_duration_days} days\n"
            f"😴 Rest: {parsed.rest_period_days} days\n\n"
            f"🧪 TEST MODE: I'll send you reminders every minute for testing!"
        )
    else:
        await update.message.reply_text(
            "❌ I couldn't understand that schedule format.\n\n"
            "Please try something like:\n"
            "GHK-Cu 1mg daily for 6 weeks\n"
            "BPC-157 500mcg twice weekly for 8 weeks"
        )

def main():
    """start the bot with embedded reminder worker"""
    logger.info("starting Peptide Scheduler Bot with embedded reminder worker...")
    
    # initialize database
    init_database()
    
    # start reminder scheduler in background thread
    reminder_thread = threading.Thread(target=reminder_worker, daemon=True)
    reminder_thread.start()
    logger.info("embedded reminder worker started in background thread")
    
    # create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # check if running in production with webhook
    webhook_url = os.getenv('WEBHOOK_URL')
    port = int(os.getenv('PORT', 8443))
    
    if webhook_url:
        # production mode with webhooks
        logger.info(f"starting bot with webhook: {webhook_url}")
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TELEGRAM_BOT_TOKEN,
            webhook_url=f"{webhook_url}/{TELEGRAM_BOT_TOKEN}"
        )
    else:
        # development mode with polling
        logger.info("bot is running in polling mode...")
        application.run_polling()

if __name__ == '__main__':
    main()
