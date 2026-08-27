"""
SQLAlchemy ORM models.

Two tables for the v0.1 scope:
- ANPREvent: one row per camera sighting of a plate (entry/exit/passing)
- ParkingSession: one row per open/closed parking stay, linked to a plate
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Direction(str, enum.Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    PASSING = "PASSING"


class ParkingStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ANPREvent(Base):
    __tablename__ = "anpr_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plate: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    country: Mapped[str] = mapped_column(String(8), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(32), nullable=False)
    make: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    color: Mapped[str] = mapped_column(String(32), nullable=False)
    camera_id: Mapped[str] = mapped_column(String(32), nullable=False)
    site_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    direction: Mapped[str] = mapped_column(Enum(Direction), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True, nullable=False
    )

    __table_args__ = (
        Index("ix_anpr_events_plate_timestamp", "plate", "timestamp"),
    )


class ParkingSession(Base):
    __tablename__ = "parking_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plate: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    site_id: Mapped[str] = mapped_column(String(32), nullable=False)
    entry_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(ParkingStatus), default=ParkingStatus.OPEN, nullable=False
    )
    fee: Mapped[float | None] = mapped_column(Float, nullable=True)
