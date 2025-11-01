"""
Targeted regression tests for content moderation service.
"""

from unittest.mock import Mock, patch

from api.services.content_moderation import ContentModerationService


class TestContentModerationService:
    def test_moderate_photo_success(self, db):
        service = ContentModerationService()

        with patch(
            "api.services.content_moderation.tphoto_crud"
        ) as mock_crud, patch.object(
            service, "_get_server_for_photo"
        ) as mock_get_server, patch(
            "api.services.content_moderation.download_photo_bytes"
        ) as mock_download, patch.object(
            service.rekognition, "moderate_content"
        ) as mock_moderate:
            mock_photo = Mock()
            mock_photo.id = 1
            mock_photo.server_id = 1
            mock_photo.deleted_ind = "N"
            mock_photo.filename = "photo.jpg"
            mock_crud.get_photo_by_id.return_value = mock_photo

            mock_server = Mock()
            mock_server.url = "https://example.com"
            mock_get_server.return_value = mock_server

            mock_download.return_value = b"bytes"
            mock_moderate.return_value = {"is_inappropriate": False, "findings": []}

            assert service.moderate_photo(db, 1) is True
            mock_download.assert_called_once()
            mock_moderate.assert_called_once_with(b"bytes")

    def test_moderate_photo_not_found(self, db):
        service = ContentModerationService()
        with patch("api.services.content_moderation.tphoto_crud") as mock_crud:
            mock_crud.get_photo_by_id.return_value = None
            assert service.moderate_photo(db, 999) is False

    def test_moderate_photo_download_failure(self, db):
        service = ContentModerationService()
        with patch(
            "api.services.content_moderation.tphoto_crud"
        ) as mock_crud, patch.object(
            service, "_get_server_for_photo"
        ) as mock_get_server, patch(
            "api.services.content_moderation.download_photo_bytes"
        ) as mock_download:
            mock_photo = Mock()
            mock_photo.id = 1
            mock_photo.server_id = 1
            mock_photo.deleted_ind = "N"
            mock_photo.filename = "photo.jpg"
            mock_crud.get_photo_by_id.return_value = mock_photo

            mock_server = Mock()
            mock_server.url = "https://example.com"
            mock_get_server.return_value = mock_server

            mock_download.side_effect = Exception("download error")
            assert service.moderate_photo(db, 1) is False

    def test_moderate_photo_inappropriate_content(self, db):
        service = ContentModerationService()
        with patch(
            "api.services.content_moderation.tphoto_crud"
        ) as mock_crud, patch.object(
            service, "_get_server_for_photo"
        ) as mock_get_server, patch(
            "api.services.content_moderation.download_photo_bytes"
        ) as mock_download, patch.object(
            service.rekognition, "moderate_content"
        ) as mock_moderate:
            mock_photo = Mock()
            mock_photo.id = 1
            mock_photo.server_id = 1
            mock_photo.deleted_ind = "N"
            mock_photo.filename = "photo.jpg"
            mock_crud.get_photo_by_id.return_value = mock_photo

            mock_server = Mock()
            mock_server.url = "https://example.com"
            mock_get_server.return_value = mock_server

            mock_download.return_value = b"bytes"
            mock_moderate.return_value = {
                "is_inappropriate": True,
                "findings": [{"label": "Explicit Nudity", "confidence": 97.5}],
            }

            assert service.moderate_photo(db, 1) is False

    def test_moderate_photo_moderation_failure_marks_deleted(self, db):
        service = ContentModerationService()
        with patch(
            "api.services.content_moderation.tphoto_crud"
        ) as mock_crud, patch.object(
            service, "_get_server_for_photo"
        ) as mock_get_server, patch(
            "api.services.content_moderation.download_photo_bytes"
        ) as mock_download, patch.object(
            service.rekognition, "moderate_content"
        ) as mock_moderate:
            mock_photo = Mock()
            mock_photo.id = 1
            mock_photo.server_id = 1
            mock_photo.deleted_ind = "N"
            mock_photo.filename = "photo.jpg"
            mock_crud.get_photo_by_id.return_value = mock_photo

            mock_server = Mock()
            mock_server.url = "https://example.com"
            mock_get_server.return_value = mock_server

            mock_download.return_value = b"bytes"
            mock_moderate.return_value = None

            assert service.moderate_photo(db, 1) is False

    def test_moderate_photo_server_missing(self, db):
        service = ContentModerationService()
        with patch("api.services.content_moderation.tphoto_crud") as mock_crud:
            mock_photo = Mock()
            mock_photo.id = 1
            mock_photo.server_id = 123
            mock_photo.deleted_ind = "N"
            mock_photo.filename = "photo.jpg"
            mock_crud.get_photo_by_id.return_value = mock_photo

            assert service.moderate_photo(db, 1) is False

    def test_moderate_photo_already_moderated(self, db):
        service = ContentModerationService()
        with patch("api.services.content_moderation.tphoto_crud") as mock_crud:
            mock_photo = Mock()
            mock_photo.id = 1
            mock_photo.server_id = 1
            mock_photo.deleted_ind = "M"
            mock_photo.filename = "photo.jpg"
            mock_crud.get_photo_by_id.return_value = mock_photo

            assert service.moderate_photo(db, 1) is True

    def test_moderate_photo_handles_exception(self, db):
        service = ContentModerationService()
        with patch("api.services.content_moderation.tphoto_crud") as mock_crud:
            mock_crud.get_photo_by_id.side_effect = Exception("boom")
            assert service.moderate_photo(db, 1) is False
