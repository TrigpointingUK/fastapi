"""
Content moderation service for photos.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from api.crud import tphoto as tphoto_crud
from api.services.rekognition import RekognitionService

logger = logging.getLogger(__name__)


def download_photo_bytes(url: str) -> Optional[bytes]:
    """Download photo bytes from the given URL."""
    import requests

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content


class ContentModerationService:
    """Service for content moderation of uploaded photos."""

    def __init__(self):
        """Initialise the content moderation service."""
        self.rekognition = RekognitionService()

    def _get_server_for_photo(self, db: Session, server_id: int):
        from api.models.server import Server

        return db.query(Server).filter(Server.id == server_id).first()

    def moderate_photo(self, db: Session, photo_id: int) -> bool:
        """Moderate a photo for inappropriate content."""
        try:
            photo = tphoto_crud.get_photo_by_id(db, photo_id=photo_id)
            if not photo:
                logger.error(f"Photo {photo_id} not found for moderation")
                return False

            if photo.deleted_ind == "M":
                logger.info(f"Photo {photo_id} is already moderated")
                return True

            server = self._get_server_for_photo(db, int(photo.server_id))
            if not server or not server.url:
                logger.error(f"Server {photo.server_id} not found or has no URL")
                return False

            photo_url = f"{server.url.rstrip('/')}/{photo.filename}"

            try:
                photo_bytes = download_photo_bytes(photo_url)
            except Exception as exc:
                logger.error(
                    "Failed to download photo %s from %s: %s",
                    photo_id,
                    photo_url,
                    exc,
                )
                return False

            moderation_result = self.rekognition.moderate_content(photo_bytes)

            if not moderation_result:
                logger.warning(f"Content moderation failed for photo {photo_id}")
                self._mark_photo_moderated(
                    db, photo_id, "Moderation service unavailable"
                )
                return False

            if moderation_result.get("is_inappropriate", False):
                logger.warning(f"Inappropriate content detected in photo {photo_id}")
                findings = moderation_result.get("findings", [])
                reasons = [
                    f"{finding.get('label', 'Unknown')} ({finding.get('confidence', 0):.1f}%)"
                    for finding in findings[:3]
                ]
                reason = "Inappropriate content detected: " + ", ".join(reasons)
                self._mark_photo_moderated(db, photo_id, reason)
                return False

            logger.info(f"Photo {photo_id} passed content moderation")
            return True

        except Exception as exc:
            logger.error(f"Content moderation failed for photo {photo_id}: {exc}")
            self._mark_photo_moderated(db, photo_id, f"Moderation error: {exc}")
            return False

    def _mark_photo_moderated(self, db: Session, photo_id: int, reason: str) -> None:
        """Mark a photo as moderated (deleted_ind = 'M')."""
        try:
            from api.models.tphoto import TPhoto

            photo = db.query(TPhoto).filter(TPhoto.id == photo_id).first()
            if photo:
                setattr(photo, "deleted_ind", "M")
                db.add(photo)
                db.commit()
                logger.info(f"Marked photo {photo_id} as moderated: {reason}")
        except Exception as exc:
            logger.error(f"Failed to mark photo {photo_id} as moderated: {exc}")


content_moderation_service = ContentModerationService()


def moderate_photo_async(photo_id: int) -> None:
    logger.info(f"Starting async moderation for photo {photo_id}")
    logger.info(f"Photo {photo_id} moderation would run asynchronously")
