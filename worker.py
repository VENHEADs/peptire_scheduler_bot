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
from bot.scheduler import reminder_scheduler
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
    """main worker loop with 1-minute testing schedule"""
    logger.info("starting TEST reminder worker process - sending reminders every minute...")
    
    # initialize database
    init_database()
    
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
            
        except KeyboardInterrupt:
            logger.info("worker stopped by user")
            break
        except Exception as e:
            logger.exception(f"unexpected error in worker loop: {e}")
            # sleep 1 minute on error in test mode
            time.sleep(60)

if __name__ == '__main__':
    main() 