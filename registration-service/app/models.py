import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    start_time = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow)

    registrations = relationship(
        "Registration", back_populates="event", cascade="all, delete-orphan"
    )


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    ticket_id = Column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    created_at = Column(DateTime, default=_utcnow)

    event = relationship("Event", back_populates="registrations")
