from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CheckinRecord(Base):
    __tablename__ = "checkin_records"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(36), unique=True, nullable=False, index=True)
    event_id = Column(Integer, nullable=False)
    checked_in_at = Column(DateTime, default=_utcnow)
