import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL
from database.models import Base, User, Schedule, Reminder
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# create database engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """create all database tables"""
    Base.metadata.create_all(bind=engine)
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
                   frequency: str, cycle_duration_days: int, 
                   rest_period_days: int, notes: str = None):
    """create a new peptide schedule"""
    db = SessionLocal()
    try:
        schedule = Schedule(
            user_id=user_id,
            peptide_name=peptide_name,
            dosage=dosage,
            frequency=frequency,
            cycle_duration_days=cycle_duration_days,
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