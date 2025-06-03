import logging
import time
import asyncio
import os
import ssl
from datetime import datetime, timedelta
from database.operations import SessionLocal, get_or_create_user
from database.models import User, Schedule, Reminder
from parser.schedule_parser import parse_frequency_to_days
from telegram import Bot
from config.settings import TELEGRAM_BOT_TOKEN

# configure SSL for macOS
if os.name == 'posix' and os.uname().sysname == 'Darwin':
    ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)

class ReminderScheduler:
    """handles daily reminder notifications"""
    
    def __init__(self, test_mode=False):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.test_mode = test_mode
    
    def should_send_reminder_today(self, schedule_obj, today):
        """check if user should get reminder today based on frequency"""
        # TEST MODE: always send reminders
        if self.test_mode:
            return True
            
        days_since_start = (today - schedule_obj.start_date.date()).days
        frequency_days = parse_frequency_to_days(schedule_obj.frequency)
        
        # check if cycle is still active
        if days_since_start >= schedule_obj.cycle_duration_days:
            return False
            
        # check if today matches frequency pattern
        return days_since_start % frequency_days == 0
    
    async def send_reminder(self, user_telegram_id, message):
        """send reminder message to user"""
        try:
            await self.bot.send_message(
                chat_id=user_telegram_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info(f"sent reminder to user {user_telegram_id}")
            return True
        except Exception as e:
            logger.exception(f"failed to send reminder to {user_telegram_id}: {e}")
            return False
    
    async def process_daily_reminders(self):
        """process all users and send daily reminders"""
        if self.test_mode:
            logger.info("processing TEST reminders (every minute)...")
        else:
            logger.info("processing daily reminders...")
            
        today = datetime.utcnow().date()
        
        db = SessionLocal()
        try:
            # get all active schedules
            active_schedules = db.query(Schedule).filter(
                Schedule.is_active == True
            ).all()
            
            if not active_schedules:
                logger.info("no active schedules found")
                return
            
            for schedule_obj in active_schedules:
                # check if reminder needed today
                if not self.should_send_reminder_today(schedule_obj, today):
                    continue
                
                # in test mode, don't check if already sent today
                if not self.test_mode:
                    # check if reminder already sent today
                    existing_reminder = db.query(Reminder).filter(
                        Reminder.schedule_id == schedule_obj.id,
                        Reminder.reminder_date >= datetime.combine(today, datetime.min.time()),
                        Reminder.is_sent == True
                    ).first()
                    
                    if existing_reminder:
                        continue  # already sent today
                
                # get user info
                user = db.query(User).filter(User.id == schedule_obj.user_id).first()
                if not user:
                    continue
                
                # create reminder message
                days_remaining = schedule_obj.cycle_duration_days - (today - schedule_obj.start_date.date()).days
                
                test_prefix = "🧪 TEST REMINDER - " if self.test_mode else ""
                message = (
                    f"{test_prefix}🌅 <b>Good morning!</b>\n\n"
                    f"💊 Today you need to take: <b>{schedule_obj.peptide_name}</b>\n"
                    f"📏 Dosage: <b>{schedule_obj.dosage}</b>\n"
                    f"📅 Days remaining in cycle: <b>{days_remaining}</b>\n\n"
                    f"Have a great day! 🧬"
                )
                
                # send reminder
                success = await self.send_reminder(user.telegram_id, message)
                
                # create reminder record
                reminder = Reminder(
                    schedule_id=schedule_obj.id,
                    reminder_date=datetime.utcnow(),
                    is_sent=success
                )
                if success:
                    reminder.sent_at = datetime.utcnow()
                
                db.add(reminder)
                
            db.commit()
            
            if self.test_mode:
                logger.info("TEST reminders processing complete")
            else:
                logger.info("daily reminders processing complete")
            
        except Exception as e:
            logger.exception(f"error processing reminders: {e}")
            db.rollback()
        finally:
            db.close()

# create scheduler instance with test mode
reminder_scheduler = ReminderScheduler(test_mode=True)

def run_daily_reminders():
    """sync wrapper for daily reminders"""
    asyncio.run(reminder_scheduler.process_daily_reminders())

def calculate_seconds_until_next_8am():
    """calculate seconds to sleep until next 8:00 AM"""
    now = datetime.now()
    next_8am = now.replace(hour=8, minute=0, second=0, microsecond=0)
    
    # if past 8 AM today, schedule for tomorrow
    if now.hour >= 8:
        next_8am += timedelta(days=1)
    
    sleep_seconds = (next_8am - now).total_seconds()
    return sleep_seconds, next_8am

def start_reminder_worker():
    """optimized reminder worker - sleeps until needed"""
    logger.info("starting optimized reminder scheduler...")
    
    while True:
        try:
            # calculate sleep time until next 8 AM
            sleep_seconds, next_8am = calculate_seconds_until_next_8am()
            
            logger.info(f"sleeping {sleep_seconds/3600:.1f} hours until next reminder: {next_8am}")
            time.sleep(sleep_seconds)
            
            # execute daily reminders
            logger.info("waking up to send daily reminders...")
            run_daily_reminders()
            
            # small buffer to avoid immediate re-execution
            time.sleep(60)
            
        except Exception as e:
            logger.exception(f"error in reminder worker: {e}")
            # fallback: sleep 1 hour on error
            time.sleep(3600) 