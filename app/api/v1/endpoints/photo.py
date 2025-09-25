"""
Photo endpoints (RUD) and user photo count.
"""

import logging

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_scopes
from app.api.lifecycle import openapi_lifecycle
from app.crud import tphoto as tphoto_crud
from app.models.server import Server
from app.models.user import TLog, User
from app.schemas.tphoto import TPhotoEvaluationResponse, TPhotoResponse, TPhotoUpdate
from app.services.rekognition import RekognitionService, get_image_dimensions

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{photo_id}",
    response_model=TPhotoResponse,
    openapi_extra=openapi_lifecycle("beta"),
)
def get_photo(photo_id: int, db: Session = Depends(get_db)):
    photo = tphoto_crud.get_photo_by_id(db, photo_id=photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Build URLs by joining server.url with filenames
    server: Server | None = (
        db.query(Server).filter(Server.id == photo.server_id).first()
    )
    base_url = str(server.url) if server and server.url else ""

    # Ensure single slash joining
    def join_url(base: str, path: str) -> str:
        if not base:
            return path
        if base.endswith("/"):
            return f"{base}{path}"
        return f"{base}/{path}"

    # Lookup user_id from tlog
    tlog: TLog | None = db.query(TLog).filter(TLog.id == photo.tlog_id).first()
    response = {
        "id": photo.id,
        "tlog_id": photo.tlog_id,
        "user_id": int(tlog.user_id) if tlog else 0,
        "type": str(photo.type),
        "filesize": int(photo.filesize),
        "height": int(photo.height),
        "width": int(photo.width),
        "icon_filesize": int(photo.icon_filesize),
        "icon_height": int(photo.icon_height),
        "icon_width": int(photo.icon_width),
        "name": str(photo.name),
        "text_desc": str(photo.text_desc),
        "public_ind": str(photo.public_ind),
        "photo_url": join_url(base_url, str(photo.filename)),
        "icon_url": join_url(base_url, str(photo.icon_filename)),
    }
    return response


@router.patch(
    "/{photo_id}",
    response_model=TPhotoResponse,
    openapi_extra=openapi_lifecycle("beta"),
)
def update_photo(
    photo_id: int,
    payload: TPhotoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Load current photo and authorise BEFORE applying updates
    existing = tphoto_crud.get_photo_by_id(db, photo_id=photo_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Authorisation: owner or trig:admin
    tlog: TLog | None = db.query(TLog).filter(TLog.id == existing.tlog_id).first()
    if not tlog:
        raise HTTPException(status_code=404, detail="TLog not found for photo")

    # If not owner, require admin scope
    if int(current_user.id) != int(tlog.user_id):
        # This will raise 403 if missing
        require_scopes("trig:admin")(db=db)

    # Proceed with update
    updated = tphoto_crud.update_photo(
        db, photo_id=photo_id, updates=payload.model_dump(exclude_none=True)
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    server: Server | None = (
        db.query(Server).filter(Server.id == updated.server_id).first()
    )
    base_url = str(server.url) if server and server.url else ""

    def join_url(base: str, path: str) -> str:
        if not base:
            return path
        if base.endswith("/"):
            return f"{base}{path}"
        return f"{base}/{path}"

    response = {
        "id": updated.id,
        "tlog_id": updated.tlog_id,
        "user_id": int(tlog.user_id),
        "type": str(updated.type),
        "filesize": int(updated.filesize),
        "height": int(updated.height),
        "width": int(updated.width),
        "icon_filesize": int(updated.icon_filesize),
        "icon_height": int(updated.icon_height),
        "icon_width": int(updated.icon_width),
        "name": str(updated.name),
        "text_desc": str(updated.text_desc),
        "public_ind": str(updated.public_ind),
        "photo_url": join_url(base_url, str(updated.filename)),
        "icon_url": join_url(base_url, str(updated.icon_filename)),
    }
    return response


@router.delete("/{photo_id}", status_code=204, openapi_extra=openapi_lifecycle("beta"))
def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Load and authorise BEFORE delete
    existing = tphoto_crud.get_photo_by_id(db, photo_id=photo_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Photo not found")

    tlog = db.query(TLog).filter(TLog.id == existing.tlog_id).first()
    if not tlog:
        raise HTTPException(status_code=404, detail="TLog not found for photo")

    if int(current_user.id) != int(tlog.user_id):
        require_scopes("trig:admin")(db=db)

    ok = tphoto_crud.delete_photo(db, photo_id=photo_id, soft=True)
    if not ok:
        raise HTTPException(status_code=404, detail="Photo not found")
    return None


@router.get("/users/{user_id}/count", openapi_extra=openapi_lifecycle("beta"))
def get_user_photo_count(user_id: int, db: Session = Depends(get_db)):
    count = tphoto_crud.count_photos_by_user(db, user_id=user_id)
    return {"user_id": user_id, "photo_count": int(count)}


@router.post(
    "/{photo_id}/evaluate",
    response_model=TPhotoEvaluationResponse,
    openapi_extra=openapi_lifecycle("beta"),
)
def evaluate_photo(photo_id: int, db: Session = Depends(get_db)):
    """
    Evaluate a photo by downloading it and running AWS Rekognition analysis.

    Checks:
    - Photo and icon accessibility
    - Dimension validation against database
    - Orientation analysis (90°, 180°, 270° rotation detection)
    - Content moderation (inappropriate content detection)
    """
    # Look up photo in database
    photo = tphoto_crud.get_photo_by_id(db, photo_id=photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Get server URL for constructing full URLs
    server: Server | None = (
        db.query(Server).filter(Server.id == photo.server_id).first()
    )
    base_url = str(server.url) if server and server.url else ""

    def join_url(base: str, path: str) -> str:
        if not base:
            return path
        if base.endswith("/"):
            return f"{base}{path}"
        return f"{base}/{path}"

    photo_url = join_url(base_url, str(photo.filename))
    icon_url = join_url(base_url, str(photo.icon_filename))

    # Initialise response
    response = TPhotoEvaluationResponse(
        photo_id=photo_id,
        photo_accessible=False,
        icon_accessible=False,
        photo_dimension_match=False,
        icon_dimension_match=False,
        errors=[],
    )

    # Initialise Rekognition service
    rekognition = RekognitionService()

    # Download and analyse main photo
    photo_bytes = None
    try:
        logger.info(f"Downloading photo from: {photo_url}")
        photo_response = requests.get(photo_url, timeout=30)
        photo_response.raise_for_status()
        photo_bytes = photo_response.content
        response.photo_accessible = True

        # Check dimensions
        actual_width, actual_height = get_image_dimensions(photo_bytes)
        if actual_width is not None and actual_height is not None:
            response.photo_width_actual = actual_width
            response.photo_height_actual = actual_height
            response.photo_dimension_match = (
                actual_width == photo.width and actual_height == photo.height
            )
            if not response.photo_dimension_match:
                response.errors.append(
                    f"Photo dimensions mismatch: DB({photo.width}x{photo.height}) "
                    f"vs Actual({actual_width}x{actual_height})"
                )
        else:
            response.errors.append("Could not determine photo dimensions")

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download photo {photo_url}: {e}")
        response.errors.append(f"Photo download failed: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing photo {photo_url}: {e}")
        response.errors.append(f"Photo processing error: {str(e)}")

    # Download and analyse icon
    try:
        logger.info(f"Downloading icon from: {icon_url}")
        icon_response = requests.get(icon_url, timeout=30)
        icon_response.raise_for_status()
        icon_bytes = icon_response.content
        response.icon_accessible = True

        # Check dimensions
        actual_width, actual_height = get_image_dimensions(icon_bytes)
        if actual_width is not None and actual_height is not None:
            response.icon_width_actual = actual_width
            response.icon_height_actual = actual_height
            response.icon_dimension_match = (
                actual_width == photo.icon_width and actual_height == photo.icon_height
            )
            if not response.icon_dimension_match:
                response.errors.append(
                    f"Icon dimensions mismatch: DB({photo.icon_width}x{photo.icon_height}) "
                    f"vs Actual({actual_width}x{actual_height})"
                )
        else:
            response.errors.append("Could not determine icon dimensions")

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download icon {icon_url}: {e}")
        response.errors.append(f"Icon download failed: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing icon {icon_url}: {e}")
        response.errors.append(f"Icon processing error: {str(e)}")

    # Run AWS Rekognition analysis on main photo if available
    if photo_bytes and len(photo_bytes) > 0:
        try:
            # Orientation analysis
            orientation_result = rekognition.analyse_orientation(photo_bytes)
            if orientation_result:
                response.orientation_analysis = orientation_result
            else:
                response.errors.append(
                    "Orientation analysis unavailable (AWS configuration issue)"
                )

            # Content moderation
            moderation_result = rekognition.moderate_content(photo_bytes)
            if moderation_result:
                response.content_moderation = moderation_result
            else:
                response.errors.append(
                    "Content moderation unavailable (AWS configuration issue)"
                )

        except Exception as e:
            logger.error(f"AWS Rekognition analysis failed: {e}")
            response.errors.append(f"AWS analysis error: {str(e)}")
    else:
        response.errors.append("No photo data available for AWS analysis")

    return response
