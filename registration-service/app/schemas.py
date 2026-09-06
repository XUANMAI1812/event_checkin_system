from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class EventCreate(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None
    start_time: datetime
    capacity: int


class EventOut(BaseModel):
    id: int
    name: str
    description: str | None
    location: str | None
    start_time: datetime
    capacity: int

    model_config = ConfigDict(from_attributes=True)


class RegistrationCreate(BaseModel):
    full_name: str
    email: EmailStr


class RegistrationOut(BaseModel):
    id: int
    event_id: int
    full_name: str
    email: EmailStr
    ticket_id: str
    qr_code_path: str

    model_config = ConfigDict(from_attributes=True)
