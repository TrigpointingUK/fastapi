"""
Tests for CRUD operations focusing on functions with low coverage.
"""

from datetime import date, time

from sqlalchemy.orm import Session

from api.crud.tlog import (
    create_log,
    delete_log_hard,
    get_log_by_id,
    list_logs_filtered,
    soft_delete_photos_for_log,
    update_log,
)
from api.crud.trig import (
    get_trig_by_id,
    get_trig_by_waypoint,
    get_trigs_by_county,
    get_trigs_count,
    search_trigs_by_name,
)
from api.crud.user import (
    authenticate_user,
    get_user_by_auth0_id,
    get_user_by_email,
    get_user_by_id,
    get_user_by_name,
    is_admin,
)
from api.models.trig import Trig
from api.models.user import TLog, User


class TestTLogCRUD:
    """Test cases for TLog CRUD operations."""

    def test_list_logs_filtered_by_user(self, db: Session):
        """Test filtering logs by user ID."""
        # Create test user and logs
        user = User(id=1001, name="testuser", email="test@example.com")
        log1 = TLog(id=2001, user_id=1001, trig_id=1, date_=date.today())
        log2 = TLog(id=2002, user_id=1001, trig_id=2, date_=date.today())
        log3 = TLog(
            id=2003, user_id=1002, trig_id=1, date_=date.today()
        )  # Different user

        db.add_all([user, log1, log2, log3])
        db.commit()

        # Test the function
        user_logs = list_logs_filtered(db, user_id=1001)
        assert len(user_logs) == 2
        assert all(log.user_id == 1001 for log in user_logs)

    def test_list_logs_filtered_no_logs(self, db: Session):
        """Test filtering logs for user with no logs."""
        user_logs = list_logs_filtered(db, user_id=9999)
        assert len(user_logs) == 0

    def test_list_logs_filtered_by_trig(self, db: Session):
        """Test filtering logs by trig ID."""
        # Create test logs for same trig
        log1 = TLog(id=2004, user_id=1001, trig_id=5, date_=date.today())
        log2 = TLog(id=2005, user_id=1002, trig_id=5, date_=date.today())
        log3 = TLog(
            id=2006, user_id=1001, trig_id=6, date_=date.today()
        )  # Different trig

        db.add_all([log1, log2, log3])
        db.commit()

        trig_logs = list_logs_filtered(db, trig_id=5)
        assert len(trig_logs) == 2
        assert all(log.trig_id == 5 for log in trig_logs)

    def test_get_log_by_id(self, db: Session):
        """Test getting log by ID."""
        log = TLog(id=2007, user_id=1001, trig_id=1, date=date.today())
        db.add(log)
        db.commit()

        retrieved = get_log_by_id(db, log_id=2007)
        assert retrieved is not None
        assert retrieved.id == 2007

        # Test non-existent log
        not_found = get_log_by_id(db, log_id=9999)
        assert not_found is None

    def test_create_log(self, db: Session):
        """Test creating a new log."""
        log_data = {
            "user_id": 1001,
            "trig_id": 1,
            "date": date.today(),
            "time": time(12, 0),
            "osgb_eastings": 500000,
            "osgb_northings": 200000,
            "osgb_gridref": "TQ 50000 20000",
            "condition": "G",
            "comment": "Test log",
            "score": 10,
            "ip_addr": "127.0.0.1",
            "source": "W",
        }

        new_log = create_log(db, **log_data)

        assert new_log is not None
        assert new_log.user_id == 1001
        assert new_log.trig_id == 1
        assert new_log.condition == "G"
        assert new_log.comment == "Test log"

        # Verify it's in database
        db.refresh(new_log)
        assert new_log.id is not None

    def test_update_log(self, db: Session):
        """Test updating an existing log."""
        log = TLog(
            id=2008,
            user_id=1001,
            trig_id=1,
            date=date.today(),
            condition="F",
            comment="Original comment",
        )
        db.add(log)
        db.commit()

        updates = {"condition": "E", "comment": "Updated comment"}
        updated = update_log(db, log_id=2008, updates=updates)

        assert updated is not None
        assert updated.condition == "E"
        assert updated.comment == "Updated comment"

        # Test updating non-existent log
        not_updated = update_log(db, log_id=9999, updates=updates)
        assert not_updated is None

    def test_delete_log(self, db: Session):
        """Test deleting a log."""
        log = TLog(id=2009, user_id=1001, trig_id=1, date=date.today())
        db.add(log)
        db.commit()

        # Hard delete (soft delete not available in current API)
        result = delete_log_hard(db, log_id=2009)
        assert result is True

        # Test deleting non-existent log
        result = delete_log_hard(db, log_id=9999)
        assert result is False

    def test_soft_delete_photos_for_log(self, db: Session):
        """Test soft deleting photos for a log."""
        from api.models.tphoto import TPhoto

        # Create log and photos
        log = TLog(id=2010, user_id=1001, trig_id=1, date=date.today())
        photo1 = TPhoto(id=3001, tlog_id=2010, filename="test1.jpg", deleted_ind="N")
        photo2 = TPhoto(id=3002, tlog_id=2010, filename="test2.jpg", deleted_ind="N")

        db.add_all([log, photo1, photo2])
        db.commit()

        # Soft delete photos for log
        deleted_count = soft_delete_photos_for_log(db, log_id=2010)
        assert deleted_count == 2

        # Verify photos were soft deleted
        db.refresh(photo1)
        db.refresh(photo2)
        assert photo1.deleted_ind == "Y"
        assert photo2.deleted_ind == "Y"

        # Test with log that has no photos
        deleted_count = soft_delete_photos_for_log(db, log_id=9999)
        assert deleted_count == 0


class TestTrigCRUD:
    """Test cases for Trig CRUD operations."""

    def test_get_trig_by_id(self, db: Session):
        """Test getting trig by ID."""
        trig = Trig(id=1, name="Test Trig", county="Testshire")
        db.add(trig)
        db.commit()

        retrieved = get_trig_by_id(db, trig_id=1)
        assert retrieved is not None
        assert retrieved.name == "Test Trig"

        # Test non-existent trig
        not_found = get_trig_by_id(db, trig_id=9999)
        assert not_found is None

    def test_get_trig_by_waypoint(self, db: Session):
        """Test getting trig by waypoint."""
        trig = Trig(id=2, name="Waypoint Trig", waypoint="TP1234", county="Testshire")
        db.add(trig)
        db.commit()

        retrieved = get_trig_by_waypoint(db, waypoint="TP1234")
        assert retrieved is not None
        assert retrieved.id == 2

        # Test non-existent waypoint
        not_found = get_trig_by_waypoint(db, waypoint="TP9999")
        assert not_found is None

    def test_get_trigs_by_county(self, db: Session):
        """Test getting trigs by county."""
        trig1 = Trig(id=3, name="Trig 1", county="Testshire")
        trig2 = Trig(id=4, name="Trig 2", county="Testshire")
        trig3 = Trig(id=5, name="Trig 3", county="Othershire")

        db.add_all([trig1, trig2, trig3])
        db.commit()

        testshire_trigs = get_trigs_by_county(db, county="Testshire")
        assert len(testshire_trigs) == 2
        assert all(trig.county == "Testshire" for trig in testshire_trigs)

    def test_search_trigs_by_name(self, db: Session):
        """Test searching trigs by name pattern."""
        trig1 = Trig(id=7, name="Test Trig One", county="Testshire")
        trig2 = Trig(id=8, name="Another Test", county="Testshire")
        trig3 = Trig(id=9, name="Different Trig", county="Othershire")

        db.add_all([trig1, trig2, trig3])
        db.commit()

        # Search for "Test"
        test_results = search_trigs_by_name(db, name="Test")
        assert len(test_results) == 2
        assert all("Test" in trig.name for trig in test_results)

        # Search for "Trig"
        trig_results = search_trigs_by_name(db, name="Trig")
        assert len(trig_results) == 3

        # Search with no results
        empty_results = search_trigs_by_name(db, name="Nonexistent")
        assert len(empty_results) == 0

    def test_get_trigs_count(self, db: Session):
        """Test getting total trig count."""
        # Create some trigs
        trig1 = Trig(id=10, name="Count Trig 1", county="Testshire")
        trig2 = Trig(id=11, name="Count Trig 2", county="Testshire")

        db.add_all([trig1, trig2])
        db.commit()

        total_count = get_trigs_count(db)
        assert total_count >= 2  # Should be at least the ones we created
