import os

os.environ["DATABASE_URL"] = "sqlite:///./test_hololink.db"

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import Base, engine


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)

SAMPLE_EVENT = {
    "plate": "A12345",
    "country": "UAE",
    "category": "Private",
    "vehicle_type": "SUV",
    "make": "Toyota",
    "model": "Land Cruiser",
    "color": "White",
    "camera_id": "CAM-001",
    "site_id": "SITE-001",
    "direction": "ENTRY",
}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_anpr_event():
    resp = client.post("/api/v1/anpr/events", json=SAMPLE_EVENT)
    assert resp.status_code == 201
    body = resp.json()
    assert body["plate"] == SAMPLE_EVENT["plate"]
    assert "id" in body and "timestamp" in body


def test_vehicle_not_found():
    resp = client.get("/api/v1/vehicles/UNKNOWN99")
    assert resp.status_code == 404


def test_vehicle_search_and_history():
    client.post("/api/v1/anpr/events", json=SAMPLE_EVENT)
    second = {**SAMPLE_EVENT, "direction": "EXIT", "camera_id": "CAM-002"}
    client.post("/api/v1/anpr/events", json=second)

    resp = client.get(f"/api/v1/vehicles/{SAMPLE_EVENT['plate']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["plate"] == SAMPLE_EVENT["plate"]
    assert body["sighting_count"] == 2
    assert body["last_direction"] == "EXIT"

    history = client.get(f"/api/v1/vehicles/{SAMPLE_EVENT['plate']}/history")
    assert history.status_code == 200
    assert len(history.json()) == 2


def test_parking_session_lifecycle():
    create = client.post(
        "/api/v1/parking/sessions",
        json={"plate": "B99999", "site_id": "SITE-001"},
    )
    assert create.status_code == 201
    session = create.json()
    assert session["status"] == "OPEN"
    assert session["fee"] is None

    # A second open session for the same plate should be rejected.
    dup = client.post(
        "/api/v1/parking/sessions",
        json={"plate": "B99999", "site_id": "SITE-001"},
    )
    assert dup.status_code == 409

    close = client.post(f"/api/v1/parking/sessions/{session['id']}/close")
    assert close.status_code == 200
    closed = close.json()
    assert closed["status"] == "CLOSED"
    assert closed["fee"] >= 5.0

    # Closing again should fail.
    close_again = client.post(f"/api/v1/parking/sessions/{session['id']}/close")
    assert close_again.status_code == 409
