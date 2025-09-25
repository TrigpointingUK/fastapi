"""
Photo endpoints (RUD) and user photo count.
"""

from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_scopes
from app.api.lifecycle import openapi_lifecycle
from app.crud import tphoto as tphoto_crud
from app.models.server import Server
from app.models.user import TLog, User
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
