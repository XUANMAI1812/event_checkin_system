from sqlalchemy.orm import Session

from . import models


def create_sent_notification(
    db: Session, ticket_id: str, email: str
) -> models.SentNotification:
    record = models.SentNotification(ticket_id=ticket_id, email=email)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_sent_notification(db: Session, ticket_id: str) -> models.SentNotification | None:
    return (
        db.query(models.SentNotification)
        .filter(models.SentNotification.ticket_id == ticket_id)
        .first()
    )
