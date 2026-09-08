from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SentNotification(Base):
    __tablename__ = "sent_notifications"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(36), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    sent_at = Column(DateTime, default=_utcnow)
