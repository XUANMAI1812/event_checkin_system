from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.security import verify_ticket


def _sign(private_key: bytes, ticket_id: str, event_id: int, expires_days: int = 30) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "ticket_id": ticket_id,
        "event_id": event_id,
        "iat": now,
        "exp": now + timedelta(days=expires_days),
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def test_verify_ticket_valid(test_keys):
    token = _sign(test_keys["private_key"], "ticket-abc", event_id=1)
    payload = verify_ticket(token)
    assert payload["ticket_id"] == "ticket-abc"
    assert payload["event_id"] == 1


def test_verify_ticket_wrong_key_raises(other_keys, test_keys):
    token = _sign(other_keys["private_key"], "ticket-fake", event_id=1)
    with pytest.raises(jwt.InvalidSignatureError):
        verify_ticket(token)


def test_verify_ticket_expired_raises(test_keys):
    token = _sign(test_keys["private_key"], "ticket-exp", event_id=1, expires_days=-1)
    with pytest.raises(jwt.ExpiredSignatureError):
        verify_ticket(token)
