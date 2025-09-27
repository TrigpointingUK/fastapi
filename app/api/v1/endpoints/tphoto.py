"""
TPhoto endpoints (RUD) and user photo count.
"""

from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.lifecycle import openapi_lifecycle
from app.crud import tphoto as tphoto_crud
from app.models.server import Server
from app.schemas.tphoto import TPhotoResponse, TPhotoUpdate
from fastapi import APIRouter, Depends, HTTPException

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

    response = {
        "id": photo.id,
        "log_id": photo.tlog_id,
        "type": str(photo.type),
        "filesize": int(photo.filesize),
        "height": int(photo.height),
        "width": int(photo.width),
        "icon_filesize": int(photo.icon_filesize),
        "icon_height": int(photo.icon_height),
        "icon_width": int(photo.icon_width),
        "caption": str(photo.name),
        "text_desc": str(photo.text_desc),
        "license": str(photo.public_ind),
        "photo_url": join_url(base_url, str(photo.filename)),
        "icon_url": join_url(base_url, str(photo.icon_filename)),
    }
    return response


@router.patch(
    "/{photo_id}",
    response_model=TPhotoResponse,
    openapi_extra={
        **openapi_lifecycle("beta"),
        "security": [{"OAuth2": []}],
    },
)
def update_photo(photo_id: int, payload: TPhotoUpdate, db: Session = Depends(get_db)):
    updated = tphoto_crud.update_photo(
        db, photo_id=photo_id, updates=payload.model_dump(exclude_none=True)
    )
    if not updated:
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
        "log_id": updated.tlog_id,
        "type": str(updated.type),
        "filesize": int(updated.filesize),
        "height": int(updated.height),
        "width": int(updated.width),
        "icon_filesize": int(updated.icon_filesize),
        "icon_height": int(updated.icon_height),
        "icon_width": int(updated.icon_width),
        "caption": str(updated.name),
        "text_desc": str(updated.text_desc),
        "license": str(updated.public_ind),
        "photo_url": join_url(base_url, str(updated.filename)),
        "icon_url": join_url(base_url, str(updated.icon_filename)),
    }
    return response


@router.delete(
    "/{photo_id}",
    status_code=204,
    openapi_extra={
        **openapi_lifecycle("beta"),
        "security": [{"OAuth2": []}],
    },
)
def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    ok = tphoto_crud.delete_photo(db, photo_id=photo_id, soft=True)
    if not ok:
        raise HTTPException(status_code=404, detail="Photo not found")
    return None


# removed user photo count endpoint; use filtered listings instead
