"""
HoloLink FastAPI application.

Implements the v0.1 scope from the README:
- ANPR event ingestion
- Vehicle search / recognition history
- Parking session creation + closing with fee calculation
- Health/status endpoint
"""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.database import get_db, init_db

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "HoloLink")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

# Simple flat-rate parking fee model for v0.1. Replace with a real pricing
# engine (tiered rates, grace periods, site-specific pricing) in v0.3.
PARKING_RATE_PER_HOUR = float(os.getenv("PARKING_RATE_PER_HOUR", "5.0"))
PARKING_MIN_FEE = float(os.getenv("PARKING_MIN_FEE", "5.0"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered ANPR vehicle intelligence platform (proof-of-concept, synthetic data only).",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", response_model=schemas.HealthOut, tags=["health"])
def health() -> schemas.HealthOut:
    return schemas.HealthOut(status="ok", app_name=APP_NAME, app_version=APP_VERSION)


# ---------------------------------------------------------------------------
# ANPR events
# ---------------------------------------------------------------------------

@app.post(
    "/api/v1/anpr/events",
    response_model=schemas.ANPREventOut,
    status_code=201,
    tags=["anpr"],
)
def create_anpr_event(
    event: schemas.ANPREventCreate, db: Session = Depends(get_db)
) -> models.ANPREvent:
    db_event = models.ANPREvent(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


# ---------------------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/vehicles/{plate}",
    response_model=schemas.VehicleOut,
    tags=["vehicles"],
)
def get_vehicle(plate: str, db: Session = Depends(get_db)) -> schemas.VehicleOut:
    plate = plate.upper()

    latest = db.scalar(
        select(models.ANPREvent)
        .where(func.upper(models.ANPREvent.plate) == plate)
        .order_by(models.ANPREvent.timestamp.desc())
        .limit(1)
    )
    if latest is None:
        raise HTTPException(status_code=404, detail=f"No sightings found for plate '{plate}'")

    count = db.scalar(
        select(func.count())
        .select_from(models.ANPREvent)
        .where(func.upper(models.ANPREvent.plate) == plate)
    )

    return schemas.VehicleOut(
        plate=latest.plate,
        country=latest.country,
        category=latest.category,
        vehicle_type=latest.vehicle_type,
        make=latest.make,
        model=latest.model,
        color=latest.color,
        last_seen_camera_id=latest.camera_id,
        last_seen_site_id=latest.site_id,
        last_direction=latest.direction,
        last_seen_at=latest.timestamp,
        sighting_count=count or 0,
    )


@app.get(
    "/api/v1/vehicles/{plate}/history",
    response_model=list[schemas.ANPREventOut],
    tags=["vehicles"],
)
def get_vehicle_history(
    plate: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[models.ANPREvent]:
    plate = plate.upper()
    events = db.scalars(
        select(models.ANPREvent)
        .where(func.upper(models.ANPREvent.plate) == plate)
        .order_by(models.ANPREvent.timestamp.desc())
        .limit(limit)
    ).all()

    if not events:
        raise HTTPException(status_code=404, detail=f"No sightings found for plate '{plate}'")

    return list(events)


# ---------------------------------------------------------------------------
# Parking
# ---------------------------------------------------------------------------

@app.post(
    "/api/v1/parking/sessions",
    response_model=schemas.ParkingSessionOut,
    status_code=201,
    tags=["parking"],
)
def create_parking_session(
    payload: schemas.ParkingSessionCreate, db: Session = Depends(get_db)
) -> models.ParkingSession:
    existing_open = db.scalar(
        select(models.ParkingSession).where(
            func.upper(models.ParkingSession.plate) == payload.plate.upper(),
            models.ParkingSession.status == models.ParkingStatus.OPEN,
        )
    )
    if existing_open is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Plate '{payload.plate}' already has an open parking session ({existing_open.id})",
        )

    session = models.ParkingSession(plate=payload.plate.upper(), site_id=payload.site_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@app.get(
    "/api/v1/parking/sessions/{session_id}",
    response_model=schemas.ParkingSessionOut,
    tags=["parking"],
)
def get_parking_session(session_id: str, db: Session = Depends(get_db)) -> models.ParkingSession:
    session = db.get(models.ParkingSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Parking session not found")
    return session


@app.post(
    "/api/v1/parking/sessions/{session_id}/close",
    response_model=schemas.ParkingSessionOut,
    tags=["parking"],
)
def close_parking_session(session_id: str, db: Session = Depends(get_db)) -> models.ParkingSession:
    session = db.get(models.ParkingSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Parking session not found")
    if session.status == models.ParkingStatus.CLOSED:
        raise HTTPException(status_code=409, detail="Parking session is already closed")

    session.exit_time = datetime.now(timezone.utc)
    session.status = models.ParkingStatus.CLOSED
    session.fee = _calculate_fee(session.entry_time, session.exit_time)

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _calculate_fee(entry_time: datetime, exit_time: datetime) -> float:
    """Flat per-hour rate with a minimum fee, rounded up to the next hour."""
    if entry_time.tzinfo is None:
        entry_time = entry_time.replace(tzinfo=timezone.utc)
    if exit_time.tzinfo is None:
        exit_time = exit_time.replace(tzinfo=timezone.utc)

    import math

    duration_hours = (exit_time - entry_time).total_seconds() / 3600
    billable_hours = max(1, math.ceil(duration_hours))
    fee = billable_hours * PARKING_RATE_PER_HOUR
    return round(max(fee, PARKING_MIN_FEE), 2)
