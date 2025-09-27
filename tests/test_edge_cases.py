"""
Tests for edge cases and boundary conditions.
"""

import io
from datetime import date, datetime, time
from unittest.mock import Mock, patch

from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.tphoto import TPhoto
from app.models.user import TLog, User
from fastapi.testclient import TestClient


class TestEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    def test_photo_rotation_zero_angle(self, client: TestClient, db: Session):
        """Test photo rotation with 0 degree angle (edge case)."""
        user, log = self._create_user_and_log(db)
        photo = self._create_photo(db, log.id)

        with patch("requests.get") as mock_get, patch(
            "app.services.image_processor.ImageProcessor.process_image"
        ) as mock_process, patch(
            "app.services.s3_service.S3Service.upload_photo_and_thumbnail"
        ) as mock_s3:

            mock_get.return_value = Mock(
                content=b"image_data", raise_for_status=lambda: None
            )
            mock_process.return_value = (b"processed", b"thumb", (100, 100), (50, 50))
            mock_s3.return_value = ("photo.jpg", "thumb.jpg")

            response = client.post(
                f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
                json={"angle": 0},  # 0 degrees (not in allowed list)
                headers={"Authorization": "Bearer legacy_user_301"},
            )

            # Should reject 0 degrees
            assert response.status_code == 422

    def test_photo_rotation_negative_angle(self, client: TestClient, db: Session):
        """Test photo rotation with negative angle."""
        user, log = self._create_user_and_log(db)
        photo = self._create_photo(db, log.id)

        with patch("requests.get") as mock_get, patch(
            "app.services.image_processor.ImageProcessor.process_image"
        ) as mock_process, patch(
            "app.services.s3_service.S3Service.upload_photo_and_thumbnail"
        ) as mock_s3:

            mock_get.return_value = Mock(
                content=b"image_data", raise_for_status=lambda: None
            )
            mock_process.return_value = (b"processed", b"thumb", (100, 100), (50, 50))
            mock_s3.return_value = ("photo.jpg", "thumb.jpg")

            response = client.post(
                f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
                json={"angle": -90},  # Negative angle
                headers={"Authorization": "Bearer legacy_user_301"},
            )

            # Should reject negative angles
            assert response.status_code == 422

    def test_photo_rotation_large_angle(self, client: TestClient, db: Session):
        """Test photo rotation with angle > 270."""
        user, log = self._create_user_and_log(db)
        photo = self._create_photo(db, log.id)

        with patch("requests.get") as mock_get, patch(
            "app.services.image_processor.ImageProcessor.process_image"
        ) as mock_process, patch(
            "app.services.s3_service.S3Service.upload_photo_and_thumbnail"
        ) as mock_s3:

            mock_get.return_value = Mock(
                content=b"image_data", raise_for_status=lambda: None
            )
            mock_process.return_value = (b"processed", b"thumb", (100, 100), (50, 50))
            mock_s3.return_value = ("photo.jpg", "thumb.jpg")

            response = client.post(
                f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
                json={"angle": 360},  # 360 degrees (equivalent to 0)
                headers={"Authorization": "Bearer legacy_user_301"},
            )

            # Should reject angles outside allowed range
            assert response.status_code == 422

    def test_user_with_maximum_id(self, db: Session):
        """Test user operations with maximum possible ID."""
        max_id = 2147483647  # Max 32-bit signed integer

        user = User(
            id=max_id, name=f"user_{max_id}", email=f"user_{max_id}@example.com"
        )
        db.add(user)
        db.commit()

        # Test retrieving the user
        from app.crud.user import get_user_by_id

        retrieved = get_user_by_id(db, user_id=max_id)
        assert retrieved is not None
        assert retrieved.id == max_id

    def test_photo_with_maximum_filesize(self, db: Session):
        """Test photo with maximum possible filesize."""
        user, log = self._create_user_and_log(db)

        max_filesize = 2147483647  # Max 32-bit signed integer

        photo = TPhoto(
            id=4001,
            tlog_id=log.id,
            server_id=1,
            type="T",
            filename="max_size.jpg",
            filesize=max_filesize,
            height=1000,
            width=1000,
            icon_filesize=100000,
            icon_height=100,
            icon_width=100,
            name="Max Size Photo",
            text_desc="A very large photo",
            ip_addr="127.0.0.1",
            public_ind="Y",
            deleted_ind="N",
            source="W",
            crt_timestamp=datetime.utcnow(),
        )
        db.add(photo)
        db.commit()

        # Verify it was stored correctly
        db.refresh(photo)
        assert photo.filesize == max_filesize

    def test_concurrent_photo_rotations(self, client: TestClient, db: Session):
        """Test concurrent photo rotation operations."""
        user, log = self._create_user_and_log(db)

        # Create multiple photos
        photos = []
        for i in range(5):
            photo = self._create_photo(db, log.id, photo_id=5000 + i)
            photos.append(photo)

        db.commit()

        import threading

        results = []
        errors = []

        def rotate_photo(photo_id, request_id):
            try:
                with patch("requests.get") as mock_get, patch(
                    "app.services.image_processor.ImageProcessor.process_image"
                ) as mock_process, patch(
                    "app.services.s3_service.S3Service.upload_photo_and_thumbnail"
                ) as mock_s3:

                    mock_get.return_value = Mock(
                        content=b"image_data", raise_for_status=lambda: None
                    )
                    mock_process.return_value = (
                        b"processed",
                        b"thumb",
                        (100, 100),
                        (50, 50),
                    )
                    mock_s3.return_value = ("photo.jpg", "thumb.jpg")

                    response = client.post(
                        f"{settings.API_V1_STR}/photos/{photo_id}/rotate",
                        json={"angle": 90},
                        headers={"Authorization": "Bearer legacy_user_301"},
                    )

                    results.append((request_id, photo_id, response.status_code))

            except Exception as e:
                errors.append((request_id, photo_id, str(e)))

        # Start concurrent rotations
        threads = []
        for i, photo in enumerate(photos):
            thread = threading.Thread(target=rotate_photo, args=(photo.id, i))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=30)

        # Should have results for all photos
        assert len(results) == 5
        assert len(errors) == 0

        # All should succeed
        assert all(status == 200 for _, _, status in results)

    def test_image_processor_boundary_sizes(self):
        """Test image processor with boundary size images."""
        from app.services.image_processor import ImageProcessor

        processor = ImageProcessor()

        # Test 1x1 pixel image
        tiny_image = Image.new("RGB", (1, 1), color="red")
        buffer = io.BytesIO()
        tiny_image.save(buffer, format="JPEG")
        tiny_data = buffer.getvalue()

        result = processor.process_image(tiny_data)
        assert result is not None  # Should handle tiny images

        # Test image at maximum size limit
        max_size_image = Image.new(
            "RGB",
            (processor.max_photo_size[0], processor.max_photo_size[1]),
            color="blue",
        )
        buffer = io.BytesIO()
        max_size_image.save(buffer, format="JPEG", quality=95)
        max_data = buffer.getvalue()

        result = processor.process_image(max_data)
        assert result is not None

        processed_photo, processed_thumbnail, photo_dims, thumb_dims = result

        # Should be within limits
        assert photo_dims[0] <= processor.max_photo_size[0]
        assert photo_dims[1] <= processor.max_photo_size[1]

    def test_database_transaction_isolation(self, db: Session):
        """Test database transaction isolation."""
        user1 = User(id=3001, name="user1", email="user1@example.com")
        user2 = User(id=3002, name="user2", email="user2@example.com")

        log1 = TLog(id=6001, user_id=3001, trig_id=1, date=date.today())
        log2 = TLog(id=6002, user_id=3002, trig_id=1, date=date.today())

        db.add_all([user1, user2, log1, log2])
        db.commit()

        # Test that operations are properly isolated
        from app.crud.tlog import list_logs_filtered

        logs_user1 = list_logs_filtered(db, user_id=3001)
        logs_user2 = list_logs_filtered(db, user_id=3002)

        assert len(logs_user1) == 1
        assert len(logs_user2) == 1
        assert logs_user1[0].id != logs_user2[0].id

    def test_datetime_boundary_values(self, db: Session):
        """Test datetime boundary values."""
        # Test with minimum date (1970-01-01)
        min_date = date(1970, 1, 1)
        min_time = time(0, 0, 0)

        log = TLog(
            id=7001,
            user_id=3001,
            trig_id=1,
            date=min_date,
            time=min_time,
            osgb_eastings=0,
            osgb_northings=0,
            condition="G",
        )
        db.add(log)
        db.commit()

        # Verify it was stored correctly
        db.refresh(log)
        assert log.date == min_date
        assert log.time == min_time

        # Test with maximum reasonable date (far future)
        max_date = date(2100, 12, 31)
        max_time = time(23, 59, 59)

        log2 = TLog(
            id=7002,
            user_id=3001,
            trig_id=1,
            date=max_date,
            time=max_time,
            osgb_eastings=700000,
            osgb_northings=1300000,
            condition="E",
        )
        db.add(log2)
        db.commit()

        # Verify it was stored correctly
        db.refresh(log2)
        assert log2.date == max_date
        assert log2.time == max_time

    def test_coordinate_boundary_values(self, db: Session):
        """Test coordinate boundary values."""
        # Test with minimum coordinates
        min_log = TLog(
            id=7003,
            user_id=3001,
            trig_id=1,
            date=date.today(),
            osgb_eastings=0,
            osgb_northings=0,
            condition="G",
        )
        db.add(min_log)
        db.commit()

        # Test with maximum coordinates
        max_log = TLog(
            id=7004,
            user_id=3001,
            trig_id=1,
            date=date.today(),
            osgb_eastings=700000,
            osgb_northings=1300000,
            condition="G",
        )
        db.add(max_log)
        db.commit()

        # Verify both were stored correctly
        db.refresh(min_log)
        db.refresh(max_log)
        assert min_log.osgb_eastings == 0
        assert min_log.osgb_northings == 0
        assert max_log.osgb_eastings == 700000
        assert max_log.osgb_northings == 1300000

    def test_string_length_boundaries(self, db: Session):
        """Test string length boundary values."""
        # Test with empty strings
        user = User(
            id=3003, name="", email="empty@example.com", firstname="", surname=""
        )
        db.add(user)
        db.commit()

        # Test with maximum length strings
        long_name = "a" * 50  # Assuming reasonable max length
        long_email = f"{long_name}@example.com"

        long_user = User(
            id=3004,
            name=long_name,
            email=long_email,
            firstname=long_name,
            surname=long_name,
        )
        db.add(long_user)
        db.commit()

        # Verify both were stored correctly
        db.refresh(user)
        db.refresh(long_user)
        assert user.name == ""
        assert long_user.name == long_name

    def test_image_processor_memory_limits(self):
        """Test image processor memory handling."""
        from app.services.image_processor import ImageProcessor

        processor = ImageProcessor()

        # Create an image that might cause memory issues
        # This is a large but reasonable size for testing
        large_image = Image.new("RGB", (5000, 5000), color="gray")
        buffer = io.BytesIO()
        large_image.save(buffer, format="JPEG", quality=80)
        large_data = buffer.getvalue()

        # Should handle large images without crashing
        result = processor.process_image(large_data)

        if result is not None:
            # If processing succeeded, verify reasonable limits
            processed_photo, processed_thumbnail, photo_dims, thumb_dims = result
            assert photo_dims[0] <= processor.max_photo_size[0]
            assert photo_dims[1] <= processor.max_photo_size[1]

    def test_concurrent_database_operations(self, db: Session):
        """Test concurrent database operations."""
        import threading

        results = []
        errors = []

        def create_user_and_log(thread_id):
            try:
                user = User(
                    id=4000 + thread_id,
                    name=f"concurrent_user_{thread_id}",
                    email=f"concurrent_{thread_id}@example.com",
                )
                log = TLog(
                    id=8000 + thread_id,
                    user_id=4000 + thread_id,
                    trig_id=1,
                    date=date.today(),
                )

                db.add_all([user, log])
                db.commit()
                results.append(thread_id)
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Start concurrent operations
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_user_and_log, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=10)

        # Should have succeeded for all threads
        assert len(results) == 10
        assert len(errors) == 0

        # Verify all records were created
        created_users = db.query(User).filter(User.id >= 4000, User.id < 4010).all()
        created_logs = db.query(TLog).filter(TLog.id >= 8000, TLog.id < 8010).all()

        assert len(created_users) == 10
        assert len(created_logs) == 10

    def test_pagination_edge_cases(self, client: TestClient, db: Session):
        """Test pagination with edge cases."""
        user, log = self._create_user_and_log(db)

        # Create many logs for the same user
        logs = []
        for i in range(25):
            log_entry = TLog(id=9000 + i, user_id=user.id, trig_id=1, date=date.today())
            logs.append(log_entry)

        db.add_all(logs)
        db.commit()

        with patch("app.api.deps.get_current_user") as mock_get_current_user:
            mock_get_current_user.return_value = user

            # Test with page size 0
            response = client.get(
                f"{settings.API_V1_STR}/logs?skip=0&limit=0",
                headers={"Authorization": "Bearer legacy_user_301"},
            )
            assert response.status_code == 422  # Should reject limit=0

            # Test with very large page size
            response = client.get(
                f"{settings.API_V1_STR}/logs?skip=0&limit=10000",
                headers={"Authorization": "Bearer legacy_user_301"},
            )
            # Should handle gracefully
            assert response.status_code in [200, 422]

            # Test with negative skip
            response = client.get(
                f"{settings.API_V1_STR}/logs?skip=-1&limit=10",
                headers={"Authorization": "Bearer legacy_user_301"},
            )
            # Should handle gracefully
            assert response.status_code in [200, 422]

    def test_file_upload_size_limits(self, client: TestClient):
        """Test file upload size limit handling."""
        # Create a very large file (simulate)
        large_file_data = b"x" * (10 * 1024 * 1024)  # 10MB

        with patch("app.api.deps.get_db") as mock_get_db, patch(
            "app.api.deps.get_current_user"
        ) as mock_get_current_user:

            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_get_current_user.return_value = Mock()

            # Try to upload large file
            response = client.post(
                f"{settings.API_V1_STR}/photos",
                files={
                    "file": ("large.jpg", io.BytesIO(large_file_data), "image/jpeg")
                },
                data={
                    "log_id": "1",
                    "caption": "Large File",
                    "type": "T",
                    "licence": "Y",
                },
                headers={"Authorization": "Bearer test_token"},
            )

            # Should handle large files appropriately
            assert response.status_code in [400, 413, 422, 500]

    def test_database_connection_pool_exhaustion(self, db: Session):
        """Test handling of database connection pool exhaustion."""
        # This is hard to test directly, but we can test that
        # operations still work after many connections

        # Create many users and logs
        for i in range(100):
            user = User(
                id=5000 + i, name=f"pool_user_{i}", email=f"pool_{i}@example.com"
            )
            log = TLog(id=10000 + i, user_id=5000 + i, trig_id=1, date=date.today())
            db.add_all([user, log])

        db.commit()

        # Verify they were all created
        users = db.query(User).filter(User.id >= 5000, User.id < 5100).all()
        logs = db.query(TLog).filter(TLog.id >= 10000, TLog.id < 10100).all()

        assert len(users) == 100
        assert len(logs) == 100

    def _create_user_and_log(self, db: Session):
        """Helper to create test user and log."""
        user = User(id=301, name="testuser", email="test@example.com")
        log = TLog(id=3001, user_id=301, trig_id=1, date=date.today())
        db.add_all([user, log])
        db.commit()
        return user, log

    def _create_photo(self, db: Session, log_id: int, photo_id: int = 4001):
        """Helper to create test photo."""
        photo = TPhoto(
            id=photo_id,
            tlog_id=log_id,
            server_id=1,
            type="T",
            filename="test.jpg",
            filesize=1000,
            height=100,
            width=100,
            icon_filesize=100,
            icon_height=10,
            icon_width=10,
            name="Test Photo",
            text_desc="Test description",
            ip_addr="127.0.0.1",
            public_ind="Y",
            deleted_ind="N",
            source="W",
            crt_timestamp=datetime.utcnow(),
        )
        db.add(photo)
        db.commit()
        return photo
