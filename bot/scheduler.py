import logging
import schedule
import time
import asyncio
from datetime import datetime, timedelta
from database.operations import SessionLocal, get_or_create_user
from database.models import User, Schedule, Reminder
from parser.schedule_parser import parse_frequency_to_days
from telegram import Bot
from config.settings import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

class ReminderScheduler:
    """handles daily reminder notifications"""
    
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    def should_send_reminder_today(self, schedule_obj, today):
        """check if user should get reminder today based on frequency"""
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
        logger.info("processing daily reminders...")
        today = datetime.utcnow().date()
        
        db = SessionLocal()
        try:
            # get all active schedules
            active_schedules = db.query(Schedule).filter(
                Schedule.is_active == True
            ).all()
            
            for schedule_obj in active_schedules:
                # check if reminder needed today
                if not self.should_send_reminder_today(schedule_obj, today):
                    continue
                
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
                
                message = (
                    f"🌅 <b>Good morning!</b>\n\n"
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
            logger.info("daily reminders processing complete")
            
        except Exception as e:
            logger.exception(f"error processing daily reminders: {e}")
            db.rollback()
        finally:
            db.close()

# create scheduler instance
reminder_scheduler = ReminderScheduler()

def run_daily_reminders():
    """sync wrapper for daily reminders"""
    asyncio.run(reminder_scheduler.process_daily_reminders())

def setup_reminder_schedule():
    """setup daily reminder schedule for 8 AM"""
    schedule.clear()
    schedule.every().day.at("08:00").do(run_daily_reminders)
    logger.info("reminder schedule set for 8:00 AM daily")

def start_reminder_worker():
    """start the reminder worker in background"""
    setup_reminder_schedule()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # check every minute 