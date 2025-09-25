"""
Tests for include=photos on logs endpoints.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.tphoto import TPhoto
from app.models.user import TLog, User
from fastapi.testclient import TestClient


def seed_user_and_tlog(db: Session) -> tuple[User, TLog]:
    user = User(
        id=201,
        name="logphotouser",
        firstname="Log",
        surname="PhotoUser",
        email="lp@example.com",
    )
    tlog = TLog(
        id=3001,
        trig_id=1,
        user_id=201,
        date=datetime(2024, 1, 2).date(),
        time=datetime(2024, 1, 2).time(),
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


def create_sample_photo(db: Session, tlog_id: int, photo_id: int) -> TPhoto:
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


def test_list_logs_include_photos(client: TestClient, db: Session):
    user, tlog = seed_user_and_tlog(db)
    create_sample_photo(db, tlog_id=tlog.id, photo_id=4001)
    create_sample_photo(db, tlog_id=tlog.id, photo_id=4002)

    resp = client.get(
        f"{settings.API_V1_STR}/logs?user_id={user.id}&include=photos&limit=10&skip=0"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert len(body["items"]) >= 1
    first = body["items"][0]
    assert "photos" in first
    assert isinstance(first["photos"], list)
    assert len(first["photos"]) >= 2
    assert {p["id"] for p in first["photos"]} >= {4001, 4002}


def test_get_log_include_photos(client: TestClient, db: Session):
    _, tlog = seed_user_and_tlog(db)
    create_sample_photo(db, tlog_id=tlog.id, photo_id=4101)
    create_sample_photo(db, tlog_id=tlog.id, photo_id=4102)

    resp = client.get(f"{settings.API_V1_STR}/logs/{tlog.id}?include=photos")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == tlog.id
    assert "photos" in body
    assert isinstance(body["photos"], list)
    assert {p["id"] for p in body["photos"]} >= {4101, 4102}


def test_list_logs_unknown_include(client: TestClient, db: Session):
    seed_user_and_tlog(db)
    resp = client.get(f"{settings.API_V1_STR}/logs?include=bogus")
    assert resp.status_code == 400


def test_get_log_unknown_include(client: TestClient, db: Session):
    _, tlog = seed_user_and_tlog(db)
    resp = client.get(f"{settings.API_V1_STR}/logs/{tlog.id}?include=bogus")
    assert resp.status_code == 400
