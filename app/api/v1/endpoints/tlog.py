"""
Logs endpoints under /v1/logs (create, read, update, delete) and nested photos.

Only PATCH (no PUT). DELETE is hard-delete for logs and soft-deletes their photos.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_scopes
from app.api.lifecycle import openapi_lifecycle
from app.crud import tlog as tlog_crud
from app.crud import tphoto as tphoto_crud
from app.models.server import Server
from app.models.user import TLog as TLogModel
from app.models.user import User
from app.schemas.tlog import TLogCreate, TLogResponse, TLogUpdate, TLogWithIncludes
from app.schemas.tphoto import TPhotoResponse
from app.utils.url import join_url
from fastapi import APIRouter, Body, Depends, HTTPException, Query

router = APIRouter()


@router.get("", openapi_extra=openapi_lifecycle("beta"))
def list_logs(
    trig_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    order: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    include: Optional[str] = Query(
        None, description="Comma-separated list of includes: photos"
    ),
    db: Session = Depends(get_db),
):
    items = tlog_crud.list_logs_filtered(
        db, trig_id=trig_id, user_id=user_id, order=order, skip=skip, limit=limit
    )
    total = tlog_crud.count_logs_filtered(db, trig_id=trig_id, user_id=user_id)
    items_serialized = [TLogResponse.model_validate(i).model_dump() for i in items]

    # Handle includes
    if include:
        tokens = {t.strip() for t in include.split(",") if t.strip()}
        unknown = tokens - {"photos"}
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown include(s): {', '.join(sorted(unknown))}",
            )
        if "photos" in tokens:
            # Attach photos list for each log item
            for out, orig in zip(items_serialized, items):
                photos = tphoto_crud.list_all_photos_for_log(db, tlog_id=int(orig.id))
                # Build base URLs per photo server
                out["photos"] = []
                for p in photos:
                    server: Server | None = (
                        db.query(Server).filter(Server.id == p.server_id).first()
                    )
                    base_url = str(server.url) if server and server.url else ""
                    out["photos"].append(
                        TPhotoResponse(
                            id=int(p.id),
                            tlog_id=int(p.tlog_id),
                            user_id=int(orig.user_id),
                            type=str(p.type),
                            filesize=int(p.filesize),
                            height=int(p.height),
                            width=int(p.width),
                            icon_filesize=int(p.icon_filesize),
                            icon_height=int(p.icon_height),
                            icon_width=int(p.icon_width),
                            name=str(p.name),
                            text_desc=str(p.text_desc),
                            public_ind=str(p.public_ind),
                            photo_url=join_url(base_url, str(p.filename)),
                            icon_url=join_url(base_url, str(p.icon_filename)),
                        ).model_dump()
                    )
    has_more = (skip + len(items)) < total
    base = "/v1/logs"
    params = [f"limit={limit}"]
    if trig_id is not None:
        params.append(f"trig_id={trig_id}")
    if user_id is not None:
        params.append(f"user_id={user_id}")
    if order:
        params.append(f"order={order}")
    self_link = base + "?" + "&".join(params + [f"skip={skip}"])
    next_link = (
        base + "?" + "&".join(params + [f"skip={skip + limit}"]) if has_more else None
    )
    prev_offset = max(skip - limit, 0)
    prev_link = (
        base + "?" + "&".join(params + [f"skip={prev_offset}"]) if skip > 0 else None
    )
    return {
        "items": items_serialized,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": skip,
            "has_more": has_more,
        },
        "links": {"self": self_link, "next": next_link, "prev": prev_link},
    }


@router.get(
    "/{log_id}",
    response_model=TLogWithIncludes,
    openapi_extra=openapi_lifecycle("beta"),
)
def get_log(
    log_id: int,
    include: Optional[str] = Query(
        None, description="Comma-separated list of includes: photos"
    ),
    db: Session = Depends(get_db),
) -> TLogWithIncludes:
    log = tlog_crud.get_log_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    base = TLogResponse.model_validate(log).model_dump()

    photos_out: Optional[list[TPhotoResponse]] = None
    if include:
        tokens = {t.strip() for t in include.split(",") if t.strip()}
        unknown = tokens - {"photos"}
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown include(s): {', '.join(sorted(unknown))}",
            )
        if "photos" in tokens:
            photos = tphoto_crud.list_all_photos_for_log(db, tlog_id=int(log.id))
            photos_out = [
                TPhotoResponse(
                    id=int(p.id),
                    tlog_id=int(p.tlog_id),
                    user_id=int(log.user_id),
                    type=str(p.type),
                    filesize=int(p.filesize),
                    height=int(p.height),
                    width=int(p.width),
                    icon_filesize=int(p.icon_filesize),
                    icon_height=int(p.icon_height),
                    icon_width=int(p.icon_width),
                    name=str(p.name),
                    text_desc=str(p.text_desc),
                    public_ind=str(p.public_ind),
                    photo_url="",
                    icon_url="",
                )
                for p in photos
            ]

    return TLogWithIncludes(**base, photos=photos_out)


@router.post(
    "",
    response_model=TLogResponse,
    status_code=201,
    openapi_extra=openapi_lifecycle("beta"),
)
def create_log(
    trig_id: int = Query(..., description="Parent trig ID"),
    payload: TLogCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = tlog_crud.create_log(
        db, trig_id=trig_id, user_id=int(current_user.id), values=payload.model_dump()
    )
    return TLogResponse.model_validate(log)


@router.patch(
    "/{log_id}", response_model=TLogResponse, openapi_extra=openapi_lifecycle("beta")
)
def update_log_endpoint(
    log_id: int,
    payload: TLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing: Optional[TLogModel] = tlog_crud.get_log_by_id(db, log_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Log not found")
    if int(existing.user_id) != int(current_user.id):
        # Require admin scope if not owner
        require_scopes("trig:admin")(db=db)

    updated = tlog_crud.update_log(
        db, log_id=log_id, updates=payload.model_dump(exclude_none=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Log not found")
    return TLogResponse.model_validate(updated)


@router.delete("/{log_id}", status_code=204, openapi_extra=openapi_lifecycle("beta"))
def delete_log_endpoint(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = tlog_crud.get_log_by_id(db, log_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Log not found")
    if int(existing.user_id) != int(current_user.id):
        require_scopes("trig:admin")(db=db)

    # Soft-delete photos then hard-delete log
    tlog_crud.soft_delete_photos_for_log(db, log_id=log_id)
    ok = tlog_crud.delete_log_hard(db, log_id=log_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Log not found")
    return None


@router.get(
    "/{log_id}/photos",
    openapi_extra=openapi_lifecycle("beta"),
)
def list_photos_for_log(
    log_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items = tphoto_crud.list_photos_filtered(db, tlog_id=log_id, skip=skip, limit=limit)
    # Note: total is estimated as count of non-deleted photos for log
    total = (
        db.query(tphoto_crud.TPhoto)
        .filter(
            tphoto_crud.TPhoto.tlog_id == log_id, tphoto_crud.TPhoto.deleted_ind != "Y"
        )
        .count()
    )
    # Build response shape similar to other collections
    # Need user_id from joining TLog for each photo
    photos = []
    for p in items:
        # fetch user_id via TLog
        tlog = db.query(TLogModel).filter(TLogModel.id == p.tlog_id).first()
        server: Server | None = (
            db.query(Server).filter(Server.id == p.server_id).first()
        )
        base_url = str(server.url) if server and server.url else ""
        photos.append(
            TPhotoResponse(
                id=int(p.id),
                tlog_id=int(p.tlog_id),
                user_id=int(tlog.user_id) if tlog else 0,
                type=str(p.type),
                filesize=int(p.filesize),
                height=int(p.height),
                width=int(p.width),
                icon_filesize=int(p.icon_filesize),
                icon_height=int(p.icon_height),
                icon_width=int(p.icon_width),
                name=str(p.name),
                text_desc=str(p.text_desc),
                public_ind=str(p.public_ind),
                photo_url=join_url(base_url, str(p.filename)),
                icon_url=join_url(base_url, str(p.icon_filename)),
            ).model_dump()
        )
    has_more = (skip + len(items)) < total
    base = f"/v1/logs/{log_id}/photos"
    self_link = base + f"?limit={limit}&skip={skip}"
    next_link = base + f"?limit={limit}&skip={skip + limit}" if has_more else None
    prev_offset = max(skip - limit, 0)
    prev_link = base + f"?limit={limit}&skip={prev_offset}" if skip > 0 else None
    return {
        "items": photos,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": skip,
            "has_more": has_more,
        },
        "links": {"self": self_link, "next": next_link, "prev": prev_link},
    }
