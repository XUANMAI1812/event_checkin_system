from sqlalchemy.orm import Session

from . import models


def create_checkin(db: Session, ticket_id: str, event_id: int) -> models.CheckinRecord:
    record = models.CheckinRecord(ticket_id=ticket_id, event_id=event_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_checkin_by_ticket(db: Session, ticket_id: str) -> models.CheckinRecord | None:
    return (
        db.query(models.CheckinRecord)
        .filter(models.CheckinRecord.ticket_id == ticket_id)
        .first()
    )
