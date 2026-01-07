import os
import tempfile
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Schedule, User, WorkerState


class TestDatabase:
    """test database operations"""

    @pytest.fixture
    def test_db(self):
        """create a temporary test database"""
        # create temporary database file
        db_fd, db_path = tempfile.mkstemp()
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        session = Session()

        yield session

        # cleanup
        session.close()
        os.close(db_fd)
        os.unlink(db_path)

    def test_user_creation(self, test_db):
        """test user creation and uniqueness"""
        # create user
        user = User(telegram_id=123456789, username="testuser", first_name="Test", last_name="User")
        test_db.add(user)
        test_db.commit()

        # verify user exists
        found_user = test_db.query(User).filter_by(telegram_id=123456789).first()
        assert found_user is not None
        assert found_user.username == "testuser"

        # test unique constraint
        duplicate_user = User(telegram_id=123456789, username="another")
        test_db.add(duplicate_user)
        with pytest.raises(Exception):  # should raise integrity error
            test_db.commit()

    def test_schedule_creation(self, test_db):
        """test schedule creation with validation"""
        # create user first
        user = User(telegram_id=123456789)
        test_db.add(user)
        test_db.commit()

        # create schedule
        schedule = Schedule(
            user_id=user.id,
            peptide_name="GHK-Cu",
            dosage="1mg",
            frequency="daily",
            cycle_duration_days=42,
            rest_period_days=14,
            start_date=datetime.utcnow(),
        )
        test_db.add(schedule)
        test_db.commit()

        # verify schedule
        found_schedule = test_db.query(Schedule).filter_by(user_id=user.id).first()
        assert found_schedule is not None
        assert found_schedule.peptide_name == "GHK-Cu"
        assert found_schedule.is_active == True

    def test_cascade_deletion(self, test_db):
        """test that deleting user deletes related schedules"""
        # create user with schedule
        user = User(telegram_id=123456789)
        test_db.add(user)
        test_db.commit()

        schedule = Schedule(
            user_id=user.id,
            peptide_name="Test",
            dosage="1mg",
            frequency="daily",
            cycle_duration_days=30,
            rest_period_days=7,
            start_date=datetime.utcnow(),
        )
        test_db.add(schedule)
        test_db.commit()

        # delete user
        test_db.delete(user)
        test_db.commit()

        # verify schedule is also deleted
        remaining_schedules = test_db.query(Schedule).all()
        assert len(remaining_schedules) == 0

    def test_worker_state(self, test_db):
        """test worker state tracking"""
        # create worker state
        state = WorkerState(worker_name="reminder_scheduler", last_run_time=datetime.utcnow())
        test_db.add(state)
        test_db.commit()

        # verify state
        found_state = test_db.query(WorkerState).filter_by(worker_name="reminder_scheduler").first()
        assert found_state is not None
        assert found_state.last_run_time is not None

        # test unique constraint
        duplicate_state = WorkerState(worker_name="reminder_scheduler")
        test_db.add(duplicate_state)
        with pytest.raises(Exception):
            test_db.commit()


class TestDataIntegrity:
    """test data integrity and constraints"""

    def test_required_fields(self):
        """test that required fields are enforced"""
        # user without telegram_id should fail
        with pytest.raises(Exception):
            _user = User(username="test")
            # telegram_id is required

        # schedule without required fields should fail
        with pytest.raises(Exception):
            _schedule = Schedule(peptide_name="Test")
            # missing user_id, dosage, frequency, etc.
