"""Pydantic schemas for request validation and response serialization."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Direction(str, Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    PASSING = "PASSING"


class ParkingStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


# ---- ANPR events ----------------------------------------------------------

class ANPREventCreate(BaseModel):
    plate: str = Field(..., min_length=1, max_length=32)
    country: str = Field(..., min_length=1, max_length=8)
    category: str = Field(..., min_length=1, max_length=32)
    vehicle_type: str = Field(..., min_length=1, max_length=32)
    make: str = Field(..., min_length=1, max_length=64)
    model: str = Field(..., min_length=1, max_length=64)
    color: str = Field(..., min_length=1, max_length=32)
    camera_id: str = Field(..., min_length=1, max_length=32)
    site_id: str = Field(..., min_length=1, max_length=32)
    direction: Direction


class ANPREventOut(ANPREventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: datetime


# ---- Vehicles ---------------------------------------------------------

class VehicleOut(BaseModel):
    """Latest known snapshot of a plate, derived from its most recent event."""
    model_config = ConfigDict(from_attributes=True)

    plate: str
    country: str
    category: str
    vehicle_type: str
    make: str
    model: str
    color: str
    last_seen_camera_id: str
    last_seen_site_id: str
    last_direction: Direction
    last_seen_at: datetime
    sighting_count: int


# ---- Parking ------------------------------------------------------------

class ParkingSessionCreate(BaseModel):
    plate: str = Field(..., min_length=1, max_length=32)
    site_id: str = Field(..., min_length=1, max_length=32)


class ParkingSessionClose(BaseModel):
    pass  # exit_time is set server-side; body kept for future fields


class ParkingSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    plate: str
    site_id: str
    entry_time: datetime
    exit_time: datetime | None
    status: ParkingStatus
    fee: float | None


# ---- Misc ------------------------------------------------------------

class HealthOut(BaseModel):
    status: str
    app_name: str
    app_version: str
