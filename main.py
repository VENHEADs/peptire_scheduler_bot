#!/usr/bin/env python3

import logging
import threading
import os
import ssl
import certifi
import time
import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from config.settings import get_bot_token, logger
from database.operations import init_database, get_or_create_user, create_schedule, get_active_schedules, SessionLocal
from database.models import User, Schedule, WorkerState
from parser.schedule_parser import parse_schedule
from bot.scheduler import reminder_scheduler, calculate_seconds_until_next_8am

# configure SSL for macOS
if os.name == 'posix' and os.uname().sysname == 'Darwin':
    ssl._create_default_https_context = ssl._create_unverified_context

def update_last_run_time():
    """update the last successful reminder run time"""
    logger.info("starting update_last_run_time")
    db = SessionLocal()
    try:
        logger.info("querying for existing worker state")
        state = db.query(WorkerState).filter(WorkerState.worker_name == "reminder_scheduler").first()
        if not state:
            logger.info("creating new worker state record")
            state = WorkerState(worker_name="reminder_scheduler")
            db.add(state)
        else:
            logger.info("updating existing worker state record")
        
        state.last_run_time = datetime.utcnow()
        logger.info("committing worker state to database")
        db.commit()
        logger.info("successfully updated last run time")
    except Exception as e:
        logger.exception(f"failed to update last run time: {e}")
        db.rollback()
        raise  # re-raise to see if this is causing the issue
    finally:
        logger.info("closing database connection")
        db.close()

async def run_reminder_with_retry(max_retries=3):
    """run reminder with retry logic"""
    logger.info(f"starting run_reminder_with_retry with max_retries={max_retries}")
    
    for attempt in range(max_retries):
        try:
            logger.info(f"reminder attempt {attempt + 1}/{max_retries}")
            await reminder_scheduler.process_daily_reminders()
            logger.info(f"reminder attempt {attempt + 1} succeeded")
            update_last_run_time()
            logger.info("successfully updated last run time")
            return True
        except Exception as e:
            logger.exception(f"reminder attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                sleep_time = 60 * (attempt + 1)
                logger.info(f"sleeping {sleep_time} seconds before retry...")
                await asyncio.sleep(sleep_time)  # exponential backoff
            else:
                logger.error(f"all {max_retries} attempts failed")
    return False

def reminder_worker():
    """reminder worker function that runs in background thread"""
    logger.info("starting optimized reminder worker - 8 AM daily scheduling...")
    
    # run first reminder immediately
    logger.info("running initial reminder check...")
    try:
        asyncio.run(run_reminder_with_retry())
        logger.info("initial reminder check completed successfully")
    except Exception as e:
        logger.exception(f"initial reminder check failed: {e}")
    
    iteration = 0
    while True:
        try:
            iteration += 1
            logger.info(f"starting reminder iteration #{iteration}")
            
            # PRODUCTION MODE: calculate sleep time until next 8 AM
            sleep_seconds, next_8am = calculate_seconds_until_next_8am()
            logger.info(f"sleeping {sleep_seconds/3600:.1f} hours until next reminder: {next_8am}")
            time.sleep(sleep_seconds)
            
            logger.info(f"woke up at 8 AM, starting reminder iteration #{iteration}")
            
            # execute daily reminders with retry
            logger.info("calling run_reminder_with_retry()...")
            success = asyncio.run(run_reminder_with_retry())
            
            if not success:
                logger.error("failed to send reminders after all retries")
            else:
                logger.info("reminder check completed successfully")
                
            logger.info(f"completed reminder iteration #{iteration}, continuing loop...")
            
            # small buffer to avoid immediate re-execution
            time.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("reminder worker stopped by keyboard interrupt")
            break
        except Exception as e:
            logger.exception(f"unexpected error in reminder worker iteration #{iteration}: {e}")
            logger.info("continuing after error...")
            # sleep 1 hour on error in production mode
            time.sleep(3600)
    
    logger.error("reminder worker exited main loop - this should not happen!")

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
        "/status - Check your current schedule\n"
        "/clear - Stop schedules with buttons\n\n"
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
    
    today = datetime.utcnow().date()
    response = "📊 Your active schedules:\n\n"
    
    for schedule in schedules:
        days_since_start = (today - schedule.start_date.date()).days
        days_remaining = schedule.cycle_duration_days - days_since_start
        rest_end_date = schedule.start_date.date() + timedelta(days=schedule.cycle_duration_days + schedule.rest_period_days)
        
        response += f"💊 <b>{schedule.peptide_name}</b>\n"
        response += f"   📏 Dosage: {schedule.dosage}\n"
        response += f"   ⏰ Frequency: {schedule.frequency}\n"
        response += f"   📅 Days remaining: {max(0, days_remaining)}\n"
        response += f"   😴 Rest period: {schedule.rest_period_days} days\n"
        response += f"   🔄 Can restart: {rest_end_date.strftime('%b %d, %Y')}\n\n"
    
    await update.message.reply_text(response, parse_mode='HTML')

async def stop_command(update, context):
    """handle /stop command - deactivate specific schedule"""
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify the peptide name.\n"
            "Example: /stop GHK-Cu"
        )
        return
    
    peptide_name = ' '.join(context.args)
    
    db = SessionLocal()
    try:
        # find user
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user:
            await update.message.reply_text("❌ User not found.")
            return
        
        # find matching active schedule
        schedule = db.query(Schedule).filter(
            Schedule.user_id == user.id,
            Schedule.peptide_name.ilike(f"%{peptide_name}%"),
            Schedule.is_active == True
        ).first()
        
        if not schedule:
            await update.message.reply_text(
                f"❌ No active schedule found for '{peptide_name}'.\n"
                "Use /status to see your active schedules."
            )
            return
        
        # deactivate schedule
        schedule.is_active = False
        schedule.completed_at = datetime.utcnow()
        db.commit()
        
        await update.message.reply_text(
            f"✅ Stopped schedule for <b>{schedule.peptide_name}</b>\n"
            f"You will no longer receive reminders for this peptide.",
            parse_mode='HTML'
        )
        logger.info(f"user {user.telegram_id} stopped schedule {schedule.id}")
        
    finally:
        db.close()

async def stopall_command(update, context):
    """handle /stopall command - deactivate all schedules"""
    db = SessionLocal()
    try:
        # find user
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user:
            await update.message.reply_text("❌ User not found.")
            return
        
        # find all active schedules
        active_schedules = db.query(Schedule).filter(
            Schedule.user_id == user.id,
            Schedule.is_active == True
        ).all()
        
        if not active_schedules:
            await update.message.reply_text("You have no active schedules to stop.")
            return
        
        # deactivate all schedules
        count = 0
        for schedule in active_schedules:
            schedule.is_active = False
            schedule.completed_at = datetime.utcnow()
            count += 1
        
        db.commit()
        
        await update.message.reply_text(
            f"✅ Stopped all {count} active schedule(s).\n"
            f"You will no longer receive reminders."
        )
        logger.info(f"user {user.telegram_id} stopped all {count} schedules")
        
    finally:
        db.close()

async def clear_command(update, context):
    """handle /clear command - show schedules with inline delete buttons"""
    schedules = get_active_schedules(update.effective_user.id)
    
    if not schedules:
        await update.message.reply_text("You have no active schedules to clear.")
        return
    
    today = datetime.utcnow().date()
    keyboard = []
    
    for schedule in schedules:
        days_remaining = schedule.cycle_duration_days - (today - schedule.start_date.date()).days
        button_text = f"❌ {schedule.peptide_name} ({max(0, days_remaining)}d left)"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"clear:{schedule.id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🗑️ <b>Select a schedule to stop:</b>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_clear_callback(update, context):
    """handle inline button callbacks for clearing schedules"""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("clear:"):
        return
    
    schedule_id = int(query.data.split(":")[1])
    
    db = SessionLocal()
    try:
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        
        if not schedule:
            await query.edit_message_text("❌ Schedule not found.")
            return
        
        # verify ownership
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user or schedule.user_id != user.id:
            await query.edit_message_text("❌ Unauthorized.")
            return
        
        peptide_name = schedule.peptide_name
        schedule.is_active = False
        schedule.completed_at = datetime.utcnow()
        db.commit()
        
        await query.edit_message_text(
            f"✅ Stopped <b>{peptide_name}</b>\n"
            f"Use /clear to manage remaining schedules.",
            parse_mode='HTML'
        )
        logger.info(f"user {user.telegram_id} cleared schedule {schedule_id} via button")
        
    finally:
        db.close()

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
            f"🌅 I'll send you daily reminders at 8:00 AM!"
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
    logger.info("starting Peptide Scheduler Bot with embedded reminder worker (production mode)...")
    
    # initialize database
    init_database()
    
    # start reminder scheduler in background thread
    reminder_thread = threading.Thread(target=reminder_worker, daemon=True)
    reminder_thread.start()
    logger.info("embedded reminder worker started in background thread")
    
    # create application
    application = Application.builder().token(get_bot_token()).build()
    
    # add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("stopall", stopall_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CallbackQueryHandler(handle_clear_callback, pattern="^clear:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # check if running in production with webhook
    webhook_url = os.getenv('WEBHOOK_URL')
    port = int(os.getenv('PORT', 8443))
    
    if webhook_url:
        # production mode with webhooks
        logger.info(f"starting bot with webhook: {webhook_url}")
        bot_token = get_bot_token()
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=bot_token,
            webhook_url=f"{webhook_url}/{bot_token}"
        )
    else:
        # development mode with polling
        logger.info("bot is running in polling mode...")
        application.run_polling()

if __name__ == '__main__':
    main()
