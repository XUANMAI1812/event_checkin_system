from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CheckinRequest(BaseModel):
    token: str


class CheckinOut(BaseModel):
    ticket_id: str
    event_id: int
    checked_in_at: datetime

    model_config = ConfigDict(from_attributes=True)
