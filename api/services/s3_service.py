"""
S3 service for photo uploads with rollback support.
"""

import logging
from typing import List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from api.core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for S3 operations with rollback support."""

    def __init__(self):
        """Initialise the S3 client."""
        try:
            self.s3_client = boto3.client("s3")
            self.bucket = settings.PHOTOS_S3_BUCKET
        except Exception as e:
            logger.error(f"Failed to initialise S3 client: {e}")
            self.s3_client = None

    def upload_photo_and_thumbnail(
        self, photo_id: int, photo_bytes: bytes, thumbnail_bytes: bytes
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Upload photo and thumbnail to S3.

        Args:
            photo_id: Database photo ID
            photo_bytes: Processed photo image bytes
            thumbnail_bytes: Processed thumbnail image bytes

        Returns:
            Tuple of (photo_key, thumbnail_key) on success, (None, None) on failure
        """
        if not self.s3_client:
            logger.error("S3 client not available")
            return None, None

        # Generate S3 keys
        photo_key = self._generate_photo_key(photo_id)
        thumbnail_key = self._generate_thumbnail_key(photo_id)

        uploaded_keys = []

        try:
            # Upload photo
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=photo_key,
                Body=photo_bytes,
                ContentType="image/jpeg",
                CacheControl="public, max-age=31536000",  # 1 year
                ACL="public-read",
            )
            uploaded_keys.append(photo_key)
            logger.info(f"Uploaded photo to S3: {photo_key}")

            # Upload thumbnail
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=thumbnail_key,
                Body=thumbnail_bytes,
                ContentType="image/jpeg",
                CacheControl="public, max-age=31536000",  # 1 year
                ACL="public-read",
            )
            uploaded_keys.append(thumbnail_key)
            logger.info(f"Uploaded thumbnail to S3: {thumbnail_key}")

            return photo_key, thumbnail_key

        except (ClientError, BotoCoreError) as e:
            logger.error(f"S3 upload failed: {e}")
            # Rollback any partial uploads
            self._rollback_uploads(uploaded_keys)
            return None, None

    def _generate_photo_key(self, photo_id: int) -> str:
        """Generate S3 key for photo using the required path pattern."""
        folder = photo_id // 1000
        return f"{folder:03d}/P{photo_id:05d}.jpg"

    def _generate_thumbnail_key(self, photo_id: int) -> str:
        """Generate S3 key for thumbnail using the required path pattern."""
        folder = photo_id // 1000
        return f"{folder:03d}/I{photo_id:05d}.jpg"

    def _rollback_uploads(self, keys: List[str]) -> None:
        """Delete uploaded files in case of failure."""
        if not self.s3_client or not keys:
            return

        for key in keys:
            try:
                self.s3_client.delete_object(Bucket=self.bucket, Key=key)
                logger.info(f"Rolled back S3 upload: {key}")
            except (ClientError, BotoCoreError) as e:
                logger.error(f"Failed to rollback S3 upload {key}: {e}")

    def delete_photo_and_thumbnail(self, photo_id: int) -> bool:
        """Delete photo and thumbnail from S3."""
        if not self.s3_client:
            logger.error("S3 client not available")
            return False

        photo_key = self._generate_photo_key(photo_id)
        thumbnail_key = self._generate_thumbnail_key(photo_id)

        try:
            # Delete both files
            for key in [photo_key, thumbnail_key]:
                self.s3_client.delete_object(Bucket=self.bucket, Key=key)

            logger.info(
                f"Deleted S3 files for photo {photo_id}: {photo_key}, {thumbnail_key}"
            )
            return True

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to delete S3 files for photo {photo_id}: {e}")
            return False
