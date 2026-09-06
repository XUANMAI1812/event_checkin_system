from sqlalchemy.orm import Session

from . import models, schemas


def create_event(db: Session, event: schemas.EventCreate) -> models.Event:
    db_event = models.Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_event(db: Session, event_id: int) -> models.Event | None:
    return db.query(models.Event).filter(models.Event.id == event_id).first()


def count_registrations(db: Session, event_id: int) -> int:
    return (
        db.query(models.Registration)
        .filter(models.Registration.event_id == event_id)
        .count()
    )


def create_registration(
    db: Session,
    event_id: int,
    reg: schemas.RegistrationCreate,
    ticket_id: str,
) -> models.Registration:
    db_reg = models.Registration(
        event_id=event_id,
        full_name=reg.full_name,
        email=reg.email,
        ticket_id=ticket_id,
    )
    db.add(db_reg)
    db.commit()
    db.refresh(db_reg)
    return db_reg
