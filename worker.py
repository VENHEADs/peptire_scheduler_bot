#!/usr/bin/env python3
"""
Reminder worker process - runs independently from the main bot
"""

import logging
import time
import asyncio
import os
import ssl
import certifi
from datetime import datetime, timedelta
from bot.scheduler import reminder_scheduler, calculate_seconds_until_next_8am
from database.operations import init_database, SessionLocal
from database.models import WorkerState
from config.settings import logger

# configure SSL for macOS
if os.name == 'posix' and os.uname().sysname == 'Darwin':
    ssl._create_default_https_context = ssl._create_unverified_context

def get_last_run_time():
    """get the last successful reminder run time from database"""
    db = SessionLocal()
    try:
        state = db.query(WorkerState).filter(WorkerState.worker_name == "reminder_scheduler").first()
        if state:
            return state.last_run_time
        return None
    finally:
        db.close()

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

def should_run_catch_up_reminders():
    """check if we need to run catch-up reminders after a crash/restart"""
    last_run = get_last_run_time()
    if not last_run:
        return True  # first run
    
    # if last run was more than 24 hours ago, we missed reminders
    hours_since_last_run = (datetime.utcnow() - last_run).total_seconds() / 3600
    return hours_since_last_run > 24

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

def main():
    """main worker loop with crash recovery"""
    logger.info("starting reminder worker process...")
    
    # initialize database
    init_database()
    
    # check if we need to run catch-up reminders
    if should_run_catch_up_reminders():
        logger.info("running catch-up reminders after restart...")
        asyncio.run(run_reminder_with_retry())
    
    while True:
        try:
            # calculate sleep time until next 8 AM
            sleep_seconds, next_8am = calculate_seconds_until_next_8am()
            
            logger.info(f"sleeping {sleep_seconds/3600:.1f} hours until next reminder: {next_8am}")
            time.sleep(sleep_seconds)
            
            # execute daily reminders with retry
            logger.info("waking up to send daily reminders...")
            success = asyncio.run(run_reminder_with_retry())
            
            if not success:
                logger.error("failed to send reminders after all retries")
            
            # small buffer to avoid immediate re-execution
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("worker stopped by user")
            break
        except Exception as e:
            logger.exception(f"unexpected error in worker loop: {e}")
            # sleep 5 minutes on unexpected error
            time.sleep(300)

if __name__ == '__main__':
    main() 