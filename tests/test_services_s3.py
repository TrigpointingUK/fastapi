"""
Tests for S3 service.
"""

from unittest.mock import MagicMock, Mock, patch

import boto3
import pytest
from botocore.exceptions import ClientError

from app.services.s3_service import S3Service


class TestS3Service:
    """Test cases for S3 service."""

    def test_init(self):
        """Test service initialization."""
        service = S3Service()
        assert service is not None
        assert hasattr(service, "s3_client")
        assert hasattr(service, "bucket_name")

    @patch("app.services.s3_service.boto3.client")
    def test_init_with_custom_config(self, mock_boto_client):
        """Test service initialization with custom AWS config."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        service = S3Service()
        assert service.s3_client == mock_client
        mock_boto_client.assert_called_once()

    def test_get_photo_key(self):
        """Test photo key generation."""
        service = S3Service()

        # Test various photo IDs
        assert service.get_photo_key(123) == "123/P00123.jpg"
        assert service.get_photo_key(1) == "001/P00001.jpg"
        assert service.get_photo_key(999999) == "999999/P999999.jpg"

    def test_get_thumbnail_key(self):
        """Test thumbnail key generation."""
        service = S3Service()

        # Test various photo IDs
        assert service.get_thumbnail_key(123) == "123/I00123.jpg"
        assert service.get_thumbnail_key(1) == "001/I00001.jpg"
        assert service.get_thumbnail_key(999999) == "999999/I999999.jpg"

    @patch("app.services.s3_service.boto3.client")
    def test_upload_photo_success(self, mock_boto_client):
        """Test successful photo upload."""
        mock_client = Mock()
        mock_client.put_object.return_value = {"ETag": '"test-etag"'}
        mock_boto_client.return_value = mock_client

        service = S3Service()

        photo_data = b"test photo data"
        key = service.upload_photo(123, photo_data)

        assert key == "123/P00123.jpg"
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        assert call_args[1]["Bucket"] == service.bucket_name
        assert call_args[1]["Key"] == "123/P00123.jpg"
        assert call_args[1]["Body"] == photo_data
        assert call_args[1]["ContentType"] == "image/jpeg"

    @patch("app.services.s3_service.boto3.client")
    def test_upload_photo_s3_error(self, mock_boto_client):
        """Test photo upload with S3 error."""
        mock_client = Mock()
        mock_client.put_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}, "PutObject"
        )
        mock_boto_client.return_value = mock_client

        service = S3Service()

        photo_data = b"test photo data"
        with pytest.raises(ClientError):
            service.upload_photo(123, photo_data)

    @patch("app.services.s3_service.boto3.client")
    def test_upload_thumbnail_success(self, mock_boto_client):
        """Test successful thumbnail upload."""
        mock_client = Mock()
        mock_client.put_object.return_value = {"ETag": '"thumb-etag"'}
        mock_boto_client.return_value = mock_client

        service = S3Service()

        thumbnail_data = b"test thumbnail data"
        key = service.upload_thumbnail(123, thumbnail_data)

        assert key == "123/I00123.jpg"
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        assert call_args[1]["Bucket"] == service.bucket_name
        assert call_args[1]["Key"] == "123/I00123.jpg"
        assert call_args[1]["Body"] == thumbnail_data
        assert call_args[1]["ContentType"] == "image/jpeg"

    @patch("app.services.s3_service.boto3.client")
    def test_upload_photo_and_thumbnail_success(self, mock_boto_client):
        """Test successful upload of both photo and thumbnail."""
        mock_client = Mock()
        mock_client.put_object.return_value = {"ETag": '"test-etag"'}
        mock_boto_client.return_value = mock_client

        service = S3Service()

        photo_data = b"test photo data"
        thumbnail_data = b"test thumbnail data"

        photo_key, thumbnail_key = service.upload_photo_and_thumbnail(
            123, photo_data, thumbnail_data
        )

        assert photo_key == "123/P00123.jpg"
        assert thumbnail_key == "123/I00123.jpg"
        assert mock_client.put_object.call_count == 2

        # Check first call (photo)
        photo_call = mock_client.put_object.call_args_list[0]
        assert photo_call[1]["Key"] == "123/P00123.jpg"
        assert photo_call[1]["Body"] == photo_data

        # Check second call (thumbnail)
        thumb_call = mock_client.put_object.call_args_list[1]
        assert thumb_call[1]["Key"] == "123/I00123.jpg"
        assert thumb_call[1]["Body"] == thumbnail_data

    @patch("app.services.s3_service.boto3.client")
    def test_upload_photo_and_thumbnail_partial_failure(self, mock_boto_client):
        """Test upload with partial failure (photo succeeds, thumbnail fails)."""

        def side_effect(*args, **kwargs):
            if kwargs.get("Key", "").endswith(".jpg"):  # Photo
                return {"ETag": '"photo-etag"'}
            else:  # Thumbnail
                raise ClientError(
                    {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
                    "PutObject",
                )

        mock_client = Mock()
        mock_client.put_object.side_effect = side_effect
        mock_boto_client.return_value = mock_client

        service = S3Service()

        photo_data = b"test photo data"
        thumbnail_data = b"test thumbnail data"

        # Should return None for both on partial failure
        photo_key, thumbnail_key = service.upload_photo_and_thumbnail(
            123, photo_data, thumbnail_data
        )

        assert photo_key is None
        assert thumbnail_key is None
        assert mock_client.put_object.call_count == 2

    @patch("app.services.s3_service.boto3.client")
    def test_delete_photo_success(self, mock_boto_client):
        """Test successful photo deletion."""
        mock_client = Mock()
        mock_client.delete_object.return_value = {}
        mock_boto_client.return_value = mock_client

        service = S3Service()

        result = service.delete_photo(123)

        assert result is True
        mock_client.delete_object.assert_called_once_with(
            Bucket=service.bucket_name, Key="123/P00123.jpg"
        )

    @patch("app.services.s3_service.boto3.client")
    def test_delete_photo_not_found(self, mock_boto_client):
        """Test photo deletion when photo doesn't exist."""
        mock_client = Mock()
        mock_client.delete_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "DeleteObject"
        )
        mock_boto_client.return_value = mock_client

        service = S3Service()

        # Should return False for non-existent photo
        result = service.delete_photo(123)
        assert result is False

    @patch("app.services.s3_service.boto3.client")
    def test_delete_thumbnail_success(self, mock_boto_client):
        """Test successful thumbnail deletion."""
        mock_client = Mock()
        mock_client.delete_object.return_value = {}
        mock_boto_client.return_value = mock_client

        service = S3Service()

        result = service.delete_thumbnail(123)

        assert result is True
        mock_client.delete_object.assert_called_once_with(
            Bucket=service.bucket_name, Key="123/I00123.jpg"
        )

    @patch("app.services.s3_service.boto3.client")
    def test_delete_photo_and_thumbnail_success(self, mock_boto_client):
        """Test successful deletion of both photo and thumbnail."""
        mock_client = Mock()
        mock_client.delete_object.return_value = {}
        mock_boto_client.return_value = mock_client

        service = S3Service()

        result = service.delete_photo_and_thumbnail(123)

        assert result is True
        assert mock_client.delete_object.call_count == 2

        # Check calls
        calls = mock_client.delete_object.call_args_list
        assert calls[0][1]["Key"] == "123/P00123.jpg"
        assert calls[1][1]["Key"] == "123/I00123.jpg"

    @patch("app.services.s3_service.boto3.client")
    def test_delete_photo_and_thumbnail_partial_failure(self, mock_boto_client):
        """Test deletion with partial failure."""

        def side_effect(*args, **kwargs):
            key = kwargs.get("Key", "")
            if key.endswith(".jpg"):  # Photo
                return {}  # Success
            else:  # Thumbnail
                raise ClientError(
                    {"Error": {"Code": "NoSuchKey", "Message": "Not found"}},
                    "DeleteObject",
                )

        mock_client = Mock()
        mock_client.delete_object.side_effect = side_effect
        mock_boto_client.return_value = mock_client

        service = S3Service()

        # Should return False on partial failure
        result = service.delete_photo_and_thumbnail(123)
        assert result is False
        assert mock_client.delete_object.call_count == 2

    @patch("app.services.s3_service.boto3.client")
    def test_photo_exists_true(self, mock_boto_client):
        """Test checking if photo exists (exists)."""
        mock_client = Mock()
        mock_client.head_object.return_value = {
            "ContentLength": 1024,
            "ContentType": "image/jpeg",
        }
        mock_boto_client.return_value = mock_client

        service = S3Service()

        result = service.photo_exists(123)

        assert result is True
        mock_client.head_object.assert_called_once_with(
            Bucket=service.bucket_name, Key="123/P00123.jpg"
        )

    @patch("app.services.s3_service.boto3.client")
    def test_photo_exists_false(self, mock_boto_client):
        """Test checking if photo exists (doesn't exist)."""
        mock_client = Mock()
        mock_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "HeadObject"
        )
        mock_boto_client.return_value = mock_client

        service = S3Service()

        result = service.photo_exists(123)
        assert result is False

    @patch("app.services.s3_service.boto3.client")
    def test_thumbnail_exists_true(self, mock_boto_client):
        """Test checking if thumbnail exists (exists)."""
        mock_client = Mock()
        mock_client.head_object.return_value = {
            "ContentLength": 512,
            "ContentType": "image/jpeg",
        }
        mock_boto_client.return_value = mock_client

        service = S3Service()

        result = service.thumbnail_exists(123)

        assert result is True
        mock_client.head_object.assert_called_once_with(
            Bucket=service.bucket_name, Key="123/I00123.jpg"
        )

    @patch("app.services.s3_service.boto3.client")
    def test_get_photo_url(self, mock_boto_client):
        """Test getting photo URL."""
        service = S3Service()

        url = service.get_photo_url(123)
        expected_url = f"https://{service.bucket_name}.s3.amazonaws.com/123/P00123.jpg"
        assert url == expected_url

    @patch("app.services.s3_service.boto3.client")
    def test_get_thumbnail_url(self, mock_boto_client):
        """Test getting thumbnail URL."""
        service = S3Service()

        url = service.get_thumbnail_url(123)
        expected_url = f"https://{service.bucket_name}.s3.amazonaws.com/123/I00123.jpg"
        assert url == expected_url

    @patch("app.services.s3_service.boto3.client")
    def test_download_photo_success(self, mock_boto_client):
        """Test successful photo download."""
        mock_client = Mock()
        mock_client.get_object.return_value = {"Body": Mock(read=lambda: b"photo data")}
        mock_boto_client.return_value = mock_client

        service = S3Service()

        data = service.download_photo(123)
        assert data == b"photo data"
        mock_client.get_object.assert_called_once_with(
            Bucket=service.bucket_name, Key="123/P00123.jpg"
        )

    @patch("app.services.s3_service.boto3.client")
    def test_download_photo_not_found(self, mock_boto_client):
        """Test photo download when photo doesn't exist."""
        mock_client = Mock()
        mock_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject"
        )
        mock_boto_client.return_value = mock_client

        service = S3Service()

        data = service.download_photo(123)
        assert data is None

    @patch("app.services.s3_service.boto3.client")
    def test_download_thumbnail_success(self, mock_boto_client):
        """Test successful thumbnail download."""
        mock_client = Mock()
        mock_client.get_object.return_value = {
            "Body": Mock(read=lambda: b"thumbnail data")
        }
        mock_boto_client.return_value = mock_client

        service = S3Service()

        data = service.download_thumbnail(123)
        assert data == b"thumbnail data"
        mock_client.get_object.assert_called_once_with(
            Bucket=service.bucket_name, Key="123/I00123.jpg"
        )

    def test_get_bucket_name_from_config(self):
        """Test bucket name retrieval from config."""
        service = S3Service()

        # Mock the config
        with patch("app.services.s3_service.settings") as mock_settings:
            mock_settings.S3_BUCKET_NAME = "test-bucket"
            service2 = S3Service()
            assert service2.bucket_name == "test-bucket"

    def test_key_generation_edge_cases(self):
        """Test key generation with edge case photo IDs."""
        service = S3Service()

        # Test with ID 0
        assert service.get_photo_key(0) == "000/P00000.jpg"
        assert service.get_thumbnail_key(0) == "000/I00000.jpg"

        # Test with very large ID
        assert service.get_photo_key(999999999) == "999999999/P999999999.jpg"
        assert service.get_thumbnail_key(999999999) == "999999999/I999999999.jpg"

        # Test with negative ID (should handle gracefully)
        assert service.get_photo_key(-1) == "-001/P-00001.jpg"
        assert service.get_thumbnail_key(-1) == "-001/I-00001.jpg"
