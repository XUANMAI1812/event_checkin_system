import pytest
from sqlalchemy.exc import IntegrityError

from app import crud


def test_create_sent_notification(db_session):
    record = crud.create_sent_notification(db_session, "ticket-001", "a@example.com")
    assert record.ticket_id == "ticket-001"


def test_create_sent_notification_duplicate_raises(db_session):
    crud.create_sent_notification(db_session, "ticket-002", "a@example.com")
    with pytest.raises(IntegrityError):
        crud.create_sent_notification(db_session, "ticket-002", "a@example.com")
