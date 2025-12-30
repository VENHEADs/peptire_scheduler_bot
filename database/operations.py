import logging
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config.settings import DATABASE_URL
from database.models import Base, User, Schedule, Reminder

logger = logging.getLogger(__name__)

# create database engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def _frequency_to_days(frequency: str) -> str:
    """convert legacy frequency string to days_of_week format"""
    freq = frequency.lower().strip()
    if "daily" in freq or "every day" in freq:
        return "1,2,3,4,5,6,7"
    elif "twice weekly" in freq or "2x weekly" in freq:
        return "1,4"  # mon, thu
    elif "3x weekly" in freq or "three times weekly" in freq:
        return "1,3,5"  # mon, wed, fri
    elif "every other day" in freq or "eod" in freq:
        return "1,3,5,7"  # approximate
    elif "weekly" in freq or "once weekly" in freq:
        return "1"  # monday only
    return "1,2,3,4,5,6,7"  # default to daily

def _migrate_legacy_schedules():
    """migrate schedules with frequency to days_of_week"""
    db = SessionLocal()
    try:
        schedules = db.query(Schedule).filter(
            Schedule.days_of_week.is_(None),
            Schedule.frequency.isnot(None)
        ).all()
        
        for schedule in schedules:
            schedule.days_of_week = _frequency_to_days(schedule.frequency)
            logger.info(f"migrated schedule {schedule.id}: {schedule.frequency} -> {schedule.days_of_week}")
        
        if schedules:
            db.commit()
            logger.info(f"migrated {len(schedules)} legacy schedules")
    finally:
        db.close()

def _add_column_if_missing():
    """add days_of_week column if it doesn't exist (SQLite migration)"""
    with engine.connect() as conn:
        try:
            conn.execute(text("SELECT days_of_week FROM schedules LIMIT 1"))
        except Exception:
            conn.execute(text("ALTER TABLE schedules ADD COLUMN days_of_week VARCHAR(20)"))
            conn.commit()
            logger.info("added days_of_week column to schedules table")

def init_database():
    """create all database tables and run migrations"""
    Base.metadata.create_all(bind=engine)
    _add_column_if_missing()
    _migrate_legacy_schedules()
    logger.info("database initialized")

def get_db():
    """get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_or_create_user(telegram_id: int, username: str = None, 
                      first_name: str = None, last_name: str = None):
    """get existing user or create new one"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"created new user: {telegram_id}")
        return user
    finally:
        db.close()

def create_schedule(user_id: int, peptide_name: str, dosage: str, 
                   days_of_week: str, cycle_duration_weeks: int, 
                   rest_period_days: int, notes: str | None = None):
    """create a new peptide schedule"""
    db = SessionLocal()
    try:
        schedule = Schedule(
            user_id=user_id,
            peptide_name=peptide_name,
            dosage=dosage,
            days_of_week=days_of_week,
            cycle_duration_days=cycle_duration_weeks * 7,
            rest_period_days=rest_period_days,
            start_date=datetime.utcnow(),
            notes=notes
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        logger.info(f"created schedule for user {user_id}: {peptide_name}")
        return schedule
    finally:
        db.close()

def get_active_schedules(telegram_id: int):
    """get all active schedules for a user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            return []
        
        schedules = db.query(Schedule).filter(
            Schedule.user_id == user.id,
            Schedule.is_active == True
        ).all()
        return schedules
    finally:
        db.close() 