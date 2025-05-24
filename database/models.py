from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """telegram user model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # relationship to schedules
    schedules = relationship("Schedule", back_populates="user", cascade="all, delete-orphan")

class Schedule(Base):
    """peptide schedule model"""
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # peptide info
    peptide_name = Column(String(100), nullable=False)
    dosage = Column(String(50), nullable=False)
    frequency = Column(String(100), nullable=False)  # "daily", "twice weekly", etc.
    
    # cycle info
    cycle_duration_days = Column(Integer, nullable=False)
    rest_period_days = Column(Integer, nullable=False)
    
    # tracking
    start_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # relationships
    user = relationship("User", back_populates="schedules")
    reminders = relationship("Reminder", back_populates="schedule", cascade="all, delete-orphan")

class Reminder(Base):
    """daily reminder tracking"""
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('schedules.id'), nullable=False)
    
    reminder_date = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # relationships
    schedule = relationship("Schedule", back_populates="reminders") 