"""
Tests for S3 service aligned with current implementation.
"""

from unittest.mock import Mock, patch

from botocore.exceptions import ClientError

from app.services.s3_service import S3Service


class TestS3Service:
    def test_init_sets_client_and_bucket(self):
        service = S3Service()
        assert hasattr(service, "s3_client")
        assert hasattr(service, "bucket")

    @patch("app.services.s3_service.boto3.client", side_effect=Exception("boom"))
    def test_init_handles_client_error(self, _mock_boto):
        service = S3Service()
        assert service.s3_client is None

    def test_generate_keys(self):
        service = S3Service()
        assert service._generate_photo_key(123) == "000/P00123.jpg"
        assert service._generate_thumbnail_key(123) == "000/I00123.jpg"
        assert service._generate_photo_key(999999) == "999/P999999.jpg"

    @patch("app.services.s3_service.boto3.client")
    def test_upload_photo_and_thumbnail_success(self, mock_boto_client):
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        service = S3Service()
        photo_bytes = b"photo"
        thumb_bytes = b"thumb"

        photo_key, thumb_key = service.upload_photo_and_thumbnail(
            42, photo_bytes, thumb_bytes
        )

        expected_photo_key = service._generate_photo_key(42)
        expected_thumb_key = service._generate_thumbnail_key(42)

        assert photo_key == expected_photo_key
        assert thumb_key == expected_thumb_key
        assert mock_client.put_object.call_count == 2

    @patch("app.services.s3_service.boto3.client")
    def test_upload_failure_rolls_back(self, mock_boto_client):
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        mock_client.put_object.side_effect = [
            None,
            ClientError({"Error": {"Code": "AccessDenied"}}, "PutObject"),
        ]

        service = S3Service()
        photo_key, thumb_key = service.upload_photo_and_thumbnail(1, b"photo", b"thumb")

        assert (photo_key, thumb_key) == (None, None)
        mock_client.delete_object.assert_called_once()

    def test_upload_without_client(self):
        service = S3Service()
        service.s3_client = None
        assert service.upload_photo_and_thumbnail(1, b"p", b"t") == (None, None)

    @patch("app.services.s3_service.boto3.client")
    def test_delete_photo_and_thumbnail_success(self, mock_boto_client):
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        service = S3Service()
        assert service.delete_photo_and_thumbnail(55) is True
        assert mock_client.delete_object.call_count == 2

    @patch("app.services.s3_service.boto3.client")
    def test_delete_photo_and_thumbnail_failure(self, mock_boto_client):
        mock_client = Mock()
        mock_client.delete_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey"}},
            "DeleteObject",
        )
        mock_boto_client.return_value = mock_client

        service = S3Service()
        assert service.delete_photo_and_thumbnail(123) is False

    def test_delete_without_client(self):
        service = S3Service()
        service.s3_client = None
        assert service.delete_photo_and_thumbnail(1) is False
