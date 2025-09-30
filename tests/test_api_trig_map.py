"""
Test get_trig_map endpoint.
"""

from datetime import date, time
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.trig import Trig
from fastapi.testclient import TestClient


def test_get_trig_map_default_params(client: TestClient, db: Session):
    """Test get_trig_map with default parameters."""
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

    # Call the endpoint with default parameters
    response = client.get(f"/v1/trigs/{test_trig.id}/map")

    # Should return a valid PNG image
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0
    # Verify it's a PNG by checking magic bytes
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_get_trig_map_with_custom_colours(client: TestClient, db: Session):
    """Test get_trig_map with custom land and coastline colours."""
    # Create a test trig
    test_trig = Trig(
        id=2,
        waypoint="TP0002",
        name="Test Trigpoint 2",
        status_id=10,
        user_added=0,
        current_use="Passive station",
        historic_use="Primary",
        physical_type="Pillar",
        wgs_lat=Decimal("52.50000"),
        wgs_long=Decimal("-1.12500"),
        wgs_height=100,
        osgb_eastings=430000,
        osgb_northings=280000,
        osgb_gridref="SP 30000 80000",
        osgb_height=95,
        fb_number="S1235",
        stn_number="TEST124",
        permission_ind="Y",
        condition="G",
        postcode6="SW1A 2",
        county="Oxfordshire",
        town="Oxford",
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

    # Call with custom colours
    response = client.get(
        f"/v1/trigs/{test_trig.id}/map",
        params={
            "land_colour": "#aabbcc",
            "coastline_colour": "#112233",
            "dot_colour": "#ff0000",
            "dot_diameter": 30,
            "height": 200,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0


def test_get_trig_map_wgs84_variant(client: TestClient, db: Session):
    """Test get_trig_map with wgs84 map variant."""
    test_trig = Trig(
        id=3,
        waypoint="TP0003",
        name="Test Trigpoint 3",
        status_id=10,
        user_added=0,
        current_use="Passive station",
        historic_use="Primary",
        physical_type="Pillar",
        wgs_lat=Decimal("53.50000"),
        wgs_long=Decimal("-2.12500"),
        wgs_height=100,
        osgb_eastings=380000,
        osgb_northings=380000,
        osgb_gridref="SD 80000 80000",
        osgb_height=95,
        fb_number="S1236",
        stn_number="TEST125",
        permission_ind="Y",
        condition="G",
        postcode6="M1 1AA",
        county="Greater Manchester",
        town="Manchester",
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

    # Call with wgs84 variant
    response = client.get(
        f"/v1/trigs/{test_trig.id}/map", params={"map_variant": "wgs84"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0


def test_get_trig_map_not_found(client: TestClient, db: Session):
    """Test get_trig_map with non-existent trig."""
    response = client.get("/v1/trigs/999999/map")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_trig_map_no_land_colour(client: TestClient, db: Session):
    """Test get_trig_map with land_colour='none'."""
    test_trig = Trig(
        id=4,
        waypoint="TP0004",
        name="Test Trigpoint 4",
        status_id=10,
        user_added=0,
        current_use="Passive station",
        historic_use="Primary",
        physical_type="Pillar",
        wgs_lat=Decimal("54.50000"),
        wgs_long=Decimal("-3.12500"),
        wgs_height=100,
        osgb_eastings=330000,
        osgb_northings=480000,
        osgb_gridref="NY 30000 80000",
        osgb_height=95,
        fb_number="S1237",
        stn_number="TEST126",
        permission_ind="Y",
        condition="G",
        postcode6="CA1 1AA",
        county="Cumbria",
        town="Carlisle",
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

    # Call with land_colour='none' to skip recolouring
    response = client.get(
        f"/v1/trigs/{test_trig.id}/map", params={"land_colour": "none"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
