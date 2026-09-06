import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..security import verify_ticket

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.post("", response_model=schemas.CheckinOut, status_code=201)
def checkin(payload: schemas.CheckinRequest, db: Session = Depends(get_db)):
    try:
        claims = verify_ticket(payload.token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Ticket token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid ticket token")
    try:
        record = crud.create_checkin(db, claims["ticket_id"], claims["event_id"])
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ticket already checked in")

    return record
