"""
Tests for trig endpoints.
"""
from datetime import date, time
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.trig import Trig


def test_get_trig_success(client: TestClient, db: Session):
    """Test getting a trig by ID - success case."""
    # Create a test trig
    test_trig = Trig(
        id=1,
        waypoint="TP0001",
        name="Test Trigpoint",
        status_id=10,
        user_added=0,
        current_use="Passive station",
        historic_use="Primary",
        physical_type="Pillar",
        wgs_lat=Decimal("51.50000"),
        wgs_long=Decimal("-0.12500"),
        wgs_height=100,
        osgb_eastings=530000,
        osgb_northings=180000,
        osgb_gridref="TQ 30000 80000",
        osgb_height=95,
        fb_number="S1234",
        stn_number="TEST123",
        permission_ind="Y",
        condition="G",
        postcode6="SW1A 1",
        county="London",
        town="Westminster",
        needs_attention=0,
        attention_comment="",
        crt_date=date(2023, 1, 1),
        crt_time=time(12, 0, 0),
        crt_user_id=1,
        crt_ip_addr="127.0.0.1",
    )
    db.add(test_trig)
    db.commit()
    db.refresh(test_trig)

    # Test the endpoint
    response = client.get("/api/v1/trig/1")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == 1
    assert data["waypoint"] == "TP0001"
    assert data["name"] == "Test Trigpoint"
    assert data["wgs_lat"] == "51.50000"
    assert data["county"] == "London"


def test_get_trig_not_found(client: TestClient, db: Session):
    """Test getting a trig by ID - not found case."""
    response = client.get("/api/v1/trig/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trigpoint not found"


def test_get_trig_by_waypoint_success(client: TestClient, db: Session):
    """Test getting a trig by waypoint - success case."""
    # Create a test trig
    test_trig = Trig(
        id=2,
        waypoint="TP0002",
        name="Another Trigpoint",
        status_id=10,
        user_added=0,
        current_use="Passive station",
        historic_use="Primary",
        physical_type="Pillar",
        wgs_lat=Decimal("52.50000"),
        wgs_long=Decimal("-1.12500"),
        wgs_height=150,
        osgb_eastings=440000,
        osgb_northings=290000,
        osgb_gridref="SP 40000 90000",
        osgb_height=145,
        fb_number="S5678",
        stn_number="TEST456",
        permission_ind="Y",
        condition="G",
        postcode6="B1 1AA",
        county="West Midlands",
        town="Birmingham",
        needs_attention=0,
        attention_comment="",
        crt_date=date(2023, 1, 2),
        crt_time=time(14, 30, 0),
        crt_user_id=2,
        crt_ip_addr="192.168.1.1",
    )
    db.add(test_trig)
    db.commit()

    # Test the endpoint
    response = client.get("/api/v1/trig/waypoint/TP0002")
    assert response.status_code == 200

    data = response.json()
    assert data["waypoint"] == "TP0002"
    assert data["name"] == "Another Trigpoint"


def test_get_trig_by_waypoint_not_found(client: TestClient, db: Session):
    """Test getting a trig by waypoint - not found case."""
    response = client.get("/api/v1/trig/waypoint/NONEXISTENT")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trigpoint not found"


def test_search_trigs_by_name(client: TestClient, db: Session):
    """Test searching trigs by name."""
    # Create test trigs
    trig1 = Trig(
        id=3,
        waypoint="TP0003",
        name="Ben Nevis",
        status_id=10,
        user_added=0,
        current_use="Passive station",
        historic_use="Primary",
        physical_type="Pillar",
        wgs_lat=Decimal("56.79000"),
        wgs_long=Decimal("-5.00000"),
        wgs_height=1345,
        osgb_eastings=216000,
        osgb_northings=771000,
        osgb_gridref="NN 16000 71000",
        osgb_height=1344,
        fb_number="S9999",
        stn_number="BENNEVIS",
        permission_ind="Y",
        condition="G",
        postcode6="PH15 4",
        county="Highland",
        town="Fort William",
        needs_attention=0,
        attention_comment="",
        crt_date=date(2023, 1, 3),
        crt_time=time(9, 0, 0),
        crt_user_id=1,
        crt_ip_addr="10.0.0.1",
    )

    trig2 = Trig(
        id=4,
        waypoint="TP0004",
        name="Ben More",
        status_id=10,
        user_added=0,
        current_use="Passive station",
        historic_use="Primary",
        physical_type="Pillar",
        wgs_lat=Decimal("56.42000"),
        wgs_long=Decimal("-6.02000"),
        wgs_height=966,
        osgb_eastings=165000,
        osgb_northings=732000,
        osgb_gridref="NM 65000 32000",
        osgb_height=965,
        fb_number="S8888",
        stn_number="BENMORE",
        permission_ind="Y",
        condition="G",
        postcode6="PA75 6",
        county="Argyll and Bute",
        town="Craignure",
        needs_attention=0,
        attention_comment="",
        crt_date=date(2023, 1, 4),
        crt_time=time(11, 45, 0),
        crt_user_id=2,
        crt_ip_addr="172.16.0.1",
    )

    db.add_all([trig1, trig2])
    db.commit()

    # Test search
    response = client.get("/api/v1/trig/search/name?q=Ben")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert any(trig["name"] == "Ben Nevis" for trig in data)
    assert any(trig["name"] == "Ben More" for trig in data)


def test_get_trig_count(client: TestClient, db: Session):
    """Test getting total trig count."""
    # The test database should start empty, but let's add one record
    test_trig = Trig(
        id=5,
        waypoint="TP0005",
        name="Count Test",
        status_id=10,
        user_added=0,
        current_use="Passive station",
        historic_use="Primary",
        physical_type="Pillar",
        wgs_lat=Decimal("50.00000"),
        wgs_long=Decimal("-5.00000"),
        wgs_height=200,
        osgb_eastings=200000,
        osgb_northings=100000,
        osgb_gridref="SW 00000 00000",
        osgb_height=195,
        fb_number="S0000",
        stn_number="COUNT",
        permission_ind="Y",
        condition="G",
        postcode6="TR1 1",
        county="Cornwall",
        town="Truro",
        needs_attention=0,
        attention_comment="",
        crt_date=date(2023, 1, 5),
        crt_time=time(16, 20, 0),
        crt_user_id=1,
        crt_ip_addr="203.0.113.1",
    )
    db.add(test_trig)
    db.commit()

    response = client.get("/api/v1/trig/stats/count")
    assert response.status_code == 200

    data = response.json()
    assert "total_trigpoints" in data
    assert data["total_trigpoints"] >= 1
