#!/usr/bin/env python3

import logging
import threading
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import TELEGRAM_BOT_TOKEN, logger
from database.operations import init_database, get_or_create_user, create_schedule, get_active_schedules
from parser.schedule_parser import parse_schedule
from bot.scheduler import start_reminder_worker

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
            f"I'll send you daily reminders at 8:00 AM!"
        )
    else:
        await update.message.reply_text(
            "❌ I couldn't understand that schedule format.\n\n"
            "Please try something like:\n"
            "GHK-Cu 1mg daily for 6 weeks\n"
            "BPC-157 500mcg twice weekly for 8 weeks"
        )

def main():
    """start the bot"""
    logger.info("starting Peptide Scheduler Bot...")
    
    # initialize database
    init_database()
    
    # start reminder scheduler in background thread
    reminder_thread = threading.Thread(target=start_reminder_worker, daemon=True)
    reminder_thread.start()
    logger.info("reminder scheduler started in background")
    
    # create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # start the bot
    logger.info("bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
