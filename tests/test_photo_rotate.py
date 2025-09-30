"""
Tests for photo rotation endpoint.
"""

import io
from datetime import datetime
from unittest.mock import Mock, patch

from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.tphoto import TPhoto
from app.models.user import TLog, User
from fastapi.testclient import TestClient


def seed_user_and_tlog(db: Session) -> tuple[User, TLog]:
    """Create test user and tlog."""
    user = User(
        id=301,
        name="rotateuser",
        firstname="Rotate",
        surname="User",
        email="r@example.com",
        auth0_user_id="auth0|301",
    )
    tlog = TLog(
        id=3001,
        trig_id=1,
        user_id=301,
        date=datetime(2023, 1, 1).date(),
        time=datetime(2023, 1, 1).time(),
        osgb_eastings=1,
        osgb_northings=1,
        osgb_gridref="AA 00000 00000",
        fb_number="",
        condition="G",
        comment="",
        score=0,
        ip_addr="127.0.0.1",
        source="W",
    )
    db.add(user)
    db.add(tlog)
    db.commit()
    return user, tlog


def create_sample_photo(db: Session, tlog_id: int, photo_id: int = 5001) -> TPhoto:
    """Create a test photo."""
    photo = TPhoto(
        id=photo_id,
        tlog_id=tlog_id,
        server_id=1,
        type="T",
        filename="000/P00001.jpg",
        filesize=100,
        height=100,
        width=100,
        icon_filename="000/I00001.jpg",
        icon_filesize=10,
        icon_height=10,
        icon_width=10,
        name="Test Photo",
        text_desc="A test",
        ip_addr="127.0.0.1",
        public_ind="Y",
        deleted_ind="N",
        source="W",
        crt_timestamp=datetime.utcnow(),
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def create_test_image() -> bytes:
    """Create a small test JPEG image."""
    image = Image.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


class TestPhotoRotate:
    """Test cases for photo rotation endpoint."""

    def test_rotate_photo_success_90_degrees(self, client: TestClient, db: Session):
        """Test successful photo rotation by 90 degrees."""
        user, tlog = seed_user_and_tlog(db)
        photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=5001)

        test_image_bytes = create_test_image()

        with patch("requests.get") as mock_get, patch(
            "app.services.image_processor.ImageProcessor.process_image"
        ) as mock_process, patch(
            "app.services.s3_service.S3Service.upload_photo_and_thumbnail"
        ) as mock_s3_upload, patch(
            "app.services.s3_service.S3Service.delete_photo_and_thumbnail"
        ) as mock_s3_delete:

            # Mock photo download
            mock_response = Mock()
            mock_response.content = test_image_bytes
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Mock image processing
            mock_process.return_value = (
                b"processed_photo",
                b"processed_thumbnail",
                (150, 200),
                (75, 100),
            )

            # Mock S3 upload
            mock_s3_upload.return_value = ("new_photo.jpg", "new_thumb.jpg")

            headers = {"Authorization": "Bearer auth0_user_301"}
            resp = client.post(
                f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
                json={"angle": 90},
                headers=headers,
            )

            assert resp.status_code == 200
            body = resp.json()

            # Check that we got a new photo ID
            assert body["id"] != photo.id
            assert body["log_id"] == photo.tlog_id
            assert body["user_id"] == user.id
            assert body["type"] == "T"
            assert body["height"] == 200
            assert body["width"] == 150
            assert body["caption"] == "Test Photo"

            # Verify original photo was soft-deleted
            db.refresh(photo)
            assert photo.deleted_ind == "Y"

            # Verify new photo exists
            new_photo_id = body["id"]
            new_photo = db.query(TPhoto).filter(TPhoto.id == new_photo_id).first()
            assert new_photo is not None
            assert new_photo.deleted_ind == "N"
            assert new_photo.source == "R"  # R for rotated

            # Verify S3 operations
            mock_s3_upload.assert_called_once()
            mock_s3_delete.assert_not_called()

    def test_rotate_photo_success_180_degrees(self, client: TestClient, db: Session):
        """Test successful photo rotation by 180 degrees."""
        user, tlog = seed_user_and_tlog(db)
        photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=5002)

        test_image_bytes = create_test_image()

        with patch("requests.get") as mock_get, patch(
            "app.services.image_processor.ImageProcessor.process_image"
        ) as mock_process, patch(
            "app.services.s3_service.S3Service.upload_photo_and_thumbnail"
        ) as mock_s3_upload:

            mock_response = Mock()
            mock_response.content = test_image_bytes
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            mock_process.return_value = (
                b"processed_photo",
                b"processed_thumbnail",
                (100, 100),
                (50, 50),
            )
            mock_s3_upload.return_value = ("new_photo.jpg", "new_thumb.jpg")

            headers = {"Authorization": "Bearer auth0_user_301"}
            resp = client.post(
                f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
                json={"angle": 180},
                headers=headers,
            )

            assert resp.status_code == 200
            body = resp.json()
            assert body["id"] != photo.id

    def test_rotate_photo_default_angle(self, client: TestClient, db: Session):
        """Test photo rotation with default angle (90 degrees)."""
        user, tlog = seed_user_and_tlog(db)
        photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=5003)

        test_image_bytes = create_test_image()

        with patch("requests.get") as mock_get, patch(
            "app.services.image_processor.ImageProcessor.process_image"
        ) as mock_process, patch(
            "app.services.s3_service.S3Service.upload_photo_and_thumbnail"
        ) as mock_s3_upload:

            mock_response = Mock()
            mock_response.content = test_image_bytes
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            mock_process.return_value = (
                b"processed_photo",
                b"processed_thumbnail",
                (150, 200),
                (75, 100),
            )
            mock_s3_upload.return_value = ("new_photo.jpg", "new_thumb.jpg")

            headers = {"Authorization": "Bearer auth0_user_301"}
            # Don't specify angle - should default to 90
            resp = client.post(
                f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
                json={},
                headers=headers,
            )

            assert resp.status_code == 200

    def test_rotate_photo_invalid_angle(self, client: TestClient, db: Session):
        """Test photo rotation with invalid angle."""
        user, tlog = seed_user_and_tlog(db)
        photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=5004)

        headers = {"Authorization": "Bearer auth0_user_301"}
        resp = client.post(
            f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
            json={"angle": 45},  # Invalid angle
            headers=headers,
        )

        assert resp.status_code == 422  # Validation error
        assert "angle must be 90, 180, or 270" in resp.text

    def test_rotate_photo_not_found(self, client: TestClient, db: Session):
        """Test rotation of non-existent photo."""
        # Create user first so auth works
        user, tlog = seed_user_and_tlog(db)

        headers = {"Authorization": "Bearer auth0_user_301"}
        resp = client.post(
            f"{settings.API_V1_STR}/photos/99999/rotate",
            json={"angle": 90},
            headers=headers,
        )

        assert resp.status_code == 404
        assert "Photo not found" in resp.json()["detail"]

    def test_rotate_photo_unauthorized_user(self, client: TestClient, db: Session):
        """Test rotation by user who doesn't own the photo."""
        user, tlog = seed_user_and_tlog(db)
        photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=5005)

        # Create a different user
        other_user = User(
            id=999,
            name="otheruser",
            firstname="Other",
            surname="User",
            email="other@example.com",
            auth0_user_id="auth0|999",
        )
        db.add(other_user)
        db.commit()

        # Try to rotate with different user
        headers = {"Authorization": "Bearer auth0_user_999"}
        resp = client.post(
            f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
            json={"angle": 90},
            headers=headers,
        )

        assert resp.status_code == 403
        assert "Missing required scope" in resp.json()["detail"]

    def test_rotate_photo_no_auth(self, client: TestClient, db: Session):
        """Test rotation without authentication."""
        user, tlog = seed_user_and_tlog(db)
        photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=5006)

        resp = client.post(
            f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
            json={"angle": 90},
        )

        assert resp.status_code == 401

    def test_rotate_photo_download_failure(self, client: TestClient, db: Session):
        """Test rotation when photo download fails."""
        user, tlog = seed_user_and_tlog(db)
        photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=5007)

        with patch("requests.get") as mock_get:
            # Mock download failure
            mock_get.side_effect = Exception("Download failed")

            headers = {"Authorization": "Bearer auth0_user_301"}
            resp = client.post(
                f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
                json={"angle": 90},
                headers=headers,
            )

            assert resp.status_code == 500
            assert "Error downloading photo" in resp.json()["detail"]

    def test_rotate_photo_image_processing_failure(
        self, client: TestClient, db: Session
    ):
        """Test rotation when image processing fails."""
        user, tlog = seed_user_and_tlog(db)
        photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=5008)

        test_image_bytes = create_test_image()

        with patch("requests.get") as mock_get, patch(
            "PIL.Image.open"
        ) as mock_image_open:

            mock_response = Mock()
            mock_response.content = test_image_bytes
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Mock image processing failure
            mock_image_open.side_effect = Exception("Image processing failed")

            headers = {"Authorization": "Bearer auth0_user_301"}
            resp = client.post(
                f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
                json={"angle": 90},
                headers=headers,
            )

            assert resp.status_code == 500
            assert "Failed to rotate image" in resp.json()["detail"]

    def test_rotate_photo_s3_upload_failure_rollback(
        self, client: TestClient, db: Session
    ):
        """Test rollback when S3 upload fails."""
        user, tlog = seed_user_and_tlog(db)
        photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=5009)

        test_image_bytes = create_test_image()
        original_deleted_ind = photo.deleted_ind

        with patch("requests.get") as mock_get, patch(
            "app.services.image_processor.ImageProcessor.process_image"
        ) as mock_process, patch(
            "app.services.s3_service.S3Service.upload_photo_and_thumbnail"
        ) as mock_s3_upload:

            mock_response = Mock()
            mock_response.content = test_image_bytes
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            mock_process.return_value = (
                b"processed_photo",
                b"processed_thumbnail",
                (150, 200),
                (75, 100),
            )

            # Mock S3 upload failure
            mock_s3_upload.return_value = (None, None)

            headers = {"Authorization": "Bearer auth0_user_301"}
            resp = client.post(
                f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
                json={"angle": 90},
                headers=headers,
            )

            assert resp.status_code == 500
            assert "Failed to upload rotated files" in resp.json()["detail"]

            # Verify original photo was not soft-deleted (rollback)
            db.refresh(photo)
            assert photo.deleted_ind == original_deleted_ind

            # Verify no new photo record exists
            new_photos = (
                db.query(TPhoto)
                .filter(TPhoto.tlog_id == tlog.id, TPhoto.source == "R")
                .all()
            )
            assert len(new_photos) == 0

    def test_rotate_photo_database_failure_rollback(
        self, client: TestClient, db: Session
    ):
        """Test rollback when database operations fail."""
        user, tlog = seed_user_and_tlog(db)
        photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=5010)

        test_image_bytes = create_test_image()

        with patch("requests.get") as mock_get, patch(
            "app.services.image_processor.ImageProcessor.process_image"
        ) as mock_process, patch(
            "app.services.s3_service.S3Service.upload_photo_and_thumbnail"
        ) as mock_s3_upload, patch(
            "app.services.s3_service.S3Service.delete_photo_and_thumbnail"
        ), patch(
            "app.crud.tphoto.create_photo"
        ) as mock_create:

            mock_response = Mock()
            mock_response.content = test_image_bytes
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            mock_process.return_value = (
                b"processed_photo",
                b"processed_thumbnail",
                (150, 200),
                (75, 100),
            )
            mock_s3_upload.return_value = ("new_photo.jpg", "new_thumb.jpg")

            # Mock database creation failure
            mock_create.side_effect = Exception("Database error")

            headers = {"Authorization": "Bearer auth0_user_301"}
            resp = client.post(
                f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
                json={"angle": 90},
                headers=headers,
            )

            assert resp.status_code == 500
            assert "Failed to create new photo record" in resp.json()["detail"]

    def test_rotate_photo_preserves_metadata(self, client: TestClient, db: Session):
        """Test that rotation preserves original photo metadata."""
        user, tlog = seed_user_and_tlog(db)
        photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=5011)

        # Set specific metadata
        photo.name = "Special Photo"
        photo.text_desc = "Special description"
        photo.public_ind = "N"
        photo.type = "L"
        db.add(photo)
        db.commit()

        test_image_bytes = create_test_image()

        with patch("requests.get") as mock_get, patch(
            "app.services.image_processor.ImageProcessor.process_image"
        ) as mock_process, patch(
            "app.services.s3_service.S3Service.upload_photo_and_thumbnail"
        ) as mock_s3_upload:

            mock_response = Mock()
            mock_response.content = test_image_bytes
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            mock_process.return_value = (
                b"processed_photo",
                b"processed_thumbnail",
                (150, 200),
                (75, 100),
            )
            mock_s3_upload.return_value = ("new_photo.jpg", "new_thumb.jpg")

            headers = {"Authorization": "Bearer auth0_user_301"}
            resp = client.post(
                f"{settings.API_V1_STR}/photos/{photo.id}/rotate",
                json={"angle": 90},
                headers=headers,
            )

            assert resp.status_code == 200
            body = resp.json()

            # Verify metadata is preserved
            assert body["caption"] == "Special Photo"
            assert body["text_desc"] == "Special description"
            assert body["license"] == "N"
            assert body["type"] == "L"

            # Verify in database
            new_photo_id = body["id"]
            new_photo = db.query(TPhoto).filter(TPhoto.id == new_photo_id).first()
            assert new_photo.name == "Special Photo"
            assert new_photo.text_desc == "Special description"
            assert new_photo.public_ind == "N"
            assert new_photo.type == "L"
            assert new_photo.source == "R"
