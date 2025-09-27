"""
Tests for tphoto endpoints.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.tphoto import TPhoto
from app.models.user import TLog, User
from fastapi.testclient import TestClient


def seed_user_and_tlog(db: Session) -> tuple[User, TLog]:
    user = User(
        id=101,
        name="photouser",
        firstname="Photo",
        surname="User",
        email="p@example.com",
    )
    tlog = TLog(
        id=1001,
        trig_id=1,
        user_id=101,
        date=datetime(2023, 1, 1).date(),
        time=datetime(2023, 1, 1).time(),
        osgb_eastings=1,
        osgb_northings=1,
        osgb_gridref="AA 00000 00000",
        fb_number="",
        condition="G",
        comment="",
        score=0,
        ip_addr="127.0.0.1",
        source="W",
    )
    db.add(user)
    db.add(tlog)
    db.commit()
    return user, tlog


def create_sample_photo(db: Session, tlog_id: int, photo_id: int = 2001) -> TPhoto:
    photo = TPhoto(
        id=photo_id,
        tlog_id=tlog_id,
        server_id=1,
        type="T",
        filename="000/P00001.jpg",
        filesize=100,
        height=100,
        width=100,
        icon_filename="000/I00001.jpg",
        icon_filesize=10,
        icon_height=10,
        icon_width=10,
        name="Test Photo",
        text_desc="A test",
        ip_addr="127.0.0.1",
        public_ind="Y",
        deleted_ind="N",
        source="W",
        crt_timestamp=datetime.utcnow(),
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def test_get_photo(client: TestClient, db: Session):
    _, tlog = seed_user_and_tlog(db)
    photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=2002)

    resp = client.get(f"{settings.API_V1_STR}/photos/{photo.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == photo.id
    assert body["caption"] == "Test Photo"


def test_update_photo(client: TestClient, db: Session):
    _, tlog = seed_user_and_tlog(db)
    photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=2003)

    headers = {"Authorization": "Bearer legacy_user_101"}
    resp = client.patch(
        f"{settings.API_V1_STR}/photos/{photo.id}",
        json={"caption": "New Name", "license": "N", "type": "F"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["caption"] == "New Name"
    assert body["license"] == "N"
    assert body["type"] == "F"


def test_delete_photo_soft(client: TestClient, db: Session):
    _, tlog = seed_user_and_tlog(db)
    photo = create_sample_photo(db, tlog_id=tlog.id, photo_id=2004)

    headers = {"Authorization": "Bearer legacy_user_101"}
    resp = client.delete(f"{settings.API_V1_STR}/photos/{photo.id}", headers=headers)
    assert resp.status_code == 204

    # subsequent get should 404 due to soft delete
    resp2 = client.get(f"{settings.API_V1_STR}/photos/{photo.id}")
    assert resp2.status_code == 404


# removed user photo count endpoint tests; evaluation tests retained upstream
