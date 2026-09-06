from datetime import datetime, timedelta, timezone

import jwt


def _sign(private_key: bytes, ticket_id: str, event_id: int, expires_days: int = 30) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "ticket_id": ticket_id,
        "event_id": event_id,
        "iat": now,
        "exp": now + timedelta(days=expires_days),
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def test_checkin_success(client, test_keys):
    token = _sign(test_keys["private_key"], "ticket-001", event_id=1)

    resp = client.post("/checkin", json={"token": token})
    assert resp.status_code == 201
    data = resp.json()
    assert data["ticket_id"] == "ticket-001"
    assert data["event_id"] == 1


def test_checkin_duplicate_rejected(client, test_keys):
    token = _sign(test_keys["private_key"], "ticket-002", event_id=1)

    r1 = client.post("/checkin", json={"token": token})
    assert r1.status_code == 201

    r2 = client.post("/checkin", json={"token": token})
    assert r2.status_code == 409


def test_checkin_forged_signature_rejected(client, other_keys):
    # ky bang key la (khong phai key registration-service that su dung)
    token = _sign(other_keys["private_key"], "ticket-003", event_id=1)

    resp = client.post("/checkin", json={"token": token})
    assert resp.status_code == 401


def test_checkin_expired_token_rejected(client, test_keys):
    token = _sign(test_keys["private_key"], "ticket-004", event_id=1, expires_days=-1)

    resp = client.post("/checkin", json={"token": token})
    assert resp.status_code == 401
