from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """telegram user model"""

    __tablename__ = "users"

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

    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # peptide info
    peptide_name = Column(String(100), nullable=False)
    dosage = Column(String(50), nullable=False)
    frequency = Column(String(100), nullable=True)  # legacy field
    days_of_week = Column(String(20), nullable=True)  # "1,2,3,4,5,6,7" or "1,3,5" etc.

    # cycle info
    cycle_duration_days = Column(Integer, nullable=False)
    rest_period_days = Column(Integer, nullable=False)

    # tracking
    start_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    user = relationship("User", back_populates="schedules")
    reminders = relationship("Reminder", back_populates="schedule", cascade="all, delete-orphan")


class Reminder(Base):
    """daily reminder tracking"""

    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)

    reminder_date = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    schedule = relationship("Schedule", back_populates="reminders")

    def __repr__(self):
        return f"<Reminder(schedule_id={self.schedule_id}, date={self.reminder_date})>"


class WorkerState(Base):
    """track worker process state for crash recovery"""

    __tablename__ = "worker_states"

    id = Column(Integer, primary_key=True)
    worker_name = Column(String(100), unique=True, nullable=False)
    last_run_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<WorkerState(name={self.worker_name}, last_run={self.last_run_time})>"
