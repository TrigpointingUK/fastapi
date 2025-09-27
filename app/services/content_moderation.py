"""
Content moderation service for photos.
"""

import logging

from sqlalchemy.orm import Session

from app.crud import tphoto as tphoto_crud
from app.services.rekognition import RekognitionService

logger = logging.getLogger(__name__)


class ContentModerationService:
    """Service for content moderation of uploaded photos."""

    def __init__(self):
        """Initialise the content moderation service."""
        self.rekognition = RekognitionService()

    def moderate_photo(self, db: Session, photo_id: int) -> bool:
        """
        Moderate a photo for inappropriate content.

        Args:
            db: Database session
            photo_id: Photo ID to moderate

        Returns:
            True if moderation passed, False if inappropriate content found
        """
        try:
            # Get photo from database
            photo = tphoto_crud.get_photo_by_id(db, photo_id=photo_id)
            if not photo:
                logger.error(f"Photo {photo_id} not found for moderation")
                return False

            # Check if photo is already moderated
            if photo.deleted_ind == "M":
                logger.info(f"Photo {photo_id} is already moderated")
                return True

            # Download photo from S3 for analysis
            # Note: This assumes the photo is accessible via the URL in the database
            # In a real implementation, you might want to download directly from S3
            from app.models.server import Server

            server = db.query(Server).filter(Server.id == photo.server_id).first()
            if not server or not server.url:
                logger.error(f"Server {photo.server_id} not found or has no URL")
                return False

            photo_url = f"{server.url.rstrip('/')}/{photo.filename}"

            import requests

            try:
                response = requests.get(photo_url, timeout=30)
                response.raise_for_status()
                photo_bytes = response.content
            except Exception as e:
                logger.error(
                    f"Failed to download photo {photo_id} from {photo_url}: {e}"
                )
                return False

            # Run content moderation
            moderation_result = self.rekognition.moderate_content(photo_bytes)

            if not moderation_result:
                logger.warning(f"Content moderation failed for photo {photo_id}")
                # Mark as moderated due to failure
                self._mark_photo_moderated(
                    db, photo_id, "Moderation service unavailable"
                )
                return False

            # Check if inappropriate content was found
            if moderation_result.get("is_inappropriate", False):
                logger.warning(f"Inappropriate content detected in photo {photo_id}")

                # Get details about what was found
                findings = moderation_result.get("findings", [])

                # Create a reason string
                reasons = []
                for finding in findings[:3]:  # Limit to first 3 findings
                    reasons.append(
                        f"{finding.get('label', 'Unknown')} ({finding.get('confidence', 0):.1f}%)"
                    )

                reason = "Inappropriate content detected: " + ", ".join(reasons)

                # Mark photo as moderated
                self._mark_photo_moderated(db, photo_id, reason)
                return False

            logger.info(f"Photo {photo_id} passed content moderation")
            return True

        except Exception as e:
            logger.error(f"Content moderation failed for photo {photo_id}: {e}")
            # Mark as moderated due to error
            self._mark_photo_moderated(db, photo_id, f"Moderation error: {str(e)}")
            return False

    def _mark_photo_moderated(self, db: Session, photo_id: int, reason: str) -> None:
        """Mark a photo as moderated (deleted_ind = 'M')."""
        try:
            from app.models.tphoto import TPhoto

            photo = db.query(TPhoto).filter(TPhoto.id == photo_id).first()
            if photo:
                setattr(photo, "deleted_ind", "M")
                db.add(photo)
                db.commit()
                logger.info(f"Marked photo {photo_id} as moderated: {reason}")
        except Exception as e:
            logger.error(f"Failed to mark photo {photo_id} as moderated: {e}")


# Global instance
content_moderation_service = ContentModerationService()


def moderate_photo_async(photo_id: int) -> None:
    """
    Async wrapper for photo moderation.

    Note: This is a synchronous implementation that can be easily converted
    to use Celery, RQ, or another async task queue.
    """
    # For now, this is synchronous, but could be wrapped with threading
    # or converted to use an async task queue
    logger.info(f"Starting async moderation for photo {photo_id}")

    # This would typically be handled by a task queue
    # For now, we'll just log that it would run
    logger.info(f"Photo {photo_id} moderation would run asynchronously")

    # In a real implementation, you might want to use threading:
    # import threading
    # threading.Thread(target=_moderate_photo_sync, args=(photo_id,)).start()
