"""
S3 service for photo uploads with rollback support.
"""

import logging
import re
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

    def generate_revision_filename(self, current_filename: str) -> str:
        """
        Generate a new filename with an incremented revision suffix.

        Args:
            current_filename: Current filename (e.g., '002/P02001.jpg' or '023/P23001_r12.png')

        Returns:
            New filename with revision suffix (e.g., '002/P02001_r1.jpg' or '023/P23001_r13.png')

        Examples:
            '002/P02001.jpg' -> '002/P02001_r1.jpg'
            '023/P23001_r12.png' -> '023/P23001_r13.png'
            '000/I00001_r5.jpg' -> '000/I00001_r6.jpg'
        """
        # Split the filename into parts
        # Pattern: path/basename(_rN)?.extension
        match = re.match(r"^(.+?)(_r(\d+))?(\.[^.]+)$", current_filename)

        if not match:
            # Fallback: just add _r1 before any extension
            logger.warning(
                f"Could not parse filename pattern: {current_filename}, using fallback"
            )
            parts = current_filename.rsplit(".", 1)
            if len(parts) == 2:
                return f"{parts[0]}_r1.{parts[1]}"
            return f"{current_filename}_r1"

        base = match.group(1)  # Everything before _rN (e.g., '002/P02001')
        current_revision = match.group(3)  # The number N from _rN (if exists)
        extension = match.group(4)  # The extension (e.g., '.jpg')

        if current_revision:
            # Increment existing revision
            new_revision = int(current_revision) + 1
        else:
            # First revision
            new_revision = 1

        new_filename = f"{base}_r{new_revision}{extension}"
        logger.info(
            f"Generated revision filename: {current_filename} -> {new_filename}"
        )
        return new_filename

    def upload_photo_and_thumbnail_with_keys(
        self,
        photo_bytes: bytes,
        thumbnail_bytes: bytes,
        photo_key: str,
        thumbnail_key: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Upload photo and thumbnail to S3 with specified keys.

        Args:
            photo_bytes: Processed photo image bytes
            thumbnail_bytes: Processed thumbnail image bytes
            photo_key: S3 key for the photo
            thumbnail_key: S3 key for the thumbnail

        Returns:
            Tuple of (photo_key, thumbnail_key) on success, (None, None) on failure
        """
        if not self.s3_client:
            logger.error("S3 client not available")
            return None, None

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
