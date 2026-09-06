import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas, crud
from ..database import get_db
from ..security import sign_ticket, generate_qr_code
from ..config import settings

router = APIRouter(prefix="/events", tags=["registrations"])


@router.post(
    "/{event_id}/register", response_model=schemas.RegistrationOut, status_code=201
)
def register_attendee(
    event_id: int, reg: schemas.RegistrationCreate, db: Session = Depends(get_db)
):
    db_event = crud.get_event(db, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    if crud.count_registrations(db, event_id) >= db_event.capacity:
        raise HTTPException(status_code=400, detail="Event is full")

    ticket_id = str(uuid.uuid4())
    db_reg = crud.create_registration(db, event_id, reg, ticket_id)

    # Ve QR chua 1 JWT ky bang pri key -> checkin-service, verify = pub key
    token = sign_ticket(ticket_id, event_id)
    qr_path = os.path.join(settings.ticket_qr_dir, f"{ticket_id}.png")
    generate_qr_code(token, qr_path)

    return schemas.RegistrationOut(
        id=db_reg.id,
        event_id=db_reg.event_id,
        full_name=db_reg.full_name,
        email=db_reg.email,
        ticket_id=db_reg.ticket_id,
        qr_code_path=qr_path,
    )
